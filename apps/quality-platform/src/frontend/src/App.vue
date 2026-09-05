<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from '@/app/components/AppShell.vue'
import GongzuoShell from '@/features/gongzuo/components/GongzuoShell.vue'

const route = useRoute()
const isGongzuo = computed(() => Boolean(route.meta.gongzuo))
</script>

<template>
  <GongzuoShell v-if="isGongzuo" />
  <AppShell v-else />
</template>
