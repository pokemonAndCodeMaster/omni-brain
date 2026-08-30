<script setup lang="ts">
import { nextTick, reactive, shallowRef, useTemplateRef, watch } from 'vue'
import type {
  DashboardJumpTarget,
  DashboardMetricBlock,
  DashboardMetricBreakdownBlock,
  DashboardMetricCard,
  DashboardMetricValueBlock,
} from '../types'

const props = defineProps<{
  open: boolean
  card: DashboardMetricCard | null
  metrics: Array<{
    id: string
    label: string
    unit: 'count' | 'percent'
  }>
}>()

const emit = defineEmits<{
  close: []
  submit: [card: DashboardMetricCard]
}>()

const dialog = useTemplateRef<HTMLDialogElement>('metricEditor')
const jumpEnabled = shallowRef(true)
const form = reactive<DashboardMetricCard>({
  id: '',
  kind: 'metric',
  origin: { type: 'user' },
  title: '',
  description: '',
  query: { scopeMode: 'inherit-page', filters: [] },
  blocks: [],
  action: { type: 'jump', targetCardId: 'annotation-quality' },
  style: {
    accentColor: '#2458d3',
    backgroundColor: '#ffffff',
    textColor: '#17212b',
    titleSize: 15,
    density: 'comfortable',
  },
  layout: { x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
})

function copyCard(card: DashboardMetricCard): DashboardMetricCard {
  return JSON.parse(JSON.stringify(card)) as DashboardMetricCard
}

function resetForm(): void {
  if (!props.card) return
  Object.assign(form, copyCard(props.card))
  form.origin = { ...props.card.origin }
  form.query = JSON.parse(JSON.stringify(props.card.query))
  form.blocks = JSON.parse(JSON.stringify(props.card.blocks))
  form.action = props.card.action ? { ...props.card.action } : null
  form.style = { ...props.card.style }
  form.layout = { ...props.card.layout }
  jumpEnabled.value = Boolean(props.card.action)
}

watch(
  () => props.open,
  async (requestedOpen) => {
    await nextTick()
    if (props.open !== requestedOpen) return
    if (requestedOpen && props.card && !dialog.value?.open) {
      resetForm()
      if (document.visibilityState !== 'visible' || !document.hasFocus()) {
        emit('close')
        return
      }
      dialog.value?.showModal()
    } else if (!requestedOpen && dialog.value?.open) {
      dialog.value.close()
    }
  },
  { immediate: true },
)

function close(): void {
  if (dialog.value?.open) dialog.value.close()
  else emit('close')
}

function blockId(prefix: string): string {
  return `${prefix}-${Date.now()}-${form.blocks.length}`
}

function firstMetric() {
  return props.metrics[0] ?? {
    id: 'annotation.submitted',
    label: '标注提交量',
    unit: 'count' as const,
  }
}

function addMetricBlock(): void {
  const metric = firstMetric()
  form.blocks.push({
    id: blockId('metric'),
    kind: 'metric-value',
    metric: { id: metric.id },
    label: metric.label,
    emphasis: form.blocks.some(
      (block) => block.kind === 'metric-value' && block.emphasis === 'primary',
    )
      ? 'supporting'
      : 'primary',
    width: 'half',
    style: {
      valueSize: 24,
      valueColor: form.style.accentColor,
      labelSize: 10,
      labelColor: '#667085',
    },
  })
}

function addTextBlock(): void {
  form.blocks.push({
    id: blockId('text'),
    kind: 'text',
    content: '补充说明',
    width: 'full',
    style: { fontSize: 11, color: '#667085' },
  })
}

function addBreakdownBlock(): void {
  const metric = firstMetric()
  form.blocks.push({
    id: blockId('breakdown'),
    kind: 'breakdown',
    dimension: 'project',
    metrics: [{ id: metric.id }],
    limit: 8,
    width: 'full',
  })
}

function moveBlock(index: number, offset: -1 | 1): void {
  const target = index + offset
  if (target < 0 || target >= form.blocks.length) return
  const [block] = form.blocks.splice(index, 1)
  if (block) form.blocks.splice(target, 0, block)
}

function removeBlock(index: number): void {
  form.blocks.splice(index, 1)
}

function setEmphasis(
  block: DashboardMetricValueBlock,
  emphasis: 'primary' | 'supporting',
): void {
  if (emphasis === 'primary') {
    for (const candidate of form.blocks) {
      if (candidate.kind === 'metric-value') {
        candidate.emphasis = candidate.id === block.id ? 'primary' : 'supporting'
      }
    }
    return
  }
  block.emphasis = emphasis
}

function syncMetricLabel(block: DashboardMetricValueBlock): void {
  const metric = props.metrics.find((candidate) => candidate.id === block.metric.id)
  if (metric) block.label = metric.label
}

function toggleBreakdownMetric(
  block: DashboardMetricBreakdownBlock,
  metricId: string,
  checked: boolean,
): void {
  if (checked) {
    if (!block.metrics.some((metric) => metric.id === metricId)) {
      block.metrics.push({ id: metricId })
    }
    return
  }
  if (block.metrics.length <= 1) return
  block.metrics = block.metrics.filter((metric) => metric.id !== metricId)
}

function jumpTarget(): DashboardJumpTarget {
  return form.action?.targetCardId ?? 'annotation-quality'
}

function setJumpTarget(target: DashboardJumpTarget): void {
  form.action = { type: 'jump', targetCardId: target }
}

function submit(): void {
  const card = copyCard(form)
  card.title = card.title.trim() || '未命名总览'
  card.description = card.description.trim()
  card.origin = {
    ...card.origin,
    type: 'user',
  }
  card.action = jumpEnabled.value
    ? { type: 'jump', targetCardId: jumpTarget() }
    : null
  emit('submit', card)
  close()
}
</script>

<template>
  <dialog
    ref="metricEditor"
    class="metric-editor"
    aria-labelledby="metric-editor-title"
    @cancel.prevent="close"
    @close="emit('close')"
  >
    <form method="dialog" @submit.prevent="submit">
      <header class="editor-header">
        <div>
          <p>业务总览配置</p>
          <h2 id="metric-editor-title">编辑可组合总览</h2>
        </div>
        <button type="button" class="close-button" aria-label="关闭" @click="close">
          ×
        </button>
      </header>

      <div class="editor-body">
        <section class="editor-section">
          <div class="section-heading">
            <h3>卡片信息</h3>
            <p>总览只保存定义，数据始终按页面当前范围重新计算。</p>
          </div>
          <div class="field-grid">
            <label>
              <span>标题</span>
              <input v-model="form.title" class="field" type="text" />
            </label>
            <label>
              <span>说明</span>
              <input v-model="form.description" class="field" type="text" />
            </label>
            <label>
              <span>点击动作</span>
              <select
                :value="jumpTarget()"
                class="select-field"
                :disabled="!jumpEnabled"
                @change="setJumpTarget(($event.target as HTMLSelectElement).value as DashboardJumpTarget)"
              >
                <option value="annotation-quality">标注数量与质量分布</option>
                <option value="bad-options">Bad 问题排行</option>
                <option value="acceptance-progress">验收分配与完成</option>
                <option value="acceptance-result">验收通过与打回</option>
                <option value="snapshot-detail">逐级明细表</option>
              </select>
            </label>
            <label class="inline-check">
              <input v-model="jumpEnabled" type="checkbox" />
              <span>点击卡片后跳转</span>
            </label>
          </div>
        </section>

        <section class="editor-section">
          <div class="section-heading block-heading">
            <div>
              <h3>内容块</h3>
              <p>按阅读顺序组合指标、说明和一层拆分；最多一个主指标。</p>
            </div>
            <div class="add-actions">
              <button type="button" @click="addMetricBlock">＋ 指标</button>
              <button type="button" @click="addTextBlock">＋ 说明</button>
              <button type="button" @click="addBreakdownBlock">＋ 拆分</button>
            </div>
          </div>

          <div class="block-list">
            <article
              v-for="(block, index) in form.blocks"
              :key="block.id"
              class="block-editor"
            >
              <header class="block-editor-header">
                <strong>
                  {{
                    block.kind === 'metric-value'
                      ? '指标块'
                      : block.kind === 'text'
                        ? '说明块'
                        : '拆分块'
                  }}
                </strong>
                <span>
                  <button
                    type="button"
                    :disabled="index === 0"
                    :aria-label="`上移第 ${index + 1} 个内容块`"
                    @click="moveBlock(index, -1)"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    :disabled="index === form.blocks.length - 1"
                    :aria-label="`下移第 ${index + 1} 个内容块`"
                    @click="moveBlock(index, 1)"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    :aria-label="`删除第 ${index + 1} 个内容块`"
                    @click="removeBlock(index)"
                  >
                    删除
                  </button>
                </span>
              </header>

              <div v-if="block.kind === 'metric-value'" class="block-fields">
                <label>
                  <span>指标</span>
                  <select
                    v-model="block.metric.id"
                    class="select-field"
                    @change="syncMetricLabel(block)"
                  >
                    <option
                      v-for="metric in metrics"
                      :key="metric.id"
                      :value="metric.id"
                    >
                      {{ metric.label }}
                    </option>
                  </select>
                </label>
                <label>
                  <span>显示名称</span>
                  <input v-model="block.label" class="field" type="text" />
                </label>
                <label>
                  <span>重要程度</span>
                  <select
                    :value="block.emphasis"
                    class="select-field"
                    @change="setEmphasis(block, ($event.target as HTMLSelectElement).value as 'primary' | 'supporting')"
                  >
                    <option value="primary">主指标</option>
                    <option value="supporting">辅助指标</option>
                  </select>
                </label>
                <label>
                  <span>宽度</span>
                  <select v-model="block.width" class="select-field">
                    <option value="full">整行</option>
                    <option value="half">二分之一</option>
                    <option value="third">三分之一</option>
                  </select>
                </label>
                <label>
                  <span>数字大小</span>
                  <input v-model.number="block.style.valueSize" class="field" type="number" min="18" max="64" />
                </label>
                <label>
                  <span>数字颜色</span>
                  <input v-model="block.style.valueColor" type="color" />
                </label>
                <label>
                  <span>名称大小</span>
                  <input v-model.number="block.style.labelSize" class="field" type="number" min="9" max="20" />
                </label>
                <label>
                  <span>名称颜色</span>
                  <input v-model="block.style.labelColor" type="color" />
                </label>
              </div>

              <div v-else-if="block.kind === 'text'" class="block-fields">
                <label class="field-wide">
                  <span>说明内容</span>
                  <textarea v-model="block.content" class="field" rows="2" />
                </label>
                <label>
                  <span>宽度</span>
                  <select v-model="block.width" class="select-field">
                    <option value="full">整行</option>
                    <option value="half">二分之一</option>
                    <option value="third">三分之一</option>
                  </select>
                </label>
                <label>
                  <span>字号</span>
                  <input v-model.number="block.style.fontSize" class="field" type="number" min="9" max="24" />
                </label>
                <label>
                  <span>文字颜色</span>
                  <input v-model="block.style.color" type="color" />
                </label>
              </div>

              <div v-else class="block-fields">
                <label>
                  <span>拆分维度</span>
                  <select v-model="block.dimension" class="select-field">
                    <option value="project">项目</option>
                    <option value="task">标注任务</option>
                    <option value="group">组</option>
                  </select>
                </label>
                <label>
                  <span>最多显示</span>
                  <input v-model.number="block.limit" class="field" type="number" min="1" max="30" />
                </label>
                <label>
                  <span>宽度</span>
                  <select v-model="block.width" class="select-field">
                    <option value="full">整行</option>
                    <option value="half">二分之一</option>
                    <option value="third">三分之一</option>
                  </select>
                </label>
                <fieldset class="metric-choices field-wide">
                  <legend>拆分后显示的指标</legend>
                  <label v-for="metric in metrics" :key="metric.id">
                    <input
                      type="checkbox"
                      :checked="block.metrics.some((item) => item.id === metric.id)"
                      @change="toggleBreakdownMetric(block, metric.id, ($event.target as HTMLInputElement).checked)"
                    />
                    <span>{{ metric.label }}</span>
                  </label>
                </fieldset>
              </div>
            </article>
          </div>
        </section>

        <section class="editor-section">
          <div class="section-heading">
            <h3>整卡外观</h3>
            <p>每个指标块的数字和名称样式在内容块中独立设置。</p>
          </div>
          <div class="field-grid color-grid">
            <label>
              <span>重点色</span>
              <input v-model="form.style.accentColor" type="color" />
            </label>
            <label>
              <span>背景色</span>
              <input v-model="form.style.backgroundColor" type="color" />
            </label>
            <label>
              <span>文字色</span>
              <input v-model="form.style.textColor" type="color" />
            </label>
            <label>
              <span>标题大小</span>
              <input v-model.number="form.style.titleSize" class="field" type="number" min="11" max="28" />
            </label>
            <label>
              <span>内容密度</span>
              <select v-model="form.style.density" class="select-field">
                <option value="comfortable">舒展</option>
                <option value="compact">紧凑</option>
              </select>
            </label>
          </div>
        </section>
      </div>

      <footer class="editor-footer">
        <button type="button" class="button" @click="close">取消</button>
        <button type="submit" class="button primary">应用修改</button>
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.metric-editor {
  width: min(900px, calc(100vw - 28px));
  max-height: min(860px, calc(100vh - 28px));
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  color: var(--color-ink);
  box-shadow: 0 24px 70px rgb(17 24 39 / 28%);
}

.metric-editor::backdrop {
  background: rgb(23 32 43 / 35%);
}

.metric-editor form {
  display: grid;
  max-height: inherit;
  grid-template-rows: auto minmax(0, 1fr) auto;
}

.editor-header,
.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
}

