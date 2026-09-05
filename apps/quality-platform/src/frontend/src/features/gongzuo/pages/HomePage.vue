<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import GongzuoIcon from '../components/GongzuoIcon.vue'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'

const router = useRouter()
const quickIdea = shallowRef('')
const { activeWorkspace, rootItems, runs, state, openModal, createIdea } = useGongzuoWorkspace()
const needsAttention = computed(() => rootItems.value.filter((item) => item.attention))
const activeItems = computed(() => rootItems.value.filter((item) => item.state !== '已完成' && item.state !== 'accepted'))
const activeRuns = computed(() => runs.value.filter((run) => ['queued', 'claimed', 'running', 'pause_requested'].includes(run.state)))
const isTeam = computed(() => activeWorkspace.value === 'team')

function itemUrl(id: string, tab = 'overview') {
  return `/gongzuo/${activeWorkspace.value}/items/${encodeURIComponent(id)}/${tab}`
}

async function saveQuickIdea() {
  const body = quickIdea.value.trim()
  if (!body) return
  await createIdea({ body, scope: activeWorkspace.value === 'team' ? '团队' : '个人' })
  quickIdea.value = ''
}
</script>

<template>
  <PageHeader
    title="我的工作"
    subtitle="把需要判断、正在推进与委托运行放在同一处。"
    eyebrow="FOCUS / 把注意力留给真正需要你的事"
  >
    <button class="gz-btn" type="button" @click="router.push(`/gongzuo/${activeWorkspace}/meeting`)">
      <GongzuoIcon name="meeting" />{{ isTeam ? '打开组会' : '打开周回顾' }}
    </button>
  </PageHeader>

  <div class="gz-two-cols">
    <div>
      <div class="gz-summary-line">
        <div><strong>{{ needsAttention.length }}</strong><span>项需要判断</span></div>
        <div><strong>{{ activeItems.length }}</strong><span>项正在推进</span></div>
        <div><strong>{{ activeRuns.length }}</strong><span>个委托运行</span></div>
      </div>

      <div class="gz-section-title"><h2>需要我处理</h2><StatusBadge value="先看变化，再作决定" tone="blue" /></div>
      <div class="gz-panel">
        <div v-for="item in needsAttention" :key="item.id" class="gz-action-row">
          <span class="gz-badge-icon"><GongzuoIcon :name="item.state === '已阻塞' ? 'flag' : 'message'" /></span>
          <div class="gz-row-main">
            <div class="gz-inline"><span class="gz-mono gz-muted">{{ item.id }}</span><StatusBadge :value="item.state === '已阻塞' ? '补充条件' : '有新提案'" tone="amber" /></div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.update }}</p>
            <span class="gz-tiny gz-muted">{{ item.context.proposals.length ? '候选修改保留原文与来源，采纳后更新共享上下文。' : '这项决定属于你，不需要重新描述全部背景。' }}</span>
          </div>
          <RouterLink class="gz-btn" :to="itemUrl(item.id, item.context.proposals.length ? 'context' : 'overview')">
            {{ item.context.proposals.length ? '查看上下文变化' : '打开事项' }}
          </RouterLink>
        </div>
        <div v-if="!needsAttention.length" class="gz-empty">当前没有待你判断的事项。</div>
      </div>

      <div class="gz-section-title">
        <h2>我关注的结果</h2>
        <RouterLink class="gz-btn ghost sm" :to="`/gongzuo/${activeWorkspace}/items`">查看全部 <GongzuoIcon name="arrow" /></RouterLink>
      </div>
      <div class="gz-panel">
        <div v-for="item in activeItems" :key="item.id" class="gz-list-row">
          <span class="gz-mono gz-muted">{{ item.id }}</span>
          <div class="gz-grow">
            <RouterLink class="gz-text-btn gz-list-title" :to="itemUrl(item.id)">{{ item.title }}</RouterLink>
            <div class="gz-list-sub">{{ item.update }}</div>
          </div>
          <StatusBadge :value="item.state" />
          <button class="gz-btn ghost icon-only" type="button" :aria-label="`速览 ${item.title}`" @click="openModal('peek', { item })"><GongzuoIcon name="eye" /></button>
        </div>
        <div v-if="!activeItems.length" class="gz-empty">当前没有正在推进的事项。</div>
      </div>

      <div class="gz-section-title"><h2>回来后，不必再从头解释</h2></div>
      <div class="gz-notice"><GongzuoIcon name="layers" /><div><strong>每件工作有自己的持续上下文。</strong><br />目标、共识、材料、未决问题与成果都留在事项里。</div></div>
    </div>

    <aside class="gz-stack">
      <section class="gz-panel pad">
        <h2 class="gz-small-heading">先把想法留下来</h2>
        <textarea v-model="quickIdea" class="gz-capture" aria-label="随手记录" placeholder="一句灵感、一个问题，或一段反馈……"></textarea>
        <div class="gz-between gz-mt-10"><span class="gz-tiny gz-muted">仅保存，不启动 AI</span><button class="gz-btn primary sm" type="button" @click="saveQuickIdea">记下来</button></div>
      </section>
      <section v-if="rootItems[0]" class="gz-panel pad">
        <h2 class="gz-small-heading">最近的共同理解</h2>
        <div class="gz-note-card">
          <div class="gz-inline"><StatusBadge :value="rootItems[0].context.revision ? `共识 v${rootItems[0].context.revision}` : '打开查看上下文'" tone="blue" /><span class="gz-tiny gz-muted">{{ rootItems[0].id }}</span></div>
          <p>{{ rootItems[0].scope }}</p>
          <RouterLink class="gz-text-btn" :to="itemUrl(rootItems[0].id, 'context')">查看依据与未决问题 <GongzuoIcon name="arrow" /></RouterLink>
        </div>
      </section>
      <section class="gz-panel pad">
        <span class="gz-tiny gz-muted">当前工作环境</span>
        <h3 class="gz-environment-title">{{ isTeam ? 'OpenCode + 团队执行机' : 'Codex / OpenCode + 我的 WSL' }}</h3>
        <p class="gz-small gz-sub">{{ isTeam ? '运行状态来自团队执行端。' : '个人事项也可以没有代码仓、容器和研发流程。' }}</p>
      </section>
      <section v-if="!state?.items.length" class="gz-notice neutral">当前空间没有数据，可从“记录”开始建立真实内容。</section>
    </aside>
  </div>
</template>
