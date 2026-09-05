# 共作 v03 独立交付复核

> 2026-09-05 · 复核结论：**FAIL（有一项批准契约未满足）**

## 对象与边界

任务与用户明确批准的 v0.3 原型/拆解对齐：在本地 `local-admin`、`personal/team` 工作区范围实现可持续上下文、会议、Run 和能力候选闭环。原型本身没有批准为企业身份、跨物理机或生产部署规格。本复核没有继承旧 reviewer 结论；只使用本轮新建 `ind-final-*` 对象和新鲜 API/数据库运行。

## 新鲜结果

| 契约 | 结论 | 本轮观察 |
|---|---|---|
| fresh migration 后 personal/team 默认会议 | PASS | `GET /meeting` 两空间均取得 `meeting-default-*` 与三段默认议程。 |
| 事项创建原子生成 context v1 | PASS | 新事项与 `revisionNo=1` 上下文一次读取成功；相关单测也覆盖事务回滚。 |
| 旧上下文修订冲突 | PASS | 接受 v2 后以 `baseVersion=1` 再提案返回 `409`。 |
| 子贡献继承父 context | **FAIL** | 新建 child 后建立 `part_of → parent`，child Run 固定的是 child 自动创建的 context (`ctxv-b841…`)，不是 parent (`ctxv-9d8…`)；无 `inheritedFrom`。当前 `create_item()` 总是创建 context，令 fallback 继承路径不可达。 |
| 决策/专题/近期交付预览与冻结 | PASS | 同一新事项在决策和交付板块分别为 `full/decision`，专题摘要关联同一事项；冻结后更新事项标题，快照仍保留冻结前事实。 |
| cancel/pause 迟到 success | PASS | 实机 API：`cancelling → cancelled`、`pause_requested → paused`；迟到结果仍可从成果接口读取，带 ETag。 |
| 租约拒绝 | PASS | 错误 lease 的 Worker report 返回 `403`。 |
| 候选发布的 Run/evidence 状态门禁 | PASS（状态机） | 未验证发布返回 `409`；候选 Run 成功、关联证据人工接受、验证后才变为 `published`。 |
| personal/team 对象隔离 | PASS | 跨空间读取事项和能力候选均为 `404`；配置明确为 `identityMode=local-admin`。 |

## 验证

- 真实本地服务：`127.0.0.1:8011`，隔离 PostgreSQL（55433），所有 HTTP 客户端 `trust_env=False`。
- `pytest tests/test_gongzuo.py tests/test_gongzuo_runtime.py tests/test_gongzuo_knowledge.py -q`：31 passed。
- `tests/verify_gongzuo_legacy_migration_db.py`：通过，包含历史迁移重跑不覆盖检查。
- `tests/verify_gongzuo_core_db.py`：通过。
- 前端 `npm run build`（含 `vue-tsc`）与 `npm test -- --run`：41 passed；构建仍有 500 kB chunk 警告。

## 未证明与阻塞

1. **阻塞交付：** 修复子贡献应在没有局部 accepted context 时可靠继承父 context，或明确改为父引用与局部 context 的合成；随后重跑“child → parent → Run snapshot”实证。
2. 本轮候选闭环用持有 Worker token 的受控 API 回报验证状态机，并未启动 Codex/OpenCode。因此“已有真实执行器实际完成且证据真实”的语义为 **NOT PROVEN**；当前接口可证明门禁，不能证明报告内容来自执行器。
3. Docker、不同物理机、公司 SSO/企业成员权限不在本机实测范围，均为 **NOT PROVEN**。当前证据只支持 localhost local-admin 与 `GONGZUO_WORKSPACES` 数据边界。
4. 根代理报告的两个前端修复（关系弹窗“新建并关联”、冻结后记录决定）尚在其改动中；本独立复核没有可用浏览器运行器，不能把类型检查/构建作为实际交互通过证据。
