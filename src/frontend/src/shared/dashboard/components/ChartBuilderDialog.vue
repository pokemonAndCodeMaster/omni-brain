<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  reactive,
  shallowRef,
  useTemplateRef,
  watch,
} from 'vue'
import ChartLayerEditor from './ChartLayerEditor.vue'
import ChartVisualization from './ChartVisualization.vue'
import type {
  ChartBuilderOptions,
  DashboardCardResolver,
  DashboardChartAxis,
  DashboardChartCard,
  DashboardChartFilter,
  DashboardChartLayer,
  DashboardChartResult,
} from '../types'

const props = defineProps<{
  open: boolean
  card: DashboardChartCard | null
  options: ChartBuilderOptions
  mode: 'create' | 'edit'
  previewResolver: DashboardCardResolver
}>()

const emit = defineEmits<{
  close: []
  submit: [card: DashboardChartCard]
}>()

const dialog = useTemplateRef<HTMLDialogElement>('dialog')
const form = reactive<DashboardChartCard>(emptyCard())
const preview = shallowRef<DashboardChartResult | null>(null)
const previewLoading = shallowRef(false)
const previewError = shallowRef('')
let previewSequence = 0
let previewTimer: number | null = null

function emptyCard(): DashboardChartCard {
  return {
    id: '',
    kind: 'chart',
    origin: { type: 'user' },
    title: '',
    description: '',
    baseQuery: {
      sourceId: props.options.sourceId,
      scopeMode: 'inherit-page',
      categoryDimension: 'task',
      timeGrain: null,
      questionLabels: [],
      filters: [],
    },
    axes: [
      {
        id: 'count-axis',
        side: 'left',
        unit: 'count',
        label: '数量',
        minimum: 0,
        maximum: null,
      },
      {
        id: 'rate-axis',
        side: 'right',
        unit: 'percent',
        label: '占比',
        minimum: 0,
        maximum: 100,
      },
    ],
    layers: [],
    presentation: {
      showLegend: true,
      legendPosition: 'top',
      categorySort: 'natural',
      categoryLimit: 20,
      orientation: 'vertical',
      fontScale: 'medium',
    },
    layout: { x: 0, y: 0, w: 6, h: 7, minW: 4, minH: 5 },
  }
}

function copyCard(card: DashboardChartCard): DashboardChartCard {
  return JSON.parse(JSON.stringify(card)) as DashboardChartCard
}

function resetForm(): void {
  if (!props.card) return
  Object.assign(form, copyCard(props.card))
  form.origin = { ...props.card.origin }
  form.baseQuery = copyCard(props.card).baseQuery
  form.axes = props.card.axes.map((axis) => ({ ...axis }))
  form.layers = copyCard(props.card).layers
  form.presentation = { ...props.card.presentation }
  form.layout = { ...props.card.layout }
}

const validationMessage = computed(() => {
  if (!form.title.trim()) return '请填写卡片名称。'
  if (!form.axes.length) return '请至少保留一个坐标轴。'
  if (!form.layers.length) return '请至少添加一个图层。'
  if (form.layers.length > 8) return '一张卡片最多包含 8 个图层。'
  const axisIds = new Set(form.axes.map((axis) => axis.id))
  if (form.layers.some((layer) => !axisIds.has(layer.axisId))) {
    return '有图层引用了不存在的坐标轴。'
  }
  if (
    form.baseQuery.categoryDimension === 'question-option' &&
    form.layers.some((item) => !item.metric.id.startsWith('option.'))
  ) {
    return '问题选项横轴只能使用问题选项指标。'
  }
  const invalidQuestionMetric = form.layers.some((item) => {
    const metric = props.options.metrics.find(
      (candidate) => candidate.id === item.metric.id,
    )
    if (!metric?.requiresQuestionOption) return false
    if (item.splitBy?.dimension === 'question-option') {
      return !item.splitBy.questionLabel || !item.splitBy.values?.length
    }
    return !item.metric.parameters?.questionLabel ||
      !item.metric.parameters?.questionOption
  })
  if (invalidQuestionMetric) return '问题选项指标缺少问题标签或问题选项。'
  const emptyFilter = [
    ...form.baseQuery.filters,
    ...form.layers.flatMap((item) => item.filters),
  ].some((item) =>
    Array.isArray(item.value) ? !item.value.length : item.value === '',
  )
  return emptyFilter ? '筛选条件不能为空，请填写或移除空条件。' : ''
})

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

