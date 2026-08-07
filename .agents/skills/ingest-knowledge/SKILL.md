---
name: ingest-knowledge
description: >
  摄入一批有界的文档、代码、Schema 或人工材料，把它们整理为可浏览、可追溯、可继续工作的规范知识与产品视图。
  当用户要求整理、导入、摄入或归并材料，或把已经完成的代码变化回写到现有知识时使用；
  同时支持宽范围完整整理、代码变化回写与聚焦问题整理。
  不用于只回答一个问题、直接改代码或无来源创作。
---

# 知识摄入

把授权材料转化为**规范知识、产品视图和一份 `review.md`**。来源始终只读；候选只写入
`workspaces/knowledge-ingestion/<case-id>/draft/`。用户批准前不得修改正式 `knowledge/` 或 `config/`。

机器状态只保存在 `.state/case.json` 和 `.state/source-manifest.jsonl`。使用工作台命令读写状态，不手工编辑这两个文件，也不把它们交给用户维护。

## 1. 选择最低充分路径

- **宽范围完整整理（`complete`）**：用户交来一个此前不清楚结构的领域、模块或混合材料包，希望从零建立知识，或材料本身的主题和现实身份尚待发现。先审视材料地图和读后发现，再对照已有知识规划目录。不要在读材料前猜主题或现实身份。
- **代码变化回写（`writeback`）**：来源是固定代码仓库/commit，目标是让既有知识跟上新增系统、功能、规则或实现变化。先判断系统身份，再从变化影响定向读取；**不要为了回写一个代码纵切运行完整材料盘点**。
- **聚焦整理（`focused`）**：用户已限定一个代码动作、接口、指标、脚本或具体问题。直接按读者问题定向取源，保留真实运行能力，不要求先审视整个领域材料地图。

这是同一个 Skill、同一规范知识底座的三条轻重路径。范围已经清楚时直接选择，不向用户询问内部模式名称。

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

工作台在启动时冻结正式 `knowledge/` 与领域配置的文件指纹，并原样复制到 `draft/`。空正式知识由此得到首版候选；已有正式知识由此得到隔离的子版本。只把本次新增材料登记为 `--source`，不要把旧材料重新加入来源，也不要在正式目录直接编辑。

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
  [--finding <finding-id>] [--finding <finding-id>] \
  [--view 'draft/knowledge/views/by-domain/<slug>.md'] \
  [--view 'draft/knowledge/views/by-journey/<slug>.md']
```

处理已有知识时，先从候选中的领域入口、产品视图和受影响正文理解当前落点，再选择动作：

- `create`：父知识没有该页面，新增长期知识主题；
- `update`：新材料补充或修正现有主题，保持原规范路径；
- `merge`：新发现应融入一个现有规范落点，而不是另建近义页；
- `view`：只调整产品视图的选择、排序和导航，不复制规范事实。

`view` 可以不关联读后发现，因为它只负责导航，不维护新的规范事实。新增领域目录需要
`overview.md` 时，把这个入口与正文主题一起规划为 `view`，并让领域视图链接它；不要等写完后再补一个未登记页面。
普通正文主题只在对应产品视图应新增或继续维护其直接入口时声明 `--view`；不要为了照抄命令示例给每个主题机械绑定两种视图。

工作台会校验 `create` 不能覆盖父页面，`update/merge` 必须指向父页面且最终确有内容变化。本切片不支持直接删除父知识页；发现过时内容时先在原页中区分新旧状态和适用范围，页面退役需要另行审查。

`update/merge` 不是在旧页末尾追加“本批材料”“本次增量”或日期章节，也不是把父页面重写成更短的摘要。写作前先通读原页标题和正文，默认保留已有 frontmatter、段落、图表、链接和技术细节；把新发现插入原有语义章节，只局部修订被新证据直接改变的表述。原结构承载不了时，只新增面向长期读者的稳定标题。批次、文件和摄入轮次只进入来源追溯与审查页。产品视图原位增加或调整导航，不新增“增量导航”，也不删除仍有效的入口。

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

如果全部主题写完后的语义复核或 `review` 发现漏规划的规范页、领域入口或产品视图，不要先制造未登记修改，不要重读材料，也不要手改状态。即使当前已是 `publish_ready`，也可以运行：

```bash
python scripts/ingestion_workspace.py plan-reopen <case-id> \
  --reason '<最终审查暴露的具体漏规划问题>'
