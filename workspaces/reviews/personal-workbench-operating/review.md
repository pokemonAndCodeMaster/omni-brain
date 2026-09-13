# 个人工作台交付说明

日常侧栏已收简为领域总览、工作阶段、优先级与计划三个入口，四个旧快捷视图移出收藏但保留原链接。七个 View 的实际成员、三个收藏及顺序已验证；四象限标签与按周排期已配置。项目、标签有效显示仍为隐藏，原生浏览器交互未验收，YYH-12 保持进行中。具体新结果见[简化视图证据](../../../eval/trials/integrations/LINEAR_SIMPLE_VIEWS_20260913/README.md)。下方早期五视图记录保留其历史验证范围，当前配置以新证据和线上用法为准。

本轮将现有领域标签归入“领域”，新增“事项类型”分组并为真实事项标记想法、需求或任务；保留原标签 ID、其他标签与进度状态。工作台项目 Overview 已改成能力、可用范围和操作例子的总览；原入口文档保留说明与 Agent 约定。[日常视图方案](https://linear.app/yyhpokemonmaster/document/a43b2877e7d9)维护当前三个主入口、四个快捷视图和核对结果，以及文档不能直接参加 Issue View 标签筛选的边界。方案在线原位维护，不另建报告副本。

## 从哪里使用

从侧栏三个收藏进入：[领域总览](https://linear.app/yyhpokemonmaster/view/31f2c0ec-56c6-44ca-99b3-65a04f666e7f)、[工作阶段](https://linear.app/yyhpokemonmaster/view/5e7379f4-e21d-4272-8869-1efaa4f4cdd3)、[优先级与计划](https://linear.app/yyhpokemonmaster/view/5342c3bf-41e8-4c87-878d-ecba161e03d4)。想法、待确认、以后安排、近期成果四个快捷视图继续可从 Views 或[用法说明](https://linear.app/yyhpokemonmaster/document/a43b2877e7d9)打开。均查看 YYH 团队分配给本人的事项，跨项目和领域。
[工作台项目](https://linear.app/yyhpokemonmaster/project/个人工作台日常使用与持续推进-a2184ae8c325)的 Overview 看现在能做什么和怎样用，Issues 看建设进度；[原入口文档](https://linear.app/yyhpokemonmaster/document/abed03cc1da2)保留使用说明和 Agent 接续约定。
[完整文档目录](https://linear.app/yyhpokemonmaster/document/736bd2d7d4bb)覆盖当前可访问的团队、事项和项目文档；[已有知识与能力](https://linear.app/yyhpokemonmaster/document/43d261329834)按金铲铲、质检、共作、技能和历史实验进入原文。
本地浏览器打开 `.derived/personal-workbench/index.html`，可以搜索中文全文、按场景与领域选择，在同一页阅读并复制接续口令。生成和更新见 [README](../../../docs/linear-workbench/README.md)。
也可以直接从 [YYH-12 附件](https://linear.app/yyhpokemonmaster/issue/YYH-12)下载 HTML 后打开；上传后重新下载，1,344,326 字节与 SHA-256 均一致。最终快照通过真实桌面和手机浏览，[最终页面证据](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/personal-workbench/final-browser-check.json)记录对应文件指纹。

现有工作台事项归入一个项目，三个里程碑分别承接找到材料、接续工作和留下成果。YYH-9 至 YYH-14 的正文和关联结果已原位重写；新建 YYH-15 跟踪并修复共作问题，YYH-16 保留 Spider 复用审查。YYH-7 更正重复项引用，仍跟踪缺失历史文件；当前金铲铲攻略未被导航整理覆盖。

## 实际结果与验证

| 使用结果 | 实际证据与范围 |
| --- | --- |
| 五个原生事项 View 与收藏可供直接打开 | 官方 API 保存后逐项回读，真实命中条数为 9、0、1、2、5，与独立读取的本人事项判断一致；再次执行保留五个 View 和收藏 ID、顺序。[API 证据](../../../eval/trials/integrations/LINEAR_NATIVE_VIEWS_20260913/verified.json)。这是 API 层验证，显示列差异与默认首页单列保留。 |
| 新 Codex 不需要编号也能找到工作 | 在另一独立 Git 项目新开会话，自动发现用户级技能，找到 YYH-12 并读取全文；普通 Python 问题不触发工作台。[行为记录](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/codex-entry/evidence.json) |
| 来源和阅读材料变化可以发现 | YYH-11 的真实 MCP 读取成功组装为事项、项目与四篇文档全文；包不代替线上当前记录。离线独立复核覆盖分页不全、漏材料、错误归属、错链接、文件删改和版本变化。[独立报告](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/context-final-review/report.md) |
| 全文目录和页面可以实际浏览 | 完整目录生成保留阅读路线，拒绝不完整清单；Chromium 检查中文检索、正文、关系跳转、窄屏和复制失败备用方式。[页面记录](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/personal-workbench/browser-check.json) |
| Git 文档原位发布并检查冲突 | 四篇说明登记唯一源，plan → MCP save → get → receipt 已执行并回读；旧远端指纹不直接覆盖，重复发布无变化跳过。发布记录在 config/linear-workbench.json |
| 共作子事项交给 AI 不再传错父目标 | 页面实际 POST 传子事项 ID；真实服务生成子目标与父背景，父背景更新影响新运行，旧输入保持固定。[运行与页面证据](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/gongzuo-child-delegation/verification.json) |

最终页面检查还修正了两处阅读语义：Todo 属于准备推进，Backlog 才是未安排；Linear 的原生事项标签转换为正常链接。转换仅接受纯引用，保留代码示例并拒绝额外标记和会改变目的事项的路径。独立复核发现的两个边界已修正后定点复验；已上传快照的全部 56 段正文与最终渲染器一致。

工作台 42 项检查已通过：发布与目录 16、入口安装 6、阅读页 8、上下文 12。最后一次组合运行发现旧测试项目缺少 URL；补齐有效输入，并加入错误工作区的拒绝断言后，受影响 12 项重跑通过。其余 30 项此前同次运行通过。
共作相关前端 9 项、后端 28 项、局部类型检查和生产构建通过。浏览器使用隔离 API 数据，同一请求交给真实服务与内存 Repository；未重新验证用户 PostgreSQL 或调用外部 AI。
系统默认 Python 没有 pytest，工作台使用其 stdlib unittest 入口；这不是忽略失败测试。

本次原生 Views 维护新增 10 项 stdlib 检查，覆盖查重与身份、丢失写响应、筛选边界、分页、凭据文件、收藏顺序、偏好保留和读写重试差异。独立复核发现旧字段被漏读后已修复，新上下文用官方 Schema 的严格投影确认非本功能偏好保留；真实 API 完整偏好读取也成功。具体通过范围、失败与复验记录在 [Views 证据](../../../eval/trials/integrations/LINEAR_NATIVE_VIEWS_20260913/README.md)，不将离线复核当成浏览器验收。

## 明确未完成的范围

当前七个原生视图的保存偏好已回读；项目、标签两列保存为显示，但 API 最终显示值为隐藏。默认首页未设置；没有已登录的原生浏览器控制，侧栏点击、列显示和状态改变后的页面行为仍未独立核验。不能把 API 回读当成人工界面验收。

知识分类也不能通过给文档标题加前缀或借用 Issue 标签来冒充原生功能。已有离线 HTML 保留为其抓取时的历史快照，包含旧状态；它的浏览器验证不证明现在的 Linear 界面符合用户预期。知识分类与阅读体验继续由 YYH-12 跟踪。

新的非交互 Codex 会话读取成功，但 save_document 被工具审批要求拒绝（该次 codex exec 为 read-only、审批策略 never）；失败后完整回读确认未写入。[失败与读取证据](../../../eval/trials/integrations/PERSONAL_WORKBENCH_20260912/codex-entry/write-evidence.json)。没有修改安全配置来绕过拒绝。YYH-11 保持 In Progress，交互式正常审批下的新会话写回仍需验证；本会话已有写入成功不替代这一结果。

用户已报告在 ChatGPT 个人自定义指令加入入口，但没有独立验证 ChatGPT 新会话或其他机器。无 Linear 工具的环境不能读写线上，已有长会话不保证热更新。当前没有后台巡视、执行或自动同步。MCP 不提供 View 操作，本次由官方 GraphQL API 补充；API 密钥只在本机私有文件保存，没有修改 MCP OAuth 或整个工作区的默认首页。

金铲铲当前正文已纳入阅读，原 ChatGPT 历史对话、图片、HTML/ZIP 和模型未全部取得，继续由 YYH-7、YYH-8 分别维护材料迁移与当前教学。Spider 归档入口已登记，复用决定在 YYH-16；没有把整分支当成当前可运行能力。

## 知识、代码与技能怎样联动

共享工作方法只维护在 docs/linear-workbench/issue-lifecycle.md；AGENTS 留短入口，personal-workbench Skill 负责选择原事项和相应知识、讨论、开发、整理或审查方法。原有技能继续复用，没有为每个阶段新建一个 Agent。

本次知识变更仅为导航层：新目录链接现有原文、在 knowledge/index.md 登记并记录日志；raw 原料、taxonomy 和规范卡事实未改。新导航不意味着认证了旧实验。变更可通过撤回导航提交回退，原材料无移动或重命名。

代码和方法变化保留提交与真实案例。独立检查曾发现评论中的新材料被遗漏、阅读文件删改未检出、项目链接跨工作区等问题；已修正并保存失败与复验，没有只归档成功结果。用户当前授权决定执行范围，文档和评论不扩大授权。

## 安装与回退

用户级 Skill 链接由安装器切回正式仓，检查原文与链接保留；安装备份在用户目录，由安装器返回实际路径。重新安装、检查和恢复方法见 [Codex 入口](../../../docs/linear-workbench/codex-bootstrap.md)。
只提交本轮工作台及相关共作修复、导航和证据，主仓其他未提交修改保留。线上修改前重读、精确保存并回读；Git 源的回退也需检查线上差异再发布，不能用旧正文覆盖新的有效内容。
