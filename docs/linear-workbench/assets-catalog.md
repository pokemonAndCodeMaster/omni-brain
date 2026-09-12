# 已有知识与能力：从哪里开始读

这里按你想做的事情找入口。只想学习或查资料，直接打开正文；需要继续推进，再进入相关事项。目录不复制一份攻略、代码说明或实时进度。

核对日期：2026-09-12。本次核对了 Linear 当前金铲铲入口、资料索引、版本说明及 YYH-5、YYH-7、YYH-8 全文，以及仓库现行知识入口、共作说明、技能入口和相关源码。游戏规则没有在这次整理中重新验证，软件也没有因“登记到目录”而重新通过运行验收。

## 先按目的选择

| 我现在想做什么 | 从哪里开始 | 能得到什么 |
|---|---|---|
| 学金铲铲阵容、经济和对局判断 | [金铲铲：从这里开始](https://linear.app/yyhpokemonmaster/document/4ab9d21ea156) | 按学习问题进入独立攻略，不需要先找事项 |
| 查质检业务和代码背景 | [质检知识入口](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/index.md) | 从领域全貌进入人工质检、验收、规则、数据与软件 |
| 了解“共作”工作台已经能做什么 | [共作使用与运行](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/docs/gongzuo.md) → [交付说明](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/workspaces/reviews/team-workbench-product-definition/review.md) | 日常使用过程、启动办法、真实结果与尚未解决的部分 |
| 让 Codex 使用已有方法做事 | [本仓 Agent 入口](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/AGENTS.md)与[下方技能表](#让-codex-使用已经积累的方法) | 从查询、讨论、开发、整理到审查选择合适方法 |
| 找项目当前方向和后续工作 | [当前工作台](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/docs/now.md) → [长期目标](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/docs/blueprint.md) | 区分近期正在做的事、产品方向和历史阶段 |
| 复用过去实验的实现或证据 | [实验总账](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/eval/STATUS.md) | 找到固定来源、结果、适用边界和可恢复的版本 |

## 金铲铲：当前正文、历史线索与工具探索

第一次来先读[领域入口](https://linear.app/yyhpokemonmaster/document/4ab9d21ea156)。以后可以直接进入下面对应的正文：

| 想弄清的问题 | 正文入口 |
|---|---|
| 攻速怎样成长、前后排怎样配合、换人会得到和失去什么 | [五迅捷射手精讲](https://linear.app/yyhpokemonmaster/document/6501984799cb) |
| 商店机会怎样变成战斗收益、八级到九级怎样选择 | [地狱火精讲](https://linear.app/yyhpokemonmaster/document/70ca7da5e63d) |
| 奖励给谁、何时收取、追星和升级怎样取舍 | [黑暗仪式精讲](https://linear.app/yyhpokemonmaster/document/29d44128413e) |
| 金币、装备、换人和对手信息怎样支持一次选择 | [公共决策精讲](https://linear.app/yyhpokemonmaster/document/9274007dcedb) |
| 哪些依据来自公告、作者、模型或真实对局 | [版本依据与数据口径](https://linear.app/yyhpokemonmaster/document/a393ec381487) |
| 回看已有的条件阵容 | [裁决婕拉](https://linear.app/yyhpokemonmaster/document/5c213c5441b5) |
| 复盘已经停用的旧思路 | [皎月螳螂](https://linear.app/yyhpokemonmaster/document/98bfdfec42fd) |
| 找历史讨论线索，或者了解材料应怎样写才好读 | [资料索引与阅读要求](https://linear.app/yyhpokemonmaster/document/fcdbaefb8333) |

这些正文在 Linear 维护。当前三条阵容路线是学习与研究材料，不能据此说已经取得本服同口径统计、证明了最强排名或完成实战验证。裁决婕拉尚未按最新图文教学标准整篇重写；皎月螳螂的旧循环只供历史复盘。使用时先看目标正文的适用版本和依据。

不用新增一批同名事项。已有三条工作分别负责不同结果：

- [YYH-8：图文教学与对局推演](https://linear.app/yyhpokemonmaster/issue/YYH-8)维护当前攻略、机制与实战核验。具体剩余问题以事项当前正文为准。
- [YYH-7：原有资料接入](https://linear.app/yyhpokemonmaster/issue/YYH-7)负责原 ChatGPT 材料的完整阅读与接续。索引已经记录部分可读附件和旧讨论线索，但全部历史正文、图片、对话尚未迁入 Linear。
- [YYH-5：游戏助手需求探索](https://linear.app/yyhpokemonmaster/issue/YYH-5)先明确首个实际使用场景和数据来源。尚无正式产品规格、数据接口验证或代码成果，不因已有攻略就把助手算作已开发。

YYH-8 记载已在原 ChatGPT 会话交付图文 HTML、ZIP 与可复算模型。本次没有拿到这些文件，不能把它们列成本仓可打开的资产，也不能把本地路径伪装成 Linear 图片附件。要保存到仓库时，先取得原文件并核对正文、图片和模型，再把稳定文件入口关联回 YYH-8；历史材料取得与迁移仍在 YYH-7 接续。

## 质检知识：先读正式知识，再查当前实现

[质检知识入口](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/index.md)已经提供完整阅读路线：质检领域 → 人工质检 → 验收 → 业务、数据和软件专题。日常不需要浏览原始材料目录。

| 我需要理解什么 | 直接入口 |
|---|---|
| 验收在整个业务中的位置和完整过程 | [验收总览](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/overview.md) |
| 采样、分配、状态和结论怎样影响工作 | [采样与分配](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/sampling-and-assignment.md) · [数据流与状态](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/data-flow-and-state.md) |
| 业务问题应该查哪层代码 | [业务到代码地图](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/implementation-map.md) · [Python 软件结构](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/python-architecture-and-implementation.md) |
| 哪些说法还有缺口、应向哪里追溯 | [待确认事项](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/domains/quality/manual/acceptance/open-questions.md) · [来源记录](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/knowledge/published/quality-check/sources/index.md) |
| 当前应用的人工质检页面和数据契约 | [应用说明](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/README.md) · [快照契约](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/docs/snapshot-contract.md) · [运行验证记录](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/docs/verification-report.md) |

正式知识对人工质检验收最深入，已经支持学习和局部开发定位；大模型质检、自动化质检等目前只有领域位置，不能据此解释完整内部流程。知识包也不是生产操作手册：当前规则、真实数据、部署和接口行为仍要核对源码与运行。

已有开发和回写实验有各自冻结的代码版本。不能把实验里成功的功能自动写成当前应用已经具备，也不能让较新的源码静默覆盖历史知识的适用范围。继续一项开发时，先用知识找位置，再读当前对应源码；形成长期规则变化时，回到原主题修订并保留来源。

## 共作：已有的产品、源码与明确边界

共作已经有本地应用，承载想法讨论、工作事项、共同背景、AI 委托、成果与验证、会议和能力改进。先看[交付说明](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/workspaces/reviews/team-workbench-product-definition/review.md)了解实际使用，再按[运行说明](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/docs/gongzuo.md)启动。正式使用前先启动应用。本次只用隔离的测试数据验证了子事项委托页面和输入组装，不把文档中的本地地址算成已经启动的完整服务。

| 需要继续哪部分 | 当前入口 |
|---|---|
| 看页面结构、交互和调用 | [共作前端](https://github.com/pokemonAndCodeMaster/omni-brain/tree/main/apps/quality-platform/src/frontend/src/features/gongzuo) |
| 查事项、共同背景、关系和会议 | [工作服务](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/src/gongzuo/service.py) |
| 查一次 AI 运行如何固定任务与背景 | [运行服务](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/src/gongzuo_runtime/service.py) |
| 查执行环境如何准备、怎样接单运行 | [执行进程](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/src/gongzuo_runtime/worker.py) |
| 查知识修订、试用和发布给后续运行的行为 | [知识与能力服务](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/src/gongzuo_knowledge/service.py) |

已有证据证明过本地事项保存、背景版本、会议快照，以及一条很小的“试用工作指引 → 检查结果 → 发布 → 后续执行采用”的过程。这证明内容和运行能接起来，还没有证明复杂真实需求能自动得到好方案、充分测试和合格交付。

当前修复与仍需跟踪的范围：

- **子事项委托修复。** [YYH-15](https://linear.app/yyhpokemonmaster/issue/YYH-15)跟踪[事项页](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/apps/quality-platform/src/frontend/src/features/gongzuo/pages/ItemDetailPage.vue)原先把父事项误传给委托表单的问题。候选修复已通过真实浏览器请求与服务端输入组装验证：提交子事项，保留子目标及父背景，父背景更新不改变旧运行。此次使用隔离测试数据，没有把外部 AI 实际执行或用户数据库持久化算成新验证；合入与后续状态看原事项。
- **真实任务和团队环境。** 按任务选择恰当知识、跨多次开发保留环境、CodeHub/MR 自动同步、公司身份与权限、真实团队工作站和容器运行，都不能因为本地原型存在就标为完成。先围绕一项实际工作明确要验证的路径，再决定实施范围，避免为所有历史设想机械建待办。

共作的现行使用说明、源码和交付证据已经可以直接阅读；目前正式知识总入口仍只登记了质检知识包，尚不能把这些共作文档称为已发布的规范知识包。

## 让 Codex 使用已经积累的方法

在仓库中直接说明要解决什么，Agent 应根据任务读取已有技能；无需你记住每个名字。技能负责做事的方法，事项保存这件事的目标、当前判断和结果；新开会话时先读事项，再选择所需技能。

| 当前任务 | 已有方法 | 已知适用范围 |
|---|---|---|
| 学习、查已有事实、找缺口和任务背景 | [answer-from-knowledge](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/.agents/skills/answer-from-knowledge/SKILL.md) | 正式质检知识的问答与入口路由有实际验证；精确代码行为还需实时源码 |
| 把复杂诉求讨论成可实施的方案 | [form-solution](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/.agents/skills/form-solution/SKILL.md) | 从真实场景、目标与例子明确需求，再比较方案；第二领域试验仍有失败边界 |
| 开发、修复和重构 | [develop-with-knowledge](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/.agents/skills/develop-with-knowledge/SKILL.md) | 先取得必要知识与当前事实，完成可运行变化和验证，再交接知识变化 |
| 整理新材料或把代码变化更新进知识 | [ingest-knowledge](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/.agents/skills/ingest-knowledge/SKILL.md) | 质检增量文档、同系统相邻代码回写有范围限定的成功证据；不保证任意领域自动可靠 |
| 审查成果、解释变化与交付边界 | [review-work](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/.agents/skills/review-work/SKILL.md) | 对照原需求、实现和证据，明确解决到了哪里；检查清单不能代替可读说明 |

[AGENTS.md](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/AGENTS.md)是项目操作入口；[harness.yaml](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/harness.yaml)与[Agent 注册表](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/config/agent-registry.yaml)是现有配置；[packages/harness](https://github.com/pokemonAndCodeMaster/omni-brain/tree/main/packages/harness)保存可追溯发布快照。当前能力与失败边界以[实验总账](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/eval/STATUS.md)和对应证据为准，不能仅凭技能文件存在就声明有效。

技能改进应来自真实工作：在原事项记录具体失败例子，修改负责该行为的已有技能，用原例和一个相邻例检查，再更新使用入口和版本。普通反馈先修内容或页面；只有做事方法反复导致错误时，才改技能或全局 Agent 规则。

## Spider 与历史实验：保留成果，带着边界复用

Spider 多源信息平台已经有获批方案、实现与真实验证证据，入口是[参考实现审计](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/eval/trials/real_work/SPIDER_REFERENCE_IMPLEMENTATION_SOL_XHIGH_001/audit.md)和[版本清单](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/eval/trials/real_work/SPIDER_REFERENCE_IMPLEMENTATION_SOL_XHIGH_001/manifest.yaml)。方案归档 `refs/eval/workspaces/spider-multisource-r2-certified-v1` 与产品输入归档 `refs/eval/workspaces/spider-multisource-platform-v1` 本次已在主仓核实存在。

参考记录包含多源配置与采集、数据迁移、信息列表/详情、个人状态、筛选和导出。它们是可审查和选择复用的历史资产，没有整分支自动晋升到 Omni-Brain 产品主线。受保护页面的真实采集仍有人工验证边界。

恢复前先核对目标版本：早期审计、manifest 与后续总账的功能分支提交记录存在时间差。旧 manifest 的临时执行路径不是长期入口，应依据 Git 归档重建，再检验当前要复用的部分。不要因旧路径不存在就丢掉已保存证据，也不要把旧报告当成刚刚运行成功。

[YYH-16](https://linear.app/yyhpokemonmaster/issue/YYH-16)跟踪下一步：选定一个实际要复用的能力，说明它进入主线后服务什么工作，恢复对应版本，审查实现、知识与测试分别怎样接入。其余历史 Trial 继续从[实验总账](https://github.com/pokemonAndCodeMaster/omni-brain/blob/main/eval/STATUS.md)查阅，不把每条旧实验的“下一步”重新登记为日常待办。

## 目录怎样保持有用

新增成果只把入口加到对应领域，正文仍在原知识页、Linear 文档或代码仓维护。事项结束后，读者仍能从领域入口找到成果；事项只是保留它形成和验证的过程。

本目录和页面里的资产清单是导航。来源更新后先读取原文再修正导航，不在多个地方维护相同的规则、游戏参数或进度表。正式知识、原始依据、可运行代码和历史实验各自保留清楚入口，来源不完整时保留缺口。
