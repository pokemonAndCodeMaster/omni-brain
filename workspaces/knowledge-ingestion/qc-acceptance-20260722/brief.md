# 摄入案入口：人工质检验收

- **Case ID**：qc-acceptance-20260722
- **目标**：只基于用户指定的 `ai-knowledge-base` 与 `omni-brain-m1-input-v1/quality_check`，形成可浏览、可理解、可追溯的人工质检候选知识。
- **状态**：候选已修订，等待人工门禁；不得发布正式知识。
- **范围**：人工质检全貌中的验收定位、交付闭环、验收粒度、快照、抽样/预览、通过打回、Python/API/数据库运行链，以及数据库、OBS、Delta 等相邻能力的真实使用边界。
- **禁区**：不修改来源；不扩展到其他仓库/环境；不把设计目标、旧版行为或测试 fixture 当成当前生产事实。
- **来源基线**：`ai-knowledge-base` Git `3cf393479d59dae57280df3c80a1ff213a936909`，来源工作区有未提交改动；`quality_check` 目录无 Git 基线，实际包含 25 份 `.txt`。
- **正式知识状态**：`knowledge/` 与正式 `config/knowledge-domains.yaml` 保持未修改。

## 必须回答的问题

1. 人工质检在全局交付流程中的位置是什么？
2. 验收从业务动作到 Python/API/数据库的真实链路是什么？
3. 数据库、OBS、Delta 等公共能力在当前实现、旧流程和设计目标中的关系分别是什么？
4. 哪些结论可发布，哪些必须继续标为未知？

## 入口

- [来源盘点](inventory.md)
- [开放问题](questions.md)
- [人工门禁审查](review.md)
- [领域浏览候选](draft/knowledge/views/by-domain/acceptance-map.md)
- [零背景旅程候选](draft/knowledge/views/by-journey/acceptance-understanding.md)
