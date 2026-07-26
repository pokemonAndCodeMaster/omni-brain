import { cleanup, fireEvent, render, screen } from '@testing-library/vue'
import { afterEach, describe, expect, it } from 'vitest'
import type {
  DashboardMetricCard,
  DashboardMetricResult,
} from '../types'
import MetricCard from './MetricCard.vue'

const card: DashboardMetricCard = {
  id: 'overview-test',
  kind: 'metric',
  origin: {
    type: 'system-preset',
    presetId: 'manual-qc.test',
    presetVersion: 2,
  },
  title: '可组合总览',
  description: '内容块测试',
  query: { scopeMode: 'inherit-page', filters: [] },
  blocks: [
    {
      id: 'submitted',
      kind: 'metric-value',
      metric: { id: 'annotation.submitted' },
      label: '标注提交',
      emphasis: 'primary',
      width: 'full',
      style: {
        valueSize: 38,
        valueColor: '#2458d3',
        labelSize: 10,
        labelColor: '#667085',
      },
    },
    {
      id: 'note',
      kind: 'text',
      content: '先看总量，再看项目拆分。',
      width: 'full',
      style: { fontSize: 11, color: '#667085' },
    },
    {
      id: 'by-project',
      kind: 'breakdown',
      dimension: 'project',
      metrics: [{ id: 'annotation.submitted' }],
      limit: 8,
      width: 'full',
    },
  ],
  action: { type: 'jump', targetCardId: 'annotation-quality' },
  style: {
    accentColor: '#2458d3',
    backgroundColor: '#ffffff',
    textColor: '#17212b',
    titleSize: 15,
    density: 'comfortable',
  },
  layout: { x: 0, y: 0, w: 4, h: 4, minW: 3, minH: 3 },
}

const result: DashboardMetricResult = {
  values: {
    submitted: {
      metricId: 'annotation.submitted',
      label: '标注提交',
      value: 100,
      formattedValue: '100',
      unit: 'count',
    },
  },
  breakdowns: {
    'by-project': [
      {
        label: '园区',
        values: [
          {
            metricId: 'annotation.submitted',
            label: '标注提交量',
            value: 40,
            formattedValue: '40',
            unit: 'count',
          },
        ],
      },
    ],
  },
}

afterEach(cleanup)

describe('MetricCard', () => {
  it('按块顺序展示指标、说明和通用拆分，并暴露复制与恢复动作', async () => {
    const rendered = render(MetricCard, {
      props: { card, result },
    })

    const body = screen.getByRole('button', { name: /标注提交/ })
    expect(body.textContent).toContain('100')
    expect(body.textContent).toContain('先看总量，再看项目拆分。')
    expect(body.textContent).toContain('园区')
    expect(body.textContent).toContain('标注提交量')

    await fireEvent.click(
      screen.getByRole('button', { name: '复制总览卡片' }),
    )
    await fireEvent.click(
      screen.getByRole('button', { name: '恢复系统默认总览' }),
    )
    expect(rendered.emitted().duplicate).toHaveLength(1)
    expect(rendered.emitted().restore).toHaveLength(1)
  })
})
