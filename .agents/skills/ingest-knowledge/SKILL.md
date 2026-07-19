---
name: ingest-knowledge
description: >
  将一组有界的混乱文档、代码、导出材料或人工说明摄入为可浏览、可追溯、可维护的规范知识。
  当用户要求整理、导入、摄入、归并一批材料，建立或更新领域知识、来源记录和产品视图时使用；
  不用于只回答一个问题、直接改代码或无来源的自由创作。
---

# 知识摄入

把来源当作证据，把 `knowledge/` 当作唯一发布面，把
`workspaces/knowledge-ingestion/<case-id>/` 当作发布前工作台。一次摄入只有在规范知识、来源记录、产品视图、人工批准和只读检查同时完成后才完成。

## 1. 打开摄入案

1. 从用户请求提取材料位置、期望结果和不能做错的事项；只有缺失信息会改变范围、权威或发布结果时，最多追问一次。
2. 读取 `knowledge/index.md`、`config/knowledge-domains.yaml`、相关产品视图和已有规范页；不要先遍历整个知识库。
3. 记录 `git status --short`。只读取用户明确指定的来源，不搜索同级项目、历史聊天、旧答案或其他未声明材料；需要扩展范围时先说明原因并取得同意。来源仓库保持只读；若是 Git 来源，记录 commit 和工作区状态，不切换分支、不安装工具、不修改来源。
4. 创建 `workspaces/knowledge-ingestion/<case-id>/`，从 `assets/brief.md`、`inventory.md` 和 `questions.md` 建立工作文件。

完成条件：`brief.md` 能独立说明目标、范围、禁区、来源位置和基线；已有知识入口与本轮材料边界已经明确。

## 2. 盘点来源

按 `brief.md` 的问题有界阅读材料，不逐文件机械总结。把每个来源登记到 `inventory.md`：

- 区分当前实现、历史快照、目标设计、人工决定、原始记录和生成综合；
- 记录能证明什么、不能证明什么、实际读取范围和权威边界；
- 识别字节重复、语义重复、冲突、过时和缺失；
- 为需要长期引用的来源起草 `assets/source-record.md`；
- 将无法安全回答的事项写入 `questions.md`，不以常识补齐。

如果没有找到有效知识，保留盘点和缺口并停止发布；请求具体来源、系统或人员补充。没有产出知识不是失败，发布空洞总结才是失败。

完成条件：每个纳入候选都能回到直接来源；每个关键冲突、未知和未读范围都已显式登记。

## 3. 编织候选

先提出结构，再写内容：

1. 为每个稳定主题选择一个规范页面；同一核心定义只保留一份。
2. 使用 `config/knowledge-domains.yaml` 确定主要领域归属。需要新增或改变领域时，在 `review.md` 展示 ID、唯一上级、范围、排除项和目录差异，未经批准不修改正式地图。
3. 从 `assets/knowledge-page.md`、`domain-overview.md` 编写候选页。规则和算法必须保留输入、输出、不变量、步骤、边界、失败行为和实现入口。
4. 用标准 Markdown 相对链接表达跨页关系，并在链接所在句子中说明业务含义和边界。禁止 `[[Wiki Link]]`、`file://` 和本机绝对路径。
5. 同步起草产品视图。首批知识至少需要领域位置视图和用户旅程/学习视图；使用 `assets/product-view.md`，只保存位置、顺序、问题入口和下一跳，不复制规则正文。
6. 相似机制出现在多个领域时，先使用 `assets/shared-capability-review.md` 比较共同核心与领域差异。第二个消费者只触发审查；没有独立输入、输出、不变量、失败边界和维护责任时，不抽取公共能力。
7. 所有候选写入工作台的 `draft/knowledge/` 和 `draft/config/`，不写正式目录。

完成条件：每个候选页有唯一规范落点、来源、现实形态、适用范围和视图入口；公共能力与领域使用契约没有混写。

## 4. 提交人工审查

从 `assets/review.md` 生成唯一审查入口，按以下四类列出变更：

- 可以发布：直接证据充分且没有语义冲突；
- 需要选择：来源冲突、领域归属变化、公共能力抽取或会替代现有定义；
- 需要补充：缺当前事实、范围或责任人；
- 建议忽略：重复、过时、派生或与目标无关，并说明理由。

对候选目录运行：

```bash
python scripts/knowledge_check.py \
  --knowledge-root workspaces/knowledge-ingestion/<case-id>/draft/knowledge \
  --domain-map workspaces/knowledge-ingestion/<case-id>/draft/config/knowledge-domains.yaml
```

展示审查页和检查结果后暂停。用户可以整体批准低风险项，但语义冲突、领域地图变化、公共能力抽取和正式发布必须有人决定。

完成条件：用户明确批准、拒绝或保留每个会改变正式知识语义的项目；没有批准时正式知识零变化。

## 5. 发布获准内容

只应用获准项目：

1. 写入 `knowledge/domains/`、`knowledge/capabilities/`、`knowledge/systems/` 和 `knowledge/sources/`；
2. 同步更新 `knowledge/views/`、根 `knowledge/index.md`、相关目录 `index.md` 和 `knowledge/log.md`；
3. 需要时应用已批准的 `config/knowledge-domains.yaml` 变更；
4. 运行 `python scripts/knowledge_check.py`；
5. 展示 `git diff -- knowledge config`，确认来源仓库没有变化。

检查失败时恢复本次正式目录的整组发布差异，保留工作台与失败记录；不要在半发布状态继续叠补丁。

完成条件：只读检查通过，Git diff 与批准项一致，所有规范页可以从产品视图经标准 Markdown 链接到达。

## 6. 立即消费

从根 `knowledge/index.md` 沿产品视图完成一次人类浏览路线，并交付可直接点击的入口、推荐阅读顺序、已知范围和当前未知。用户提出真实问题时，只沿产品视图和最低充分规范页回答；记录实际读取页面、引用来源、明确未知、误解和无法回答项。

只有同时满足以下条件才报告摄入完成：

- 规范知识、来源记录和两种首批产品视图均已发布；
- 关键规则和算法没有被压缩成空泛摘要；
- 历史、目标、当前实现、人工决定和未知没有混写；
- 人工批准与只读检查均通过；
- 用户可以从根入口找到并使用知识。

真实内容质量只能由后续实际使用证明。结构检查通过不得表述为知识已经正确或能力已经验证。

## 模板导航

- 任务边界：`assets/brief.md`
- 来源盘点：`assets/inventory.md`
- 开放问题：`assets/questions.md`
- 规范知识页：`assets/knowledge-page.md`
- 领域说明页：`assets/domain-overview.md`
- 来源记录：`assets/source-record.md`
- 产品视图：`assets/product-view.md`
- 公共能力抽取审查：`assets/shared-capability-review.md`
- 人工审查入口：`assets/review.md`
