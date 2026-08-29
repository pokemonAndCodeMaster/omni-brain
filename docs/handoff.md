# 人工质检实验接力报告

> 更新时间：2026-08-29
> 仓库：`/home/yyh/project/quality-platform-lab`
> 分支：`feature/agent-workbench-opencode-v1`
> 功能基线：待提交的 Agent Runtime 纵切

## 1. 当前结论

本仓库已经不是静态 Demo，而是一条可运行、可验证的本地实验链：

```text
确定性实验数据
  → 本地 PostgreSQL 16
  → Repository / Service
  → FastAPI 受控分析接口
  → Vue 人工质检分析工作台
```

当前完成的是**人工质检标注与验收的只读分析工作台**。用户可以从业务总览进入多图层
统计图，再进入任务明细，按任务 → 日期 → 组 → 标注员逐级查看标注、Good/Bad、
验收分配、完成、通过、打回和问题选项。

2026-08-29 新增了同一平台内的 **OpenCode-only Agent Runtime**：Agent 定义从发布
Harness 注册表读取，Run 元数据和规范事件进入现有 PostgreSQL；Vue 列表使用摘要接口，
只有选中具体 Run 才加载 prompt、结果与增量 trace。React、SQLite 和 Codex 不属于该纵切。

当前阶段已经收口。下一位模型不应继续做无目的的组件抽象、V1 清理或页面微调，而应先
和用户确认下一项真实业务结果。

## 2. 后续模型的阅读顺序

1. [`../AGENTS.md`](../AGENTS.md)：当前操作边界和安全规则；
2. [`../README.md`](../README.md)：启动、页面使用和数据库访问；
3. 本报告：当前状态、未决问题和续接方式；
4. [`snapshot-contract.md`](snapshot-contract.md)：快照粒度、字段与业务语义；
5. [`component-map.md`](component-map.md)：后端、Vue、表格和卡片边界；
6. [`verification-report.md`](verification-report.md)：已经跑过的真实证据；
7. [`archive/README.md`](archive/README.md)：只有需要追溯设计理由时才进入历史方案。

归档文档中的“下一步”“建议新增”不再自动生效。当前行为以源码、规范文档和新鲜运行
结果为准。

## 3. 用户当前能拿到什么

打开：

```text
http://127.0.0.1:5173/manual-qc/snapshots
http://127.0.0.1:5173/ai/agents
http://127.0.0.1:5173/ai/runs
```

页面从上到下包括：

1. **全页范围：** 日期、项目、标注任务、组和标注员；
2. **业务总览：** 3 张 V2 总览卡，支持内容块、项目/任务/组拆分、编辑、复制、
   恢复、拖动、缩放和保存；
3. **统计看板：** 当前保存 5 张 V2 图表卡，支持多图层、柱/线/面积、数量/比例双轴、
   图层拆分、公共/图层筛选、实时图表和聚合数据预览；
4. **任务分析表：** 默认 24 个任务，逐级展开 14 个日期、组和标注员；
5. **指标详情：** 点击 Good 占比、完成率或通过率，查看整体、Good/Bad、趋势和
   问题标签—选项；问题选项可以固定为可筛选、可排序的列。

顶部范围作用于全页。表头聚合筛选默认只影响任务表，只有日期、单个项目或单个任务等
可以无损表达的条件，才允许显式提升到全页或统计卡片。

## 4. 关键业务语义

- `scene_name` 是**标注任务名/批次名**，不是项目；
- `project_name` 是项目，当前实验值只有 `园区`、`城区/高速`；
- 一行快照粒度是
  `stat_date × project_name × scene_name × group_name × employee_id`；
- 问题信息必须保留“问题标签 → 问题选项”两层；
- 百分比使用聚合后的总分子 ÷ 总分母，禁止平均员工行百分比；
- 分母为零返回 `null`，页面显示 `—`；
- 问题选项可能多选，占 Bad 比例之和不保证等于 100%；
- 没有业务方确认的统一阈值时，不擅自把 80% 等数字标成风险。

完整字段以 [`snapshot-contract.md`](snapshot-contract.md) 为准。

## 5. 当前技术结构

### 5.1 后端

```text
src/config/                    ConfigManager
src/database/                  PostgreSQL connector / manager
src/manual_qc/snapshot/        快照行与旧四级聚合
src/manual_qc/analysis/        指标目录、受控查询、动态问题选项
src/portal/                    视图配置保存
src/agent_runtime/             OpenCode Run 编排、PostgreSQL 元数据/事件、worktree
src/api/routers/               FastAPI 路由
src/api/schemas/               Pydantic HTTP / 配置契约
```

