# 组件边界

## 后端与公共能力

| 组件 | 单一职责 | 不负责 |
|---|---|---|
| `ConfigManager` | 合并 YAML、替换环境变量、管理连接别名与原子重载 | 建立数据库连接、保存秘密 |
| `DatabaseManager` | 按别名创建并复用 PostgreSQL connector | 编写业务 SQL |
| `PGConnector` | 连接池、只读查询、写事务和批量写 | 验收业务判断 |
| `SnapshotRepository` | 快照行查询与项目、标注任务、组、员工四级聚合 SQL | HTTP 和页面状态 |
| `SnapshotQueryService` | 聚合级别和必填筛选的业务边界 | 拼接 SQL |
| FastAPI Router | 校验 HTTP 参数并调用 Service | 直接访问数据库 |
| `ViewConfigRepository / Service` | 保存和恢复页面统计卡片定义、样式与布局 | 计算图表数据、解释指标 |

数据依赖方向固定为 `Router → Service → Repository → Connector → PostgreSQL`。

物理目录对齐目标资料：`src/api/routers/`、`src/api/schemas/`、`src/config/config_loader.py`、`src/database/pg_connector.py` 和 `src/manual_qc/snapshot/`。

## Vue 组件边界

## 应用层

| 组件 | 单一职责 | 输入 / 输出 |
|---|---|---|
| `App.vue` | 渲染应用外壳 | 无 |
| `AppShell.vue` | 提供侧边栏、顶栏和路由内容区 | 读取路由元数据，不拥有领域状态 |
| `SnapshotPage.vue` | 组装人工质检总览、可编辑看板和逐级明细 | 使用 composable，把状态传给子组件；处理图表下钻 |

## 人工质检快照功能

| 组件或 composable | 单一职责 | 输入 / 输出 |
|---|---|---|
| `useSnapshotExplorer` | 管理查询、加载、错误、树数据和四级懒加载 | 输出只读状态与 `load/reset/expand` 动作 |
| `SnapshotFilters.vue` | 编辑日期、项目、标注任务、组和员工筛选 | `modelValue`；发出 `submit`、`reset` |
| `SnapshotSummaryChart.vue` | 用数量柱、比率折线和 Bad 问题排行展示标注与验收，并切换任务/日期 | 最小快照行；发出任务/日期下钻 |
| `SnapshotDataTable.vue` | 定义领域列、完成率/通过率公式并连接 DataWorkbench | `rows`、`loadingKeys`；发出制图或申请全页筛选 |
| `snapshotChart.ts` | 按日期、项目、标注任务、组、员工和结果层级聚合指标 | 保存的查询卡片；返回用最新快照计算的图表结果 |
| `snapshotOverview.ts` | 计算全量及各项目的总览指标 | 总览卡片定义和最小快照行；返回标注/验收结果 |

## 共享组件

| 组件 | 单一职责 | 输入 / 输出 |
|---|---|---|
| `DataWorkbench.vue` | 管理通用表格状态和渲染 | 行、列、编辑器、展开规则；发出编辑、选择、状态、展开和当前筛选制图请求 |
| `HeaderFilter.vue` | 在列头内提供文本、枚举、日期和数值范围筛选 | 列筛选值；发出更新与清除 |
| `WorkbenchToolbar.vue` | 展示行数、筛选作用域、制图和列管理动作 | 统计与列描述；发出制图或“应用到全页” |
| `BaseCheckbox.vue` | 提供可访问的二态/三态复选框 | `modelValue`、`indeterminate`；发出更新 |
| `BaseEChart.vue` | 管理 ECharts 生命周期和尺寸响应 | `option`、可访问标签和最小高度 |
| `DashboardGrid.vue` | 用 GridStack 管理卡片拖动、缩放和响应式布局 | 卡片与运行结果；发出布局、编辑、删除、刷新和下钻 |
| `CardShell.vue` | 统一卡片标题、拖动手柄、动作、内容和来源区 | 插槽；发出编辑和删除 |
| `ChartCard.vue` | 把卡片定义渲染为 ECharts 与可读数据表 | 卡片及运行结果；发出编辑、刷新、删除和图表点击 |
| `ChartBuilderDialog.vue` | 编辑标题、数据源、分组、指标、筛选、图形与样式 | 初始卡片；发出完整卡片配置 |
| `useDashboardWorkspace` | 恢复、重算、修改并持久化页面看板 | 页面键和卡片解析器；输出卡片、结果和保存状态 |
| `MetricCard / MetricCardEditor` | 展示和编辑项目拆分总览、跳转目标、文字与颜色 | 总览定义与计算结果；发出编辑、删除和跳转 |
| `MetricCardGrid / useMetricWorkspace` | 管理总览卡片布局和持久化 | 页面键、总览卡片；输出保存状态与布局变更 |