watch(
  () => JSON.stringify([props.open, form]),
  () => {
    if (previewTimer != null) window.clearTimeout(previewTimer)
    if (!props.open || validationMessage.value) {
      preview.value = null
      previewError.value = ''
      previewLoading.value = false
      return
    }
    previewTimer = window.setTimeout(() => {
      void resolvePreview()
    }, 280)
  },
)

onBeforeUnmount(() => {
  if (previewTimer != null) window.clearTimeout(previewTimer)
})

async function resolvePreview(): Promise<void> {
  const sequence = ++previewSequence
  previewLoading.value = true
  previewError.value = ''
  try {
    const result = await props.previewResolver(copyCard(form))
    if (sequence === previewSequence) preview.value = result
  } catch (error) {
    if (sequence !== previewSequence) return
    preview.value = null
    previewError.value =
      error instanceof Error ? error.message : '图表预览生成失败。'
  } finally {
    if (sequence === previewSequence) previewLoading.value = false
  }
}

function close(): void {
  if (dialog.value?.open) dialog.value.close()
  else emit('close')
}

function submit(): void {
  if (validationMessage.value) return
  const result = copyCard(form)
  result.title = result.title.trim()
  result.description = result.description.trim()
  result.origin = {
    ...result.origin,
    type: 'user',
  }
  emit('submit', result)
  close()
}

function eventValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLSelectElement).value
}

function eventChecked(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}

function updateAxis(
  axisId: string,
  value: Partial<DashboardChartAxis>,
): void {
  form.axes = form.axes.map((axis) =>
    axis.id === axisId ? { ...axis, ...value } : axis,
  )
}