依赖方向是：

```text
Router → Service → Repository → Connector → PostgreSQL
```

SQL 只能进入 Repository。分析接口只接受白名单指标、维度、筛选和分组，不接受自由
SQL 或任意公式。

### 5.2 前端

```text
src/frontend/src/features/manual-qc/pages/SnapshotPage.vue
  页面组合与全页范围

src/frontend/src/features/manual-qc/analysis/
  任务树、指标详情、受控查询和表格配置

src/frontend/src/features/manual-qc/utils/snapshotChart.ts
  人工质检图表预设、V1→V2 迁移、V2 查询解析

src/frontend/src/features/manual-qc/utils/snapshotOverview.ts
  总览卡片定义、迁移和当前快照结果解析

src/frontend/src/shared/data-workbench/
  TanStack Table 通用状态和表头筛选

src/frontend/src/shared/dashboard/
  GridStack、总览卡、图表卡、多图层编辑器和持久化

src/frontend/src/features/agent-runtime/
  Agent 摘要目录、按需启动、Run 摘要列表、详情和增量 trace
```

通用组件只负责呈现和交互；人工质检指标、问题选项语义和预设留在人工质检 feature。

### 5.3 数据和配置

本地 schema：

```text
manual_qc_lab.t_qc_daily_snapshot
manual_qc_lab.t_portal_view_config
manual_qc_lab.t_agent_run
manual_qc_lab.t_agent_run_event
```

当前确定性种子：

- 14 天；
- 2 个项目；
- 24 个任务；
- 12 个组；
- 120 名轮换标注员；
- 3024 条员工日快照；
- 2 个问题标签，每个标签 4 个选项。

视图配置使用三个独立 page key：

| page key | 内容 | 当前本机状态 |
|---|---|---|
| `manual-qc-snapshot-overview` | 总览卡片 | `dashboard-v2`，3 张卡 |
| `manual-qc-snapshots` | 统计图表 | `dashboard-v2`，5 张卡 |
| `manual-qc-task-analysis` | 任务表列与固定问题选项 | 当前使用默认配置 |

保存的是定义和布局，不保存会过期的统计结果。页面重开后使用最新快照重新计算。

## 6. 启动和恢复

首次准备：

```bash
cd /home/yyh/project/quality-platform-lab
cp .env.example .env
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'

scripts/postgres.sh init
.venv/bin/python -m src.cli migrate
.venv/bin/python -m src.cli seed
```

启动后端：

```bash
.venv/bin/uvicorn src.api.app:create_app --factory --reload --port 8000
```

另开终端启动前端：

```bash
cd /home/yyh/project/quality-platform-lab/src/frontend
npm install
npm run dev
```

状态检查：

```bash
cd /home/yyh/project/quality-platform-lab
scripts/postgres.sh status
curl http://127.0.0.1:8000/api/health
```

编写本报告时，PostgreSQL、FastAPI 和 Vite 分别监听 `127.0.0.1:55432`、`:8000`
和 `:5173`。这是临时运行状态；后续会话必须重新检查，不能假定进程始终存在。

Windows Navicat 使用 `127.0.0.1:55432`、数据库/用户 `quality_lab`。密码必须通过
`scripts/postgres.sh enable-tcp` 在本机设置，不得从聊天、日志或 Git 中寻找或写入密码。

## 7. 验证基线

运行：

```bash
cd /home/yyh/project/quality-platform-lab
.venv/bin/pytest

cd src/frontend
npm test
npm run type-check
npm run build
```

当前基线：

- Python：18 项通过；
- Vue/Vitest：32 项通过；
- `vue-tsc`：通过；
- Vite 生产构建：通过，仍有单 bundle 超过 500 kB 的警告；
- OpenCode 真实纵链：`run-20260829-154845-cd07a9` 成功，session、worktree、最终文本和
  规范事件均由 PostgreSQL API 回读；
- 真实页面：5 张图表、24 个任务、首个任务展开得到 14 个日期；
- 图表卡增高一格时，卡片、内容区、ECharts 容器和 canvas 同步增加 58px。

详细用户路径和核算值见 [`verification-report.md`](verification-report.md)。CSS、拖拽、
弹窗和 ECharts 尺寸问题必须使用真实浏览器验证，不能只以 jsdom 测试通过为结论。

## 8. 已完成且不要重复建设

