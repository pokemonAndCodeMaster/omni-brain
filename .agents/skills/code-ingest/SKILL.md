---
name: code-ingest
description: >
  Omni-Brain 代码知识摄入技能。当用户要求"摄入这个项目的代码"、"把代码架构记录下来"时触发。
  提取代码骨架（函数签名/依赖关系），创建 CodeModule 类型卡片，不复制具体实现代码。
  核心原则：代码的实现细节留在文件系统，知识库只存架构骨架和关键决策。
  触发关键词：摄入代码、记录代码架构、代码地图、代码结构
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 代码摄入技能（code-ingest）

## 触发条件

- 用户要求摄入整个代码目录或项目
- 新项目初始化后建立代码地图
- 代码重构后更新架构知识

## 执行流程

### 第 1 步：骨架提取

**禁止直接大量阅读源码文件。**

```bash
python scripts/extract_code_skeleton.py <目标代码目录>
# 生成 .chunks/code_skeleton.md（只含函数签名、依赖、模块边界）
```

### 第 2 步：架构扫描（Map）

阅读骨架文件，在回复中输出《代码架构清单》：
```
📁 模块划分：
- 核心层：[模块1, 模块2]
- API 层：[模块3]
- 工具层：[模块4, 模块5]
- 数据层：[模块6]

关键依赖关系：
- 模块1 → 依赖 → 模块4, 模块6
- 模块3 → 依赖 → 模块1, 模块2
```

### 第 3 步：CodeModule 卡片建立（Reduce）

针对每个核心模块创建 `type: CodeModule` 的知识卡片。

**强制约束（索引隔离原则）**：
- ❌ 禁止在卡片中复制具体实现代码
- ✅ 卡片只包含三项：
  - **Why**：该模块的职责和设计意图（一句话）
  - **Who**：依赖关系（用 `relations` 字段和 Markdown 链接表达）
  - **Where**：`related_code` 字段指向实际源文件路径

```yaml
---
type: CodeModule
title: "搜索引擎模块"
description: "执行 BM25+图扩展的多路检索，是知识查询的核心执行层"
domain: [knowledge_mgmt, meta]
status: active
related_code: ["scripts/search_engine.py"]
code_hash: ""    # 由 compile_index.py 自动填充
relations:
  - target: "code/compile_index"
    type: depends_on
---
```

### 第 4 步：绑定代码哈希

```bash
python scripts/compile_index.py  # 自动计算并填充 code_hash
```

### 第 5 步：收尾

- 在 `knowledge/index.md` 的「代码模块」区注册新卡片
- 追加 `knowledge/log.md`
- 重编译索引

## 代码过期检测

当怀疑 CodeModule 卡片与实际代码不同步时：
```bash
python scripts/health_checker.py --code-only
# 对比 code_hash，标出已修改的文件
```
