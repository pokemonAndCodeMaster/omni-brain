---
type: Software Architecture
title: 人工质检验收系统架构与跨层调用
description: 说明验收工作台、API、Python 服务、规则、数据库和外部任务系统之间的责任与关键调用顺序。
tags: [manual-qc, acceptance, architecture]
---

# 人工质检验收系统架构与跨层调用

## 先看结论

验收系统目标上由五个边界协作：工作台表达用户任务，API 校验请求并提供稳定契约，Service 串起完整用例，纯 Python 规则完成配额或结论计算，Repository 和外部客户端分别访问本地数据与外部任务状态。固定代码只实现了其中“查询与 Ratio 数量预览”的局部纵向链路。

## 系统上下文

```mermaid
flowchart LR
    U[质检负责人/验收员] --> UI[验收工作台]
    UI --> API[FastAPI API]
    API --> APP[人工质检 Python 应用]
    APP --> DB[(交付任务、快照、预览)]
    APP -.目标能力.-> EXT[外部任务系统\n材料称 Delta]
    APP -.目标依赖.-> PERSON[人员与分组]
    JOB[目标/历史调度任务\n刷新统计与回查状态] -.触发.-> APP
    EXT --> RAW[task/clip 状态]
    RAW --> JOB
```

数据库与外部任务系统不能混成同一个数据源：数据库提供本平台读模型、预览和管理状态；task/clip 的最终状态属于外部系统，真正执行后必须在那里确认。目标材料使用调度任务周期刷新快照和回查状态，固定代码提交中没有这些 DAG。

## 跨层组件和责任

```mermaid
flowchart TB
    subgraph HTTP[HTTP 边界]
        UI[Vue 页面/其他调用方]
        R[FastAPI Router]
        SC[Pydantic Schema]
    end
    subgraph APP[应用编排]
        QS[AcceptanceQueryService]
        AS[AssignmentPreviewService]
        TS[目标：Assignment/Execution/Stat Service]
    end
    subgraph RULE[纯 Python 计算]
        SR[当前：plan_ratio_sampling]
        TR[目标：其他 Sampler 与结论 Rule]
    end
    subgraph IO[数据与外部调用]
        REPO[AcceptanceRepository]
        PG[PostgresConnector]
        DC[目标：DeltaClient]
    end
    UI --> R
    SC --> R
    R --> QS
    R --> AS
    R -.未实现.-> TS
    QS --> REPO
    AS --> SR
    AS --> REPO
    TS -.目标.-> TR
    TS -.目标.-> REPO
    TS -.目标.-> DC
    REPO --> PG
```

图中实线是固定提交中可以定位的当前代码，虚线是材料中的目标设计。

## 当前已实现：分配预览时序

```mermaid
sequenceDiagram
    actor U as 用户
    participant R as router.py
    participant S as AssignmentPreviewService
    participant Repo as AcceptanceRepository
    participant Algo as plan_ratio_sampling
    participant DB as PostgreSQL
    U->>R: POST /assignment/preview
    R->>S: create_preview(request, employee_id)
    S->>S: 解析显式选择或筛选全选
    S->>Repo: get_selection_units(...)
    Repo->>DB: 参数化查询可用统计单元
    DB-->>Repo: 日期桶与 Good/Bad 可用量
    Repo-->>S: rows
    S->>Algo: buckets, target_count, good_ratio
    Algo-->>S: 数量计划、缺口和警告
    S->>S: 生成 preview_id/source_version/过期时间
    S->>Repo: save_preview(...)
    Repo->>DB: 写 t_qc_operation_preview
    S-->>R: AssignmentPreviewResponse
    R-->>U: 预览结果
```

这条链路只冻结选择描述、请求、统计单元和数量结果；没有冻结具体 task_ids，也没有 execute 端点。

## 目标链路：结论执行与回查

```mermaid
sequenceDiagram
    actor U as 有执行权限的用户
    participant API as Execution API
    participant S as ExecutionService
    participant Repo as Repository
    participant Rule as PassRule
    participant Ext as DeltaClient
    participant Delta as 外部任务系统
    U->>API: 提交已确认结论与范围
    API->>S: execute(scope, submitted_decision)
    S->>Repo: 重新聚合当前指标
    S->>Rule: evaluate(current_metrics)
    Rule-->>S: PASS/REJECT/PENDING + reason
    S->>S: 校验与用户提交一致且非 PENDING
    S->>Repo: 按范围反查当前 task_ids
    S->>Ext: 通过或打回
    Ext->>Delta: 批量请求
    Delta-->>Ext: 即时结果
    Ext-->>S: 成功/跳过/失败/未知
    S-->>API: 即时摘要
    API-->>U: 进入回查状态
    S->>Delta: 后续回查真实状态
```

这是目标设计，不是当前代码。生产接口、状态值和调用顺序仍需实时系统确认。

## 三种数据结构为什么要转换

```mermaid
flowchart LR
    HTTP[Pydantic 请求/响应\n面向前端契约] --> IN[内部 dataclass/计算结构\n面向算法]
    IN --> ROW[Repository 字典行\n面向 SQL 结果]
    ROW --> DB[(数据库列)]
```

当前代码已经存在这种分工，但并未完全隔离：`AssignmentPreviewService` 直接依赖 `src.api.schemas.acceptance` 中的 Pydantic 类型。它对当前小切片很直接，却意味着应用服务与 HTTP Schema 一起变化；未来是否拆出内部结构，应由真实变化证明，而不是先建一套抽象。

## 当前与目标的边界

| 能力 | 固定代码 | 目标材料 |
|---|---|---|
| 工作台 | 无完整验收前端证据 | 总览与单需求五标签工作区 |
| 查询、按天展开 | 已实现 | 继续扩展到组、人员和 scene |
| Ratio 数量预览 | 已实现 | 预览应含具体 task_ids 和更多约束 |
| 真正分配 | 未实现 | Service + Repository + DeltaClient |
| 结论规则 | 未实现 | 纯规则输出 PASS/REJECT/PENDING |
| 通过/打回与回查 | 未实现 | 执行前重算、即时结果、最终回查 |
| 快照刷新与调度 | 未实现 | 目标材料描述周期刷新和状态驱动任务；历史材料也记录过定时脚本 |

# Citations

1. [当前验收原型](../../../../sources/current-prototype.md)
2. [目标验收平台设计](../../../../sources/target-design.md)
3. [ChatGPT 质检项目导出](../../../../sources/chatgpt-quality-project.md)
4. [数据库访问公共能力](../../../../capabilities/database-access.md)
