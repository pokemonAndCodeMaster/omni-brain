<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    indeterminate?: boolean
    disabled?: boolean
    label?: string
  }>(),
  {
    indeterminate: false,
    disabled: false,
    label: '',
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const input = ref<HTMLInputElement | null>(null)

function syncIndeterminate() {
  if (input.value) input.value.indeterminate = props.indeterminate
}

onMounted(syncIndeterminate)
watch(() => props.indeterminate, syncIndeterminate)
</script>

<template>
  <label class="checkbox-label">
    <input
      ref="input"
      type="checkbox"
      :checked="modelValue"
      :disabled="disabled"
      @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <span v-if="label">{{ label }}</span>
  </label>
</template>

<style scoped>
.checkbox-label {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
</style>
