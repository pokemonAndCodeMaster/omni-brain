# 独立上下文与目录复核

最终结果：**pass（本次明确授权的离线 CLI 复核范围，verified@offline）**。首次发现的材料遗漏、文档与父子事项链接冲突、默认目录入口缺失，以及后续发现的项目链接归属问题均已用原反例或直接同类输入独立复验关闭。事项与材料全文、阅读文件完整性、声明文件与代码版本变化、完整清单到目录的呈现及既有阅读路线保留均有实际运行证据。

**真实新 Codex/ChatGPT 会话恢复、线上当前状态和完整分页获取仍是 `not_proven`，不在上述 verified 范围内。** 本次严格不联网，不用离线结果替代连接配置、云端入口或真实新会话成功。

以下先保留第一轮失败原始记录，随后记载修复后的定点复验，不用新结果覆盖失败证据。

第一轮结果：**fail**。在本次检查的候选身份下，事项与材料全文可以携带，阅读文件篡改和已声明文件变化能检出，完整传入的不同归属文档也能进入目录。但评论中明确提出的必读资料可以遗漏；相互矛盾的文档身份和父事项链接可进入阅读包；真实登记的目录源文件尚不能运行新命令。这些会使新会话缺材料或打开错误事项，不能按整体完成接受。

本次没有读取开发者交付结论，没有联网，没有修改候选代码、配置、文档或 Linear。临时仓库、输入与产物均位于本目录。相关 tests 只用于了解接口形状；以下结论来自独立构造输入后调用实际 CLI，并检查其阅读产物。

| 关闭条件 | 结果 | 亲自执行的动作 | 观察结果与证据 | 需要怎样处理 |
|---|---|---|---|---|
| 保留当前事项、必要文档、评论全文 | pass（已经提供的材料） | 用包含 800 行重复段落和结尾标记的事项、代码块文档、两条不同时间评论、父目标、项目与子事项构建新阅读包 | 所有全文均逐字存在，评论引用位置保留，旧本地技能内容只做引用；见 `reading-assertions.json` 与 `fixture/.derived/linear/contexts/full_context/context.md` | 已提供材料的保存行为成立，不等于必需材料已经取齐 |
| 未完成分页、直接必需资料漏失时报错 | fail（部分路径） | 分别输入未完成 comments/children、缺少 issue 直接文档、只含列表摘要、缺少正文裸链接；另在评论明确要求先读新文档而不传该正文 | 前五类均返回 2；`missing_required_comment_document` 返回 0，并没有提示缺少 `new-111111111111`。见同名 `inputs/*.json` 与 `execution.json` | 让本轮明确必读的材料具有可校验的声明范围，覆盖评论中新增决定或其他已声明来源；缺失时拒绝或明确报缺，不能只校验 issue.description |
| 父子、项目和链接归属不串 | fail（链接身份） | 错误 parentId/projectId/comment.issueId 均尝试；另提供与 slugId 矛盾的文档 URL，以及 URL 指向另一工作区的已绑定父事项 | ID 关联错误均被拒绝；`contradictory_slug_url` 返回 0，错误 URL 满足必读 slug；`contradictory_parent_url` 返回 0，阅读包“共同目标”链接实际指向 `other/issue/OTH-999`。子事项矛盾 URL 也被接受。见同名输入和阅读包 | 校验已提供 URL、identifier/slugId 与工作区的一致性；用于阅读的关联链接不可仅因另一个 ID 匹配而放行 |
| 真正阅读的 context.md 被删改须发现 | pass | 分别改成摘要、删除文件后执行 check | 两次均返回 2，明确 `context reading file changed or is missing`。见 `changed_reading_file` / `deleted_reading_file` 的执行记录 | 无 |
| 已声明 Agent 入口、技能、公开配置、代码版本变化可检出 | pass（声明范围） | 分别修改 fixture 的 AGENTS、SKILL、harness、公开 config、源码；修改捕获输入；在 fixture Git 新建空提交 | 每个已声明文件变化都以路径报告；输入变化与 HEAD 变化分别报错，返回 2。见 `changed_declared_*`、`changed_capture`、`changed_repository_commit` | 不把这项证据扩张为未声明文件或所有代码工作树差异均被发现 |
| 离线检查不能宣称线上没有变化 | pass | 运行未改动输入的 check 并读取 context 与 manifest | `unchangedCapturedInputs: true` 同时明确 `remoteFreshness: unknown; fetch current Linear data before continuing`；阅读正文也要求重读线上 | 无 |
| 目录包含所有已完整传入的挂载位置并保留阅读路线 | pass（CLI 数据转换） | 用团队、项目、事项、initiative 和独立文档共五项生成目录，再用 MarkdownIt 解析实际表格与链接 | 五个文档 URL 均可从表格解析出，所属位置全部保留，已有阅读路线与维护说明不变；未完成分页、重复 ID、其他工作区均返回 2 且原文不变。见 `directory-assertions.json` 与 `directory_all_mounts` 等日志 | 这证明完整清单传入后不会因挂载不同被过滤，不证明线上清单确实全量取得 |
| 默认目录入口能够用于当前工作台 | fail（当前源文档集成） | 将候选真实 config 和 publication source 复制到本目录隔离夹具，用相同默认 key 调用 directory | `actual_declared_directory_entry` 返回 2：`Directory source must have unique ordered directory headings`；当前 knowledge.md 缺少两个必需锚点。README 也尚未提供声明过的 context/build/check 与 directory 使用命令 | 补齐真实目录维护位置及可用入口，然后以实际源文件复制件复验 |
| 路径、凭据和原料边界可控 | pass（代表路径） | 传入绝对路径、`../`、knowledge/raw、config/token.json、apps/.env、通往原料的软链，以及逃逸/原料/软链输出；再次写同一包目录 | 全部在构建前明确返回 2；已有阅读包没有被覆盖。见 `bad_source_*`、`raw_symlink_source`、`escape_output`、`forbidden_output`、`symlink_output`、`no_overwrite` | 本次未审计所有凭据命名约定或并发文件系统攻击 |
| 新 Codex/ChatGPT 实际会话恢复、真实线上目录分页 | not_proven | 按任务明确不联网，只运行离线 CLI | 没有真实新会话或在线 MCP 的独立运行证据 | 不能由上述 CLI 检查宣称云端连接、新会话恢复和线上全量清单已验证 |

