---
name: task-knowledge-prep
description: >
  为目标模糊、关键知识缺失或冲突、跨业务—系统—代码、高风险难回滚或形成长期架构的任务准备知识。
  也用于用户明确要求先调研、补知或带着知识澄清需求再决策。维护可恢复账本、决策上下文和长期知识候选；
  不用于直接执行或单次有界查询。
---

# 任务知识准备

把会话作为语义执行器，把工作区作为可恢复**账本**。本 Skill 假定 AGENTS.md 已完成路由，且用户要继续推进一个 C 类任务；仅查看或恢复任务案状态时不要加载本 Skill。若加载后发现任务只需直接执行或有界查询，立即退出并交还路由；不要为展示流程创建任务案。

## 1. 打开账本

有明确 case ID 时直接用 `python scripts/task_case.py status <case-id>` 打开，不运行 `list` 或目录搜索；没有 ID 时才运行 `python scripts/task_case.py list`。确实没有相关任务时用 `python scripts/task_case.py create <title> --id <case-id>` 创建。脚本因环境依赖不可用时报告阻塞并进入人工基线，不自行安装依赖。

```text
workspaces/task-cases/<case-id>/
├─ case.yaml
├─ evidence.jsonl
├─ events.jsonl
├─ overview.md
├─ outputs/
│  ├─ decision-context.md
│  └─ readiness-report.md
└─ knowledge-proposals/
   └─ change-set.md
```

`case.yaml` 是当前状态；两个 JSONL 文件只追加证据和事件；`overview.md` 与 `outputs/` 是可重建视图；`knowledge-proposals/` 只存候选。使用 `event` 和 `evidence` 追加记录，不直接改写 JSONL。脚本不可用时安全编辑文件，并在事件中标记 `manual_baseline`。

完成标准：不依赖聊天历史即可说出目标、当前焦点、阻塞项、最近动作和下一允许动作。

## 2. 框定任务

在 `case.yaml` 维护触发信号、当前目标、待支持决策、范围/非目标、约束、假设和关键问题。允许决策暂时不明，但必须登记为阻塞项。新知识改变目标时递增 `frame_version`，使受影响问题和旧上下文失效。

每次语义修改后运行 `python scripts/task_case.py event <case-id> --type frame_updated --summary <摘要>`；不要让聊天记录成为唯一变更说明。

完成标准：每个可能改变方向的歧义都已成为关键问题、显式假设或非目标，当前范围足以开始查证。

## 3. 查证并补缺

对每个关键问题按 AGENTS.md 的事实源顺序定向查证：读取相关文档、代码、Schema、配置和运行事实，或请求人工确认；有适用的领域 Skill 时再调用。把查询范围、实际模式和动作写入事件，把来源、Claim 与冲突写入证据；召回不足时登记缺口类型，需要专家决定时使用 `human_confirmation`。

不得用模型常识填补关键事实。需要正式摄入时，先说明影响并取得用户授权，按项目的知识硬约束和安全变更协议执行；摄入工具不可用时保留候选与人工门禁，不得声称已经完成摄入。

回答关键问题时使用原子命令：

```bash
python scripts/task_case.py answer <case-id> <question-id> \
  --answer <简洁答案> --source <可追溯来源> \
  --kind <source|claim|human_confirmation> \
  --next-action <下一允许动作>
```

命令一次完成证据追加、答案和引用回写、事件登记、机械门禁重算与视图重建；多个下一动作可重复传入 `--next-action`，省略则保留原值。未知问题、已回答问题或无效输入必须停止且不改写账本。冲突仍先用 `evidence --kind conflict` 登记和解决，不得借 `answer` 抹去冲突。

完成标准：每个阻塞问题都有带来源答案、明确责任动作或可解释阻塞；“没搜到”没有被写成“知识不存在”。

## 4. 编织并过门禁

将 Claim 标成当前事实、历史事实、推断、目标设计或开放问题，并关联来源与适用范围。分别产出：

- 本次决策的任务投影；
- 长期知识候选及 `create / merge / update / task_only / discard` 建议、规范归属、关系和视图影响。

一次运行明细、查询片段和未验证推断默认留在账本，不批量建卡。

- `decision_ready`：待支持决策明确；阻塞问题已回答或风险被用户接受；关键 Claim 有当前适用证据；关键冲突已解决；上下文足以指导行动、验证和失败处理。
- `knowledge_handoff_ready`：稳定新增内容已分流；拟入库内容有来源、归属、关系和视图影响；提案可审查、可回滚。

运行 `python scripts/task_case.py check <case-id>` 更新机械门禁并重建视图。退出码 `2` 表示至少一个门禁未通过，是正常阻断，不是脚本故障。允许前者为真、后者为假：可以进入决策，但不能关闭任务案。机械通过不等于知识真实或充分，仍须逐项审查报告；脚本不可用时在报告中标记 `manual_gate`，不能声称系统已验证。

完成标准：关键 Claim 均可追溯；任务投影与长期候选没有混写；两个门禁逐项给出通过、失败或人工接受的证据。

## 5. 交接

通过决策门禁时生成 `decision-context.md`，包括任务框架、关键答案与来源、约束、冲突、已接受未知、纳入理由和下钻入口。暂停前更新账本、追加事件并运行 `python scripts/task_case.py render <case-id>`；只有两个门禁都通过，才能用 `python scripts/task_case.py close <case-id> --reason <原因>` 正常关闭。用户明确终止时使用 `--termination abandoned|superseded` 并记录理由。

完成标准：新会话或另一基础模型无需聊天历史即可恢复状态；用户知道当前结论、门禁状态、所需动作和下一产物。

## 护栏

- 会话不是状态源；重要进展必须进入账本。
- 强模型自行完成但未通过组件/记录约束的步骤只算人工基线。
- 不因知识不足自动扩大到全领域调研；只补充会改变行动、方案、验证、风险或结果解释的知识。
- 不在用户未授权时保存完整原始会话或把候选写入规范知识库。
- `decision_ready: false` 时只展示假设和待验证选项，不输出冒充最终结论的方案。
- 组件不可用时使用显式人工降级，不虚构脚本、索引、健康检查或摄入已经执行。
