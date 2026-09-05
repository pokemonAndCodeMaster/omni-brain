<script setup lang="ts">
defineProps<{ title: string; subtitle: string; eyebrow?: string }>()
</script>

<template>
  <header class="gz-page-head">
    <div>
      <div v-if="eyebrow" class="gz-eyebrow">{{ eyebrow }}</div>
      <h1>{{ title }}</h1>
      <div class="gz-subtitle">{{ subtitle }}</div>
    </div>
    <div class="gz-inline"><slot /></div>
  </header>
</template>
