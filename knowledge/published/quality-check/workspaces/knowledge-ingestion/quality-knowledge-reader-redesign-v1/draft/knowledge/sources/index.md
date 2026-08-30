# 来源记录

来源记录保存“这批材料是什么、版本在哪里、能证明什么和不能证明什么”，用于追溯与复核；它不是规范知识正文。业务定义、算法步骤、状态边界和软件结构必须在对应知识页中被充分解释，不能压成一两句后把理解责任推给下面的链接。

- [人工语义决定](human-decisions.md)：三阶段边界和执行全集；两份文件完全重复，缺原始对话。
- [历史验收运行快照](historical-pipeline.md)：旧分配、阈值、通过打回、状态刷新和中间表链路。
- [目标验收平台设计](target-design.md)：平台、人工质检、快照、采样、规则、外部系统和 Repository 的目标方案。
- [当前验收原型](current-prototype.md)：固定提交中的 Python、SQL、前端和直接依赖。

上面四项是父版本 Batch 1 来源导航；本候选已在下方登记 Batch 2 材料及其发现、正文落点。日志中的“Batch 2 尚未进入”仅描述父版本形成时的历史状态。

## 来源怎样进入规范知识

| 来源 | 已内化的主要知识 | 仍保留在来源记录中的内容 |
|---|---|---|
| 人工语义决定 | [生命周期与阶段边界](../domains/quality/manual/acceptance/lifecycle.md)、[结论与执行对象](../domains/quality/manual/acceptance/conclusion-and-execution.md) | 原始决定缺失、重复文件和可证明边界 |
| 历史运行快照 | [采样算法与历史策略](../domains/quality/manual/acceptance/sampling-and-assignment.md)、[历史结论规则](../domains/quality/manual/acceptance/conclusion-and-execution.md) | 历史材料身份及为何不能外推当前 |
| 目标设计 | [数据流与状态](../domains/quality/manual/acceptance/data-flow-and-state.md)、[系统架构](../domains/quality/manual/acceptance/system-architecture.md) | 目标方案的来源范围和未实现边界 |
| 当前原型 | [Python 软件结构](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)、[当前仓库原型](../systems/manual-qc-acceptance-prototype.md) | 固定提交、实际读取文件和测试证据边界 |

如果规范知识页只剩摘要而必须打开原始来源才能知道机制、算法、约束或例外，应判定为摄入不完整；来源链接只能用于核验和继续下钻，不能用于补偿正文缺失。

<!-- omni-brain:incremental-provenance:start -->

## 本次摄入的材料范围

| 来源 ID | 固定位置 | 文件数 | 指纹 |
|---|---|---:|---|
| `batch-2` | `/home/yyh/project/omni-brain-m1-brownfield-input-v1/batch-2` | 25 | `f106093ab416c46b9f7b518bd4d46eb2437d763d63dd61c03d3de13e6d0cec73` |

## 本次结论与规范知识落点

### [人工质检总览与业务视图](../domains/quality/manual/overview.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f015-overview-workbench：人工质检总览应作为需求对齐与日常交付推进工作台，而不是统计大屏：首屏依次呈现经营摘要、阶段轴、近期交付、需求接纳、标注健康、验收健康和可交付完成。 | `target_design` | `batch-2:quality_check/人工质检总览信息架构.txt#1. 页面任务; 2. 首屏顺序` | 总览与工作台边界 |
| f016-overview-queues：总览的四类工作队列分别面向需求接纳、标注健康、验收健康和可交付/盖章，并覆盖完整队列而非单任务样例；每个区域应能下钻到对应工作台。 | `target_design` | `batch-2:quality_check/人工质检总览信息架构.txt#2.4-2.7; 5. 总览与交付中心边界` | 总览与工作台边界 |
| f017-overview-unknowns：总览设计明确将留存率正式定义、倒排时间计算来源、Bad/打回原因分类和盖章完成条件列为待确认。 | `unknown` | `batch-2:quality_check/人工质检总览信息架构.txt#6. 待确认` | 当前事实、目标、未知 |
| f022-platform-boundary：统一平台承载人工质检、大模型质检、自动化质检和专题数据质量四类业务，统一工作台、交互语言和公共能力，但保持各模块业务模型、表和流程边界。 | `current_decision` | `batch-2:quality_check/质检一站式平台顶层架构.txt#§0.1-§0.2; §1.2` | 先看全貌 |
| f026-business-overview：平台首页是团队业务全景和阶段复盘入口，不是系统监控或个人待办；需回答里程碑、近期质量护航、四块业务阶段和需要协调的团队风险。 | `target_design` | `batch-2:quality_check/质检业务总览信息架构.txt#1. 页面定位; 3. 首页信息优先级` | 总览与工作台边界 |
| f027-business-responsibility：近期质量护航台账必须区分业务责任：城区/高速/园区/仿真中人工质检处于交付前最后一环，感知只做抽检防护，自动化质检属于数据生产产线的拦截/清理，不应伪造独立交付阶段。 | `current_decision` | `batch-2:quality_check/质检业务总览信息架构.txt#2.2 数据需求与交付轴` | 先看全貌 |
| f028-business-unknowns：平台首页仍缺团队阶段目标来源与更新频率、自动化准召率统计粒度、大模型 Benchmark/上线阈值/能力维度和专题质量专属指标等权威口径。 | `unknown` | `batch-2:quality_check/质检业务总览信息架构.txt#7. 待确认口径` | 当前事实、目标、未知 |
| f049-fe-information-architecture：新版人工质检页面以数据集交付任务为主线：总览→交付中心→标注中心→验收中心→人力与分组；交付中心维护完整字段，验收中心按数据集聚合后按需下钻 task。 | `current_decision` | `batch-2:quality_check/质检平台-人工质检前端页面与状态设计.txt#⑤ 页面结构（2026-07-05新版）; 页面组织原则` | 人工质检工作旅程 |

