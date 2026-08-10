# Omni-Brain Agent Harness

这不是一个独立 AI 运行平台，而是一套放进项目根目录后由 **Codex 或 OpenCode 原生会话直接使用**的项目能力包。AI 会话负责理解、判断、写作和开发；本仓库提供任务路由、专项 Skill、确定性脚本、状态工作区、知识结构和回归测试。

稳定 Release 身份仍记录在 [`harness.yaml`](harness.yaml)；当前实验分支还包含经过限定工况验证的查询、开发和代码知识回写能力。具体采用范围也以该文件为准。

## 实际包含哪些实体

```text
AGENTS.md                              AI 进入项目后首先读取的任务路由与安全边界
harness.yaml                           各能力入口、依赖、成熟度和限制

.agents/skills/
├─ answer-from-knowledge/SKILL.md      从正式知识回答问题
│  └─ scripts/knowledge_route.py       只读知识入口排序器
├─ develop-with-knowledge/SKILL.md     带知识完成真实软件修改与验证
├─ ingest-knowledge/SKILL.md           完整整理、聚焦整理和代码变化回写
│  └─ assets/*.md                      知识页、产品视图、软件架构等写作骨架
└─ task-knowledge-prep/SKILL.md        模糊或高风险任务的知识准备

scripts/
├─ ingestion_workspace.py             可恢复知识摄入/回写工作台
├─ knowledge_check.py                  OKF/Markdown 知识结构只读检查
├─ source_run.py                       固定本地 Git 来源版本、范围和内容指纹
└─ task_case.py                        可恢复任务案、证据、事件和双准备度检查

knowledge/                             空的规范知识与产品视图入口
config/knowledge-domains.yaml          显式领域层级地图
tests/                                 组件、路由、工作台和知识结构回归
```

`.agents/skills/*/agents/openai.yaml` 只提供 Skill 的显示名称和默认提示元数据；真正的工作流定义在对应 `SKILL.md`。

## 各组件实际做什么

### 1. `AGENTS.md`：任务路由器

[`AGENTS.md`](AGENTS.md) 不生产知识或代码。它让宿主模型先判断请求类型，然后只加载最低充分能力：

| 用户请求 | 实际路由 |
|---|---|
| “整理/摄入/归并这些材料” | `ingest-knowledge` |
| “根据现有知识回答、学习、判断缺口” | `answer-from-knowledge` |
| “开发、修复、重构并真实验证” | `develop-with-knowledge` |
| “恢复某个任务案” | 直接读取任务案状态；需要继续复杂准备时再加载 `task-knowledge-prep` |
| 明确、局部、低风险任务 | 不加载完整 Skill，直接执行 |

它还强制候选隔离、来源只读、最低充分阅读、真实路径验证和人工发布边界。OpenCode 与 Codex 都复用这个根文件，不需要单独适配器。

### 2. `answer-from-knowledge`：可信知识问答

入口：[`SKILL.md`](.agents/skills/answer-from-knowledge/SKILL.md) 和 [`knowledge_route.py`](.agents/skills/answer-from-knowledge/scripts/knowledge_route.py)。

实际过程：

1. 用原始问题调用路由器；
2. 路由器只遍历 `knowledge/index.md` 和受维护导航可达的 Markdown，按标题、链接上下文、正文词项和问题意图排序；
3. 模型先读一个 `PRIMARY`，明确有未答子问题时才读候补，单题最多三篇规范页；
4. 输出直接答案，并区分已确认、历史、目标设计、冲突和未知；
5. 只有用户要求当前代码、Schema 或运行结果时，才沿知识登记的直接入口继续核验。

普通问答**不创建工作区、不修改知识、不读取原料**。路由器不是向量库或问答模型，只负责把阅读范围从“翻全库”收束到少数候选。

可直接观察路由结果：

```bash
python .agents/skills/answer-from-knowledge/scripts/knowledge_route.py \
  --root knowledge/index.md \
  --query '我的问题' \
  --format json
```

