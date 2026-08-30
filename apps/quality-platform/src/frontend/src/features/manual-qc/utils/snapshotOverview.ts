import type { AnalysisMetric } from '../analysis/types/analysis'
import type { SnapshotRow } from '../types/snapshot'
import type {
  DashboardMetricBlock,
  DashboardMetricCard,
  DashboardMetricReference,
  DashboardMetricResult,
  DashboardMetricValueResult,
  LegacyDashboardMetricCard,
  LegacyDashboardMetricId,
} from '@/shared/dashboard/types'

interface ResultTotals {
  annotationTotal: number
  annotationSubmitted: number
  goodSubmitted: number
  badSubmitted: number
  goodExpectedAllocated: number
  badExpectedAllocated: number
  goodAllocated: number
  badAllocated: number
  goodCompleted: number
  badCompleted: number
  goodPassed: number
  badPassed: number
  goodRejected: number
  badRejected: number
}

const FALLBACK_LABELS: Record<string, string> = {
  'annotation.total': '标注总量',
  'annotation.submitted': '标注提交量',
  'annotation.good_submitted': 'Good 提交量',
  'annotation.bad_submitted': 'Bad 提交量',
  'annotation.good_rate': 'Good 占比',
  'annotation.bad_rate': 'Bad 占比',
  'acceptance.expected_allocated': '预期验收分配量',
  'acceptance.allocated': '实际验收分配量',
  'acceptance.allocation_coverage_rate': '分配覆盖率',
  'acceptance.allocation_fulfillment_rate': '分配达成率',
  'acceptance.completed': '验收完成量',
  'acceptance.pending': '验收未完成量',
  'acceptance.completion_rate': '验收完成率',
  'acceptance.passed': '验收通过量',
  'acceptance.rejected': '验收打回量',
  'acceptance.pass_rate': '验收通过率',
  'acceptance.reject_rate': '验收打回率',
  'good.acceptance.allocated': 'Good 验收分配量',
  'good.acceptance.completed': 'Good 验收完成量',
  'good.acceptance.completion_rate': 'Good 验收完成率',
  'good.acceptance.passed': 'Good 验收通过量',
  'good.acceptance.rejected': 'Good 验收打回量',
  'good.acceptance.pass_rate': 'Good 验收通过率',
  'bad.acceptance.allocated': 'Bad 验收分配量',
  'bad.acceptance.completed': 'Bad 验收完成量',
  'bad.acceptance.completion_rate': 'Bad 验收完成率',
  'bad.acceptance.passed': 'Bad 验收通过量',
  'bad.acceptance.rejected': 'Bad 验收打回量',
  'bad.acceptance.pass_rate': 'Bad 验收通过率',
}

function cloneConfig<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

function emptyTotals(): ResultTotals {
  return {
    annotationTotal: 0,
    annotationSubmitted: 0,
    goodSubmitted: 0,
    badSubmitted: 0,
    goodExpectedAllocated: 0,
    badExpectedAllocated: 0,
    goodAllocated: 0,
    badAllocated: 0,
    goodCompleted: 0,
    badCompleted: 0,
    goodPassed: 0,
    badPassed: 0,
    goodRejected: 0,
    badRejected: 0,
  }
}

function addRow(total: ResultTotals, row: SnapshotRow): void {
  total.annotationTotal += row.annotation_total
  total.annotationSubmitted += row.annotation_submitted
  total.goodSubmitted += row.good_metrics.annotation_submitted
  total.badSubmitted += row.bad_metrics.annotation_submitted
  total.goodExpectedAllocated += row.good_metrics.expect_alloc
  total.badExpectedAllocated += row.bad_metrics.expect_alloc
  total.goodAllocated += row.good_metrics.actual_alloc
  total.badAllocated += row.bad_metrics.actual_alloc
  total.goodCompleted += row.good_metrics.actual_complete
  total.badCompleted += row.bad_metrics.actual_complete
  total.goodPassed += row.good_metrics.actual_pass
  total.badPassed += row.bad_metrics.actual_pass
  total.goodRejected += row.good_metrics.actual_reject
  total.badRejected += row.bad_metrics.actual_reject
}

function ratio(numerator: number, denominator: number): number | null {
  return denominator ? numerator / denominator * 100 : null
}

