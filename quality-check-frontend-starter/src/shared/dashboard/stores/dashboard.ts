import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'
import { loadPersisted, savePersisted } from '@/shared/persistence/storage'
import type { ChartSpec } from '@/shared/analysis/types/chart'
import type { DashboardCard, GridPosition } from '@/shared/dashboard/types/dashboard'

const STORAGE_KEY = 'quality-check.dashboard.cards'
const SCHEMA_VERSION = 1

function defaultCards(): DashboardCard[] {
  return [
    {
      id: 'system-kpi-active',
      title: '活跃交付任务',
      type: 'kpi',
      system: true,
      layout: { x: 0, y: 0, w: 3, h: 2 },
      kpi: {
        value: '5',
        label: '当前活跃',
        helper: '其中 1 项处于风险状态',
      },
    },
    {
      id: 'system-kpi-quality',
      title: '整体 Good 比例',
      type: 'kpi',
      system: true,
      layout: { x: 3, y: 0, w: 3, h: 2 },
      kpi: {
        value: '95.4%',
        label: '最近两周',
        helper: '较上个周期 +1.2 个百分点',
      },
    },
    {
      id: 'system-throughput-chart',
      title: '周度质检通量',
      type: 'chart',
      system: true,
      layout: { x: 6, y: 0, w: 6, h: 4 },
      chart: {
        id: 'chart-throughput-default',
        title: '周度质检通量',
        description: '演示卡片：真实接入后由后端聚合接口提供。',
        dimension: 'project',
        metric: 'completedCount',
        chartType: 'bar',
        filtersSummary: '最近两周',
        createdAt: new Date().toISOString(),
        data: [
          { name: '城区', value: 4120 },
          { name: '高速', value: 3310 },
          { name: '园区', value: 1960 },
          { name: '仿真', value: 2840 },
        ],
      },
    },
    {
      id: 'system-risk-table',
      title: '需要关注的任务',
      type: 'table',
      system: true,
      layout: { x: 0, y: 2, w: 6, h: 3 },
      tableRows: [
        { 任务: '高速施工区 July-W3', 风险: '完成率偏低', 负责人: '王凯' },
        { 任务: '城区路口交互 July-W3', 风险: '验收剩余时间紧张', 负责人: '张晨' },
      ],
    },
  ]
}

export const useDashboardStore = defineStore('dashboard', () => {
  const cards = ref<DashboardCard[]>(
    loadPersisted(STORAGE_KEY, SCHEMA_VERSION, defaultCards()),
  )

  const cardCount = computed(() => cards.value.length)

  watch(
    cards,
    (value) => savePersisted(STORAGE_KEY, SCHEMA_VERSION, value),
    { deep: true },
  )

  function addChartCard(chart: ChartSpec) {
    const index = cards.value.length
    cards.value.push({
      id: `card-${crypto.randomUUID()}`,
      title: chart.title,
      description: chart.description,
      type: 'chart',
      layout: {
        x: (index * 3) % 12,
        y: 20,
        w: 6,
        h: 4,
      },
      chart,
    })
  }

  function addTextCard() {
    const index = cards.value.length
    cards.value.push({
      id: `card-${crypto.randomUUID()}`,
      title: '个人备注',
      type: 'text',
      layout: {
        x: (index * 3) % 12,
        y: 20,
        w: 4,
        h: 2,
      },
      text: '这是一个个人卡片。进入编辑布局后可以拖动、缩放、复制或删除。',
    })
  }

  function removeCard(id: string) {
    const card = cards.value.find((item) => item.id === id)
    if (card?.system) return
    cards.value = cards.value.filter((item) => item.id !== id)
  }

  function duplicateCard(id: string) {
    const source = cards.value.find((item) => item.id === id)
    if (!source) return

    cards.value.push({
      ...structuredClone(source),
      id: `card-${crypto.randomUUID()}`,
      system: false,
      title: `${source.title}（副本）`,
      layout: {
        ...source.layout,
        x: Math.min(10, source.layout.x + 1),
        y: source.layout.y + 1,
      },
    })
  }

  function updateLayouts(layouts: Array<{ id: string; layout: GridPosition }>) {
    const layoutMap = new Map(layouts.map((item) => [item.id, item.layout]))
    cards.value = cards.value.map((card) => ({
      ...card,
      layout: layoutMap.get(card.id) ?? card.layout,
    }))
  }

  function resetDashboard() {
    cards.value = defaultCards()
  }

  return {
    cards,
    cardCount,
    addChartCard,
    addTextCard,
    removeCard,
    duplicateCard,
    updateLayouts,
    resetDashboard,
  }
})