**表格状态：** TanStack Table 负责排序、筛选、列顺序、列宽、选择和展开状态；Vue 组件负责交互与视觉。服务端懒加载子行时，只有成功取得子行后才把父行置为展开，避免“减号已出现但数据尚未展开”的伪状态。

**数据流：** props 向下，typed events 向上。路由页不直接拼 API，不把 SQL 或指标公式放入共享组件。

## TanStack Table 的采用边界

TanStack Table 是无样式的表格状态与行模型引擎，不是开箱即用的视觉组件。
它的能力上限已经覆盖排序、筛选、分面筛选、分页、分组、聚合、展开、选择、
列顺序/宽度/显隐/固定、行固定以及受控状态；大数据场景可和 TanStack Virtual
组合实现行列虚拟化。图表、业务统计卡片、工具栏信息架构和视觉设计不属于它的职责。

本项目不再逐项发明底层表格状态，采用以下成熟实践：

| 参考实现 | 直接借鉴 | 本项目落点 |
|---|---|---|
| TanStack Table Vue examples | 官方行模型与受控状态组合方式 | `DataWorkbench` 的排序、筛选、展开、选择和列状态 |
| Nuxt UI `Table.vue` | 单一内核暴露受控状态，按需组合固定列、分组和虚拟滚动 | 后续扩展仍进入同一表格内核，不另写平行表格 |
| shadcn-vue Data Table | 工具栏、分面筛选、列管理、分页、行操作拆成组合部件 | `HeaderFilter`、`WorkbenchToolbar` 继续独立演进 |

当前已实现列头文本/枚举/日期/数值范围筛选、默认降序排序、调宽、显隐、顺序、
选择和树形懒加载。下一批只有在
真实数据量或操作工况触发时，再接列固定、分面筛选、服务端分页与虚拟滚动。
统计卡片是独立的 Dashboard 能力，通过“当前筛选结果”这一语义事件连接表格，
不侵入 TanStack 内核。

当前卡片的查询、样式和布局已保存到 `t_portal_view_config`。页面重开后只恢复
定义，并对最新快照重新计算，不保存易过期的统计值。当前是本地单用户默认视图；
共享权限、多视图切换和历史版本恢复尚未实现。

## 筛选作用域

```text
顶部筛选
  └─ 定义全页快照范围 → 总览、固定图、个人看板初始条件、明细

表头筛选
  └─ 默认只分析已加载明细
       ├─ 生成统计卡片：转换可表达的数据条件，卡片以后独立刷新
       └─ 应用到全页：只提升日期和单值维度等可无损条件
```

完成率、通过率是聚合结果，当前 API 没有对应的全页查询参数，所以只在明细层筛选。
界面会明确提示，不能把它们伪装成已应用到原始快照的条件。

组合图采用数量左轴、比率右轴。实现依据分别是
[ECharts 多坐标轴能力](https://echarts.apache.org/handbook/en/concepts/axis/)和
[TanStack Table 受控筛选、排序模型](https://tanstack.com/table/latest/docs/guide/column-filtering)。
