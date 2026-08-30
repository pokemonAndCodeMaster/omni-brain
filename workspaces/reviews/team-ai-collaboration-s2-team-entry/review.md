# S2-A：团队身份与责任协作——方案审查

> 当前阶段：R1 已通过；R2 方案待确认；开发等待
> 来源：用户要求继续 S2，团队管理认证先简化，不直接接 SSO  
> 产品位置：`docs/team-ai-collaboration-delivery-hub-product-design.md` 的 S2“团队执行可靠性”  
> 本轮切片：先让真实团队成员能够进入平台、被分配责任并留下可信操作身份；Worker/Lease 等后续承接

**怎样使用：** R1 已于 2026-08-30 经用户回复“通过”。现在只审 R2，可直接回复 `R2：通过`，或写明
需要调整的实现边界。R2 通过后才修改数据库、后端和 Vue 页面。

**导航：** [背景与问题](#1-背景与问题) · [目标与用户结果](#2-目标与用户结果) ·
[功能与规则](#3-功能与规则) · [范围](#4-范围与保持不变) · [完成标准](#5-完成标准) ·
[R1 结论](#r1需求结论) · [R2 方案](#7-r2实施方案) · [R2](#r2方案是否可实施)

## 1. 背景与问题

平台目前把所有业务动作都记为固定 `admin`。这在 S0/S1 单人自举时足够，但团队共用后会出现三个
直接问题：不知道是谁提出、执行或接受；Owner/Reviewer 只能填写自由文本，可能指向不存在的人；
成员离开或职责变化后，历史责任和当前可分配名单无法同时保持正确。

S2 的完整方向还包括 Worker、Lease、RunAttempt、远端 ArtifactStore 和多执行端点。若一次全部建设，
会在没有真实团队使用证据时过早引入调度和基础设施。因此先交付一个能独立产生结果的 S2-A：
**团队成员以平台内建轻量身份进入，平台从可信会话取得 actor，并在现有需求、Work、Run 和决定中使用。**

## 2. 目标与用户结果

管理员第一次打开平台时，使用本地初始化的管理员账号登录；之后可以在“团队”页面新增、停用和查看
成员。成员使用自己的平台账号登录后，导航和业务页面显示当前身份；创建 Idea、补充讨论、启动 Run、
确认 Gate 或作出决定时，后端自动记录当前成员，客户端不能伪造 `actor_id`。

管理员在 Requirement 和 Work 中选择 Owner/Reviewer 时，只能从当前有效成员中选择；历史对象继续
显示当时的成员身份，即使该成员后来被停用。普通成员可以完成被授权的日常协作动作，但不能创建、
停用成员或改变成员角色。未登录访问业务页面时进入登录页，API 返回明确的未认证原因。

## 3. 功能与规则

| 类别 | 本切片要做到的事 | 规则 | 用户看到的结果 |
|---|---|---|---|
| 登录 | 使用平台本地账号登录、退出并保持短期会话 | 不接 SSO；不允许客户端声明 actor | 登录后显示本人，退出后回到登录页 |
| 团队成员 | 管理员新增、查看、停用成员 | 第一版只有 `admin`、`member` 两种角色；成员身份不可覆盖删除 | 团队页能看见有效/停用成员和角色 |
| 责任分配 | Owner/Reviewer 从有效成员中选择 | 不再新增自由文本身份；既有 `admin` 记录保持兼容 | Requirement/Work 中不会选到不存在的人 |
| 操作留痕 | 现有业务写动作从服务端会话取得 actor | 历史记录保持原 actor；停用不改写历史 | 时间线、Run、Gate、Decision 能回答“谁做的” |
| 权限 | 管理员管成员；登录成员做现有协作动作 | 第一版不建设细粒度资源 ACL | 越权操作得到明确 403，不伪装成环境问题 |
| 失效 | 停用成员的新会话和后续写入被拒绝 | 已启动 Run 不因成员停用被强杀，结果仍归原 actor | 历史可读，新动作被阻止 |

### 建议采用的简化认证口径

“不接 SSO”仍需要区分真实团队成员，因此建议第一版采用：

- 管理员创建本地用户名和初始密码；成员首次使用该账号登录；
- 密码只保存成熟哈希，不保存或回显明文；
- 使用服务端会话 Cookie，浏览器不自行保存长期 Token；
- 不做公开注册、邮件、找回密码、MFA、组织/租户、LDAP/OAuth/OIDC；管理员可以重置密码；
- 本地初始化 `admin` 的方式必须显式且可轮换，不能把固定密码提交到 Git。

这比“页面选一个名字就算登录”多一个最小密码步骤，但才足以把数据库里的 actor 从展示标签升级为
团队审计身份；同时仍远小于 SSO。

## 4. 范围与保持不变

### 本次必须覆盖

- 登录/退出、当前身份、会话失效；
- 成员列表、新增、停用、角色和管理员密码重置；
- Idea、Requirement、Thread、Decision、Work、PlanStep Gate、Evidence、Agent Run 的 actor 注入；
- Requirement/Work 的 Owner/Reviewer 有效成员选择；
- 一条管理员旅程和一条普通成员旅程的真实 PostgreSQL/API/Chromium 验证。

### 本次不做

- SSO、企业目录同步、MFA、公开注册、邮件与自助找回；
- 组织/租户、项目级 ACL、复杂角色编辑器和审批流；
- Worker 注册、心跳、Pull、Lease、Drain、Lost/Retry；
- RunAttempt、NAS/OBS、Docker、Secret 管理和多执行端点；
- 因接入登录而改变 S1 的固定六步、Git Gate、人工接受和不自动 Push/Merge 边界。

Worker 等能力仍属于 S2，但应在 S2-A 让真实成员进入后，作为下一条独立 Requirement 用实际工作站
和故障场景设计，避免身份、调度、产物存储同时改动。

## 5. 完成标准

1. 全新浏览器访问业务路由会进入登录；正确账号能进入，错误密码显示明确原因，退出立即失效。
2. 管理员新增普通成员后，该成员能登录；普通成员不能新增、停用或改角色。
3. 管理员把一条 Work 的 Owner/Reviewer 分配给两个有效成员；停用成员不再出现在新分配选项中，
   既有 Work 和历史时间线仍显示原身份。
4. 普通成员启动一次允许的 Agent Run，数据库、Run 详情和业务时间线记录的是该成员，而不是 `admin`
   或客户端传入值。
5. 停用成员的既有会话在下一次受保护请求时失效；历史 Run 与 Decision 保持可读。
6. 现有 S0/S1 回归、类型检查和构建通过；桌面和手机真实 Chromium 覆盖登录、团队页、分配和 Run。
7. 迁移与初始化可回滚，不把密码、Cookie 密钥或用户凭据写入 Git、日志、Run prompt 或页面响应。

## 6. R1 需求结论

- **结论：** 通过。
- **确认时间与原话：** 2026-08-30，用户回复“通过”。
- **已锁定边界：** S2 先做本地身份、团队成员、责任分配和可信 actor；不把 SSO、Worker、Lease、
  RunAttempt、远端 ArtifactStore 或 Docker 混入本切片。
- **对 R2 的约束：** 保持现有模块化单体、PostgreSQL 和 Vue 3，不另建认证服务，不引入前端声明身份的捷径。

## 7. R2 实施方案

### 7.1 当前事实与改动落点

定向源码核验得到以下实现事实：

- `src/api/deps.py` 的 `get_actor_id()` 固定返回 `admin`；协作、Work 和 Run 创建接口依赖它，Run 取消、
  查询、质检分析、快照和个人视图配置尚未统一要求身份。
- `t_collab_idea`、`t_collab_requirement`、`t_work` 已有 Owner/Reviewer 字符串字段，默认值是 `admin`；
  Thread 的 actor type 仍限定为 `admin/system`。
- `ViewConfigService` 把所有个人视图归给固定 `local-user`；这会让团队成员互相覆盖配置。
- Vue 路由当前全部直达业务页，`AppShell` 固定显示 `admin`，Work 的 Owner/Reviewer 是自由文本输入。
- 当前迁移到 `007_create_collaboration_s1.sql`，后端尚无密码哈希依赖和身份领域。

因此本切片在现有质量平台模块化单体内新增 `identity` 领域，而不是拆认证微服务；修改面限定为一条完整
纵切：PostgreSQL 身份事实源 → FastAPI 会话与权限依赖 → 现有业务 actor/责任校验 → Vue 登录和团队页。

### 7.2 核心取舍

| 议题 | 采用方案 | 为什么现在这样做 | 明确不做 |
|---|---|---|---|
| 登录方式 | 本地用户名 + 密码 | 满足共享工作站的真实成员区分，又不依赖企业身份系统 | SSO/OIDC/LDAP、公开注册 |
| 密码 | `pwdlib[argon2]` 的推荐配置，保存 Argon2id 哈希 | 直接采用成熟的慢哈希与库默认参数，不自造密码学 | 明文、可逆加密、自写哈希 |
| 会话 | 服务端保存随机不透明 Session，浏览器仅持有 HttpOnly Cookie | 可立即停用、撤销和审计；第一版无需 JWT 的签发/刷新复杂度 | localStorage Token、JWT 刷新链 |
| 权限 | `admin/member` 两角色 | 覆盖“管成员”和“做业务”两个现实边界 | 项目 ACL、资源级权限编辑器 |
| 成员历史 | 稳定 member id + 停用，不物理删除 | 历史 Owner、Reviewer 和 actor 可长期回溯 | 删除成员后改写历史 |
| 个人配置 | 由当前 Session member 隔离 | 修复当前 `local-user` 共享覆盖 | 新建 Profile/HostProfile 抽象 |
| 初始管理员 | 迁移保留 id=`admin`，CLI 交互式设置首个密码 | 兼容既有数据且不提交默认密码 | 默认口令、通过命令行参数传密码 |

密码实现遵循 [FastAPI 官方安全示例](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) 推荐的
`pwdlib`/Argon2 路径，以及 [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
对现代自适应密码哈希的要求。会话采用高熵随机标识、服务端语义和 Cookie，是
[OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
建议的简洁形态。

### 7.3 数据模型与迁移

新增 `008_create_team_identity.sql`，只做可追溯的增量迁移：

#### `t_team_member`

| 字段 | 约束/语义 |
|---|---|
| `id varchar(64)` | 主键；首个成员固定为 `admin`，之后使用 UUID，永不复用 |
| `username varchar(64)` | 统一 trim + lowercase 后唯一；3—64 字符，只允许字母、数字、`.`、`_`、`-` |
| `display_name varchar(64)` | 页面展示名，1—64 字符，不作为外键 |
| `role varchar(16)` | `admin/member` |
| `status varchar(24)` | `pending_setup/active/disabled` |
| `password_hash text` | 仅 `pending_setup` 可为空；响应模型永不包含 |
| `must_change_password boolean` | 新增成员或管理员重置后为 true |
| 审计字段 | `created_by/created_at/updated_at/disabled_by/disabled_at` |

#### `t_auth_session`

| 字段 | 约束/语义 |
|---|---|
| `token_hash char(64)` | 主键；浏览器持有 256-bit 随机原值，数据库只存 SHA-256 查找摘要 |
| `member_id` | 外键到成员 |
| `created_at/expires_at` | 服务端绝对过期时间，默认 12 小时，可由部署配置覆盖 |
| `revoked_at` | 退出、停用和重置密码时撤销 |

这里的 SHA-256 只用于不可猜测 Session Token 的等值查找，绝不用于密码。Cookie 名为
`omni_session`，设置 `HttpOnly; SameSite=Lax; Path=/`，不设置 `Domain`；本地 HTTP 开发允许
`Secure=false`，共享工作站的非本机访问必须由 HTTPS 入口提供并配置 `Secure=true`。Cookie 不写
localStorage，也不进入 API 响应。

#### `t_team_member_event`

记录 `member.created/member.role_changed/member.disabled/member.enabled/password.reset/password.changed`，
字段包括目标成员、事件类型、操作者、时间和不含凭据的 JSON payload。成员永不物理删除，事件也不级联删除。

#### 既有表兼容

1. 先插入 `id='admin'`、`status='pending_setup'` 的管理员占位行，既有 `admin` Owner/Reviewer/actor
   不需重写。
2. 将现有个人视图配置的 `owner_id='local-user'` 改为 `admin`。
3. 为 Idea Owner、Requirement Owner、Work Owner/Reviewer、个人视图 Owner 增加成员外键；迁移前先列出
   非 `admin/local-user` 的既有值，存在未知身份就停止并报告，不静默造成员。
4. Thread 既有 `actor_type='admin'` 改为 `member`，约束改为 `member/system`。
5. 通用 actor 字段暂不加外键，因为系统事件合法使用 `system`；可信性由服务端依赖保证，成员不删除保证历史可解引用。
6. 为兼容回退，本次不删除旧列默认值；新 API 和服务代码不得依赖默认值，测试证明任何 HTTP 写操作都取当前 Session。

迁移前保存 PostgreSQL dump 和受影响行计数。尚未产生新团队数据时，可回退代码并用对应回滚 SQL 恢复
`local-user` 与 Thread 约束；正式产生多成员配置后不承诺无损降级到 S1，只允许从备份整体恢复或向前修复，
避免伪造“可回滚”承诺。

### 7.4 会话、登录与权限规则

登录流程保持短而完整：

```text
提交用户名/密码
  → 统一校验用户名与 Argon2id（未知用户名也执行 dummy verify）
  → 确认成员 active
  → 生成随机 Session，数据库只存摘要
  → Set-Cookie，返回不含凭据的 MemberSummary
  → must_change_password=true 时只允许改密/退出
```

具体规则：

- 密码长度 15—128 字符；不增加复杂字符拼图。创建/重置时由管理员填写一次性初始密码，响应和事件都不回显；
  成员首次登录必须改密。
- 登录失败统一返回“账号或密码错误”，不暴露用户名是否存在、已停用还是待初始化；初始化状态只由本机部署入口处理。
- 改密会验证当前密码、撤销该成员全部 Session，再创建一个新 Session；管理员重置和停用会立即撤销目标成员全部 Session。
- `require_member` 同时校验 Session 存在、未过期、未撤销、成员仍 active；浏览器残留 Cookie 不代表权限仍有效。
- 处于 `must_change_password` 的会话只能访问当前身份、改密和退出接口，其余返回稳定错误码
  `password_change_required`，前端引导到改密页。
- 所有 active 成员可使用 S0/S1 已有业务读写能力；只有 admin 可查看停用成员、创建/恢复/停用成员、
  改角色和重置他人密码。
- 始终至少保留一个 active admin；禁止当前管理员停用/降级自己，也禁止停用/降级最后一个 active admin。
- Owner/Reviewer 赋值必须在服务端验证目标成员为 active。成员停用后不出现在新选择列表，但详情可按 id
  解析其展示名和“已停用”状态。

### 7.5 后端组件与 API 契约

后端新增 `src/identity/`，由 `MemberRepository`、`SessionRepository`、`IdentityService` 三个边界组成；
`src/api/routers/auth.py` 和 `team.py` 只负责 HTTP 转换，规则留在 Service。`app.state` 只持有一个
`IdentityService`，不增加全局可变用户变量。

| 方法与路径 | 身份要求 | 输入/输出与行为 |
|---|---|---|
| `GET /api/auth/status` | 公开 | 只返回 `setup_required`，不泄露成员清单 |
| `POST /api/auth/login` | 公开 | username/password；成功 Set-Cookie + MemberSummary，失败统一 401 |
| `GET /api/auth/me` | 有效 Session | 当前 MemberSummary；失效 401 |
| `POST /api/auth/logout` | 可带 Session | 有则撤销、始终清 Cookie，204；过期 Cookie 也能退出 |
| `POST /api/auth/change-password` | 有效登录，允许 must-change | 当前密码 + 新密码；轮换 Session，204/新 Cookie |
| `GET /api/team/members` | member/admin | member 仅能取 active；admin 可筛 active/disabled；分页默认 50、最大 100 |
| `POST /api/team/members` | admin | username/display_name/role/initial_password；创建 must-change 成员 |
| `PATCH /api/team/members/{id}` | admin | 修改 display_name/role；保护最后管理员与当前管理员 |
| `POST /api/team/members/{id}/disable` | admin | 停用并撤销全部 Session |
| `POST /api/team/members/{id}/enable` | admin | 恢复为 active，保留原历史 |
| `POST /api/team/members/{id}/reset-password` | admin | 写入新临时哈希、must-change、撤销 Session，204 |
| `GET /api/team/members/{id}/events` | admin | 成员管理事件，分页返回 |
| `PATCH /api/requirements/{id}/owner` | member/admin | 选择 active member；追加既有 Requirement 时间线事件 |
| 既有 `PATCH /api/works/{id}` | member/admin | Owner/Reviewer 改为 active member 校验，不再接受任意文本 |

公共路由仅保留 `/api/health`、`/api/auth/status`、登录与可安全重复的退出。分析、快照、视图配置、
协作、Work、Agent Catalog/Run 的所有读写路由统一挂 `require_member`；管理路由再挂 `require_admin`。
FastAPI 的 `get_actor_id` 改为从同一请求已解析的 current member 取 id，客户端 payload 即使附带 actor 也不会使用。

现有遗漏一并收口：

- Run 取消接口也取得 current actor，并在 `t_agent_run_event.payload.actor_id` 留痕；
- Agent Run 创建继续把 member id 写到 `t_agent_run.actor_id`；
- `ViewConfigService` 不再使用 `LOCAL_OWNER_ID`，每次由依赖传入 member id；
- Idea/Requirement/Decision/Thread/Work/Gate/Evidence 的既有写路径统一由依赖传 actor；
- 401 使用 `not_authenticated/session_expired`，403 使用 `admin_required/password_change_required`，409 用于
  用户名冲突、最后管理员保护和无效责任人；错误详情保留真实原因，不统一简化成“环境问题”。

### 7.6 Vue 页面、状态与组件边界

遵循现有 Vue 3 `<script setup lang="ts">` 和 Composition API，新建 `features/identity/`，不为这一条状态
额外引入 Pinia：

| 组件/模块 | 责任 | 交互边界 |
|---|---|---|
| `useSession.ts` | 单例式响应状态、`load/login/logout/changePassword` | 只通过 `/auth/*` 获取身份；不持久化 Token |
| `LoginPage.vue` | 登录与首次初始化提示 | emit/调用登录；不包含业务壳 |
| `PasswordChangePage.vue` | 首次强制改密和主动改密 | 成功后回到原目标页 |
| `TeamPage.vue` | 成员筛选、分页和管理动作编排 | 仅 admin 导航可见；403 仍由后端兜底 |
| `MemberCreateDialog.vue` | 新增成员表单 | props: busy；emits: submit/close；清空密码字段 |
| `MemberRow.vue` | 展示状态、角色和管理菜单 | emits: edit/disable/enable/reset；不直接发 API |
| `MemberSelect.vue` | Owner/Reviewer 统一选择器 | props: modelValue/members/label；emits: update:modelValue |
| `AppShell.vue` | 展示当前成员、角色、退出和 Team 入口 | 删除硬编码 `admin`；member 不显示管理入口 |

路由新增 `/login`、`/account/password`、`/team`。全局 guard 首次导航只请求一次 `/auth/me`：未登录跳
登录并保留 `redirect`，must-change 跳改密，普通 member 进入 `/team` 时转到首页并显示明确无权限信息。
Axios 对 401 清空会话并跳登录；业务页面不会各自重复拉当前身份。

Work 元数据编辑由两个自由文本框改为 `MemberSelect`；Requirement 详情增加 Owner 选择器。成员选项按需请求
active 列表并在 feature composable 内缓存，打开相关编辑区才加载，不让 AppShell 高频轮询全量成员。页面对停用
历史成员展示“姓名（已停用）”，而不是把 id 或空值丢给用户。

响应式与可访问性边界：登录、成员表格/卡片、选择器和对话框覆盖 1440px 桌面与 390px 手机；表单具有
真实 label、错误摘要和焦点回归；菜单/对话框可用键盘完成；禁用状态不能只靠颜色表达。

### 7.7 初始化、运行与失败恢复

迁移会创建待初始化 `admin`，但不产生默认密码。部署者在服务端运行：

```bash
python -m src.cli bootstrap-admin
```

命令通过 `getpass` 交互读取并二次确认密码，不接受 `--password`，不打印密码；只允许将
`pending_setup` 的首个 admin 激活。已初始化时命令明确拒绝，日常轮换走登录后的改密或管理员重置。
前端发现 `setup_required=true` 时只展示上述本机操作提示，不开放匿名网页初始化管理员。

需要新增配置仅有 `auth.session_ttl_hours`、`auth.cookie_secure` 和 Cookie 名；随机 Session 不需要额外提交
签名密钥。远程共享部署未提供 HTTPS 时明确判定为部署不合格，不悄悄退化为不安全 Cookie。

失败与恢复：

- PostgreSQL 不可用：登录和业务接口如实返回数据库不可用，不误报密码错误；健康接口仍给出真实失败。
- 模型、OpenCode/Codex 鉴权或模型不可用：继续保留各自真实 Run 失败原因，与登录失败分开。
- Session 过期/撤销：返回稳定 401，前端保留原目标位置，重新登录后恢复导航。
- 成员停用发生在 Run 进行中：不杀 Run；Run 完成仍归原 actor，成员不能再创建/取消新 Run。
- 新迁移失败：事务回滚；恢复备份后仍可运行 S1 版本，不在半迁移状态继续启动。

### 7.8 实施顺序

R2 通过后按一条纵切推进，不再新增方案门禁：

1. 数据库迁移、identity repository/service、CLI bootstrap 与后端单元/集成测试；
2. 全局认证依赖覆盖全部现有路由，替换固定 actor 与个人视图 owner；
3. 成员管理 API、责任人校验、Run 取消留痕；
4. Vue session、登录/改密/团队页、AppShell 身份和 MemberSelect；
5. 真实 PostgreSQL 迁移与 API 冒烟；
6. Chromium 桌面/手机完整旅程、性能观察和 S0/S1 回归；
7. 形成唯一 review 证据，回写当前路线状态；之后再进入 S2-B Worker/Lease 的 R1。

### 7.9 验收与证据

#### 自动化

- 后端：密码绝不以明文落库；Session 只存摘要；未知用户与错误密码均 401；停用、过期、撤销、must-change、
  member 越权、最后 admin 保护、无效 Owner/Reviewer、客户端伪造 actor 全部有测试。
- 路由矩阵：除明确公共端点外，逐一证明无 Cookie 为 401；member 管理团队为 403；admin 成功。
- 数据迁移：既有 `admin` 历史和 `local-user` 视图转换数量精确；存在未知 Owner 时迁移失败而非吞掉。
- 前端：`useSession`、路由 guard、登录错误、成员动作、MemberSelect 和 401 恢复有 Vitest；`vue-tsc` 与 build 通过。
- 全量回归：保持现有后端与前端测试全部通过，不用删测或弱化断言换取通过。

#### 真实纵向旅程

在迁移前先做数据库 dump，然后用真实 PostgreSQL、真实后端和生产构建前端完成：

1. 全新 Chromium 访问业务 URL → 登录页；错误密码显示“账号或密码错误”。
2. CLI 初始化 admin → 登录 → 新增普通成员 `member-a`；数据库只有 Argon2id 哈希。
3. `member-a` 首次登录 → 被强制改密 → 无法访问团队管理动作（API 403）。
4. admin 把真实 Work 的 Owner 设为 `member-a`、Reviewer 设为 admin；刷新后数据和页面一致。
5. `member-a` 启动一次安全的 Agent Run；Run 详情、数据库和事件均为其 member id，失败时保留真实执行原因。
6. admin 停用 `member-a`；其已打开浏览器下一次请求立即 401，历史 Work/Run 仍显示姓名和已停用状态。
7. 1440×900 与 390×844 Chromium 检查登录、团队页、责任选择和 Run 详情；记录截图、控制台错误和网络请求。

组合边界采用分页而不是假定小团队：成员列表真实制造 101 条测试记录，验证 50 默认页、100 最大页和第二页；
同一成员两个浏览器 Session 均可使用，停用/重置后两者同时失效。会话请求只做一次主键摘要查找 + member
查找，不在每次导航加载团队列表，也不恢复曾造成卡顿的全量高频轮询。

### 7.10 完成定义与后续边界

只有以下条件同时满足才可称 S2-A 完成：上述真实旅程通过；数据库和 API 能回答“谁做了什么”；成员责任
选择不再接受自由文本；停用立即生效且历史不丢；桌面/手机 Chromium 有新鲜证据；现有 S0/S1 回归通过；
没有凭据进入 Git、日志、prompt、API 响应或截图。

这条完成后，S2-B 才围绕“工作站注册 → Worker 心跳/Pull → 单任务 Lease → RunAttempt → 丢失恢复”形成
独立 R1。S2-A 不预建 Worker 表、远端对象存储接口或 Docker 抽象。

## R2：方案是否可实施

- **审查目的：** 确认本地密码 + 服务端不透明 Session、两角色、增量迁移、统一路由鉴权、Vue 页面边界和
  真实验收路径足以直接开发。
- **推荐结论：** `通过`。方案没有需要你额外拍板的产品分叉；12 小时 Session 和字段长度属于可配置/可测试
  的实现默认值，不改变产品语义。
- **通过后的动作：** 我将直接实现数据库、后端、Vue 和自动化测试，随后启动真实 PostgreSQL/API/Chromium
  完成纵向验收；不再在开发中途追加 SSO、Worker 或细粒度 ACL。
- **你的反馈：** `状态：待审；意见：__________`
