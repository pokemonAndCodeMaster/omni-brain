# 共作 v03 使用与运行

## 入口与事实

从应用首页进入“我的工作”，工作事项详情包含概览、共享上下文、成果与验证、推进记录和复盘与成长。
灵感可以直接保存并讨论；个人学习、研究等工作无需先走研发流水线。
工作事项可以服务多个专题，关系编辑保存语义而非复制任务。组会从同一事实生成按议程组织的阅读视图。

事项、上下文、讨论、会议、运行及发布记录存于本应用 PostgreSQL。浏览器不会把一份 localStorage
演示状态当成正式事实。新数据库没有示例业务对象，并提供默认周回顾/组会议程；历史 S0 Requirement 由 migration 008 带来源身份迁移到团队事项。
旧 `/ai` 入口保留历史，`/manual-qc` 保留质检能力。

具体产品输入和 U1—U12 验收：
[唯一审查记录](../../../workspaces/reviews/team-workbench-product-definition/review.md)。

## 启动

在应用目录使用现有启动方式：

```bash
scripts/postgres.sh init
.venv/bin/python -m src.cli migrate
.venv/bin/python -m uvicorn src.api.app:create_app --factory --host 127.0.0.1 --port 8000
```

另一个终端在 `src/frontend` 运行 `npm run dev`。默认前端 `5173`，代理指向 `8000`。
临时验证可通过 `VITE_API_PROXY_TARGET` 和 Vite `--port` 改端口，不改变受版本管理的默认值。
已有数据库先备份；本次不要求运行 `seed`，该命令是旧质检实验数据初始化入口。

## 个人与团队配置

`.env.example` 列出配置。个人与团队实际部署各使用独立数据库、知识根目录、执行凭证与 Worker。

| 配置 | 含义 |
|---|---|
| `GONGZUO_WORKSPACES` | 本地比较可为 `personal,team`；单独部署设 `personal` 或 `team`，服务端拒绝另一空间 API |
| `GONGZUO_PERSONAL_KNOWLEDGE_ROOT` | 个人 Markdown 根目录，默认独立空目录 `.runtime/gongzuo-knowledge/personal` |
| `GONGZUO_TEAM_KNOWLEDGE_ROOT` | 团队知识根目录，默认本仓 `knowledge/published` |
| `GONGZUO_PERSONAL_REGISTRATION_TOKEN` | 个人节点注册凭证，未配置时明确拒绝注册 |
| `GONGZUO_TEAM_REGISTRATION_TOKEN` | 团队节点注册凭证，与个人凭证分别配置 |

当前沿用本地 `admin` 身份，并未接入公司 SSO 或完整成员权限管理。默认仅监听回环地址；
单独工作区配置提供数据范围边界，不等同于成员身份认证。内部 CodeHub 状态/API 与公司镜像需要实际连接后验证，保存链接不代表同步已经发生。

## 执行节点

工作事项先保存当前共同上下文，再委托 Codex/OpenCode。每次 Run 固定事项、上下文版本、原生会话、
环境及能力版本；同步新共识生成新尝试，旧尝试的依据保留。运行成功只表示执行器正常结束，业务结果
还需查看实际证据并接受。

节点通过 `/api/gongzuo/{workspace}/machines/register` 注册，传 `X-Gongzuo-Registration-Token`。
注册返回一次 `workerToken`，中心数据库只保存其哈希。后续节点使用 `X-Gongzuo-Worker-Token` 接单和心跳；
列表不显示凭证。维护中心可以暂停接单或等待当前工作结束后排空。

注册字段示例（不含真实凭证）：

```json
{"name":"我的 WSL","capacity":1,"engines":["codex"],"runtimes":["native"],"images":[],"labels":{}}
```

在节点通过安全的进程环境提供 `GONGZUO_WORKER_TOKEN`，然后运行：

```bash
python -m src.gongzuo_runtime.worker \
  --server http://127.0.0.1:8000 --workspace personal \
  --machine-id <注册所得ID> --runtime-root /本机隔离目录 --capacity 1
```

委托表单可指定模型；留空沿用节点配置。本次实测个人 Codex 使用 `gpt-5.6-luna`，具体可用模型取决于节点 CLI 和账号。

