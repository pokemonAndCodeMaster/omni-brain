结论：当前正式注册了 **8 项 Harness 能力**，其中 **6 项已在限定切片中验证、1 项仅提供空骨架、1 项是已实现但未验证的候选能力**。

正式判定源是 `harness.yaml`。当前整体阶段虽为 M4 集成发布，但明确是“scoped verification”，不能解释为所有场景均已验证。

| 能力名称 | 采用分类 | 正式 adoption 状态 | 证据与适用边界 |
|---|---|---|---|
| `knowledge_base` | 仅实现 | `implemented_empty_okf_scaffold` | 已有知识入口和领域配置骨架；当前没有正式领域知识或已验证产品视图，目录约定也不是 OKF 标准 taxonomy。 |
| `knowledge_ingestion` | 已验证 | `verified_at_cross_model_incremental_slice` | 聚焦代码、宽范围整理和增量融合有内容证据；增量融合通过两个独立模型重放，并完成过人工批准、发布和干净消费。仅覆盖固定真实材料和少量模型运行；跨领域、OpenCode 实际宿主、部分批准、回滚等未验证。 |
| `knowledge_query_and_context` | 已验证 | `verified_at_quality_check_trusted_query_slices` | 确定性路由通过十个质检问法，并有较弱模型实际查询切片。证据限于中文 Markdown、单一宿主/模型、单一质检领域及最多三篇规范页；第二领域、大规模知识、精确源码联查未验证。 |
| `knowledge_guided_development` | 已验证 | `verified_at_four_manual_qc_development_and_one_trusted_context_composite_slice` | 四类人工质检开发用例和一个可信上下文复合切片成功；覆盖两种宿主/模型组合，但领域仍是同一质检系统。不包含自动上下文组装、环境管理或正式知识自动发布；CSV 写库案例因输入不完整不计入已验证切片。 |
| `local_work_review` | 已验证 | `verified_at_deepseek_software_review_positive_mismatch_no_trigger_slice` | DeepSeek 软件审查的正向、任务错位和不触发切片已有证据。仅验证本地 Markdown 软件开发审查；知识摄入、方案和 Harness 修改的专属审查未验证，也不会自动收集证据。 |
| `independent_delivery_verification` | 未验证 | `implemented_unverified_candidate` | 入口与契约测试已经实现，但尚无复杂开发 Trial 证明它能阻止错误完成声明。仅面向跨层、公共能力、多消费者等复杂施工；其他宿主还需等价的新上下文机制。 |
| `solution_formation` | 已验证 | `verified_at_deepseek_complex_solution_and_routing_slice` | 同一复杂前后端用例的两个 DeepSeek 重放及两项路由回归通过。只覆盖复杂软件诉求的 R1/R2 形成；证据限于单一质检系统、单一复杂用例和 OpenCode DeepSeek，实际开发交接、第二领域及其他弱模型未验证。 |
| `knowledge_writeback` | 已验证 | `verified_at_manual_qc_same_system_adjacent_writeback_slice` | 同一质检系统的相邻代码增量达到冻结内容接受线。候选必须停在人工审查前；外部契约及数据库状态密集型保留集尚未通过，跨系统、删除退役、冲突改写、第二领域和 OpenCode 实际宿主均未验证。 |

证据边界：

- 上述“已验证”表示 `harness.yaml` 登记的特定 Trial/切片已经验证，不代表跨领域、跨模型、跨宿主或生产规模的普遍保证。
- 我只读确认了清单中登记的所有 entrypoint 文件当前均存在；文件存在只能证明实现入口存在，不能替代内容或行为验证。
- 路线图、设计方案、stub、合成测试及聊天中的临场能力不能增加正式能力清单。
- 本次没有运行历史 Trial，也没有修改任何文件。用户当前无需执行后续操作。
