---
name: knowledge-query
description: >
  Omni-Brain 知识库智能检索技能。当用户提出知识性问题、开发任务开始前需要查阅历史经验、
  或需要查找项目规范和避坑指南时触发。执行「意图路由→BM25检索→关系图扩展→重排→分级输出」
  流水线，返回结构化的知识上下文，供后续任务使用。
  触发关键词：查一下、有没有相关的、历史上有没有、之前怎么做的、有什么规范
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 知识检索技能（knowledge-query）

## 触发条件

- 用户提出知识性问题（"X 是怎么做的？""有什么规范？"）
- 开发任务开始前的强制知识检索（所有非平凡任务）
- 用户明确要求"查一下知识库"、"有没有相关的记录"

## 前置检查

1. 确认 `.derived/fts.db` 存在
   - 不存在 → 先运行 `python scripts/compile_index.py`
   - 存在但知识库刚更新 → 也运行重编译

## 执行流程

```bash
# 基础检索
python scripts/search_engine.py "<查询描述>"

# 指定域过滤（推荐，可提高精度）
python scripts/search_engine.py "<查询描述>" --domain backend_dev,software_engineering

# 指定类型过滤
python scripts/search_engine.py "<查询描述>" --type Norm,Pitfall,Concept

# 组合过滤
python scripts/search_engine.py "<查询描述>" --domain agent_engineering --type Concept,Synthesis
```

## 结果处理

按脚本返回的优先级处理：

1. **full_read 列表**：全文读取，提取关键信息（特别是 Norm/Pitfall 类型）
2. **summary_only 列表**：只使用 `description` 字段，不读全文
3. **title_only 列表**：仅列出标题，供用户按需下钻

## 输出格式

```
📋 领域知识：[Concept/Synthesis 卡片要点，含文件路径]
⚠️  避坑护栏：[Pitfall 卡片全文要点，必须全部列出]
📐 操作规范：[Norm 卡片全文要点，必须全部列出]
🔗 代码关联：[CodeModule 卡片 + 关键函数/路径]
📄 参考来源：[Source 卡片标题列表]
🌟 相关经历：[Experience 卡片要点]
```

## 硬规则

- **若检索到 Norm 或 Pitfall，必须在输出末尾强制标出**：
  `> ⚠️ 架构护栏：[具体约束描述]`
- 若召回不足（< 3 个相关卡片），说明知识缺口，建议补充摄入
- 不要凭记忆给出没有出处的事实，必须来自知识库

## 知识缺口处理

召回不足时输出：
```
📭 知识缺口：未找到关于「X」的足够信息。
建议：通过 knowledge-ingest 技能摄入相关资料，或手动创建卡片。
```
