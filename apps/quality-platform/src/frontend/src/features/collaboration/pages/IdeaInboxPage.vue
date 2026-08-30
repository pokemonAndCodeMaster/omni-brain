<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import IdeaCaptureForm from '../components/IdeaCaptureForm.vue'
import IdeaSummaryList from '../components/IdeaSummaryList.vue'
import { useIdeaInbox } from '../composables/useIdeaInbox'

const router = useRouter()
const { items, total, loading, error, status, load, create } = useIdeaInbox()
const creating = shallowRef(false)
const createError = shallowRef('')

onMounted(() => void load())

async function submit(input: { title: string; raw_content: string; domain_key?: string }) {
  creating.value = true
  createError.value = ''
  try {
    const idea = await create(input)
    await router.push({ name: 'idea-detail', params: { ideaId: idea.id } })
  } catch (reason) {
    createError.value = reason instanceof Error ? reason.message : 'Idea 创建失败'
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <section class="collab-page">
    <header class="collab-heading">
      <div>
        <p class="collab-eyebrow">IDEA INBOX</p>
        <h2>先留下，再一起想清楚</h2>
        <p>原始想法不会被 Agent 覆盖；进入详情后再补背景、讨论或转成候选需求。</p>
      </div>
      <span class="collab-count">{{ total }} Ideas</span>
    </header>

    <p v-if="error || createError" class="collab-error" role="alert">{{ error || createError }}</p>

    <div class="collab-split collab-split-narrow">
      <section class="panel collab-panel">
        <header class="collab-toolbar">
          <strong>Idea 列表</strong>
          <div>
            <select v-model="status" class="select-field" aria-label="按 Idea 状态筛选" @change="load">
              <option value="">全部状态</option>
              <option value="captured">待展开</option>
              <option value="discussing">讨论中</option>
              <option value="converted">已转需求</option>
              <option value="archived">已归档</option>
            </select>
            <button class="button" type="button" :disabled="loading" @click="load">刷新</button>
          </div>
        </header>
        <IdeaSummaryList :items="items" :loading="loading" @select="router.push(`/ai/ideas/${$event}`)" />
      </section>

      <aside class="panel collab-panel collab-sticky-card">
        <IdeaCaptureForm :submitting="creating" @submit="submit" />
      </aside>
    </div>
  </section>
</template>
