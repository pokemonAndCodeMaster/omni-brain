# Agent Harness 实体、能力与验证报告

> **审计对象：** `/home/yyh/project/omni-brain-harness@a2f790e`
> **详细使用入口：** [Harness README](../../../omni-brain-harness/README.md)
> **实验真值：** [实验与评测总账](../../eval/STATUS.md)

## 当前 Harness 到底是什么

它不是一个后台服务，也不是 Python 把 AI 圈进固定流程。实际运行结构是：

```text
Codex / OpenCode 原生会话
        ↓ 自动读取
AGENTS.md：判断任务类型并选择最低充分 Skill
        ↓
4 个 Skill：指导模型怎样理解、阅读、开发、写知识和交付
        ↓ 按需调用
5 个确定性脚本：负责路由、状态、来源、隔离运行和结构检查
        ↓
真实产物：答案 / 代码与运行结果 / 候选知识与产品视图 / 可恢复任务案
```

AI 会话负责语义工作；文件和脚本把模型不应临场发挥的部分固定下来。把这套目录复制进另一个项目后，宿主从根 `AGENTS.md` 和 `.agents/skills/` 发现能力，不需要 Omni-Brain 自己调用模型 API。

## 组件实体清单

| 实体 | 类型 | 实际职责 | 用户最终拿到什么 | 当前成熟度 |
|---|---|---|---|---|
| [`AGENTS.md`](../../../omni-brain-harness/AGENTS.md) | 根项目规则 | 把自然语言请求路由到直接执行、知识问答、知识摄入、带知识开发或任务准备；约束来源只读、候选隔离和真实验证 | 正确工作流被自动触发；用户无需记脚本命令 | 已实现，109 项回归覆盖关键路由 |
| [`harness.yaml`](../../../omni-brain-harness/harness.yaml) | 能力 manifest | 声明每项能力的入口文件、依赖、采用级别和限制 | 人和 Agent 能知道“哪些真的能用、只能用到哪里” | 已实现；它不是运行引擎 |
| [`answer-from-knowledge/SKILL.md`](../../../omni-brain-harness/.agents/skills/answer-from-knowledge/SKILL.md) | Skill | 从正式/候选知识回答学习、事实、缺口和任务上下文问题；最多三篇规范页 | 直接答案、现实状态、依据和最小补证动作 | `verified@quality-check-trusted-query-slices` |
| [`knowledge_route.py`](../../../omni-brain-harness/.agents/skills/answer-from-knowledge/scripts/knowledge_route.py) | Python 只读工具 | 遍历知识入口可达 Markdown，用标题、链接上下文、正文词项和问题意图返回 `PRIMARY/FALLBACK` | 少量确定性候选路径；不生成答案、不写状态 | 10 条质检路由通过；不是全文/向量/图检索 |
| [`develop-with-knowledge/SKILL.md`](../../../omni-brain-harness/.agents/skills/develop-with-knowledge/SKILL.md) | Skill | 让原生开发会话先取最低充分知识，再沿真实纵切改代码，验证最大组合、真实 API/数据库/页面和副作用 | 用户要求的代码/SQL/配置、真实运行证据、知识变化候选 | 三类质检开发和一个查询→开发复合切片 verified |
| [`ingest-knowledge/SKILL.md`](../../../omni-brain-harness/.agents/skills/ingest-knowledge/SKILL.md) | Skill | 指导模型执行完整材料整理、聚焦代码整理或代码变化回写；规定内容保真、知识组织、产品视图和人工发布 | 规范知识、领域/旅程视图、来源记录、审查说明 | 增量摄入跨模型 verified；代码回写在相邻同系统切片 verified |
| [`ingestion_workspace.py`](../../../omni-brain-harness/scripts/ingestion_workspace.py) | Python 状态/隔离工具 | 建摄入案，扫描来源，限制每轮来源，登记发现和知识 owner，检查影响，冻结 Python 字段契约，隔离运行，重建审查页 | `draft/knowledge/`、候选领域地图、`review.md`、运行证据和可恢复状态 | 核心工作台已实现；不判断业务真伪、不自动写正文 |
| [`knowledge_check.py`](../../../omni-brain-harness/scripts/knowledge_check.py) | Python 检查器 | 检查 OKF frontmatter、领域地图、Markdown 链接/锚点、规范页可达性、视图、引用和来源记录 | 可读 PASS/ERROR 报告或 JSON | 已实现并进入摄入发布前检查 |
| [`task-knowledge-prep/SKILL.md`](../../../omni-brain-harness/.agents/skills/task-knowledge-prep/SKILL.md) | Skill | 为目标模糊、知识冲突或高风险任务建立问题—证据—决策准备循环 | 可跨会话续接的任务框架、关键答案、决策上下文和长期知识候选 | 恢复与原子回答有限切片 verified；不是当前开发主线 |
| [`task_case.py`](../../../omni-brain-harness/scripts/task_case.py) | Python 账本工具 | 创建/恢复任务案，追加事件和证据，原子回答关键问题，重算两类准备度，重建 Markdown 视图 | `case.yaml`、JSONL 证据/事件、准备度报告、决策上下文 | 已实现；机械准备度不等于语义质量 |
| [`source_run.py`](../../../omni-brain-harness/scripts/source_run.py) | Python 来源工具 | 固定用户授权的本地 Git 范围、HEAD、文件状态、SHA-256 和范围指纹，并比较变化 | 原子 `run.yaml`、manifest、必要快照和变更判断 | 本地 Git 范围切片 implemented；不解释业务语义 |
| [`knowledge/`](../../../omni-brain-harness/knowledge/index.md) + [`knowledge-domains.yaml`](../../../omni-brain-harness/config/knowledge-domains.yaml) | 空知识 Bundle | 提供规范知识、系统、公共能力、来源和两种产品视图的正式落点 | 可由普通 Markdown 工具浏览和跳转的知识库 | 空 OKF 兼容骨架 implemented；不预装质检答案 |
| [`assets/`](../../../omni-brain-harness/.agents/skills/ingest-knowledge/assets/) | 写作骨架 | 提供知识页、领域总览、软件架构、来源、产品视图和公共能力审查的可复用结构 | 风格一致但不强制同一章节的候选知识 | 已进入摄入 Skill；正文仍由模型与人审查 |
| [`tests/`](../../../omni-brain-harness/tests/) | 回归集 | 固定路由、Skill 契约、工作台状态、查询排序、来源信封和知识结构行为 | 修改 Harness 后能发现能力回退 | 当前 108/108 通过 |