### [人工质检交付与行动项](../domains/quality/manual/delivery-management.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f001-delivery-task：人工质检以数据集对应的交付任务为主对象，从需求登记持续到验收通过、打回返修完成和可交付 Good 数量确认；标注任务创建成功不是交付完成。 | `current_decision` | `batch-2:quality_check/人工质检-交付任务与行动项机制.txt#2. 标准交付轨道; 8. 完成定义` | 交付任务是长期维护边界 |
| f002-delivery-fields：需求计划值与实际值必须并列保留，交付任务要覆盖需求身份、送检、规范与适配、任务生产、标注、验收、通过打回和最终可交付量等字段域。 | `current_decision` | `batch-2:quality_check/人工质检-交付任务与行动项机制.txt#3. 需求对齐机制; 3.1 完整字段域` | 交付任务是长期维护边界 |
| f003-action-items：非标准行动项作为交付任务之外的可跟踪事项，至少需要标题、归属任务、责任人、截止时间、状态、优先级、风险和闭环结论，并暴露临期、逾期、缺责任人/截止时间、阻塞及未闭环阻碍阶段推进的事项。 | `current_decision` | `batch-2:quality_check/人工质检-交付任务与行动项机制.txt#4. 非标准行动项` | 行动项与交付中心 |
| f004-state-separation：交付阶段、健康状态、行动项状态和验收结论是四个独立状态维度，前端不应合并为单一状态标签。 | `current_decision` | `batch-2:quality_check/人工质检-交付任务与行动项机制.txt#6. 四类状态分离` | 四条互不替代的状态轴 |
| f005-delivery-forecast：交付时间判断应保留目标交付、预计标注完成、预计验收完成、验收预留时长及提前/延迟，并识别倒排计划中已偏离的环节及其传导风险。 | `unknown` | `batch-2:quality_check/人工质检-交付任务与行动项机制.txt#7. 交付时间判断` | 交付任务是长期维护边界 |
| f044-delivery-center：交付中心承接完整交付任务跟踪与编辑，使用同一任务集合提供表格和时间轴视图；保存视图只保存筛选、排序、列配置和展示模式，不复制任务。 | `target_design` | `batch-2:quality_check/质检平台-人工质检交付中心前端设计.txt#1-5; 7-8` | 行动项与交付中心 |
| f045-delivery-deeplink：总览到交付中心的上下文下钻必须把 stage、topic、priority、window、risk 编入 URL，渲染为可删除筛选 Chip 并真实改变任务结果，刷新/分享后保持一致。 | `target_design` | `batch-2:quality_check/质检平台-人工质检交付中心前端设计.txt#10. 导航与状态保持; 10.1 上下文深链` | 行动项与交付中心 |
| f046-delivery-unknowns：交付中心待确认移动端能力、需求对齐会议模式、时间轴粒度和行动项评论/附件/提醒订阅。 | `unknown` | `batch-2:quality_check/质检平台-人工质检交付中心前端设计.txt#13. 待后续确认; 14. 可交互原型` | 边界与未知 |
| f047-delivery-surface：交付中心的关键交互是局部保存、区分无值/未知/不适用、批量编辑显示范围、时间轴表达计划与实际，并用文本和图标表达行动项临期/逾期。 | `target_design` | `batch-2:quality_check/质检平台-人工质检交付中心前端设计.txt#6. 编辑交互; 9. 行动项面板; 11. 与总览关系` | 行动项与交付中心 |
| f052-annotation-center：标注中心是标注作业与分析工作台，承接进入标注阶段的任务，覆盖分配、进度、日标效、Good/Bad、Bad Top5 和风险处理，而非只读报表。 | `target_design` | `batch-2:quality_check/质检平台-人工质检标注中心前端设计.txt#页面任务; 任务队列` | 行动项与交付中心 |
| f053-annotation-boundary：标注中心工作区按总览、任务分配、日进度与标效、Good/Bad分析、Bad原因与行动项组织；任务行下钻通过 URL task 参数打开对应任务，总重大状态推进需二次确认并写审计记录。 | `target_design` | `batch-2:quality_check/质检平台-人工质检标注中心前端设计.txt#单任务工作区; 操作边界` | 行动项与交付中心 |

