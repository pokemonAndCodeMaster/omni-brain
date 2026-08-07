# 正式知识可信问答包 v1：专家参考

## 参考身份

- 固定知识：`/home/yyh/project/omni-brain-harness-quality-check-v1@900cf851865bcea9a959d795cf2c127f2c8094e1`；
- 固定问题：[用例说明](../../../fixtures/real_work/trusted_knowledge_answer_pack_v1/README.md)；
- 参考答案：[Q1](answers/q1-learning.md)、[Q2](answers/q2-current-and-unknown.md)、[Q3](answers/q3-conflict-decision.md)、[Q4](answers/q4-development-context.md)；
- 参考答案只使用知识根、产品视图和每题最多三篇规范页，没有读取原始材料、摄入工作区、源码或运行系统。

## 自审结果

| 场景 | 分数 | 结论 |
|---|---:|---|
| Q1 学习全貌 | 6/6 | 领域位置、业务主线、五类对象和三篇路线完整 |
| Q2 现状与未知 | 6/6 | 五项逐项判断，目标、原型和生产未知分离 |
| Q3 冲突决策 | 5/5 | 不裁决版本冲突，不允许直接改生产库，补证责任明确 |
| Q4 开发上下文 | 7/7 | 用户结果、规则、现有入口、真实验证和关键未知最低充分 |
| **合计** | **24/24** | 所有关键题通过 |

参考答案不是唯一措辞；只要候选在相同证据边界内给出语义等价、可直接消费的答案，即可得分。后续直接源码、Schema 或生产运行证据可以纠正参考中的知识版本边界。
