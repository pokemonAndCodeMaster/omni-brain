<script setup lang="ts">
import { computed, nextTick, reactive, ref, useTemplateRef, watch } from 'vue'
import type {
  ChartBuilderOptions,
  ChartBuilderValue,
  DashboardChartType,
  DashboardOrientation,
  DashboardPalette,
} from '../types'

const props = withDefaults(
  defineProps<{
    open: boolean
    options: ChartBuilderOptions
    defaultTitle: string
    initialValue?: ChartBuilderValue | null
    initialFilters?: Record<string, string>
  }>(),
  {
    initialValue: null,
    initialFilters: () => ({}),
  },
)

const emit = defineEmits<{
  close: []
  submit: [value: ChartBuilderValue]
}>()

const dialog = useTemplateRef<HTMLDialogElement>('dialog')
const form = reactive<ChartBuilderValue>(emptyValue())
const validationMessage = computed(() => {
  if (form.measureIds.length === 0) return '请至少选择一个统计指标。'
  if (!form.sourceId || !form.dimensionId) return '请选择数据源和分组维度。'
  return ''
})

function emptyValue(): ChartBuilderValue {
  return {
    title: props.defaultTitle,
    description: '',
    sourceId: props.options.defaultSourceId,
    chartType: 'bar',
    dimensionId: props.options.defaultDimensionId,
    measureIds: [...props.options.defaultMeasureIds],
    filters: { ...props.initialFilters },
    stacked: false,
    showLegend: true,
    showLabels: false,
    smooth: true,
    palette: 'business',
    orientation: 'vertical',
  }
}

function copyValue(value: ChartBuilderValue): ChartBuilderValue {
  return {
    ...value,
    measureIds: [...value.measureIds],
    filters: { ...value.filters },
  }
}

function resetForm(): void {
  const source = props.initialValue
    ? copyValue(props.initialValue)
    : emptyValue()
  Object.assign(form, source)
  form.measureIds = [...source.measureIds]
  form.filters = { ...source.filters }
}

watch(
  () => props.open,
  async (open) => {
    await nextTick()
    if (open && !dialog.value?.open) {
      resetForm()
      dialog.value?.showModal()
    } else if (!open && dialog.value?.open) {
      dialog.value.close()
    }
  },
  { immediate: true },
)

function close(): void {
  if (dialog.value?.open) {
    dialog.value.close()
  } else {
    emit('close')
  }
}

