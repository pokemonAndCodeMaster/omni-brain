<script setup lang="ts">
import { onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import RequirementEditor from '../components/RequirementEditor.vue'
import { useRequirementList } from '../composables/useRequirementList'
import { emptyRequirementContent, type RequirementContent } from '../types'

const router = useRouter()
const { items, total, loading, error, status, commitment, query, load, create } = useRequirementList()
const createOpen = shallowRef(false)
const creating = shallowRef(false)
const localError = shallowRef('')
const title = shallowRef('')
const content = shallowRef<RequirementContent>(emptyRequirementContent())

onMounted(() => void load())

async function submit() {
  if (!title.value.trim()) return
  creating.value = true
  localError.value = ''
  try {
    const requirement = await create({ title: title.value.trim(), content: content.value })
    await router.push({ name: 'requirement-detail', params: { requirementId: requirement.id } })
  } catch (reason) {
    localError.value = reason instanceof Error ? reason.message : 'Requirement 创建失败'
  } finally {
    creating.value = false
  }
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
}
</script>

<template>
  <section class="collab-page">
    <header class="collab-heading">
      <div>
        <p class="collab-eyebrow">REQUIREMENT PIPELINE</p>
        <h2>候选和正式需求</h2>
        <p>同一 Requirement 从 candidate 走向 accepted；内容变化由不可覆盖的 Revision 承载。</p>
      </div>
      <button class="button primary" type="button" @click="createOpen = !createOpen">直接创建需求</button>
    </header>

    <p v-if="error || localError" class="collab-error" role="alert">{{ error || localError }}</p>

    <section v-if="createOpen" class="panel collab-section create-requirement">
      <header class="section-heading"><strong>新建 candidate Requirement</strong><button class="button" type="button" @click="createOpen = false">收起</button></header>
      <label class="collab-field-label"><span>需求标题</span><input v-model="title" class="field" /></label>
      <RequirementEditor v-model="content" />
      <div class="section-actions"><button class="button primary" type="button" :disabled="creating" @click="submit">创建候选需求</button></div>
    </section>

    <section class="panel collab-panel">
      <header class="collab-toolbar requirement-toolbar">
        <strong>{{ total }} 条需求</strong>
        <div>
          <input v-model="query" class="field" type="search" aria-label="搜索需求标题" placeholder="搜索标题" @keyup.enter="load" />
          <select v-model="status" class="select-field" aria-label="按需求状态筛选" @change="load">
            <option value="">全部状态</option>
            <option value="candidate">candidate</option>
            <option value="accepted">accepted</option>
            <option value="rejected">rejected</option>
            <option value="deferred">deferred</option>
            <option value="merged">merged</option>
          </select>
          <select v-model="commitment" class="select-field" aria-label="按需求承诺筛选" @change="load">
            <option value="">全部承诺</option>
            <option value="NOW">NOW</option>
            <option value="NEXT">NEXT</option>
            <option value="LATER">LATER</option>
          </select>
          <button class="button" type="button" :disabled="loading" @click="load">查询</button>
        </div>
      </header>
      <div class="requirement-list">
        <button v-for="item in items" :key="item.id" type="button" @click="router.push(`/ai/requirements/${item.id}`)">
          <span class="requirement-title"><strong>{{ item.title }}</strong><span :class="`requirement-status status-${item.status}`">{{ item.status }}</span></span>
          <span class="requirement-meta">
            <span>R{{ item.current_revision_no }}</span><span>{{ item.commitment || '未承诺' }}</span><span>{{ item.run_count }} Run</span><span>{{ formatTime(item.updated_at) }}</span>
          </span>
        </button>
        <p v-if="!items.length && !loading" class="collab-loading">尚无 Requirement</p>
      </div>
    </section>
  </section>
</template>