### [人工质检验收生命周期](../domains/quality/manual/acceptance/lifecycle.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f011-three-phase：人工质检分为标注、验收、执行三阶段：标注员产出逐 clip good/bad/选项结果，验收员只对抽样集产出 PASS/REJECT 支撑结论，执行阶段依据结论对该类别标注全集执行通过或打回。 | `current_decision` | `batch-2:quality_check/人工质检-标注验收执行三阶段流程.txt#① 三阶段定义; ⑤ 与通过打回规则组件的关系` | 人工质检验收生命周期与阶段边界 |
| f012-execution-granularity：执行阶段范围可按 good/bad、选项、任务、组或人变化，ExecutionService 需要接收执行范围并据此反查具体 task_ids。 | `target_design` | `batch-2:quality_check/人工质检-标注验收执行三阶段流程.txt#③ 执行粒度（可变）` | 人工质检验收生命周期与阶段边界 |
| f034-eventual-consistency：Delta 接口即时返回不等于最终成功量：请求量、即时成功/失败与状态回查确认的实际成功量必须分开；快照中的 acceptance_allocated 设计为回查确认的实际量，缺口显式展示。 | `target_design` | `batch-2:quality_check/质检平台-Delta调用与状态回查设计.txt#5.3-5.6; 5.8` | 现实形态 |

### [验收数据流与快照状态](../domains/quality/manual/acceptance/data-flow-and-state.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f041-scene-hierarchy：scene_name 是上游送入人工质检的一批同类场景/采集/挖掘数据的任务组标识和最小管理范围；clip/task 才是可采样、可执行并需逐任务检查状态的操作单元。 | `current_decision` | `batch-2:quality_check/质检平台-scene_name概念.txt#①; ⑤ 1-2, 6` | 人工质检验收数据对象、数据流与状态 |
| f042-scene-extraction：scene_name 的提取依赖项目命名结构：材料给出 e2e 使用 SPLIT_PART(task_name, "_", 2)，vpd 使用 SPLIT_PART(task_name, "_", 3)。 | `target_design` | `batch-2:quality_check/质检平台-scene_name概念.txt#③ 数据表交互; ④ 子模块清单` | 人工质检验收数据对象、数据流与状态 |
| f043-scene-key-conflict：scene_name 材料的快照联合键图和查询示例仍使用 annotator_id，而 Repository/人力重设计已改为 employee_id；这是字段迁移期间的冲突，当前快照键应以直接 Schema 裁决。 | `conflict` | `batch-2:quality_check/质检平台-scene_name概念.txt#概念层级关系图; 4. 快照表如何使用 scene_name` | 状态与未知 |
| f038-snapshot-upsert：快照 UPSERT 只更新统计列和维护时间，不得覆盖 execution、confirmed_*、executed_*、good_conclusion/bad_conclusion 等人工执行字段；联合键为 stat_date、scene_name、group_name、employee_id。 | `current_decision` | `batch-2:quality_check/质检平台-Repository与数据库访问设计.txt#6. 快照查询口径; 7. UPSERT与约束` | 人工质检验收数据对象、数据流与状态 |
| f065-snapshot-min-row：快照表设计以 stat_date×scene_name×group_name×employee_id 为最小统计单元，聚合结果通过 GROUP BY 计算；不保存 clip/task 列表，执行时反查 Delta 原始表。 | `current_decision` | `batch-2:quality_check/质检平台-综合快照表设计.txt#①; ⑤ 1-2; 边界情况2` | 人工质检验收数据对象、数据流与状态 |
| f066-snapshot-refresh：目标刷新链路由 Airflow 每 30 分钟覆盖最近 4 天，直连 Delta ODS 原始表一次取全量任务，Python 层区分标注与验收子集，按当前有效人力补 team_leader/project_name 后 UPSERT 快照。 | `target_design` | `batch-2:quality_check/质检平台-综合快照表设计.txt#② 快照刷新数据流; 12. 定时刷新机制; 13. 边界情况` | 人工质检验收数据对象、数据流与状态 |
| f067-snapshot-jsonb-conflict：快照材料前部描述 26 字段和 good/bad 独立列，后部 V20260709_01 又声明删除 13 列、改为 18 字段+good_metrics/bad_metrics/option_metrics JSONB；这是版本结构冲突，最新结构不能仅凭该文档确定。 | `conflict` | `batch-2:quality_check/质检平台-综合快照表设计.txt#顶部重设计说明; ⑧ V20260709_01 JSONB重构更新` | 状态与未知 |
| f068-snapshot-unknowns：快照材料把 SnapshotRepository、StatService、DAG 和 JSONB 重构列为待实现/待验证，同时引用多个未在本批授权来源中提供的 ODS Schema、解析器和迁移文件。 | `unknown` | `batch-2:quality_check/质检平台-综合快照表设计.txt#⑥ 完成情况与 TODO; ⑧` | 状态与未知 |
| f072-passrule-conflict：通过/打回材料前部以 conclusion/is_executed 标量描述执行字段，后部声明 V20260709_01 已迁移至 JSONB exec_status/conclusion；与快照设计材料的 26字段/18字段冲突共同构成版本冲突。 | `conflict` | `batch-2:quality_check/质检平台-通过打回规则与执行设计.txt#③ 数据表交互; 5.7; ⑧` | 状态与未知 |
| f088-contract-migration：契约记录从旧 t_personnel/annotator_id/join_date 到 t_data_check_screeners/employee_id/id/start_time/end_time/team_leader 的迁移，以及 project_name 从 task_name 前缀推断、快照 group_name 写入即冻结的边界。 | `historical` | `batch-2:quality_check/验收前置条件-快照刷新四级实现契约.txt#顶部 V20260714适配说明; ②时序; 规范消化清单` | 人工质检验收数据对象、数据流与状态 |