另保留 `conflicting_document_identity` 输入，它显示只凭 document.id 能满足挂载引用，而没有检查内容真伪的能力。因为 UUID 与 URL slug 本来可能不同，此例本身不足以单独判错；上述明确 `slugId` 与 URL 尾标冲突的反例才是接受结论的依据。

复现时无需执行整个 fixture 初始化脚本。每条精确 CLI 命令及返回正文都已记录在 `execution.json`；将 build 命令的 `--output` 换成一个尚不存在的 `.derived/linear/contexts/<new-name>` 即可重复单例。输入均为人工构造，不包含真实业务原料或凭据。`reproduce.py` 是本次独立运行脚本，`reviewed-source/` 保存本次实际审过且 SHA 一致的源码与直接入口。

批准依据：主执行者转交的 2026-09-12 本轮用户会话授权与本次任务列明关闭条件。没有伪造修改前批准文件，也没有将候选说明当作批准事实。

候选身份：工作树 `/home/yyh/project/.omni-brain-runs/personal-workbench-20260912`，Git HEAD 与给定基线均为 `a7f35f7ca2e5864ea59755f7b148639cdb03b4b8`。既有未提交工作台内容以 `.derived/overlay-baseline.json` 为读入基线；其中旧 `scripts/linear_workbench.py` 为 `c45a9c7639824fad87890af64c980c288d21bd06bb823d5719de7af5f68f0244`。本次检查的 `workbench_context.py` 为 `32597cafb3f7da9f43af2066912032080a0146e69e66b8a7fdf07d5c7d90a8da`，`linear_workbench.py` 为 `f80dc0f5354586c10c3871c07e4e60366197452991f4e04ae2c3f7b0ec81da5c`。其余入口哈希见 `candidate-identities.json`，归档时复查均未变化，见 `source-preservation.json`。

