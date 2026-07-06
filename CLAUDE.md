# CLAUDE.md — Omni-Brain Claude Code 操作指南

> 本文件由 platform-sync 从 AGENTS.md 生成，核心规则与 AGENTS.md 保持一致。
> Claude Code 专有配置在本文件末尾。

---

## 项目使命

**Omni-Brain** 是个人 AI 操作系统。统一知识库 + Agent Skills + 评测体系，持续进化。

核心原则：知识即文件 / 索引可重建 / 能力即技能 / 记忆即知识

---

## 仓库关键路径

- `knowledge/` — 统一知识库（OKF 兼容），含 taxonomy.yaml / index.md / log.md
- `knowledge/raw/` — 不可变原始资料区（**禁止修改**）
- `.agents/skills/` — Agent Skills 技能体系（跨平台可复用）
- `scripts/` — 核心脚本（compile_index / search_engine / ingest_pipeline）
- `config/system.yaml` — 全局配置
- `AGENTS.md` — 完整操作指南（本文件为精简版）

---

## 必须遵守的规则

1. **知识优先**：非平凡任务开始前必须先检索知识库
   ```bash
   python scripts/search_engine.py "<任务描述>"
   ```

2. **禁止修改 `knowledge/raw/`**

3. **卡片入库必须经过验证门禁**（触发 `knowledge-ingest` 技能）

4. **知识变更后必须重编译**
   ```bash
   python scripts/compile_index.py
   ```

5. **任务完成后触发 `task-reflector` 沉淀经验**

---

## 技能触发

Claude Code 支持 `.agents/skills/` 下的所有技能：

| 场景 | 触发技能 |
|---|---|
| 知识查询 | `knowledge-query` |
| 摄入资料 | `knowledge-ingest` |
| 知识体检 | `knowledge-health` |
| 代码摄入 | `code-ingest` |
| 任务反思 | `task-reflector` |
| 创建技能 | `skill-creator` |
| 运行评测 | `eval-runner` |

---

## 沟通约定

- 面向用户的回复优先使用**中文**
- 知识回答必须给出文件路径出处
- 回答不确定时，说明不确定，不要捏造事实
