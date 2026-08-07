# 路由器集成后的可信问答盲测 v1

## 真实工况

用户询问此前未进入弱模型答案 Trial 的人员历史/权限和交付状态问题。Harness 应先运行确定性入口路由器，再只读主规范页形成答案；只有主页面留下明确子问题时才打开一个候补。

固定输入：

- Harness：`experiment/development-harness-v1@2fe1e47`；
- 正式知识：`omni-brain-harness-quality-check-v1@900cf85`；
- 模型：Codex Luna，中等推理，只读独立会话；
- 模型不读取设计仓 Eval、参考、原料或其他 Trial，不写文件。

## 场景

- [Q9 人员历史与权限](prompts/q9-personnel-history-and-permissions.md)；
- [Q10 交付多状态](prompts/q10-delivery-status-axes.md)。

内容共 10 项，最低 9 分且关键题全过。过程要求实际调用路由器、零宽泛搜索、零失败命令；Q9 最多读取主入口和一个有明确未答项的候补，Q10 预期只读主入口。
