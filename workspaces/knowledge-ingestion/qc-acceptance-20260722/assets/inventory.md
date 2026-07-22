# 来源盘点

| 来源 ID | 位置与实际读取范围 | 现实形态 | 版本/时间 | 能证明 | 不能证明 | 重复/冲突 | 本轮处理 |
|---|---|---|---|---|---|---|---|
| source-a-repo | `ai-knowledge-base`：根索引、implementation/task/log、人工质检验收 wiki、quality_portal 相关卡片、`src/manual_qc/acceptance/`、API schema/router、Acceptance Repository、验收纵切测试/fixture、相关 migration 与验证脚本；未读无关 raw 学习材料 | 当前实现 + 历史/综合 wiki + 生成综合 | Git `3cf3934`；wiki/代码含 2026-06 至 2026-07 记录 | 可证明当前代码入口、HTTP 契约、Ratio 计划算法、preview TTL/owner/source_version、SQL/测试断言和实现范围 | 不能证明生产 Delta 已执行、当前业务阈值正确或所有 wiki 结论仍有效 | wiki 使用 NotebookLM/Obsidian 双链，且旧业务卡与新纵切存在路径/语义差异 | 作为当前实现优先证据；旧 wiki 仅作历史与背景，冲突时显式标记 |
| source-b-design | `omni-brain-m1-input-v1/quality_check` 全部 24 个 `.txt`：逐文件盘点标题、完成情况/TODO、关键规则、契约、交互和冲突；重点深读交付/行动项、验收中心、快照、采样、通过打回、Repository、Delta 回查、四级实现契约及模块实施计划 | 目标设计 + 人工决定 + 历史快照 + 生成综合混合 | 无 Git 基线；文档内部标注 2026-06 至 2026-07 | 可证明设计意图、旧版行为摘录、建议接口/字段/流程、已标记的完成项与 TODO | 不能独立证明代码部署、数据库真实状态、Delta 外部调用结果或设计决策已获批准 | 同一阈值/字段在旧版人工质检卡、M1 设计与当前 vertical slice 中不同 | 作为设计/历史/决策证据；不直接升级为当前实现 |

## 阅读计划

| 要回答的问题 | 最小直接来源 | 停止条件 | 实际结果 |
|---|---|---|---|
| 业务闭环和完成定义 | source-b 的交付任务、验收中心、总览/状态设计；source-a 的交付 wiki | 已能区分阶段、健康、行动项、验收结论 | 已回答；“通过且状态回查、Good 交付量对照、记录归档”是候选完成定义，留存率未定 |
| 当前可用查询和预览 | source-a 的 acceptance 源码、schema、测试、migration、验证脚本 | 路由、输入输出、失败边界、测试证据齐全 | 已回答；只读查询和 preview 回读可由代码/测试证明 |
| 抽样与通过打回 | source-b 采样/通过打回/Delta/快照设计；source-a sampler 与旧 wiki | 记录新旧规则及是否实现 | 部分回答；Ratio 已实现，旧版阈值与新设计存在取舍 |
| 数据粒度和快照 | source-b scene_name、综合快照、Repository、四级契约；source-a migration/fixture | 记录管理单元、操作单元和 schema 差异 | 已回答到候选层；source-b 目标快照与 source-a vertical slice 表不可直接等同 |

## 未纳入材料

| 材料 | 原因 | 后续触发条件 |
|---|---|---|
| `ai-knowledge-base/raw/**` 中未命中质检验收的学习/文章材料 | 与本轮主题无直接证据关系 | 需要建立 Agent/知识管理背景域时另开摄入案 |
| `ai-knowledge-base/demo/vendor/**` 与通用前端依赖 | 不是验收业务事实 | 需要复现 Demo 或做前端实现审查时再读取 |
| 两来源之外的仓库、部署环境、Delta/DMP 实例 | 来源边界禁止自行扩展 | 用户指定具体运行环境或日志后再补证 |
