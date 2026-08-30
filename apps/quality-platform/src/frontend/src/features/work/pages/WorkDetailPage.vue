<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import WorkEvidencePanel from '../components/WorkEvidencePanel.vue'
import WorkMetadataPanel from '../components/WorkMetadataPanel.vue'
import WorkPlanTimeline from '../components/WorkPlanTimeline.vue'
import { useWorkDetail } from '../composables/useWorkDetail'
import type { WorkEvidenceInput, WorkStepRunInput, WorkUpdateInput } from '../types'

const route = useRoute()
const workId = computed(() => String(route.params.workId ?? ''))
const { work, loading, acting, error, hasActiveRun, load, saveMetadata, startStep, completeStep, saveEvidence, decide } = useWorkDetail(workId)

const statusLabels = {
  planned: '已计划',
  in_progress: '进行中',
  in_review: '等待交付接受',
  revision_requested: '要求修订',
  accepted: '已接受',
  cancelled: '已取消',
} as const

async function launch(stepId: string, input: WorkStepRunInput) {
  try {
    await startStep(stepId, input)
  } catch {
    // Composable exposes the precise API error in-page.
  }
}

async function metadata(input: WorkUpdateInput) {
  try {
    await saveMetadata(input)
  } catch {
    // Composable exposes the precise API error in-page.
  }
}

async function complete(stepId: string, note: string) {
  try {
    await completeStep(stepId, note)
  } catch {
    // Composable exposes the precise API error in-page.
  }
}

async function evidence(input: WorkEvidenceInput) {
  try {
    await saveEvidence(input)
  } catch {
    // Composable exposes the precise API error in-page.
  }
}

async function decision(type: 'accept' | 'request_changes', reason: string) {
  try {
    await decide(type, reason)
  } catch {
    // Composable exposes the precise API error in-page.
  }
}

function shortSha(value: string) {
  return value.slice(0, 10)
}
</script>

<template>
  <section class="work-detail-page">
    <header class="work-detail-heading">
      <div>
        <p class="work-eyebrow">WORK / {{ workId }}</p>
        <h2>{{ work?.title || '正在读取 Work…' }}</h2>
        <p v-if="work">
          <span class="work-state" :class="`status-${work.status}`">{{ statusLabels[work.status] }}</span>
          <span>{{ work.completed_step_count }}/{{ work.step_count }} 步</span>
          <span>{{ work.run_count }} Runs</span>
          <span v-if="hasActiveRun">活跃 Run 增量刷新中</span>
        </p>
      </div>
      <div class="work-heading-actions">
        <RouterLink v-if="work" class="button" :to="`/ai/requirements/${work.requirement_id}`">来源需求</RouterLink>
        <button class="button" type="button" :disabled="loading" @click="load()">刷新</button>
      </div>
    </header>

    <p v-if="error" class="collab-error" role="alert">{{ error }}</p>
    <div v-if="loading && !work" class="panel work-loading">正在读取 Work…</div>

    <template v-else-if="work">
      <section class="work-facts panel">
        <div><span>Owner</span><strong>{{ work.owner_id }}</strong></div>
        <div><span>Reviewer</span><strong>{{ work.reviewer_id }}</strong></div>
        <div><span>固定 Base</span><strong>{{ shortSha(work.base_commit) }}</strong></div>
        <div><span>计划</span><strong>{{ work.plan.recipe_key }}</strong></div>
        <div class="wide"><span>分支</span><strong>{{ work.branch_name }}</strong></div>
        <div class="wide"><span>Worktree</span><strong>{{ work.worktree_path }}</strong></div>
      </section>

      <div class="work-detail-grid">
        <main class="panel work-plan-panel">
          <header class="work-section-heading">
            <div>
              <strong>执行计划</strong>
              <span>顺序 Gate · 每次重试新增 Run</span>
            </div>
            <span>{{ work.plan.status }}</span>
          </header>
          <WorkPlanTimeline
            :steps="work.plan.steps"
            :work-status="work.status"
            :disabled="acting"
            @launch="launch"
            @complete="complete"
          />
        </main>

        <aside class="work-side-stack">
          <section class="panel work-side-panel">
            <header class="work-section-heading">
              <div><strong>责任与时间盒</strong><span>Work 级确定性元数据</span></div>
            </header>
            <WorkMetadataPanel :work="work" :disabled="acting" @save="metadata" />
          </section>

          <section class="panel work-side-panel">
            <header class="work-section-heading">
              <div><strong>交付证据</strong><span>Git 事实 + 人工判断</span></div>
            </header>
            <WorkEvidencePanel
              :evidence="work.latest_evidence"
              :work-status="work.status"
              :disabled="acting"
              @save="evidence"
              @decide="decision"
            />
          </section>

          <section class="panel work-side-panel">
            <header class="work-section-heading">
              <div><strong>人工决定</strong><span>{{ work.decisions.length }} 条，不覆盖历史</span></div>
            </header>
            <div v-if="!work.decisions.length" class="work-no-decisions">尚无交付决定</div>
            <article v-for="item in work.decisions" :key="item.id" class="work-decision">
              <strong>{{ item.decision_type === 'accept' ? '接受交付' : '要求修订' }}</strong>
              <p>{{ item.reason }}</p>
              <small>{{ item.actor_id }} · {{ new Date(item.created_at).toLocaleString('zh-CN') }}</small>
            </article>
          </section>
        </aside>
      </div>
    </template>
  </section>