Worker 复用既有执行器适配器，独立准备检出目录、HOME 和会话数据。现有原生执行器的认证/模型配置
须在对应工作区的执行节点设置；中心不会把个人认证发送给团队。Docker 模式检测 Docker 和镜像，
缺失时回报不可用，不退化成未说明的宿主运行。

可用仅当前用户可读的 `--credential-file` JSON 保存注册所得 `workspace`、`id`、`workerToken`，
替代在命令行中传凭证。中心与节点仓库目录不同，用 `--repository-map` 指定 JSON 映射：
键为中心登记的仓库身份路径，值为工作站已有检出的路径；节点验证固定提交确实存在后才接着执行。

个人节点可以复用本机认证。团队节点必须显式设置 `GONGZUO_TEAM_CODEX_HOME`，或 OpenCode 的
`GONGZUO_TEAM_OPENCODE_DATA_HOME` 与 `GONGZUO_TEAM_OPENCODE_CONFIG_HOME` / `GONGZUO_TEAM_OPENCODE_CONFIG`。
缺失时返回不可用，不回退到个人 HOME。团队执行进程也不会默认继承个人 provider 密钥；确需传入
团队专用变量时，用 `GONGZUO_TEAM_ENV_ALLOWLIST` 明确列出，并由团队自己的进程环境供给。

终止、失联和失败都会保留状态与原因；中心不可把恢复中的运行改成成功。
文本结果可通过 `/api/gongzuo/{workspace}/runs/{id}/artifacts/result` 打开，带内容版本；
远程文件路径只是定位信息，不自动声称中心能够读取所有文件。

## 知识修订与能力采用

知识页读取实际 Markdown，记录路径、原文内容哈希和当前发布身份。只读来源也允许提出修订。
原始材料不混入当前规范知识目录；路径跳出配置目录和跨目录符号链接会被拒绝。

能力候选记录期望行为与验证办法，可试验知识、Skill、Agent 指引或 Harness 指引。试验 Run 必须显式
选择候选，固定其内容和版本。接受候选的验证记录要求同一候选版本的真实成功运行，以及该运行已人工接受的
证据，并写清判断；随后才可发布。失败或不可用的试验也可记录拒绝结论，不能据此发布。工具安装、环境镜像变更、模型替换仍需对应真实实现和评测，不能
把一段文字发布冒充这些动作。

当前发布由工作台维护受审版本，新委托通过同一解析入口采用：知识物化为运行引用文件，Skill 保持
原始 SKILL.md 结构，Agent/Harness 内容作为具名运行指引。页面区分 `git-file` 和 `workspace-release`。
知识来源文件保持原样，发布内容不会悄悄覆盖 Git 或 `knowledge/raw`；来源变化会显示复核提示并阻止
旧候选发布；来源变化后，该旧发布也暂不自动加入新运行，待复核。正式回写 Git 知识包需按已有受审知识流程进行，不把工作台运行层发布当作已提交的规范变更。

## 会议

实时预览、浏览器演示和 Markdown 导出消费同一服务端呈现规则。首次出现的事项完整呈现，其他
板块折叠重复进度，同时保留独立业务决定。冻结保存配置、选入的事实与呈现结果；后续修改不会
漂移历史快照。决定和后续事项关联回原工作，导出标明时间与来源。

## 回滚与验证位置

代码按 Git 提交回退。新增数据表与旧质检数据表分开；回退前保留数据库与运行产物备份，不能仅删表
丢弃用户数据。能力发布保存旧版本与运行快照，可用明确的新候选恢复旧内容并再次验证发布。
临时验证工作树、数据库、进程和私密凭证仅属于本次 Trial；其审查证据归档后回收，不作为并列产品入口。

测试入口：后端 `python -m pytest tests`；前端 `npm test`、`npm run type-check:gongzuo`、`npm run build`。
`npm run type-check` 现在真正检查整个应用；原主线已有的 40 条类型诊断单独记录于审查证据，本次不将局部检查称为全量通过。
真实页面、原生 Worker、
会议快照与能力闭环的具体结果，以审查记录中的逐项证据为准。
