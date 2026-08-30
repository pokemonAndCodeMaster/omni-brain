<script setup lang="ts">
import { computed } from 'vue'
import type {
  ChartBuilderOptions,
  DashboardChartAxis,
  DashboardChartFilter,
  DashboardChartLayer,
  DashboardChartSplit,
  DashboardMetricReference,
} from '../types'

const props = defineProps<{
  layer: DashboardChartLayer
  axes: DashboardChartAxis[]
  options: ChartBuilderOptions
  index: number
  total: number
}>()

const emit = defineEmits<{
  update: [layer: DashboardChartLayer]
  remove: []
  move: [direction: -1 | 1]
}>()

const selectedMetric = computed(() =>
  props.options.metrics.find((item) => item.id === props.layer.metric.id),
)

const selectedQuestionLabel = computed(
  () =>
    props.layer.splitBy?.questionLabel ??
    props.layer.metric.parameters?.questionLabel ??
    '',
)

const selectedQuestionOptions = computed(
  () =>
    props.options.questionOptions[selectedQuestionLabel.value] ?? [],
)

function patch(value: Partial<DashboardChartLayer>): void {
  emit('update', { ...props.layer, ...value })
}

function updateMetric(metricId: string): void {
  const metric = props.options.metrics.find((item) => item.id === metricId)
  if (!metric) return
  const axis =
    props.axes.find((item) => item.unit === metric.unit) ?? props.axes[0]
  patch({
    metric: { id: metric.id },
    label: metric.label,
    axisId: axis?.id ?? props.layer.axisId,
  })
}

function updateMetricParameters(
  value: Partial<Record<'questionLabel' | 'questionOption', string>>,
): void {
  patch({
    metric: {
      ...props.layer.metric,
      parameters: {
        ...props.layer.metric.parameters,
        ...value,
      },
    },
  })
}

function updateStyle(value: Partial<DashboardChartLayer['style']>): void {
  patch({ style: { ...props.layer.style, ...value } })
}

function updateSplit(value: string): void {
  if (!value) {
    patch({ splitBy: null })
    return
  }
  const split: DashboardChartSplit = {
    dimension: value as DashboardChartSplit['dimension'],
  }
  if (value === 'question-option') {
    const questionLabel =
      Object.keys(props.options.questionOptions)[0] ?? ''
    split.questionLabel = questionLabel
    split.values = props.options.questionOptions[questionLabel]?.slice(0, 8) ?? []
    const optionMetric = props.options.metrics.find(
      (item) => item.requiresQuestionOption,
    )
    if (optionMetric && !selectedMetric.value?.requiresQuestionOption) {
      patch({
        splitBy: split,
        metric: { id: optionMetric.id },
        label: optionMetric.label,
      })
      return
    }
  }
  patch({ splitBy: split })
}

function updateSplitLabel(questionLabel: string): void {
  if (!props.layer.splitBy) return
  patch({
    splitBy: {
      ...props.layer.splitBy,
      questionLabel,
      values: props.options.questionOptions[questionLabel]?.slice(0, 8) ?? [],
    },
  })
}

function toggleSplitOption(option: string, checked: boolean): void {
  if (!props.layer.splitBy) return
  const values = new Set(props.layer.splitBy.values ?? [])
  if (checked) values.add(option)
  else values.delete(option)
  patch({
    splitBy: {
      ...props.layer.splitBy,
      values: [...values],
    },
  })
}

function addFilter(): void {
  const filter: DashboardChartFilter = {
    target: { id: 'project' },
    operator: 'equals',
    value: '',
  }
  patch({ filters: [...props.layer.filters, filter] })
}

function updateFilter(
  index: number,
  value: Partial<DashboardChartFilter>,
): void {
  patch({
    filters: props.layer.filters.map((filter, current) =>
      current === index ? { ...filter, ...value } : filter,
    ),
  })
}

