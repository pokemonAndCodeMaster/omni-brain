# Omni-Brain 质量与 AI 协作平台

Omni-Brain 主线内的 Vue3 + FastAPI + PostgreSQL 产品应用。当前同时提供团队 Idea、候选/正式
Requirement、人机时间线、Codex/OpenCode 双执行器和人工质检数据链。

工程目录和快照字段以原始质检平台资料中的当前实现为基线，不再使用早期实验自定义的 `quality_platform_lab` 包或 `lab-v1` 字段集。

## 当前可以做什么

1. 在项目 `.runtime/` 中启动隔离的 PostgreSQL 16；
2. 创建 `V20260709_01` JSONB 版快照表并写入 14 天、24 个任务、12 个组、
   120 名轮换标注员的确定性实验数据；
3. 用 FastAPI 查询快照行、旧四级聚合，以及按选定周期汇总的受控任务分析；
4. 在 Vue 页面先看标注产出，再看验收分配、完成和结论；总览可组合指标、说明以及
   项目/任务/组拆分，并独立设置主指标与逐块样式；
5. 在同一张统计卡片中叠加多个柱形、折线或面积图层；分别配置指标、数量/比例轴、
   项目/任务/组/人员/问题选项拆分、公共筛选和图层筛选，并把任务横轴改为按日趋势；
6. 添加、编辑、复制、恢复、拖动和缩放总览卡片与 ECharts 统计卡片，并把定义保存到 PostgreSQL；
7. 在任务汇总表中先比较标注、Good 占比、验收分配、完成和通过率，再按任务 →
   日期 → 组 → 标注员逐级展开；
8. 点击 Good 占比、完成率或通过率查看整体、Good/Bad、按日趋势和问题选项详情，
   并把关注的问题选项固定为可筛选、可排序的新列；
9. 把卡片的查询、样式和布局，以及任务表列配置保存到 PostgreSQL；重开页面时
   用最新快照重新计算并恢复。
10. 在同一 Vue3 平台记录不可覆盖的 Idea，并把它转成带 Revision 的 candidate Requirement；
11. 由固定服务端身份 `admin` 记录人的消息、Agent Run 和接纳/驳回/延期/合并决定；
12. 查看已发布能力的轻量目录和历史 Run 计数，按能力默认或显式选择 Codex/OpenCode；
13. 在 PostgreSQL 中保存 Run 元数据和规范事件，选择具体 Run 后再读取完整任务、结果与
    `after_sequence` 增量 trace。
14. 从 accepted Requirement 创建共享 worktree 的 Work 与固定六步
    `standard_development_v1`，逐步启动/重试 Run、确认 Gate、刷新 Git/验证证据并记录人工交付决定。

## 快速开始

```bash
cd /home/yyh/project/omni-brain/apps/quality-platform
cp .env.example .env
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'

scripts/postgres.sh init
.venv/bin/python -m src.cli migrate
.venv/bin/python -m src.cli seed

.venv/bin/uvicorn src.api.app:create_app --factory --reload --port 8000
```

另开终端：

```bash
cd src/frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173/manual-qc/snapshots`。

Agent 入口：

- `http://127.0.0.1:5173/ai/ideas`：Idea Inbox、讨论、Agent 动作与转候选需求；
- `http://127.0.0.1:5173/ai/requirements`：candidate/accepted Requirement、Revision 与评审；
- `http://127.0.0.1:5173/ai/works`：Work 队列、固定计划、Run、Git 证据与人工接受；
- `http://127.0.0.1:5173/ai/agents`：能力目录与启动入口；
- `http://127.0.0.1:5173/ai/runs`：轻量 Run 列表和按需详情/trace。

Agent Runtime 从主线根目录的 `config/agent-registry.yaml` 与 `harness.yaml` 读取已登记能力，
并以同一个主线版本建立 Run worktree。它同时支持 `codex exec --json` 与
`opencode run --format json`。开发、方案和
协作动作默认 Codex，评测/对照默认 OpenCode；能力允许时可以显式切换。OpenCode 默认
使用本机随机端口，也可通过 `OPENCODE_ENDPOINT` 连接已登记 server。worktree 只隔离
代码和文件，不充当进程、端口或租户隔离；S1 仍是单仓单写入、单执行并发。独立 Run 默认建立
自己的 worktree；进入 Work 后，六个步骤复用 Work 的同一个 worktree 和分支。
Work 中的 OpenCode 验证/审查 Run 通过运行时 inline permission 禁用编辑、外部目录和未列入白名单的
shell 命令；显式切换 OpenCode 做开发时允许工作区写入，但仍拒绝 Push、Merge 和创建 PR/MR。

需要保留旧控制台中的 OpenCode 历史时，迁移一次：

```bash
.venv/bin/python scripts/import_opencode_runs.py
```

脚本只导入 `executor=opencode` 的 Run 与事件；重复执行按 Run ID 跳过，不导入 Codex。

## 页面怎么用

页面从上到下分成四部分：

1. **全页数据范围：** 顶部日期、项目、标注任务、组和员工决定本页使用哪些快照，
   会同时刷新业务总览、固定统计图和逐级明细。
