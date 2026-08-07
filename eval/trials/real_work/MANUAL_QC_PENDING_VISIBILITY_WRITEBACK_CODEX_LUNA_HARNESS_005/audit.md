# 验收未完成量知识回写第五次盲测审计

## 结论

Luna 的候选达到 **24/24**，全部关键问题通过，首次跨过本用例的冻结接受线。结果说明：在同一质检系统的相邻代码增量范围内，当前 Harness 已能让较弱模型把固定代码变化原位回写到既有规范知识、公共能力和产品视图，并停在人工审查前；不再需要继续针对同一道题增加提示。

这不是“任意代码都能自动更新知识”的证明。证据仍限于一个已有较完整父知识、固定 Git 来源和验证报告的同系统增量；跨系统、缺少报告、真实冲突、删除/退役和第二领域仍需新用例反证。

## 实验输入与过程

- Prompt：[`prompt.md`](../../../fixtures/real_work/manual_qc_pending_visibility_writeback_v1/prompt.md)
- 父知识：`28b0951be7c49f00439365113d3d0b1c90dbdf44`
- Harness：`6deafb9d357bcd81189ecfed974f4f782e9b4173`
- 模型：Codex CLI `0.144.1`，`gpt-5.6-luna`，medium reasoning
- 冻结结果：`omni-brain-pending-writeback-luna-v5@a8ea723ed3f72c472dfb013fb84d59970a5247ad`

模型从项目根自然语言请求进入 `ingest-knowledge` 的 writeback 路线，建立 5 个读者问题，读取固定 diff、当前源码、聚焦测试和验证报告，并原位修改 10 个长期 owner。它没有读取专家参考答案或历史 Trial，也没有发布正式知识。

本轮新增的两个 Harness 约束都产生了可观察收益：

1. 来源身份冻结了实际 root、branch、HEAD 和 parent，来源页不再出现“新 commit + 旧 branch”的矛盾；
2. 兼容问题必须登记恢复机制源码。模型因此读取 `DataWorkbench.applyState`，把旧 `columnOrder`、当前 utility 列、保存业务顺序和新增业务列可见性写入软件页与公共能力页。

首次全局审查还发现 `sampling-and-assignment.md` 被修改但没有知识单元负责。模型补回既有长期 owner、重做影响复核后再次审查通过。这是工作台帮助模型维护知识归属的有效案例，而不是只检查文件格式。

## 内容评分

| 结果 | 项目 |
|---|---|
| 通过（24） | C01—C14、I01—I06、S01—S04 |
| 失败 | 无 |
| 关键失败 | 无 |

主要内容证据：

- 来源页准确写入 `/home/yyh/project/qpl-pending-ref`、`reference/manual-qc-pending-visibility-v1`、`26db0e1` 和父实现 `35948ae`，并与早期 Ratio 原型分开；
- `acceptance.pending = max(sum(actual_alloc) - sum(actual_complete), 0)` 与分类原子分配缺口的输入、聚合顺序和后续行动均被原位内化；
- 文档明确父版本已有 Catalog/Repository 指标，本次只贯通请求、类型、映射和 Vue 表格消费，没有虚构专用 API、Service 或表；
- 11 个基础指标加 5 个问题选项、16 项通过和第 17 项 422 已统一到来源、系统、软件和实现地图；
- PostgreSQL、API、Python、Vue、构建和 Edge 的验证范围与 `1737 → 144 → 51 → 20` 四级代表值被保留，同时没有外推生产部署或执行闭环；
- 公共数据工作台说明了真实消费者、旧配置恢复机制和不拥有业务公式的边界；根入口、学习旅程和日志同步更新；
- 候选留在隔离工作台的 `publish_ready`，正式 `knowledge/` 和 `config/` 未修改。

## 过程表现

本轮用时约 545 秒，执行 65 条命令，8 条失败；输入 token 539 万，较第四轮增加约 27%。内容已经收敛，但交互成本仍偏高：模型曾把候选知识路径当成当前目录下的相对路径、超出 `next --limit` 的允许范围，并因导航单元和重复登记发生数次可恢复失败。

这些问题没有损害最终内容，但说明 writeback 还不是低成本能力。下一步不再为本题增加门禁，而是在新用例中优先观察：精确路径是否能减少无效读取、现有知识 owner 是否容易定位、没有完整验证报告时模型能否主动补充真实证据。

## 成熟度判断

代码变化回写能力可从“implemented / 需人工纠错”升级为：

`verified@manual-qc-same-system-adjacent-writeback-slice`

它允许在已验证范围内作为推荐试用入口，但仍必须人工审查和批准。下一项验证应换题，不再重跑验收未完成量：优先选择同一工程但不同变化类型，随后再选择第二工程或领域。
