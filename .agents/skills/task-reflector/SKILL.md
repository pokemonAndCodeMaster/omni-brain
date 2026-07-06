---
name: task-reflector
description: >
  Omni-Brain 任务反思与经验沉淀技能。在任务完成或失败后触发，从执行过程中提取有价值的
  经验、规范、避坑指南，并以 Experience / Norm / Pitfall 类型卡片形式沉淀到知识库。
  这是系统自进化的核心机制：让每次任务都产生可复用的价值。
  触发关键词：任务完成、出问题了、有个坑、总结一下、沉淀经验、这次学到了什么
metadata:
  author: omni-brain
  version: "1.0"
  platform: [codex, antigravity, opencode]
---

# 任务反思技能（task-reflector）

## 触发时机

- 开发任务完成后（成功或失败均可）
- 遇到意外错误或踩坑后
- 用户要求"总结一下"、"记录下来"

## 执行流程

### 第 1 步：提取反思内容

根据任务上下文，识别以下内容：

| 类别 | 判断标准 | 目标类型 |
|---|---|---|
| 踩坑/错误 | "没想到"、"花了很长时间"、反直觉的约束 | `Pitfall` |
| 可复用规范 | "下次应该先..."、强制性操作步骤 | `Norm` |
| 方法/模式 | 发现了更好的做法、解决问题的思路 | `Concept` / `Experience` |
| 偏好 | 发现了自己的喜好或习惯 | `Preference` |
| 背景事实 | 关于环境/项目/工具的新事实 | `Context` |

### 第 2 步：价值筛选

**不是所有东西都值得沉淀**。通过以下问题判断：
- 下次类似任务中，知道这个信息会节省 5 分钟以上吗？
- 这是第二次或以上遇到的问题吗？
- 对团队其他人（未来的多用户场景）有用吗？

若三个问题都是否 → 跳过，不创建卡片。

### 第 3 步：创建卡片

满足价值筛选的内容，通过 `knowledge-ingest` 技能创建卡片，特别注意：

对于 **Experience 类型**，必须包含：
```yaml
source:
  type: task_execution      # 或 conversation
  project: <项目名>
  date: <YYYY-MM-DD>
  outcome: success / failure / partial
```

对于 **Pitfall 类型**，必须包含：
- `affects_path`：在哪个路径/组件踩了坑
- 内联引用：具体的错误信息或配置

### 第 4 步：链接关联知识

将新卡片与已有相关卡片建立 `relations` 链接：
- 错误修复的 Pitfall → 链接到对应的 Norm（`supports` 关系）
- Experience → 链接到对应的 Concept（`exemplifies` 关系）

### 第 5 步：评估技能化潜力

如果这是**重复出现的模式**（第 2+ 次），考虑升级为技能：
- 提示用户：「这个操作模式出现了多次，是否创建一个 Skill？」
- 若是 → 触发 `skill-creator` 技能

## 输出示例

```
✅ 任务反思完成

沉淀内容（2 条）：
1. [Pitfall] FastAPI lifespan 不能用普通 async def → knowledge/pitfalls/fastapi_lifespan.md
2. [Norm] 异步数据库初始化必须在 lifespan 中 → knowledge/norms/async_db_init.md

跳过内容（1 条）：
- "uvicorn 启动命令" → 价值不足，已知常识
```
