人工质检验收中最容易混淆的五类对象是：

| 业务对象 | 形成阶段 | 用来做什么 | 不能替代什么 |
|---|---|---|---|
| 候选总体 | 选定交付任务、日期、scene 等范围后 | 定义本轮可被抽样、统计和最终执行的数据边界 | 不能替代具体的验收样本 |
| 验收样本 | 抽样并分配给验收员后 | 供验收员逐条判断质量 | 不能替代对应范围内的标注全集 |
| 验收记录 | 验收员完成人工作业后 | 保存逐样本判断、完成度、分类结果和原因 | 不能替代 PASS/REJECT/PENDING 质量结论 |
| 质量结论 | 规则汇总并经人工确认后 | 决定是否允许进入通过、打回或补验 | 不能替代外部系统中的实际状态 |
| 执行结果 | 调用外部系统并完成状态回查后 | 证明标注全集实际通过、打回或仍不确定 | 不能替代接口返回的即时响应 |

它们必须分开，因为“抽到什么、检查出什么、决定什么、系统实际改成什么”分别属于不同阶段和不同事实，任何一个都不能代替另一个。

依据：[验收生命周期与阶段边界](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/lifecycle.md)、[人工质检验收领域总览](</home/yyh/project/omni-brain-trusted-query-luna-v1/knowledge/domains/quality/manual/acceptance/overview.md)。