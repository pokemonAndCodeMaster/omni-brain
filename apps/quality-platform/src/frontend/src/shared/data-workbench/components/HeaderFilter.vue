<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  shallowRef,
  useId,
  useTemplateRef,
} from 'vue'
import type { CSSProperties } from 'vue'
import BaseCheckbox from './BaseCheckbox.vue'
import {
  parseTextSelectionFilter,
  type WorkbenchFilterSpec,
  type WorkbenchTextSelectionFilterValue,
} from '../types'

const props = defineProps<{
  label: string
  spec: WorkbenchFilterSpec
  modelValue: unknown
}>()

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

const open = shallowRef(false)
const root = useTemplateRef<HTMLElement>('root')
const trigger = useTemplateRef<HTMLButtonElement>('trigger')
const panel = useTemplateRef<HTMLElement>('panel')
const firstInput = useTemplateRef<HTMLInputElement>('firstInput')
const panelId = `filter-${useId().replaceAll(':', '')}`
const popoverStyle = shallowRef<CSSProperties>({ visibility: 'hidden' })

const textSelection = computed(() =>
  parseTextSelectionFilter(props.modelValue),
)

const active = computed(() => {
  if (props.spec.type === 'text-select') {
    return Boolean(
      textSelection.value.query.trim() ||
        textSelection.value.selected.length,
    )
  }
  return String(props.modelValue ?? '').length > 0
})

const selectedValues = computed(() =>
  props.spec.type === 'text-select'
    ? textSelection.value.selected
    : String(props.modelValue ?? '').split('\u0000').filter(Boolean),
)

const range = computed(() =>
  String(props.modelValue ?? '').split('\u0000'),
)

const visibleOptions = computed(() => {
  const options = props.spec.options ?? []
  if (props.spec.type !== 'text-select') return options
  const query = textSelection.value.query.trim().toLocaleLowerCase()
  if (!query) return options
  return options.filter((option) =>
    option.toLocaleLowerCase().includes(query),
  )
})

function positionPopover(): void {
  if (!open.value || !trigger.value) return
  const viewportWidth = document.documentElement.clientWidth
  const viewportHeight = document.documentElement.clientHeight
  const margin = 12
  const gap = 8
  const width = Math.max(120, Math.min(320, viewportWidth - margin * 2))
  const anchor = trigger.value.getBoundingClientRect()
  const spaceBelow = viewportHeight - anchor.bottom - margin - gap
  const spaceAbove = anchor.top - margin - gap
  const availableHeight = Math.max(120, Math.max(spaceBelow, spaceAbove))
  const maxHeight = Math.min(
    420,
    availableHeight,
    Math.max(120, viewportHeight - margin * 2),
  )
  const desiredHeight = Math.min(panel.value?.scrollHeight ?? 320, maxHeight)
  const openAbove = spaceBelow < Math.min(desiredHeight, 240) && spaceAbove > spaceBelow
  const top = openAbove
    ? Math.max(margin, anchor.top - gap - desiredHeight)
    : Math.min(anchor.bottom + gap, viewportHeight - margin - desiredHeight)
  const left = Math.min(
    Math.max(margin, anchor.right - width),
    viewportWidth - margin - width,
  )
  popoverStyle.value = {
    top: `${top}px`,
    left: `${left}px`,
    width: `${width}px`,
    maxHeight: `${maxHeight}px`,
    visibility: 'visible',
  }
}

function setOpen(value: boolean): void {
  open.value = value
  if (!value) return
  positionPopover()
  void nextTick().then(() => {
    if (!open.value) return
    positionPopover()
    if (document.visibilityState === 'visible' && document.hasFocus()) {
      firstInput.value?.focus()
    }
  })
}

function emitTextSelection(
  value: WorkbenchTextSelectionFilterValue,
): void {
  const normalized = {
    query: value.query,
    selected: [...new Set(value.selected)],
  }
  emit(
    'update:modelValue',
    normalized.query.trim() || normalized.selected.length
      ? normalized
      : '',
  )
  void nextTick().then(positionPopover)
}

