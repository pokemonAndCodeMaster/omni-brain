---
type: Synthesis
title: "Omni-Brain Agent 评测方法论（v0.1）"
description: "以真实行为和 Outcome 为起点，用 Suite、Task、Trial、Grader 与 Transcript 证明 Agent 和知识组件能力。"
tags: [agent_evaluation, capability_eval, regression_eval, task_continuity]
timestamp: 2026-07-12T00:00:00+08:00
domain: [agent_engineering, knowledge_mgmt, software_engineering]
status: draft
source:
  type: documentation
  uri: "docs/research/agent-evaluation-reference-review.md"
relations:
  - target: "synthesis/omni_brain_product_direction_v0_1"
    type: supports
---

# Omni-Brain Agent 评测方法论（v0.1）

## 规范摘要

Omni-Brain 的评测从真实工作行为和可核验 Outcome 出发，而不是先建设批量模型 Runner。首要对象是：围绕能力族组织的 Suite、具有明确环境和成功标准的 Task、某模型与 Agent Harness 的一次 Trial、完整 Transcript、最终 Outcome，以及分别判断结果、知识状态、安全、行为质量和效率的 Grader。

确定性代码测试、契约检查、Agent Capability Eval、Agent Regression Eval 和真实能力切片验证回答不同问题，不能用其中一层代替另一层。Capability Eval 用于发现和爬坡；行为在代表任务中稳定后，才选择少量任务晋升 Regression Eval。

## 当前采用原则

- Task 来自真实旅程、失败、dogfood 或明确产品要求，并具备参考 Outcome、允许策略、正反例和干净环境；
- Outcome 与安全不变量优先，合理工具顺序差异通常只影响轨迹效率；
- 单次成功只是一条 Trial，报告必须标识模型、Agent Harness 和 Eval Harness；
- 优先使用确定性 Grader，开放质量使用分维度 rubric 并以人工样本校准；
- 正确性通过后再比较步骤、工具、token、延迟和人工负担；
- Runner、模型调用和沙箱按真实任务风险与重复成本渐进引入，不先预建通用平台；
- 外部项目的宣传指标只是待复现实验线索，不自动成为 Omni-Brain 证据。

## 当前项目落点

- 方法与生命周期：`docs/specs/evaluation-strategy.md`；
- 外部来源评审：`docs/research/agent-evaluation-reference-review.md`；
- 首个 Task：`eval/datasets/task_case/acceptance_exploration.yaml`；
- 冻结环境和参考响应：`eval/fixtures/task_case/acceptance_knowledge_prep_v1/`；
- 人工 Trial 与 Grader 校准：`eval/reports/task_case/`。

## 证据来源

- Anthropic, “Demystifying evals for AI agents”: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Anthropic, model-written evals repository: https://github.com/anthropics/evals
- LangChain, “How we build evals for Deep Agents”: https://www.langchain.com/blog/how-we-build-evals-for-deep-agents
- 组件实验与知识系统项目的适用边界见 `docs/research/agent-evaluation-reference-review.md`。

## 成熟度与待验证

本卡是 `draft`：上述方法已经指导首个 Task v2、fixture 和人工校准，但尚无自动 Runner、完整 Transcript、足量重复 Trial、模型 Judge 校准或跨能力 Suite。首个任务恢复切片的成功不能推广为整个评测系统已验证。

