<script setup lang="ts">
import { computed } from 'vue'
import GongzuoIcon from './GongzuoIcon.vue'
import StatusBadge from './StatusBadge.vue'
import { useGongzuoWorkspace } from '../composables/useGongzuoWorkspace'
import type { WorkItem } from '../types'

const props = defineProps<{ item: WorkItem }>()
const { openModal } = useGongzuoWorkspace()
const proven = computed(() => props.item.evidence.filter((entry) => entry.result === '已证明').length)
</script>

<template>
  <div class="gz-artifact-grid">
    <article v-for="artifact in item.artifacts" :key="artifact.id" class="gz-artifact-card"><div class="gz-inline gz-muted gz-mb-10"><GongzuoIcon name="file" />{{ artifact.kind || '可阅读成果' }}</div><h3>{{ artifact.name }}</h3><p>{{ artifact.summary || '打开查看实际产物与固定版本。' }}</p><button class="gz-btn" type="button" @click="openModal('artifact', { artifact, item })">打开成果</button></article>
    <article v-if="!item.artifacts.length" class="gz-artifact-card"><div class="gz-inline gz-muted gz-mb-10"><GongzuoIcon name="file" />成果</div><h3>尚无成果回传</h3><p>委托运行或手工工作可以把真实产物关联到这里。</p><button class="gz-btn" type="button" @click="openModal('delegate', { item })">委托补充</button></article>
  </div>
  <div class="gz-section-title"><h2>要求与验证证据</h2><StatusBadge value="实际证据" tone="blue" /></div>
  <div class="gz-panel"><div class="gz-table-wrap"><table class="gz-data-table"><thead><tr><th>要证明什么</th><th>为什么要验证</th><th>对应证据</th><th>结论</th></tr></thead><tbody><tr v-for="evidence in item.evidence" :key="evidence.id ?? evidence.name"><td>{{ evidence.name }}</td><td>{{ evidence.purpose }}</td><td><button class="gz-text-btn" type="button" @click="openModal('evidence', { evidence, item })">{{ evidence.source }}</button></td><td><StatusBadge :value="evidence.result" /></td></tr></tbody></table></div><div v-if="!item.evidence.length" class="gz-empty">尚未登记验证证据。</div><div class="gz-panel-body"><div class="gz-between"><span class="gz-small gz-sub">{{ proven }}/{{ item.evidence.length }} 类要求已有证明；数量不代替覆盖说明。</span><button class="gz-btn" type="button" @click="openModal('delegate', { item })"><GongzuoIcon name="spark" />委托补充验证</button></div></div></div>
  <div class="gz-section-title"><h2>接受的是结果，不是一次运行</h2></div>
  <div class="gz-panel pad"><p class="gz-small gz-sub">运行结束不会自动完成事项。责任人确认范围、成果与证据后再接受结果。</p><div class="gz-inline"><button class="gz-btn primary" type="button" :disabled="item.state === '已完成' || item.state === 'accepted'" @click="openModal('accept-result', { item })">接受本轮结果</button><button class="gz-btn" type="button" @click="openModal('feedback', { item, anchor: '成果与验证' })">提出结果反馈</button><StatusBadge v-if="item.state === '已完成' || item.state === 'accepted'" value="已完成" /></div></div>
</template>
