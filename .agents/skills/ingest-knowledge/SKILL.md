---
name: ingest-knowledge
description: >
  摄入一批有界的文档、代码、Schema 或人工材料，把它们整理为可浏览、可追溯、可继续工作的规范知识与产品视图。
  当用户要求整理、导入、摄入或归并材料，或用新材料更新现有知识时使用；不用于只回答一个问题、直接改代码或无来源创作。
---

# 知识摄入

以**问题闭环**推进：一个读者问题，一小批直接来源，一至三篇规范知识，一次可检查的结果。来源盘点和状态由工具在后台维护；主要精力必须用于理解、写知识和真实验证。

来源保持只读，候选只写入 `workspaces/knowledge-ingestion/<case-id>/draft/`。用户批准前不得修改正式 `knowledge/` 或 `config/`。

## 1. 建立读者问题

从用户请求中提取：授权来源、目标读者、读完后要解决的问题，以及不能做错的边界。范围已经清楚时不要追问。

把复合目标拆成读者实际会问的问题。问题必须能够用知识回答或明确说明缺口，不能写成“整理全部材料”之类工作动作。随后启动摄入案：

```bash
python scripts/ingestion_workspace.py start <case-id> \
  --goal '<读者最终能够理解、判断或执行什么>' \
  --reader '<目标读者>' \
  --source <source-id>=<authorized-directory> \
  --question '<读者问题>' [--question '<下一个问题>'] \
  [--boundary '<不能做错的边界>']
```

继续已有摄入案时，先运行：

```bash
python scripts/ingestion_workspace.py status <case-id>
```

只恢复当前问题、知识落点、候选数量、运行结果和下一动作；不要读取 `.state/source-manifest.jsonl` 或手工编辑 `.state/case.json`。

**完成标准：** 用户目标没有被焦点材料悄悄缩窄；每个问题都对应真实阅读或工作结果；来源与禁止事项已经明确。

## 2. 规划当前知识单元

只为当前问题规划一至三个会被独立阅读或维护的规范落点：

```bash
python scripts/ingestion_workspace.py plan-unit <case-id> <question-id> <unit-id> \
  --title '<知识单元标题>' \
  --kind <business|data|software|run|other> \
  --path 'draft/knowledge/<area>/<page>.md' \
  [--require-run]
```

按独立变化划分，而不是按模板凑页：事实源、现实状态、更新节奏或读者任务不同，或者一种内容会淹没另一种内容时才拆开。一个问题需要超过三篇正文才能回答，说明问题或知识地图仍过宽，应先收束。

写第一篇规范页时读取 [knowledge-page.md](assets/knowledge-page.md)。涉及领域全貌时再读 [domain-overview.md](assets/domain-overview.md)；涉及软件实现时再读 [software-architecture.md](assets/software-architecture.md)。不要在开始时读取全部模板。

**完成标准：** 当前问题有一至三个清楚的规范落点；需要 API、SQL、页面或数值证明的问题已经标记真实运行要求。

## 3. 取得一小批直接来源

围绕当前问题提供精确业务词、字段、接口、表名、类名或页面名：

```bash
python scripts/ingestion_workspace.py next <case-id> <question-id> \
  --query '<term>' [--query '<term>'] [--limit 6]
```

工具只返回当前 **1—8 份**候选及其用途，并补充直接 import 邻接；它不会向会话倾倒全库目录。只打开返回的 `absolute_path`，不要自行递归搜索授权来源。查询太宽或方向错误时，用新的精确词重新运行 `next`；当前小批未登记前不能再取下一批。

事实源优先级：

- 当前软件行为：源码、Schema、配置和新鲜运行结果；
- 当前业务语义：人工决定、业务原始记录和当前口径；
- 目标方案与历史做法：分别标明，不能伪装成当前实现；
- 综合文档与旧知识：用于定位和发现冲突，不能替代其指向的直接来源。

代码问题至少沿真实业务动作连接适用部分：

```text
页面或命令入口
→ 状态与交互
→ API 与类型
→ 路由、服务和数据访问
→ SQL、Schema 与口径
→ 返回转换、渲染和样式
→ 运行与验证入口
```

这不是固定文件清单。某层不适用可以省略；缺失且会改变答案时继续补证据，不能让总览页代替中央实现。

**完成标准：** 当前小批每份来源都预计改变问题的一部分；没有因为文件名像答案就跳过更直接的实现或业务来源。

## 4. 立即形成知识并登记结果

读完当前小批后立即更新规范知识，不要连续囤积来源。正文必须充分内化：解释输入、转换、输出、条件、边界、失败方式和继续工作入口；引用只负责追溯，不能代替内容。

建立来源记录时读取 [source-record.md](assets/source-record.md)。每篇规范页使用标准 Markdown 相对链接回到来源记录，并区分当前实现、当前业务决定、目标设计、历史快照和开放问题。

完成正文后登记本批结果：

