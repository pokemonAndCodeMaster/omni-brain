---
type: Software Design and Implementation
title: 人工质检验收 Python 软件结构与实现
description: 从 Ratio 分配预览这一真实业务动作解释当前 Python 代码的对象协作、包结构、调用过程、数据转换、设计取舍和修改入口。
tags: [manual-qc, acceptance, python, software-design]
---

# 人工质检验收 Python 软件结构与实现

## 本页导航

- [软件能力概览](#软件能力概览)
- [业务场景与实现边界](#业务场景与实现边界)
- [核心对象与职责](#核心对象与职责)
- [代码结构与依赖方向](#代码结构与依赖方向)
- [一次分配预览的调用过程](#一次分配预览的调用过程)
- [数据怎样跨层转换](#数据怎样跨层转换)
- [配额算法的位置](#配额算法的位置)
- [当前设计的优点与限制](#当前设计的优点与限制)
- [一次具体修改会影响哪里](#一次具体修改会影响哪里)
- [运行边界与待确认事项](#运行边界与待确认事项)

## 软件能力概览

**本页用途：** 帮助开发者从“生成 Ratio 分配预览”这个业务动作进入当前 Python 实现，理解请求怎样经过接口、业务编排、配额算法和数据访问，最后形成并保存预览。

**核心结构：** 当前实现最重要的设计是把**HTTP 接入、业务编排、纯配额计算、领域 SQL 和数据库连接**分开。配额算法不依赖 FastAPI、SQL 或用户对象，领域查询集中在 Repository，Router 只处理接口责任。

**内容顺序：** 本页先界定业务动作和实现范围，再依次说明核心对象、包结构、调用过程、数据转换、算法位置、设计取舍和一次修改路径。

**适用边界：** 当前代码只贯通任务查询、按日期展开和 **Ratio 数量预览**。它没有选择具体 task、正式分配验收员、完成验收作业、形成结论或调用外部系统执行通过和打回。现有单元测试也不能证明真实 PostgreSQL、部署环境或生产数据已经兼容。

## 业务场景与实现边界

**用户目标：** 操作人员已经选择一个交付任务或若干日期，希望在正式分配前看到本次最多可抽多少、Good 与 Bad 各抽多少、每个统计桶分配多少，以及数据是否不足。

**输入：**

- 任务或日期范围；
- 目标验收数量；
- Good/Bad 比例；
- 当前操作者身份。

**成功结果：** 系统返回一个有效期为 30 分钟的预览，包含目标量、计划 Good/Bad 数量、各桶分配、缺口、警告、来源版本和过期时间，并把预览保存到数据库。

**失败结果：** 选择条件非法、候选数据为空或 Repository 操作失败时，接口返回对应错误；生成预览本身不会改变外部任务状态。

~~~mermaid
flowchart LR
    A[选择任务或日期与 Ratio 参数] --> B[解析选择范围]
    B --> C[查询各桶可用量]
    C --> D[计算 Good/Bad 与分桶配额]
    D --> E[组装预览、缺口和警告]
    E --> F[保存 30 分钟有效的预览]
    F --> G[返回调用方]
~~~

| 当前已经实现 | 当前没有实现 | 对业务的直接含义 |
|---|---|---|
| • 解析显式任务或日期选择<br>• 查询统计桶可用量<br>• 计算 Ratio 数量计划<br>• 保存并读取预览 | • 冻结具体 task IDs<br>• 选择和分配验收员<br>• 改变外部任务状态<br>• 形成或执行质量结论 | 预览只能回答“计划分多少”，不能回答“具体分了哪些任务、分给谁、是否已经生效” |

## 核心对象与职责

**对象关系：** Router、Service、Repository 和纯算法围绕一次分配预览协作。请求与响应对象负责接口契约，`SamplingBucket` 和 `SamplingPlan` 只表达算法输入输出。

~~~mermaid
classDiagram
    class AcceptanceRouter {
        +create_assignment_preview()
        +get_assignment_preview()
    }
    class AssignmentPreviewService {
        -repository
        -ttl
        +create_preview(request, actor_id)
        +get_preview(preview_id, actor_id)
        -_resolve_selection(selection)
        -_source_version(rows)
    }
    class AcceptanceRepository {
        +get_selection_units(task_ids, date_keys)
        +resolve_filtered_task_ids(spec)
        +save_preview(...)
        +get_preview(preview_id, actor_id)
    }
    class SamplingBucket {
        +id
        +good_available
        +bad_available
    }
    class SamplingPlan {
        +target_count
        +planned_good
        +planned_bad
        +shortage
        +allocations
        +warnings
    }
    class RatioSampling {
        +plan_ratio_sampling(buckets, target, ratio)
    }
    AcceptanceRouter --> AssignmentPreviewService
    AssignmentPreviewService --> AcceptanceRepository
    AssignmentPreviewService --> SamplingBucket
    AssignmentPreviewService --> RatioSampling
    RatioSampling --> SamplingPlan
~~~

| 对象或函数 | 主要职责 | 输入 | 输出或副作用 | 不负责什么 |
|---|---|---|---|---|
| `AcceptanceRouter` | • 接收 HTTP 请求<br>• 读取操作者<br>• 映射业务错误<br>• 统一响应 | Pydantic 请求、请求头 | HTTP 响应 | SQL、配额公式和预览持久化 |
| `AssignmentPreviewService` | • 解析选择<br>• 协调查询与算法<br>• 组装响应<br>• 保存和读取预览 | 请求、操作者、Repository | `AssignmentPreviewResponse` 和预览写入 | 数据库连接细节和 HTTP 状态码 |
| `AcceptanceRepository` | • 查询统计单元<br>• 解析筛选范围<br>• 保存和读取预览 | task/date 范围、预览 payload | 字典行和数据库写入 | HTTP 语义和配额决策 |
| `SamplingBucket` | 表示一个统计桶的最小算法输入 | 桶 ID、Good/Bad 可用量 | 冻结的数据对象 | 用户、SQL 和展示信息 |
| `plan_ratio_sampling` | 计算总目标、类别数量和分桶配额 | buckets、目标量、比例 | `SamplingPlan` | 数据查询、持久化和人员分配 |
| `SamplingPlan` | 保存计划数量、缺口、分桶和警告 | 算法计算结果 | 冻结的数据对象 | 选择具体任务或执行分配 |

**设计含义：** Service 把 Repository 的字典行收缩为算法所需的最小输入。算法因此可以使用普通 Python 数据独立验证，也不会因 HTTP 或数据库结构变化而直接改变。

## 代码结构与依赖方向

**包结构：** 代码按接口契约、数据库公共能力和人工质检业务实现组织。下面的树只列与分配预览直接相关的入口。

```text
src/
├── api/
│   ├── deps.py                                组装连接、Repository 与 Service
│   └── schemas/acceptance.py                  HTTP 请求与响应对象
├── database/
│   ├── manager.py                             管理命名数据库连接
│   └── postgresql.py                          连接池、事务和查询助手
└── manual_qc/
    ├── repository.py                          人工质检 SQL 与预览持久化
    └── acceptance/
        ├── router.py                          HTTP 路由与错误映射
        ├── sampler.py                         纯 Ratio 配额算法
        └── services/
            ├── query_service.py               只读查询编排
            └── assignment_preview_service.py  选择解析、计算、组装与保存
```

| 依赖方向 | 为什么这样组织 | 当前限制 |
|---|---|---|
| Router → Service | 接口层只把请求交给业务用例 | Service 当前直接使用 API Pydantic Schema |
| Service → 算法 | 编排 I/O 后把最小数据交给纯计算 | 当前只直接调用 Ratio 函数，尚无多策略接口 |
| Service → Repository | 业务用例不直接编写 SQL | Service 同时承担选择解析、对象转换、响应组装和保存 |
| Repository → 数据库公共能力 | 领域 SQL 与连接池、事务助手分开 | Repository 继续扩张后可能混入过多验收职责 |
| `deps.py` → 具体实现 | 依赖在应用入口集中组装 | 当前证据只覆盖 FastAPI 这一种调用入口 |

## 一次分配预览的调用过程

**调用主线：** 一次请求从 HTTP 对象开始，中间经历选择解析、数据库查询、纯算法计算、响应组装和预览写入。下面的时序图说明调用主体，表格补足每一步的数据变化和副作用。

~~~mermaid
sequenceDiagram
    actor User as 操作人员
    participant Router as AcceptanceRouter
    participant Service as AssignmentPreviewService
    participant Repo as AcceptanceRepository
    participant Sampler as plan_ratio_sampling
    participant DB as PostgreSQL

    User->>Router: 创建预览请求
    Router->>Service: request + actor_id
    Service->>Repo: 解析筛选或查询统计单元
    Repo->>DB: 参数化查询
    DB-->>Repo: 可用量字典行
    Repo-->>Service: selection rows
    Service->>Sampler: SamplingBucket[] + target + ratio
    Sampler-->>Service: SamplingPlan
    Service->>Repo: 保存预览 payload
    Repo->>DB: INSERT/UPDATE 预览
    Service-->>Router: AssignmentPreviewResponse
    Router-->>User: 统一 HTTP 响应
~~~

| 顺序 | 代码入口 | 进入的数据 | 关键处理 | 输出或副作用 |
|---:|---|---|---|---|
| 1 | `router.create_assignment_preview` | HTTP JSON、请求头 | JSON 校验为 `AssignmentPreviewRequest`，读取 `employee_id` | 调用 Service；非法业务选择映射为 422 |
| 2 | `AssignmentPreviewService._resolve_selection` | 显式 ID 或筛选选择 | 解析为 task IDs/date keys；筛选全选最多解析 5000 个 task IDs | 形成可查询范围，不写数据库 |
| 3 | `AcceptanceRepository.get_selection_units` | task/date 范围 | 转为参数化 SQL，读取交付任务和快照 | 返回可用量及展示字段的字典行 |
| 4 | `SamplingBucket(...)` | Repository 字典行 | 只保留桶 ID 和 Good/Bad 可用量 | 形成与 I/O 无关的算法输入 |
| 5 | `plan_ratio_sampling` | buckets、目标量、比例 | 计算总目标、类别补足、分桶配额和缺口 | 返回不可变 `SamplingPlan` |
| 6 | `AssignmentPreviewResponse(...)` | SamplingPlan 与原始行 | 合并任务、日期、场景、预览 ID、来源版本和过期时间 | 形成接口响应对象 |
| 7 | `AcceptanceRepository.save_preview` | Pydantic 响应和请求 | 转为 JSON payload 并持久化 | 写入 `t_qc_operation_preview` |
| 8 | Router | Service 响应 | 包装为统一返回结构 | 返回调用方，不改变外部任务状态 |

## 数据怎样跨层转换

**转换原则：** 每次跨层只保留下一层需要的信息，并在明确责任处补充接口或持久化字段，避免数据库行直接泄漏给前端，也避免算法依赖用户和 SQL 结构。

~~~mermaid
flowchart LR
    JSON[HTTP JSON] --> REQ[AssignmentPreviewRequest]
    REQ --> IDS[task_ids / date_keys]
    IDS --> ROWS[Repository 字典行]
    ROWS --> BUCKET[SamplingBucket]
    BUCKET --> PLAN[SamplingPlan]
    PLAN --> RESP[AssignmentPreviewResponse]
    RESP --> PAYLOAD[预览 JSONB]
~~~

| 转换 | 保留的信息 | 移除或新增的信息 | 责任位置 |
|---|---|---|---|
| JSON → Pydantic 请求 | 用户选择、目标量和比例 | 增加类型、范围和组合校验 | FastAPI / Pydantic |
| 请求 → task IDs/date keys | 业务选择语义 | 移除 UI 结构，形成查询条件 | Service |
| Repository 行 → `SamplingBucket` | 桶 ID、Good/Bad 可用量 | 移除 SQL 列、日期和展示信息 | Service |
| `SamplingPlan` → Pydantic 响应 | 目标、配额、缺口和警告 | 补充任务、日期、场景、ID、来源版本和有效期 | Service |
| 响应 → JSONB | 可重放的请求与预览结果 | 转为持久化 payload | Repository |

## 配额算法的位置

**算法责任：** `plan_ratio_sampling` 只负责根据可用量、目标量和 Good/Bad 比例计算数量计划。它输出目标数量、计划 Good/Bad、每桶分配、总缺口和警告，不负责选择具体任务或人员。

**设计收益：**

- 算法输入输出是冻结 dataclass，**同样输入得到同样结果**；
- 可以不启动 FastAPI、不连接数据库就验证类别补足和分桶结果；
- Repository 字段变化只要仍能转换成 `SamplingBucket`，就不必直接改变算法；
- 后续若增加 Personal 或 Group 策略，可以先独立实现和比较算法，再决定编排方式。

**进一步阅读：** Ratio 的目标量、类别补足、分桶和缺口规则见[采样与分配](sampling-and-assignment.md)。本页只解释算法在软件结构中的位置，不复制公式。

## 当前设计的优点与限制

**评价方法：** 下面从真实业务变化出发评价当前结构，不用设计模式名称替代代码责任，也不因为目标方案存在就声称当前代码已经具备未来能力。

| 设计点 | 当前做得好的地方 | 对业务变化的帮助 | 当前限制 |
|---|---|---|---|
| **接口与业务编排分离** | Router 很薄，没有 SQL 或配额公式 | 接口错误映射和业务计算可以分别修改 | Service 仍直接依赖 API Schema，新增 CLI 或调度入口时可能受限 |
| **纯算法与 I/O 分离** | Ratio 是普通 Python 函数，输入输出清楚 | 修改配额规则时可以快速验证，不需要数据库 | 当前只支持 Ratio，Service 对具体函数有直接依赖 |
| **领域 SQL 集中** | Repository 保存人工质检查询和预览持久化 | SQL 变化有明确入口，公共数据库组件不理解业务表 | 同一 Repository 已承担多类查询，继续扩展后可能职责过多 |
| **入口集中组装依赖** | `deps.py` 组装连接、Repository 和 Service | 测试可以替换 Repository 或数据库 | 还没有多种运行入口证明抽象已经充分 |
| **按当前切片实现** | 没有提前搭建所有未来采样策略和执行框架 | 当前代码规模与已实现业务相匹配 | 预览没有冻结具体 task IDs，不能直接支撑“预览即执行” |

**总体判断：** 当前结构对“查询容量并计算数量预览”这一纵向切片是清晰的。最需要关注的不是增加更多模式或抽象名词，而是随着真实分配、作业和执行进入代码后，Service 与 Repository 是否开始承担互不相关的职责。

## 一次具体修改会影响哪里

**修改场景：** 如果新增 Personal 采样，系统需要根据人员维度计算计划，而不再只根据 Good/Bad 比例生成 Ratio 数量。

| 修改顺序 | 代码位置 | 需要改变什么 | 验证重点 |
|---:|---|---|---|
| 1 | `sampler.py` | 增加 Personal 的明确输入、输出和算法函数 | 人员容量、目标量、边界和缺口的真实输入输出 |
| 2 | `schemas/acceptance.py` | 扩展 `AssignmentRuleSpec.strategy` 和 Personal 参数 | 非法组合是否在入口被拒绝 |
| 3 | `AssignmentPreviewService` | 根据策略准备最小算法输入并选择对应计算 | Ratio 不回归，Personal 不泄漏 SQL 或 UI 结构 |
| 4 | `AcceptanceRepository` | 只在算法确实需要时补充人员或分组查询字段 | 查询范围、人员有效性和字段口径 |
| 5 | 算法与 Service 测试 | 加入代表性容量、人员变化、样本不足和边界用例 | 验证业务结果而不是只断言函数被调用 |
| 6 | `/metadata` 与调用方 | 公布实际可用策略和参数 | 前端只展示后端真实支持的能力 |

**设计结论：** 当前结构可以容纳一次有限扩展，但新增策略仍会修改 Schema、Service 和能力元数据。只有多种策略实际出现并产生重复编排后，策略注册表或统一接口才具有明确收益。

## 运行边界与待确认事项

**部署关系：** 当前源码包含 FastAPI 到 PostgreSQL 的访问路径，但还没有证据证明服务已部署、真实 Schema 兼容或外部任务系统客户端存在。

~~~mermaid
flowchart LR
    CLIENT[HTTP 调用方] --> API[FastAPI 进程]
    API --> PG[(PostgreSQL<br/>代码期望存在)]
    API -.当前没有客户端.-> EXT[外部任务系统]
~~~

| 运行边界 | 当前代码证据 | 仍需确认 | 对开发的影响 |
|---|---|---|---|
| HTTP 调用方 → FastAPI | Router、Schema、依赖组装和路由测试存在 | 服务部署、认证、网关和真实调用结果 | 可以理解接口代码，不能承诺环境可访问 |
| FastAPI → PostgreSQL | 连接器、Repository 和参数化 SQL 存在 | `t_qc_daily_snapshot` 真实 DDL、字段兼容、初始化和负载 | 精确查询开发前必须核对 Schema 并运行代表查询 |
| FastAPI → 外部任务系统 | 只有历史做法和目标材料 | 客户端、契约、认证、批量限制、状态映射和回查 | 正式分配和通过/打回不能从现有代码继续假设 |
| 目标前端 → 当前 Python 接口 | 目标交互要求区分加载、过期、执行和刷新等状态 | 对应页面、API 状态模型和端到端实现 | 这些状态是后续设计输入，不是当前已实现能力 |

**按需展开：** 性能、通用幂等、重试、可观察性和专项测试不在本页基础路线中展开。出现真实负载、执行副作用或维测需求时，应沿对应故障路径单独分析，而不是提前罗列通用检查项。

# Citations

1. [当前验收原型](../../../../sources/current-prototype.md)
2. [目标验收平台设计](../../../../sources/target-design.md)
3. [数据库访问公共能力](../../../../capabilities/database-access.md)
