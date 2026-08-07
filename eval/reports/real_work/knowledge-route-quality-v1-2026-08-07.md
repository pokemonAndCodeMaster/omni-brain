# 质检知识入口路由 v1：确定性评测

## 当前结论

Harness `0da62f3` 的只读知识入口路由器在 10 个固定质检问法上取得 **10/10**。所有主入口均属于预先冻结的语义等价集合；跨主题上线判断的前三个结果同时覆盖交付主线和验收现实边界。返回路径均为正式知识根内的绝对现存路径。

这个结果只验证“问题先去哪里读”。后续[人员权限与交付状态盲测](../../trials/real_work/TRUSTED_KNOWLEDGE_ANSWER_ROUTER_CODEX_LUNA_HARNESS_001/audit.md)已经证明弱模型会真实调用路由器，并在两条新问题上用主入口和一个候补取得 `10/10`；因此路由与问答组合可在该质检切片记为 verified。它仍不证明另一知识领域、宿主、语言或大规模知识同样有效。

## 固定身份

- 用例：[质检知识入口路由用例](../../fixtures/real_work/knowledge_route_quality_v1/README.md)；
- Harness：`/home/yyh/project/omni-brain-harness@0da62f3`；
- 路由器：`.agents/skills/answer-from-knowledge/scripts/knowledge_route.py`；
- 正式知识：`/home/yyh/project/omni-brain-harness-quality-check-v1@900cf851865bcea9a959d795cf2c127f2c8094e1`；
- Harness 回归：103 项通过；Skill 与知识检查通过。

## 路由结果

| ID | 主入口 | 结果 |
|---|---|---|
| R01 新人位置与学习路线 | `views/by-domain/quality.md` | 通过 |
| R02 多能力生产上线判断 | `acceptance/conclusion-and-execution.md`；候补含验收总览和交付主线 | 通过 |
| R03 快照版本冲突 | `acceptance/data-flow-and-state.md` | 通过 |
| R04 Ratio 到正式分配开发 | `acceptance/sampling-and-assignment.md` | 通过 |
| R05 五类业务对象 | `acceptance/lifecycle.md` | 通过 |
| R06 通过率分母 | `acceptance/open-questions.md` | 通过 |
| R07 Ratio 精确算例 | `acceptance/sampling-and-assignment.md` | 通过 |
| R08 空库运行判断 | `acceptance/python-architecture-and-implementation.md`；候补含实现地图和当前原型 | 通过 |
| R09 数据库公共能力 | `capabilities/database-access.md` | 通过 |
| R10 OBS 当前能力 | `capabilities/object-storage.md` | 通过 |

## 设计边界

- 只遍历 `knowledge/index.md` 及受治理导航页可达的 Markdown；未链接副本不参与排序；
- 用链接标签、上下文、frontmatter、标题与正文词项做确定性排序，结果可重建；
- 学习意图允许产品视图成为主入口；普通事实题优先规范页；非追溯问题降低来源页权重；
- 多部分问题按子句补充不同候选，避免三个结果都重复回答同一部分；
- 只返回 `PRIMARY` 和候补，不把排名或分数写成事实置信度；
- 不读取 `knowledge/raw/`，不写索引，不保存查询状态，不替 Agent 形成答案；
- 当前中文路由基于 2—4 字词项与英文词项，不承诺跨语言、超大知识库或复杂关系问题已经解决。

## 下一验证

已完成：`0da62f3` 集成到干净质检知识候选，人员 SCD2 与交付多状态两次只读盲测均通过。下一步不继续调整同领域排序，而是在新的开发复合工况中验证路由结果能否成为真实代码工作的最低充分上下文。
