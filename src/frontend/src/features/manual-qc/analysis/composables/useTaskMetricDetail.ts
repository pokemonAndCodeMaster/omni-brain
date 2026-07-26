import { readonly, shallowRef, watch, type Ref } from 'vue'
import axios from 'axios'
import type { SnapshotQuery } from '../../types/snapshot'
import {
  postAnalysisFacets,
  postAnalysisQuery,
} from '../api/analysis'
import { metricReferenceKey } from '../utils'
import type {
  AnalysisMetricReference,
  AnalysisScope,
  TaskMetricDetail,
  TaskMetricDetailOption,
  TaskMetricDetailSelection,
} from '../types/analysis'

const SOURCE_ID = 'manual_qc.snapshot.v20260709'

const SUMMARY_MEASURES: Record<
  TaskMetricDetailSelection['metricId'],
  AnalysisMetricReference[]
> = {
  'annotation.good_rate': [
    { id: 'annotation.submitted' },
    { id: 'annotation.good_submitted' },
    { id: 'annotation.bad_submitted' },
    { id: 'annotation.good_rate' },
    { id: 'annotation.bad_rate' },
  ],
  'acceptance.completion_rate': [
    { id: 'acceptance.allocated' },
    { id: 'acceptance.completed' },
    { id: 'acceptance.pending' },
    { id: 'acceptance.completion_rate' },
    { id: 'good.acceptance.allocated' },
    { id: 'good.acceptance.completed' },
    { id: 'good.acceptance.completion_rate' },
    { id: 'bad.acceptance.allocated' },
    { id: 'bad.acceptance.completed' },
    { id: 'bad.acceptance.completion_rate' },
  ],
  'acceptance.pass_rate': [
    { id: 'acceptance.completed' },
    { id: 'acceptance.passed' },
    { id: 'acceptance.rejected' },
    { id: 'acceptance.pass_rate' },
    { id: 'good.acceptance.passed' },
    { id: 'good.acceptance.rejected' },
    { id: 'good.acceptance.pass_rate' },
    { id: 'bad.acceptance.passed' },
    { id: 'bad.acceptance.rejected' },
    { id: 'bad.acceptance.pass_rate' },
  ],
}

const OPTION_METRIC_IDS = [
  'option.annotation_submitted',
  'option.annotation_rate_of_bad',
  'option.acceptance.allocated',
  'option.acceptance.completed',
  'option.acceptance.completion_rate',
  'option.acceptance.passed',
  'option.acceptance.rejected',
  'option.acceptance.pass_rate',
] as const

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (!error.response) return '无法连接指标详情接口。'
    return `指标详情接口返回 ${error.response.status}。`
  }
  return error instanceof Error ? error.message : '指标详情读取失败。'
}

function selectionScope(
  selection: TaskMetricDetailSelection,
  pageQuery: SnapshotQuery,
): AnalysisScope {
  const path = selection.row.path
  return {
    dateStart: path.date ?? pageQuery.stat_date_start ?? undefined,
    dateEnd: path.date ?? pageQuery.stat_date_end ?? undefined,
    projectNames: [path.project],
    taskNames: [path.task],
    groupNames: path.group ? [path.group] : [],
    employeeIds: path.employee ? [path.employee] : [],
  }
}

function summaryGroupBy(
  selection: TaskMetricDetailSelection,
): string[] {
  return {
    task: ['project', 'task'],
    date: ['date'],
    group: ['group'],
    employee: ['employee'],
  }[selection.row.level]
}

function optionReferences(
  questionLabel: string,
  questionOption: string,
): AnalysisMetricReference[] {
  return OPTION_METRIC_IDS.map((id) => ({
    id,
    parameters: { questionLabel, questionOption },
  }))
}

function value(
  measures: Record<string, number | null>,
  reference: AnalysisMetricReference,
): number | null {
  return measures[metricReferenceKey(reference)] ?? null
}

export function useTaskMetricDetail(
  selection: Ref<TaskMetricDetailSelection | null>,
  pageQuery: SnapshotQuery,
) {
  const detail = shallowRef<TaskMetricDetail | null>(null)
  const loading = shallowRef(false)
  const error = shallowRef('')
  let requestId = 0

  async function loadOptions(
    scope: AnalysisScope,
    groupBy: string[],
  ): Promise<TaskMetricDetailOption[]> {
    const labels = await postAnalysisFacets({
      sourceId: SOURCE_ID,
      scope,
      dimensionId: 'question_label',
    })
    const pairs = (
      await Promise.all(
        labels.values.map(async (questionLabel) => {
          const result = await postAnalysisFacets({
            sourceId: SOURCE_ID,
            scope,
            dimensionId: 'question_option',
            questionLabel,
          })
          return result.values.map((questionOption) => ({
            questionLabel,
            questionOption,
          }))
        }),
      )
    ).flat()
    return Promise.all(
      pairs.map(async ({ questionLabel, questionOption }) => {
        const references = optionReferences(questionLabel, questionOption)
        const result = await postAnalysisQuery({
          sourceId: SOURCE_ID,
          scope,
          groupBy,
          measures: references,
          page: { number: 1, size: 1 },
        })
        const measures = result.rows[0]?.measures ?? {}
        return {
          questionLabel,
          questionOption,
          annotationSubmitted:
            value(measures, references[0]!) ?? 0,
          annotationRateOfBad: value(measures, references[1]!),
          allocated: value(measures, references[2]!) ?? 0,
          completed: value(measures, references[3]!) ?? 0,
          completionRate: value(measures, references[4]!),
          passed: value(measures, references[5]!) ?? 0,
          rejected: value(measures, references[6]!) ?? 0,
          passRate: value(measures, references[7]!),
        }
      }),
    )
  }

  async function load(): Promise<void> {
    const current = selection.value
    const activeRequestId = ++requestId
    if (!current) {
      detail.value = null
      error.value = ''
      return
    }
    loading.value = true
    error.value = ''
    try {
      const scope = selectionScope(current, pageQuery)
      const measures = SUMMARY_MEASURES[current.metricId]
      const [summaryResult, trendResult, options] = await Promise.all([
        postAnalysisQuery({
          sourceId: SOURCE_ID,
          scope,
          groupBy: summaryGroupBy(current),
          measures,
          page: { number: 1, size: 1 },
        }),
        postAnalysisQuery({
          sourceId: SOURCE_ID,
          scope,
          groupBy: ['date'],
          measures,
          sort: [
            {
              target: { id: 'date' },
              direction: 'ascending',
            },
          ],
          page: { number: 1, size: 31 },
        }),
        loadOptions(scope, summaryGroupBy(current)),
      ])
      if (activeRequestId !== requestId) return
      detail.value = {
        selection: current,
        summary: summaryResult.rows[0]?.measures ?? {},
        trend: trendResult.rows.map((row) => ({
          date: row.dimensions.date ?? '',
          measures: row.measures,
        })),
        options,
      }
    } catch (caught) {
      if (activeRequestId !== requestId) return
      detail.value = null
      error.value = errorMessage(caught)
    } finally {
      if (activeRequestId === requestId) loading.value = false
    }
  }

  watch(
    selection,
    () => void load(),
    { immediate: true },
  )

  return {
    detail: readonly(detail),
    loading: readonly(loading),
    error: readonly(error),
    load,
  }
}
