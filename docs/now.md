# Omni-Brain 当前工作台

> **用途**：新会话先读这一页，确认项目现在做什么、没有做成什么。细节按链接下钻。
> **最近整理**：2026-07-20。

## 一句话状态

Omni-Brain 要交付一套可移植、OpenCode/Codex 兼容、换模型后仍能工作的知识与任务 Harness。M1 reference v1 已由用户认证，内容快照为 `1f3760b3d8e02e77bf0117cc6a6b7ef90b874be7`；当前从候选 Harness 干净基线 `890e65f` 启动 GPT-5.6 Luna（medium）正式盲测。

## 当前唯一主线

围绕一批真实的人工质检验收材料，先设计、再实现一条用户实际能用的知识整理与摄入纵向切片：

```text
用户把混乱材料交给 Harness
→ Harness 帮助理解、归并、保留细节并暴露冲突与未知
→ 用户在必要位置确认或纠正
→ 获准内容进入唯一规范知识底座
→ 形成用户可浏览的领域/产品视图
→ 人和另一模型立刻用这些知识回答真实问题
```

这条链路对应 Blueprint 的 C1、C2、C5、C7 和最低必要的 C9。脚本、Skill、Schema、Eval 只在支撑这条真实链路时才建设，不单独算产品进展。

## 已确认保留的成果

- 长期产品目标、质检平台长期牵引和 Blueprint C1—C10 组件边界；
- 设计/实践仓与独立实验 Harness 分离的交付方式；
- `/home/yyh/project/omni-brain-harness` 的干净可移植基线；
- 任务案恢复的单切片实现和既有 Eval 资产，但它们不是当前产品主线；
- OKF、OpenWiki、LLMWiki、gbrain、Yuxi、CodeGraph、Graphify 等一手调研材料；调研结论仍只是技术输入，不是已定方案；
- 仓库外 `/home/yyh/project/ai-knowledge-base` 中的真实业务原料，未被清理或改写。

## 已撤回并清理的内容

- `ingest-brownfield-knowledge` 实验 Skill；
- `knowledge_case.py`、`materialize_m1_trial.py` 和对应 Schema、测试、fixture、spike、Eval 包装；
- 由错误路线手工生成并当作能力成果的人工质检验收知识卡和 Hub；
- `portable-opencode-harness` 旧 M1 任务案、架构包和 ADR；
- 独立实验 Harness 中的全部旧 M1 增量。

这些内容不再作为实现、验证证据或后续兼容负担。相关想法只有在新设计中被真实用户流程重新证明必要时才会重做。

## 当前已批准并实现的实验切片

[M1 真实知识摄入方案](specs/m1-real-knowledge-ingestion-design.md) 的以下五项基础取舍已获用户批准：

1. 领域主题优先的规范结构，不再按 Source/Concept/Playbook/CodeModule 拆散领域知识；
2. 文档加段落级知识块，规则和算法强制保留输入、输出、不变量、步骤、边界和证据；
3. Markdown/OKF + Git + 摄入 Skill + 一个只读校验器，M1 不引入数据库、图或向量；
4. 用户只审发布、冲突、补充和忽略四类项，批准后才写正式知识；
5. 第一轮直接使用真实验收材料，旧五张手工卡不作为输入或参考答案。

用户已批准 M1 真实知识摄入方案的全部取舍。首批知识没有形成可浏览的领域位置视图和旅程/学习视图时，不算摄入完成；固定关系词表、`stable_id` 和 `applies_to` 不进入 M1，改用显式领域地图、OKF 正文语义链接和受审公共能力抽取；所有内部跳转使用带 `.md` 的标准相对链接，反向链接由只读扫描派生，不依赖 Obsidian。

Codex 已将空知识骨架、`ingest-knowledge` Skill、模板和只读校验器实现到 `/home/yyh/project/omni-brain-harness`，并通过 40 项测试、空 Bundle 检查和 Skill 校验。候选目录及其 Git 历史均不含旧手工知识、旧 AQ、M1 Eval Contract、固定验收材料或参考答案；目标库仍没有验收知识，并已建立单根提交盲测基线 `890e65f`。

新的 [Milestone 参考成果与晋升闭环](specs/milestone-reference-promotion-loop.md) 已建立。M1 私有参考成果位于 `eval/reference/m1-knowledge-ingestion-v1/`；第 4 轮现有 35 个 Markdown、26 个概念页，使用“业务动作 → Python 结构与运行”和按需 4+1 多视图解释软件，并以“公共能力唯一落点 + 领域使用契约”处理数据库和 OBS。ChatGPT 质检项目的 25 份原料已登记在 `knowledge/raw/index.md`。用户已批准稳定核心、D1—D5 与保留未知，参考内容冻结并认证；候选 Harness 仍在干净基线 `890e65f`，下一步是使用 GPT-5.6 Luna（medium）运行正式盲测并记录完整过程。

## 权威下钻

- 长期目标、组件和成熟度：[Blueprint](blueprint.md)
- 真实能力阶段与当前 M1 完成定义：[Harness 真实能力路线](harness-roadmap.md)
- 产品判断的历史与争议：[产品方向讨论](product-direction-discussion.md)
- 外部技术研究：[知识 Harness 参考研究](research/knowledge-harness-reference-study-2026-07-17.md)
- 当前已实现、待 Trial 方案：[M1 真实知识摄入方案](specs/m1-real-knowledge-ingestion-design.md)
- 参考成果、Harness 蒸馏和阶段晋升：[Milestone 参考成果与晋升闭环](specs/milestone-reference-promotion-loop.md)
- M1 第 1 轮参考成果审查：[review.md](../eval/reference/m1-knowledge-ingestion-v1/review.md)
- 可恢复设计任务案：[m1-real-knowledge-ingestion-design](../workspaces/task-cases/m1-real-knowledge-ingestion-design/overview.md)
