# 组件边界

## 后端与公共能力

| 组件 | 单一职责 | 不负责 |
|---|---|---|
| `ConfigManager` | 合并 YAML、替换环境变量、管理连接别名与原子重载 | 建立数据库连接、保存秘密 |
| `DatabaseManager` | 按别名创建并复用 PostgreSQL connector | 编写业务 SQL |
| `PGConnector` | 连接池、只读查询、写事务和批量写 | 验收业务判断 |
| `SnapshotRepository` | 快照行查询与三级聚合 SQL | HTTP 和页面状态 |
| `SnapshotQueryService` | 聚合级别和必填筛选的业务边界 | 拼接 SQL |
| FastAPI Router | 校验 HTTP 参数并调用 Service | 直接访问数据库 |

数据依赖方向固定为 `Router → Service → Repository → Connector → PostgreSQL`。

物理目录对齐目标资料：`src/api/routers/`、`src/api/schemas/`、`src/config/config_loader.py`、`src/database/pg_connector.py` 和 `src/manual_qc/snapshot/`。

## Vue 组件边界

## 应用层

| 组件 | 单一职责 | 输入 / 输出 |
|---|---|---|
| `App.vue` | 渲染应用外壳 | 无 |
| `AppShell.vue` | 提供侧边栏、顶栏和路由内容区 | 读取路由元数据，不拥有领域状态 |
| `SnapshotPage.vue` | 组装验收快照与页面级统计卡片 | 使用 composable，把状态传给子组件；持有卡片状态 |

## 验收快照功能

| 组件或 composable | 单一职责 | 输入 / 输出 |
|---|---|---|
| `useSnapshotExplorer` | 管理查询、加载、错误、树数据和三级懒加载 | 输出只读状态与 `load/reset/expand` 动作 |
| `SnapshotFilters.vue` | 编辑日期、场景和组筛选 | `modelValue`；发出 `submit`、`reset` |
| `SnapshotSummaryChart.vue` | 把场景聚合展示为 ECharts 图 | `rows` |
| `SnapshotDataTable.vue` | 定义领域列并连接 DataWorkbench | `rows`、`loadingKeys`；发出展开和当前筛选制图请求 |
| `snapshotChart.ts` | 按维度聚合验收指标，产出可渲染卡片 | 快照行、维度、指标和来源上下文 |

## 共享组件

| 组件 | 单一职责 | 输入 / 输出 |
|---|---|---|
| `DataWorkbench.vue` | 管理通用表格状态和渲染 | 行、列、编辑器、展开规则；发出编辑、选择、状态、展开和当前筛选制图请求 |
| `HeaderFilter.vue` | 在列头内提供文本、枚举和日期筛选入口 | 列筛选值；发出更新与清除 |
| `WorkbenchToolbar.vue` | 展示行数、选择、筛选、制图和列管理动作 | 统计与列描述；发出工具栏动作 |
| `BaseCheckbox.vue` | 提供可访问的二态/三态复选框 | `modelValue`、`indeterminate`；发出更新 |
| `BaseEChart.vue` | 管理 ECharts 生命周期和尺寸响应 | `option`、可访问标签和最小高度 |
| `DashboardGrid.vue` | 展示卡片集合及添加入口 | 卡片列表；发出添加、删除、图形切换 |
| `CardShell.vue` | 统一卡片标题、动作、内容和来源区 | 插槽；发出删除 |
| `ChartCard.vue` | 把统计卡片规格渲染为 ECharts 与可读数据表 | 卡片；发出删除和图形切换 |
| `ChartBuilderDialog.vue` | 选择标题、维度、指标和图形 | 构建选项；发出结构化制图参数 |
| `useDashboardCards` | 管理当前页面卡片集合 | `add/remove/changeChartType` |

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

当前已实现列头筛选、排序、调宽、显隐、顺序、选择和树形懒加载。下一批只有在
真实数据量或操作工况触发时，再接列固定、分面筛选、服务端分页与虚拟滚动。
统计卡片是独立的 Dashboard 能力，通过“当前筛选结果”这一语义事件连接表格，
不侵入 TanStack 内核。

当前卡片状态只存在于页面会话。拖拽/缩放、布局持久化、共享权限和版本恢复尚未
实现，不能把这一切片描述为完整可配置看板。
