# 人工质检与验收知识入口

这套候选知识帮助没有背景的读者理解人工质检如何从需求登记、交付任务和行动项，经过数据准备、标注、验收、结论执行与返工，走到可交付结果；同时说明人员与权限、平台模块、统一数据工作台和当前仓库原型分别处于什么现实状态。

内容按长期维护主题组织，融合了既有历史、目标设计、人工决定和当前原型证据。新增的交付、人员、平台共享能力和前端状态材料已经归入相应主题，但目标设计或材料中的完成声明不等于页面、API、SSO、生产数据库或端到端闭环已经部署。

## 第一次学习，从这条主线开始

1. [质检领域位置](views/by-domain/quality.md)：先分清质检、人工质检与验收的上下级关系，以及当前知识能讲到的深度。
2. [人工质检全貌](domains/quality/manual/overview.md)：理解交付任务、规则与数据准备、标注、验收、结论执行、返工和交付确认之间的业务链。
3. [交付与行动项](domains/quality/manual/delivery-management.md)：理解任务字段、四类状态轴、风险和非标准事项怎样支持持续推进。
4. [验收总览](domains/quality/manual/acceptance/overview.md)：建立验收业务、数据、算法和软件的整体地图。
5. [验收学习与任务旅程](views/by-journey/manual-qc-acceptance.md)：按“业务机制 → 数据与规则 → 软件实现 → 可信边界”继续深入。

读完这条路线，应该能够解释交付完成为什么不等于标注任务创建、验收样本为什么不等于执行全集、PASS 为什么不等于交付完成，以及遇到生产问题时还缺哪些直接证据。

## 已经知道问题时，直接进入对应主题

| 想解决的问题 | 入口 | 继续下钻 |
|---|---|---|
| 人工质检和验收处于什么位置 | [领域视图](views/by-domain/quality.md) | [人工质检平台与模块](domains/quality/manual/platform-and-module-map.md) |
| 一个交付任务怎样推进到可交付结果 | [交付与行动项](domains/quality/manual/delivery-management.md) | [人工质检全貌](domains/quality/manual/overview.md) |
| 标注、验收、结论和执行有什么区别 | [验收生命周期](domains/quality/manual/acceptance/lifecycle.md) | [结论与执行](domains/quality/manual/acceptance/conclusion-and-execution.md) |
| 人员、分组、SCD2 和权限怎样定义 | [人员与权限](domains/quality/manual/personnel-and-permissions.md) | [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md) |
| 统一数据工作台共享什么契约 | [统一数据工作台](capabilities/quality-data-workbench.md) | [平台与模块地图](domains/quality/manual/platform-and-module-map.md) |
| 历史上怎样抽样和分配 | [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md) | [历史来源](sources/historical-pipeline.md) |
| task、scene、快照和预览怎样连接 | [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md) | [当前原型](systems/manual-qc-acceptance-prototype.md) |
| 一次分配预览怎样落到代码 | [Python 软件结构](domains/quality/manual/acceptance/python-architecture-and-implementation.md) | [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md) |
| 系统分层和调用顺序是什么 | [系统架构](domains/quality/manual/acceptance/system-architecture.md) | [数据库公共能力](capabilities/database-access.md) |
| 当前到底实现了什么 | [当前原型](systems/manual-qc-acceptance-prototype.md) | [当前代码来源](sources/current-prototype.md) |
| 哪些还不能回答 | [未知与冲突](domains/quality/manual/acceptance/open-questions.md) | [来源记录](sources/index.md) |

## 按知识主题浏览

- 领域与业务全貌
  - [质检领域位置](domains/quality/overview.md)
  - [人工质检](domains/quality/manual/overview.md)
  - [交付与行动项](domains/quality/manual/delivery-management.md)
  - [人工质检平台与模块](domains/quality/manual/platform-and-module-map.md)
  - [人工质检验收](domains/quality/manual/acceptance/overview.md)
- 验收业务、规则与数据
  - [生命周期](domains/quality/manual/acceptance/lifecycle.md)
  - [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md)
  - [结论与执行](domains/quality/manual/acceptance/conclusion-and-execution.md)
  - [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md)
- 人员与平台共享能力
  - [人员与权限](domains/quality/manual/personnel-and-permissions.md)
  - [统一数据工作台](capabilities/quality-data-workbench.md)
- 软件与实现
  - [系统架构](domains/quality/manual/acceptance/system-architecture.md)
  - [Python 软件结构](domains/quality/manual/acceptance/python-architecture-and-implementation.md)
  - [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md)
  - [当前仓库原型](systems/manual-qc-acceptance-prototype.md)
  - [数据库访问](capabilities/database-access.md)
  - [对象存储（当前仅能确认预留目录）](capabilities/object-storage.md)
- 可信边界与追溯
  - [来源记录](sources/index.md)
  - [未知与冲突](domains/quality/manual/acceptance/open-questions.md)

## 当前知识能确认什么

| 信息性质 | 当前候选能确认的内容 |
|---|---|
| 业务与人工决定 | 交付任务主线、行动项、四类状态轴、验收边界、返工和可交付结果的定义线索 |
| 历史做法 | 旧抽样、阈值、通过打回、状态刷新和中间表链路 |
| 目标设计 | 交付中心、人员与权限、平台分层、统一数据工作台、快照、采样、规则、外部系统和 Repository 方案 |
| 当前仓库原型 | 查询、按日展开、Ratio 数量规划、预览保存及对应前端边界 |
| 当前生产 | 没有运行系统、生产 Schema、真实接口、SSO 和端到端执行证据，不能确认已部署或已闭环 |

正文区分 current_decision、target_design、historical、conflict 和 unknown；来源记录只用于追溯，不能替代正文中的业务机制、算法和软件结构说明。

## 仍需补充或人工决定

- 交付时间预测、留存率、验收通过率分母、Bad/打回原因和盖章完成条件等业务口径仍有未知或冲突，需由业务负责人裁决。
- 人员 SCD2 与操作日志事务、真实 SSO 参数、权限接入、人员服务和前端字段适配仍缺直接实现证据。
- API 状态码与批量上限、Delta 外部契约、Repository 事务、快照字段版本（旧标量或 JSONB）、DAG 和端到端刷新结果仍需源码、Schema、迁移或运行结果核验。
- 真实交付中心、验收监控、返工跟踪、人员工作台和统一数据工作台的页面/API 是否部署，不能由目标设计或 Demo 描述推出。
- 大模型质检、自动化质检和专题数据质量只保留领域位置，尚未形成同等深度的规范知识。

## 管理导航

- [产品视图](views/index.md)
- [系统与实现](systems/index.md)
- [公共能力](capabilities/index.md)
- [领域目录](domains/index.md)
- [来源](sources/index.md)
- [变更日志](log.md)
