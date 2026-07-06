# AGENTS.md — Omni-Brain 项目级 Agent 操作指南

本文件是 Codex / OpenCode / Antigravity IDE 进入本仓库后默认加载的操作指南。
**请保持精简可执行**——详细工作流放在 `.agents/skills/`，知识放在 `knowledge/`。

---

## 项目使命

**Omni-Brain** 是个人 AI 操作系统。以统一知识库为核心，将工作、学习、开发、
生活的所有活动纳入认知闭环。目标：每次交互都产生可沉淀的价值，让系统持续变聪明。

核心理念：
- 知识即文件（OKF 兼容 Markdown + YAML Frontmatter）
- 索引可重建（BM25/图均为派生产物，可从知识文件重建）
- 能力即技能（Agent Skills 开放标准，跨平台可复用）
- 记忆即知识（经历直接形成 Experience / Preference / Context 类型卡片）

---

## 仓库地图

```
omni-brain/
├── knowledge/          # 统一知识库（含知识、经历记忆、偏好、背景）
│   ├── index.md        # 全局黄页（所有查询的起点）
│   ├── log.md          # 操作时间线（append-only）
│   ├── taxonomy.yaml   # 知识分类法（type/domain/relation 权威来源）
│   ├── raw/            # 不可变原始资料区（禁止修改）
│   ├── concepts/       # 概念卡
│   ├── sources/        # 来源摘要卡
│   ├── entities/       # 实体卡
│   ├── synthesis/      # 综合分析卡
│   ├── norms/          # 操作规范卡
│   ├── pitfalls/       # 避坑指南卡
│   ├── playbooks/      # 操作手册卡
│   ├── code/           # 代码模块卡
│   ├── experiences/    # 经历记忆卡（来自任务/对话）
│   └── context/        # 背景事实卡（关于我/环境/项目）
├── .agents/skills/     # Agent Skills（Codex/OpenCode/Antigravity 均可读）
├── scripts/            # 核心 Python 脚本（检索、摄入、健康检查等）
├── eval/               # 评测系统
├── src/                # 开发代码区（业务项目在此）
└── config/             # 系统配置
```

---

## 沟通约定

- 面向用户的回复优先使用**中文**
- 回答知识库事实时必须给出具体文件路径，不要把无出处的推测包装成事实
- 需求不清时先讨论目标、约束和成功标准；小而安全的改动可先假设并明示
- 保持简洁，不省略关键取舍、风险和验证证据

---

## 知识优先原则

**任何非平凡的设计、实现、排障、重构开始前，必须先做知识检索。**

### 检索流程

1. 确认 `.derived/fts.db` 存在（不存在则运行 `python scripts/compile_index.py`）
2. 运行 `python scripts/search_engine.py "<任务描述>"` 启动多路检索
3. 可选过滤：`--domain backend_dev,software_engineering` 或 `--type Norm,Pitfall`
4. 按输出的优先级读取：`full_read` 全文 → `summary_only` 仅摘要 → `title_only` 仅标题
5. 如检索不足，说明知识缺口，并建议补充摄入

### 使用技能（推荐方式）

触发 `knowledge-query` 技能，它封装了上述完整流程，并提供结构化输出。

---

## 知识维护规则（根级硬规则）

- **禁止修改 `knowledge/raw/` 中的任何文件**
- 所有 `knowledge/` 下的卡片必须包含 OKF 兼容的 YAML Frontmatter
- `type` 和 `domain` 必须取自 `knowledge/taxonomy.yaml` 的枚举值
- 新建卡片后必须在 `knowledge/index.md` 对应分类下注册一行
- 知识变更后必须追加 `knowledge/log.md` 记录
- `Norm` 和 `Pitfall` 类型卡片必须填写 `affects_path` 字段
- `CodeModule` 类型卡片必须填写 `related_code` 和 `code_hash` 字段
- 卡片中的关键参数/API/配置必须用 `> 📌 引自原文：` 内联引用锚定

### 完整摄入规则

触发 `knowledge-ingest` 技能。核心约束：
1. 新知识不直接覆盖旧知识，变更经验证门禁和冲突检测后入库
2. 摄入结束后重新编译索引：`python scripts/compile_index.py`

---

## 开发工作流

### 路线 A：纯知识查询

触发：用户询问知识、架构、规范、历史经验，不要求代码修改。

→ 触发 `knowledge-query` 技能 → 返回带文件路径出处的答案

### 路线 B：标准开发 / 排障

触发：新增功能、改代码、重构、修复报错、架构调整。

1. **知识检索**：执行知识优先检索流程
2. **方案确认**：复杂/高风险任务先给方案摘要，等用户确认；小任务说明假设后直接做
3. **实现**：外科手术式修改，避免无关重构
4. **验证**：优先验证端到端路径，必要时补单测
5. **经验沉淀**：触发 `task-reflector` 技能，将新规范/坑点/决策沉淀为 Experience 卡片

### 路线 C：知识摄入 / 更新

触发：用户要求"加入知识库"、"整理资料"、"沉淀经验"。

→ 触发 `knowledge-ingest` 技能（含验证门禁，确保信息无损）

### 路线 D：知识健康检查

触发：用户要求"体检"、"检查知识库"。

→ 触发 `knowledge-health` 技能 → 输出报告，不执行删改，等待人工审批

---

## 技能使用

所有技能在 `.agents/skills/` 下，符合 Agent Skills 开放标准（Codex / OpenCode / Antigravity IDE 均支持）。

主要技能：
- `knowledge-query`：知识检索（最常用，每次任务开始前触发）
- `knowledge-ingest`：知识摄入（含验证门禁）
- `knowledge-health`：知识健康检查
- `code-ingest`：代码知识摄入
- `task-reflector`：任务反思与经验沉淀
- `skill-creator`：识别重复模式并创建新技能
- `eval-runner`：运行评测集

---

## 验证标准

- 完成声明必须有新鲜验证证据
- 行为改动优先验证端到端用户路径
- 知识回答必须有文件路径出处
- 摄入完成后必须重编译索引并验证新卡片可被检索到

---

## 质量标准

- 知识卡片：极致精简、有具体证据、有双向关系、不造假
- 代码变更：聚焦且可验证，外科手术式修改
- 重复错误和反馈应沉淀为 `Norm`、`Pitfall` 或 `Experience` 卡片
- 不要为了流程好看而执行无意义的仪式步骤

---

## 安全编辑

- 广泛编辑前查看 `git status --short`
- 保留用户已有改动，不要回滚无关文件
- 搜索优先使用 `rg`（ripgrep）
- 禁止修改 `knowledge/raw/` 目录
