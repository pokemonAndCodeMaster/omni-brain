# 质检知识阅读体验重构审查

> **状态：** 用户已于 2026-08-09 审查通过，作为认证参考发布到正式 `knowledge/`。
> **目标：** 让第一次接触质检的人从一个入口建立领域全貌，逐层进入人工质检和验收，并能继续业务分析、方案设计或 Python 开发。
> **审查对象：** 候选知识正文、领域视图、学习旅程和本轮改进后的知识摄入 Harness。

## 从这里开始审查

建议只沿下面四个入口阅读，不需要查看摄入状态文件或来源清单：

1. [质检知识入口](draft/knowledge/index.md)：检查知识层级、默认阅读顺序和任务快捷入口；
2. [质检领域全貌](draft/knowledge/domains/quality/overview.md)：检查四类质检业务的位置、职责和当前覆盖；
3. [人工质检全貌](draft/knowledge/domains/quality/manual/overview.md)：检查从需求到交付的业务链、模块协作和角色边界；
4. [人工质检验收总览](draft/knowledge/domains/quality/manual/acceptance/overview.md)：检查验收定位、流程、内部知识结构和深入顺序。

需要继续检查软件内容时，进入[Python 软件结构与实现](draft/knowledge/domains/quality/manual/acceptance/python-architecture-and-implementation.md)；需要检查未知是否清楚，进入[验收待确认事项](draft/knowledge/domains/quality/manual/acceptance/open-questions.md)。

## 候选知识结果

本候选共修改 **22 个用户可见页面**，没有修改不可变原始材料和正式知识。

| 页面组 | 主要结果 | 代表入口 |
|---|---|---|
| 总入口与领域全貌 | 合并大纲、知识地图和默认阅读顺序；先列全业务模块，再说明模块协作与覆盖缺口 | [总入口](draft/knowledge/index.md)、[质检领域](draft/knowledge/domains/quality/overview.md)、[人工质检](draft/knowledge/domains/quality/manual/overview.md) |
| 验收业务知识 | 从业务位置进入生命周期、采样、数据、结论和待确认事项；保留历史规则、目标设计、当前代码和冲突的差别 | [验收总览](draft/knowledge/domains/quality/manual/acceptance/overview.md)、[生命周期](draft/knowledge/domains/quality/manual/acceptance/lifecycle.md) |
| 软件与实现 | 从真实业务动作进入对象、代码结构、调用过程、数据转换、设计取舍和一次修改路径，不以模式名称代替解释 | [系统架构](draft/knowledge/domains/quality/manual/acceptance/system-architecture.md)、[Python 软件结构](draft/knowledge/domains/quality/manual/acceptance/python-architecture-and-implementation.md)、[当前原型](draft/knowledge/systems/manual-qc-acceptance-prototype.md) |
| 交付、人员与公共能力 | 明确长期业务责任、共享能力与领域语义的边界，并保留未实现事实 | [交付与行动项](draft/knowledge/domains/quality/manual/delivery-management.md)、[人员与权限](draft/knowledge/domains/quality/manual/personnel-and-permissions.md)、[公共能力](draft/knowledge/capabilities/index.md) |
| 产品视图 | 领域视图负责逐层下钻，学习旅程按业务、数据规则、软件和核验排序；两者只导航，不维护第二套事实 | [领域视图](draft/knowledge/views/by-domain/quality.md)、[学习与任务旅程](draft/knowledge/views/by-journey/manual-qc-acceptance.md) |

## 本轮统一的表达规则

- 长页面先给可点击导航，开头说明**主题、内容顺序和适用边界**；
- 章节标题使用稳定的名词短语，章节内用贴合内容的短标签标明段落作用；
- 只对决定理解或行动的**关键词、关系和限制**加粗，不整段加粗；
- 同类对象用同维度表格，流程说明输入、处理、输出和进入条件，图表不替代正文信息；
- 引用只负责追溯，业务机制、字段、算法、异常和责任必须在正文中完成内化；
- 当前实现、当前业务决定、目标设计、历史做法、冲突和未知分别呈现；
- 普通读者页面不再出现知识摄入批次、候选版本和内部代号。

## Harness 阶段性结果

本轮已经把上述规则落入 `ingest-knowledge`，而不是只靠当前模型记忆：

- 新增并收敛了总入口、领域全貌、未知与冲突、软件结构和产品视图模板；
- 明确“指定少量既有页面重构”走聚焦模式，避免错误启动完整材料盘点；
- 多个页面责任必须拆成独立读者问题，分别取最低充分来源；
- 模板作者说明使用占位符或 HTML 注释，防止弱模型复制到读者正文；
- `check-unit` 能发现计划页面未修改、模板占位符、结构或链接问题，并只报告当前小批相关警告；
- `record` 现在支持在来源读取结束、正文完成后更新最终摘要和状态，避免 `review.md` 保留过时结论。

DeepSeek V4 Flash 的多轮盲测表明：它已经能选择聚焦模式、加载相应页面模板、形成有实质结构的领域页、未知页和软件页。当前仍有两个限制：弱模型可能把两个页面责任合并成一个大问题，从而读取过多来源；内容虽然明显优于原稿，仍需要人工检查业务模块划分和信息取舍。因此当前成熟度是**有限切片可用、人工审查必需**，不是任意领域全自动可靠。

## 验证结果

| 验证项 | 结果 | 能证明什么 |
|---|---|---|
| Harness 单元与契约测试 | **92/92 通过** | 路由、状态闭环、模板约束和已有工作台行为未回归 |
| 候选知识结构检查 | **通过，0 error / 0 warning** | frontmatter、相对链接、领域登记和结构约束一致 |
| Markdown 文件与锚点检查 | **通过，0 个失效目标** | 当前候选内的标准 Markdown 跳转可解析 |
| 用户页面过程术语扫描 | **通过** | 批次、候选版本、父版本和内部代号只保留在来源/日志维护区 |
| 正式知识保护 | **通过** | 正式 `knowledge/` 与 `config/` 未修改 |

这些检查不能替代业务事实审查。业务公式、生产 Schema、外部接口、真实部署和组织责任仍按正文中的待确认事项处理。

## 人工审查决定

- [x] 总入口、质检领域、人工质检和验收四级阅读主线可以接受；
- [x] 业务模块划分、流程、角色、数据、算法和软件讲解没有重要事实丢失或归位错误；
- [x] 待确认事项的分类、优先级、影响和补知责任符合实际；
- [x] 两种产品视图能够支持第一次学习与实际任务进入；
- [x] 批准把本候选合并到正式 `knowledge/`，并把当前 Harness 版本作为下一阶段实验基线。

正式知识采用本认证参考。后续弱模型输出只作为隔离 Trial，不得覆盖该版本；Harness 的改动必须通过重新盲测证明有效。
