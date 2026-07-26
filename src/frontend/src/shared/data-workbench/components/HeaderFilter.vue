<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, shallowRef, useId, useTemplateRef } from 'vue'
import BaseCheckbox from './BaseCheckbox.vue'
import type { WorkbenchFilterSpec } from '../types'

const props = defineProps<{
  label: string
  spec: WorkbenchFilterSpec
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = shallowRef(false)
const root = useTemplateRef<HTMLElement>('root')
const firstInput = useTemplateRef<HTMLInputElement>('firstInput')
const panelId = `filter-${useId().replaceAll(':', '')}`
const active = computed(() => props.modelValue.length > 0)
const selectedValues = computed(() =>
  props.modelValue.split('\u0000').filter(Boolean),
)
const range = computed(() => props.modelValue.split('\u0000'))

function setOpen(value: boolean): void {
  open.value = value
  if (value) void nextTick(() => firstInput.value?.focus())
}

function toggleOption(option: string, checked: boolean): void {
  const next = new Set(selectedValues.value)
  if (checked) next.add(option)
  else next.delete(option)
  emit('update:modelValue', [...next].join('\u0000'))
}

function setRange(index: number, value: string): void {
  const next = [range.value[0] ?? '', range.value[1] ?? '']
  next[index] = value
  emit('update:modelValue', next.some(Boolean) ? next.join('\u0000') : '')
}

function handlePointerDown(event: PointerEvent): void {
  if (open.value && !root.value?.contains(event.target as Node)) setOpen(false)
}

function handleKeyDown(event: KeyboardEvent): void {
  if (event.key === 'Escape' && open.value) {
    event.stopPropagation()
    setOpen(false)
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handlePointerDown)
  document.addEventListener('keydown', handleKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handlePointerDown)
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div ref="root" class="header-filter">
    <button
      class="filter-trigger"
      :class="{ active }"
      type="button"
      :aria-label="`${label}${active ? '（已筛选）' : ''}筛选`"
      :aria-controls="panelId"
      :aria-expanded="open"
      @click.stop="setOpen(!open)"
    >
      <svg
        v-if="spec.type === 'text'"
        aria-hidden="true"
        viewBox="0 0 20 20"
      >
        <circle cx="8.5" cy="8.5" r="4.5" />
        <path d="m12 12 4 4" />
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

    <div
      v-if="open"
      :id="panelId"
      class="filter-popover"
      role="dialog"
      :aria-label="`${label}筛选条件`"
      @click.stop
    >
      <div class="filter-popover-header">
        <strong>{{ label }}筛选</strong>
        <button type="button" @click="setOpen(false)">关闭</button>
      </div>

      <label v-if="spec.type === 'text'" class="filter-field">
        <span>包含文字</span>
        <input
          ref="firstInput"
          type="search"
          :value="modelValue"
          placeholder="输入关键词"
          @input="
            emit(
              'update:modelValue',
              ($event.target as HTMLInputElement).value,
            )
          "
        />
      </label>

      <div v-else-if="spec.type === 'select'" class="filter-options">
        <p>选择一个或多个值</p>
        <BaseCheckbox
          v-for="option in spec.options ?? []"
          :key="option"
          :model-value="selectedValues.includes(option)"
          :label="option"
          @update:model-value="toggleOption(option, $event)"
        />
        <p v-if="!(spec.options ?? []).length" class="empty-options">
          当前没有可选值
        </p>
      </div>

      <div v-else class="date-range-fields">
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
  position: absolute;
  z-index: 40;
  top: 31px;
  right: 0;
  display: grid;
  width: 250px;
  gap: 12px;
  padding: 12px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: white;
  box-shadow: var(--shadow-md);
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
  min-height: 32px;
  padding: 5px 7px;
  border: 1px solid var(--color-line);
  border-radius: 4px;
}

.filter-options {
  display: grid;
  max-height: 230px;
  gap: 8px;
  overflow-y: auto;
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
  padding-top: 10px;
  border-top: 1px solid var(--color-line-subtle);
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
</style>
