---
name: knowledge-ingest
description: >
  Omni-Brain 知识高保真摄入技能。当用户要求"加入知识库"、"整理资料"、"沉淀经验"、
  "摄入这篇文章/对话"时触发。执行「保存原料→分块→草案→验证门禁→冲突检测→入库→重编译」
  流水线，确保信息完整无损地融入知识体系。
  触发关键词：加入知识库、整理一下、记录下来、沉淀、摄入、归档
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 知识摄入技能（knowledge-ingest）

## 触发条件

- 用户要求"把这个加入知识库"、"整理这篇资料"
- 任务完成后需要沉淀 Experience/Norm/Pitfall
- 有新的学习资料、文档或代码需要摄入

## 摄入流水线

### 第 0 步：保存原料

```bash
# 将原始资料保存到 raw/（只读区，之后禁止修改）
# 根据来源类型选择目录：
#   raw/articles/     - 文章、文档
#   raw/conversations/ - 对话记录
#   raw/assets/       - 图片、PDF 等附件
```

### 第 1 步：分块扫描（Map）

若资料较长（>1000 字），运行分块：
```bash
python scripts/chunk.py <raw文件路径>
# 在同目录生成 .chunks/ 文件夹，逐个读取分块
```

**不要立即建卡。** 先输出《高保真摄入清单》：
```
📋 摄入清单：
- 新概念：[X]（位置：第Y节）
- 规范约束：[A]（位置：第Z段）
- 避坑要点：[B]（包含具体参数/配置）
- 代码结构：[C]
- 来源信息：[URL/标题/作者/日期]
```

### 第 2 步：草案生成（Reduce）

按清单逐条建卡草案，遵循写卡原则：
- **具体 > 通用**：拒绝模棱两可的概括
- **证据驱动**：关键参数/API/配置必须内联引用原文
- **Token 意识**：极致精简，消除客套话

**强制约束（信息无损）**：
写 `Norm`、`Pitfall`、`CodeModule` 时，涉及具体参数/API/代码，
**必须**使用内联引用：
```markdown
> 📌 引自 raw/articles/xxx.md#第2节:
> "具体的原文内容，一字不改"
```

### 第 3 步：验证门禁（Verification Gate）

对照清单检查草案，逐条确认：
- [ ] 清单中的每个知识点在卡片中都体现了吗？
- [ ] 卡片中的表述有没有扭曲原文意思？
- [ ] 关键数字/参数/API 名称是否准确？
- [ ] 是否使用了内联引用锚定证据？

**若检查未通过 → 打回草案，说明缺失点，重新生成。**

### 第 4 步：冲突与重复检测

```bash
python scripts/search_engine.py "<新卡片标题/核心主题>"
```

比对结果：
- **重复度高** → 合并到现有卡片，或标注更新
- **内容冲突** → 标记冲突，生成冲突提案，等待人工确认
- **时效性问题** → 标记旧卡为 `status: stale`

### 第 5 步：人工审核确认

- 低风险（纯新增、无冲突）→ 直接进入入库
- 存在冲突或覆盖旧内容 → **必须人工确认**

### 第 6 步：入库与收尾

```bash
# 1. 写入卡片文件（按 taxonomy.yaml 选择正确目录）
# 2. 在 knowledge/index.md 对应分类下注册
# 3. 在 knowledge/log.md 追加操作记录
# 4. 重编译索引（必须！）
python scripts/compile_index.py
```

**验证入库成功**：
```bash
python scripts/search_engine.py "<新卡片标题>"
# 确认新卡片出现在检索结果中
```

## Frontmatter 模板

```yaml
---
type: Concept                        # 取自 taxonomy.yaml types
title: "卡片完整标题"
description: "一句话概括，用于索引和预览"
tags: [标签1, 标签2]
timestamp: YYYY-MM-DDTHH:MM:SS
domain: [backend_dev]                # 取自 taxonomy.yaml domains，列表
status: active                       # active | draft | stale | superseded
confidence: 0.9                      # 可信度 0-1（可选）
source:
  type: article                      # 取自 taxonomy.yaml source_types
  uri: "raw/articles/xxx.md"         # 原始资料路径（可选）
relations:
  - target: "concepts/related_concept"
    type: supports                   # 取自 taxonomy.yaml relation_types
affects_path: []                     # Norm/Pitfall 必须填写
related_code: []                     # CodeModule 必须填写
---
```

## 特殊类型约束

| 类型 | 额外必填 |
|---|---|
| `Norm` | `affects_path`（约束哪些路径）|
| `Pitfall` | `affects_path`（在哪里踩了坑）|
| `CodeModule` | `related_code`（关联代码路径）、`code_hash` |
| `Experience` | `source.type: task_execution / conversation` |
