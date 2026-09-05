<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: string; tone?: string }>()
const toneClass = computed(() => props.tone ?? ({
  待确认: 'amber', 进行中: 'blue', 待验收: 'purple', 已完成: 'green', 已阻塞: 'red',
  running: 'blue', queued: 'amber', succeeded: 'green', failed: 'red', cancelled: 'amber',
  在线: 'green', 离线: 'red', 已暂停: 'amber', 未验证: 'amber', 已证明: 'green',
  待补证: 'amber', 待发布: 'purple', 已发布: 'green', 已登记: 'blue',
}[props.value] ?? ''))
</script>

<template>
  <span class="gz-tag" :class="toneClass"><slot>{{ value }}</slot></span>
</template>