## 四条用户工作流如何落到实体

### 1. 用户问现有知识

```text
用户自然语言问题
→ AGENTS.md 选择 answer-from-knowledge
→ knowledge_route.py 返回 PRIMARY 和候补
→ Skill 要求先读 PRIMARY、按未答项最多再读两篇
→ 模型输出答案、已知/未知/冲突、知识路径和下一补证动作
```

**不会产生：** 摄入案、YAML、中间报告、知识修改。

**已经证明：** 质检学习、人员权限、交付状态和冲突问题能从少量规范页得到完整答案；当前未证明大知识库、第二领域或精确源码联查。

### 2. 用户要求开发或排障

```text
用户需求
→ AGENTS.md 选择 develop-with-knowledge
→ knowledge_route.py 取得最多三篇会改变实现的知识
→ Skill 要求编辑前固定用户结果、责任链、组合总量和验证计划
→ 原生 Codex/OpenCode 读取当前源码并完成最小纵切
→ 真实 API / SQL / CLI / 页面 / 副作用验证
→ 交付代码、实际证据、未验证边界和知识变化候选
```

**真正产物：** 代码和运行结果，不是 Harness 报告。Skill 不生成额外任务工作区。

**已经证明：** 页面指标接通、SQL 性能优化、跨层业务算法、无 Bug 零修改排障和一次知识查询→开发组合任务。数据写入有正向证据，但严格输入校验仍有缺口。

### 3. 用户给一批混乱材料

```text
用户指定材料与读者目标
→ AGENTS.md 选择 ingest-knowledge 的 complete 模式
→ ingestion_workspace.py 创建隔离候选并扫描材料
→ next 返回当前材料单元，模型完整阅读并登记 finding
→ 模型按长期 owner 规划 topic，而不是按来源文件建知识
→ 使用 assets 形成规范正文、领域视图和旅程视图
→ knowledge_check.py + 工作台 review
→ 用户只审查 draft/knowledge 和 review.md
```

物理产物：

```text
workspaces/knowledge-ingestion/<case-id>/
├─ draft/knowledge/
├─ draft/config/knowledge-domains.yaml
├─ review.md
├─ evidence/runs/<run-id>/
└─ .state/case.json + source-manifest.jsonl
```

**已经证明：** 真实质检基础文档、代码纵切和存量增量可以形成可浏览知识；同一增量由两个不同模型完成，父知识保留和产品视图同步通过。

