---
name: ingest-knowledge
description: >
  将有界的混乱文档、代码、导出材料或人工说明摄入为可浏览、可追溯、可维护的规范知识。
  当用户要求整理、导入、摄入或归并一批材料，建立或更新知识与产品视图时使用；
  不用于只回答一个问题、直接改代码或无来源的自由创作。
---

# 知识摄入

把来源当作证据，把 `knowledge/` 当作唯一发布面，把
`workspaces/knowledge-ingestion/<case-id>/` 当作发布前工作台。机器工具负责来源身份、固定入口和机械门禁；Agent 负责理解语义、组织知识和暴露未知；人负责批准发布与语义选择。

## 1. 建立工作台

从用户请求提取材料位置、期望结果和不能做错的事项。只有缺失信息会改变授权范围或发布结果时才追问一次。先读取 `knowledge/index.md`、`config/knowledge-domains.yaml` 和直接相关入口，不遍历整个知识库。

用用户授权的每个来源目录执行一次初始化：

```bash
python scripts/ingestion_workspace.py init <case-id> \
  --goal '<用户最终要得到的结果>' \
  --source <source-id>=<authorized-directory> [--source ...]
```

该命令确定性生成真实文件数、逐文件指纹、Git 基线、固定根入口、覆盖账本和正式知识副本。不要自行手搓工作台，也不要把 `brief.md`、`inventory.md`、`questions.md` 或 `review.md` 放入 `assets/`。

填写根目录的 `brief.md` 和 `completion.yaml`。当用户要求“浏览、理解、学习或让后续模型继续使用”且未说明读者背景时，按零背景读者填写；内容深度必须由预期使用结果反推。

完成条件：`source-summary.md` 显示每个授权来源的机器计数；`brief.md` 能独立说明目标、读者、范围、禁区和停止条件；`completion.yaml` 的读者与结果已经填写。

## 2. 有界阅读并登记覆盖

先读 `source-summary.md`，再按 `brief.md` 中的问题搜索最小直接来源。来源很多时不要整份打开 `source-manifest.jsonl` 或 `coverage.yaml`，用以下命令有界查看文件名：

```bash
python scripts/ingestion_workspace.py files <case-id> <source-id> \
  [--glob '<pattern>'] [--limit 100]
```

先查文件名或命中文件，再读直接相关段落；宽泛检索必须限制输出，不能把整批标题或正文一次灌入上下文。不要从全量逐文件精读开始，也不要在手写文本中重新猜测来源数量。

每次实际读取或决定排除一组文件后更新覆盖账本：

```bash
python scripts/ingestion_workspace.py mark <case-id> <source-id> \
  --status <read_full|read_targeted|excluded|duplicate|unread_blocked> \
  --reason '<为何这样处理>' \
  [--evidence '<文件#标题或代码符号>'] \
  [--path <relative-path> | --glob <pattern> | --all-unreviewed]
```

`read_full`/`read_targeted` 必须给实际定位；排除必须给与本轮目标相关的理由。将来源区分为当前实现、历史快照、目标设计、人工决定、原始记录和生成综合，并在 `inventory.md` 记录能证明、不能证明、冲突、时效与实际读取策略。无法安全回答的事项写入 `questions.md`，不以常识补齐。

完成条件：每个机器清单文件都有处理状态；每个纳入结论可回到直接定位；关键冲突、未知和未读范围均可见。没有有效知识时保留工作台并停止，不发布空洞总结。

## 3. 按完成契约编织候选

先用 `completion.yaml` 逐项决定本轮必须覆盖、明确未知或不适用的内容，再提出知识结构：

1. 为每个稳定主题选择一个规范页面，同一核心定义只保留一份；为需要长期引用的来源建立来源记录；
2. 按 `config/knowledge-domains.yaml` 确定领域归属，从上级位置和边界展开到当前主题。新增或改变领域时，在 `review.md` 展示 ID、唯一上级、范围、排除项和目录差异，未经批准不修改正式地图；
3. 若材料涉及流程，讲清角色、状态、异常和返工；涉及数据，讲清标识、口径和输入输出；涉及软件或代码，连接业务动作、组件、接口、运行链路和实现入口；涉及规则或算法，保留输入、输出、不变量、步骤、边界和失败行为；
4. 跨领域或公共能力只保留一个规范落点，领域页说明真实使用契约；证据不足时明确未知，不为凑全貌虚构；
5. 层级、流程、多组件协作、时序或算法仅靠文字不易理解时，提供 Mermaid 图和文字说明；确实不需要图时在 `completion.yaml` 说明理由；
6. 使用标准 Markdown 相对链接。禁止 `[[Wiki Link]]`、`file://`、本机绝对路径和无解释的关系标签；
7. 首批知识同步形成领域位置视图和旅程/学习视图。视图只保存位置、顺序、问题入口和下一跳，不复制规范事实；
8. 所有候选只写入 `draft/knowledge/` 和 `draft/config/`。

为每个 `completion.yaml` 维度填 `covered`、`unknown` 或 `not_applicable`；`covered` 必须指向真实候选页，后两者必须说明理由。

完成条件：目标读者能沿产品视图取得约定结果；每个内容维度都有证据或显式边界；当前、历史、目标、人工决定和未知没有混写。

## 4. 交给人工审查

从根 `review.md` 提供唯一审查入口，链接 `brief.md`、`source-summary.md`、`inventory.md`、`questions.md` 和 `completion.yaml`，并把变更分成：

- 可以发布：直接证据充分且没有语义冲突；
- 需要选择：来源冲突、领域归属、公共能力抽取或定义替换；
- 需要补充：缺当前事实、范围、责任人或实现证据；
- 建议忽略：重复、过时、派生或与目标无关。

运行整个工作台门禁：

```bash
python scripts/ingestion_workspace.py check <case-id>
```

它同时检查来源是否变化、文件覆盖、固定入口、内容完成契约、图表声明、审查链接、正式知识零变化和候选知识 Bundle。检查通过只表示候选可以交给人审，不表示知识真实或充分。

最终消息只链接根 `review.md`，说明正式知识未修改并暂停；不要手工拼接多个深层绝对路径。

完成条件：工作台门禁通过，用户可以从一个入口检查来源、范围、候选、未知和待决定项；没有批准时正式知识零变化。

## 5. 发布并立即消费

只应用用户批准的项目，更新规范页、来源记录、产品视图、索引、日志和已批准的领域地图。运行：

```bash
python scripts/knowledge_check.py
```

展示 `git diff -- knowledge config` 并确认来源未变化。检查失败时回滚本次正式发布整组差异，保留工作台证据。

发布后从根 `knowledge/index.md` 沿产品视图完成一次真实浏览或问题消费，记录实际读取页面、引用来源、未知、误解和无法回答项。只有发布、人工批准、只读检查和真实消费都完成，才报告摄入完成。

## 模板

- 根工作文件：`assets/brief.md`、`inventory.md`、`questions.md`、`completion.yaml`、`review.md`
- 候选知识：`assets/knowledge-page.md`、`domain-overview.md`、`source-record.md`
- 产品视图与公共能力：`assets/product-view.md`、`shared-capability-review.md`
