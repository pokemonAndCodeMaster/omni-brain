# 来源纠偏后的纵向切片验证记录

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

验证日期为 2026-07-26。运行数据位于 `.runtime/`，不进入 Git。

## 结果

| 验证项 | 实际结果 | 状态 |
|---|---|---|
| ConfigManager 单元测试 | 环境优先级、失败回载保护、别名、pickle、切换 env 共 7 项通过 | 通过 |
| PostgreSQL 初始化 | 当前用户独立集群，Unix socket 可连接 | 通过 |
| 来源目录对齐 | 后端采用 `src/api|config|database|manual_qc`，前端位于 `src/frontend` | 通过 |
| migration / seed | 旧实验平铺字段迁移为 18 字段 JSONB 结构，固定写入 16 条员工级快照；选项保留问题标签层 | 通过 |
| 数据库字段核对 | 18 个顶层字段顺序与 `V20260709_01` 显式清单一致 | 通过 |
| 确定性 SQL 核对 | 4 条日期—场景、4 条指定场景日期—组、4 条指定组日期—员工 | 通过 |
| FastAPI | health、rows、scene/group/employee 聚合可通过 HTTP 查询；rows 返回问题标签→选项→指标 | 通过 |
| Vue 组件回归 | 单滚动区、懒加载展开成功/失败、表头筛选、筛选结果制图和指标聚合共 7 项通过 | 通过 |
| Vue 类型与构建 | `vue-tsc` 通过，Vite 生产构建通过 | 通过（有 bundle 大小警告） |
| HTTP 数据链 | health、rows、scene 聚合和前端路由均可真实访问 | 通过 |
| Windows 最小化回弹 | 新开 Windows Edge 窗口后最小化，连续 20 次状态采样均保持最小化；源码也不存在主动聚焦/恢复窗口逻辑 | 页面侧未复现 |
| Windows Edge 页面渲染 | 使用 Windows Edge headless 打开真实路由并生成 1440×1200 截图 | 通过 |
| 筛选结果一键制图 | 在真实 Edge DOM 中将场景筛选为“城区交互”，表格由 4 行变 2 行，按钮显示 2 行；点击后生成 1 张 ECharts 卡片，来源上下文记录筛选和 2 行样本 | 通过 |

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

本轮已经完成“快照只读链 + 会话内统计卡片”，能够浏览、在列头筛选、逐级
懒加载，并把页面或表格筛选结果转成 ECharts 卡片。卡片支持主动添加、选择维度/
指标/图形、删除、图形切换和数据明细，但尚不保存布局。

平台还不包含采样配额、精确任务预览、人工确认、执行、部分失败和状态回查；
这些属于下一条“验收操作闭环”，不能把当前结果描述为完整人工质检平台。