### 3. `develop-with-knowledge`：带知识开发

入口：[`SKILL.md`](.agents/skills/develop-with-knowledge/SKILL.md)，并复用 `knowledge_route.py`。

它没有再造一套开发 CLI，而是约束 Codex/OpenCode 原生开发会话完成以下动作：

1. 编辑前公开用户结果、知识入口、现有责任链、最大合法组合、副作用基线和真实验证计划；
2. 最多读取三篇会改变实现的规范知识，再用当前源码、Schema、配置和运行结果裁决精确行为；
3. 沿真实用户动作定位最小修改链，优先复用现有能力；
4. 对可增长集合验证“最大合法组合通过、再多一项失败”；
5. 在真实 API、CLI、数据库或页面验证正常和关键边界；写数据时额外验证基线、冲突状态、失败阻断、幂等和恢复；
6. 最终交付真实代码、运行证据、未验证边界和知识变化候选。

实际产物首先是**用户要求的代码/SQL/配置和真实运行结果**。知识变化候选默认只写在交付说明中；只有用户要求正式回写时，才进入下面的 `writeback` 工作台。

该 Skill 已在同一人工质检系统的页面、SQL 性能、跨层算法和详情交互四类真实开发中取得证据，并覆盖两种宿主/模型组合。最新详情对照在相同模型与任务下补齐了焦点进入、Tab/Shift+Tab 环绕、关闭恢复和逐项证据声明；这些规则没有写入题目公式、固定数字或页面名称。当前结论仍不能外推到第二领域或任意软件项目。

### 4. `ingest-knowledge`：知识摄入和代码变化回写

入口：[`SKILL.md`](.agents/skills/ingest-knowledge/SKILL.md)；确定性状态工具是 [`ingestion_workspace.py`](scripts/ingestion_workspace.py)。

它有三种模式：

| 模式 | 适用输入 | 核心动作 |
|---|---|---|
| `complete` | 一批混乱、重复、冲突或结构不一的材料 | 建材料地图，逐个审阅材料单元，登记带定位发现，规划长期知识主题，生成规范知识和产品视图 |
| `focused` | 一个明确问题或一段代码 | 形成读者问题，只取最低充分小批来源，需要时隔离运行，再形成对应知识 |
| `writeback` | 固定代码版本相对已有知识的变化 | 判断同系统/新系统，分析业务、软件、兼容、公共能力、证据和导航影响，原位更新父知识候选 |

每次执行创建一个隔离工作区：

```text
workspaces/knowledge-ingestion/<case-id>/
├─ draft/knowledge/                   用户实际审查的候选规范知识与产品视图
├─ draft/config/knowledge-domains.yaml 候选领域地图
├─ review.md                          唯一人工审查入口
├─ evidence/runs/<run-id>/            隔离运行的命令、stdout、stderr、artifact 和 run.json
└─ .state/
   ├─ case.json                       当前问题、计划、阶段、来源包和下一动作
   └─ source-manifest.jsonl           来源文件身份与范围
```

工作台能做的确定性动作包括：创建摄入案、固定系统身份、输出下一小批来源、登记发现、规划知识落点、检查变化影响、冻结 Python 字段契约、在临时 Git worktree 中运行来源项目、检查单元完整性、恢复状态和重建 `review.md`。

它**不会**判断业务结论真假、替模型写知识或自动发布。结构达到 `publish_ready` 只表示可以交给人审查。

查看完整命令：

```bash
python scripts/ingestion_workspace.py --help
```

### 5. `knowledge_check.py`：知识结构检查器

入口：[`knowledge_check.py`](scripts/knowledge_check.py)。它只读检查：

- OKF `type` 及推荐 frontmatter；
- `knowledge/index.md`、显式领域地图和镜像目录；
- 标准 Markdown 相对链接、标题锚点和断链；
- 禁止 Obsidian wiki link、`file://` 和越界链接；
- 规范标题唯一性、正文与产品视图的可达性；
- 发布知识是否同时具有领域视图、旅程视图、`# Citations` 和来源记录；
- Markdown 表格基本结构和重复产品视图正文。

