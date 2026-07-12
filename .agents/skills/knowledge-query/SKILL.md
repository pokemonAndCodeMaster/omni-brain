---
name: knowledge-query
description: >
  有边界地查询 Omni-Brain 已有知识。用于回答明确的知识问题、为范围清楚的任务补少量规范或历史背景，
  或供 task-knowledge-prep 盘点存量知识。不用于管理任务状态、补知、摄入或判断决策准备度。
---

# 有界知识查询

保持**有界**：只查可能改变当前答案或下一动作的知识，并返回来源与缺口。由父 Skill 调用时只返回结果，不自行维护任务状态。

## 1. 定界

写下一项主问题，以及领域/项目、事实时间或状态、所需深度和停止条件。若无法形成单一主问题，返回 `scope_ambiguous`，不要用宽泛查询掩盖目标不清。

完成标准：能说明“要回答什么、在哪个范围回答、读到什么程度停止”。

## 2. 查询

按 AGENTS.md 的事实源顺序选择入口。先确认工具的真实能力；不可用时使用 `rg`、`rg --files` 和直接读取，并记录 `manual_fallback`。全文读取所有高相关结果及适用的 Norm/Pitfall；不要把摘要当作精确当前事实。

完成标准：实际查询方式已记录；所有高相关命中已按其允许深度处理；每项答案都能回到具体来源。

## 3. 收束

输出以下结构；自然语言回答也不得省略来源、查询模式、缺口和限制。

```yaml
question: "..."
scope: "..."
mode: tool | manual_fallback
answers:
  - claim: "..."
    source: "path-or-uri"
    reality: as_is | to_be | historical | unknown
gaps:
  - type: not_retrieved | not_codified | missing_source | stale | conflicted | access_blocked | scope_ambiguous
    detail: "..."
limitations: []
next: answer | refine_scope | broaden_sources | escalate | ask_human
```

查询没有命中时只报告缺口，不能推断知识不存在；不要自动摄入、建卡或创建任务工作区。若命中适用的 Norm/Pitfall，在末尾列出架构护栏。

完成标准：主问题得到带来源的回答，或每个关键未回答项都有明确缺口类型和下一动作；本 Skill 未产生任何知识或任务状态变更。
