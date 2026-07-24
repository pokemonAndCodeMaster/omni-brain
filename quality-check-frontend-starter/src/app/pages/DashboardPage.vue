<script setup lang="ts">
import { ref } from 'vue'
import DashboardGrid from '@/shared/dashboard/components/DashboardGrid.vue'
import { useDashboardStore } from '@/shared/dashboard/stores/dashboard'

const dashboard = useDashboardStore()
const editMode = ref(false)
</script>

<template>
  <div>
    <div class="page-toolbar">
      <div>
        <h2 style="margin: 0">可配置卡片看板</h2>
        <p class="help-text" style="margin: 6px 0 0">
          图表和布局保存在浏览器 localStorage。进入交付中心可以从当前筛选结果创建新图表卡片。
        </p>
      </div>
      <div class="toolbar-group">
        <span class="badge">{{ dashboard.cardCount }} 张卡片</span>
        <button class="button" type="button" @click="dashboard.addTextCard">新增备注卡片</button>
        <button class="button" type="button" @click="dashboard.resetDashboard">恢复默认</button>
        <button class="button primary" type="button" @click="editMode = !editMode">
          {{ editMode ? '完成布局编辑' : '编辑布局' }}
        </button>
      </div>
    </div>

    <DashboardGrid
      :cards="dashboard.cards"
      :edit-mode="editMode"
      @layout-change="dashboard.updateLayouts"
      @remove="dashboard.removeCard"
      @duplicate="dashboard.duplicateCard"
    />
  </div>
</template>
