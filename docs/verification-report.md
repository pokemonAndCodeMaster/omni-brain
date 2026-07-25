# 首个纵向切片验证记录

## 验证对象

本记录验证的不是静态页面，而是以下真实数据链：

```text
YAML / .env
→ ConfigManager
→ 本地 PostgreSQL 16.14
→ SnapshotRepository / Service
→ FastAPI
→ Vue 验收快照页
```

验证日期为 2026-07-25。运行数据位于 `.runtime/`，不进入 Git。

## 结果

| 验证项 | 实际结果 | 状态 |
|---|---|---|
| ConfigManager 单元测试 | 环境优先级、失败回载保护、别名、pickle、切换 env 共 7 项通过 | 通过 |
| PostgreSQL 初始化 | 当前用户独立集群，Unix socket 可连接 | 通过 |
| migration / seed | 建表成功，固定写入 16 条员工级快照 | 通过 |
| 确定性 SQL 核对 | 4 条日期—场景、4 条指定场景日期—组、4 条指定组日期—员工 | 通过 |
| FastAPI | health、rows、scene/group/employee 聚合可通过 HTTP 查询 | 通过 |
| Vue 类型与构建 | `vue-tsc` 通过，Vite 生产构建通过 | 通过 |
| 浏览器真实加载 | 页面显示 4 条日期—场景结果与两场景图表 | 通过 |
| 浏览器三级下钻 | 场景展开到组，组展开到 `E001/E002` 员工 | 通过 |
| 浏览器控制台 | 修复响应式状态克隆问题后，交互过程 0 error | 通过 |

## 实际命令

```bash
scripts/postgres.sh init
.venv/bin/python -m quality_platform_lab.cli migrate
.venv/bin/python -m quality_platform_lab.cli seed
.venv/bin/python -m quality_platform_lab.cli health
.venv/bin/python -m quality_platform_lab.cli verify
.venv/bin/pytest

cd frontend
npm run build
```

## 当前能力边界

本轮已经完成“快照只读链”，能够浏览、筛选和三级下钻验收统计。它还不包含采样配额、精确任务预览、人工确认、执行、部分失败和状态回查；这些属于下一条“验收操作闭环”，不能把当前结果描述为完整人工质检平台。