### [验收采样、配额与通过规则](../domains/quality/manual/acceptance/sampling-and-assignment.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f013-pass-rate-safety：通过率应以已完成验收数作为分母，而非分配数；执行前要重新聚合指标并重算结论，避免基于过期页面数据执行。 | `current_decision` | `batch-2:quality_check/人工质检-标注验收执行三阶段流程.txt#⑤ 与通过打回规则组件的关系` | 人工质检验收采样、选择与分配 |
| f018-acceptance-rate-conflict：该总览材料写明验收通过率按“通过数之和 / 分配数之和”计算，但三阶段流程材料明确要求以 completed 为分母，二者形成业务口径冲突。 | `conflict` | `batch-2:quality_check/人工质检总览信息架构.txt#2.6 验收健康` | 人工质检验收采样、选择与分配 |
| f060-acceptance-rate-conflict：验收中心质量视图把 Good/Bad 打回比例分母写为各自分配数，而三阶段流程材料要求通过率以 completed 为分母；这是同一批材料中的再次口径冲突。 | `conflict` | `batch-2:quality_check/质检平台-人工质检验收中心前端设计.txt#4.2 质量视图` | 人工质检验收采样、选择与分配 |
| f069-passrule-separation：通过/打回设计分离规则计算与执行：PassRule 只接收聚合指标输出 PASS/REJECT/PENDING、原因和细节；ExecutionService 负责 preview、权限、重算校验、task 状态重查和 Delta 调用。 | `target_design` | `batch-2:quality_check/质检平台-通过打回规则与执行设计.txt#①-②; 5.4-5.6; 5.9` | 人工质检验收采样、选择与分配 |
| f070-passrule-historical：材料记录旧版规则事实：完成度达到应抽或总提交 95% 才进入判定；Good/Bad 样本占比充足时阈值约 95%/80%，不足 90% 时用总通过率约 95% 兜底，边界严格大于；旧版打回调用两次并等待 60 秒。 | `historical` | `batch-2:quality_check/质检平台-通过打回规则与执行设计.txt#5.3 现有规则; 边界事实; 打回2次调用` | 人工质检验收采样、选择与分配 |
| f076-sampling-separation：采样设计分离“算多少”和“取哪些”：Sampler 只从快照最小行计算 SamplingQuota，Repository 在 preview 选择满足 waiting_review 和 Good/Bad 分类的 task_ids，AssignmentService 编排 preview/execute。 | `target_design` | `batch-2:quality_check/质检平台-验收采样配额与任务选择设计.txt#①-②; 5.1-5.2; 5.5; 5.8` | 人工质检验收采样、选择与分配 |
| f077-sampling-strategies：三种采样策略为 GroupSampler、PersonalSampler、RatioSampler：组目标 min(组员数×90,300)，个人目标 90，默认 Good/Bad 各 50%，一侧不足时由另一侧补足；RatioSampler 接受目标量和 Good 比例并校验范围。 | `historical` | `batch-2:quality_check/质检平台-验收采样配额与任务选择设计.txt#④ 类清单; 5.3 三种策略; 5.4; 5.6` | 人工质检验收采样、选择与分配 |
| f078-sampling-registry：SAMPLER_REGISTRY 是采样策略名称、描述和实现的唯一来源，前端 /samplers 直接读取，不另维护 SamplerName Enum。 | `target_design` | `batch-2:quality_check/质检平台-验收采样配额与任务选择设计.txt#②; 5.7` | 人工质检验收采样、选择与分配 |
| f079-sampling-unknowns：采样实现仍待确定 GroupSampler 奇数余量归属、task_ids 稳定/随机排序、验收员池从硬编码迁移方式和测试矩阵；sampler.py 尚未由本材料证明已实现。 | `unknown` | `batch-2:quality_check/质检平台-验收采样配额与任务选择设计.txt#5.3; 5.4; 5.5; ⑥ TODO` | 人工质检验收采样、选择与分配 |
| f057-plan-unknowns：实施计划仍把 Delta 状态字段/值、preview/execute Schema、回查示例深度、抽样比例与上限、通过率阈值、规则配置化、task_rollback 两次调用和人员导入方式留给人类决策。 | `unknown` | `batch-2:quality_check/质检平台-人工质检模块实施计划.txt#§6 待决疑问区` | 人工质检验收采样、选择与分配 |

