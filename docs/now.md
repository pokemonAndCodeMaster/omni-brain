# 当前工作台

> 更新时间：2026-08-29
> 本页只回答：**现在到哪里、产物在哪里、下一步做什么**。完整用例与 Trial 看
> [Eval 总账](../eval/STATUS.md)，长期架构看 [Blueprint](blueprint.md)。

## 当前结论

**Agent 能力工作台已纠偏到现有质检一站式平台。** 实际宿主为
`/home/yyh/project/quality-platform-lab@feature/agent-workbench-opencode-v1`：前端复用 Vue3
`AppShell` 和 Router，Run 元数据与规范事件复用 PostgreSQL 公共层，执行器第一版只支持
OpenCode。本仓原 React/SQLite/Codex 控制服务已退役，只保留 Agent 注册表、评测资产与历史证据。

目录和列表已经按摘要/详情拆分：未点具体 Agent 或 Run 时不读取能力 limits、prompt、结果和
trace；只有已选择且活跃的 Run 每 8 秒读取详情与 `after_sequence` 增量事件。真实 Run
`run-20260829-154845-cd07a9` 已回填 worktree、session、最终文本和规范事件；4 条旧 OpenCode
历史已迁入 PostgreSQL，余额不足等具体原因完整保留。当前仍不使用 Docker，也没有内建鉴权、
多 worker 调度、远程工作站或评测/进化入口。实现边界见
[`agent-workbench-v0.md`](specs/agent-workbench-v0.md)。

**当前主线是 Spider 多源信息平台的真实实现与第二领域 Harness 验证。** 用户已经批准 Spider 的
R1/R2；认证参考归档为 `refs/eval/workspaces/spider-multisource-r2-certified-v1@73dfdd1`。参考实现已
完成双网站采集、统一配置、六表信息库、版本化迁移、FastAPI、Vue 浏览页、分类/收藏/偏好和导出，
并进入已推送的 Spider 分支 `feature/multi-source-information-platform-v1@6176afe`。原脏 `main`
没有被覆盖；可运行工作区位于
`/home/yyh/project/.omni-brain-runs/SPIDER_PRODUCT_INTEGRATION_V1`。

实现的关键验证包括：16,875 条旧帖子、130,647 张旧图片和 26,072 条去重下载的 PostgreSQL
迁移/降级/再升级对账；旧帖子 URL `tid` 与新采集身份逐条一致；13 项后端测试、Vue 类型检查和
生产构建通过；Chromium 完整快照、筛选、收藏、人工分类、CSV 与详情按需图片通过；南+公开板块
真实小批采集 `2/2`。2026-08-16 已对真实 `spider_db` 完成六表迁移和全量对账，并用自动刷新
的 Sehuatang Cookie 实采一条新帖子进入新表；旧表未变。受验证码保护的南+ `fid=4` 仍需要用户在
可见浏览器中人工完成一次登录，代码不会绕过验证码，也没有提交真实凭据。

统一 Harness 已发布到 `release/harness@7076817`。这次发布合入批准施工约束、下游效果验证、独立
交付复核、方案只读边界、按真实工作流划分服务，以及 OpenCode 的限知 R1 Agent；90 项回归通过。
Spider 三次弱模型方案 Trial 仍不能证明第二领域泛化：001/002 越界读取其他工作区，003 虽完成
Bubblewrap 隔离，但模型在 R1 前过读源码且首次无产物。限知 R1 Agent 因此只作为受控入口发布，
尚未升级为默认方案形成路径。

## 实际由什么组成

| 实体 | 作用 |
|---|---|
| `omni-brain-harness/AGENTS.md` | 在直接执行、有界上下文、先形成方案、按批准方案开发和事后审查之间路由 |
| `.agents/skills/form-solution/SKILL.md` | 先形成 R1 需求理解，再做最低充分查证并形成 R2 可施工方案 |
| `.agents/skills/form-solution/references/software-solution.md` | 复杂软件方案的系统位置、数据流、模块、接口、迁移、验证与决策结构 |
| `.opencode/agents/r1-requirements-reviewer.md` | 只凭原始诉求形成 R1，权限上禁止读取源码、配置、测试和历史 Trial；当前为受控入口 |
| `.agents/skills/develop-with-knowledge/SKILL.md` | 从批准方案提取施工约束，完成实现、真实验证和知识变化交接；候选新增强范围声明反例检查 |
| `.agents/skills/review-work/SKILL.md` | 把实际需求、方案、实现、验证和关闭条件组织进唯一审查页，防止边界与完成声明互相矛盾 |
| `workspaces/reviews/<task-id>/review.md` | 用户唯一需要阅读和反馈的本地审查入口 |

