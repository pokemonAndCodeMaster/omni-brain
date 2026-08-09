---
name: ingest-knowledge
description: >
  摄入一批有界的文档、代码、Schema 或人工材料，把它们整理为可浏览、可追溯、可继续工作的规范知识与产品视图。
  当用户要求整理、导入、摄入或归并材料，用新材料更新现有知识，或系统整改既有知识的阅读体验时使用；
  同时支持宽范围完整整理、聚焦代码/问题整理与整库阅读审视。
  不用于只回答一个问题、直接改代码或无来源创作。
---

# 知识摄入

把授权材料转化为**规范知识、产品视图和一份 `review.md`**。来源始终只读；候选只写入
`workspaces/knowledge-ingestion/<case-id>/draft/`。用户批准前不得修改正式 `knowledge/` 或 `config/`。

机器状态只保存在 `.state/case.json` 和 `.state/source-manifest.jsonl`。使用工作台命令读写状态，不手工编辑这两个文件，也不把它们交给用户维护。

## 0. 第一个来源动作

先选模式，再执行对应的唯一入口。**在工作台返回精确路径前，不读取、列举或搜索来源和 `knowledge/`，也不查看 `workspaces/` 猜测状态。**

| 任务形态 | 唯一首轮 | 首次允许读取的内容 |
|---|---|---|
| 从一批新材料建立或增量融合知识 | `start --mode complete → survey → next` | `next` 返回的当前材料组成员 |
| 围绕明确问题或代码动作整理 | `start --mode focused → plan-unit → next` | `next` 返回的当前来源小批 |
| 整体整改已有知识的阅读体验 | `start --mode focused --audit-all-user-pages → audit-pages → audit-next` | `audit-next` 返回的 `absolute_path` 与写作指导 |

整库模式中，正式 `knowledge/` 虽然是直接事实源，也只能通过 `audit-next` 按一至三个页面读取；`audit-pages` 的公开清单已经足够选择第一组，不需要先通读正文。选定模式后不要混用另一模式的命令。

## 1. 选择最低充分模式

- **宽范围完整整理（`complete`）**：用户交来一个领域、模块或混合材料包，希望从零建立知识，或需要从新增材料中发现应怎样有机融入现有知识。先审视本次材料地图和读后发现，再对照已有知识规划目录。不要在读材料前猜主题或现实身份。
- **聚焦整理（`focused`）**：用户已限定一个代码动作、接口、指标、脚本、具体问题，或明确指定少量既有知识页进行阅读重构。直接按读者问题定向取源，保留真实运行能力，不要求先审视整个领域材料地图。即使这些页面分别属于业务、未知和软件，只要任务不是从新材料发现知识范围，就仍然使用聚焦模式并按页面目的拆题。
- **整库阅读审视（`focused --audit-all-user-pages`）**：用户明确要求整体整改已有知识库或某个完整知识包，且现有规范知识本身就是直接事实源。逐页判断应该重构还是有理由保留，不重新摄入项目外材料，也不把所有页面塞进一个宽泛问题反复检索。

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

- 形成或重构任何用户可见页面前，先读[读者优先的知识表达](references/reader-first-writing.md)；
- 知识总入口：[root-entry.md](assets/root-entry.md)；
- 通用规范页：[knowledge-page.md](assets/knowledge-page.md)；
- 领域全貌：[domain-overview.md](assets/domain-overview.md)；
- 未知与冲突：[open-questions.md](assets/open-questions.md)；
- 软件结构：[software-architecture.md](assets/software-architecture.md)；
- 产品视图：[product-view.md](assets/product-view.md)；
- 来源记录：[source-record.md](assets/source-record.md)；
- 公共能力抽取审查：[shared-capability-review.md](assets/shared-capability-review.md)。

模板选择不是自由抽样：总入口必须读 `root-entry.md`，领域 `overview.md` 必须读 `domain-overview.md`，用途是集中管理未知、冲突和补知责任的页面必须读 `open-questions.md`，`plan-unit --kind software` 必须读 `software-architecture.md`，其他规范正文读 `knowledge-page.md`，具名视图读 `product-view.md`。同一页面只加载与其责任直接相关的模板，不因一次任务有三类页面就把所有模板预读一遍。

先逐项比较 `next` 返回的核心结论、关键细节、定位和边界，再组织正文。正文必须充分内化输入、转换、输出、条件、边界、失败方式和继续工作入口；不能只保留发现的概括句而丢掉机制、字段变化、算法步骤、类函数或责任。引用只负责追溯，不能替代内容。章节先说明作用或核心判断；只加粗决定理解或行动的关键词、关系和限制。图表回答一个主要问题，并在邻近表格或段落补足图上没有的输入输出、约束和异常。