function removeFilter(index: number): void {
  patch({
    filters: props.layer.filters.filter((_, current) => current !== index),
  })
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

function eventValue(event: Event): string {
  return (event.target as HTMLInputElement | HTMLSelectElement).value
}

function eventChecked(event: Event): boolean {
  return (event.target as HTMLInputElement).checked
}
</script>

<template>
  <article class="layer-editor">
    <header class="layer-header">
      <div>
        <span>图层 {{ index + 1 }}</span>
        <strong>{{ layer.label }}</strong>
      </div>
      <div class="layer-actions">
        <button
          type="button"
          :disabled="index === 0"
          aria-label="上移图层"
          @click="emit('move', -1)"
        >
          ↑
        </button>
        <button
          type="button"
          :disabled="index === total - 1"
          aria-label="下移图层"
          @click="emit('move', 1)"
        >
          ↓
        </button>
        <button type="button" aria-label="删除图层" @click="emit('remove')">
          删除
        </button>
      </div>
    </header>

    <div class="field-grid">
      <label>
        <span>统计指标</span>
        <select
          class="select-field"
          :value="layer.metric.id"
          @change="updateMetric(eventValue($event))"
        >
          <option
            v-for="metric in options.metrics"
            :key="metric.id"
            :value="metric.id"
          >
            {{ metric.label }}
          </option>
        </select>
      </label>
      <label>
        <span>图层名称</span>
        <input
          class="field"
          type="text"
          :value="layer.label"
          @input="patch({ label: eventValue($event) })"
        />
      </label>
      <label>
        <span>图形</span>
        <select
          class="select-field"
          :value="layer.renderAs"
          @change="patch({ renderAs: eventValue($event) as DashboardChartLayer['renderAs'] })"
        >
          <option value="bar">柱形</option>
          <option value="line">折线</option>
          <option value="area">面积</option>
        </select>
      </label>
      <label>
        <span>坐标轴</span>
        <select
          class="select-field"
          :value="layer.axisId"
          @change="patch({ axisId: eventValue($event) })"
        >
          <option v-for="axis in axes" :key="axis.id" :value="axis.id">
            {{ axis.label }} · {{ axis.side === 'left' ? '左轴' : '右轴' }}
          </option>
        </select>
      </label>
      <label>
        <span>拆分序列</span>
        <select
          class="select-field"
          :value="layer.splitBy?.dimension ?? ''"
          @change="updateSplit(eventValue($event))"
        >
          <option value="">不拆分</option>
          <option
            v-for="dimension in options.dimensions.filter((item) => item.id !== 'date')"
            :key="dimension.id"
            :value="dimension.id"
          >
            按{{ dimension.label }}
          </option>
        </select>
      </label>
      <label>
        <span>堆叠组</span>
        <input
          class="field"
          type="text"
          :value="layer.stackGroup ?? ''"
          placeholder="留空表示不堆叠"
          @input="patch({ stackGroup: eventValue($event) || null })"
        />
      </label>
    </div>

    <div
      v-if="selectedMetric?.requiresQuestionOption && layer.splitBy?.dimension !== 'question-option'"
      class="field-grid question-config"
    >
      <label>
        <span>问题标签</span>
        <select
          class="select-field"
          :value="layer.metric.parameters?.questionLabel ?? ''"
          @change="updateMetricParameters({
            questionLabel: eventValue($event),
            questionOption: options.questionOptions[eventValue($event)]?.[0] ?? '',
          })"
        >
          <option
            v-for="label in Object.keys(options.questionOptions)"
            :key="label"
            :value="label"
          >
            {{ label }}
          </option>
        </select>
      </label>
      <label>
        <span>问题选项</span>
        <select
          class="select-field"
          :value="layer.metric.parameters?.questionOption ?? ''"
          @change="updateMetricParameters({ questionOption: eventValue($event) })"
        >
          <option
            v-for="option in selectedQuestionOptions"
            :key="option"
            :value="option"
          >
            {{ option }}
          </option>
        </select>
      </label>
    </div>

    <fieldset
      v-if="layer.splitBy?.dimension === 'question-option'"
      class="option-split"
    >
      <legend>问题选项拆分</legend>
      <label>
        <span>问题标签</span>
        <select
          class="select-field"
          :value="layer.splitBy.questionLabel ?? ''"
          @change="updateSplitLabel(eventValue($event))"
        >
          <option
            v-for="label in Object.keys(options.questionOptions)"
            :key="label"
            :value="label"
          >
            {{ label }}
          </option>
        </select>
      </label>
      <div class="option-list">
        <label v-for="option in selectedQuestionOptions" :key="option">
          <input
            type="checkbox"
            :checked="layer.splitBy.values?.includes(option)"
            @change="toggleSplitOption(option, eventChecked($event))"
          />
          <span>{{ option }}</span>
        </label>
      </div>
    </fieldset>

    <section class="layer-filters">
      <header>
        <div>
          <strong>图层筛选</strong>
          <span>只影响当前图层，不改变其他图层和全页范围。</span>
        </div>
        <button type="button" @click="addFilter">＋ 添加筛选</button>
      </header>
      <div
        v-for="(filter, filterIndex) in layer.filters"
        :key="filterIndex"
        class="filter-row"
      >
        <select
          class="select-field"
          :value="filter.target.id"
          @change="updateFilter(filterIndex, { target: { id: eventValue($event) } })"
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
          @change="updateFilter(filterIndex, { operator: eventValue($event) as DashboardChartFilter['operator'] })"
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
          @input="updateFilter(filterIndex, {
            value: parseFilterValue(filter, eventValue($event)),
          })"
        />
        <button type="button" @click="removeFilter(filterIndex)">移除</button>
      </div>
      <p v-if="!layer.filters.length">当前图层继承卡片范围，没有额外筛选。</p>
    </section>

    <div class="style-row">
      <label>
        <span>颜色</span>
        <input
          type="color"
          :value="layer.style.color"
          @input="updateStyle({ color: eventValue($event) })"
        />
      </label>
      <label>
        <input
          type="checkbox"
          :checked="layer.style.showLabels"
          @change="updateStyle({ showLabels: eventChecked($event) })"
        />
        <span>显示数值</span>
      </label>
      <label v-if="layer.renderAs !== 'bar'">
        <input
          type="checkbox"
          :checked="layer.style.smooth"
          @change="updateStyle({ smooth: eventChecked($event) })"
        />
        <span>平滑曲线</span>
      </label>
    </div>
  </article>
