# 当前工作台

> 更新时间：2026-08-15
> 本页只回答：**现在到哪里、产物在哪里、下一步做什么**。完整用例与 Trial 看
> [Eval 总账](../eval/STATUS.md)，长期架构看 [Blueprint](blueprint.md)。

## 当前结论

**本地 AI 软件工作审查已经完成首个可用切片，不再继续拟合同一用例。**

用户多轮审查形成的“验收未完成量”报告已经固化为认证参考。Agent 随后独立比较弱模型候选、
修改通用 Harness 并回归，不再把弱模型候选交给用户逐份审查。最终结果：

- 正向对齐任务：OpenCode DeepSeek 候选达到 `17/18`，超过 `16/18` 接受线；
- 任务对象错位：只读取任务身份包，发现用户未批准该切片后立即停止，不读产品实现；
- 简单状态查询：只回答问题，不创建审查单；
- Harness：`/home/yyh/project/omni-brain-harness`，分支
  `experiment/development-harness-v1`，发布提交 `ab902c6`。

能力当前标记为
`verified_at_deepseek_software_review_positive_mismatch_no_trigger_slice`。这只证明**软件开发的
本地 Markdown 审查**，不代表方案形成、知识摄入审查或 Harness 自审已经验证。

## 实际由什么组成

| 实体 | 作用 |
|---|---|
| `omni-brain-harness/AGENTS.md` | 决定复杂成果何时触发审查，简单任务何时不触发 |
| `.agents/skills/review-work/SKILL.md` | 核对任务对象、控制事实读取、错位停止、按阶段收反馈 |
| `.agents/skills/review-work/references/software-development.md` | 软件报告的完整全貌、需求、方案、实现、验证、R1—R5 结构 |
| `workspaces/reviews/<task-id>/review.md` | 用户唯一需要阅读和反馈的本地审查入口 |

没有新增审查 YAML 协议、事实采集脚本或模型 API。事实仍来自原始任务、Git Diff、源码和真实
运行记录。

## 结果去哪里看

- [认证正向参考](../eval/reference/real_work/manual_qc_pending_visibility_composite_v1/review.md)
- [正向弱模型候选 004](../eval/trials/task_review/TASK_REVIEW_POSITIVE_OPENCODE_DEEPSEEK_004/candidate-review.md)
- [任务错位候选 006](../eval/trials/task_review/TASK_REVIEW_NEGATIVE_MISMATCH_OPENCODE_DEEPSEEK_006/candidate-review.md)
- [多维评价与接受线](../eval/datasets/task_review/task_review_v0_3.yaml)
- [完整独立审计](../eval/trials/task_review/audit.md)
- [三类结果总表](../eval/trials/task_review/suite.yaml)
- [最终提交补充重放的运行失败边界](../eval/trials/task_review/TASK_REVIEW_FINAL_REPLAY_INFRA_FAILURES/README.md)

## 下一步

**推荐转入“模糊开发需求怎样形成可审方案”的能力切片。**

真实输入使用已经保留的“人工质检多维结果分析”原始诉求。目标不是马上开发页面，而是让
Harness 能按任务规模选择轻量或完整方案过程，形成：需求理解、系统上下文、影响范围、方案
选项、需要人工决定的问题、验证计划和可直接交给开发的任务。完成后继续复用本轮
`review-work` 生成本地审查单。

**用户现在需要做的事：无。** 下一轮由 Agent 先整理固定输入、认证参考的待评维度和最薄
Harness 设计；只有出现认证参考无法裁决的新产品选择时，再请用户决定。

## 后续顺序

1. 方案形成：模糊诉求 → 合理需求理解与可审方案；
2. 开发执行：批准方案 → 代码、真实运行和变更说明；
3. 本地审查：复用本轮能力评需求、方案、实现和验证；
4. 知识回写：把批准后的代码与设计变化并入长期知识；
5. 换第二类任务或较弱模型，验证泛化后再扩大默认采用范围。
