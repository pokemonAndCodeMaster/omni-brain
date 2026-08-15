# 当前工作台

> 更新时间：2026-08-16
> 本页只回答：**现在到哪里、产物在哪里、下一步做什么**。完整用例与 Trial 看
> [Eval 总账](../eval/STATUS.md)，长期架构看 [Blueprint](blueprint.md)。

## 当前结论

**分阶段方案形成已经达到首个可发布切片，下一步进入批准方案下的真实开发。**

用户批准的“人工质检多维结果分析”R1 v0.4 与 R2 v0.7 已固化为认证参考。Agent 随后冻结输入、
反馈、六维评分和关键失败条件，独立比较 DeepSeek 候选、修改通用 Harness 并回归。最终结果：

- 复杂目标任务：OpenCode DeepSeek 两次独立候选均达到 `16/18`，六维不低于 2 且无关键失败；
- 简单局部修改：直接编辑并验证，不创建方案审查页；
- 缺少批准证据：只检查当前审查入口，找不到后索取路径，不读产品代码或历史实验；
- Harness：`/home/yyh/project/omni-brain-harness`，统一远端消费分支
  `release/harness`；实验分支不作为使用入口。

方案形成能力当前标记为
`verified_at_deepseek_complex_solution_and_routing_slice`。这只证明**单一质检系统中的复杂需求、
分阶段方案和两类路由行为**，不代表跨领域或所有模型已经验证。

## 实际由什么组成

| 实体 | 作用 |
|---|---|
| `omni-brain-harness/AGENTS.md` | 在直接执行、有界上下文、先形成方案、按批准方案开发和事后审查之间路由 |
| `.agents/skills/form-solution/SKILL.md` | 先形成 R1 需求理解，再做最低充分查证并形成 R2 可施工方案 |
| `.agents/skills/form-solution/references/software-solution.md` | 复杂软件方案的系统位置、数据流、模块、接口、迁移、验证与决策结构 |
| `workspaces/reviews/<task-id>/review.md` | 用户唯一需要阅读和反馈的本地审查入口 |

没有新增需求 YAML、方案账本、模型 API 或专题脚本。阶段状态和反馈都在同一张 Markdown
审查页中；事实仍来自用户请求、当前知识、源码和必要运行结果。

## 结果去哪里看

- [用户批准的 R1/R2 认证参考](../workspaces/reviews/manual-qc-multidimensional-result-analysis/review.md)
- [冻结输入、反馈、评分和晋升规则](../eval/datasets/solution_formation/manual_qc_multidimensional_result_analysis_v1.yaml)
- [第一份独立通过候选](../eval/trials/solution_formation/SOLUTION_FORMATION_HARNESS_OPENCODE_DEEPSEEK_005/review.md)
- [第二份独立通过候选](../eval/trials/solution_formation/SOLUTION_FORMATION_HARNESS_OPENCODE_DEEPSEEK_009/review.md)
- [全部迭代、失败原因和适用边界](../eval/trials/solution_formation/audit.md)

## 下一步

**方案形成实验已经收敛；当前进入“按批准方案真实开发”的下一环。**

真实输入使用用户纠偏后的“人工质检多维结果分析”诉求。用户否决了“有序分析维度、固定逐级
展开、只读首个纵切”的旧方案假设，并进一步明确：默认按项目与任务展示，其他维度聚合；聚合
维度按需勾选；任意未聚合维度均可整列或单行展开；行选择优先导出；详情窗口上方按每个剩余
维度各放一张分析图，下方复用公共多维表格；当前快照表全部数据和可计算的标注、验收指标均在
需求范围内。

- 唯一审查入口：
  [`workspaces/reviews/manual-qc-multidimensional-result-analysis/review.md`](../workspaces/reviews/manual-qc-multidimensional-result-analysis/review.md)；
- R1 v0.4 已按“目标与主要问题 → 完整使用过程 → 产品模块与职责 → 数据和业务规则 →
  需求范围与验收”的统一逻辑获得用户批准；
- R2 v0.7 已按两轮架构反馈收敛并获得用户批准：现有 1000/10000 仅为临时实现，不作为业务上限；完整性改为
  接口正确性——成功必须取齐、任一分批失败则整体失败，不增加 `complete` 等局部状态或备用路径；
  后端把刷新、Repository、统计规则和 Service 统一收进 `manual_qc/snapshot`，Router 与 Schema
  也归入人工质检快照领域，并以“完整结果集、统计指标定义、聚合统计”三个具体接口替代万能
  `query`；默认导出 XLSX，结构化拆分 JSON，不建设异步导出；没有修改产品代码；
- 任务案 `knowledge-driven-work-harness-design` 已用 `q-014` 记录 R1 批准结果，当前由 `q-015`
  跟踪 R2 v0.7 是否可以成为实施与 Harness 评测基线。

下一步把 R2 v0.7 作为开发输入，由 `develop-with-knowledge` 修改真实前后端、数据库查询和公共组件，
优先取得数据库/API/浏览器用户路径证据；完成后由 `review-work` 生成本地审查页，并由现有摄入能力
提出知识变化候选。用户暂时无需再补充信息；只有开发中出现 R2 未覆盖且会改变产品行为的选择时，
才返回相应章节请求决定。

## 后续顺序

1. 方案形成：模糊诉求 → 合理需求理解与可审方案；
2. 开发执行：批准方案 → 代码、真实运行和变更说明；
3. 本地审查：复用本轮能力评需求、方案、实现和验证；
4. 知识回写：把批准后的代码与设计变化并入长期知识；
5. 换第二类任务或较弱模型，验证泛化后再扩大默认采用范围。