### 4. 用户要求代码变化回写知识

```text
固定代码仓库@commit + 已有正式知识
→ AGENTS.md 选择 ingest-knowledge 的 writeback 模式
→ ingestion_workspace.py 冻结来源并判断 same_system / new_system
→ 固定 diff 与报告驱动业务、软件、兼容、公共能力、证据和导航影响计划
→ 模型定向读取并原位修改 draft 中的既有 owner
→ contract-inspect / 临时 worktree run / check-unit / review
→ 停在 publish_ready，等待人工批准
```

**已经证明：** “验收未完成量”同系统相邻增量候选内容 `24/24`，来源身份、公式、前后端职责、旧配置兼容、公共能力和产品视图均可答。

**仍未证明：** 快照导入 holdout 为 `21/24`，模型仍会压缩精确类型/范围、代表性数据库状态值和固定日期夹具；所以当前不能自动发布。

## 工作台脚本与 Skill 的边界

这是理解 Harness 最关键的一点：

| 工作 | 谁负责 |
|---|---|
| 理解用户目的、判断语义、规划知识、写正文、做代码修改 | Codex/OpenCode 模型，在 Skill 指导下完成 |
| 限制来源范围、记录状态、恢复会话、复制父知识、生成 diff、隔离运行 | Python 工具 |
| 判断业务事实是否正确、冲突怎么裁决、是否批准正式发布 | 直接证据 + 模型分析 + 人工决定 |
| 保存正式知识 | 只有人工批准后的发布动作；当前不自动执行 |

因此 `ingestion_workspace.py` 不是一个自主 Agent，也不会调用模型；`SKILL.md` 也不是代码生成器。真正的 Harness 是 **AGENTS 路由 + Skill 语义流程 + 确定性工具 + 知识/工作区 + 测试** 的组合。

## 本轮实际改了哪些 Harness 文件

| 提交 | 实体变化 | 目的与实际结果 |
|---|---|---|
| `6deafb9` | `ingest-knowledge/SKILL.md`、`ingestion_workspace.py` 及测试 | 固定代码来源 branch/HEAD/parent；兼容结论必须追到恢复机制源码。下一轮弱模型正确写出旧列配置合并机制 |
| `183fc6d` | `harness.yaml`、`AGENTS.md`、`docs/now.md` 和契约测试 | 将代码回写标为“同一质检系统相邻增量切片内 verified”，同时保留人工审查和不可外推边界 |
| `a2f790e` | `harness.yaml`、`docs/now.md` | 登记外部契约/数据库状态 holdout 未通过，防止把一个成功题误报成通用能力 |
| 本次修订 | `README.md` | 把此前只展示知识摄入的旧入口改为完整实体地图、真实工作流和明确非能力 |

回归结果为 **109/109**，空知识 Bundle 检查和 Git diff 检查通过。

## 当前能覆盖哪些日常需求

| 日常需求 | 当前判断 |
|---|---|
| 用已有知识快速学习、问答、判断未知 | **可用，质检切片已验证** |
| 整理一批杂乱文档为长期知识和产品视图 | **可用，真实质检材料已验证** |
| 把新增材料融入已有知识而不另建平行库 | **可用，同一增量跨模型已验证** |
| 从业务知识进入前后端/SQL 开发并真实运行 | **可用，三类开发与一个复合切片已验证** |
| 判断页面和 API 不一致是否真是 Bug | **可用，已有零修改排障证据** |
| 安全执行任意数据库写入 | **不可泛化；只有有限正向证据** |
| 代码改完自动更新并发布正式知识 | **只能生成高价值候选；仍需人工批准** |
| 跨领域、任意模型、任意规模稳定工作 | **未验证** |
| 向量检索、知识图谱、Web 知识产品 | **尚未实现** |

## 下一项真正需要开发的实体

不是再增加一份计划文档，也不是继续给 Skill 加提示。下一组件应落在 `ingestion_workspace.py` 的来源 packet/契约检查附近：

1. 从固定源码机械提取常量、类型/范围和跨字段不变量；
2. 从固定验证报告机械暴露代表性前后状态和夹具/环境变换；
3. 把这些结果交给当前问题的 `check-unit`，但不替模型解释或直接写知识；
4. 用一项新的精确约束代码变化验证它是否改善弱模型最终内容。

只有这个新实体让新题的知识内容变好，才进入下一版 Harness；若只让检查更复杂而内容没有改善，应撤回。
