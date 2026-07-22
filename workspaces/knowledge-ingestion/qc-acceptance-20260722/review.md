# 知识摄入审查

## 本轮结果

- **用户目标**：整理两个指定来源中与人工质检验收有关的材料，形成可浏览、理解、追溯和继续使用的候选知识。
- **来源范围与基线**：见 [source-a](draft/knowledge/sources/ai-knowledge-base-qc.md) 与 [source-b](draft/knowledge/sources/omni-brain-m1-quality-check.md)；source-a Git `3cf3934` 且工作区 dirty，source-b 无 Git 基线。
- **新增/更新规范页**：人工质检领域、验收子域总览、数据粒度与快照、抽样与预览、通过打回与回查、前后端实现边界；系统事实页记录验收 vertical slice。
- **同步产品视图**：[领域位置](draft/knowledge/views/by-domain/acceptance-map.md)、[旅程/学习路线](draft/knowledge/views/by-journey/acceptance-understanding.md)。
- **仍然未知**：Q1–Q6，尤其是正式阈值、schema、execute/回查落地和交付口径。

## 领域地图差异

```diff
+ manual-quality: 人工质检
+ manual-quality.acceptance: 人工质检验收
```

正式 `config/knowledge-domains.yaml` 尚未修改。

## 可以发布

| 项目 | 规范落点 | 依据 | 产品视图影响 |
|---|---|---|---|
| 验收在交付闭环中的位置、REJECT 返回返修、四类状态不混用 | `domains/manual-quality/acceptance/overview.md` | source-b 交付/前端设计，source-a 交付 wiki | 领域和旅程均覆盖 |
| 当前 vertical slice 的查询、date breakdown、Ratio preview 和测试边界 | `systems/acceptance-vertical-slice.md`、`implementation-boundaries.md` | source-a 代码、migration、测试、脚本 | 领域和旅程均可回查 |
| scene/task/date 粒度的候选解释及 schema 差异 | `data-granularity-and-snapshot.md` | source-b scene/snapshot/契约，source-a 纵切 | 领域路线覆盖 |
| preview 的选择解析、容量补足、过期和 owner/source_version | `sampling-and-preview.md` | source-a sampler/service/schema/test | 领域和旅程均覆盖 |

## 需要选择

| 项目 | 选项与影响 | 推荐 | 用户决定 |
|---|---|---|---|
| Q1 正式通过/打回规则 | 采用旧版阈值；采用 M1 目标状态机/新规则；并存为迁移期 | 先并存并标注版本，待当前规则配置确认 | 待定 |
| Q2 scene_name/project 推断 | 采用 source-b 新修复口径；沿用旧版；按真实字段重定 | 按当前生产字段和代码确认 | 待定 |
| Q3 快照/schema | 将 vertical slice 视为正式演进；与目标快照分开；补迁移映射 | 分开记录，确认正式库/schema 后再合并 | 待定 |
| Q4 execute/回查 | 暂不发布当前能力；提供实现/运行证据后发布；仅发布设计契约 | 暂不发布当前能力，保留设计契约 | 待定 |

## 需要补充

| 问题 | 缺什么 | 谁/哪个系统能回答 | 不补充的影响 |
|---|---|---|---|
| Q5 完成口径 | 留存率、Good 交付量、责任人与权限 | 业务负责人/当前配置 | 交付闭环只能作为候选定义 |
| Q6 “完成情况”证据 | 对应 commit、测试报告或人工确认 | 工程负责人/原始审查记录 | source-b 的完成标记不能升级为当前事实 |

## 建议忽略

| 材料/内容 | 理由 | 后续何时重新考虑 |
|---|---|---|
| 未命中验收主题的 raw 学习资料、vendor、通用文章 | 超出用户指定主题，不提供验收证据 | 另开知识摄入案 |
| Obsidian `[[...]]` 关系语法 | 本项目正式知识要求可移植 Markdown 相对链接 | 只作为来源文本定位，不进入正式页 |
| 重复的工作台/卡片组件设计 | 本轮没有足够证据抽取公共能力 | 第二个业务域独立消费并明确维护责任时再审查 |

## 只读检查

```text
knowledge-check: PASS
root: workspaces/knowledge-ingestion/qc-acceptance-20260722/draft/knowledge
files: 19; concepts: 11
链接、锚点、领域镜像和产品视图可达性通过；检查不判断业务真伪或内容充分性。
```

## 人工门禁

- [ ] 批准“可以发布”项
- [ ] 已逐项决定“需要选择”项
- [ ] 已接受或分配“需要补充”项
- [x] 正式知识在批准前没有变化
