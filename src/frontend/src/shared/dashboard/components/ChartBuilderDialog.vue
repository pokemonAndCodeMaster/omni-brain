<script setup lang="ts">
import { computed, nextTick, ref, useTemplateRef, watch } from 'vue'
import type {
  ChartBuilderOptions,
  ChartBuilderValue,
  DashboardChartType,
} from '../types'

const props = defineProps<{
  open: boolean
  options: ChartBuilderOptions
  defaultTitle: string
}>()

const emit = defineEmits<{
  close: []
  submit: [value: ChartBuilderValue]
}>()

const dialog = useTemplateRef<HTMLDialogElement>('dialog')
const title = ref(props.defaultTitle)
const chartType = ref<DashboardChartType>('bar')
const dimensionId = ref(props.options.defaultDimensionId)
const measureIds = ref<string[]>([...props.options.defaultMeasureIds])
const validationMessage = computed(() =>
  measureIds.value.length === 0 ? '请至少选择一个统计指标。' : '',
)

watch(
  () => props.open,
  async (open) => {
    await nextTick()
    if (open && !dialog.value?.open) {
      title.value = props.defaultTitle
      dimensionId.value = props.options.defaultDimensionId
      measureIds.value = [...props.options.defaultMeasureIds]
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
    title: title.value.trim() || props.defaultTitle,
    chartType: chartType.value,
    dimensionId: dimensionId.value,
    measureIds: [...measureIds.value],
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
          <p>ANALYSIS BUILDER</p>
          <h2 id="chart-builder-title">添加统计卡片</h2>
        </div>
        <button type="button" class="close-button" aria-label="关闭" @click="close">
          ×
        </button>
      </header>

      <div class="builder-body">
        <label>
          <span>卡片标题</span>
          <input v-model="title" class="field" type="text" />
        </label>

        <div class="field-row">
          <label>
            <span>图表类型</span>
            <select v-model="chartType" class="select-field">
              <option value="bar">柱状图</option>
              <option value="line">折线图</option>
              <option value="pie">饼图（单指标）</option>
            </select>
          </label>
          <label>
            <span>分组维度</span>
            <select v-model="dimensionId" class="select-field">
              <option
                v-for="dimension in options.dimensions"
                :key="dimension.id"
                :value="dimension.id"
              >
                {{ dimension.label }}
              </option>
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
            <input v-model="measureIds" type="checkbox" :value="measure.id" />
            <span>{{ measure.label }}</span>
          </label>
        </fieldset>

        <p v-if="validationMessage" class="validation-message" role="alert">
          {{ validationMessage }}
        </p>
        <p class="builder-note">
          当前卡片使用页面已加载的数据；保存布局和跨会话恢复将在后续切片接入。
        </p>
      </div>

      <footer>
        <button type="button" class="button" @click="close">取消</button>
        <button type="submit" class="button primary">添加卡片</button>
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.chart-builder {
  width: min(560px, calc(100vw - 28px));
  padding: 0;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  color: var(--color-ink);
  box-shadow: 0 24px 70px rgb(17 24 39 / 28%);
}

.chart-builder::backdrop {
  background: rgb(23 32 43 / 35%);
}

.chart-builder header,
.chart-builder footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
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
.builder-note,
.validation-message {
  margin: 0;
}

.chart-builder h2 {
  margin-top: 3px;
  font-size: 18px;
}

.chart-builder header p {
  color: var(--color-primary);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.08em;
}

.close-button {
  border: 0;
  background: transparent;
  color: var(--color-muted);
  font-size: 24px;
}

.builder-body {
  display: grid;
  gap: 15px;
  padding: 17px 16px;
}

.builder-body label > span,
.builder-body legend {
  display: block;
  margin-bottom: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
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

.builder-note {
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.55;
}

@media (max-width: 560px) {
  .field-row {
    grid-template-columns: 1fr;
  }
}
</style>
