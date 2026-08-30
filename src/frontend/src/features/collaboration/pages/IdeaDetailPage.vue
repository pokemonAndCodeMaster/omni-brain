<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAgentRun } from '@/features/agent-runtime/api/agentRuntime'
import AgentActionPanel from '../components/AgentActionPanel.vue'
import CollaborationTimeline from '../components/CollaborationTimeline.vue'
import RequirementEditor from '../components/RequirementEditor.vue'
import { useIdeaDetail } from '../composables/useIdeaDetail'
import { emptyRequirementContent, type AgentActionInput, type RequirementContent } from '../types'

const route = useRoute()
const router = useRouter()
const ideaId = computed(() => String(route.params.ideaId ?? ''))
const { idea, timeline, loading, actionPending, error, load, addMessage, startAction, convert, archive } = useIdeaDetail(ideaId)
const message = shallowRef('')
const localError = shallowRef('')
const messagePending = shallowRef(false)
const converting = shallowRef(false)
const convertOpen = shallowRef(false)
const requirementTitle = shallowRef('')
const requirementContent = shallowRef<RequirementContent>(emptyRequirementContent())
const sourceRunId = shallowRef<string | undefined>()

watch(
  idea,
  (value) => {
    if (value && !requirementTitle.value) requirementTitle.value = value.title
  },
  { immediate: true },
)

async function submitMessage() {
  if (!message.value.trim()) return
  messagePending.value = true
  localError.value = ''
  try {
    await addMessage(message.value.trim())
    message.value = ''
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : '消息保存失败'
  } finally {
    messagePending.value = false
  }
}

async function launch(input: AgentActionInput) {
  localError.value = ''
  try {
    await startAction(input)
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Agent 动作启动失败'
  }
}

async function useRun(runId: string) {
  localError.value = ''
  try {
    const run = await getAgentRun(runId)
    const payload = run.result_payload
    if (!payload || typeof payload.title !== 'string' || typeof payload.content !== 'object' || !payload.content) {
      throw new Error('该 Run 没有可用的结构化 Requirement 结果')
    }
    requirementTitle.value = payload.title
    requirementContent.value = { ...emptyRequirementContent(), ...(payload.content as Partial<RequirementContent>) }
    sourceRunId.value = runId
    convertOpen.value = true
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Run 结果读取失败'
  }
}

async function submitConversion() {
  if (!requirementTitle.value.trim()) return
  converting.value = true
  localError.value = ''
  try {
    const requirement = await convert({
      title: requirementTitle.value.trim(),
      content: requirementContent.value,
      source_run_id: sourceRunId.value,
    })
    await router.push({ name: 'requirement-detail', params: { requirementId: requirement.id } })
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : '转为候选需求失败'
  } finally {
    converting.value = false
  }
}

async function archiveCurrent() {
  try {
    await archive()
    await router.push({ name: 'idea-inbox' })
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Idea 归档失败'
  }
}
</script>

<template>
  <section class="collab-page">
    <header class="collab-heading">
      <div>
        <p class="collab-eyebrow">IDEA / {{ ideaId }}</p>
        <h2>{{ idea?.title || '正在读取 Idea…' }}</h2>
        <p v-if="idea">{{ idea.domain_key || '未分类' }} · admin · {{ idea.run_count }} Runs</p>
      </div>
      <div class="collab-heading-actions">
        <RouterLink v-if="idea?.requirement_id" class="button primary" :to="`/ai/requirements/${idea.requirement_id}`">查看需求</RouterLink>
        <button v-else class="button primary" type="button" @click="convertOpen = !convertOpen">转为候选需求</button>
        <button v-if="idea && !['converted', 'archived'].includes(idea.status)" class="button" type="button" @click="archiveCurrent">归档</button>
      </div>
    </header>

    <p v-if="error || localError" class="collab-error" role="alert">{{ error || localError }}</p>
    <div v-if="loading && !idea" class="panel collab-loading">正在读取 Idea…</div>

    <div v-else-if="idea" class="collab-detail-grid">
      <main class="collab-main-stack">
        <section class="panel collab-section">
          <header class="section-heading"><strong>协作时间线</strong><button class="button" type="button" @click="load">刷新</button></header>
          <CollaborationTimeline :items="timeline" @use-run="useRun" />
          <form class="message-composer" @submit.prevent="submitMessage">
            <label class="message-field">
              <span>补充意见</span>
              <textarea v-model="message" class="field" rows="3" placeholder="补充判断、纠正或约束"></textarea>
            </label>
            <button class="button" type="submit" :disabled="messagePending || !message.trim()">记录人的意见</button>
          </form>
        </section>

        <section v-if="convertOpen && !idea.requirement_id" class="panel collab-section">
          <header class="section-heading"><strong>候选需求预览</strong><span>{{ sourceRunId ? `来源 ${sourceRunId}` : '人工填写' }}</span></header>
          <label class="collab-field-label"><span>需求标题</span><input v-model="requirementTitle" class="field" /></label>
          <RequirementEditor v-model="requirementContent" />
          <div class="section-actions"><button class="button primary" type="button" :disabled="converting" @click="submitConversion">{{ converting ? '正在创建…' : '创建 candidate Requirement' }}</button></div>
        </section>
      </main>

      <aside class="collab-side-stack">
        <section class="panel collab-section original-card">
          <header class="section-heading"><strong>原始想法</strong><span>{{ idea.status }}</span></header>
          <p>{{ idea.raw_content }}</p>
        </section>
        <section class="panel collab-section"><AgentActionPanel :submitting="actionPending" @submit="launch" /></section>
      </aside>
    </div>
  </section>
</template>
