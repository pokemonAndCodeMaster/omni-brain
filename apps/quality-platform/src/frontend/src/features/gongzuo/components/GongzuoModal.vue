<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, useTemplateRef } from 'vue'
import GongzuoIcon from './GongzuoIcon.vue'

withDefaults(defineProps<{ title: string; wide?: boolean }>(), { wide: false })
const emit = defineEmits<{ close: [] }>()
const panel = useTemplateRef<HTMLElement>('panel')
const returnTarget = document.activeElement instanceof HTMLElement ? document.activeElement : null
const focusableSelector = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('close')
    return
  }
  if (event.key !== 'Tab' || !panel.value) return
  const focusable = [...panel.value.querySelectorAll<HTMLElement>(focusableSelector)].filter((element) => !element.hidden)
  if (!focusable.length) { event.preventDefault(); panel.value.focus(); return }
  const first = focusable[0]
  const last = focusable.at(-1)
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
}

onMounted(async () => {
  await nextTick()
  const preferred = panel.value?.querySelector<HTMLElement>('[autofocus]')
    ?? panel.value?.querySelector<HTMLElement>('.gz-modal-body')?.querySelector<HTMLElement>(focusableSelector)
    ?? panel.value?.querySelector<HTMLElement>(focusableSelector)
  ;(preferred ?? panel.value)?.focus()
})
onBeforeUnmount(() => returnTarget?.focus())
</script>

<template>
  <div class="gz-modal-backdrop" role="presentation" @mousedown.self="$emit('close')">
    <section ref="panel" class="gz-modal" :class="{ wide }" role="dialog" aria-modal="true" :aria-label="title" tabindex="-1" @keydown="onKeydown">
      <header class="gz-modal-head">
        <h2>{{ title }}</h2>
        <button class="gz-btn ghost icon-only" type="button" aria-label="关闭弹窗" @click="$emit('close')"><GongzuoIcon name="close" /></button>
      </header>
      <div class="gz-modal-body"><slot /></div>
      <footer v-if="$slots.footer" class="gz-modal-foot"><slot name="footer" /></footer>
    </section>
  </div>
</template>
