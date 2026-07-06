# Omni-Brain

> 个人 AI 操作系统——以统一知识库为核心，将工作、学习、开发、生活的所有活动纳入认知闭环。

## 项目定位

Omni-Brain 不是一个笔记应用，而是一个持续进化的个人知识操作系统：

- **知识系统**：OKF 兼容的统一知识库，含经历记忆、偏好、背景事实
- **检索系统**：BM25 + 关系图的多路混合检索
- **能力系统**：Agent Skills 开放标准技能体系，跨 Codex / Antigravity IDE / OpenCode 可复用
- **评测系统**：持续回归测试，防止能力退化
- **自进化**：每次任务沉淀经验，每次发现模式固化为技能

## 快速开始

```bash
# 1. 创建 Conda 环境
conda env create -f environment.yml
conda activate omni-brain

# 2. 编译知识库索引（Phase 1 完成后可用）
python scripts/compile_index.py

# 3. 检索知识
python scripts/search_engine.py "你的查询"

# 4. 摄入新知识
python scripts/ingest_pipeline.py --file path/to/article.md
```

## 目录结构

```
omni-brain/
├── knowledge/          # 统一知识库（OKF 兼容）
│   ├── index.md        # 全局黄页
│   ├── log.md          # 操作时间线
│   ├── taxonomy.yaml   # 分类法定义
│   ├── raw/            # 不可变原始资料（禁止修改）
│   ├── concepts/       # 概念卡
│   ├── experiences/    # 经历记忆卡
│   ├── norms/          # 操作规范卡
│   ├── pitfalls/       # 避坑指南卡
│   └── ...             # 其他知识类型目录
├── .agents/skills/     # Agent Skills（Codex/Antigravity/OpenCode 共享）
├── scripts/            # 核心脚本（检索、摄入、健康检查）
├── eval/               # 评测系统
├── src/                # 开发代码区
├── config/             # 系统配置
├── AGENTS.md           # AI Agent 操作指南（主要入口）
└── environment.yml     # Conda 环境定义
```

## AI 工具接入

本项目支持以下 AI 开发工具，共享同一套技能和知识：

| 工具 | 入口文件 | 状态 |
|---|---|---|
| Codex | `AGENTS.md` | ✅ 已配置 |
| OpenCode | `AGENTS.md` | ✅ 已配置 |
| Antigravity IDE | `AGENTS.md` + `.agents/skills.json` | ✅ 已配置 |
| Claude Code | `CLAUDE.md`（由 platform-sync 生成）| 待生成 |

## 开发状态

- **Phase 0** ✅：项目骨架初始化
- **Phase 1** 🔲：知识存储 + 基础摄入流水线
- **Phase 2** 🔲：BM25 + 关系图检索引擎
- **Phase 3** 🔲：评测系统
- **Phase 4** 🔲：自进化（健康检查 + 技能创建）
