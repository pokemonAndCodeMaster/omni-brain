import { computed, onMounted, reactive, readonly, shallowRef } from 'vue'
import axios from 'axios'
import {
  getEmployeeAggregate,
  getGroupAggregate,
  getProjectAggregate,
  getSceneAggregate,
} from '../api/snapshot'
import type {
  AggregateLevel,
  AggregateNode,
  EmployeeAggregate,
  GroupAggregate,
  ProjectAggregate,
  SceneAggregate,
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
    project_name: '',
    scene_name: '',
    group_name: '',
    employee_id: '',
  }
}

function toNode(
  value: ProjectAggregate | SceneAggregate | GroupAggregate | EmployeeAggregate,
  level: AggregateLevel,
): AggregateNode {
  const sceneName = 'scene_name' in value ? value.scene_name : ''
  const groupName = 'group_name' in value ? value.group_name : ''
  const employeeId = 'employee_id' in value ? value.employee_id : ''
  const id = [
    level,
    value.stat_date,
    value.project_name,
    sceneName,
    groupName,
    employeeId,
  ]
    .filter(Boolean)
    .join(':')
  return {
    id,
    level,
    stat_date: value.stat_date,
    project_name: value.project_name,
    scene_name: sceneName,
    group_name: groupName,
    employee_id: employeeId,
    computed_at: value.computed_at,
    annotation_total: value.annotation_total,
    annotation_submitted: value.annotation_submitted,
    good_metrics: structuredClone(value.good_metrics),
    bad_metrics: structuredClone(value.bad_metrics),
    hasChildren: level !== 'employee',
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

  const projectOptions = computed(() =>
    [...new Set(sceneRows.value.map((row) => row.project_name))].sort(),
  )

  const sceneOptions = computed(() =>
    [...new Set(sceneRows.value.map((row) => row.scene_name))].sort(),
  )

  const filtersSummary = computed(() => {
    const parts = [
      query.stat_date_start ? `${query.stat_date_start} 起` : '',
      query.stat_date_end ? `${query.stat_date_end} 止` : '',
      query.project_name ? `项目：${query.project_name}` : '',
      query.scene_name ? `标注任务：${query.scene_name}` : '',
      query.group_name ? `组：${query.group_name}` : '',
      query.employee_id ? `标注员：${query.employee_id}` : '',
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
      const [projectResponse, sceneResponse] = await Promise.all([
        getProjectAggregate(apiQuery()),
        getSceneAggregate(apiQuery()),
      ])
      sceneRows.value = sceneResponse.items
      tree.value = projectResponse.items.map((item) => toNode(item, 'project'))
      computedAt.value =
        [projectResponse.computed_at, sceneResponse.computed_at]
          .filter((value): value is string => Boolean(value))
          .sort()
          .at(-1) ?? null
      notice.value = sceneResponse.total
        ? `已加载 ${projectResponse.total} 条日期—项目、${sceneResponse.total} 条日期—标注任务聚合。可按项目继续下钻到任务、组和员工。`
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

  async function expand(node: AggregateNode): Promise<boolean> {
    if (
      node.level === 'employee' ||
      loadedKeys.value.has(node.id) ||
      loadingKeys.value.has(node.id)
    ) {
      return Boolean(node.children?.length)
    }

    loadingKeys.value = new Set([...loadingKeys.value, node.id])
    updateNode(node.id, (current) => {
      current.loading = true
    })
    error.value = ''

    try {
      let children: AggregateNode[]
      if (node.level === 'project') {
        const response = await getSceneAggregate({
          ...apiQuery(),
          stat_date_start: node.stat_date,
          stat_date_end: node.stat_date,
          project_name: node.project_name,
        })
        children = response.items.map((item) => toNode(item, 'scene'))
      } else if (node.level === 'scene') {
        const response = await getGroupAggregate({
          ...apiQuery(),
          stat_date_start: node.stat_date,
          stat_date_end: node.stat_date,
          project_name: node.project_name,
          scene_name: node.scene_name,
        })
        children = response.items.map((item) => toNode(item, 'group'))
      } else {
        const response = await getEmployeeAggregate({
          ...apiQuery(),
          stat_date_start: node.stat_date,
          stat_date_end: node.stat_date,
          project_name: node.project_name,
          scene_name: node.scene_name,
          group_name: node.group_name,
        })
        children = response.items.map((item) => toNode(item, 'employee'))
      }

      updateNode(node.id, (current) => {
        current.children = children
        current.hasChildren = children.length > 0
        current.loading = false
      })
      loadedKeys.value = new Set([...loadedKeys.value, node.id])
      return children.length > 0
    } catch (caught) {
      updateNode(node.id, (current) => {
        current.loading = false
      })
      error.value = `“${node.project_name}${node.scene_name ? ` / ${node.scene_name}` : ''}${node.group_name ? ` / ${node.group_name}` : ''}”下层数据加载失败：${errorMessage(caught)}`
      return false
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
    projectOptions,
    filtersSummary,
    load,
    expand,
    resetAndLoad,
  }
}
