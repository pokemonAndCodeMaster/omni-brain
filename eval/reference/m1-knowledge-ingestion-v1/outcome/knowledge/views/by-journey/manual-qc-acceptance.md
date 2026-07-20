---
type: Navigation View
title: 人工质检验收学习与任务旅程
description: 面向零背景读者，按先全貌、再业务、再数据与软件、最后核验事实的顺序导航验收知识。
tags: [view, journey, manual-qc, acceptance]
---

# 人工质检验收学习与任务旅程

## 先看结论

要学懂验收，不能从 Ratio 公式或 API 文件直接开始。先确定它在人工质检交付中的位置，再沿实际任务走过分配、验收、结论、执行和返工，之后才下钻数据、软件和代码。

## 完整学习路线

```mermaid
flowchart LR
    Q[1 质检位置] --> M[2 人工质检全貌]
    M --> L[3 验收生命周期]
    L --> W[4 产品工作台]
    W --> D[5 数据与状态]
    D --> S[6 系统架构]
    S --> P[7 Python 代码走读]
    P --> A[8 算法与执行]
    A --> I[9 实现证据]
    I --> U[10 未知与补知]
```

1. [质检领域位置](../../domains/quality/overview.md)
2. [人工质检全貌](../../domains/quality/manual/overview.md)
3. [验收生命周期](../../domains/quality/manual/acceptance/lifecycle.md)
4. [验收产品工作台](../../domains/quality/manual/acceptance/product-workbench.md)
5. [数据对象、数据流与状态](../../domains/quality/manual/acceptance/data-flow-and-state.md)
6. [系统架构与跨层调用](../../domains/quality/manual/acceptance/system-architecture.md)
7. [Python 软件结构与实现](../../domains/quality/manual/acceptance/python-architecture-and-implementation.md)
8. [采样与分配](../../domains/quality/manual/acceptance/sampling-and-assignment.md)和[结论与执行](../../domains/quality/manual/acceptance/conclusion-and-execution.md)
9. [业务到代码与证据地图](../../domains/quality/manual/acceptance/implementation-map.md)
10. [当前未知与冲突](../../domains/quality/manual/acceptance/open-questions.md)

## 如果你正在推进一条真实任务

```text
确认交付任务和当前轮次
→ 在工作台定位待分配/风险范围
→ 查看采样预览和缺口
→ 跟踪实际分配与完成
→ 分析质量与原因
→ 确认结论、范围和数据时间
→ 执行并回查
→ 通过后判断可交付量，打回后进入返工
```

对应页面是[产品工作台](../../domains/quality/manual/acceptance/product-workbench.md)，业务边界见[验收生命周期](../../domains/quality/manual/acceptance/lifecycle.md)。

## 按常见问题查找

| 问题 | 去哪里 |
|---|---|
| 验收和通过/打回为什么不是一回事？ | [验收生命周期](../../domains/quality/manual/acceptance/lifecycle.md) |
| 任务分下去后怎样看进度、异常和返工？ | [验收产品工作台](../../domains/quality/manual/acceptance/product-workbench.md) |
| `scene_name`、task、快照和交付任务怎样连接？ | [数据对象、数据流与状态](../../domains/quality/manual/acceptance/data-flow-and-state.md) |
| 页面操作怎样走到 Python 和数据库？ | [系统架构](../../domains/quality/manual/acceptance/system-architecture.md) |
| 当前 Python 包、类、函数怎样协作，设计是否清楚？ | [Python 软件结构与实现](../../domains/quality/manual/acceptance/python-architecture-and-implementation.md) |
| Ratio 怎样处理总量、类别不足和取整？ | [采样与分配](../../domains/quality/manual/acceptance/sampling-and-assignment.md) |
| 历史通过率规则具体是什么？ | [结论与执行](../../domains/quality/manual/acceptance/conclusion-and-execution.md) |
| 当前代码到底实现到哪里？ | [当前原型](../../systems/manual-qc-acceptance-prototype.md) |
| 哪些字段、接口和规则不能确定？ | [当前未知与冲突](../../domains/quality/manual/acceptance/open-questions.md) |

## 读取时始终保留的事实边界

- 业务人工纠正、历史脚本、目标设计和固定代码分别表达。
- 目标图中的组件不等于当前文件已经存在。
- 固定代码行为不等于生产已经部署。
- 没有证据的接口、状态、字段和阈值保持未知。

# Citations

1. [人工质检验收总览](../../domains/quality/manual/acceptance/overview.md)
2. [当前实现与证据地图](../../domains/quality/manual/acceptance/implementation-map.md)