```bash
python scripts/ingestion_workspace.py record <case-id> <question-id> \
  --status <answered|partial|external_missing|conflict> \
  --summary '<规范知识当前能回答什么>' \
  --source '<source-id>:<path>' \
  --knowledge 'draft/knowledge/<area>/<page>.md' \
  [--missing '<还缺什么>'] \
  [--dismiss-unused '<当前小批其余项为何不改变答案>'] \
  [--close-candidates '<为什么可以停止继续取源>'] \
  [--next-action '<下一动作>']
```

状态含义：

- `answered`：规范知识已经能够独立回答；
- `partial`：已有可用局部，但还缺会改变结论的内容；
- `external_missing`：库内没有合理候选，缺失事实必须由外部系统或责任方补充；
- `conflict`：直接来源不兼容，需要人决定。

“没有读到”不等于“外部缺失”。相关候选仍在队列时，工具拒绝结束；停止继续取源必须用问题级理由说明，而不是给全部未读文件逐项分类。

**完成标准：** 当前来源带来的机制和边界已经进入规范页；状态、缺口、知识落点和下一动作一致；会话此时中断也能从 `status` 恢复。

## 5. 取得真实运行证据

知识要支持运行、调试、SQL、页面或数值判断时，静态阅读不够。先把来源项目自己的操作说明、环境声明、启动脚本和真实入口作为当前问题的一批直接来源，随后在临时 Git worktree 执行：

```bash
python scripts/ingestion_workspace.py run <case-id> <question-id> \
  --source-id <source-id> \
  --kind <health|api|sql|page|other> \
  --purpose '<这次运行准备证明什么>' \
  --command '<可直接执行的完整命令>' \
  [--mount '.venv'] [--mount '<项目声明的本地运行目录>'] \
  [--artifact '<需要保留的相对路径>']
```

工具固定来源提交，在临时 worktree 运行并保存命令、输出和 artifact；原来源代码不被修改。只复用项目已经声明的环境，不安装依赖、不切换系统 Python、不连接未授权环境。

软件纵切通常依次取得 health、固定 API、同范围 SQL 和页面证据。比较值时所有环节必须使用同一筛选范围；页面默认日期与数据库全量范围不同，不能据此宣布数值错误或一致。

把运行结论写回规范知识：说明输入范围、实际输出、环境身份和不能外推的边界。Harness 自身测试不能冒充来源项目运行结果，失败运行也不能写成已验证。

**完成标准：** 需要运行证明的问题至少有一项通过的隔离运行；关键数值或行为能够在声明范围内复现，失败则有具体阻塞而不是假想命令。

## 6. 收完一个问题

知识形成后读取 [product-view.md](assets/product-view.md)，同步建立领域位置视图和旅程/学习视图，分别保存到 `draft/knowledge/views/by-domain/` 和 `draft/knowledge/views/by-journey/`。视图提供位置、阅读路线和问题入口，链接规范知识，不复制另一套事实。

运行：

```bash
python scripts/ingestion_workspace.py check-unit <case-id> <question-id>
```

它检查：计划知识是否形成、是否能从产品视图到达、相关候选是否已经处理或说明停止理由、直接依据是否存在、要求的真实运行是否通过，以及已回答页面是否仍残留“待核实/待补充”。结构问题回到对应知识页修复，不能靠改状态掩盖内容缺失。

**完成标准：** `check-unit` 通过；读者从产品视图和最多三篇规范页能够回答原问题；可靠局部、外部缺失和冲突边界都清楚。

## 7. 人工审查与发布

所有当前问题形成可用结果后运行：

```bash
python scripts/ingestion_workspace.py review <case-id>
```

只把根 `review.md` 交给用户。它链接候选知识和产品视图，汇总问题结果、真实运行及需要人工决定的事项；不要再生成平行答案页或完成度表。

用户批准后才把候选知识合并到正式目录，更新知识入口、来源记录、领域地图和日志，并运行：

```bash
python scripts/knowledge_check.py
git diff -- knowledge config
```

最后从正式 `knowledge/index.md` 完成一次真实浏览或问题消费。结构检查通过只说明链接和格式成立，不代表内容正确；人工批准、正式发布和真实消费全部完成后才能报告摄入结束。

**完成标准：** 用户只需审查知识、视图和 `review.md`；正式变更可追溯、可回滚，发布后的知识能够直接用于下一次学习、查询或开发。

## 护栏

- 不手工编辑 `.state/`，不把机器 manifest 当作用户产物。
- 不恢复逐文件 `mark`、覆盖率或“所有文件必须分类”的完成方式。
- 不用模型常识补关键业务事实，不把目标设计写成当前实现。
- 不在原来源代码目录运行会写文件的命令；隔离运行仍须遵守来源项目自己的安全边界。
- 公共能力只有出现真实复用、共同契约和明确维护责任时才读取 [shared-capability-review.md](assets/shared-capability-review.md) 并提出抽取，不因名称相似自动合并。
