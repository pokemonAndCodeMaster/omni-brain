---
name: ingest-knowledge
description: >
  摄入一批有界的文档、代码、Schema 或人工材料，把它们整理为可浏览、可追溯、可继续工作的规范知识与产品视图。
  当用户要求整理、导入、摄入或归并材料，或用新材料更新现有知识时使用；同时支持宽范围完整整理与聚焦代码/问题整理。
  不用于只回答一个问题、直接改代码或无来源创作。
---

# 知识摄入

把授权材料转化为**规范知识、产品视图和一份 `review.md`**。来源始终只读；候选只写入
`workspaces/knowledge-ingestion/<case-id>/draft/`。用户批准前不得修改正式 `knowledge/` 或 `config/`。

机器状态只保存在 `.state/case.json` 和 `.state/source-manifest.jsonl`。使用工作台命令读写状态，不手工编辑这两个文件，也不把它们交给用户维护。

## 1. 选择最低充分模式

- **宽范围完整整理（`complete`）**：用户交来一个领域、模块或混合材料包，希望从零建立可学习的全貌与细节。先审视材料地图和读后发现，再规划知识目录。不要在读材料前猜主题或现实身份。
- **聚焦整理（`focused`）**：用户已限定一个代码动作、接口、指标、脚本或具体问题。直接按读者问题定向取源，保留真实运行能力，不要求先审视整个领域材料地图。

这是同一个 Skill、同一规范知识底座的轻重路由。范围已经清楚时直接选择，不向用户询问内部模式名称。

## 2. 宽范围完整整理

### 2.1 固定用户承诺与材料范围

从请求中提取目标读者、读完后应具备的理解或行动能力、授权来源和不能做错的边界。启动时不预先编造读者问题或知识目录：

```bash
python scripts/ingestion_workspace.py start <case-id> \
  --mode complete \
  --goal '<读者最终能够理解、判断或执行什么>' \
  --reader '<目标读者>' \
  --source <source-id>=<authorized-directory> \
  [--source <next-source-id>=<authorized-directory>] \
  [--boundary '<不能做错的边界>']
```

继续已有摄入案时先运行：

```bash
python scripts/ingestion_workspace.py status <case-id>
```

状态首页只看当前阶段、当前材料组或知识主题、已形成数量和下一动作。

### 2.2 审视材料地图并形成读后发现

工作台只用路径、完全重复、文档链接和代码导入建立材料地图。独立叙述文档各自形成审视单元；文档链接保留关联但不把多份长文合成一次阅读任务。代码、配置、迁移和测试继续按共同路径形成小型实现单元。工作台不根据标题判断当前、历史或目标。先查看整体地图：

```bash
python scripts/ingestion_workspace.py survey <case-id>
python scripts/ingestion_workspace.py next <case-id>
```

`next` 始终返回同一个当前审视单元，直到本单元完成登记；重复调用不会丢状态或切换任务。按以下顺序处理：

1. 用成员路径、标题和章节概要判断本组与用户目标的关系；
2. 相关时，完整读取会改变结论的成员；完全重复组只完整读取一个代表文件并确认重复位置；
3. 一项发现只表达一个可独立复用的结论；同一来源包含多个业务机制、数据变化、算法步骤、类/函数、职责或异常时，拆成多项发现；
4. 每项发现保存决定理解或行动的关键细节，并定位到来源中的章节、表、代码符号或配置键；
5. 只用直接材料说明现实形态、适用范围和限制，不用文件名或模型常识补全。

每项读后发现使用稳定 ID：

```bash
python scripts/ingestion_workspace.py finding-add <case-id> <finding-id> \
  --group-id <group-id> \
  --content '<一个可独立复用的核心结论>' \
  --detail '<不可在合并时丢失的机制、字段、步骤、类函数、责任或异常>' \
  [--detail '<另一项关键细节>'] \
  --reality <current_implementation|current_decision|target_design|historical|conflict|unknown> \
  --source '<source-id>:<path>' \
  --anchor '<章节、表、符号或配置键>' \
  --scope '<结论适用于什么范围>' \
  [--limit '<不能据此推出什么>'] \
  [--topic '<可能进入的长期知识主题>']
```

同一组可以重复执行 `finding-add`；同一 ID、同一内容的重试是幂等的。随后登记整组：

单一来源时 `--anchor` 只写章节或符号，工作台会和已经校验的 `--source` 组合；一项发现有多个来源时，分别使用 `--anchor '<source-id>:<path>#<定位>'`，避免定位归错文件。

```bash
python scripts/ingestion_workspace.py record-material <case-id> <group-id> \
  --status <reviewed|irrelevant|partial|external> \
  --summary '<本组提供了什么，或为何不影响用户结果>'
```