function metricValue(metricId: string, total: ResultTotals): number | null {
  const allocated = total.goodAllocated + total.badAllocated
  const expectedAllocated =
    total.goodExpectedAllocated + total.badExpectedAllocated
  const completed = total.goodCompleted + total.badCompleted
  const passed = total.goodPassed + total.badPassed
  const rejected = total.goodRejected + total.badRejected
  const values: Record<string, number | null> = {
    'annotation.total': total.annotationTotal,
    'annotation.submitted': total.annotationSubmitted,
    'annotation.good_submitted': total.goodSubmitted,
    'annotation.bad_submitted': total.badSubmitted,
    'annotation.good_rate': ratio(
      total.goodSubmitted,
      total.annotationSubmitted,
    ),
    'annotation.bad_rate': ratio(
      total.badSubmitted,
      total.annotationSubmitted,
    ),
    'acceptance.expected_allocated': expectedAllocated,
    'acceptance.allocated': allocated,
    'acceptance.allocation_coverage_rate': ratio(
      allocated,
      total.annotationSubmitted,
    ),
    'acceptance.allocation_fulfillment_rate': ratio(
      allocated,
      expectedAllocated,
    ),
    'acceptance.completed': completed,
    'acceptance.pending': Math.max(0, allocated - completed),
    'acceptance.completion_rate': ratio(completed, allocated),
    'acceptance.passed': passed,
    'acceptance.rejected': rejected,
    'acceptance.pass_rate': ratio(passed, completed),
    'acceptance.reject_rate': ratio(rejected, completed),
    'good.acceptance.allocated': total.goodAllocated,
    'good.acceptance.completed': total.goodCompleted,
    'good.acceptance.completion_rate': ratio(
      total.goodCompleted,
      total.goodAllocated,
    ),
    'good.acceptance.passed': total.goodPassed,
    'good.acceptance.rejected': total.goodRejected,
    'good.acceptance.pass_rate': ratio(
      total.goodPassed,
      total.goodCompleted,
    ),
    'bad.acceptance.allocated': total.badAllocated,
    'bad.acceptance.completed': total.badCompleted,
    'bad.acceptance.completion_rate': ratio(
      total.badCompleted,
      total.badAllocated,
    ),
    'bad.acceptance.passed': total.badPassed,
    'bad.acceptance.rejected': total.badRejected,
    'bad.acceptance.pass_rate': ratio(
      total.badPassed,
      total.badCompleted,
    ),
  }
  return values[metricId] ?? null
}

function metricUnit(
  metricId: string,
  catalog: AnalysisMetric[],
): 'count' | 'percent' {
  return (
    catalog.find((metric) => metric.id === metricId)?.unit ??
    (metricId.endsWith('_rate') ? 'percent' : 'count')
  )
}

function formatMetric(value: number | null, unit: 'count' | 'percent'): string {
  if (value == null) return '—'
  return unit === 'percent'
    ? `${value.toFixed(1)}%`
    : Math.round(value).toLocaleString('zh-CN')
}

function resolveValue(
  reference: DashboardMetricReference,
  total: ResultTotals,
  catalog: AnalysisMetric[],
  labelOverride?: string,
): DashboardMetricValueResult {
  const unit = metricUnit(reference.id, catalog)
  const value = metricValue(reference.id, total)
  return {
    metricId: reference.id,
    label:
      labelOverride ||
      catalog.find((metric) => metric.id === reference.id)?.label ||
      FALLBACK_LABELS[reference.id] ||
      reference.id,
    value,
    formattedValue: formatMetric(value, unit),
    unit,
  }
}

function dimensionValue(
  row: SnapshotRow,
  dimension: 'project' | 'task' | 'group',
): string {
  return {
    project: row.project_name,
    task: row.scene_name,
    group: row.group_name,
  }[dimension]
}

export function resolveOverviewMetric(
  card: DashboardMetricCard,
  rows: SnapshotRow[],
  catalog: AnalysisMetric[] = [],
): DashboardMetricResult {
  const total = emptyTotals()
  for (const row of rows) addRow(total, row)

  const values: DashboardMetricResult['values'] = {}
  const breakdowns: DashboardMetricResult['breakdowns'] = {}
  for (const block of card.blocks) {
    if (block.kind === 'metric-value') {
      values[block.id] = resolveValue(
        block.metric,
        total,
        catalog,
        block.label,
      )
      continue
    }
    if (block.kind !== 'breakdown') continue
    const grouped = new Map<string, ResultTotals>()
    for (const row of rows) {
      const label = dimensionValue(row, block.dimension)
      const group = grouped.get(label) ?? emptyTotals()
      addRow(group, row)
      grouped.set(label, group)
    }
    breakdowns[block.id] = [...grouped.entries()]
      .sort(([left], [right]) => left.localeCompare(right, 'zh-CN'))
      .slice(0, block.limit)
      .map(([label, group]) => ({
        label,
        values: block.metrics.map((metric) =>
          resolveValue(metric, group, catalog),
        ),
      }))
  }
  return { values, breakdowns }
}

