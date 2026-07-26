# Quality Platform Lab

人工质检一站式平台的本地实验工程。当前切片把 ConfigManager、独立 PostgreSQL、验收快照、FastAPI 和 Vue 页面连成一条可运行的数据链。

工程目录和快照字段以原始质检平台资料中的当前实现为基线，不再使用早期实验自定义的 `quality_platform_lab` 包或 `lab-v1` 字段集。

## 当前可以做什么

1. 在项目 `.runtime/` 中启动隔离的 PostgreSQL 16；
2. 创建 `V20260709_01` JSONB 版快照表并写入可手工核算的实验数据；
3. 用 FastAPI 查询快照行和场景、组、员工三级聚合；
4. 在 Vue 页面查看验收图表、筛选并逐级下钻；
5. 主动添加 ECharts 统计卡片，或把表格当前筛选结果一键转成卡片。

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

最近一次真实验证结果见 [`docs/verification-report.md`](docs/verification-report.md)。

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

连接后在 `quality_lab` 数据库的 `manual_qc_lab` schema 中查看 `t_qc_daily_snapshot`。密码只用于修改数据库角色，不写入项目文件；TCP 只监听本机回环地址。使用完可关闭：

如果日志提示 `user "quality_lab", database "postgres"` 被拒绝，说明 Navicat
的“初始数据库”仍填成了 `postgres`；改为 `quality_lab` 即可，不需要放宽
`pg_hba.conf`。

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

详细边界见 [`docs/component-map.md`](docs/component-map.md)，最新表结构见 [`docs/snapshot-contract.md`](docs/snapshot-contract.md)。