没有新增需求 YAML、方案账本、模型 API 或专题脚本。阶段状态和反馈都在同一张 Markdown
审查页中；事实仍来自用户请求、当前知识、源码和必要运行结果。

## Harness 架构收口

当前已完成现役组件编织与职责审计，详见 [Blueprint 4.1—4.3](blueprint.md#41-当前-release-的物理编织)：

- `task-knowledge-prep`、通用任务案账本及其旧来源快照已从 Release 退役；
- 设计仓负责参考、Trial 和晋升，Release 只负责模型实际运行；
- 方案、开发与软件审查通过同一张 `review.md` 交接，不再维护通用任务状态；
- 问答、方案和开发中重复的定向下钻被识别为 `gather-context` 候选，但尚未实现；
- 下一条真实开发同时记录取知问题、读取路径、停止点和遗漏，用来决定公共能力的最小接口，而不是先造新工作流。

## 结果去哪里看

- [用户批准的 R1/R2 认证参考](../workspaces/reviews/manual-qc-multidimensional-result-analysis/review.md)
- [冻结输入、反馈、评分和晋升规则](../eval/datasets/solution_formation/manual_qc_multidimensional_result_analysis_v1.yaml)
- [第一份独立通过候选](../eval/trials/solution_formation/SOLUTION_FORMATION_HARNESS_OPENCODE_DEEPSEEK_005/review.md)
- [第二份独立通过候选](../eval/trials/solution_formation/SOLUTION_FORMATION_HARNESS_OPENCODE_DEEPSEEK_009/review.md)
- [全部迭代、失败原因和适用边界](../eval/trials/solution_formation/audit.md)
- [开发评测与接受条件](../eval/datasets/development/manual_qc_multidimensional_result_analysis_v1.yaml)
- [开发第一轮审计](../eval/trials/real_work/MANUAL_QC_MULTIDIM_RESULT_OPENCODE_DEEPSEEK_001/audit.md)
- [开发第二轮审计](../eval/trials/real_work/MANUAL_QC_MULTIDIM_RESULT_OPENCODE_DEEPSEEK_002/audit.md)
- [开发第三轮审计](../eval/trials/real_work/MANUAL_QC_MULTIDIM_RESULT_OPENCODE_DEEPSEEK_003/audit.md)
- [Spider 方案形成用例](../eval/fixtures/solution_formation/spider_multisource_platform_v1/README.md)
- [Spider 评分候选](../eval/datasets/solution_formation/spider_multisource_platform_v1.yaml)
- [Spider 首轮基线](../eval/trials/solution_formation/SPIDER_MULTISOURCE_CODEX_TERRA_BASELINE_001/README.md)
- [Spider 认证 R1/R2 与实现审查页](/home/yyh/project/.omni-brain-runs/SPIDER_PRODUCT_INTEGRATION_V1/workspaces/reviews/spider-multi-source-platform-refactor/review.md)
- [Spider 隔离弱模型 Trial 003](../eval/trials/solution_formation/SPIDER_MULTISOURCE_SOLUTION_OPENCODE_DEEPSEEK_003/README.md)
- [Spider 可运行功能分支工作区](/home/yyh/project/.omni-brain-runs/SPIDER_PRODUCT_INTEGRATION_V1/README.md)

## 下一步

**当前动作是让 Spider 实现进入实际试用。** Agent 已完成独立分支、真实库迁移、旧数据对账和
Sehuatang 新表增量采集；下一项产品动作是启动 Web，确认旧数据浏览与页面入口。用户只需要在
认证采集 `fid=4` 前，通过可见浏览器人工完成一次验证码。

Harness 已先发布可复用改进，不再等待一个第二领域 Trial 才让其他项目获得收益。下一次有效
Trial 使用已发布的限知 R1 Agent，把第一阶段输入物理限制为原始请求和根入口；R1 通过后才由
默认 `form-solution` 路径定向开放源码。Trial 通过后只升级这项 Agent 的采用范围，不重新发明流程。

## 后续顺序

1. 启动 Spider Web，确认迁移后的旧数据浏览与页面入口；
2. 由用户完成南+ `fid=4` 的可见浏览器验证码登录，再跑认证板块小批采集；
3. 根据真实试用修正产品问题，并把最终架构、运行入口和变化回写进 Spider 知识；
4. 用分阶段可见性重新运行隔离弱模型方案 Trial，验证需求优先和 Service 责任边界；
5. 用 Spider 隔离 Trial 验证 `release/harness@7076817` 的限知 R1 Agent，再决定是否设为默认；
6. 回到人工质检多维结果开发保留项，不让其状态丢失，也不与当前 Spider 主线混在一起。