- `reviewed`：已形成至少一项带精确来源的发现；
- `irrelevant`：概要审视后确认不影响用户承诺，理由必须面向结果而非文件名；
- `partial`：已获得局部，但本组仍有会改变结论的内容未读或无法解释；游标留在本组；
- `external`：文件格式、权限或外部依赖使材料无法可靠读取，概要中说明责任动作。

继续运行 `next`，直到状态进入 `planning`。不维护逐文件阅读打卡，也不绕过当前材料组递归通读来源。

### 2.3 规划并复核知识目录

根据全部读后发现规划规范落点，而不是把来源目录翻译成知识目录。按独立变化和读者用途拆分；同一项发现只能由一个规范主题维护，其他页面和产品视图使用标准 Markdown 链接进入该落点：

```bash
python scripts/ingestion_workspace.py topic-add <case-id> <topic-id> \
  --title '<稳定、直观的知识标题>' \
  --purpose '<这页让目标读者理解或完成什么>' \
  --action <create|update|merge|view> \
  --path 'draft/knowledge/<area>/<page>.md' \
  --finding <finding-id> [--finding <finding-id>] \
  --view 'draft/knowledge/views/by-domain/<slug>.md' \
  --view 'draft/knowledge/views/by-journey/<slug>.md'
```

写正文前做第二遍目录复核。八个名称是**理解角度**，不是八篇固定页面：

- `position`：上级位置、上下游和相邻边界；
- `lifecycle`：端到端过程、角色、对象与异常循环；
- `data`：数据对象、标识、状态、输入输出和新鲜度；
- `rules`：规则、算法、口径与决定结果的条件；
- `software`：软件结构、代码职责、调用链与修改入口；
- `shared`：跨模块公共能力及其维护边界；
- `reality`：当前实现、当前决定、目标、历史、冲突和未知；
- `navigation`：从全貌到细节的产品视图和继续工作入口。

把每个适用角度映射到一个或多个主题；只有用户边界或读后发现能证明不适用时才排除：

```bash
python scripts/ingestion_workspace.py plan-review <case-id> \
  --lens position=<topic-id>[,<topic-id>] \
  --lens lifecycle=<topic-id>[,<topic-id>] \
  --lens data=<topic-id>[,<topic-id>] \
  --lens rules=<topic-id>[,<topic-id>] \
  --lens software=<topic-id>[,<topic-id>] \
  --lens shared=<topic-id>[,<topic-id>] \
  --lens reality=<topic-id>[,<topic-id>] \
  --lens navigation=<topic-id>[,<topic-id>]
```

不适用项使用 `--not-applicable <lens>=<依据>`。复核必须暴露未审材料组、未归位发现、未知主题和理解角度缺口；不要为了通过而把所有角度机械塞进一页。

目录复核前发现主题标题、落点、用途或发现归属不合理时，使用同一个 `topic-add` ID 重新提交完整计划；工作台会在尚未进入写作时更新它。若复核证明某个材料组被过早结束，显式回到该组：

```bash
python scripts/ingestion_workspace.py material-reopen <case-id> <group-id> \
  --reason '<哪项读者理解或目录决定需要重新核对本组>'
```

随后按 `next → finding-add → record-material` 补齐，再重新复核目录。不要手改后台状态，也不要为了修一个主题重跑全部材料。

### 2.4 按目录形成规范知识和产品视图

目录复核通过后运行 `next`。它一次返回一个主题及其读后发现。重复调用保持当前主题不变。

根据内容按需读取模板，不在开始时加载全部资产：

- 通用规范页：[knowledge-page.md](assets/knowledge-page.md)；
- 领域全貌：[domain-overview.md](assets/domain-overview.md)；
- 软件结构：[software-architecture.md](assets/software-architecture.md)；
- 产品视图：[product-view.md](assets/product-view.md)；
- 来源记录：[source-record.md](assets/source-record.md)；
- 公共能力抽取审查：[shared-capability-review.md](assets/shared-capability-review.md)。

先逐项比较 `next` 返回的核心结论、关键细节、定位和边界，再组织正文。正文必须充分内化输入、转换、输出、条件、边界、失败方式和继续工作入口；不能只保留发现的概括句而丢掉机制、字段变化、算法步骤、类函数或责任。引用只负责追溯，不能替代内容。章节先说明作用或核心判断；只加粗决定理解或行动的关键词、关系和限制。图表回答一个主要问题，并在邻近表格或段落补足图上没有的输入输出、约束和异常。

规范页与计划中的领域/旅程视图都形成后登记当前主题：

```bash
python scripts/ingestion_workspace.py record-topic <case-id> <topic-id> \
  --section '<finding-id>=<正文中的真实章节标题>' \
  [--section '<next-finding-id>=<正文中的真实章节标题>']
```

