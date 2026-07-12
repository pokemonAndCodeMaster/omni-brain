# 项目 Skill 体系审计｜2026-07-12

> **状态**：Static audit + first remediation / Provisional。它回答当前文件与实现是否一致，并记录首轮治理结果；不证明 Agent 在真实运行中会稳定遵守 Skill。  
> **范围**：`.agents/skills/` 中九个历史项目 Skill、其引用脚本、Git 首次出现记录，以及与 Blueprint/AGENTS 的契约关系。  
> **判断原则**：文件存在不等于能力存在；初始化来源不等于已经批准；静态合理不等于行为已验证。

## 1. 审计尺度

每个 Skill 按七项检查：

1. 是否服务 Blueprint 中明确组件或真实用户旅程；
2. 是否值得模型自动发现，还是应由用户显式触发或仅作参考；
3. 描述、步骤、依赖脚本和当前代码是否一致；
4. 是否越过授权边界，尤其是原料保存、规范入库、基线更新和创建新 Skill；
5. 是否有清晰、可检查的完成标准和失败降级；
6. 是否与 AGENTS、其他 Skill、代码或规格重复维护同一含义；
7. 是否有真实 Task、Trial 或运行证据支持其采用强度。

采用强度仅为本轮审计建议：

- **retain-experimental**：可继续在已声明范围实验，但不得扩大全局能力声明；
- **reference-only**：只提供写作或设计尺度，不是 Omni-Brain 运行组件；
- **quarantine**：保留文件供迁移，不应按当前描述自动执行；
- **rewrite-first**：有产品价值，但必须先重写契约并建立用例；
- **retire/merge candidate**：职责可能应合并到其他机制，尚待实例决定。

## 2. 全量矩阵

| Skill | 来源证据 | 蓝图归属 | 当前事实 | 主要问题 | 建议 |
|---|---|---|---|---|---|
| `knowledge-query` | Phase 0 创建；2026-07-12 重写 | 6 检索与任务上下文 | 能以 `rg`/直读做人工有界查询；检索脚本仍是 stub | 尚无检索质量 Eval；“所有高相关命中”在大库中缺预算契约 | **retain-experimental**，以人工 fallback 为当前真实能力 |
| `task-knowledge-prep` | 2026-07-12 新建并重写 | 8 任务知识准备工作区 | 账本脚本已实现；恢复切片有 Task v2 和两次人工 Trial | 只有恢复核心切片；语义准备度、补知、长期分流仍主要靠强模型 | **retain-experimental@recovery-core**，不得泛化成完整闭环 |
| `writing-great-skills` | 2026-07-12 从用户级 Skill 安装 | 不属于产品组件；Skill 工程参考 | 提供 invocation、information hierarchy、predictability、pruning 尺度 | 缺上游版本/许可证/同步方式记录；不应被当作 Omni-Brain 产品决定 | **reference-only**，补 provenance 后固定版本 |
| `knowledge-ingest` | Phase 0 初始化；2026-07-12 首次治理重写 | 5 摄入与 Brownfield 迁移 | 已收窄为明确长期知识变更，支持 research/spec/knowledge/eval/task 分流与 stub `manual_fallback` | 仅通过静态契约测试，尚无独立模型路由和端到端摄入 Trial | **implemented / explicit-experiment** |
| `eval-runner` | Phase 0 初始化；2026-07-12 退役活动 Skill | 10 评测与可观测性 | `eval/runner.py` 不存在；已有 Task v2、fixture 和人工校准 | 旧命令、阈值、Suite 和基线更新均为虚构或过早固定 | **retired until runner**；由真实实现重新申请准入 |
| `knowledge-health` | Phase 0 初始化；2026-07-12 退役活动 Skill | 9 知识治理与演进 | `health_checker.py` 和索引编译器为 stub | 旧契约声称可扫描冲突/过期/孤岛并生成报告 | **retired until deterministic checks** |
| `code-ingest` | Phase 0 初始化；2026-07-12 退役活动 Skill | 2/4 规范知识与派生结构 | `extract_code_skeleton.py` 不存在，编译/哈希为 stub | 旧契约假设自动提取和哈希回写，从目录批量建卡会制造易失副本 | **retired until code-context slice** |
| `task-reflector` | Phase 0 初始化；2026-07-12 退役活动 Skill | 9 治理与演进 | 无独立实现或 Eval，且调用已退役项目 `skill-creator` | 自动反思—建卡—建 Skill 链会绕过授权和价值门禁 | **retired / merge decision pending** |
| `skill-creator` | Phase 0 初始化；2026-07-12 退役活动 Skill | 9/10 系统演进与评测 | 与系统级同名能力冲突 | “重复即固化”违反实例验证后固化 | **retired**；长期变更先走 C 类任务和 change set |

