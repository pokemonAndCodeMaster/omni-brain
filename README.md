# Quality Platform Lab

人工质检一站式平台的本地实验工程。当前切片把 ConfigManager、独立 PostgreSQL、人工质检快照、FastAPI 和 Vue 页面连成一条可运行的数据链。

工程目录和快照字段以原始质检平台资料中的当前实现为基线，不再使用早期实验自定义的 `quality_platform_lab` 包或 `lab-v1` 字段集。

## 当前可以做什么

1. 在项目 `.runtime/` 中启动隔离的 PostgreSQL 16；
2. 创建 `V20260709_01` JSONB 版快照表并写入可手工核算的实验数据；
3. 用 FastAPI 查询快照行、旧四级聚合，以及按选定周期汇总的受控任务分析；
4. 在 Vue 页面先看标注产出，再看验收分配、完成和结论；总览同时展示全量与项目拆分；
5. 在同一张图中查看数量、Good/Bad 构成、Bad 问题选项和比率，或切换为按天趋势；
6. 添加、编辑、拖动和缩放总览卡片与 ECharts 统计卡片，配置文字、颜色、大小、布局、数据和图形；
7. 在任务汇总表中先比较标注、Good 占比、验收分配、完成和通过率；当前表格可按全部可见业务列筛选、排序与调整列；
8. 把卡片的查询、样式和布局保存到 PostgreSQL，重开页面时用最新快照重新计算并恢复。

## 快速开始

```bash
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

## 页面怎么用

页面从上到下分成四部分：

1. **全页数据范围：** 顶部日期、项目、标注任务、组和员工决定本页使用哪些快照，
   会同时刷新业务总览、固定统计图和逐级明细。
2. **业务总览：** 每张卡先给选定周期总量，再按项目拆分；点击卡片会跳到对应细分图。
   卡片右上角可编辑文字、颜色和字号，拖动或缩放后点击“保存总览”即可恢复。
3. **细分统计与个人看板：** 固定图可在“按任务/按天趋势”间切换；个人看板可添加
   柱图、折线、饼图或数量—比率双轴图，并保存独立的数据条件和样式。
4. **任务汇总：** 默认按选定周期的标注任务汇总，按“任务信息→标注情况→验收进度→验收结果”比较。表头点击排序，漏斗按钮筛选；
   任务和项目既可输入文字做包含筛选，也可勾选一个或多个精确值；数量和比率使用上下限筛选。
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
  manual_qc/
    snapshot/            快照 Repository 与 Service
  frontend/              Vue 一站式平台（app/features/shared）
scripts/postgres.sh     隔离数据库生命周期
```

详细边界见 [`docs/component-map.md`](docs/component-map.md)，最新表结构见
[`docs/snapshot-contract.md`](docs/snapshot-contract.md)，页面的信息顺序、图表和
后续切片见 [`docs/snapshot-page-plan.md`](docs/snapshot-page-plan.md)。
