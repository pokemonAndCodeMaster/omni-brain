<script setup lang="ts">
import BaseCheckbox from './BaseCheckbox.vue'
import type { WorkbenchColumnControl } from '../types'

defineProps<{
  rowCount: number
  selectedCount: number
  activeFilterCount: number
  columns: WorkbenchColumnControl[]
  hasExpandedRows: boolean
  analysisEnabled: boolean
  analysisRowCount: number
}>()

const emit = defineEmits<{
  clearFilters: []
  collapseAll: []
  toggleColumn: [payload: { id: string; visible: boolean }]
  moveColumn: [payload: { id: string; direction: -1 | 1 }]
  createChart: []
}>()
</script>

<template>
  <div class="workbench-toolbar">
    <div class="toolbar-group">
      <span class="badge"><strong>{{ rowCount }}</strong>&nbsp;个顶层对象</span>
      <span class="badge">已选择&nbsp;<strong>{{ selectedCount }}</strong>&nbsp;行</span>
      <span v-if="activeFilterCount > 0" class="badge filter-badge">
        {{ activeFilterCount }} 个筛选
        <button type="button" class="link-button" @click="emit('clearFilters')">
          清除
        </button>
      </span>
      <button
        v-if="hasExpandedRows"
        class="button compact"
        type="button"
        @click="emit('collapseAll')"
      >
        折叠已展开行
      </button>
    </div>

    <div class="toolbar-actions">
      <button
        v-if="analysisEnabled"
        class="button compact analysis-button"
        type="button"
        :disabled="analysisRowCount === 0"
        @click="emit('createChart')"
      >
        生成统计卡片
        <small>{{ analysisRowCount }} 行</small>
      </button>

      <details class="column-manager">
        <summary class="button compact">列配置</summary>
        <div class="column-popover">
          <p class="popover-title">显示与顺序</p>
          <div v-for="column in columns" :key="column.id" class="column-row">
            <BaseCheckbox
              :model-value="column.visible"
              :label="column.label"
              @update:model-value="
                emit('toggleColumn', { id: column.id, visible: $event })
              "
            />
            <span class="move-actions">
              <button
                type="button"
                :disabled="!column.canMoveLeft"
                :aria-label="`${column.label} 左移`"
                @click="emit('moveColumn', { id: column.id, direction: -1 })"
              >
                ←
              </button>
              <button
                type="button"
                :disabled="!column.canMoveRight"
                :aria-label="`${column.label} 右移`"
                @click="emit('moveColumn', { id: column.id, direction: 1 })"
              >
                →
              </button>
            </span>
          </div>
        </div>
      </details>
    </div>
  </div>
</template>

<style scoped>
.workbench-toolbar {
  display: flex;
  min-height: 52px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 10px;
  border-bottom: 1px solid var(--color-line);
}

.compact {
  min-height: 28px;
  padding: 4px 8px;
  font-size: 11px;
}

.filter-badge {
  background: var(--color-primary-soft);
  color: #24499f;
}

.link-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-size: 11px;
}

.column-manager {
  position: relative;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.analysis-button {
  border-color: #9fb2e5;
  background: var(--color-primary-soft);
  color: #24499f;
  font-weight: 700;
}

.analysis-button small {
  margin-left: 5px;
  color: var(--color-muted);
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 500;
}

.column-manager summary {
  list-style: none;
}

.column-manager summary::-webkit-details-marker {
  display: none;
}

.column-popover {
  position: absolute;
  z-index: 20;
  top: 36px;
  right: 0;
  width: 290px;
  max-height: 390px;
  overflow: auto;
  padding: 10px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: white;
  box-shadow: var(--shadow-md);
}

.popover-title {
  margin: 0;
  padding: 3px 4px 8px;
  color: var(--color-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.column-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 4px;
  border-top: 1px solid var(--color-line-subtle);
}

.move-actions {
  display: flex;
  gap: 3px;
}

.move-actions button {
  display: grid;
  width: 25px;
  height: 25px;
  place-items: center;
  border: 1px solid var(--color-line);
  border-radius: 3px;
  background: white;
  color: var(--color-muted);
}

.move-actions button:disabled {
  opacity: 0.3;
}

@media (max-width: 720px) {
  .workbench-toolbar {
    align-items: flex-start;
  }
}
</style>
