# 来源纠偏后的纵向切片验证记录

## 验证对象

本记录验证的不是静态页面，而是以下真实数据链：

```text
YAML / .env
→ ConfigManager
→ 本地 PostgreSQL 16.14
→ SnapshotRepository / Service
→ FastAPI
→ Vue 人工质检快照页
```

验证日期为 2026-07-26。运行数据位于 `.runtime/`，不进入 Git。

## 结果

| 验证项 | 实际结果 | 状态 |
|---|---|---|
| ConfigManager 单元测试 | 环境优先级、失败回载保护、别名、pickle、切换 env 共 7 项通过 | 通过 |
| PostgreSQL 初始化 | 当前用户独立集群，Unix socket 可连接 | 通过 |
| 来源目录对齐 | 后端采用 `src/api|config|database|manual_qc`，前端位于 `src/frontend` | 通过 |
| migration / seed | 旧实验平铺字段迁移为 18 字段 JSONB 结构，固定写入 16 条员工级快照；选项保留问题标签层 | 通过 |
| 数据库字段核对 | 18 个顶层字段顺序与 `V20260709_01` 显式清单一致 | 通过 |
| 确定性 SQL 核对 | 16 条员工日快照、4 条日期—项目、8 条日期—标注任务、4 条指定任务日期—组、2 条指定任务组日期—员工 | 通过 |
| 字段业务语义 | `scene_name` 为标注任务/批次；`project_name` 只使用 `园区`、`城区/高速` | 通过 |
| FastAPI | health、rows、project/scene/group/employee 聚合可通过 HTTP 查询；rows 返回问题标签→选项→指标 | 通过 |
| Vue 组件回归 | 单滚动区、懒加载展开成功/失败、表头筛选、筛选结果制图和指标聚合共 7 项通过 | 通过 |
| Vue 类型与构建 | `vue-tsc` 通过，Vite 生产构建通过 | 通过（有 bundle 大小警告） |
| HTTP 数据链 | health、rows、scene 聚合和前端路由均可真实访问 | 通过 |
| Windows 最小化回弹隔离 | 用户现有 Edge 窗口仍可稳定复现；同一真实路由在独立用户目录、禁用扩展的 Edge 窗口最小化后连续 20 次采样均保持最小化；源码无主动聚焦/恢复窗口逻辑 | 页面代码侧未复现，现有 Edge 环境待排查 |
| Windows Edge 页面渲染 | Windows Edge 真实路由能恢复 1 张已保存卡片；项目为 2 个，标注任务为 4 个，编辑器能读取已保存标题、数据定义和样式 | 通过 |
| 卡片拖动与缩放 | 在真实浏览器中拖动后 `x: 0 → 3`，缩放后 `w: 6 → 7`、`h: 6 → 7`，页面进入未保存状态 | 通过 |
| 卡片编辑与恢复 | 在真实 Edge DOM 中把标题改为“卡片编辑与保存验证”，保存并刷新后准确恢复，再还原原标题并保存 | 通过 |
| 卡片保存与恢复 | 保存后刷新页面，布局、查询和样式从 `t_portal_view_config` 恢复；统计值按最新快照重新计算 | 通过 |
| Navicat TCP 路径 | 使用 `127.0.0.1:55432`、数据库/用户 `quality_lab` 和本轮重置密码完成 PostgreSQL 认证，服务端返回 IPv4 地址、端口、数据库和用户 | 后端通过，待用户在 Navicat 复核 |

## 实际命令

```bash
scripts/postgres.sh init
.venv/bin/python -m src.cli migrate
.venv/bin/python -m src.cli seed
.venv/bin/python -m src.cli health
.venv/bin/python -m src.cli verify
.venv/bin/pytest

cd src/frontend
npm test
npm run type-check
npm run build
```

## 当前能力边界

本轮已经完成“人工质检快照只读链 + 可保存统计看板”，能够先看标注、再看验收，
在列头筛选、逐级懒加载，并把页面或表格筛选结果转成 ECharts 卡片。卡片支持
编辑数据源、维度、指标、筛选、图形和样式，也支持拖动、缩放、刷新、删除和保存。
按日期、项目、标注任务、组或员工绘图时，点击数据项会同步筛选并跳到明细。

平台还不包含采样配额、精确任务预览、人工确认、执行、部分失败和状态回查；
也尚未实现标注任务—组—员工专用产出视图、验收覆盖矩阵和问题标签—选项专用
明细。这些边界与实施顺序见 `docs/snapshot-page-plan.md`，不能把当前结果描述为
完整人工质检平台。