function metricBlock(
  id: string,
  metricId: string,
  label: string,
  emphasis: 'primary' | 'supporting',
  width: 'full' | 'half' | 'third',
  color: string,
): DashboardMetricBlock {
  return {
    id,
    kind: 'metric-value',
    metric: { id: metricId },
    label,
    emphasis,
    width,
    style: {
      valueSize: emphasis === 'primary' ? 38 : 21,
      valueColor: color,
      labelSize: 10,
      labelColor: '#667085',
    },
  }
}

function breakdownBlock(
  id: string,
  metrics: string[],
): DashboardMetricBlock {
  return {
    id,
    kind: 'breakdown',
    dimension: 'project',
    metrics: metrics.map((metricId) => ({ id: metricId })),
    limit: 8,
    width: 'full',
  }
}

function cardStyle(accentColor: string, backgroundColor: string, textColor: string) {
  return {
    accentColor,
    backgroundColor,
    textColor,
    titleSize: 15,
    density: 'comfortable' as const,
  }
}

export function defaultOverviewCards(): DashboardMetricCard[] {
  return [
    {
      id: 'overview-annotation-quality',
      kind: 'metric',
      origin: {
        type: 'system-preset',
        presetId: 'manual-qc.annotation-overview',
        presetVersion: 2,
      },
      title: '标注产出与质量构成',
      description: '选定周期内的总标注量、Good / Bad 数量与 Good 占比',
      query: { scopeMode: 'inherit-page', filters: [] },
      blocks: [
        metricBlock(
          'submitted',
          'annotation.submitted',
          '标注提交',
          'primary',
          'full',
          '#2d63d7',
        ),
        metricBlock(
          'good',
          'annotation.good_submitted',
          'Good',
          'supporting',
          'third',
          '#16233a',
        ),
        metricBlock(
          'bad',
          'annotation.bad_submitted',
          'Bad',
          'supporting',
          'third',
          '#16233a',
        ),
        metricBlock(
          'good-rate',
          'annotation.good_rate',
          'Good 占比',
          'supporting',
          'third',
          '#16233a',
        ),
        breakdownBlock('by-project', [
          'annotation.submitted',
          'annotation.good_submitted',
          'annotation.bad_submitted',
          'annotation.good_rate',
        ]),
      ],
      action: { type: 'jump', targetCardId: 'annotation-quality' },
      style: cardStyle('#2d63d7', '#f5f8ff', '#16233a'),
      layout: { x: 0, y: 0, w: 4, h: 5, minW: 3, minH: 4 },
    },
    {
      id: 'overview-acceptance-completion',
      kind: 'metric',
      origin: {
        type: 'system-preset',
        presetId: 'manual-qc.acceptance-progress-overview',
        presetVersion: 2,
      },
      title: '验收分配与完成',
      description: '分配、完成、未完成及完成率',
      query: { scopeMode: 'inherit-page', filters: [] },
      blocks: [
        metricBlock(
          'completed',
          'acceptance.completed',
          '验收完成',
          'primary',
          'full',
          '#1b8a66',
        ),
        metricBlock(
          'allocated',
          'acceptance.allocated',
          '验收分配',
          'supporting',
          'third',
          '#152b24',
        ),
        metricBlock(
          'pending',
          'acceptance.pending',
          '未完成',
          'supporting',
          'third',
          '#152b24',
        ),
        metricBlock(
          'completion-rate',
          'acceptance.completion_rate',
          '完成率',
          'supporting',
          'third',
          '#152b24',
        ),
        breakdownBlock('by-project', [
          'acceptance.allocated',
          'acceptance.completed',
          'acceptance.pending',
          'acceptance.completion_rate',
        ]),
      ],
      action: { type: 'jump', targetCardId: 'acceptance-progress' },
      style: cardStyle('#1b8a66', '#f2fbf7', '#152b24'),
      layout: { x: 4, y: 0, w: 4, h: 5, minW: 3, minH: 4 },
    },
    {
      id: 'overview-acceptance-result',
      kind: 'metric',
      origin: {
        type: 'system-preset',
        presetId: 'manual-qc.acceptance-result-overview',
        presetVersion: 2,
      },
      title: '验收通过与打回',
      description: '验收完成任务中的通过量、打回量与通过率',
      query: { scopeMode: 'inherit-page', filters: [] },
      blocks: [
        metricBlock(
          'passed',
          'acceptance.passed',
          '验收通过',
          'primary',
          'full',
          '#c24a56',
        ),
        metricBlock(
          'rejected',
          'acceptance.rejected',
          '验收打回',
          'supporting',
          'half',
          '#351b20',
        ),
        metricBlock(
          'pass-rate',
          'acceptance.pass_rate',
          '通过率',
          'supporting',
          'half',
          '#351b20',
        ),
        breakdownBlock('by-project', [
          'acceptance.passed',
          'acceptance.rejected',
          'acceptance.pass_rate',
        ]),
      ],
      action: { type: 'jump', targetCardId: 'acceptance-result' },
      style: cardStyle('#c24a56', '#fff6f7', '#351b20'),
      layout: { x: 8, y: 0, w: 4, h: 5, minW: 3, minH: 4 },
    },
  ]
}

