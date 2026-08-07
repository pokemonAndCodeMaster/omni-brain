结论：本次最小目标应是把“Ratio 数量计划”变成一组可审计的具体 `task_ids`，用户确认后再正式分配，并返回成功、跳过、失败或待回查结果。当前代码只完成到数量预览，不能直接扩展为执行。

### 用户最终结果

用户应能：

1. 选择任务或日期范围，设置总量与 Good 比例；
2. 查看具体任务清单、Good/Bad 数量、缺口和警告；
3. 确认后固定这组 `task_ids`；
4. 执行正式分配；
5. 看到即时结果，并能知道哪些任务需要回查或重试。

预览必须表达“将执行哪些任务”，而不只是每个统计桶分配多少。

### 必须保持的边界

- `task_id/clip` 是实际选择和执行对象；`scene_name`、日期、快照只是管理和聚合维度。
- Ratio 算法只负责“抽多少”，不负责查询任务、选择验收员或调用外部系统。
- 预览保存后必须绑定具体 `task_ids`、请求参数、来源版本、操作者和过期时间。
- 执行前必须重新校验任务当前状态、可分配性和预览新鲜度；过期或来源变化不能继续执行。
- 数量不足、Good/Bad 类别不足不能静默缩减；必须显示缺口和类别补足。
- 不能把验收抽样集当成后续通过/打回的执行全集。
- 交付阶段、健康状态、行动项状态和验收结论仍是独立状态轴。
- 人员、分组、供应商、有效期和权限约束必须在正式分配前确认，不能由当前 Ratio 原型推断。
- 当前 `submitted/completed`、快照字段版本和通过率分母存在冲突，不能在实现中悄悄统一。

依据：[采样与分配](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/sampling-and-assignment.md)、[数据流与状态](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/data-flow-and-state.md)。

### 当前原型与代码入口

现有纵切是：

`Router → AssignmentPreviewService → AcceptanceRepository + Ratio 算法 → t_qc_operation_preview`

主要入口：

- [`router.py`](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md:36)
- [`acceptance.py` Schema](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md:42)
- [`assignment_preview_service.py`](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md:45)
- [`sampler.py`](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md:48)
- [`repository.py`](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/implementation-map.md:51)

最低实现影响面应集中在现有 Preview Service/Repository/Schema 附近，新增：

- 具体 task 候选查询与稳定选择；
- 预览中保存 `task_ids`；
- 执行接口和执行前重查；
- 外部任务分配客户端及结果映射；
- 成功/部分成功/失败/待回查状态；
- 前端从“数量预览”进入“任务明细确认”。

当前原型的直接来源记录见：[当前验收原型来源](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/sources/current-prototype.md>)。该来源记录对应的外部仓库和 commit 未在本 Harness 工作区内，因此这里能确认的是已登记的代码入口与边界，不能重新证明真实部署或生产 Schema。

### 最低真实验证

只需验证一条纵切：

1. 固定数据库夹具中准备足够、类别不足、已被分配和状态变化的任务；
2. 真实 API 创建预览，确认返回并持久化具体 `task_ids`；
3. 真实 API 执行，确认成功任务状态和部分失败结果；
4. 在执行前改变一个任务状态，确认整批拒绝或明确部分结果；
5. 验证过期预览、重复提交、超额请求和 Good/Bad 不足；
6. 通过真实页面确认用户看到的任务集合与最终执行集合一致。

现有开发证据已经覆盖 Ratio 边界和部分分配缺口算法，但“外部正式分配、并发状态变化和真实页面闭环”仍未验证。[Python 软件结构](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/python-architecture-and-implementation.md>)对此有明确边界。

### 仍会改变方案的关键未知

- 正式分配的外部系统、接口、认证、批量上限和状态回查方式；
- 验收员如何选择，以及人员/组/供应商/有效期约束；
- `waiting_review` 等当前有效状态值；
- 具体 task 的稳定排序或随机抽样规则；
- 部分成功时是逐 task 提交、整批原子提交，还是异步任务；
- 幂等键、重复确认和重试语义；
- 当前生产快照究竟使用 `submitted` 还是 `completed` 字段；
- “正式分配”是否只写本地记录，还是必须立即改变外部 task 状态。

这些未知中，外部接口、原子性/部分成功语义和人员约束会直接决定 API、事务边界及预览数据结构；应先由外部系统负责人、验收运营负责人和数据负责人分别提供直接契约。