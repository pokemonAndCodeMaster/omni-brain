import { defineComponent } from 'vue'
import { fireEvent, render, screen } from '@testing-library/vue'
import { describe, expect, it, vi } from 'vitest'
import ChartVisualization from './ChartVisualization.vue'
import type {
  DashboardChartCard,
  DashboardChartResult,
} from '../types'

const card: DashboardChartCard = {
  id: 'progress',
  kind: 'chart',
  origin: { type: 'user' },
  title: '验收分配与完成',
  description: '',
  baseQuery: {
    sourceId: 'manual_qc.snapshot.v20260709',
    scopeMode: 'inherit-page',
    categoryDimension: 'date',
    timeGrain: 'day',
    questionLabels: [],
    filters: [],
  },
  axes: [
    {
      id: 'count-axis',
      side: 'left',
      unit: 'count',
      label: '数量',
      minimum: 0,
      maximum: null,
    },
    {
      id: 'rate-axis',
      side: 'right',
      unit: 'percent',
      label: '占比',
      minimum: 0,
      maximum: 100,
    },
  ],
  layers: [],
  presentation: {
    showLegend: true,
    legendPosition: 'top',
    categorySort: 'natural',
    categoryLimit: 31,
    orientation: 'vertical',
    fontScale: 'medium',
  },
  layout: { x: 0, y: 0, w: 8, h: 7, minW: 4, minH: 5 },
}

const result: DashboardChartResult = {
  categories: ['2026-07-25', '2026-07-26'],
  series: [
    {
      id: 'completed',
      name: '验收完成量',
      values: [120, 140],
      unit: '条',
      axisId: 'count-axis',
      renderAs: 'bar',
      color: '#315fc4',
    },
    {
      id: 'rate',
      name: '验收完成率',
      values: [90, 92.5],
      unit: '%',
      axisId: 'rate-axis',
      renderAs: 'line',
      color: '#d48a2f',
    },
  ],
  source: {
    sourceId: 'manual_qc.snapshot.v20260709',
    sourceLabel: '人工质检受控分析接口',
    rowCount: 4,
    filterSummary: '两周',
    generatedAt: '2026-07-26T10:00:00Z',
  },
}

const BaseEChartStub = defineComponent({
  emits: ['chartClick'],
  template: `
    <button type="button" @click="$emit('chartClick', { name: '2026-07-26' })">
      图表
    </button>
  `,
})

describe('ChartVisualization', () => {
  it('同时呈现多轴图层数据，并把点击分类向上交付', async () => {
    const drill = vi.fn()
    render(ChartVisualization, {
      props: {
        card,
        result,
        preview: true,
        onDrill: drill,
      },
      global: {
        stubs: {
          BaseEChart: BaseEChartStub,
        },
      },
    })

    expect(screen.getByText('120条')).toBeTruthy()
    expect(screen.getByText('92.5%')).toBeTruthy()
    await fireEvent.click(
      screen.getByRole('button', { name: /验收分配与完成/ }),
    )
    expect(drill).toHaveBeenCalledWith('2026-07-26')
  })
})