function submit(): void {
  if (validationMessage.value) return
  emit('submit', {
    ...copyValue(form),
    title: form.title.trim() || props.defaultTitle,
    description: form.description.trim(),
    filters: Object.fromEntries(
      Object.entries(form.filters).filter(([, value]) => value.trim()),
    ),
  })
  close()
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
      <header>
        <div>
          <p>统计卡片配置</p>
          <h2 id="chart-builder-title">
            {{ initialValue ? '编辑统计卡片' : '添加统计卡片' }}
          </h2>
        </div>
        <button type="button" class="close-button" aria-label="关闭" @click="close">
          ×
        </button>
      </header>

      <div class="builder-body">
        <section class="builder-section" aria-labelledby="card-copy-title">
          <div class="section-heading">
            <h3 id="card-copy-title">卡片说明</h3>
            <p>明确这张卡片要回答的业务问题。</p>
          </div>
          <div class="field-row">
            <label>
              <span>卡片标题</span>
              <input v-model="form.title" class="field" type="text" />
            </label>
            <label>
              <span>补充说明</span>
              <input
                v-model="form.description"
                class="field"
                type="text"
                placeholder="例如：同任务内比较，避免跨难度误判"
              />
            </label>
          </div>
        </section>

        <section class="builder-section" aria-labelledby="data-definition-title">
          <div class="section-heading">
            <h3 id="data-definition-title">数据定义</h3>
            <p>保存的是可重新执行的查询条件，页面重开后读取最新快照。</p>
          </div>
          <div class="field-row three-columns">
            <label>
              <span>数据源</span>
              <select v-model="form.sourceId" class="select-field">
                <option
                  v-for="source in options.sources"
                  :key="source.id"
                  :value="source.id"
                >
                  {{ source.label }}
                </option>
              </select>
            </label>
            <label>
              <span>分组维度</span>
              <select v-model="form.dimensionId" class="select-field">
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
              <span>图表类型</span>
              <select
                v-model="form.chartType"
                class="select-field"
              >
                <option value="bar">柱状图</option>
                <option value="line">折线图</option>
                <option value="pie">饼图（单指标）</option>
              </select>
            </label>
          </div>

          <fieldset>
            <legend>统计指标</legend>
            <label
              v-for="measure in options.measures"
              :key="measure.id"
              class="check-option"
            >
              <input
                v-model="form.measureIds"
                type="checkbox"
                :value="measure.id"
              />
              <span>{{ measure.label }}</span>
            </label>
          </fieldset>
        </section>

        <section class="builder-section" aria-labelledby="card-filter-title">
          <div class="section-heading">
            <h3 id="card-filter-title">卡片筛选</h3>
            <p>这些条件只属于当前卡片，不会跟随页面筛选器漂移。</p>
          </div>
          <div class="filter-grid">
            <label v-for="filter in options.filters" :key="filter.id">
              <span>{{ filter.label }}</span>
              <select
                v-if="filter.type === 'select'"
                v-model="form.filters[filter.id]"
                class="select-field"
              >
                <option value="">全部</option>
                <option
                  v-for="option in filter.options"
                  :key="option"
                  :value="option"
                >
                  {{ option }}
                </option>
              </select>
              <input
                v-else
                v-model.trim="form.filters[filter.id]"
                class="field"
                :type="filter.type"
                :placeholder="filter.placeholder"
              />
            </label>
          </div>
        </section>

        <section class="builder-section" aria-labelledby="card-style-title">
          <div class="section-heading">
            <h3 id="card-style-title">呈现方式</h3>
            <p>样式只改变表达，不改变数据口径。</p>
          </div>
          <div class="field-row">
            <label>
              <span>配色</span>
              <select
                v-model="form.palette"
                class="select-field"
              >
                <option value="business">业务蓝</option>
                <option value="quality">质量红绿</option>
                <option value="contrast">高对比</option>
              </select>
            </label>
            <label v-if="form.chartType === 'bar'">
              <span>柱图方向</span>
              <select
                v-model="form.orientation"
                class="select-field"
              >
                <option value="vertical">纵向</option>
                <option value="horizontal">横向</option>
              </select>
            </label>
          </div>
          <fieldset>
            <legend>图形细节</legend>
            <label class="check-option">
              <input v-model="form.showLegend" type="checkbox" />
              <span>显示图例</span>
            </label>
            <label class="check-option">
              <input v-model="form.showLabels" type="checkbox" />
              <span>显示数值标签</span>
            </label>
            <label v-if="form.chartType !== 'pie'" class="check-option">
              <input v-model="form.stacked" type="checkbox" />
              <span>指标堆叠</span>
            </label>
            <label v-if="form.chartType === 'line'" class="check-option">
              <input v-model="form.smooth" type="checkbox" />
              <span>平滑曲线</span>
            </label>
          </fieldset>
        </section>

        <p v-if="validationMessage" class="validation-message" role="alert">
          {{ validationMessage }}
        </p>
      </div>

      <footer>
        <button type="button" class="button" @click="close">取消</button>
        <button type="submit" class="button primary">
          {{ initialValue ? '应用修改' : '添加卡片' }}
        </button>
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.chart-builder {
  width: min(820px, calc(100vw - 28px));
  max-height: min(880px, calc(100vh - 28px));
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

.chart-builder header,
.chart-builder footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
}

.chart-builder header {
  border-bottom: 1px solid var(--color-line);
}

.chart-builder footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-line);
  background: var(--color-surface-subtle);
}

.chart-builder h2,
.chart-builder header p,
.section-heading h3,
.section-heading p,
.validation-message {
  margin: 0;
}

.chart-builder h2 {
  margin-top: 3px;
  font-size: 19px;
}

.chart-builder header p {
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
  gap: 16px;
  padding: 18px;
  overflow: auto;
}

.builder-section {
  display: grid;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.builder-section:last-of-type {
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

.builder-body label > span,
.builder-body legend {
  display: block;
  margin-bottom: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.field-row,
.filter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-row.three-columns {
  grid-template-columns: repeat(3, 1fr);
}

.filter-grid {
  grid-template-columns: repeat(3, 1fr);
}

fieldset {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin: 0;
  padding: 11px 12px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
}

.check-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.check-option span {
  margin: 0 !important;
  font-weight: 500 !important;
}

.check-option input {
  accent-color: var(--color-primary);
}

.validation-message {
  color: var(--color-danger);
  font-size: 11px;
}

@media (max-width: 680px) {
  .field-row,
  .field-row.three-columns,
  .filter-grid {
    grid-template-columns: 1fr;
  }
}
</style>