### [验收结论与执行](../domains/quality/manual/acceptance/conclusion-and-execution.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f030-preview-execute：高风险验收操作采用 preview→execute：preview 按筛选、策略和参数返回汇总、具体 task_ids、warnings 与 generated_at；execute 原样携带 task_ids，不重新随机采样，并逐项重查当前状态。 | `target_design` | `batch-2:quality_check/质检平台-API契约与前端交互设计.txt#请求/响应时序图; preview→execute契约; 状态变化处理` | 验收结论与执行 |
| f035-delta-history：材料记录了历史 Delta 接口与状态映射：批量接口有 300/500 条单批上限，状态包含待审核 66、验收中 69、已完成 70，打回是动作而非状态。 | `historical` | `batch-2:quality_check/质检平台-Delta调用与状态回查设计.txt#5.2.1-5.2.8; 5.3` | 验收结论与执行 |
| f036-delta-unknowns：Delta 集成仍有未完成边界：新版 delta_client.py、配置落地、fake/integration 回查验证和真实外部契约复核尚未开始；密钥必须来自环境变量且真实写接口需显式启用。 | `unknown` | `batch-2:quality_check/质检平台-Delta调用与状态回查设计.txt#5.7-5.9; ⑥ 完成情况与 TODO` | 验收结论与执行 |
| f071-passrule-state-machine：V20260709_01 目标设计把执行进度迁入每个 good/bad/option JSONB 维度的 exec_status：NULL→PENDING→PASS/REJECT_EXECUTING→DONE，终态不可逆；执行失败留 EXECUTING 由重试或人工介入。 | `target_design` | `batch-2:quality_check/质检平台-通过打回规则与执行设计.txt#⑧ exec_status状态机与执行DAG更新` | 验收结论与执行 |

### [人员、筛选员与权限边界](../domains/quality/manual/personnel-and-permissions.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f006-screener-redesign：人力主表的目标/当前设计从 t_personnel 切换为 t_data_check_screeners，采用 SCD Type2；同一 employee_id 可有多行，复合主键为 (employee_id, id)，end_time IS NULL 表示当前有效行。 | `current_decision` | `batch-2:quality_check/人工质检-人力管理体系设计.txt#顶部重设计说明; 2.1 t_data_check_screeners` | 人员历史模型 |
| f007-scd-transition：人员变更按 SCD Type2 封版：同一事务关闭当前 end_time IS NULL 的旧行，再插入新行，并记录 t_personnel_op_log；查询当前状态必须过滤 end_time IS NULL，历史快照按 start_time/end_time 区间查询。 | `current_decision` | `batch-2:quality_check/人工质检-人力管理体系设计.txt#2.1 SCD Type2设计说明; ④ 子模块清单` | 人员历史模型 |
| f008-personnel-rules：人力规则区分标注员、验收员和内部抽检员：供应商冲突校验适用于同一任务的标注员与验收员；分组 team_leader 只对标注员有意义；人员同时只属于一个 project_name。 | `current_decision` | `batch-2:quality_check/人工质检-人力管理体系设计.txt#⑤ 1. 人力分类体系; 3. 分组(team_leader)的作用` | 业务约束 |
| f009-personnel-permission：权限模型以 employee_id 对接 SSO JWT sub，并按 acceptance_access、personnel_access 和 is_admin 进行后端授权；前端隐藏按钮不是安全边界。 | `target_design` | `batch-2:quality_check/人工质检-人力管理体系设计.txt#2.3 t_portal_permission; 6. SSO鉴权接入设计` | 权限目标与现实边界 |
| f010-personnel-unknowns：人力体系仍有明确未完成边界：PersonnelService 物理实现、SCD 与 op_log 事务上下文、真实 SSO 参数、内部抽检一致率算法及前端新字段适配均待补充。 | `unknown` | `batch-2:quality_check/人工质检-人力管理体系设计.txt#⑥ 完成情况与 TODO` | 权限目标与现实边界 |
| f014-identifier-conflict：材料将 annotator_id 解释为可直接使用的 employee_id，并在末尾将 SCD Type2 的复合主键描述为 (employee_id, join_date)。 | `conflict` | `batch-2:quality_check/人工质检-标注验收执行三阶段流程.txt#⑥ 关键业务概念澄清` | 业务约束 |
| f032-api-personnel-conflict：API 材料的 t_personnel_op_log 表字段将被操作人员字段写为 personnel_id，而人力设计使用 employee_id；且 API 材料将契约设计描述为待实现。 | `conflict` | `batch-2:quality_check/质检平台-API契约与前端交互设计.txt#③ 数据表交互; ⑥ 完成情况与 TODO` | 业务约束 |
| f075-model-unknowns：领域模型材料明确 acceptance/models.py、personnel/models.py、API schemas 和具体上移决策均待实际复用/实现后确认。 | `unknown` | `batch-2:quality_check/质检平台-领域模型层设计.txt#③ 数据表交互; ⑥ 完成情况与 TODO` | 权限目标与现实边界 |