function presetForLegacy(metricId: LegacyDashboardMetricId): DashboardMetricCard {
  const defaults = defaultOverviewCards()
  return cloneConfig(
    metricId === 'annotation_quality'
      ? defaults[0]!
      : metricId === 'acceptance_result'
        ? defaults[2]!
        : defaults[1]!,
  )
}

export function isOverviewCardV2(
  card: DashboardMetricCard | LegacyDashboardMetricCard,
): card is DashboardMetricCard {
  return 'blocks' in card && Array.isArray(card.blocks)
}

export function normalizeOverviewCard(
  card: DashboardMetricCard | LegacyDashboardMetricCard,
): DashboardMetricCard {
  if (isOverviewCardV2(card)) return cloneConfig(card)
  const migrated = presetForLegacy(card.metricId)
  migrated.id = card.id
  migrated.title = card.title
  migrated.description = card.description
  migrated.origin.type = 'user'
  migrated.action = { type: 'jump', targetCardId: card.jumpTarget }
  migrated.style = {
    accentColor: card.style.accentColor,
    backgroundColor: card.style.backgroundColor,
    textColor: card.style.textColor,
    titleSize: card.style.titleSize,
    density: card.style.density,
  }
  migrated.layout = {
    ...cloneConfig(card.layout),
    h: Math.max(5, card.layout.h),
    minH: Math.max(4, card.layout.minH),
  }
  const primary = migrated.blocks.find(
    (block) => block.kind === 'metric-value' && block.emphasis === 'primary',
  )
  if (primary?.kind === 'metric-value') {
    primary.style.valueSize = card.style.valueSize
  }
  if (!card.style.showProjectBreakdown) {
    migrated.blocks = migrated.blocks.filter((block) => block.kind !== 'breakdown')
  }
  return migrated
}

export function nextOverviewCard(
  metricId: LegacyDashboardMetricId,
): DashboardMetricCard {
  const card = presetForLegacy(metricId)
  card.id = `overview-${Date.now()}`
  card.origin = { type: 'user' }
  card.layout = { x: 0, y: 0, w: 4, h: 5, minW: 3, minH: 4 }
  return card
}

export function duplicateOverviewCard(
  card: DashboardMetricCard,
): DashboardMetricCard {
  const copy = cloneConfig(card)
  copy.id = `overview-${Date.now()}`
  copy.title = `${card.title}（副本）`
  copy.origin = { type: 'user' }
  copy.layout = {
    ...copy.layout,
    x: Math.min(11, copy.layout.x + 1),
    y: copy.layout.y + 1,
  }
  return copy
}

export function restoreOverviewPreset(
  card: DashboardMetricCard,
): DashboardMetricCard | null {
  const presetId = card.origin.presetId
  if (!presetId) return null
  const preset = defaultOverviewCards().find(
    (candidate) => candidate.origin.presetId === presetId,
  )
  if (!preset) return null
  return {
    ...cloneConfig(preset),
    id: card.id,
    layout: cloneConfig(card.layout),
  }
}