## 3. 横切发现

### 3.1 初始化遗产被注册成默认能力

七个 Skill 与 stub 脚本在同一次 Phase 0 提交中创建；其中 `knowledge-query` 后来已经重写，其余六个仍基本保持初始化契约。它们更像目标能力草图，却全部放在活动 Skill 目录中，导致 Agent 可能发现并调用。目录存在表达了“可使用”，但没有区分 experimental、verified slice 或依赖状态。

### 3.2 描述比正文更危险

模型每轮先看到 description。`knowledge-ingest` 的“沉淀、整理、记录”覆盖面过宽，`task-reflector` 的“任务完成”也极易命中；即使正文有人工确认，错误 Skill 已经先被拉起并塑造行动。治理应先修 invocation，再修长流程。

### 3.3 Skill 把目标设计写成当前事实

多个 Skill 直接引用不存在的命令、自动索引、代码哈希、冲突检测和评测阈值。此类内容应留在 Blueprint/spec 的目标或 gap，而不是作为可执行步骤。

### 3.4 自动复利机制会先造成自动膨胀

`task-reflector → knowledge-ingest → skill-creator` 形成“任务结束就提炼、重复两次就固化”的链路。它缺少真实复用价值、唯一职责、行为 Eval、上下文负载和回滚门禁，会把偶然做法快速固化为长期资产。

### 3.5 Skill 缺少自己的生命周期与证据链

当前没有统一记录：owner、来源版本、适用组件、依赖能力、采用强度、已验证切片、失败降级、对应 Eval 和替代关系。不能把这些全部塞进 SKILL.md，也不应因此立即建设 registry；当前先由 Blueprint、审计、Git 与 Eval 分担，只有出现真实查询和同步成本后再设计派生视图。

## 4. 处置顺序

### Slice 1：止住错误触发

先处理 `knowledge-ingest`、`eval-runner`、`skill-creator`：收窄或暂停模型自动触发，删除不存在能力的承诺，并明确人工降级。完成标准是用“沉淀研究”“跑评测”“重复操作”三个正例和至少三个不应触发的反例验证路由。

### Slice 2：重建知识变更链

以真实 Eval 研究沉淀为 fixture，重新设计：来源登记 → 候选切片 → 规范归属/复用/视图影响 → 冲突与成熟度 → change set → 授权写入 → 校验。`knowledge-ingest` 不再等同于“保存全文并批量建卡”。

### Slice 3：重建治理型 Skill

决定 `task-reflector` 是保留独立 Skill，还是合并到任务关闭与对话回收；将 `skill-creator` 改为“提出 Skill change set”，只有真实重复、职责唯一、稳定步骤和 Eval 都成立后才创建。

### Slice 4：实现后再恢复操作型 Skill

`eval-runner`、`knowledge-health`、`code-ingest` 只有在对应确定性工具存在并有测试后，才能恢复模型可发现性。Skill 应调用真实接口，不承担尚未实现系统的产品想象。

## 5. 当前不能声称的结论

- 不能仅凭本次静态审计删除某个产品能力；问题可能在当前 Skill 契约而非能力本身。
- 不能声称 `knowledge-query` 或 `task-knowledge-prep` 已普遍可靠；它们只有人工实现或单切片证据。
- 不能声称需要独立的 Skill 清单或状态 Schema；先用活动文件、Blueprint 和 Eval 解决当前问题。
- 不能把 `writing-great-skills` 的写作理论直接当成 Omni-Brain 的 Skill 产品模型。

## 6. 首轮治理结果

活动 Skill 已从九个收敛为四个：`knowledge-query`、`task-knowledge-prep`、`writing-great-skills` 和重写后的 `knowledge-ingest`。退役直接删除 `SKILL.md`，历史仍由 Git 保存；无实际消费者的 `.agents/skills.json` 也已删除，没有建立新的 registry 或 `skill-change-proposal`。

新增 `tests/test_skill_contracts.py` 与 `eval/datasets/skill_execution/skill_governance_v1.yaml`：前者机械检查活动注册、窄触发和 stub 边界；后者含 13 个正例、反例和失败例。当前只有契约测试证据，尚未运行独立 Agent Trial。