function numberOrNull(value: string): number | null {
  if (!value.trim()) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function layerId(): string {
  return `layer-${Date.now()}-${form.layers.length + 1}`
}

function addLayer(): void {
  if (form.layers.length >= 8) return
  const metric =
    props.options.metrics.find((item) => !item.requiresQuestionOption) ??
    props.options.metrics[0]
  if (!metric) return
  const axis = form.axes.find((item) => item.unit === metric.unit) ?? form.axes[0]
  const next: DashboardChartLayer = {
    id: layerId(),
    label: metric.label,
    metric: { id: metric.id },
    renderAs: metric.unit === 'percent' ? 'line' : 'bar',
    axisId: axis?.id ?? '',
    splitBy: null,
    filters: [],
    stackGroup: null,
    style: {
      color: ['#315fc4', '#268462', '#d5535d', '#d48a2f'][
        form.layers.length % 4
      ]!,
      smooth: true,
      showLabels: false,
    },
  }
  form.layers = [...form.layers, next]
}

function updateLayer(index: number, layer: DashboardChartLayer): void {
  form.layers = form.layers.map((current, currentIndex) =>
    currentIndex === index ? layer : current,
  )
}

function removeLayer(index: number): void {
  form.layers = form.layers.filter((_, current) => current !== index)
}

function moveLayer(index: number, direction: -1 | 1): void {
  const target = index + direction
  if (target < 0 || target >= form.layers.length) return
  const next = [...form.layers]
  const [layer] = next.splice(index, 1)
  if (layer) next.splice(target, 0, layer)
  form.layers = next
}

function setCategoryDimension(value: string): void {
  form.baseQuery.categoryDimension =
    value as DashboardChartCard['baseQuery']['categoryDimension']
  form.baseQuery.timeGrain = value === 'date' ? 'day' : null
  if (value !== 'question-option') return
  const optionMetric = props.options.metrics.find(
    (item) => item.requiresQuestionOption,
  )
  if (!optionMetric) return
  form.layers = form.layers.map((current, index) => ({
    ...current,
    label: index === 0 ? optionMetric.label : current.label,
    metric:
      index === 0 ? { id: optionMetric.id } : current.metric,
  }))
}

function toggleQuestionLabel(label: string, checked: boolean): void {
  const values = new Set(form.baseQuery.questionLabels)
  if (checked) values.add(label)
  else values.delete(label)
  form.baseQuery.questionLabels = [...values]
}

function addBaseFilter(): void {
  form.baseQuery.filters = [
    ...form.baseQuery.filters,
    {
      target: { id: 'project' },
      operator: 'equals',
      value: '',
    },
  ]
}

function updateBaseFilter(
  index: number,
  value: Partial<DashboardChartFilter>,
): void {
  form.baseQuery.filters = form.baseQuery.filters.map((filter, current) =>
    current === index ? { ...filter, ...value } : filter,
  )
}

function removeBaseFilter(index: number): void {
  form.baseQuery.filters = form.baseQuery.filters.filter(
    (_, current) => current !== index,
  )
}

function filterInputValue(filter: DashboardChartFilter): string {
  return Array.isArray(filter.value)
    ? filter.value.join(',')
    : String(filter.value ?? '')
}

function parseFilterValue(
  filter: DashboardChartFilter,
  value: string,
): DashboardChartFilter['value'] {
  if (filter.operator === 'in' || filter.operator === 'between') {
    return value.split(',').map((item) => item.trim()).filter(Boolean)
  }
  return value
}
</script>

<template>
  <dialog
    ref="dialog"
    class="chart-builder"
    aria-labelledby="chart-builder-title"
    @cancel.prevent="close"
    @close="emit('close')"
  >
    <form method="dialog" @submit.prevent="submit">
      <header class="builder-header">
        <div>
          <p>多图层统计卡片</p>
          <h2 id="chart-builder-title">
            {{ mode === 'edit' ? '编辑统计卡片' : '添加统计卡片' }}
          </h2>
        </div>
        <button type="button" class="close-button" aria-label="关闭" @click="close">
          ×
        </button>
      </header>

      <div class="builder-body">
        <div class="configuration-column">
          <section class="builder-section">
          <div class="section-heading">
            <h3>卡片说明</h3>
            <p>先说明业务问题，再配置横轴和各个数据图层。</p>
          </div>
          <div class="field-row">
            <label>
              <span>卡片标题</span>
              <input v-model="form.title" class="field" type="text" />
            </label>
            <label>
              <span>补充说明</span>
              <input v-model="form.description" class="field" type="text" />
            </label>
          </div>
          </section>

          <section class="builder-section">
          <div class="section-heading">
            <h3>横轴与卡片范围</h3>
            <p>所有图层共享横轴，并继承页面顶部的日期、项目、任务、组和标注员范围。</p>
          </div>
          <div class="field-row three-columns">
            <label>
              <span>横轴维度</span>
              <select
                class="select-field"
                :value="form.baseQuery.categoryDimension"
                @change="setCategoryDimension(eventValue($event))"
              >
                <option
                  v-for="dimension in options.dimensions"
                  :key="dimension.id"
                  :value="dimension.id"
                >
                  {{ dimension.label }}
                </option>
              </select>
            </label>
            <label>
              <span>分类排序</span>
              <select v-model="form.presentation.categorySort" class="select-field">
                <option value="natural">名称 / 日期顺序</option>
                <option value="value-desc">按首个图层倒排</option>
              </select>
            </label>
            <label>
              <span>最多显示分类</span>
              <input
                v-model.number="form.presentation.categoryLimit"
                class="field"
                type="number"
                min="0"
                max="200"
              />
            </label>
          </div>
          <fieldset
            v-if="form.baseQuery.categoryDimension === 'question-option'"
            class="question-labels"
          >
            <legend>问题标签范围</legend>
            <label
              v-for="label in Object.keys(options.questionOptions)"
              :key="label"
            >
              <input
                type="checkbox"
                :checked="form.baseQuery.questionLabels.includes(label)"
                @change="toggleQuestionLabel(label, eventChecked($event))"
              />
              <span>{{ label }}</span>
            </label>
            <small>不选择时读取当前范围内的全部问题标签。</small>
          </fieldset>

          <div class="base-filters">
            <header>
              <div>
                <strong>卡片公共筛选</strong>
                <span>先继承全页范围，再对所有图层追加这些条件。</span>
              </div>
              <button type="button" @click="addBaseFilter">＋ 添加筛选</button>
            </header>
            <div
              v-for="(filter, index) in form.baseQuery.filters"
              :key="index"
              class="filter-row"
            >
              <select
                class="select-field"
                :value="filter.target.id"
                @change="updateBaseFilter(index, { target: { id: eventValue($event) } })"
              >
                <option
                  v-for="dimension in options.dimensions.filter((item) => item.id !== 'question-option')"
                  :key="dimension.id"
                  :value="dimension.id"
                >
                  {{ dimension.label }}
                </option>
              </select>
              <select
                class="select-field"
                :value="filter.operator"
                @change="updateBaseFilter(index, { operator: eventValue($event) as DashboardChartFilter['operator'] })"
              >
                <option value="equals">等于</option>
                <option value="in">属于（逗号分隔）</option>
                <option value="contains">包含文字</option>
                <option value="between">范围（逗号分隔）</option>
              </select>
              <input
                class="field"
                type="text"
                :value="filterInputValue(filter)"
                @input="updateBaseFilter(index, {
                  value: parseFilterValue(filter, eventValue($event)),
                })"
              />
              <button type="button" @click="removeBaseFilter(index)">移除</button>
            </div>
          </div>
          </section>

          <section class="builder-section">
          <div class="section-heading">
            <h3>坐标轴</h3>
            <p>数量与比例使用独立坐标轴，避免数值量级不同导致折线被压扁。</p>
          </div>
          <div class="axis-grid">
            <article v-for="axis in form.axes" :key="axis.id">
              <strong>{{ axis.unit === 'count' ? '数量轴' : '比例轴' }}</strong>
              <label>
                <span>名称</span>
                <input
                  class="field"
                  type="text"
                  :value="axis.label"
                  @input="updateAxis(axis.id, { label: eventValue($event) })"
                />
              </label>
              <label>
                <span>位置</span>
                <select
                  class="select-field"
                  :value="axis.side"
                  @change="updateAxis(axis.id, { side: eventValue($event) as DashboardChartAxis['side'] })"
                >
                  <option value="left">左侧</option>
                  <option value="right">右侧</option>
                </select>
              </label>
              <label>
                <span>最小值</span>
                <input
                  class="field"
                  type="number"
                  :value="axis.minimum ?? ''"
                  @input="updateAxis(axis.id, { minimum: numberOrNull(eventValue($event)) })"
                />
              </label>
              <label>
                <span>最大值</span>
                <input
                  class="field"
                  type="number"
                  :value="axis.maximum ?? ''"
                  @input="updateAxis(axis.id, { maximum: numberOrNull(eventValue($event)) })"
                />
              </label>
            </article>
          </div>
          </section>

          <section class="builder-section">
          <div class="section-heading inline-heading">
            <div>
              <h3>数据图层</h3>
              <p>每个图层独立选择指标、图形、坐标轴、拆分维度、筛选和样式。</p>
            </div>
            <button
              type="button"
              class="button"
              :disabled="form.layers.length >= 8"
              @click="addLayer"
            >
              ＋ 添加图层
            </button>
          </div>
          <div class="layer-list">
            <ChartLayerEditor
              v-for="(layer, index) in form.layers"
              :key="layer.id"
              :layer="layer"
              :axes="form.axes"
              :options="options"
              :index="index"
              :total="form.layers.length"
              @update="updateLayer(index, $event)"
              @remove="removeLayer(index)"
              @move="moveLayer(index, $event)"
            />
          </div>
          </section>

          <section class="builder-section">
          <div class="section-heading">
            <h3>整体呈现</h3>
            <p>这些设置只改变表达方式，不改变指标口径。</p>
          </div>
          <div class="field-row three-columns">
            <label>
              <span>图例位置</span>
              <select v-model="form.presentation.legendPosition" class="select-field">
                <option value="top">顶部</option>
                <option value="bottom">底部</option>
              </select>
            </label>
            <label>
              <span>图表方向</span>
              <select v-model="form.presentation.orientation" class="select-field">
                <option value="vertical">纵向柱 / 横轴分类</option>
                <option value="horizontal">横向柱 / 纵轴分类</option>
              </select>
            </label>
            <label>
              <span>文字大小</span>
              <select v-model="form.presentation.fontScale" class="select-field">
                <option value="small">紧凑</option>
                <option value="medium">标准</option>
                <option value="large">醒目</option>
              </select>
            </label>
          </div>
          <label class="check-option">
            <input v-model="form.presentation.showLegend" type="checkbox" />
            <span>显示图例</span>
          </label>
          </section>
        </div>

        <aside class="builder-section preview-section">
          <div class="section-heading">
            <h3>实时预览与聚合数据</h3>
            <p>预览执行当前定义，下面的数据表可区分统计口径问题与图形表达问题。</p>
          </div>
          <div v-if="validationMessage" class="preview-state is-error" role="alert">
            {{ validationMessage }}
          </div>
          <div v-else-if="previewLoading" class="preview-state" role="status">
            正在生成最新预览…
          </div>
          <div v-else-if="previewError" class="preview-state is-error" role="alert">
            {{ previewError }}
          </div>
          <ChartVisualization
            v-else-if="preview"
            :card="form"
            :result="preview"
            preview
          />
        </aside>
      </div>

      <footer class="builder-footer">
        <button type="button" class="button" @click="close">取消</button>
        <button type="submit" class="button primary" :disabled="Boolean(validationMessage)">
          {{ mode === 'edit' ? '应用修改' : '添加卡片' }}
        </button>
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.chart-builder {
  width: min(1180px, calc(100vw - 28px));
  max-height: min(940px, calc(100vh - 28px));
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  color: var(--color-ink);
  box-shadow: 0 24px 70px rgb(17 24 39 / 28%);
}