```

只补充这次暴露的 `create` / `update` / `merge` / `view` 主题，重新运行 `plan-review`，完成新增主题后再次 `review`。如果只是同步父级页面中已被新增知识淘汰的“当前覆盖、当前缺口或以后再补”表述，登记一个无新发现的 `update` 主题，并在 `--purpose` 中写清需要消除的前后矛盾；不要伪造新的读后发现。已登记主题内部的内容或链接错误直接在原候选中修正，不需要重新打开目录。

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

对于 `update/merge`，必须通读最终整页，但采用保守的局部编辑：新增内容按语义归位，不得为了统一文风、缩短篇幅或重新概括而整页重写。保留父知识不等于逐字冻结；写完后逐项复核父版本中描述“当前覆盖、当前缺口、尚未进入、以后补齐”的表述，只能选择仍然成立、按新证据更新，或改成有明确时间范围的历史。完成标准是父知识细节仍在，且没有当前态表述与新发现互相矛盾。产品视图同样保留仍有效入口，同时检查重复章节、重复边界和按摄入轮次分区。

规范页与计划中的领域/旅程视图都形成后登记当前主题：

```bash
python scripts/ingestion_workspace.py record-topic <case-id> <topic-id> \
  --section '<finding-id>=<正文中的真实章节标题>' \
  [--section '<next-finding-id>=<正文中的真实章节标题>']
```

逐项检查发现的核心结论和关键细节确实进入所填章节后再登记。工作台检查所有发现都有真实章节定位、计划视图链接正文，然后推进到下一个主题；它不以关键词命中或字符数替代内容判断。完整整理的 `sources/index.md` 由工作台根据已校验来源、发现和章节落点自动重建；有父知识时保留既有来源导航并追加本次材料，不手抄或另写一套来源清单。

增量案完成正文和产品视图后，还要更新 `draft/knowledge/index.md` 的**当前知识范围、导航和缺口**，并在 `draft/knowledge/log.md` 追加一条变更记录。入口中若仍有“新增来源尚未进入”或“该能力仍缺失”等父版本声明，逐项判断它现在是已被补齐、仍然成立，还是只应保留为历史；不能一边把内容写进正文，一边让根入口继续否认它。日志保留历史原文，只追加本次实际新增、更新、冲突和未决边界。

## 3. 代码变化回写

代码回写的输入是**现有正式知识 + 固定代码事实 + 本次变化的真实验证**，产物是可拒绝的知识候选。它不是重新摄入整个代码仓，也不是在每篇旧文末尾追加一段更新摘要。

### 3.1 先固定读者问题与系统身份

启动时把用户结果拆成三到四个问题；按实际影响删减，不机械凑齐：

1. 代码属于哪个来源和系统，当前用户能做什么，不能证明什么；
2. 哪些业务对象、数据、状态、规则或算法已经变化；
3. 软件结构、跨层数据转换、关键实现和修改入口怎样变化，运行证据证明到哪里；
4. 根入口、领域/旅程视图、系统/来源导航、未知和日志怎样同步。

```bash
python scripts/ingestion_workspace.py start <case-id> \
  --mode writeback \
  --goal '<代码变化后，读者能够理解或继续完成什么>' \
  --reader '<业务读者、开发者或两者>' \
  --source <source-id>=<fixed-git-directory> \
  --question '<来源、系统身份、当前能力和现实边界是什么？>' \
  --question '<受影响的业务、数据和规则怎样变化？>' \
  --question '<软件责任、调用链、修改入口和运行证据怎样变化？>' \
  --question '<用户从哪些产品视图进入，哪些旧表述需要同步？>' \
  --boundary '<代码事实不能外推成生产或人工决定>'
```

比较候选中的既有来源页、系统页、领域入口和产品视图，再登记身份：

```bash
python scripts/ingestion_workspace.py identity-set <case-id> \
  --relationship <same_system|new_system|uncertain> \
  --reason '<仓库、commit、运行入口和版本沿革如何支持该判断>' \
  [--source-path 'draft/knowledge/sources/<source>.md'] \
  [--system-path 'draft/knowledge/systems/<system>.md']