重构既有页面时，先在推理中完成一次**结构诊断**，不新增中间文件：为每个现有章节写出它回答的读者问题，再给出目标页面责任和目标大纲。父页面的事实、图表、链接和技术细节需要保留或有依据地归位，父页面的标题与章节顺序不是约束。若现有页面缺少概览、主线、同维度比较、影响/责任或深入顺序，必须重组相应内容；只增加导航、替换过程术语或加粗原句不算完成重构。写完后按读者参考中的八项检查逐项复核，确认页面从实际入口可以独立阅读。

对于 `update/merge`，必须通读最终整页，但采用保守的局部编辑：新增内容按语义归位，不得为了统一文风、缩短篇幅或重新概括而整页重写。保留父知识不等于逐字冻结；写完后逐项复核父版本中描述“当前覆盖、当前缺口、尚未进入、以后补齐”的表述，只能选择仍然成立、按新证据更新，或改成有明确时间范围的历史。完成标准是父知识细节仍在，且没有当前态表述与新发现互相矛盾。产品视图同样保留仍有效入口，同时检查重复章节、重复边界和按摄入轮次分区。

规范页与计划中的领域/旅程视图都形成后登记当前主题：

```bash
python scripts/ingestion_workspace.py record-topic <case-id> <topic-id> \
  --section '<finding-id>=<正文中的真实章节标题>' \
  [--section '<next-finding-id>=<正文中的真实章节标题>']
```

逐项检查发现的核心结论和关键细节确实进入所填章节后再登记。工作台检查所有发现都有真实章节定位、计划视图链接正文，然后推进到下一个主题；它不以关键词命中或字符数替代内容判断。完整整理的 `sources/index.md` 由工作台根据已校验来源、发现和章节落点自动重建；有父知识时保留既有来源导航并追加本次材料，不手抄或另写一套来源清单。

增量案完成正文和产品视图后，还要更新 `draft/knowledge/index.md` 的**当前知识范围、导航和缺口**，并在 `draft/knowledge/log.md` 追加一条变更记录。入口中若仍有“新增来源尚未进入”或“该能力仍缺失”等父版本声明，逐项判断它现在是已被补齐、仍然成立，还是只应保留为历史；不能一边把内容写进正文，一边让根入口继续否认它。日志保留历史原文，只追加本次实际新增、更新、冲突和未决边界。

## 3. 聚焦代码或问题整理

聚焦模式保留已经验证的“小问题、小批来源、立即写知识”路径：

### 3.1 整库阅读审视

整库审视先复制正式知识并建立用户页面清单。这里的任务是改善已有知识的组织与表达，**不是重新发现整库事实**：

```bash
python scripts/ingestion_workspace.py start <case-id> \
  --mode focused \
  --audit-all-user-pages \
  --goal '<整库整改后读者能够理解或完成什么>' \
  --reader '<目标读者>' \
  --source current-knowledge=knowledge \
  --question '<第一类独立读者结果>' \
  --boundary '只依据现有规范知识，不新增无来源事实；正式 knowledge/ 不修改'
```

先查看公开页面清单。它只给标题、路径、决定和页面计划，不读取正文：

```bash
python scripts/ingestion_workspace.py audit-pages <case-id>
```

按**同一个读者结果、一次最多三个页面**拆成小组；一个读者问题可以连续处理多组页面，不受普通聚焦模式“三个规范落点”的限制。不得先用“了解全貌”之类宽泛目标通读整库，也不得读取 `.state/` 或工作台源码来盘点页面或猜命令。只有下一组页面确实服务于另一种独立理解或行动结果时，才用 `question-add` 新增问题；不要预先建一批重叠问题。

让工作台把本组页面绑定到读者问题，并返回同名正式页、写作指导和必须保留的机器结构：

```bash
python scripts/ingestion_workspace.py audit-next <case-id> <question-id> \
  --page 'draft/knowledge/<first-page.md>' \
  [--page 'draft/knowledge/<second-page.md>']
```

只读取 `audit-next` 返回的 `absolute_path`、`required_guidance` 和 `required_structure`。`required_structure`（例如已有 frontmatter 和一级标题 `# Citations`）是可重建知识结构所需的外壳；保留它不妨碍正文使用自然、直观的中文标题。对每页完整执行[读者优先的知识表达](references/reader-first-writing.md)中的完成前检查，然后**先计划，后写作**：

```bash
python scripts/ingestion_workspace.py audit-plan <case-id> \
  'draft/knowledge/<page.md>' \
  --decision change \
  --reason '<当前结构为何妨碍理解，需要怎样调整>' \
  --target-section '<目标一级章节>' \
  --target-section '<下一目标一级章节>'
```

目标章节是页面内容主线，不是为了通过检查而复制模板。整改不能退化为只清理批次术语、增加导航或给旧句加粗；只要页面责任、概览、主线、同维度比较、重点层次、图文互补、现实边界或软件讲解仍不能支持目标读者，就应重组相应内容并保留全部有效细节。特别是软件页要从真实业务动作解释结构、对象、调用和数据转换，不因原文已经有 4+1、分层或设计模式名称就判定合格。

