---
name: skill-creator
description: >
  Omni-Brain 技能自动创建技能。当发现重复出现（2次以上）的操作模式时触发，
  将重复操作固化为新的 Agent Skill。这是系统技能体系自进化的核心机制。
  触发关键词：每次都要、重复操作、能不能做成技能、固化一下这个流程
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 技能创建技能（skill-creator）

## 触发条件

- 同一操作模式出现 2 次以上
- 用户要求"把这个做成技能"
- `task-reflector` 判断某模式值得技能化

## 执行流程

### 第 1 步：模式提炼

明确回答以下问题：
- 这个技能做什么？（一句话）
- 什么时候触发？（触发关键词和场景）
- 步骤是什么？（可执行的操作序列）
- 成功标准是什么？

### 第 2 步：生成 SKILL.md

在 `.agents/skills/<skill-name>/` 下创建 `SKILL.md`，格式：
```yaml
---
name: <skill-name>              # 小写 + 连字符，≤64字符
description: >
  [一段话描述：做什么 + 何时触发 + 触发关键词]
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# [技能名称]

## 触发条件
## 执行流程
## 成功标准
```

### 第 3 步：注册到 skills.json

```json
// .agents/skills.json 中添加新条目：
{
  "entries": [
    { "path": ".agents/skills/<skill-name>" }
  ]
}
```

### 第 4 步：创建评测用例

在 `eval/datasets/skill_execution/` 添加技能评测用例。

### 第 5 步：验证

触发新技能，确认它按预期工作。