</template>

<style scoped>
.layer-editor {
  display: grid;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  background: #fff;
}

.layer-header,
.layer-actions,
.layer-filters header,
.style-row,
.option-list {
  display: flex;
  align-items: center;
}

.layer-header,
.layer-filters header {
  justify-content: space-between;
  gap: 12px;
}

.layer-header > div:first-child,
.layer-filters header > div {
  display: grid;
  gap: 2px;
}

.layer-header span,
.layer-filters span,
.layer-filters p {
  color: var(--color-muted);
  font-size: 10px;
}

.layer-actions,
.style-row,
.option-list {
  gap: 8px;
}

.layer-actions button,
.layer-filters button {
  min-height: 29px;
  padding: 0 9px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: var(--color-surface-subtle);
  color: var(--color-ink-secondary);
  font-size: 10px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.question-config {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field-grid label > span,
.option-split label > span,
.style-row label > span {
  display: block;
  margin-bottom: 4px;
  color: var(--color-ink-secondary);
  font-size: 10px;
  font-weight: 700;
}

.option-split {
  display: grid;
  gap: 9px;
  margin: 0;
  padding: 10px;
  border: 1px solid var(--color-line-subtle);
  border-radius: 4px;
}

.option-list {
  flex-wrap: wrap;
}

.option-list label,
.style-row label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.option-list label > span,
.style-row label > span {
  margin: 0;
  font-weight: 500;
}

.layer-filters {
  display: grid;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid var(--color-line-subtle);
}

.filter-row {
  display: grid;
  grid-template-columns: 1fr 1.25fr 1.4fr auto;
  gap: 7px;
}

.layer-filters p {
  margin: 0;
}

.style-row {
  flex-wrap: wrap;
}

@media (max-width: 800px) {
  .field-grid,
  .question-config,
  .filter-row {
    grid-template-columns: 1fr;
  }
}
</style>
