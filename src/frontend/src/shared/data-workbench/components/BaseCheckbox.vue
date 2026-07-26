<script setup lang="ts">
import { useTemplateRef, watchEffect } from 'vue'

const props = withDefaults(
  defineProps<{
    label?: string
    indeterminate?: boolean
    disabled?: boolean
  }>(),
  {
    label: '',
    indeterminate: false,
    disabled: false,
  },
)

const model = defineModel<boolean>({ required: true })
const input = useTemplateRef<HTMLInputElement>('input')

watchEffect(() => {
  if (input.value) input.value.indeterminate = props.indeterminate
})
</script>

<template>
  <label class="checkbox">
    <input
      ref="input"
      v-model="model"
      type="checkbox"
      :disabled="disabled"
    />
    <span v-if="label">{{ label }}</span>
  </label>
</template>

<style scoped>
.checkbox {
  display: inline-flex;
  gap: 7px;
  align-items: center;
  min-height: 24px;
  color: var(--color-ink-secondary);
  font-size: 12px;
}

.checkbox input {
  width: 15px;
  height: 15px;
  margin: 0;
  accent-color: var(--color-primary);
}
</style>
