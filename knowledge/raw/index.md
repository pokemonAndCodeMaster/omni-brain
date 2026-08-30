# 原始资料目录

这里登记可长期复用、但尚未自动等同于当前事实的原始资料。原文件保持不可变；后续任务先从本页定位资料集，再按问题定向读取，不需要每次遍历整个 `knowledge/raw/`。

## 资料集

| 资料集 | 内容 | 规模 | 使用状态 |
|---|---|---:|---|
| [ChatGPT 质检项目导出](quality_check/) | 质检业务、人工质检流程、验收、平台架构、前端视图和公共组件设计 | 25 文件 / 6,954 行 / 447,012 字节 | 已登记；M1 已定向使用，后续任务可继续复用 |
| `quality_materials/` 本地受限资料集 | 一站式质检平台、人工质检 15 步流程、ConfigManager、数据库、快照、验收、前端源码与工程导读 | 17 文件 / 5,123 行 / 204,555 字节 | 已登记；含生产连接和认证信息，不进入 Git，后续摄入与复刻的优先来源 |
| [项目讨论原料](conversations/) | Omni-Brain 产品、质检场景、Blueprint 与工作流讨论 | 持续增加 | 已登记 |

## quality_materials 本地受限资料集

### 来源与完整性

- 来源：用户于 2026-07-25 放入仓库根 `quality_materials/`，用于后续知识摄入、质检平台和本地实验能力复刻。
- 文件形态：17 个 UTF-8 `.txt` 文件；其中多数正文为 Markdown，另含两份 Vue 单文件组件源码和一份 Python 风格实现材料。
- 完整性指纹：按文件路径排序后汇总 SHA-256，结果为 `422474ba2d4db4508dd58cb553fa51f1379352655b95904a434b3fbd7d29baf9`。
- 逐文件路径、行数、SHA-256、主题和用途见任务案 `quality-materials-knowledge-and-replication` 的 `outputs/source-inventory.md`。
- 本资料集与 `quality_check/` 没有字节级重复文件；存在较多主题重叠，但新增了更完整的数据结构、代码、视觉规范、ConfigManager、数据库/OBS 连接、前端 starter 和真实修改路径。

### 安全边界

1. `13_env_and_references.txt` 含真实内网地址、用户名及密码/OBS Key 的实现说明，`06_delta_api.txt` 含认证方式；整个目录按本地受限来源处理并由 `.gitignore` 排除。
2. 原件保持字节不变，不在原文件上净化、改名或覆盖；后续通过逐文件 SHA-256 检查来源漂移。
3. 规范知识必须内化配置 API、加载行为、连接器职责、接口契约和陷阱，但不得复制秘密值或可直接连接生产的凭据。
4. 本地实验使用独立 `.env`、本地 PostgreSQL 和明确 mock；不得尝试连接材料中记录的生产数据库、Delta、OBS 或 SSO。
5. 需要移植到实验 Harness 时另建可提交的净化来源包，并记录原始指纹和逐项净化说明；净化副本不冒充原件。

## ChatGPT 质检项目导出

### 来源与格式

