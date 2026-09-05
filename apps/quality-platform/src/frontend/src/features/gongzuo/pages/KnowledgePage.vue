<script setup lang="ts">
import { computed, onMounted, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { apiError, getKnowledgeDocument, getKnowledgeList } from '../api/gongzuo'
import GongzuoIcon from '../components/GongzuoIcon.vue'
import LoadingState from '../components/LoadingState.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import { resolveKnowledgePath } from '../utils/knowledgeLinks'

interface KnowledgeEntry { path: string; title: string; version: string; source: string; excerpt: string }
interface KnowledgeDetail extends KnowledgeEntry { content: string; sourceVersion?: string; readOnly: boolean; releaseId?: string; sourceChanged?: boolean }

const route = useRoute()
const router = useRouter()
const { activeWorkspace, openModal } = useGongzuoWorkspace()
const query = shallowRef('')
const entries = shallowRef<KnowledgeEntry[]>([])
const selected = shallowRef<KnowledgeDetail | null>(null)
const loading = shallowRef(false)
const error = shallowRef('')


const renderedContent = computed(() => {
  const raw = marked.parse(selected.value?.content ?? '', { gfm: true, breaks: false, async: false }) as string
  const sanitized = DOMPurify.sanitize(raw, { USE_PROFILES: { html: true }, FORBID_TAGS: ['style', 'iframe', 'object', 'embed', 'form', 'input', 'button'], FORBID_ATTR: ['style', 'srcdoc'] })
  const parsed = new DOMParser().parseFromString(sanitized, 'text/html')
  parsed.querySelectorAll('a').forEach((anchor) => {
    const href = anchor.getAttribute('href') ?? ''
    if (href.startsWith('#')) return
    const knowledgePath = selected.value ? resolveKnowledgePath(selected.value.path, href) : null
    if (knowledgePath) {
      anchor.dataset.knowledgePath = knowledgePath
      anchor.href = router.resolve({ query: { ...route.query, path: knowledgePath } }).href
      return
    }
    try {
      const url = new URL(href)
      if (!['http:', 'https:', 'mailto:'].includes(url.protocol)) throw new Error('unsupported protocol')
      if (['http:', 'https:'].includes(url.protocol)) { anchor.target = '_blank'; anchor.rel = 'noopener noreferrer' }
    } catch {
      anchor.removeAttribute('href')
      anchor.dataset.sourceLocation = href
      anchor.title = `来源定位：${href}`
    }
  })
  return parsed.body.innerHTML
})

async function search() {
  loading.value = true; error.value = ''
  try {
    const result = await getKnowledgeList(activeWorkspace.value, query.value)
    entries.value = result.items ?? []
    const requested = String(route.query.path ?? '')
    if (requested) await readPath(requested, false)
    else if (!selected.value && entries.value[0]) await read(entries.value[0])
  } catch (caught) { error.value = apiError(caught).message } finally { loading.value = false }
}

async function readPath(path: string, updateRoute = true) {
  loading.value = true; error.value = ''
  try {
    selected.value = await getKnowledgeDocument(activeWorkspace.value, path) as KnowledgeDetail
    if (updateRoute && route.query.path !== path) await router.replace({ query: { ...route.query, path } })
  } catch (caught) { error.value = apiError(caught).message }
  finally { loading.value = false }
}
async function read(entry: KnowledgeEntry) { await readPath(entry.path) }
function onDocumentClick(event: MouseEvent) {
  const anchor = (event.target as HTMLElement).closest<HTMLAnchorElement>('a[data-knowledge-path]')
  if (!anchor?.dataset.knowledgePath) return
  event.preventDefault(); void readPath(anchor.dataset.knowledgePath)
}

onMounted(search)
watch(activeWorkspace, () => { selected.value = null; void search() })
watch(() => String(route.query.path ?? ''), (path) => { if (path && path !== selected.value?.path) void readPath(path, false) })
</script>


<template>
  <PageHeader title="知识" subtitle="从正式知识源浏览、定位与提出受审修订；事项只保留用途和版本引用。">
    <button class="gz-btn" type="button" :disabled="!selected" @click="openModal('knowledge-proposal', { document: selected })"><GongzuoIcon name="edit" />提出知识修订</button>
  </PageHeader>
  <div class="gz-toolbar"><input v-model="query" class="gz-grow" aria-label="搜索知识" placeholder="搜索标题、路径或正文" @keyup.enter="search" /><button class="gz-btn" type="button" @click="search"><GongzuoIcon name="search" />查找</button></div>
  <LoadingState v-if="error && !selected" :error="error" @retry="search" />
  <div v-else class="gz-knowledge-grid">
    <aside class="gz-panel gz-knowledge-nav">
      <button v-for="entry in entries" :key="entry.path" class="gz-knowledge-link" :class="{ active: selected?.path === entry.path }" type="button" @click="read(entry)"><GongzuoIcon name="file" /><span>{{ entry.title }}<small>{{ entry.path }} · {{ entry.version }}</small></span></button>
      <div v-if="!entries.length && !loading" class="gz-empty">没有找到可读取的正式知识。</div>
    </aside>
    <article class="gz-panel gz-article gz-knowledge-article">
      <div v-if="loading" class="gz-empty">正在读取正文…</div>
      <template v-else-if="selected">
        <div class="gz-between gz-mb-20"><span class="gz-eyebrow">{{ selected.path }}</span><div class="gz-inline"><StatusBadge :value="selected.readOnly ? '只读来源' : '可修订来源'" :tone="selected.readOnly ? 'amber' : 'blue'" /><StatusBadge v-if="selected.sourceChanged" value="来源已变化" tone="amber" /></div></div>
        <div class="gz-markdown" @click="onDocumentClick" v-html="renderedContent"></div>
        <hr class="gz-rule" />
        <div class="gz-prop"><span>知识版本</span><div class="gz-mono">{{ selected.version }}</div></div><div class="gz-prop"><span>来源版本</span><div class="gz-mono">{{ selected.sourceVersion || '未提供' }}</div></div><div class="gz-prop"><span>来源</span><div>{{ selected.source }}</div></div><div v-if="selected.releaseId" class="gz-prop"><span>发布身份</span><div class="gz-mono">{{ selected.releaseId }}</div></div>
      </template>
      <div v-else class="gz-empty">从左侧选择一份知识阅读。</div>
    </article>
  </div>
</template>