如果逐项检查后页面已经满足目标，不要为了通过工具制造差异。直接登记保留计划：

```bash
python scripts/ingestion_workspace.py audit-plan <case-id> \
  'draft/knowledge/<page.md>' \
  --decision keep \
  --reason '<对照哪些读者结果后确认结构与细节已经足够>'
```

整库模式中，`audit-plan` 是唯一页面计划；**不要再运行 `plan-unit` 或 `keep-unit`**。形成候选后，先把本组每页的真实决定写入整库清单；计划修改的页面必须真实出现声明的目标章节。理由说明读者结果或实际改进，不写“为了通过检查”：

```bash
python scripts/ingestion_workspace.py audit-pages <case-id> \
  --changed 'draft/knowledge/<page.md>=<解决了什么读者问题>' \
  --kept 'draft/knowledge/<other.md>=<为何现状已经足够>'
```

随后用 `record` 原样登记 `audit-next` 返回的本批 `ref`。工作台根据页面绑定自动登记本批入口、正文和视图；不要重复传 `--knowledge`：

```bash
python scripts/ingestion_workspace.py record <case-id> <question-id> \
  --status answered \
  --summary '<本组页面现在让读者理解或完成什么>' \
  --source '<first-ref>' [--source '<second-ref>']
```

误建的问题只有在**尚未绑定页面、取得证据或产生结果**时才能安全撤销：

```bash
python scripts/ingestion_workspace.py question-drop <case-id> <question-id> \
  --reason '<为何它与现有读者结果重复或不再需要>'
```

长入口页和各级 `index.md` 也使用同一页面小批，不需要伪装成规范知识单元。运行 `status` 可直接查看每个问题绑定的页面、修改/保留状态和最多三个下一待审页面，不读取内部状态。一个读者问题的相关页面全部处理后运行 `check-unit`。整库完成标准是待审页面为 0、每个保留的问题都通过 `check-unit`、`review` 返回 `ready: true`，并从根入口实际走通默认学习路线和任务入口。

### 3.2 有界问题与代码整理

启动前做一次简短的**目标覆盖**检查：用户承诺的每项结果都应由一个具体读者问题负责；不要让一两个局部问题悄悄替代完整请求。每题规划一至三个能够独立阅读和维护的规范落点；一个问题需要超过三篇正文时，先收束问题或调整知识地图，不用堆页面掩盖边界不清。

按**读者目的和直接证据集合**拆题：只有几篇页面必须共同回答同一个问题时，才把它们规划到同一问题；领域全貌、未知/冲突处理和软件实现等各自可以独立消费的结果，通常应是不同问题。不要为了利用“最多三个落点”而把互不相同的页面塞进一个长问题。每个问题分别 `next → 读当前小批 → 更新对应正文 → record`，登记来源时原样使用 `next` 返回的 `ref`。

启动命令只接收第一个读者问题。用户结果跨多个页面责任时，启动后立即用 `question-add` 为其余责任分别建题，再逐题 `plan-unit`；不要先把所有目标连接成一个长问句。一个问题应只有一个主要理解或行动结果，例如“建立领域全貌”“处理未知与冲突”或“理解一次软件修改”，而不是同时承担三者。

聚焦任务需要新建或重构用户可见页面时，同样先读[读者优先的知识表达](references/reader-first-writing.md)，再按页面责任选择模板。`index.md` 是导航而非规范知识单元，不能作为 `plan-unit` 的实质落点；在正文和具名产品视图形成后同步更新相关 `index.md`，由知识结构检查验证链接。只调整导航时，不伪造新的业务来源或知识单元。

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
  [--knowledge 'draft/knowledge/<second-page>.md'] \
  [--missing '<仍缺什么>'] \
  [--dismiss-unused '<本批其余项为何不改变答案>'] \
  [--close-candidates '<为何可以停止继续取源>']
```

已经形成可靠局部，但剩余候选不会改变当前答案时，可以用 `stop-search <case-id> <question-id> --reason '<停止理由和仍存边界>'` 结束继续取源，不需要重新运行 `next` 制造空批次。

若先用 `partial` 登记来源、随后才完成正文，候选队列关闭后可以再次运行 `record` 更新最终摘要与状态；这次不重复传 `--source`，只传最终 `--status`、`--summary` 和已完成的 `--knowledge`。工作台保留先前证据并重建 `review.md`，避免审查页残留“正文尚未完成”的旧状态。

`check-unit` 已经包含候选知识结构检查，并且聚焦输出只显示当前计划页面的读者警告。计划过但审视后无需修改的既有页面先运行 `keep-unit`，不要制造空改动。人工批准前不要为了聚焦任务再次运行全库 `knowledge_check.py`，避免被继承页面的已知警告淹没；整库阅读审视在全部页面决定完成后可以对候选运行一次全库检查，正式发布后再从正式入口复核。

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
