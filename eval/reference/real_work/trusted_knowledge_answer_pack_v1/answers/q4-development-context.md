# 从 Ratio 数量预览走向正式分配：最低充分上下文

## 用户结果

用户确认一份仍然新鲜的预览后，系统从当前可操作的原始任务中**稳定选出具体 task_ids**，只分给符合资格的验收员，记录成功、失败、跳过和结果未知，并回查外部状态。最终展示实际分配量，而不把“计划配额”冒充“已经分配”。

## 必须保持的边界

- 统计桶与数量配额不是执行对象；预览中的验收样本也不能偷偷扩大为其他标注全集。
- 当前预览只保存选择、参数、桶配额、来源版本和 30 分钟有效期，**没有冻结 task_ids**，因此不能直接拿来执行。
- 预览过期、来源版本或相关任务状态变化时必须停止并重算；外部即时返回仍需回查。
- 选择规则必须稳定且不超过桶容量；人员分组、供应商、资格和历史有效期需要在选择/分配时生效。
- 不预设生产阈值、外部状态值、批量上限或重试语义。

## 现有入口与最小扩展面

现有链路是 `AcceptanceRouter → AssignmentPreviewService → plan_ratio_sampling / AcceptanceRepository → PostgreSQL`：Router/Schema 管请求契约，Service 解析范围和组装预览，纯算法只算数量，Repository 查询统计单元并保存预览，数据库公共能力提供连接和事务。

开发时先沿这些入口核对当前源码，然后最小增加：按已确认范围查询**当前可操作 task**的 Repository 能力；稳定的 task 选择；人员资格约束；与预览绑定的冻结执行请求；外部任务系统的分配与回查边界。纯 Ratio 算法不应承担数据库、人员或外部 I/O。

## 最低真实验证

1. 用真实实验库准备正常、容量不足、状态已变化和人员无资格的数据；证明选出的 task_ids 稳定、唯一、不越界。
2. 证明过期预览、来源变化、旧确认和重复确认不会产生陈旧或重复分配。
3. 在可控的外部系统替身或测试环境覆盖全成功、部分失败、跳过、超时/未知，并回查最终状态和实际分配量。
4. 通过 API 及实际页面完成一次“预览 → 确认 → 执行摘要 → 回查”纵向路径；聚焦单测只补纯选择规则和状态转换。

## 仍会改变方案的未知

外部 API 的认证、批量上限、幂等键、返回与状态映射；当前可分配任务状态；人员与权限权威源；生产快照 Schema/新鲜度；确认和审批粒度；具体 task 的稳定排序或随机规则。这些应先向外部系统、数据、验收运营和原型维护者取得直接证据，再决定事务、批次和重试设计。

依据：[生命周期与阶段边界](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/lifecycle.md)、[采样、选择与分配](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/sampling-and-assignment.md)、[Python 软件结构与实现](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/python-architecture-and-implementation.md)。

下一步不是先搭完整分配平台，而是用当前源码与外部接口直接证据冻结上述未知，再实现一条可回查的最薄正式分配纵切。