.editor-header {
  border-bottom: 1px solid var(--color-line);
}

.editor-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-line);
  background: var(--color-surface-subtle);
}

.editor-header h2,
.editor-header p,
.section-heading h3,
.section-heading p {
  margin: 0;
}

.editor-header h2 {
  margin-top: 3px;
  font-size: 19px;
}

.editor-header p {
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 750;
}

.close-button {
  border: 0;
  background: transparent;
  color: var(--color-muted);
  font-size: 24px;
}

.editor-body {
  display: grid;
  gap: 16px;
  padding: 18px;
  overflow: auto;
}

.editor-section {
  display: grid;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.editor-section:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.section-heading h3 {
  font-size: 13px;
}

.section-heading p {
  margin-top: 3px;
  color: var(--color-muted);
  font-size: 11px;
}

.block-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 12px;
}

.add-actions {
  display: flex;
  gap: 6px;
}

.add-actions button,
.block-editor-header button {
  min-height: 30px;
  padding: 5px 9px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: white;
  color: var(--color-ink);
}

.field-grid,
.block-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-grid label > span,
.block-fields label > span {
  display: block;
  margin-bottom: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.inline-check {
  display: flex;
  align-items: center;
  gap: 7px;
}

.inline-check > span {
  margin: 0 !important;
}

.block-list {
  display: grid;
  gap: 10px;
}

.block-editor {
  display: grid;
  gap: 11px;
  padding: 12px;
  border: 1px solid var(--color-line);
  border-radius: 6px;
  background: var(--color-surface-subtle);
}

.block-editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.block-editor-header > strong {
  font-size: 12px;
}

.block-editor-header > span {
  display: flex;
  gap: 5px;
}

.field-wide {
  grid-column: 1 / -1;
}

.color-grid {
  grid-template-columns: repeat(3, 1fr);
}

.color-grid input[type='color'],
.block-fields input[type='color'] {
  width: 100%;
  min-height: 38px;
  padding: 3px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: white;
}

.metric-choices {
  display: grid;
  max-height: 180px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
  padding: 10px;
  overflow: auto;
  border: 1px solid var(--color-line);
  border-radius: 5px;
  background: white;
}

.metric-choices legend {
  padding: 0 4px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.metric-choices label {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 10px;
}

@media (max-width: 700px) {
  .field-grid,
  .block-fields,
  .color-grid,
  .metric-choices {
    grid-template-columns: 1fr;
  }

  .block-heading {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
