import { computed, onMounted, reactive, readonly, shallowRef } from 'vue'
import axios from 'axios'
import {
  getEmployeeAggregate,
  getGroupAggregate,
  getSceneAggregate,
} from '../api/snapshot'
import type {
  AggregateLevel,
  AggregateNode,
  EmployeeAggregate,
  GroupAggregate,
  SceneAggregate,
  SnapshotCounts,
  SnapshotQuery,
} from '../types/snapshot'

function formatLocalDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function defaultQuery(): Required<Pick<SnapshotQuery, 'stat_date_start' | 'stat_date_end'>> &
  SnapshotQuery {
  const today = new Date()
  const sevenDaysAgo = new Date(today)
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6)
  return {
    stat_date_start: formatLocalDate(sevenDaysAgo),
    stat_date_end: formatLocalDate(today),
    scene_name: '',
    group_name: '',
  }
}

function countsOf(value: SnapshotCounts): SnapshotCounts {
  return {
    annotation_total: value.annotation_total,
    annotation_submitted: value.annotation_submitted,
    good_annotation_submitted: value.good_annotation_submitted,
    bad_annotation_submitted: value.bad_annotation_submitted,
    total_accept_assigned: value.total_accept_assigned,
    total_accept_completed: value.total_accept_completed,
    total_accept_passed: value.total_accept_passed,
    total_accept_rejected: value.total_accept_rejected,
    good_accept_assigned: value.good_accept_assigned,
    good_accept_completed: value.good_accept_completed,
    good_accept_passed: value.good_accept_passed,
    good_accept_rejected: value.good_accept_rejected,
    bad_accept_assigned: value.bad_accept_assigned,
    bad_accept_completed: value.bad_accept_completed,
    bad_accept_passed: value.bad_accept_passed,
    bad_accept_rejected: value.bad_accept_rejected,
  }
}

function toNode(
  value: SceneAggregate | GroupAggregate | EmployeeAggregate,
  level: AggregateLevel,
): AggregateNode {
  const groupName = 'group_name' in value ? value.group_name : ''
  const employeeId = 'employee_id' in value ? value.employee_id : ''
  const id = [level, value.stat_date, value.scene_name, groupName, employeeId]
    .filter(Boolean)
    .join(':')
  return {
    id,
    level,
    stat_date: value.stat_date,
    scene_name: value.scene_name,
    group_name: groupName,
    employee_id: employeeId,
    computed_at: value.computed_at,
    ...countsOf(value),
    ...(level === 'employee' ? {} : { children: [] }),
  }
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.code === 'ECONNABORTED') return '后端请求超时，请检查本地服务。'
    if (!error.response) return '无法连接本地后端，请确认 FastAPI 已启动。'
    return `后端返回 ${error.response.status}，请检查接口日志。`
  }
  return error instanceof Error ? error.message : '发生未知错误。'
}

export function useSnapshotExplorer() {
  const query = reactive<SnapshotQuery>(defaultQuery())
  const loading = shallowRef(false)
  const error = shallowRef('')
  const notice = shallowRef('')
  const sceneRows = shallowRef<SceneAggregate[]>([])
  const tree = shallowRef<AggregateNode[]>([])
  const loadedKeys = shallowRef<Set<string>>(new Set())
  const loadingKeys = shallowRef<Set<string>>(new Set())
  const computedAt = shallowRef<string | null>(null)

  const sceneOptions = computed(() =>
    [...new Set(sceneRows.value.map((row) => row.scene_name))].sort(),
  )

  const filtersSummary = computed(() => {
    const parts = [
      query.stat_date_start ? `${query.stat_date_start} 起` : '',
      query.stat_date_end ? `${query.stat_date_end} 止` : '',
      query.scene_name ? `场景：${query.scene_name}` : '',
      query.group_name ? `组：${query.group_name}` : '',
    ].filter(Boolean)
    return parts.join(' · ') || '全部实验数据'
  })

  function apiQuery(): SnapshotQuery {
    return Object.fromEntries(
      Object.entries(query).filter(([, value]) => value !== '' && value != null),
    )
  }

  function updateNode(id: string, update: (node: AggregateNode) => void) {
    function visit(nodes: AggregateNode[]): boolean {
      for (const node of nodes) {
        if (node.id === id) {
          update(node)
          return true
        }
        if (node.children && visit(node.children)) return true
      }
      return false
    }

    const next = structuredClone(tree.value)
    if (visit(next)) tree.value = next
  }

  async function load() {
    loading.value = true
    error.value = ''
    notice.value = ''
    loadedKeys.value = new Set()
    loadingKeys.value = new Set()
    try {
      const response = await getSceneAggregate(apiQuery())
      sceneRows.value = response.items
      tree.value = response.items.map((item) => toNode(item, 'scene'))
      computedAt.value = response.computed_at
      notice.value = response.total
        ? `已加载 ${response.total} 条日期—场景聚合。展开行可继续查看组和员工。`
        : '接口返回成功，但当前筛选范围没有快照数据。'
    } catch (caught) {
      error.value = errorMessage(caught)
      sceneRows.value = []
      tree.value = []
      computedAt.value = null
    } finally {
      loading.value = false
    }
  }

  async function expand(node: AggregateNode) {
    if (
      node.level === 'employee' ||
      loadedKeys.value.has(node.id) ||
      loadingKeys.value.has(node.id)
    ) {
      return
    }

    loadingKeys.value = new Set([...loadingKeys.value, node.id])
    updateNode(node.id, (current) => {
      current.loading = true
    })
    error.value = ''

    try {
      let children: AggregateNode[]
      if (node.level === 'scene') {
        const response = await getGroupAggregate({
          stat_date_start: node.stat_date,
          stat_date_end: node.stat_date,
          scene_name: node.scene_name,
        })
        children = response.items.map((item) => toNode(item, 'group'))
      } else {
        const response = await getEmployeeAggregate({
          stat_date_start: node.stat_date,
          stat_date_end: node.stat_date,
          scene_name: node.scene_name,
          group_name: node.group_name,
        })
        children = response.items.map((item) => toNode(item, 'employee'))
      }

      updateNode(node.id, (current) => {
        current.children = children
        current.loading = false
      })
      loadedKeys.value = new Set([...loadedKeys.value, node.id])
    } catch (caught) {
      updateNode(node.id, (current) => {
        current.loading = false
      })
      error.value = `“${node.scene_name}${node.group_name ? ` / ${node.group_name}` : ''}”下层数据加载失败：${errorMessage(caught)}`
    } finally {
      const nextLoading = new Set(loadingKeys.value)
      nextLoading.delete(node.id)
      loadingKeys.value = nextLoading
    }
  }

  function reset() {
    Object.assign(query, defaultQuery())
  }

  async function resetAndLoad() {
    reset()
    await load()
  }

  onMounted(load)

  return {
    query,
    loading: readonly(loading),
    error: readonly(error),
    notice: readonly(notice),
    sceneRows: readonly(sceneRows),
    tree: readonly(tree),
    loadingKeys: readonly(loadingKeys),
    computedAt: readonly(computedAt),
    sceneOptions,
    filtersSummary,
    load,
    expand,
    resetAndLoad,
  }
}
