<script setup lang="ts">
import type { SnapshotQuery } from '../types/snapshot'

defineProps<{
  projectOptions: string[]
  sceneOptions: string[]
  loading: boolean
}>()
const model = defineModel<SnapshotQuery>({ required: true })
const emit = defineEmits<{ submit: []; reset: [] }>()
</script>

<template>
  <form class="filters panel" @submit.prevent="emit('submit')">
    <div class="filter-field">
      <label for="date-start">起始日期</label>
      <input id="date-start" v-model="model.stat_date_start" class="field" type="date" />
    </div>
    <div class="filter-field">
      <label for="date-end">截止日期</label>
      <input id="date-end" v-model="model.stat_date_end" class="field" type="date" />
    </div>
    <div class="filter-field">
      <label for="project">项目</label>
      <select id="project" v-model="model.project_name" class="select-field">
        <option value="">全部项目</option>
        <option v-for="project in projectOptions" :key="project" :value="project">
          {{ project }}
        </option>
      </select>
    </div>
    <div class="filter-field">
      <label for="scene">标注任务</label>
      <select id="scene" v-model="model.scene_name" class="select-field">
        <option value="">全部标注任务</option>
        <option v-for="scene in sceneOptions" :key="scene" :value="scene">
          {{ scene }}
        </option>
      </select>
    </div>
    <div class="filter-field">
      <label for="group">组别</label>
      <input
        id="group"
        v-model.trim="model.group_name"
        class="field"
        type="text"
        placeholder="精确组名"
      />
    </div>
    <div class="filter-field">
      <label for="employee">标注员</label>
      <input
        id="employee"
        v-model.trim="model.employee_id"
        class="field"
        type="text"
        placeholder="精确工号"
      />
    </div>
    <div class="filter-actions">
      <button class="button" type="button" :disabled="loading" @click="emit('reset')">
        重置
      </button>
      <button class="button primary" type="submit" :disabled="loading">
        {{ loading ? '查询中…' : '查询快照' }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.filters {
  display: grid;
  min-width: 0;
  grid-template-columns: repeat(6, minmax(120px, 1fr)) auto;
  gap: 12px;
  align-items: end;
  padding: 14px;
}

.filter-field {
  display: grid;
  min-width: 0;
  gap: 5px;
}

.filter-field label {
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 700;
}

.filter-actions {
  display: flex;
  gap: 6px;
}

@media (max-width: 1050px) {
  .filters {
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }
}

@media (max-width: 600px) {
  .filters {
    grid-template-columns: 1fr;
  }
}
</style>
