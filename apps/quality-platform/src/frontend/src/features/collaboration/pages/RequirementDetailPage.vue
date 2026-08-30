<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getAgentRun } from '@/features/agent-runtime/api/agentRuntime'
import AgentActionPanel from '../components/AgentActionPanel.vue'
import CollaborationTimeline from '../components/CollaborationTimeline.vue'
import RequirementDecisionPanel from '../components/RequirementDecisionPanel.vue'
import RequirementEditor from '../components/RequirementEditor.vue'
import RequirementRevisionList from '../components/RequirementRevisionList.vue'
import { useRequirementDetail } from '../composables/useRequirementDetail'
import { emptyRequirementContent, type AgentActionInput, type RequirementContent, type RequirementDecisionInput } from '../types'

const route = useRoute()
const requirementId = computed(() => String(route.params.requirementId ?? ''))
const { requirement, revisions, timeline, loading, actionPending, error, load, saveRevision, addMessage, startAction, decide } = useRequirementDetail(requirementId)
const draft = shallowRef<RequirementContent>(emptyRequirementContent())
const sourceRunId = shallowRef<string | undefined>()
const localError = shallowRef('')
const saving = shallowRef(false)
const deciding = shallowRef(false)
const message = shallowRef('')
const messagePending = shallowRef(false)

watch(
  () => requirement.value?.current_revision,
  (revision) => {
    if (revision?.content) draft.value = { ...emptyRequirementContent(), ...revision.content }
  },
  { immediate: true },
)

async function save() {
  saving.value = true
  localError.value = ''
  try {
    await saveRevision(draft.value, sourceRunId.value)
    sourceRunId.value = undefined
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Revision 保存失败'
  } finally {
    saving.value = false
  }
}

async function launch(input: AgentActionInput) {
  try {
    await startAction(input)
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Agent 动作启动失败'
  }
}

async function useRun(runId: string) {
  try {
    const run = await getAgentRun(runId)
    const content = run.result_payload?.content
    if (!content || typeof content !== 'object') throw new Error('该 Run 没有结构化 Requirement 内容')
    draft.value = { ...emptyRequirementContent(), ...(content as Partial<RequirementContent>) }
    sourceRunId.value = runId
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Run 结果读取失败'
  }
}

async function submitDecision(input: RequirementDecisionInput) {
  deciding.value = true
  localError.value = ''
  try {
    await decide(input)
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : '评审决定提交失败'
  } finally {
    deciding.value = false
  }
}

async function submitMessage() {
  if (!message.value.trim()) return
  messagePending.value = true
  try {
    await addMessage(message.value.trim())
    message.value = ''
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : '消息保存失败'
  } finally {
    messagePending.value = false
  }
}
</script>

<template>
  <section class="collab-page">
    <header class="collab-heading">
      <div>
        <p class="collab-eyebrow">REQUIREMENT / {{ requirementId }}</p>
        <h2>{{ requirement?.title || '正在读取 Requirement…' }}</h2>
        <p v-if="requirement">{{ requirement.status }} · {{ requirement.commitment || '未承诺' }} · admin</p>
      </div>
      <RouterLink v-if="requirement?.source_idea_id" class="button" :to="`/ai/ideas/${requirement.source_idea_id}`">来源 Idea</RouterLink>
    </header>

    <p v-if="error || localError" class="collab-error" role="alert">{{ error || localError }}</p>
    <div v-if="loading && !requirement" class="panel collab-loading">正在读取 Requirement…</div>

    <div v-else-if="requirement" class="collab-detail-grid">
      <main class="collab-main-stack">
        <section class="panel collab-section">
          <header class="section-heading">
            <div><strong>当前 R{{ requirement.current_revision.revision_no }}</strong><span v-if="sourceRunId">已载入 {{ sourceRunId }} 候选</span></div>
            <button v-if="requirement.status === 'candidate'" class="button primary" type="button" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存新 Revision' }}</button>
          </header>
          <RequirementEditor v-model="draft" />
        </section>

        <section class="panel collab-section">
          <header class="section-heading"><strong>协作时间线</strong><button class="button" type="button" @click="load">刷新</button></header>
          <CollaborationTimeline :items="timeline" @use-run="useRun" />
          <form class="message-composer" @submit.prevent="submitMessage">
            <label class="message-field">
              <span>补充意见</span>
              <textarea v-model="message" class="field" rows="3" placeholder="补充人的判断或纠正"></textarea>
            </label>
            <button class="button" type="submit" :disabled="messagePending || !message.trim()">记录人的意见</button>
          </form>
        </section>
      </main>

      <aside class="collab-side-stack">
        <section class="panel collab-section"><RequirementDecisionPanel :status="requirement.status" :current-revision-id="requirement.current_revision_id" :revision-content="draft" :submitting="deciding" @submit="submitDecision" /></section>
        <section class="panel collab-section"><AgentActionPanel :submitting="actionPending" @submit="launch" /></section>
        <section class="panel collab-section"><header class="section-heading"><strong>Revision 历史</strong><span>{{ revisions.length }}</span></header><RequirementRevisionList :revisions="revisions" :current-id="requirement.current_revision_id" :accepted-id="requirement.accepted_revision_id" /></section>
      </aside>
    </div>
  </section>
</template>
