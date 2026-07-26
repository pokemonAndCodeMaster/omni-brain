# AGENTS.md — Quality Platform Lab

本仓库是人工质检平台的本地实验实现。首要结果是让真实实验数据沿 PostgreSQL → FastAPI → Vue 页面完整运行。

## 当前范围

- 本地 ConfigManager 与 PostgreSQL 连接器；
- `V20260709_01` JSONB 版人工质检快照表、固定种子和四级聚合 API；
- 已验证的 V2 前四个切片：指标目录与受控查询、任务优先四级明细、可组合总览卡片、
  可叠加多图层统计图；
- 一站式平台外壳、DataWorkbench 与标注→验收总览；V1 的项目→任务→组→员工 API 保留为迁移基线，页面根表已切换为 V2 跨周期任务汇总；
- 由指标块、说明块和项目/任务/组拆分块组成，可编辑、复制、恢复、拖拽缩放并保存到
  本地 PostgreSQL 的业务总览；
- 数量—比率双轴图、按天趋势、Bad 问题排行和明细数值范围筛选。

多图层图表已经通过真实页面验证：横轴、指标、图形、数量/比例轴、拆分、公共/图层筛选
和样式可分别配置，编辑时持续显示真实聚合预览，保存后按最新数据恢复。下一切片只做
V1 重复实现清理和整页回归；后续业务扩展才加入采样预览、确认执行、状态回查和其他
人工质检页面。

## 安全边界

- 只连接 `.runtime/postgres` 下的本地实验集群；
- 不连接、复制或探测任何材料中的内部数据库、Delta、OBS、SSO 或生产地址；
- 密码、Token、AK/SK、真实账号和内部路径不得写入 Git、日志、测试或前端；
- `.runtime/` 和 `.env` 永不提交；
- 表结构对齐原始资料的 `V20260709_01` 当前版本，但本仓库和数据仍是本地实验实现，不得描述为生产系统。

## 工作方式

- 后端按 Router → Service → Repository → PostgreSQL 分层；SQL 只在 Repository；
- Vue 使用 Composition API、`<script setup lang="ts">`、typed props/emits；
- 顶部筛选定义全页数据范围，表头筛选默认只影响明细；只有用户显式点击
  “应用到全页”时才转换可无损表达的条件，不得悄悄改变所有图表；
- 优先验证真实数据库、API 和页面路径；单元测试只覆盖纯逻辑和稳定边界；
- 修改数据字段时按 DDL/SQL → Pydantic → TypeScript → 页面逐层对齐；
- 每次交付说明用户怎样启动、打开哪里、看到什么和如何判断通过。

项目入口见 `README.md`，组件边界见 `docs/component-map.md`，契约见 `docs/snapshot-contract.md`。