</template>

<style scoped>
.work-detail-page,
.work-side-stack {
  display: grid;
  gap: 16px;
}

.work-detail-heading,
.work-detail-heading > div > p:last-child,
.work-heading-actions,
.work-section-heading {
  display: flex;
  gap: 10px;
  align-items: center;
}

.work-detail-heading,
.work-section-heading {
  justify-content: space-between;
}

.work-detail-heading h2,
.work-detail-heading p {
  margin: 0;
}

.work-detail-heading h2 {
  margin-top: 3px;
  font-size: 24px;
}

.work-detail-heading > div > p:last-child {
  margin-top: 8px;
  color: var(--color-muted);
  font: 10px var(--font-mono);
}

.work-eyebrow {
  color: var(--color-primary);
  font: 800 10px var(--font-mono);
  letter-spacing: .12em;
}

.work-state {
  padding: 4px 7px;
  border-radius: 3px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 700;
}

.status-accepted {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.status-revision_requested,
.status-cancelled {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.work-loading {
  padding: 60px 20px;
  color: var(--color-muted);
  text-align: center;
}

.work-facts {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  background: var(--color-line-subtle);
}

.work-facts div {
  display: grid;
  min-width: 0;
  gap: 4px;
  padding: 12px 14px;
  background: white;
}

.work-facts .wide {
  grid-column: span 2;
}

.work-facts span {
  color: var(--color-muted);
  font-size: 9px;
}

.work-facts strong {
  overflow: hidden;
  font: 10px var(--font-mono);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(310px, .37fr);
  gap: 14px;
  align-items: start;
}

.work-plan-panel,
.work-side-panel {
  min-width: 0;
  padding: 17px;
}

.work-section-heading {
  min-height: 52px;
  margin: -17px -17px 17px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.work-section-heading > div {
  display: grid;
  gap: 3px;
}

.work-section-heading span {
  color: var(--color-muted);
  font-size: 9px;
}

.work-no-decisions {
  padding: 20px 0;
  color: var(--color-muted);
  text-align: center;
}

.work-decision {
  padding: 11px 0;
  border-bottom: 1px solid var(--color-line-subtle);
}

.work-decision p {
  margin: 5px 0;
  color: var(--color-ink-secondary);
  font-size: 11px;
  line-height: 1.6;
}

.work-decision small {
  color: var(--color-muted);
  font: 9px var(--font-mono);
}

@media (max-width: 1120px) {
  .work-detail-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .work-detail-heading,
  .work-detail-heading > div > p:last-child {
    align-items: flex-start;
    flex-direction: column;
  }

  .work-heading-actions {
    width: 100%;
  }

  .work-heading-actions > * {
    flex: 1;
    justify-content: center;
  }

  .work-facts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
