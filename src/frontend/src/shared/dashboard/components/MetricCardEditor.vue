<script setup lang="ts">
import { nextTick, reactive, useTemplateRef, watch } from 'vue'
import type { DashboardMetricCard } from '../types'

const props = defineProps<{
  open: boolean
  card: DashboardMetricCard | null
}>()

const emit = defineEmits<{
  close: []
  submit: [card: DashboardMetricCard]
}>()

const dialog = useTemplateRef<HTMLDialogElement>('metricEditor')
const form = reactive<DashboardMetricCard>({
  id: '',
  kind: 'metric',
  title: '',
  description: '',
  metricId: 'annotation_quality',
  jumpTarget: 'annotation-quality',
  style: {
    accentColor: '#2458d3',
    backgroundColor: '#ffffff',
    textColor: '#17212b',
    titleSize: 15,
    valueSize: 38,
    density: 'comfortable',
    showProjectBreakdown: true,
  },
  layout: { x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
})

function copyCard(card: DashboardMetricCard): DashboardMetricCard {
  return {
    ...card,
    style: { ...card.style },
    layout: { ...card.layout },
  }
}

function resetForm(): void {
  if (!props.card) return
  Object.assign(form, copyCard(props.card))
  form.style = { ...props.card.style }
  form.layout = { ...props.card.layout }
}

watch(
  () => props.open,
  async (open) => {
    await nextTick()
    if (open && props.card && !dialog.value?.open) {
      resetForm()
      dialog.value?.showModal()
    } else if (!open && dialog.value?.open) {
      dialog.value.close()
    }
  },
  { immediate: true },
)

function close(): void {
  if (dialog.value?.open) dialog.value.close()
  else emit('close')
}

function submit(): void {
  emit('submit', {
    ...copyCard(form),
    title: form.title.trim() || '未命名总览',
    description: form.description.trim(),
  })
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
      <header>
        <div>
          <p>业务总览配置</p>
          <h2 id="metric-editor-title">编辑总览卡片</h2>
        </div>
        <button type="button" class="close-button" aria-label="关闭" @click="close">
          ×
        </button>
      </header>

      <div class="editor-body">
        <section>
          <div class="section-heading">
            <h3>文字与数据</h3>
            <p>卡片始终使用页面顶部选定的周期和范围。</p>
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
              <span>统计内容</span>
              <select v-model="form.metricId" class="select-field">
                <option value="annotation_quality">标注产出与质量构成</option>
                <option value="acceptance_allocation">验收分配</option>
                <option value="acceptance_completion">验收分配与完成</option>
                <option value="acceptance_result">验收通过与打回</option>
              </select>
            </label>
            <label>
              <span>点击后跳转</span>
              <select v-model="form.jumpTarget" class="select-field">
                <option value="annotation-quality">标注数量与质量分布</option>
                <option value="bad-options">Bad 问题排行</option>
                <option value="acceptance-progress">验收分配与完成</option>
                <option value="acceptance-result">验收通过与打回</option>
                <option value="snapshot-detail">逐级明细表</option>
              </select>
            </label>
          </div>
        </section>

        <section>
          <div class="section-heading">
            <h3>颜色与文字大小</h3>
            <p>拖动和缩放直接在总览区操作。</p>
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
              <input
                v-model.number="form.style.titleSize"
                class="field"
                type="number"
                min="11"
                max="28"
              />
            </label>
            <label>
              <span>主数字大小</span>
              <input
                v-model.number="form.style.valueSize"
                class="field"
                type="number"
                min="22"
                max="64"
              />
            </label>
            <label>
              <span>内容密度</span>
              <select v-model="form.style.density" class="select-field">
                <option value="comfortable">舒展</option>
                <option value="compact">紧凑</option>
              </select>
            </label>
          </div>
          <label class="check-option">
            <input v-model="form.style.showProjectBreakdown" type="checkbox" />
            <span>显示各项目拆分</span>
          </label>
        </section>
      </div>

      <footer>
        <button type="button" class="button" @click="close">取消</button>
        <button type="submit" class="button primary">应用修改</button>
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.metric-editor {
  width: min(720px, calc(100vw - 28px));
  max-height: min(780px, calc(100vh - 28px));
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

.metric-editor header,
.metric-editor footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
}

.metric-editor header {
  border-bottom: 1px solid var(--color-line);
}

.metric-editor footer {
  justify-content: flex-end;
  border-top: 1px solid var(--color-line);
  background: var(--color-surface-subtle);
}

.metric-editor h2,
.metric-editor header p,
.section-heading h3,
.section-heading p {
  margin: 0;
}

.metric-editor h2 {
  margin-top: 3px;
  font-size: 19px;
}

.metric-editor header p {
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

.editor-body section {
  display: grid;
  gap: 12px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-line-subtle);
}

.editor-body section:last-child {
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

.field-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.field-grid label > span,
.check-option span {
  display: block;
  margin-bottom: 5px;
  color: var(--color-ink-secondary);
  font-size: 11px;
  font-weight: 700;
}

.color-grid {
  grid-template-columns: repeat(3, 1fr);
}

.color-grid input[type='color'] {
  width: 100%;
  min-height: 38px;
  padding: 3px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: white;
}

.check-option {
  display: flex;
  align-items: center;
  gap: 7px;
}

.check-option span {
  margin: 0;
}

@media (max-width: 620px) {
  .field-grid,
  .color-grid {
    grid-template-columns: 1fr;
  }
}
</style>
