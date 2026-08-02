# 人工质检验收知识入口（K0）

这套知识用于帮助没有背景的读者理解：人工质检验收为什么存在、它怎样从标注结果形成质量依据并推动通过或返工，以及这些业务职责目前分别有哪些历史做法、目标设计和代码实现。

K0 只使用 Batch 1。它不包含后来到达的 Batch 2 产品与实施材料，也不能代表当前生产操作手册。

## 第一次学习，从这条主线开始

1. [质检领域位置](views/by-domain/quality.md)：先分清质检、人工质检与验收的上下级关系，以及 K0 在各层能讲到多深。
2. [人工质检全貌](domains/quality/manual/overview.md)：理解规则与数据准备、标注、验收、结论执行、返工和交付之间的业务链。
3. [验收总览](domains/quality/manual/acceptance/overview.md)：建立验收业务、数据、算法和软件的整体地图。
4. [验收学习与任务旅程](views/by-journey/manual-qc-acceptance.md)：按“业务机制 → 数据与规则 → 软件实现 → 可信边界”继续深入。

读完这条路线，应该能够解释验收样本为什么不等于执行全集、PASS 为什么不等于交付完成、当前原型为什么只能算数量预览，以及遇到生产问题时还缺哪些证据。

## 已经知道问题时，直接进入对应主题

| 想解决的问题 | 入口 | 继续下钻 |
|---|---|---|
| 人工质检和验收处于什么位置 | [领域视图](views/by-domain/quality.md) | [人工质检平台与模块](domains/quality/manual/platform-and-module-map.md) |
| 标注、验收、结论和执行有什么区别 | [验收生命周期](domains/quality/manual/acceptance/lifecycle.md) | [结论与执行](domains/quality/manual/acceptance/conclusion-and-execution.md) |
| 历史上怎样抽样和分配 | [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md) | [历史来源](sources/historical-pipeline.md) |
| task、scene、快照和预览怎样连接 | [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md) | [当前原型](systems/manual-qc-acceptance-prototype.md) |
| 一次分配预览怎样落到代码 | [Python 软件结构](domains/quality/manual/acceptance/python-architecture-and-implementation.md) | [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md) |
| 系统分层和调用顺序是什么 | [系统架构](domains/quality/manual/acceptance/system-architecture.md) | [数据库公共能力](capabilities/database-access.md) |
| 当前到底实现了什么 | [当前原型](systems/manual-qc-acceptance-prototype.md) | [当前代码来源](sources/current-prototype.md) |
| 哪些还不能回答 | [未知与冲突](domains/quality/manual/acceptance/open-questions.md) | [来源记录](sources/index.md) |

## 按知识主题浏览

- 领域位置与全貌
  - [质检](domains/quality/overview.md)
  - [人工质检](domains/quality/manual/overview.md)
  - [人工质检平台与模块](domains/quality/manual/platform-and-module-map.md)
  - [人工质检验收](domains/quality/manual/acceptance/overview.md)
- 验收业务、规则与数据
  - [生命周期](domains/quality/manual/acceptance/lifecycle.md)
  - [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md)
  - [结论与执行](domains/quality/manual/acceptance/conclusion-and-execution.md)
  - [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md)
- 软件与实现
  - [系统架构](domains/quality/manual/acceptance/system-architecture.md)
  - [Python 软件结构](domains/quality/manual/acceptance/python-architecture-and-implementation.md)
  - [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md)
  - [当前仓库原型](systems/manual-qc-acceptance-prototype.md)
- 公共能力
  - [数据库访问](capabilities/database-access.md)
  - [对象存储（当前仅能确认预留目录）](capabilities/object-storage.md)
- 可信边界
  - [来源记录](sources/index.md)
  - [未知与冲突](domains/quality/manual/acceptance/open-questions.md)

## K0 可以相信到什么程度

| 信息性质 | K0 能确认的内容 |
|---|---|
| 人工语义线索 | 三阶段边界、抽样验收与执行全集不同；缺原始人类对话 |
| 历史做法 | 旧抽样、阈值、通过打回、状态刷新和中间表链路 |
| 目标设计 | 平台分层、快照、采样、规则、外部系统和 Repository 方案 |
| 当前仓库原型 | 查询、按日展开、Ratio 数量规划、预览保存及对应前端 |
| 当前生产 | 没有运行系统、生产 Schema 和接口证据，不能确认 |

来源记录只用于追溯这些判断。业务机制、算法和软件结构应当在正文中直接讲清，不要求读者先打开原始材料才能理解。

## 仍待补全的知识

Batch 1 没有把完整需求接纳、交付工作台、验收过程监控、结果分析、返工责任和当前人员模型讲透。K0 将这些作为知识缺口；它们是否由 Batch 2 补齐，要在 K1 增量阶段逐项验证。

## 管理导航

- [产品视图](views/index.md)
- [系统与实现](systems/index.md)
- [公共能力](capabilities/index.md)
- [领域目录](domains/index.md)
- [来源](sources/index.md)
- [变更日志](log.md)
