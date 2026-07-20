# M1 第 4 轮内容自检

> 性质：评测者对参考成果的内部自检，不是独立模型 Trial。检查入口为 `outcome/knowledge/index.md`，不读取原始材料补答案；用户已于 2026-07-20 完成内容与语义审查。

## 结果

十二个获批学习问题均有明确规范落点和产品视图入口；结构检查通过。用户已经确认稳定核心与 D1—D5，生产未知继续显式保留。

| # | 学习问题 | 最小充分页面 | 自检 | 必须保留的边界 |
|---|---|---|---|---|
| 1 | 人工质检在质检领域和数据交付中的位置 | `domains/quality/overview.md` | 通过 | 四类方式是项目材料分类，不扩写行业本体 |
| 2 | 人工质检从需求到交付的阶段、并行和返工 | `domains/quality/manual/end-to-end-lifecycle.md` | 通过 | 预测算法、留存率和当前责任仍未知 |
| 3 | 人工质检模块和验收上下游 | `domains/quality/manual/platform-and-module-map.md` | 通过 | 模块图是目标产品，不是当前完整实现 |
| 4 | 验收从抽样到返工怎样运转 | `acceptance/lifecycle.md`、`product-workbench.md` | 通过 | 抽样、结论、执行全集和最终状态分开 |
| 5 | 核心数据、标识、状态和口径 | `acceptance/data-flow-and-state.md` | 通过 | Schema 多版本仍未知；来源分母冲突按人工决定显式解决 |
| 6 | 前端、API、数据库、调度和外部平台协作 | `acceptance/system-architecture.md` | 通过 | 实线当前、虚线目标；DAG 和外部客户端未实现 |
| 7 | 业务动作怎样落实到 Python 结构和运行过程 | `acceptance/python-architecture-and-implementation.md` | 通过 | 以真实分配预览走读；设计评价基于代码，不按模式名词 |
| 8 | 数据库和 OBS 公共能力怎样维护 | `capabilities/database-access.md`、`object-storage.md` | 通过 | 数据库有当前代码；OBS 只有公共定位和缺口 |
| 9 | Ratio 算法和其他策略 | `acceptance/sampling-and-assignment.md` | 通过 | Ratio 当前可证明；Group/Personal 主要是历史和目标 |
| 10 | 结论怎样形成、何时不能执行、为何回查 | `acceptance/conclusion-and-execution.md` | 通过 | 历史阈值不冒充生产规则；PENDING 只作为获批目标设计 |
| 11 | 当前代码、目标设计和历史脚本分别是什么 | `acceptance/implementation-map.md`、`systems/manual-qc-acceptance-prototype.md` | 通过 | 当前迁移缺快照表，无法声称真实端到端跑通 |
| 12 | 哪些问题没证据、谁来补 | `acceptance/open-questions.md` | 通过 | 生产接口、Schema、阈值、部署和后续实现保持未知 |

## 产品视图检查

- 根入口提供零背景、业务推进、数据、软件、算法和事实核验六类入口。
- 领域视图展示 `质检 → 人工质检 → 人工质检验收` 以及三层不同深度。
- 学习旅程从领域和业务开始，不从 API 或 Ratio 公式开始。
- 数据库和 OBS 公共页已被产品视图直接链接。
- 所有关键页面均可从产品视图通过标准 Markdown 相对链接到达。

## 软件学习检查

- 有真实业务场景：分配预览。
- 有裁剪后的 4+1：业务用例、逻辑类图、代码树、运行追溯、当前物理边界。
- 有实际代码走读：Router → Service → Repository/Ratio → PostgreSQL。
- 有数据转换链：Pydantic → 选择键 → Repository 行 → dataclass → 响应 → JSONB。
- 有基于代码的设计判断和修改场景；没有把性能、幂等、重试、可测试性、可观察性前置成通用清单。

## 机械检查

```text
knowledge-check: PASS
files: 35
concepts: 26
errors: 0
warnings: 0
```

机械通过只证明结构、链接、OKF 基础字段和产品视图可达性；十二个答案是否符合业务理解仍由用户审查。