### [质检平台软件边界与实现路线](../domains/quality/manual/platform-and-module-map.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f019-demo-boundary：统一质检平台 Demo 的目标是用离线 HTML 原型承载业务总览、人工质检、自动化质检、大模型质检和专题数据质量五块页面；它是交互证明，不冒充后端已接入。 | `target_design` | `batch-2:quality_check/质检一站式平台前端Demo设计计划.txt#Demo目标; 页面范围; 必须可操作的用户路径` | 模块与边界 |
| f021-demo-current-boundary：材料将 Demo 当前状态区分为已覆盖总览与占位下级明细：交付中心有需求对齐可编辑 Demo，验收中心、人力和分组仍是占位；后端 API、SSO、真实权限、真实指标和文案审批待后续接入。 | `unknown` | `batch-2:quality_check/质检一站式平台前端Demo设计计划.txt#当前实现状态; 本轮重设计范围` | 模块与边界 |
| f024-layer-boundary：顶层架构规定 Router、Application Service、Domain/Repository、DB 的职责边界：Router 不碰 SQL，Service 编排事务，Repository 集中参数化 SQL，跨模块调用经公开 Service 边界。 | `target_design` | `batch-2:quality_check/质检一站式平台顶层架构.txt#§4; §5` | 模块与边界 |
| f025-shared-ownership：公共设计只有在两个及以上模块复用或必须全平台一致时才上移；平台层维护公共契约和最小组件 API，不吞并人工质检采样/通过打回/人力归属等模块规则。 | `current_decision` | `batch-2:quality_check/质检一站式平台顶层架构.txt#§0.5; §9.1` | 模块与边界 |
| f029-api-contract：人工质检 API 设计以 Pydantic schema/ FastAPI OpenAPI 作为前端契约事实源，内部 dataclass、数据库列和前端 TypeScript 类型不直接互替；路由统一在 /api/v1/manual-qc/ 下分 acceptance 与 personnel。 | `target_design` | `batch-2:quality_check/质检平台-API契约与前端交互设计.txt#①; ② API路由树; ⑤ 统一约定` | 模块与边界 |
| f031-api-unknowns：API 设计仍待确认 Delta 单批 task_ids 上限与超时、真实状态码与完成/打回语义映射、是否需要导出接口，以及 acceptance.py/personnel.py 是否已存在。 | `unknown` | `batch-2:quality_check/质检平台-API契约与前端交互设计.txt#⑤ 待确认项; ⑥ 完成情况与 TODO` | 模块与边界 |
| f033-delta-boundary：DeltaClient 是人工质检调用 Delta 的唯一外部出口，负责基址、认证、超时、批量拆分、HTTP 错误解析和响应标准化，不负责采样、权限、统计或数据库写入。 | `target_design` | `batch-2:quality_check/质检平台-Delta调用与状态回查设计.txt#①; ② Delta调用与回查架构; 5.2` | 模块与边界 |
| f037-repository-ownership：人工质检 Repository 层是 SQL 唯一入口，按表族拆为 ScreenerRepository、SnapshotRepository、LabelTaskRepository 和 AcceptanceTaskRepository，不建立万能 Repository；Service 不直接接触数据库。 | `target_design` | `batch-2:quality_check/质检平台-Repository与数据库访问设计.txt#①; ② 类图与数据流; 4. 数据库与连接选择` | 模块与边界 |
| f039-query-simplification：同一任务表字段集相同且过滤条件存在子集关系时，采用“一张表一个统一查询方法+可选过滤参数”：LabelTaskRepository.fetch_tasks_raw 统一查询，task_status/scene_name 在 Python 层分支处理。 | `current_decision` | `batch-2:quality_check/质检平台-Repository与数据库访问设计.txt#10. 一张表一个统一查询方法 + 可选过滤参数模式` | 模块与边界 |
| f040-repository-unknowns：Repository 设计仍待直接核对公共连接器 API、execute_values 写路径、Delta 单批限制、多语句事务 context 和临时 PostgreSQL 集成测试；材料的物理实现/QA声明不可在本批直接验证。 | `unknown` | `batch-2:quality_check/质检平台-Repository与数据库访问设计.txt#3. 公共数据库能力复用; 11. 测试要求; ⑥ TODO` | 模块与边界 |
| f054-implementation-roadmap：人工质检实施路线按 Phase 0 调研、Phase 1 架构、Phase 2 DDL、Phase 2.5 契约冻结、Phase 3 后端、Phase 4 前端、Phase 5 联调推进；实施计划强调端到端联调不能由 Swagger 可打开替代。 | `target_design` | `batch-2:quality_check/质检平台-人工质检模块实施计划.txt#§1; §2.1; §2.8` | 模块与边界 |
| f055-plan-conflict：实施计划同一文档前部将 repository.py/service.py 描述为方法体均为 NotImplementedError，后部 V20260709_01 又声明 Repository/Service 已实现并新增 exec_status、delta_client、execution_service 和两个 DAG；这是文档内部时间版本冲突。 | `conflict` | `batch-2:quality_check/质检平台-人工质检模块实施计划.txt#§2.1-§2.3; §10 V20260709_01` | 模块与边界 |
| f056-plan-contracts：实施计划冻结的关键契约包括快照最小粒度、模块等级权限、Repository/Service 边界、Delta 外部状态回查、通过率规则和执行全集语义，但旧版事实、目标设计和当前落地必须分开。 | `historical` | `batch-2:quality_check/质检平台-人工质检模块实施计划.txt#§2.5-§2.6; §5; §6` | 模块与边界 |
| f062-backend-boundary：人工质检后端采用 HTTP、应用编排、纯规则、数据/外部调用四层：Router/Schema/Auth→Service→Sampler/PassRule与Repository/DeltaClient；规则层不访问数据库或网络，Repository 是 SQL 唯一入口。 | `target_design` | `batch-2:quality_check/质检平台-后端分层与组件边界设计.txt#①-②; ⑤ 2. 组件职责` | 模块与边界 |
| f063-backend-simplicity：当前设计不提前引入 ports/adapters/domain 套件：只有一个 PostgreSQL 公共模块、一个 Delta 平台和少量规则，先用构造注入 fake；出现第二个可替换平台或替身难以注入时再抽接口。 | `current_decision` | `batch-2:quality_check/质检平台-后端分层与组件边界设计.txt#⑤ 3. 为什么不用 ports/adapters/domain 套件` | 模块与边界 |
| f064-backend-unknowns：后端分层材料明确 src/api、src/manual_qc 和 src/database 的实际目录/API、import检查、API冒烟和三条端到端示例仍待核对或验证。 | `unknown` | `batch-2:quality_check/质检平台-后端分层与组件边界设计.txt#② 目标目录; ⑥ 完成情况与 TODO` | 模块与边界 |
| f073-model-placement：数据结构按变化速度和实际复用就近放置：采样结构在 sampler.py，规则结果在 pass_rules.py，数据库行映射靠近 Repository，人员结构在 personnel/models.py，HTTP 请求响应在 api/schemas；只有至少两个组件稳定复用才上移。 | `current_decision` | `batch-2:quality_check/质检平台-领域模型层设计.txt#①; ② 类图; ⑤ 5.1-5.3` | 模块与边界 |
| f074-model-registry：采样策略和规则名称由 SAMPLER_REGISTRY/RULE_REGISTRY 作为唯一发现与校验来源，不再另建 SamplerName/RuleName Enum；封闭业务状态才适合保留 Enum。 | `target_design` | `batch-2:quality_check/质检平台-领域模型层设计.txt#④; ⑤ 5.4` | 模块与边界 |
| f087-four-level-contract：快照刷新实现契约分为 DDL→Repository→Service→Airflow DAG：全量任务查询、单遍历双累加、人员 enrich、统计列 UPSERT 和 30 分钟调度。 | `target_design` | `batch-2:quality_check/验收前置条件-快照刷新四级实现契约.txt#①-②; Task 3-5` | 模块与边界 |
| f089-contract-conflict：契约材料同时称 Task 3/4/5 待实现，又在 TODO 末尾称 Task 3/4 已物理实现；还同时描述 26字段旧快照与后续 JSONB 重构，形成文档版本冲突。 | `conflict` | `batch-2:quality_check/验收前置条件-快照刷新四级实现契约.txt#② 文件清单; ⑥ 完成情况与 TODO` | 模块与边界 |
| f090-contract-gaps：契约的直接验证仍缺 Task 5 DAG 导入冒烟、当前数据库/目录真实状态、JSONB/旧标量结构裁决以及实际端到端刷新结果；本批材料不能代替这些证据。 | `unknown` | `batch-2:quality_check/验收前置条件-快照刷新四级实现契约.txt#⑥ 完成情况与 TODO` | 模块与边界 |

