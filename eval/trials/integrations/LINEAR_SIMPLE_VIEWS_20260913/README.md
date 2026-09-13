# Linear 原生入口精简 · 2026-09-13

用户要求：领域、阶段、优先级/计划三维切换；少入口、平铺、同行可见其他维度；本轮统一执行，不逐项等待。

已实施三个顶层收藏：领域总览、工作阶段、优先级与计划；四个旧快捷视图保留。五个旧 View 身份均保留，原现在推进改名并扩大为全部未完成阶段；仅新增领域与计划两个 View。添加四象限标签组、启用周一开始的一周 Cycle（上海时区），关闭自动纳入开始/完成事项及活跃项强制属于周期。首次生成 9 月 14–20 日、21–27 日两个周期。

验证：

- [API 回读](verified.json)：七个筛选和实际成员与独立判断一致；三个主入口各十二条，待确认零条、想法一条、以后安排一条、近期成果五条；三个顶层收藏及順序一致。
- 十二项 stdlib 测试通过，包括旧名迁移保留身份、原收藏精简、无关收藏不变、丢失写响应、偏好保留、查重、分页与凭据边界。
- 独立只读审查补充模拟旧五 View+五收藏+无关收藏的迁移，身份与无关对象保留通过；发现说明未更新，已将 description 纳入计划比较并再次真实 apply 核对。
- 十二条未完成事项回读：零条有 Cycle、零条有截止日、零条已有四象限判断；本轮仅建立可使用的分类和排期位置，没有替用户编造安排。
- 线上日常视图文档、共享首页、YYH-12 已原位更新并 get 回读；Git guide 经 plan/save/get/receipt 发布到原文档。

未通过：所有 View 的 fieldProject、fieldLabels 保存 true，但有效设置 false；其余本次请求字段回读一致。官方说明 computed 值合并用户、组织与系统默认，不能将差异解释为无关范围。分组、嵌套属性是字符串，回读不证明 UI 解释；无已登录浏览器控制，未核验真实列显示、折叠、状态交互及默认首页。YYH-12 保持进行中。

回滚依据：[设置前](setup-before.json)、[设置后](setup-after.json)，完整每次 View 写前快照在被忽略的 .derived/linear/simple-views/。先重读线上并保留后续改动，恢复旧 View 名称、过滤与偏好；被移出的快捷收藏可以重新添加。不要盲目禁用已有人使用的周期：Linear 会结束当前周期并删除未来周期。没有自动回滚命令。

官方资料：[显示选项](https://linear.app/docs/display-options)、[标签](https://linear.app/docs/labels)、[周期及滚动规则](https://linear.app/docs/use-cycles)、[公开 Schema](https://github.com/linear/linear/blob/master/packages/sdk/src/schema.graphql)。