.chart-builder::backdrop {
  background: rgb(23 32 43 / 35%);
}

.chart-builder form {
  display: grid;
  max-height: inherit;
  grid-template-rows: auto minmax(0, 1fr) auto;
}

.builder-header,
.builder-footer,
.inline-heading,
.base-filters header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.builder-header,
.builder-footer {
  padding: 14px 18px;
}

.builder-header {
  border-bottom: 1px solid var(--color-line);
}

.builder-footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-line);
  background: var(--color-surface-subtle);
}

.builder-header h2,
.builder-header p,
.section-heading h3,
.section-heading p {
  margin: 0;
}

.builder-header h2 {
  margin-top: 3px;
  font-size: 19px;
}

.builder-header p {
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

.builder-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(340px, 410px);
  align-items: start;
  gap: 18px;
  padding: 18px;
  overflow: auto;
}

.configuration-column {
  display: grid;
  min-width: 0;
  gap: 18px;
}

.builder-section {
  display: grid;
  gap: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.section-heading h3 {
  font-size: 13px;
}

.section-heading p,
.base-filters header span {
  margin-top: 3px;
  color: var(--color-muted);
  font-size: 11px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-row.three-columns {
  grid-template-columns: repeat(3, 1fr);
}

.builder-body label > span,
.builder-body legend {
  display: block;
  margin-bottom: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.question-labels {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin: 0;
  padding: 11px 12px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
}

.question-labels label,
.check-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.question-labels label > span,
.check-option > span {
  margin: 0;
  font-weight: 500;
}

.question-labels small {
  flex-basis: 100%;
  color: var(--color-muted);
}

.base-filters {
  display: grid;
  gap: 8px;
  padding: 11px;
  border: 1px solid var(--color-line-subtle);
  border-radius: var(--radius-sm);
  background: var(--color-surface-subtle);
}

.base-filters header > div {
  display: grid;
}

.base-filters button,
.filter-row button {
  min-height: 30px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: #fff;
  color: var(--color-ink-secondary);
  font-size: 10px;
}

.filter-row {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1.5fr auto;
  gap: 7px;
}

.axis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.axis-grid article {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 11px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
}

.axis-grid article > strong {
  grid-column: 1 / -1;
  font-size: 11px;
}

.layer-list {
  display: grid;
  gap: 10px;
}

.preview-section {
  position: sticky;
  top: 0;
  max-height: calc(100vh - 190px);
  padding: 12px;
  border-bottom: 0;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  overflow: auto;
  background: #fff;
}

.preview-state {
  display: grid;
  min-height: 120px;
  place-items: center;
  border: 1px dashed var(--color-line);
  border-radius: var(--radius-sm);
  color: var(--color-muted);
  font-size: 11px;
}

.preview-state.is-error {
  color: var(--color-danger);
}

@media (max-width: 1000px) {
  .builder-body {
    grid-template-columns: 1fr;
  }

  .preview-section {
    position: static;
    max-height: none;
  }
}

@media (max-width: 820px) {
  .field-row,
  .field-row.three-columns,
  .axis-grid,
  .filter-row {
    grid-template-columns: 1fr;
  }

  .axis-grid article {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