### [统一数据工作台与平台共享契约](../capabilities/quality-data-workbench.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f020-demo-shared：Demo 规划了跨模块共享的 AppShell、FilterBar、DataTable、DetailDrawer、StatusBadge、AsyncActionPanel、ConfirmDialog 和反馈组件，分别承载导航权限、筛选视图、表格状态、上下文下钻、状态编码、异步执行回查和危险操作确认。 | `target_design` | `batch-2:quality_check/质检一站式平台前端Demo设计计划.txt#共享组件与状态; 视觉方向草案; 设计拨盘与实现约束` | 共享边界 |
| f023-platform-shared-contract：平台级共享契约包括统一壳层、筛选/保存视图/表格/状态/抽屉/批量确认、异步状态、危险操作 preview→confirm→execute→refresh、OneTrack 权限和 URL 上下文下钻。 | `target_design` | `batch-2:quality_check/质检一站式平台顶层架构.txt#§0.3 全局共享能力; §0.4 前端统一信息架构` | 共同交互契约 |
| f080-dashboard-layout：质检平台看板采用 DashboardLayout→CardShell→内容原子三层模型：布局负责位置/尺寸/所有权/版本，卡片壳负责标题/更新时间/权限/刷新/下钻，内容原子负责指标与图表。 | `target_design` | `batch-2:quality_check/质检平台可配置卡片布局组件设计.txt#定位; 三层模型; 卡片定义` | 共享边界 |
| f081-dashboard-safety：可配置看板支持新建/复制/删除/拖动/缩放/保存/另存为/恢复默认和上下文下钻；公共布局需发布权限和版本记录，个人布局不影响他人。 | `target_design` | `batch-2:quality_check/质检平台可配置卡片布局组件设计.txt#用户能力; 强制覆盖范围; 组合原则` | 安全边界 |
| f082-workbench-stack：统一数据工作台首版技术栈选用 @tanstack/vue-table、@tanstack/vue-virtual、GridStack 和 ECharts；XLSX 导出保持适配器边界，因间接依赖漏洞首版不安装 ExcelJS 4.4.0。 | `target_design` | `batch-2:quality_check/质检平台开源数据工作台实现设计.txt#技术栈` | 共享边界 |
| f083-workbench-boundary：DataWorkbench 负责布局与事件，useDataWorkbench 负责列/筛选/排序/选择/展开状态；首版覆盖父选子/半选、列显隐/宽度、排序、文本/枚举筛选、按日展开、横向滚动和布局序列化。 | `target_design` | `batch-2:quality_check/质检平台开源数据工作台实现设计.txt#组件边界` | 共享边界 |
| f084-data-workbench-contract：统一数据工作台由 QueryBar、ViewManager、BatchActionBar、ColumnEngine、GroupedHeader、HierarchyRows、AnalysisBuilder、Exporter 和 PagerAndScroll 组成；业务页只提供列、数据源、权限、批量动作和展开维度。 | `target_design` | `batch-2:quality_check/质检平台统一数据工作台组件设计.txt#定位; 组件分层; 列契约; 布局配置` | 共同交互契约 |
| f085-data-selection-safety：批量操作的选择契约区分当前页、筛选全部、逐行和展开子行；聚合行不是执行对象，服务端以 explicit_ids 或 filter_snapshot+excluded_ids 表达跨页叶子选择，危险操作遵循选择→预览→冻结集合→权限/版本复核→执行→回查→审计。 | `target_design` | `batch-2:quality_check/质检平台统一数据工作台组件设计.txt#行选择与批量动作; 父子选择联动; 层级行` | 共同交互契约 |
| f086-data-workbench-guard：所有业务数据表格必须通过统一数据工作台或薄封装实现；视口底部悬浮横向滚动、键盘可用、权限不足不渲染编辑控件、预览期间数据变化需阻断或要求重新预览，均属于共享验证门槛。 | `target_design` | `batch-2:quality_check/质检平台统一数据工作台组件设计.txt#一键分析; 强制覆盖范围; 视口级横向滚动; 验证清单` | 安全边界 |
| f061-acceptance-accessibility：验收中心要求延迟查询显示骨架/局部加载、写操作防重复点击、部分失败仅重试失败子集、状态用文字和图标双编码、图表提供可键盘访问的数值表格，并显示统计/刷新时间。 | `target_design` | `batch-2:quality_check/质检平台-人工质检验收中心前端设计.txt#6-7` | 安全边界 |

