# 质检知识入口

## 本页导航

- [知识库定位](#知识库定位)
- [知识地图与默认阅读顺序](#知识地图与默认阅读顺序)
- [按工作目标快速进入](#按工作目标快速进入)
- [知识覆盖与待确认事项](#知识覆盖与待确认事项)
- [来源与维护信息](#来源与维护信息)

## 知识库定位

**本页用途：** 这里是质检知识的统一入口。读者可以先建立质检领域全貌，再逐层进入人工质检、验收、数据规则和软件实现，也可以根据当前工作直接进入相关主题。

| 知识层级 | 主要内容 | 当前深度 |
|---|---|---|
| **质检领域** | • 四个业务模块<br>• 模块之间的基本关系<br>• 共享平台能力 | 已建立领域框架；除人工质检外的模块仍待补充 |
| **人工质检** | • 需求与交付<br>• 数据、规则和人员准备<br>• 标注、验收、执行、返工和交付 | 已有目标业务链和部分现状；完整现实流程仍待补充 |
| **人工质检验收** | • 验收流程<br>• 采样与分配<br>• 数据状态和结论执行<br>• 软件架构与当前代码 | 当前知识最深入，可支持学习和局部开发定位 |

**使用边界：** 当前知识对人工质检验收最为完整，对大模型质检、自动化质检和专题数据质量只确认了领域位置，尚不足以解释其内部流程。规划方案、过去做法和当前代码会分别说明，不能相互替代。

## 知识地图与默认阅读顺序

**组织逻辑：** 知识按“质检领域 → 人工质检 → 验收 → 业务、数据和软件专题”逐层展开。这个层级既是知识目录，也是默认阅读顺序；读者不需要在“大纲”“学习路线”和“主题浏览”之间反复选择。

~~~mermaid
flowchart TD
    Q[质检领域全貌]
    Q --> H[人工质检]
    Q --> L[大模型质检]
    Q --> A[自动化质检]
    Q --> D[专题数据质量]

    H --> DM[需求与交付管理]
    H --> RP[数据、规则与人员准备]
    H --> AN[标注作业]
    H --> AC[验收]
    H --> EX[结论执行、返工与交付]

    AC --> LC[生命周期]
    AC --> SA[采样与分配]
    AC --> DS[数据流与状态]
    AC --> CE[结论与执行]
    AC --> SW[软件架构与代码实现]
~~~

| 阅读层级 | 入口 | 主要回答 |
|---:|---|---|
| 1 | [质检领域全貌](domains/quality/overview.md) | 质检包含哪些业务模块，各模块是什么关系 |
| 2 | [人工质检全貌](domains/quality/manual/overview.md) | 人工质检如何从需求和准备走到交付 |
| 3 | [人工质检验收总览](domains/quality/manual/acceptance/overview.md) | 验收在人工质检中的位置、内部组成和完整闭环 |
| 4 | [验收生命周期](domains/quality/manual/acceptance/lifecycle.md) · [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md) · [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md) · [结论与执行](domains/quality/manual/acceptance/conclusion-and-execution.md) | 按业务主线深入理解验收规则和数据 |
| 5 | [系统架构](domains/quality/manual/acceptance/system-architecture.md) · [Python 软件结构](domains/quality/manual/acceptance/python-architecture-and-implementation.md) · [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md) | 从业务进入组件、调用链、代码和修改入口 |

## 按工作目标快速进入

**使用方法：** 下列入口用于缩短查找路径，不是另一套知识分类。遇到复杂问题时，先读对应总览，再按需要进入一至三个专题。

### 建立业务全貌

| 当前目标 | 建议入口 |
|---|---|
| 了解质检由哪些业务模块组成 | [质检领域全貌](domains/quality/overview.md) |
| 了解人工质检的完整业务链 | [人工质检全貌](domains/quality/manual/overview.md) |
| 了解验收为什么存在、怎样闭环 | [人工质检验收总览](domains/quality/manual/acceptance/overview.md) |
| 了解需求怎样持续推进到交付 | [交付与行动项](domains/quality/manual/delivery-management.md) |

### 理解规则、数据与人员

| 当前目标 | 建议入口 |
|---|---|
| 区分标注、验收、结论和执行 | [验收生命周期](domains/quality/manual/acceptance/lifecycle.md) |
| 理解抽样数量、样本选择和任务分配 | [采样与分配](domains/quality/manual/acceptance/sampling-and-assignment.md) |
| 理解任务、场景、快照、预览和状态 | [数据流与状态](domains/quality/manual/acceptance/data-flow-and-state.md) |
| 理解人员变化、角色和权限边界 | [人员与权限](domains/quality/manual/personnel-and-permissions.md) |

### 开发、调试与方案设计

| 当前目标 | 建议入口 |
|---|---|
| 理解当前系统分层和跨层调用 | [验收系统架构](domains/quality/manual/acceptance/system-architecture.md) |
| 理解 Python 包、对象协作和一次真实调用 | [Python 软件结构与实现](domains/quality/manual/acceptance/python-architecture-and-implementation.md) |
| 从业务能力定位到组件、代码和证据 | [业务到代码地图](domains/quality/manual/acceptance/implementation-map.md) |
| 了解数据库连接、事务和领域 SQL 的分工 | [数据库访问公共能力](capabilities/database-access.md) |
| 核对当前代码到底实现到哪里 | [当前验收原型](systems/manual-qc-acceptance-prototype.md) |

## 知识覆盖与待确认事项

**判断原则：** “有设计材料”不等于“已经上线”，“代码存在”也不等于“生产环境已经运行”。同一张表中列出各层知识的覆盖、缺口和影响。

| 知识层级 | 已经覆盖 | 仍需补充 | 缺口影响 |
|---|---|---|---|
| **质检领域** | • 四个业务模块的顶层位置<br>• 业务模块与共享能力的基本分工 | • 其他质检模块的目标、输入、输出和流程<br>• 四个模块的真实协作和运行现状 | 暂时不能完整解释一站式质检平台怎样运作 |
| **人工质检** | • 从需求准备到标注、验收、执行、返工和交付的目标业务链<br>• 交付、人员、平台和验收的基本职责 | • 当前需求管理、标注作业和过程监控<br>• 当前负责人、数据来源、返工和交付条件 | 重构或新增复杂需求前仍需补齐现状 |
| **人工质检验收** | • 验收业务闭环<br>• 采样、数据状态和结论执行<br>• 查询、按日展开和数量预览代码链路 | • 当前规则、指标公式和人员责任<br>• 真实数据库、接口、部署和端到端运行结果 | 可以学习和定位局部开发，不能作为生产操作手册 |
| **软件与公共能力** | • 当前原型的前端、接口、服务、算法和数据访问入口<br>• 数据库访问与统一工作台的目标职责 | • 对象存储、权限接入和公共组件的现实实现<br>• 当前原型与真实数据库、生产环境的兼容情况 | 精确开发和运行仍需核对源码、数据库与现场结果 |

更细的问题、影响和补充责任见[验收待确认事项](domains/quality/manual/acceptance/open-questions.md)。

## 来源与维护信息

这些页面用于追溯知识依据和变化过程，不是第一次学习的必读内容：

- [来源记录](sources/index.md)
- [知识变更日志](log.md)
- [领域目录](domains/index.md)
- [系统与实现](systems/index.md)
- [公共能力](capabilities/index.md)
