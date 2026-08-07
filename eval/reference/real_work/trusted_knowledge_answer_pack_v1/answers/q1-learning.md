# 人工质检验收：最短学习答案

**位置：** 在目标设计中，质检平台包含**人工质检、大模型质检、自动化质检、专题数据质量**四个并列子域。验收位于人工质检内部，上接标注结果，下接质量结论、通过/打回执行、返工和交付判断。当前只有人工质检验收具备较深知识，不能由此推断另外三个子域已经建设完成。

**业务主线：**

```text
标注结果可用
→ 选择验收范围
→ 计算抽样配额并选择具体样本
→ 分配给验收员并完成判断
→ 汇总完成度与质量依据
→ 形成 PASS / REJECT / PENDING 结论
→ 对结论覆盖的标注全集执行通过或打回
→ 回查外部真实状态
→ 汇总可交付数量，或返工后再次验收
```

**关键边界：** 验收样本只是被检查的一部分；验收记录是逐样本判断；质量结论决定能否进入执行；执行对象是明确范围内的**标注全集**；接口即时返回也不等于外部最终状态。PASS 后仍要执行、回查和判断交付量，REJECT 后还要返工、重提和再验，因此验收绝不是一个“通过/打回”按钮。

**继续阅读：**

1. [质检领域位置与人工质检验收](../../../../../../omni-brain-harness-quality-check-v1/knowledge/views/by-domain/quality.md)
2. [人工质检验收生命周期与阶段边界](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/lifecycle.md)
3. [验收结论与通过/打回执行](../../../../../../omni-brain-harness-quality-check-v1/knowledge/domains/quality/manual/acceptance/conclusion-and-execution.md)

当前学习问题已有充分知识，无需先补材料；若要问现网具体规则或页面，则需另行核验生产事实。