### [人工质检前端状态与验收工作台](../domains/quality/manual/acceptance/python-architecture-and-implementation.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| f048-fe-state-machine：人工质检前端的验收分配页使用六态状态机 idle→previewing→preview_ready→executing→executed→refreshing；修改筛选或策略必须使旧 preview 失效，execute 原样使用 preview task_ids。 | `target_design` | `batch-2:quality_check/质检平台-人工质检前端页面与状态设计.txt#② 分配页状态机; ⑤ 分配页/统计页/通过打回页` | 人工质检前端状态与验收工作台 |
| f050-fe-implementation-boundary：前端材料将目录、组件和六态交互描述为 Phase 4 设计目标，并明确前端目录与组件尚未在仓库物理实现；人力画像中仍出现 level/unit_price 等旧字段，与人力主表重设计不一致。 | `conflict` | `batch-2:quality_check/质检平台-人工质检前端页面与状态设计.txt#④ 子模块清单; ⑤ 人力页面; ⑥ 完成情况与 TODO` | 人工质检前端状态与验收工作台 |
| f051-fe-acceptance：前端产品验收应覆盖路由/权限/深链、交付表格与时间轴、行动项定位、preview 参数变化清空旧结果、原 task_ids execute、部分失败/跳过/刷新、统计计算时间和人员操作日志 ID。 | `target_design` | `batch-2:quality_check/质检平台-人工质检前端页面与状态设计.txt#⑤ Phase 4 验收; 前端产品验收` | 人工质检前端状态与验收工作台 |
| f058-acceptance-center：验收中心按数据集交付任务聚合，向下展开 scene→组→标注员/验收员→task；提供进度、质量、效率三套列视图和单需求验收工作区。 | `target_design` | `batch-2:quality_check/质检平台-人工质检验收中心前端设计.txt#0. 工作台深化决策; 1-5` | 人工质检前端状态与验收工作台 |
| f059-acceptance-refresh：验收分配与通过/打回的界面流程均要求确认、执行和回查；展示请求、实际发送、成功、跳过、失败和待回查，并在结果区保留当前交付上下文。 | `target_design` | `batch-2:quality_check/质检平台-人工质检验收中心前端设计.txt#5.2-5.5; 9. 可交互原型` | 人工质检前端状态与验收工作台 |

### [质检领域与人工质检工作旅程视图](../views/by-domain/quality.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| 无 | 无 | 无 | 无 |

### [质量领域概览语义同步](../domains/quality/overview.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| 无 | 无 | 无 | 无 |

### [验收实现地图语义同步](../domains/quality/manual/acceptance/implementation-map.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| 无 | 无 | 无 | 无 |

### [验收开放问题语义同步](../domains/quality/manual/acceptance/open-questions.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| 无 | 无 | 无 | 无 |

### [验收总览语义同步](../domains/quality/manual/acceptance/overview.md)

| 直接材料结论 | 现实形态 | 精确定位 | 正文章节 |
|---|---|---|---|
| 无 | 无 | 无 | 无 |

## 使用边界

- 路径和定位来自摄入开始时冻结并在登记时重新校验的来源；来源变化后必须重新摄入。
- 当前实现、当前决定、目标设计、历史、冲突和未知不能互相替代。
- 表中的正文落点只证明写作者完成了逐项对照，不自动证明业务结论正确；发布仍需人工审查。

<!-- omni-brain:incremental-provenance:end -->
