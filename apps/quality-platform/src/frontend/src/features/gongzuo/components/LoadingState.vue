<script setup lang="ts">
defineProps<{ error?: string | null; empty?: string; loading?: boolean }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="loading" class="gz-panel gz-empty" role="status">正在读取共作工作区…</div>
  <div v-else-if="error" class="gz-panel gz-empty" role="alert">
    <p>{{ error }}</p>
    <button class="gz-btn" type="button" @click="$emit('retry')">重新读取</button>
  </div>
  <div v-else class="gz-panel gz-empty">{{ empty ?? '这里还没有内容。' }}</div>
</template>
