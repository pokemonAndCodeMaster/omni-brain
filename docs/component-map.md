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
| `SnapshotPage.vue` | 组装验收快照功能 | 使用 composable，把状态传给子组件 |

## 验收快照功能

| 组件或 composable | 单一职责 | 输入 / 输出 |
|---|---|---|
| `useSnapshotExplorer` | 管理查询、加载、错误、树数据和三级懒加载 | 输出只读状态与 `load/reset/expand` 动作 |
| `SnapshotFilters.vue` | 编辑日期、场景和组筛选 | `modelValue`；发出 `submit`、`reset` |
| `SnapshotSummaryChart.vue` | 把场景聚合展示为 ECharts 图 | `rows` |
| `SnapshotDataTable.vue` | 定义领域列并连接 DataWorkbench | `rows`、`loadingKeys`；发出 `expand` |

## 共享组件

| 组件 | 单一职责 | 输入 / 输出 |
|---|---|---|
| `DataWorkbench.vue` | 管理通用表格状态和渲染 | 行、列、编辑器、展开规则；发出编辑、选择、状态、展开 |
| `HeaderFilter.vue` | 在列头内提供文本、枚举和日期筛选入口 | 列筛选值；发出更新与清除 |
| `WorkbenchToolbar.vue` | 展示行数、选择、筛选和列管理动作 | 统计与列描述；发出工具栏动作 |
| `BaseCheckbox.vue` | 提供可访问的二态/三态复选框 | `modelValue`、`indeterminate`；发出更新 |
| `BaseEChart.vue` | 管理 ECharts 生命周期 | `option` |

**表格状态：** TanStack Table 负责排序、筛选、列顺序、列宽、选择和展开状态；Vue 组件负责交互与视觉。服务端懒加载子行时，只有成功取得子行后才把父行置为展开，避免“减号已出现但数据尚未展开”的伪状态。

**数据流：** props 向下，typed events 向上。路由页不直接拼 API，不把 SQL 或指标公式放入共享组件。
