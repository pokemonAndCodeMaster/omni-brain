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

vi.mock('../analysis/composables/useTaskAnalysis', async () => {
  const { shallowRef } = await import('vue')
  return {
    useTaskAnalysis: () => ({
      rows: shallowRef([
        {
          id: '城区/高速::城区交互任务-A',
          project: '城区/高速',
          task: '城区交互任务-A',
          annotationSubmitted: 447,
          goodRate: 75.4,
          acceptanceAllocated: 98,
          allocationCoverageRate: 21.9,
          acceptanceCompleted: 93,
          completionRate: 94.9,
          passRate: 90.3,
        },
      ]),
      loading: shallowRef(false),
      error: shallowRef(''),
      total: shallowRef(1),
      load: vi.fn(),
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
  defaultOverviewCards: [],
  nextOverviewCard: vi.fn(),
  resolveOverviewMetric: vi.fn(),
}))

import SnapshotPage from './SnapshotPage.vue'

const TaskAnalysisTableStub = defineComponent({
  props: {
    rows: { type: Array, required: true },
    loading: { type: Boolean, required: true },
    total: { type: Number, required: true },
    catalog: { type: Object, required: false },
  },
  template: `
    <output data-testid="task-analysis-input">
      {{ rows[0]?.task }} | {{ loading }} | {{ total }} | {{ catalog?.dimensions?.[0]?.label }}
    </output>
  `,
})

describe('SnapshotPage', () => {
  it('将任务分析的 Ref 值解包后交给任务表，而不是把 Ref 对象作为 props', () => {
    render(SnapshotPage, {
      global: {
        stubs: {
          ChartBuilderDialog: true,
          DashboardGrid: true,
          MetricCardEditor: true,
          MetricCardGrid: true,
          SnapshotFilters: true,
          SnapshotSummaryChart: true,
          TaskAnalysisTable: TaskAnalysisTableStub,
        },
      },
    })

    expect(screen.getByTestId('task-analysis-input').textContent).toContain(
      '城区交互任务-A | false | 1 | 标注任务',
    )
  })
})