function updateTextQuery(query: string): void {
  emitTextSelection({
    query,
    selected: textSelection.value.selected,
  })
}

function toggleOption(option: string, checked: boolean): void {
  const next = new Set(selectedValues.value)
  if (checked) next.add(option)
  else next.delete(option)
  if (props.spec.type === 'text-select') {
    emitTextSelection({
      query: textSelection.value.query,
      selected: [...next],
    })
    return
  }
  emit('update:modelValue', [...next].join('\u0000'))
}

function setRange(index: number, value: string): void {
  const next = [range.value[0] ?? '', range.value[1] ?? '']
  next[index] = value
  emit('update:modelValue', next.some(Boolean) ? next.join('\u0000') : '')
}

function handlePointerDown(event: PointerEvent): void {
  if (!open.value) return
  const target = event.target as Node
  if (
    !root.value?.contains(target) &&
    !panel.value?.contains(target)
  ) {
    setOpen(false)
  }
}

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && open.value) {
    event.stopPropagation()
    setOpen(false)
    trigger.value?.focus()
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handlePointerDown)
  document.addEventListener('scroll', positionPopover, true)
  document.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', positionPopover)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handlePointerDown)
  document.removeEventListener('scroll', positionPopover, true)
  document.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', positionPopover)
})
</script>

<template>
  <div ref="root" class="header-filter">
    <button
      ref="trigger"
      class="filter-trigger"
      :class="{ active }"
      type="button"
      :aria-label="`${label}${active ? '（已筛选）' : ''}筛选`"
      :aria-controls="panelId"
      :aria-expanded="open"
      @click.stop="setOpen(!open)"
    >
      <svg
        v-if="spec.type === 'text' || spec.type === 'text-select'"
        aria-hidden="true"
        viewBox="0 0 20 20"
      >
        <circle cx="8.5" cy="8.5" r="4.5" />
        <path d="m12 12 4 4" />
        <path v-if="spec.type === 'text-select'" d="M3 17h14" />
      </svg>
      <svg
        v-else-if="spec.type === 'select'"
        aria-hidden="true"
        viewBox="0 0 20 20"
      >
        <path d="M3 5h14M5 10h10M8 15h4" />
      </svg>
      <svg v-else aria-hidden="true" viewBox="0 0 20 20">
        <rect x="3" y="4.5" width="14" height="12.5" rx="2" />
        <path d="M6 3v3M14 3v3M3 8h14" />
      </svg>
      <span v-if="active" class="active-dot" aria-hidden="true" />
    </button>

    <Teleport to="body">
      <div
        v-if="open"
        :id="panelId"
        ref="panel"
        class="filter-popover"
        role="dialog"
        :aria-label="`${label}筛选条件`"
        :style="popoverStyle"
        @click.stop
      >
        <div class="filter-popover-header">
          <div>
            <strong>{{ label }}筛选</strong>
            <small v-if="spec.type === 'text-select'">
              文字包含与精确选择可组合使用
            </small>
          </div>
          <button type="button" @click="setOpen(false)">关闭</button>
        </div>

        <label
          v-if="spec.type === 'text' || spec.type === 'text-select'"
          class="filter-field"
        >
          <span>包含文字</span>
          <input
            ref="firstInput"
            type="search"
            :value="
              spec.type === 'text-select'
                ? textSelection.query
                : String(modelValue ?? '')
            "
            placeholder="输入关键词"
            @input="
              spec.type === 'text-select'
                ? updateTextQuery(($event.target as HTMLInputElement).value)
                : emit(
                    'update:modelValue',
                    ($event.target as HTMLInputElement).value,
                  )
            "
          />
        </label>

        <div
          v-if="spec.type === 'select' || spec.type === 'text-select'"
          class="filter-options"
        >
          <p>
            {{
              spec.type === 'text-select'
                ? '精确选择（可选）'
                : '选择一个或多个值'
            }}
          </p>
          <BaseCheckbox
            v-for="option in visibleOptions"
            :key="option"
            :model-value="selectedValues.includes(option)"
            :label="option"
            @update:model-value="toggleOption(option, $event)"
          />
          <p v-if="!visibleOptions.length" class="empty-options">
            当前没有匹配的可选值
          </p>
        </div>

        <div v-else-if="spec.type === 'date-range'" class="date-range-fields">
          <label class="filter-field">
            <span>起始日期</span>
            <input
              ref="firstInput"
              type="date"
              :value="range[0] ?? ''"
              @input="
                setRange(0, ($event.target as HTMLInputElement).value)
              "
            />
          </label>
          <label class="filter-field">
            <span>截止日期</span>
            <input
              type="date"
              :value="range[1] ?? ''"
              @input="
                setRange(1, ($event.target as HTMLInputElement).value)
              "
            />
          </label>
        </div>

        <div v-else-if="spec.type === 'number-range'" class="date-range-fields">
          <label class="filter-field">
            <span>最小值</span>
            <input
              ref="firstInput"
              type="number"
              inputmode="decimal"
              :value="range[0] ?? ''"
              placeholder="不限"
              @input="
                setRange(0, ($event.target as HTMLInputElement).value)
              "
            />
          </label>
          <label class="filter-field">
            <span>最大值</span>
            <input
              type="number"
              inputmode="decimal"
              :value="range[1] ?? ''"
              placeholder="不限"
              @input="
                setRange(1, ($event.target as HTMLInputElement).value)
              "
            />
          </label>
        </div>

        <div class="filter-actions">
          <button
            type="button"
            :disabled="!active"
            @click="emit('update:modelValue', '')"
          >
            清除条件
          </button>
          <button class="primary-action" type="button" @click="setOpen(false)">
            完成
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.header-filter {
  position: relative;
  flex: none;
}

