<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import type { WorkEvidence, WorkEvidenceInput, WorkStatus } from '../types'

const props = defineProps<{
  evidence: WorkEvidence | null
  workStatus: WorkStatus
  disabled?: boolean
}>()

const emit = defineEmits<{
  save: [input: WorkEvidenceInput]
  decide: [decisionType: 'accept' | 'request_changes', reason: string]
}>()

const verification = shallowRef('')
const review = shallowRef('')
const knowledgeProposal = shallowRef('')
const candidateEvalCase = shallowRef('')
const pullRequestUrl = shallowRef('')
const reason = shallowRef('')

watch(
  () => props.evidence,
  (evidence) => {
    const payload = evidence?.payload || {}
    verification.value = String(payload.verification_summary || '')
    review.value = String(payload.review_summary || '')
    knowledgeProposal.value = String(payload.knowledge_proposal || '')
    candidateEvalCase.value = String(payload.candidate_eval_case || '')
    pullRequestUrl.value = String(payload.pull_request_url || '')
  },
  { immediate: true },
)

function save() {
  emit('save', {
    verification_summary: verification.value.trim() || undefined,
    review_summary: review.value.trim() || undefined,
    knowledge_proposal: knowledgeProposal.value.trim() || undefined,
    candidate_eval_case: candidateEvalCase.value.trim() || undefined,
    pull_request_url: pullRequestUrl.value.trim() || undefined,
  })
}

function decide(type: 'accept' | 'request_changes') {
  if (reason.value.trim()) emit('decide', type, reason.value.trim())
}
</script>

<template>
  <div class="evidence-panel">
    <div v-if="evidence" class="git-evidence">
      <div><span>HEAD</span><strong>{{ evidence.payload.head_commit || '尚无 Commit' }}</strong></div>
      <div><span>工作区</span><strong>{{ evidence.payload.worktree_status ? '有未提交变化' : 'clean' }}</strong></div>
      <div><span>Diff</span><pre>{{ evidence.payload.diff_summary || '尚无提交差异' }}</pre></div>
    </div>

    <label>
      <span>真实验证摘要</span>
      <textarea v-model="verification" class="field" rows="4" placeholder="记录执行过的命令、结果和边界"></textarea>
    </label>
    <label>
      <span>交付审查摘要</span>
      <textarea v-model="review" class="field" rows="4" placeholder="说明需求、实现与证据是否对齐"></textarea>
    </label>
    <label>
      <span>Knowledge Proposal 候选</span>
      <textarea v-model="knowledgeProposal" class="field" rows="3" placeholder="哪些长期知识可能需要受审更新"></textarea>
    </label>
    <label>
      <span>Candidate EvalCase</span>
      <textarea v-model="candidateEvalCase" class="field" rows="3" placeholder="这次真实任务可以沉淀为什么回归用例"></textarea>
    </label>
    <label>
      <span>PR / MR 引用（仅人工操作后回填）</span>
      <input v-model="pullRequestUrl" class="field" placeholder="https://…" />
    </label>
    <button class="button" type="button" :disabled="disabled || workStatus === 'accepted'" @click="save">
      刷新 Git 并保存证据
    </button>

    <div v-if="workStatus !== 'accepted'" class="decision-box">
      <label>
        <span>人的交付判断</span>
        <textarea v-model="reason" class="field" rows="3" placeholder="说明接受或要求修订的原因"></textarea>
      </label>
      <div>
        <button class="button" type="button" :disabled="disabled || !reason.trim()" @click="decide('request_changes')">
          要求修订
        </button>
        <button class="button primary" type="button" :disabled="disabled || !reason.trim()" @click="decide('accept')">
          接受交付
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.evidence-panel,
.evidence-panel label {
  display: grid;
  gap: 8px;
}

.evidence-panel {
  gap: 13px;
}

.evidence-panel label > span,
.git-evidence span {
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
}

.evidence-panel textarea {
  resize: vertical;
}

.git-evidence {
  display: grid;
  gap: 8px;
  padding: 11px;
  border: 1px solid var(--color-line-subtle);
  background: var(--color-surface-subtle);
}

.git-evidence div {
  display: grid;
  gap: 3px;
}

.git-evidence strong,
.git-evidence pre {
  overflow: auto;
  margin: 0;
  font: 10px/1.5 var(--font-mono);
}

.decision-box {
  display: grid;
  gap: 10px;
  margin-top: 3px;
  padding-top: 14px;
  border-top: 1px solid var(--color-line);
}

.decision-box > div {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