```bash
python scripts/knowledge_check.py
```

通过只代表结构和声明关系成立，不能证明内容正确或充分。

### 6. `task-knowledge-prep` + `task_case.py`：复杂任务知识准备

入口：[`SKILL.md`](.agents/skills/task-knowledge-prep/SKILL.md) 和 [`task_case.py`](scripts/task_case.py)。

只用于目标模糊、知识缺失/冲突、高风险或形成长期架构的任务。它把聊天中的目标、关键问题、证据、事件、阻塞和下一动作写成可跨会话恢复的账本：

```text
workspaces/task-cases/<case-id>/
├─ case.yaml
├─ evidence.jsonl
├─ events.jsonl
├─ overview.md
├─ outputs/readiness-report.md
├─ outputs/decision-context.md
└─ knowledge-proposals/change-set.md
```

脚本支持创建、恢复、追加事件/证据、原子回答关键问题、重算决策准备度和知识交接准备度、重建视图及关闭任务案。机械检查只检查显式状态和引用，不评价方案质量。

### 7. `source_run.py`：本地 Git 来源快照

入口：[`source_run.py`](scripts/source_run.py)。它挂在任务案下，对用户明确授权的本地 Git 路径执行：

- 登记仓库根、权威级别和 include 范围；
- 记录 Git HEAD、文件状态、内容 SHA-256 和范围指纹；
- 比较本次与上次是 initial、unchanged、changed 还是 partial；
- 原子发布 `run.yaml`、`manifest.jsonl` 和必要文件快照；
- 校验运行信封与 manifest 未被破坏。

它只回答“指定来源版本和范围发生了什么变化”，不解释变化的业务含义，也不会自动触发知识摄入。

### 8. 空知识骨架、模板和测试

- [`knowledge/index.md`](knowledge/index.md) 及其 `domains/`、`systems/`、`capabilities/`、`sources/`、`views/` 入口，是空 Harness 的知识落点；本体不预装质检答案。
- [`config/knowledge-domains.yaml`](config/knowledge-domains.yaml) 保存明确领域层级；目录约定与 OKF frontmatter 兼容，但不是把领域分类伪装成 OKF 标准。
- [`assets/`](.agents/skills/ingest-knowledge/assets/) 提供领域总览、知识页、软件架构、来源记录、产品视图和公共能力审查骨架，模型按内容选择，不机械复制所有章节。
- [`tests/`](tests/) 固定任务路由、Skill 契约、工作台状态、查询路由、来源信封和知识检查器行为。

## 用户实际怎样使用

通常不需要手工执行上述脚本。在项目根启动 Codex 或 OpenCode，直接给自然语言任务：

```text
请把 <材料路径> 中与 <主题> 有关的杂乱材料整理进知识库，供我学习和后续开发。
```

```text
根据现有知识告诉我 <问题>，明确哪些已确认、哪些未知或冲突。
```

```text
实现 <软件需求>，使用现有领域知识和真实项目环境验证，并说明知识需要怎样更新。
```

```text
把 <仓库@commit> 的代码变化原位回写到现有知识，先生成隔离候选，不要发布。
```

`AGENTS.md` 负责选 Skill，Skill 指导模型，脚本只承担范围、状态、隔离、检查和证据等必须确定的部分。

## 当前明确没有什么

- 没有额外 Agent 服务、后台进程或模型 API 调用层；
- 没有全文搜索、向量数据库、知识图谱查询或 Web UI；
- 没有自动判断知识真伪或无人审批发布；
- 没有通用环境安装与数据库沙箱；
- 没有证明跨领域、任意模型或任意规模都能达到当前质检切片效果。

## 安装与自检

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests
python scripts/knowledge_check.py
```

能力入口、依赖、成熟度和限制见 [`harness.yaml`](harness.yaml)，当前采用状态见 [`docs/now.md`](docs/now.md)。
