import { defineComponent } from 'vue'
import { render, screen } from '@testing-library/vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('../composables/useSnapshotExplorer', async () => {
  const { reactive, ref } = await import('vue')
  return {
    useSnapshotExplorer: () => ({
      query: reactive({
        stat_date_start: '',
        stat_date_end: '',
        project_name: '',
        scene_name: '',
        group_name: '',
        employee_id: '',
      }),
      loading: ref(false),
      error: ref(''),
      notice: ref(''),
      sceneRows: ref([]),
      snapshotRows: ref([]),
      computedAt: ref(null),
      sceneOptions: ref([]),
      projectOptions: ref([]),
      filtersSummary: ref(''),
      load: vi.fn(),
      resetAndLoad: vi.fn(),
    }),
  }
})

vi.mock('../analysis/composables/useAnalysisCatalog', async () => {
  const { shallowRef } = await import('vue')
  return {
    useAnalysisCatalog: () => ({
      catalog: shallowRef({
        sourceId: 'manual_qc.snapshot.v20260709',
        dimensions: [
          {
            id: 'task',
            label: '标注任务',
            valueType: 'text',
            filterOperators: [],
            groupable: true,
            sortable: true,
          },
        ],
        metrics: [],
      }),
      loading: shallowRef(false),
      error: shallowRef(''),
      load: vi.fn(),
    }),
  }
})

vi.mock('@/shared/dashboard/composables/useMetricWorkspace', async () => {
  const { ref } = await import('vue')
  return {
    useMetricWorkspace: () => ({
      cards: ref([]),
      loading: ref(false),
      saving: ref(false),
      dirty: ref(false),
      notice: ref(''),
      addCard: vi.fn(),
      updateCard: vi.fn(),
      removeCard: vi.fn(),
      updateLayouts: vi.fn(),
      save: vi.fn(),
    }),
  }
})

vi.mock('@/shared/dashboard/composables/useDashboardWorkspace', async () => {
  const { ref } = await import('vue')
  return {
    useDashboardWorkspace: () => ({
      cards: ref([]),
      results: ref({}),
      loadingCardIds: ref(new Set()),
      cardErrors: ref({}),
      loading: ref(false),
      saving: ref(false),
      dirty: ref(false),
      notice: ref(''),
      addCard: vi.fn(),
      updateCard: vi.fn(),
      updateLayouts: vi.fn(),
      removeCard: vi.fn(),
      refreshCard: vi.fn(),
      save: vi.fn(),
    }),
  }
})

vi.mock('../utils/snapshotChart', () => ({
  buildSnapshotChartCard: vi.fn(),
  chartBuilderValueFromCard: vi.fn(),
  createSnapshotChartBuilderOptions: () => ({ defaultSourceId: 'fixture' }),
  resolveSnapshotChartCard: vi.fn(),
}))

vi.mock('../utils/snapshotOverview', () => ({
  defaultOverviewCards: vi.fn(() => []),
  duplicateOverviewCard: vi.fn(),
  nextOverviewCard: vi.fn(),
  normalizeOverviewCard: vi.fn((card) => card),
  resolveOverviewMetric: vi.fn(),
  restoreOverviewPreset: vi.fn(),
}))

import SnapshotPage from './SnapshotPage.vue'

const TaskAnalysisWorkspaceStub = defineComponent({
  props: {
    pageQuery: { type: Object, required: true },
    catalog: { type: Object, required: false },
  },
  template: `
    <output data-testid="task-analysis-input">
      {{ pageQuery.project_name || '全部项目' }} | {{ catalog?.dimensions?.[0]?.label }}
    </output>
  `,
})

describe('SnapshotPage', () => {
  it('把当前全页范围和分析目录交给任务分析工作区', () => {
    render(SnapshotPage, {
      global: {
        stubs: {
          ChartBuilderDialog: true,
          DashboardGrid: true,
          MetricCardEditor: true,
          MetricCardGrid: true,
          SnapshotFilters: true,
          SnapshotSummaryChart: true,
          TaskAnalysisWorkspace: TaskAnalysisWorkspaceStub,
        },
      },
    })

    expect(screen.getByTestId('task-analysis-input').textContent).toContain(
      '全部项目 | 标注任务',
    )
  })
})