```

- `same_system` 更新已经存在的来源页和系统页；
- `new_system` 必须建立独立来源页和系统页，再通过业务主题关联，不能写进名称相近的旧原型页；
- `uncertain` 只用于先取证，最终审查前必须解决。

来源身份和系统身份不是文件分类。前者说明代码/材料来自哪里、固定到哪个版本、能证明什么；后者说明用户面对哪套可独立运行和演进的能力。不同仓库、commit 和运行链可以共享业务规则，但不能因此伪装成同一系统版本。

`identity-set` 会同时返回冻结来源中的验证报告候选。先核对报告对应的 commit、环境、夹具和覆盖范围；报告足以回答当前问题时，把它放进后续 `next`/`record` 的直接来源，不重复运行。报告过时、范围不足或用户要求复验时，才进入隔离运行。

报告标注的实现 commit 与冻结 commit 不同，不自动等于证据冲突。先核对提交关系和两者之间的实际 diff：若报告指向的实现提交是冻结提交的祖先，后续只增加报告、夹具或不改变受测行为的材料，则把它作为冻结版本的有效证据并同时记录实现/证据身份；只有两者没有祖先关系、相关实现后来发生未覆盖变化，或环境与结果无法关联时才降级为待确认。不能凭 commit 字符串不同直接否认证据。

### 3.2 从影响面规划，不从仓库目录规划

为每个问题规划一至四个规范落点，只保留共同回答该问题所需的页面。新系统的来源页、系统页必须出现在问题一；软件结构必须至少有一个 `software` 单元；业务事实优先更新现有数据、规则或流程页，只有职责确实独立时才新建。若第四个落点只是导航、日志或来源清单，留到最终同步，不占问题单元：

```bash
python scripts/ingestion_workspace.py plan-unit <case-id> <question-id> <unit-id> \
  --title '<长期稳定标题>' \
  --kind <business|data|software|run|other> \
  --path 'draft/knowledge/<area>/<page>.md' \
  [--require-run]
```

只有答案依赖**尚无固定证据的当前行为或数值**时才使用 `--require-run`。代码变化来自已经验证的开发任务，且固定 commit 内已有可定位的验证报告/结果时，把它作为直接来源并说明证据范围；不要为了通过工作台再次机械运行。已有报告不足、会改变业务结论或用户明确要求复验时，再使用隔离运行。

使用 `--require-run` 后，首次 `next` 会把冻结来源中的验证报告优先放入 packet。工作台把已登记的固定验证报告或本案成功隔离运行都视为“当前行为证据”，但只做来源与流程约束；Agent 仍必须检查报告是否真的覆盖当前 commit 和读者问题，不能因文件名叫 report 就照单全收。

随后按问题定向取源：

```bash
python scripts/ingestion_workspace.py next <case-id> <question-id> \
  --query '<页面、字段、表、指标、类、接口或规则>' --limit 6
```

一次只读当前 packet。优先连接：产品入口与用户动作 → Schema/类型与状态 → Service/算法 → Repository/SQL/迁移 → 前端转换与共享组件 → 测试和真实运行。文档帮助定位，当前行为最终以固定源码、契约和运行结果为准。取得最低充分证据后立即写知识并 `record`；剩余候选不会改变答案时用 `--close-candidates` 停止，不扩展成整仓阅读。

停止取源前，回到**原始读者问题**逐项核对，而不是只核对自己刚写的总结。问题点名了多个组件、转换或结果时，每一项都必须在正文中得到责任、输入输出或证据范围；不能用“已经讲清调用链”代替仍未说明的数据转换。软件问题若候选中仍有直接承担 `types`、`utils`、`mapper`、`adapter`、领域模型或行转换的文件，至少读取并解释决定行为的入口，直到模型、转换、编排、数据访问和写入对象的职责与修改路径闭合；不得把一个未更新的旧页面登记为已承载新答案。固定验证报告被采用时，正文应内化会改变读者判断的**具体范围与代表性结果**，包括关键输入、数量或状态前后值和本次回归范围；逐项识别日期移动、种子、夹具和环境修补，保留会影响解释的准备动作并明确它不是产品能力，不能只写“测试通过”或把报告链接当作答案。

当 packet 的源码项返回 `contract_candidates`，且读者需要完整字段对齐时，选择真正承担契约的符号冻结字段清单：

```bash
python scripts/ingestion_workspace.py contract-inspect <case-id> <question-id> \
  --source '<source-id>:<path>' \
  --symbol '<契约类名>' \
  --purpose '<该契约为什么影响读者理解或开发>'