- 来源：用户从 [ChatGPT 质检项目](https://chatgpt.com/g/g-p-6a574e9160d88191b9fc129cb47cbb1a/project)人工下载，2026-07-19 放入 `knowledge/raw/quality_check/`。
- 文件形态：25 个 UTF-8 `.txt` 文件，正文实际为 Markdown；读取时按 Markdown 解析，但不为修正后缀而重命名原文件。
- 完整性指纹：在资料集目录执行 `sha256sum -- *.txt | LC_ALL=C sort -k2 | sha256sum`，结果为 `7add0cb2ffb9ca100c657fbcc418bf17ea36a8695f1e5f10775d504c1f3955d9`。
- 去重结果：与 `/home/yyh/project/ai-knowledge-base/raw/` 比较，当前发现 1 个字节级重复文件；其余文件仍可能在语义上重叠，摄入具体主题时继续做局部合并和冲突检查。

### 内容导航

#### 业务与产品结构

- [人工质检-交付任务与行动项机制](quality_check/人工质检-交付任务与行动项机制.txt)
- [人工质检-人力管理体系设计](quality_check/人工质检-人力管理体系设计.txt)
- [人工质检-标注验收执行三阶段流程](quality_check/人工质检-标注验收执行三阶段流程.txt)
- [人工质检总览信息架构](quality_check/人工质检总览信息架构.txt)
- [质检业务总览信息架构](quality_check/质检业务总览信息架构.txt)

#### 平台与技术架构

- [质检一站式平台顶层架构](quality_check/质检一站式平台顶层架构.txt)
- [质检平台-API契约与前端交互设计](quality_check/质检平台-API契约与前端交互设计.txt)
- [质检平台-Delta调用与状态回查设计](quality_check/质检平台-Delta调用与状态回查设计.txt)
- [质检平台-Repository与数据库访问设计](quality_check/质检平台-Repository与数据库访问设计.txt)
- [质检平台-scene_name概念](quality_check/质检平台-scene_name概念.txt)
- [质检平台-人工质检模块实施计划](quality_check/质检平台-人工质检模块实施计划.txt)
- [质检平台-后端分层与组件边界设计](quality_check/质检平台-后端分层与组件边界设计.txt)
- [质检平台-综合快照表设计](quality_check/质检平台-综合快照表设计.txt)
- [质检平台-通过打回规则与执行设计](quality_check/质检平台-通过打回规则与执行设计.txt)
- [质检平台-领域模型层设计](quality_check/质检平台-领域模型层设计.txt)
- [质检平台-验收采样配额与任务选择设计](quality_check/质检平台-验收采样配额与任务选择设计.txt)
- [验收前置条件-快照刷新四级实现契约](quality_check/验收前置条件-快照刷新四级实现契约.txt)

#### 前端与产品视图

- [质检一站式平台前端Demo设计计划](quality_check/质检一站式平台前端Demo设计计划.txt)
- [质检平台-人工质检交付中心前端设计](quality_check/质检平台-人工质检交付中心前端设计.txt)
- [质检平台-人工质检前端页面与状态设计](quality_check/质检平台-人工质检前端页面与状态设计.txt)
- [质检平台-人工质检标注中心前端设计](quality_check/质检平台-人工质检标注中心前端设计.txt)
- [质检平台-人工质检验收中心前端设计](quality_check/质检平台-人工质检验收中心前端设计.txt)

#### 可复用界面组件

- [质检平台可配置卡片布局组件设计](quality_check/质检平台可配置卡片布局组件设计.txt)
- [质检平台开源数据工作台实现设计](quality_check/质检平台开源数据工作台实现设计.txt)
- [质检平台统一数据工作台组件设计](quality_check/质检平台统一数据工作台组件设计.txt)

### 使用边界

1. 文件中的 `status: active`、更新时间和“已完成”只代表导出材料自己的声明，不自动证明当前生产系统或当前代码仓状态。
2. 使用时先区分：人工确认的业务含义、历史运行记录、目标设计、实现进度声明和待确认问题；不能把它们混写成一类事实。
3. 精确代码行为仍回到对应仓库和固定提交核验。当前已观察到部分材料声称存在的 2026-07-09/14 实现，在 `/home/yyh/project/ai-knowledge-base` 提交 `3cf3934` 中并不存在。
4. 原始材料不直接写入规范知识底座。任务只定向读取会改变结论的部分，经去重、冲突检查和人工审查后，才形成规范知识和产品视图。
5. 当前 M1 的整理结果与处理边界见 [M1 来源覆盖](../../eval/reference/m1-knowledge-ingestion-v1/source-coverage.md)；这不限制资料集在后续质检、平台设计或开发任务中继续使用。
