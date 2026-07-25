# Quality Platform Lab

人工质检一站式平台的本地实验工程。第一条纵切把 ConfigManager、独立 PostgreSQL、验收快照、FastAPI 和 Vue 页面完整连起来。

## 当前可以做什么

1. 在项目 `.runtime/` 中启动隔离的 PostgreSQL 16；
2. 创建 `lab-v1` 快照表并写入可手工核算的实验数据；
3. 用 FastAPI 查询快照行和场景、组、员工三级聚合；
4. 在 Vue 页面查看验收图表、筛选并逐级下钻。

## 快速开始

```bash
cp .env.example .env
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'

scripts/postgres.sh init
.venv/bin/python -m quality_platform_lab.cli migrate
.venv/bin/python -m quality_platform_lab.cli seed

.venv/bin/uvicorn quality_platform_lab.api.app:create_app --factory --reload --port 8000
```

另开终端：

```bash
cd frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173/manual-qc/snapshots`。

## 验证

```bash
.venv/bin/python -m quality_platform_lab.cli health
.venv/bin/python -m quality_platform_lab.cli verify
.venv/bin/pytest

cd frontend
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

## 目录

```text
config/                 安全默认配置
docs/                   组件与 lab-v1 契约
migrations/             DDL
seeds/                  固定实验数据
src/quality_platform_lab/
  config.py             ConfigManager
  database.py           PostgreSQL 公共能力
  manual_qc/acceptance/ 快照 Repository 与 Service
  api/                   FastAPI Schema 与 Router
frontend/               Vue 一站式平台
scripts/postgres.sh     隔离数据库生命周期
```
