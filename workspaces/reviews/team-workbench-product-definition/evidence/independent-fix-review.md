# 共作最终修复独立复核

状态：**通过**（2026-09-05，新鲜实测）
审查对象：`gongzuo-v03-20260905`，冻结输入 `6b32092364804c3329bc0d28c70b5739efb88510`。
范围：只复核本轮四条修复及指定真实 Run 的页面结果；未修改实现。测试数据均以 `fix-check-*` 命名。

依据：[`共作-产品定义与Linear拆解-v03.md`](../../../../共作-产品定义与Linear拆解-v03.md) 第 3 节要求父项上下文版本被子工作/Run 引用且旧 Run 不被静默改写；第 5 节要求首次完整讲述去重、会议冻结事实并把会中决定关联回事项。交互原型的“关系编辑”“会议快照/纪要”段落是本次 UI 对照。

| 检查 | 新鲜观察 | 结果 |
|---|---|---|
| 父子 local v1、继承与 stale | 创建父项 `item-9db39354e5eb4502` 与两个各有 local v1 的子项；`contributes_to` 为 `rel-25c0c76048d74755`，`part_of` 为 `rel-3d4aa13ee00c4345`。只读查询运行快照：两个子 Run 都记录父项、父 v1 与各自 focus（contributes 子项为 `fix-check child local v1` / `child contributes focus`；part-of 子项为 `fix-check child part local v1` / `child part-of focus`）。 | PASS |
| 父项修订后的 Run 版本 | 接受父项 v2 后，旧 Run `gzrun-20260905-153249-f3278b83` 与 `gzrun-20260905-153249-90606b92` 均为 `rev=1,currentRev=2,staleContext=true`；新 Run `gzrun-20260905-153249-49c1c09a` 为 `rev=2,currentRev=2,staleContext=false`，保存父 v2 与原子 focus。 | PASS |
| 默认 deliveries 去重且保留独立决定 | 会议投影中父项先在 `Decisions` 为 `presentation=full`。`Deliveries` 对同一项输出 `presentation=decision`，仅含 `title/status`，没有重复 `payload`，并保留 `fix-check-independent-delivery-decision`。 | PASS |
| 关系弹窗“新建并关联” | Chromium 从 `fix-check-child-contributes` 的“编辑关系”进入“新建并关联”，建立 `fix-check-ui-created-topic`。页面立即显示该专题；API 状态读回 `topic-0e52fa389f2045ff` 和唯一 `serves` 关系 `rel-818a697c79d24cb1`。 | PASS |
| 冻结、会中决定、刷新与导出 | Chromium 冻结 `meeting-snapshot-411c873360bf4715`，从会议条目记录 `fix-check UI meeting decision after freezing`，随后把专属事项改成 `fix-check-ui-meeting-MUTATED`。以 `?snapshot=` 重载后，页面仍展示原题目、`fix-check UI frozen goal` 和 `fix-check UI frozen update`。浏览器下载的 `团队周度组会.md` 含原事实、会中决定和来源 ID `item-e212cb81824742c5`，不含 mutation。 | PASS |
| 指定真实 Run 的正文与下载 | Chromium 打开个人空间 Run `gzrun-20260905-151239-c2504114`，执行“读取真实结果”并下载 `gzrun-20260905-151239-c2504114-result.txt`。下载正文与 API 固定结果一致，包含 `with-values`、`missing` 和“未知”；API 返回固定版本 `sha256:e0c56e709d849158f4c8a6c3b9dc473794fbed21034feb15ef6cf8fb433d99ff`。 | PASS |
| 共作前端类型检查 | `npm --prefix src/frontend run type-check:gongzuo` 通过。全仓 `type-check` 仍在既有 collaboration、manual-qc、dashboard 等目录报告类型错误；本轮未将这些范围外诊断作为共作修复失败证据。 | PASS（范围内） |

验证环境：后端 `127.0.0.1:8011`（最终重启后）、前端 `127.0.0.1:5175`，独立 Chromium context；HTTP 客户端 `trust_env=False`；隔离 PostgreSQL `55433`。

未证明：机器接单、Docker、SSO、生产部署和新的父级身份切换 stale 分支不属于本轮复核。指定真实 Run 仅证明固定结果可读取/下载，不代表业务接受。