- ConfigManager、本地 PostgreSQL connector 和数据库生命周期脚本；
- `V20260709_01` JSONB 快照表、migration 和确定性种子；
- 受控指标目录、查询与 facets；
- 任务 → 日期 → 组 → 标注员四级分析；
- Good/Bad、问题标签与选项详情；
- TanStack Table 表头筛选、排序、独立列宽、列配置和懒加载；
- 可组合总览卡片 V2；
- 多图层统计图 V2、系统预设、实时预览、保存和恢复；
- GridStack 拖动缩放与 ECharts 尺寸联动；
- V1 固定统计图和日期—项目表的死代码清理。

V1 配置类型和旧四级 API 仍承担迁移、回退或顶部范围数据职责，不能因为名称中有 V1
就直接删除。

## 9. 当前边界与已知问题

### 9.1 产品边界

当前仍是**只读分析工作台**，尚未实现：

- 验收覆盖矩阵；
- 预期分配与实际分配缺口定位；
- 采样配额与任务选择；
- 执行前预览和人工确认；
- 任务下发、部分失败、重试、执行结果和状态回查；
- 多用户权限、共享视图和冲突合并。

### 9.2 技术边界

- 总览仍从当前范围的原始快照行在浏览器端汇总；统计图和任务表主要使用后端受控查询；
- 总览、图表和任务表目前分别保存，不存在统一的“保存整页”动作；
- V1 配置迁移与旧聚合 API 有意保留；
- 生产构建有 bundle 大小警告，当前数据量没有证明必须立即拆包；
- 普通汇总继续使用 PostgreSQL，未引入缓存、物化视图或专用分析存储。

这些是已知边界，不应自动变成下一轮基础设施任务。只有真实业务工况被阻塞时才处理。

### 9.3 Windows Edge 最小化回弹

用户观察到页面打开一段时间后，Windows Edge 最小化可能立即回弹。现有证据：

- 独立、禁用扩展的浏览器实例未复现；
- 源码没有 `window.focus()`；
- 审计期间没有捕获到主动 `focus()` 或 `showModal()`；
- 筛选输入框和两个编辑弹窗已经增加“页面不可见时禁止聚焦”的保护。

因此目前只能称为**防御性修复，根因未证实**。若再次复现，应记录发生时间、当时是否
打开过表头筛选或卡片编辑器，并在真实 Windows Edge 环境继续取证；不能写成已彻底解决。

## 10. 下一步候选

下一步尚未由用户最终选择。推荐顺序如下。

### 候选 A：验收覆盖与配额缺口

真实问题：验收是否分够，漏在什么任务、组、人员、Good/Bad 或问题选项。

可用基础：快照已经有 `expect_alloc`、`actual_alloc`、项目、任务、组、人员、
Good/Bad 和问题选项。

预期结果：

- 先给任务级覆盖和预期/实际差额；
- 再进入任务 × 组/人员/结果类型/问题选项矩阵；
- 点击缺口单元格进入现有任务详情或后续采样入口。

这是当前最自然的分析能力延伸，但开始实现前仍要和用户确认“分够”“覆盖”“均匀”的
业务规则和容忍阈值。

### 候选 B：验收操作闭环

真实问题：从分析发现缺口后，怎样形成采样、预览、确认、执行和状态回查。

建议不要一次实现全链路。应从一个最薄闭环开始：

```text
选择任务和配额
→ 预览将下发的样本
→ 人工确认
→ 写入本地实验任务
→ 展示成功、失败与回查状态
```

不得连接材料中的生产数据库、OBS、Delta、SSO 或内部接口。

## 11. 下一位模型的工作协议

1. 先执行 `git status --short`，保留用户已有修改；
2. 读取本报告和当前规范，不从归档方案直接开工；
3. 用普通语言说明本轮用户、场景、输入、操作、输出和验收证据；
4. 新业务切片先完成用户工作流、数据结构、组件边界和技术选项，经用户确认后再实现；
5. 复用当前页面、分析接口、表格和卡片，不新建平行 Demo；
6. 先跑真实数据库/API/页面用户路径，再用必要测试覆盖稳定边界；
7. 每轮汇报具体改了什么、为什么、得到什么效果和仍缺什么；
8. 完成后更新本报告的当前状态或用新的接力报告替换，不在文件末尾无限追加流水账。

## 12. 原始材料

主要原始质检材料位于：

```text
/home/yyh/project/omni-brain/knowledge/raw/quality_check/
```

当前有 25 个 `.txt` 文件，实际内容为 Markdown。它们涉及顶层架构、后端分层、
数据库访问、快照、人工质检、验收采样、执行状态、前端页面和公共组件。

原始材料只能读取和引用，不得覆盖或“顺手整理”。需要改变知识体系时回到 Omni-Brain
仓库按其知识摄入与治理规则处理；本实验仓库只保存实现、当前契约和验证证据。
