# AGENTS.md — Quality Platform Lab

本仓库是人工质检平台的本地实验实现。首要结果是让真实实验数据沿 PostgreSQL → FastAPI → Vue 页面完整运行。

## 当前范围

- 本地 ConfigManager 与 PostgreSQL 连接器；
- `lab-v1` 验收快照表、固定种子和三级聚合 API；
- 一站式平台外壳、DataWorkbench、验收快照图表和场景→组→员工下钻。

后续才加入采样预览、确认执行、状态回查和其他人工质检页面。

## 安全边界

- 只连接 `.runtime/postgres` 下的本地实验集群；
- 不连接、复制或探测任何材料中的内部数据库、Delta、OBS、SSO 或生产地址；
- 密码、Token、AK/SK、真实账号和内部路径不得写入 Git、日志、测试或前端；
- `.runtime/` 和 `.env` 永不提交；
- `lab-v1` 是实验契约，不得描述为生产 Schema。

## 工作方式

- 后端按 Router → Service → Repository → PostgreSQL 分层；SQL 只在 Repository；
- Vue 使用 Composition API、`<script setup lang="ts">`、typed props/emits；
- 优先验证真实数据库、API 和页面路径；单元测试只覆盖纯逻辑和稳定边界；
- 修改数据字段时按 DDL/SQL → Pydantic → TypeScript → 页面逐层对齐；
- 每次交付说明用户怎样启动、打开哪里、看到什么和如何判断通过。

项目入口见 `README.md`，组件边界见 `docs/component-map.md`，契约见 `docs/lab-v1-contract.md`。