实际读取：候选 AGENTS.md、review-work SKILL 和 independent-delivery-check、personal-workbench SKILL、两份目标脚本与两份相关测试、Linear 工作台 README/issue-lifecycle/knowledge，以及指定配置与 overlay 哈希。没有读取其他主树改动或已有交付评分。无需复用任何服务，所有子进程均为本次所有的短命 Python/Git 进程。

## 第二轮定点复验

收到新候选后只检查已修改或被修改波及的路径。`workbench_context.py` 的新 SHA 为 `a32b9d6d6b9aa9d9d524e1d83e8e93be1e73e28a3f7bc5db221cd424528fdf2d`，其他身份见 `round2-identities.json`，对应内容保存在 `reviewed-source-round2/`。

- 原评论必读资料缺失、文档 slugId/URL 矛盾、父事项跨工作区 URL、子事项矛盾 URL 四个原反例现在全部返回 2。补入评论要求的新文档全文后返回 0，实际阅读包包含新增验收条件全文。精确命令与输出见 `context-recheck.json`。
- 父目标、项目说明直接引用未提供的文档时均返回 2；已读取文档正文内部的背景链接没有被递归要求抓取，返回 0。见 `changed-scope-checks.json`。这验证了修改后的读取边界，没有扩大为整个工作区递归抓取。
- 当前真实配置和源文档复制件执行默认 directory 返回 0。使用主执行者明确指定的 `.derived/linear/directory-inventory.json`，其 `hasNextPage:false` 声明包含 21 项；成熟 Markdown 解析器识别出 21 个目录行，所有输入 URL 均存在，原有阅读路线、目录前文与维护后文逐字保留。见 `directory-recheck.json`。非 ASCII URL 按 Markdown 解析器的百分号编码规则规范化后比较；没有变更 URL 归属。README 已出现可执行的 directory、build、check 命令。此项现在 **pass（离线转换与真实源入口）**；清单是否反映此刻线上全部可访问资料依然未联网独立证明。
- 仍失败：将正确 `project-7` 项目的 URL 改为 `https://linear.app/other/project/foreign`，保持 `issue.projectId` 不变，build 返回 0，并把该错误地址放在“所属项目”中。复现输入 `inputs/recheck_contradictory_project_url.json`，输出位于 `fixture/.derived/linear/contexts/recheck_contradictory_project_url/context.md`，命令与返回值在 `context-recheck.json`。项目说明是承诺的下游阅读入口，不能因项目 ID 校验通过而允许链接串到其他工作区。需要对已提供项目 URL 检查其工作区和链接类型，再以本反例和原正确项目做正反验证。

## 第三轮：项目链接反例关闭

候选 `scripts/workbench_context.py` SHA-256 为 `1f6c5cfccf386cfd3052a17ec8830e5b9ed435e02bcc91aa6d5923fd93d2071f`，实际读取与运行期间未变化，源码保存于 `reviewed-source-final/scripts/workbench_context.py`。本轮没有重复运行未改路径。

| 动作 | 亲自观察结果 | 判断 |
|---|---|---|
| 正确项目 ID 搭配另一个工作区的项目 URL | build 返回 2，明确拒绝项目 URL 的工作区 | pass；原剩余反例关闭 |
| 正确工作区但 URL 指向 `/issue/YYH-71` | build 返回 2 | pass；错误链接类型被拒绝 |
| 项目路径相同但域名为 `example.invalid` | build 返回 2 | pass；错误域名被拒绝 |
| 正确工作区与项目路由，URL slug 为 `p-seven-0123abcd`、项目 ID 为 `project-7` | build 返回 0，Markdown 解析器确认实际阅读包含正确项目链接，项目说明逐字保留 | pass；没有错误要求 Linear slug 与项目 UUID/ID 相等 |

精确命令、输入路径、stdout、exit code、源码哈希及阅读消费者检查见 `project-final-check.json`；独立复验脚本为 `recheck_project.py`。本次所有候选修复均由主执行者完成，复核者只新增本目录内的人工输入、临时运行树和证据。第一、二轮的失败记录保持原样供回溯，其“仍失败”描述仅代表当时版本，最终状态以本节与开篇为准。