逐项检查发现的核心结论和关键细节确实进入所填章节后再登记。工作台检查所有发现都有真实章节定位、计划视图链接正文，然后推进到下一个主题；它不以关键词命中或字符数替代内容判断。完整整理的 `sources/index.md` 由工作台根据已校验来源、发现和章节落点自动重建，不手抄或另写一套来源清单。

## 3. 聚焦代码或问题整理

聚焦模式保留已经验证的“小问题、小批来源、立即写知识”路径：

启动前做一次简短的**目标覆盖**检查：用户承诺的每项结果都应由一个具体读者问题负责；不要让一两个局部问题悄悄替代完整请求。每题规划一至三个能够独立阅读和维护的规范落点；一个问题需要超过三篇正文时，先收束问题或调整知识地图，不用堆页面掩盖边界不清。

```bash
python scripts/ingestion_workspace.py start <case-id> \
  --mode focused \
  --goal '<读者最终能够理解或执行什么>' \
  --reader '<目标读者>' \
  --source <source-id>=<authorized-directory> \
  --question '<具体读者问题>' \
  [--boundary '<不能做错的边界>']

python scripts/ingestion_workspace.py plan-unit <case-id> <question-id> <unit-id> \
  --title '<知识单元标题>' \
  --kind <business|data|software|run|other> \
  --path 'draft/knowledge/<area>/<page>.md' \
  [--require-run]

python scripts/ingestion_workspace.py next <case-id> <question-id> \
  --query '<字段、接口、表、类、页面或业务词>' [--limit 6]
```

只读取 `next` 返回的 `absolute_path`。代码问题沿实际需要连接入口、状态与交互、API 与类型、业务编排、算法、数据访问、Schema、返回转换和验证入口；不机械凑层，也不让 README 代替中央实现。每批来源读完后先更新正文，再登记：

```bash
python scripts/ingestion_workspace.py record <case-id> <question-id> \
  --status <answered|partial|external_missing|conflict> \
  --summary '<正文现在能回答什么>' \
  --source '<source-id>:<path>' \
  --knowledge 'draft/knowledge/<area>/<page>.md' \
  [--missing '<仍缺什么>'] \
  [--dismiss-unused '<本批其余项为何不改变答案>'] \
  [--close-candidates '<为何可以停止继续取源>']
```

已经形成可靠局部，但剩余候选不会改变当前答案时，可以用 `stop-search <case-id> <question-id> --reason '<停止理由和仍存边界>'` 结束继续取源，不需要重新运行 `next` 制造空批次。

需要 API、SQL、页面或数值证明时，在来源项目的临时 Git worktree 运行。优先把多步命令写入摄入案 `evidence/recipes/`，再用 `--command-file`；不在原来源目录写调试文件，不安装依赖，不把 Harness 测试冒充项目运行证据：

```bash
python scripts/ingestion_workspace.py run <case-id> <question-id> \
  --source-id <source-id> \
  --kind <health|api|sql|page|other> \
  --purpose '<准备证明什么>' \
  --command-file 'evidence/recipes/<name>.sh' \
  [--mount '<必须保持存活的外部输入>'] \
  [--copy-mount '<需要私有可写副本的依赖>'] \
  [--runtime-note '<时钟、服务或数据快照边界>'] \
  [--artifact '<需要保留的相对路径>']
```

先把运行的输入范围、实际输出、环境身份和不能外推的边界写回规范页，再用 `record --run-id <run-id> --knowledge <path>` 登记。最后同步产品视图并运行一次 `check-unit`。

## 4. 人工审查与发布

所有主题或问题形成后运行：

```bash
python scripts/ingestion_workspace.py review <case-id>
```

只把候选知识、产品视图和根 `review.md` 交给用户。完整模式只有在目录主题全部形成、知识结构通过且领域/旅程视图都存在时才进入 `publish_ready`。

用户批准后才把候选合并到正式目录，更新知识入口、来源记录、领域地图和日志，并执行：

```bash
python scripts/knowledge_check.py
git diff -- knowledge config
```

最后从正式 `knowledge/index.md` 完成一次真实浏览或问题消费。结构检查只证明链接和声明一致，不证明业务事实正确；内容审查、正式发布和真实消费全部完成后才能报告摄入结束。

## 护栏

- 不用模型常识填补关键业务事实，不把目标设计写成当前实现；一个材料组可以同时产生多种现实形态。
- 不恢复逐文件 `mark`、文件覆盖率或“所有文件必须分类”；完整模式审视材料组，聚焦模式处理当前小批。
- 不让来源记录、引用或一两句摘要替代知识内化；新证据先进入正文，再登记状态。
- 公共能力只有出现真实复用、共同契约和明确维护责任时才提出抽取，不因名称相似自动合并。
- 不绕过当前游标并行推进多个材料组或主题；命令失败时先运行 `status`，按公开下一动作恢复，不读取工作台源码猜状态。
