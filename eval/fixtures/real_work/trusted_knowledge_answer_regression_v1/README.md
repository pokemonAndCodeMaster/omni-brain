# 可信知识问答相邻回归 v1

## 目的

本回归不用首轮答案包的原题，验证首轮后通用修订是否改变弱模型行为：

1. 有限集合是否完整保真，而不是用“等”缩略；
2. 单点冲突是否在最低充分页面内停下；
3. 普通知识问答是否跳过无关 Harness 状态文档、全库清单和惯例源码探测；
4. 本地知识引用是否使用可移植的绝对路径。

固定 Harness 为 `experiment/development-harness-v1@621ddd3`；正式知识仍为 `omni-brain-harness-quality-check-v1@900cf85`。模型不读取本设计仓的 Eval、参考或其他 Trial，不创建文件。

## 场景

- [Q5 五类业务对象](prompts/q5-five-business-objects.md)：预期只需根入口与生命周期规范页；
- [Q6 通过率口径](prompts/q6-pass-rate-decision.md)：预期只需根入口及数据流/未知两篇规范页。

内容共 10 项，最低通过线 9，所有关键题必须通过。过程必须零写入、零宽泛搜索；Q5 最多一篇规范页，Q6 最多两篇规范页。
