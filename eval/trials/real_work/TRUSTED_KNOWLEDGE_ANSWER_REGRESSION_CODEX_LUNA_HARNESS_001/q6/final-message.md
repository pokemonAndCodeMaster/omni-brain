结论：现有知识不能裁决分母。当前唯一可实现且不误导的方案，是把公式显式标注，暂不把任一口径冒充生产规则。

- 已完成验收口径：
  `通过率 = 已完成验收样本中的通过数 / 已完成验收数`
  回答的是“已经形成验收判断的样本，质量表现如何”。未完成样本不被算作失败。

- 已分配验收口径：
  `通过率 = 通过数 / 已分配验收数`
  回答的是“已经派发出去的验收任务，整体推进和通过表现如何”。未完成分配会压低结果，因此混合了质量与完成进度。

冲突边界在于存在“已分配但未完成”的样本：前者排除它们，后者把它们留在分母中。两者都可以有业务意义，但不能用一个名称“质量通过率”同时代表，也不能把历史阈值或目标设计中的公式当作当前生产规则。

实现前最小裁决：

- 裁决人：业务负责人，最好由验收规则实际 owner 确认。
- 最小直接证据：一条当前生效的业务决定，明确分子、分母、未完成样本处理、样本范围和零分母行为；同时用当前生产快照/Schema 确认字段映射，例如 `acceptance_completed`、分配数和通过数。

当前知识明确记录了两套冲突定义，但没有当前生产批准记录或生产 Schema，因此不能自行选边：

- [未知与冲突](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/open-questions.md>)
- [验收总览](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/overview.md>)
- [人工语义决定来源](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/sources/human-decisions.md)