```

首版只确定性提取 Python 注解类及其本地继承字段；其他语言没有提取器时仍按源码人工内化，并把组件缺口留在审查中。`contract-inspect` 返回的字段必须全部进入本问题的规范知识，`check-unit` 会逐项核对，从而防止“18 个字段”被压缩成几个字段组。

契约来自 CSV、API、消息、Schema 或配置时，不能只冻结内部对象。正文同时保留：**外部名称与顺序、内部字段映射、类型/范围、跨字段不变量、整批或单项失败语义**；外部 `*_json` 与内部解析后字段必须明确区分。直接常量、模型和解析器共同承担契约时逐个读取，直到读者可以构造合法输入、判断拒绝原因并定位修改入口。

### 3.3 把发现重构成知识，而不是更新摘要

每个规范落点都要独立承担其读者问题。写完后，读者不打开来源也应能得到：

- **核心判断和范围：** 这个对象是什么、处于哪里、当前成立到什么版本；
- **结构或运行逻辑：** 输入、对象、步骤/组件、转换、输出和异常怎样连接；
- **关键细节：** 决定理解或修改的字段、公式、粒度、状态、类/函数和跨文件入口；
- **现实边界和证据：** 已实现、目标、历史、冲突、未知分别是什么，如何继续核验。

这些是知识责任，不是四个固定标题。已有页面能承担责任时把新证据原位融入其逻辑链；不能承担时建立独立规范对象。禁止用“本次更新”“当前 QPL”“某日增量”等尾部附录代替结构重构，也禁止用引用或来源索引代替机制、算法和实现细节。

数据契约是本轮核心时，不能只写“包含若干字段”：正文至少明确**最小粒度/主键、顶层字段组、嵌套结构、状态与不变量、迁移或兼容边界**；开发者需要逐字段对齐时保留完整字段名。算法是核心时，写出输入、步骤/公式、聚合顺序、零分母与异常边界，并解释相邻概念为什么不能互相替代。

一个系统涉及软件理解或后续开发时，至少用匹配问题的视图讲清：用户场景与系统边界、组件职责、一次运行/调用时序、数据结构与转换、源码组织和一次修改路径。是否使用流程图、时序图、组件图、数据表或代码地图由内容决定；图后补充图中无法表达的输入输出、约束、异常和 owner，而不是把图再复述一遍。

登记问题为 `answered` 前做一次内容交接检查：读者不打开来源，是否能逐项回答原问题；采用的运行报告是否留下了足以判断覆盖范围的真实结果；被关闭的直接转换文件是否确实不会改变答案。这里检查的是**答案完整性**，不是要求复制源码、穷举测试或增加一份中间清单。

用户结果包含“运行、使用、调用、复现”时，答案完整性还要求一条从项目根可复制执行的命令，包含必需的运行器、子命令、参数/确认值，并在相邻位置说明关键输出与失败语义。只写动作名、类名或 `preview/apply` 等概念入口不算可运行交接。

### 3.4 完成父知识融合与审查

每个问题都按聚焦流程 `record → check-unit`。全部问题完成后再做一次全局融合：

- 更新 `draft/knowledge/index.md` 的当前范围、入口和缺口；
- 新系统同步 `sources/index.md`、`systems/index.md`，并保留所有父来源导航；
- 更新实际受影响的领域视图和旅程/学习视图，使新规范对象可达；
- 在 `draft/knowledge/log.md` 追加本轮新增、修改、保持边界和未合入内容；
- 检查旧页面中的“当前没有、尚未进入、以后补齐”和“上面 N 项”等范围/数量描述是否已过时，不改写无关父知识。
- 对每个修改的父页面，复核所有绑定旧 commit、分支、版本或能力状态的当前态句子；新事实与旧句冲突时原位修正或标成有时间范围的历史，不能只在后文追加相反结论。
- 用户点名或本次代码真实使用的既有公共能力，应更新其规范页以说明新增消费者与责任边界；若公共契约和维护责任确实没有变化，审查中明确说明为何无需修改，不能只在领域软件页提到组件就视为已融合。

根 `index.md`、各类 `*/index.md` 和 `log.md` 是最终导航/记录同步，不作为实质 `plan-unit`；需要让某个视图承担稳定阅读入口时，规划具体的领域视图或旅程视图。`record` 可以重复引用本问题已经登记过的来源来补充知识路径或状态，不必为了同一来源重新取包。

最后运行：

```bash
python scripts/ingestion_workspace.py review <case-id>
```

代码回写审查会同时检查各问题、独立系统身份、父知识保持、计划外正文变化、业务/软件影响、产品视图和结构。通过只表示候选已经具备人工审查条件；未经用户批准仍不得发布。

## 4. 聚焦代码或问题整理

聚焦模式保留已经验证的“小问题、小批来源、立即写知识”路径：

启动前做一次简短的**目标覆盖**检查：用户承诺的每项结果都应由一个具体读者问题负责；不要让一两个局部问题悄悄替代完整请求。每题规划一至四个能够独立阅读和维护的规范落点；需要更多时先收束问题或调整知识地图，不用堆页面掩盖边界不清。

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

## 5. 人工审查与发布

所有主题或问题形成后运行：

```bash
python scripts/ingestion_workspace.py review <case-id>
```

只把候选知识、产品视图和根 `review.md` 交给用户。审查页同时展示父知识指纹以及候选实际新增、修改和删除的文件；未计划的正文/视图修改和任何父知识删除都会阻止本切片进入发布准备。完整模式只有在目录主题全部形成、知识结构通过且领域/旅程视图都存在时才进入 `publish_ready`。

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