2. **业务总览：** 每张卡可按顺序组合指标块、说明块和一个项目/任务/组拆分块；主指标、
   各指标名称、字号、颜色和宽度都可独立编辑。右上角可复制或恢复系统预设，拖动或缩放
   后点击“保存总览”，重开页面会按最新快照重算。
3. **细分统计与个人看板：** 四张系统预设分别覆盖标注数量与质量、Bad 问题排行、
   验收分配与完成、验收通过与打回。它们与自定义卡片使用同一套多图层编辑器：
   共享一个横轴，每个图层独立选择指标、柱形/折线/面积、坐标轴、拆分、筛选和样式。
   编辑时右侧持续显示真实聚合图和数据表；任务较多时可横向缩放和平移，横向排行则
   使用纵向缩放。卡片可复制、恢复系统预设、拖动、缩放和保存。
4. **任务分析：** 默认按选定周期的标注任务汇总，按“任务路径→标注情况→验收进度→验收结果”比较，并可逐级展开日期、组和标注员。表头点击排序，漏斗按钮筛选；
   任务和项目既可输入文字做包含筛选，也可勾选一个或多个精确值；统计日期使用起止
   日期筛选，数量和比率使用上下限筛选。任务、日期、组和标注员属于同一条下钻路径：
   筛选下级对象时会保留必要的上级路径，后续展开的新明细会自动应用当前筛选。
   点击 Good 占比、完成率或通过率可打开详情，把问题选项固定为列后点击“保存表格”
   即可跨刷新恢复；一次性的筛选和展开状态不会保存。
   日期或单个项目/任务等条件可点“应用到全页”。完成率、通过率等聚合条件会明确
   保留在明细层，不会被错误转换成另一种数据口径。

## 验证

```bash
.venv/bin/python -m src.cli health
.venv/bin/python -m src.cli verify
.venv/bin/pytest

cd src/frontend
npm test
npm run type-check
npm run build
```

最近一次真实 Edge 浏览器与数据链验证结果见
[`docs/verification-report.md`](docs/verification-report.md)。

数据库状态：

```bash
scripts/postgres.sh status
scripts/postgres.sh stop
```

删除 `.runtime/postgres` 即可清理全部数据库实验状态。`scripts/postgres.sh reset` 会执行同样的破坏性重建，需显式输入确认。

## Windows Navicat 连接

项目默认只开 Unix socket，避免本地实验数据库无意暴露到网络。需要从 Windows Navicat 访问时，在 WSL 项目目录执行：

```bash
QC_DB_PASSWORD='请替换为你自己的本地密码' scripts/postgres.sh enable-tcp
```

当前机器的 WSL 使用 mirrored networking，Navicat 新建 PostgreSQL 连接时填写：

| 配置项 | 值 |
|---|---|
| 主机 | `127.0.0.1` |
| 端口 | `55432` |
| 初始数据库 | `quality_lab` |
| 用户名 | `quality_lab` |
| 密码 | 上一步的 `QC_DB_PASSWORD` |
| SSL | 关闭 |

必须填写 `127.0.0.1`，不要填写 `localhost`；Windows 可能把后者解析成当前实验库没有监听的 IPv6 `::1`。连接后在 `quality_lab` 数据库的 `manual_qc_lab` schema 中查看 `t_qc_daily_snapshot` 和 `t_portal_view_config`。密码只用于修改数据库角色，不写入项目文件；TCP 只监听本机回环地址。使用完可关闭：

如果日志提示 `password authentication failed`，说明已经到达正确的 PostgreSQL，
但 Navicat 保存的密码与最近一次 `enable-tcp` 设置的不一致；重新运行该命令并在
Navicat 中同步更新密码。若提示 `database "postgres"` 被拒绝，则把“初始数据库”
改为 `quality_lab`，不需要放宽 `pg_hba.conf`。

```bash
scripts/postgres.sh disable-tcp
```

## 目录

```text
config/                 安全默认配置
docs/                   组件、快照契约与验证记录
migrations/             DDL
seeds/                  固定实验数据
src/
  api/
    routers/             FastAPI 路由
    schemas/             HTTP 数据契约
  config/
    config_loader.py     ConfigManager
  database/
    pg_connector.py      PostgreSQL 公共能力
  agent_runtime/         Codex/OpenCode Run、worktree、PostgreSQL Repository/Service
  collaboration/         Idea、Requirement、Revision、Decision 与时间线
  work/                  Work、固定计划、步骤 Gate、Git 证据与交付决定
  manual_qc/
    snapshot/            快照 Repository 与 Service
  frontend/              Vue 一站式平台（app/features/shared）
scripts/postgres.sh     隔离数据库生命周期
scripts/import_opencode_runs.py  旧 OpenCode 历史的一次性导入
```

后续模型从 [`docs/handoff.md`](docs/handoff.md) 续接。详细边界见
[`docs/component-map.md`](docs/component-map.md)，最新表结构见
[`docs/snapshot-contract.md`](docs/snapshot-contract.md)，真实验证证据见
[`docs/verification-report.md`](docs/verification-report.md)。已经实施完毕的设计与页面
规划位于 [`docs/archive/`](docs/archive/README.md)，只用于追溯历史取舍。