.filter-trigger {
  position: relative;
  display: grid;
  width: 26px;
  height: 26px;
  place-items: center;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--color-muted);
}

.filter-trigger:hover,
.filter-trigger:focus-visible {
  border-color: var(--color-line);
  background: white;
}

.filter-trigger.active {
  border-color: #b8c8ef;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.filter-trigger svg {
  width: 14px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.7;
}

.active-dot {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 5px;
  height: 5px;
  border: 1px solid white;
  border-radius: 50%;
  background: var(--color-primary);
}

.filter-popover {
  position: fixed;
  z-index: 200;
  display: grid;
  gap: 12px;
  overflow: auto;
  padding: 14px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: white;
  box-shadow: 0 18px 48px rgb(17 24 39 / 22%);
  color: var(--color-ink);
  font-size: 12px;
  font-weight: 400;
}

.filter-popover-header,
.filter-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.filter-popover-header > div {
  display: grid;
  gap: 2px;
}

.filter-popover-header small {
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 400;
}

.filter-popover-header button {
  border: 0;
  background: transparent;
  color: var(--color-primary);
}

.filter-field {
  display: grid;
  gap: 5px;
}

.filter-field span,
.filter-options p {
  margin: 0;
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
}

.filter-field input {
  width: 100%;
  min-height: 34px;
  padding: 5px 8px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
}

.filter-options {
  display: grid;
  max-height: 210px;
  gap: 8px;
  overflow-y: auto;
  padding-right: 4px;
}

.date-range-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.empty-options {
  padding: 8px 0;
}

.filter-actions {
  position: sticky;
  bottom: -14px;
  padding: 10px 0 14px;
  border-top: 1px solid var(--color-line-subtle);
  background: white;
}

.filter-actions button {
  min-height: 30px;
  padding: 4px 9px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
  background: white;
}

.filter-actions button:disabled {
  opacity: 0.45;
}

.filter-actions .primary-action {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: white;
}

@media (max-width: 520px) {
  .date-range-fields {
    grid-template-columns: 1fr;
  }
}
</style>
