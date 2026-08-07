# 可信知识问答停止回归 v1

## 目的

验证 `answer-from-knowledge@fc7651d` 能否在一个直接规范页足以回答时停止，并保留精确算法与现实边界。固定知识为 `omni-brain-harness-quality-check-v1@900cf85`；模型不读取 Eval、参考、原料或其他项目，不创建文件。

## 场景

- [Q7 Ratio 算例](prompts/q7-ratio-example.md)：精确计算、warning、shortage 与能力边界；
- [Q8 空库可运行性](prompts/q8-empty-database-runtime.md)：代码存在、迁移缺口与最小直接证据。

每题预期只需根入口和一篇规范页。内容共 10 项，最低 9 分且关键题全过；过程要求零失败命令、零全库枚举、每题只读一篇规范页、绝对可点击引用、候选仓零写入。
