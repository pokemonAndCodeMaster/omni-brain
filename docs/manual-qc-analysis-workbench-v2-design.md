# 人工质检分析工作台 V2 技术设计

> 状态：**已确认；切片一、二已实现，并通过数据库、HTTP、组件、生产构建和真实 Edge 用户路径验证**
>
> 适用范围：人工质检快照页的任务明细、业务总览和统计图表
>
> 本文定义下一阶段的技术方案。已确认的内容按“实施切片”逐步落地，不能跳过前序
> 用户路径直接扩建后续能力。

**审阅范围：**

- 业务与交互取舍集中在第 1、3、6、7、8、16 节；
- 数据口径和后端实现集中在第 4、5 节；
- 后续实施模型需要完整阅读第 9—14 节。

## 1. 设计结论

### 1.1 要解决的真实问题

当前页面已经跑通 PostgreSQL → FastAPI → Vue，也具备可拖动卡片、ECharts 图表和
TanStack Table 表格，但用户仍然很难按真实工作顺序完成下面这些动作：

1. 先按标注任务判断产出、Good/Bad 构成和验收进度；
2. 再展开某个任务，查看日期、组、标注员和问题标签；
3. 按完成率、通过率或某个 Bad 问题占比筛选、倒排任务；
4. 把当前发现直接变成一张可编辑、可保存的总览卡片或统计图；
5. 后续增加指标或维度时，不再分别修改表格、总览和图表里的三套硬编码。

问题的根源不是页面缺几个按钮，而是当前系统没有统一说明：

- 有哪些业务维度和指标；
- 每个指标怎样计算；
- 可以在哪个粒度分组、筛选、排序和下钻；
- 表格、总览卡片和图表怎样使用同一份定义。

### 1.2 推荐方案

增加一层**人工质检分析语义层**。这里的“语义层”不是新数据库，也不是让用户写 SQL，
而是一份由后端维护的业务指标目录和受控查询能力：

```text
人工质检日快照
      ↓
人工质检分析语义层
├─ 维度与指标目录：名称、口径、单位、可用操作
├─ 受控查询：时间范围、筛选、分组、统计、排序、分页
└─ 结果说明：数据粒度、更新时间、空值与警告
      ↓
三种独立呈现
├─ 任务优先的明细表
├─ 可组合的总览卡片
└─ 可叠加多个图层的统计图表
```

三种呈现共享指标目录和查询方式，但**不合并成一个万能组件**：

- 表格负责比较、筛选、排序和逐级查看；
- 总览卡片负责突出少量关键数字和分项；
- 统计图表负责趋势、构成和多指标关系。

这样既能复用底层能力，也不会把项目做成一个难维护的低代码页面搭建器。

### 1.3 当前实现基线

后续模型应从下面这些真实入口改造，不能在旁边另建一套平行页面：

| 当前入口 | 已有能力 | V2 需要改变的地方 |
|---|---|---|
| [`snapshot_service.py`](../src/manual_qc/snapshot/snapshot_service.py) 与 [`repository.py`](../src/manual_qc/snapshot/repository.py) | 日期参与固定四级聚合 | 增加跨日期任务聚合和受控指标筛选；旧接口迁移期保留 |
| [`snapshotChart.ts`](../src/frontend/src/features/manual-qc/utils/snapshotChart.ts) | 浏览器聚合固定维度和指标 | 主要聚合移到后端，前端只组装查询和呈现结果 |
| [`SnapshotDataTable.vue`](../src/frontend/src/features/manual-qc/components/SnapshotDataTable.vue) | TanStack 表格、部分列筛选和懒加载 | 根节点改为任务，列从目录生成，增加指标详情 |
| [`snapshotOverview.ts`](../src/frontend/src/features/manual-qc/utils/snapshotOverview.ts) | 四种固定总览口径 | 转换为内容块和通用拆分定义 |
| [`dashboard/types.ts`](../src/frontend/src/shared/dashboard/types.ts) | V1 总览和图表配置 | 迁移为独立的 V2 总览、图表、表格配置 |
| [`SnapshotSummaryChart.vue`](../src/frontend/src/features/manual-qc/components/SnapshotSummaryChart.vue) | 固定细分统计 | 达到功能一致后转为可编辑系统预设 |
| [`t_portal_view_config`](../migrations/004_create_portal_view_config.sql) | 保存 JSONB 视图定义 | 继续复用，增加 V2 配置类型与严格校验 |

当前快照字段和业务粒度仍以
[`snapshot-contract.md`](snapshot-contract.md) 为准。本设计只改变分析和呈现方式，不修改
`V20260709_01` 的 18 个顶层字段。

## 2. 技术选项与取舍

### 2.1 指标统计放在哪里

| 方案 | 优点 | 主要问题 | 结论 |
|---|---|---|---|
| 继续把快照行拉到浏览器统计 | 改动最少 | 单请求最多 1000 行，V1 临时分页也只允许 10000 行；跨周期任务筛选不完整；动态问题标签容易漏算；多个卡片重复取数 | 不采用 |
| 接入通用 BI 或允许用户写公式、SQL | 自由度高 | 业务口径难治理；存在错误查询和安全风险；当前项目规模不需要完整 BI 引擎 | 不采用 |
| 后端维护指标目录并编译受控查询 | 口径唯一；表格、卡片和图表共用；可正确处理聚合筛选 | 需要新增一层领域代码 | **采用** |

### 2.2 前端组件是否全部统一

| 方案 | 优点 | 主要问题 | 结论 |
|---|---|---|---|
| 表格、总览、图表统一成万能 `AnalysisCard` | 类型数量少 | 组件职责混乱；编辑器复杂；容易变成页面搭建器 | 不采用 |
| 三套功能完全独立 | 初期简单 | 指标、筛选、保存逻辑继续重复 | 不采用 |
| 共享查询与指标目录，保留三种呈现模型 | 复用核心能力；交互边界清晰 | 需要设计稳定的公共数据结构 | **采用** |

### 2.3 现有技术是否保留

| 技术 | 决定 | 原因 |
|---|---|---|
| PostgreSQL JSONB 快照 | 保留 | 当前真实数据链已跑通，问题标签天然适合 JSONB |
| FastAPI + Pydantic | 保留 | 适合校验受控查询和持久化配置 |
| TanStack Table | 保留 | 已覆盖排序、筛选、列管理、展开和受控状态，不必重新发明表格内核 |
| ECharts | 保留 | 可以实现多图层、多坐标轴、趋势和构成图 |
| GridStack | 保留 | 当前拖动和缩放已可用 |
| `t_portal_view_config` | 保留 | 继续只保存视图定义和布局，不保存会过期的统计值 |

本轮不引入新的前端状态管理框架，也不引入通用 SQL 查询构建器。

## 3. 业务使用路径

页面继续使用一个顶部数据范围，但内容顺序和交互调整为：

```text
选择日期、项目、任务、组或人员范围
      ↓
业务总览：先看项目和总体规模
      ↓ 点击某个数字
对应统计图：查看任务差异、趋势和问题构成
      ↓ 点击异常任务
任务明细表：默认按任务比较
      ↓ 点击 Good 占比或通过率
任务详情：日期、组、人员、Good/Bad、问题标签和趋势
      ↓
把当前指标固定为列 / 添加筛选 / 生成统计图
```

用户不需要理解后端的查询结构。页面必须把“当前统计范围”“当前分组粒度”和
“指标计算口径”显示为可读文字。

## 4. 统一维度与指标目录

### 4.1 目录的职责

目录是指标和维度的唯一业务定义来源，后端为权威来源。前端启动时读取目录，用它决定：

- 字段显示名称和帮助说明；
- 数量、百分比、日期或文本的格式；
- 可否分组、筛选、排序和下钻；
- 应显示哪一种筛选控件；
- 图表中默认适合柱形还是折线、使用数量轴还是比例轴；
- 指标公式和分母为零时的显示规则。

目录不保存页面数据，也不允许前端传入任意公式或 SQL。

### 4.2 维度

| 实现标识 | 页面名称 | 来源 | 支持能力 |
|---|---|---|---|
| `date` | 日期 | `stat_date` | 分组、范围筛选、排序、按日趋势 |
| `project` | 项目 | `project_name` | 分组、多选筛选、排序、下钻 |
| `task` | 标注任务 | `scene_name` | 分组、多选筛选、排序、下钻 |
| `group` | 组 | `group_name` | 分组、多选/文本筛选、排序、下钻 |
| `employee` | 标注员 | `employee_id` | 分组、多选/文本筛选、排序 |
| `result_type` | 标注结果 | Good / Bad 两个指标对象 | 分组、筛选 |
| `question_label` | 问题标签 | `option_metrics` 第一层键 | 分组、筛选 |
| `question_option` | 问题选项 | `option_metrics` 第二层键 | 分组、筛选、排序 |

任务根节点在数据库查询中同时按 `project_name + scene_name` 分组，避免未来不同项目出现
同名任务时错误合并；页面仍以“标注任务”为主要名称，项目作为任务属性显示。

### 4.3 首批公开指标

所有百分比都按**先求和、再相除**计算，禁止对员工行百分比直接取平均。

| 实现标识 | 页面名称 | 计算口径 |
|---|---|---|
| `annotation.total` | 标注总量 | `SUM(annotation_total)` |
| `annotation.submitted` | 标注提交量 | `SUM(annotation_submitted)` |
| `annotation.good_submitted` | Good 提交量 | `SUM(good_metrics.annotation_submitted)` |
| `annotation.bad_submitted` | Bad 提交量 | `SUM(bad_metrics.annotation_submitted)` |
| `annotation.good_rate` | Good 占比 | Good 提交量 ÷ 标注提交量 |
| `annotation.bad_rate` | Bad 占比 | Bad 提交量 ÷ 标注提交量 |
| `acceptance.expected_allocated` | 预期验收分配量 | Good/Bad 的 `expect_alloc` 之和 |
| `acceptance.allocated` | 实际验收分配量 | Good/Bad 的 `actual_alloc` 之和 |
| `acceptance.allocation_coverage_rate` | 分配覆盖率 | 实际验收分配量 ÷ 标注提交量 |
| `acceptance.allocation_fulfillment_rate` | 分配达成率 | 实际验收分配量 ÷ 预期验收分配量 |
| `acceptance.completed` | 验收完成量 | Good/Bad 的 `actual_complete` 之和 |
| `acceptance.pending` | 验收未完成量 | `MAX(实际分配量 - 完成量, 0)` |
| `acceptance.completion_rate` | 验收完成率 | 验收完成量 ÷ 实际验收分配量 |
| `acceptance.passed` | 验收通过量 | Good/Bad 的 `actual_pass` 之和 |
| `acceptance.rejected` | 验收打回量 | Good/Bad 的 `actual_reject` 之和 |
| `acceptance.pass_rate` | 验收通过率 | 验收通过量 ÷ 验收完成量 |
| `acceptance.reject_rate` | 验收打回率 | 验收打回量 ÷ 验收完成量 |

切片一已经公开的**问题选项指标**只有下面两项：

- `option.annotation_submitted`
- `option.annotation_rate_of_bad`

它们都必须指定问题标签和问题选项。下列指标是后续切片沿用相同参数化方式扩展的
**目录候选**，目前不能在页面或接口目录中宣称为可用能力：

- `good.acceptance.*`
- `bad.acceptance.*`
- `option.acceptance.allocated`
- `option.acceptance.completed`
- `option.acceptance.completion_rate`
- `option.acceptance.passed`
- `option.acceptance.rejected`
- `option.acceptance.pass_rate`

指定问题选项时，指标引用携带参数，而不是为每个选项生成新的硬编码字段：

```json
{
  "id": "option.annotation_rate_of_bad",
  "parameters": {
    "questionLabel": "驾驶行为分类",
    "questionOption": "CUT_IN"
  }
}
```

`option.annotation_rate_of_bad` 的分母是同一统计范围内的 Bad 提交量。问题选项可能是
多选，因此各选项占比之和**不保证等于 100%**，页面帮助信息必须明确这一点。

### 4.4 暂不公开的快照字段

快照中的 `correct`、`incorrect`、`expect_pass`、`expect_reject` 已经存在，但目前
它们和“实际通过/打回”的业务使用边界还没有再次确认。第一批目录可以登记这些字段为
隐藏状态，不能默认出现在编辑器和表格中。确认口径后再改为可见，不由代码猜测含义。

### 4.5 百分比和阈值规则

- 分母为零时返回 `null`，页面显示 `—`，不能显示成 0%；
- 百分比不强制截断到 0—100%，例如重复分配可能让覆盖率超过 100%；
- 第一版不内置“低于 80% 显红”等业务阈值；
- 只有用户配置阈值，或业务方确认统一阈值后，页面才显示风险颜色；
- 指标说明中显示分子、分母和当前分组粒度，避免同名百分比被误解。

### 4.6 后端目录结构

建议新增：

```text
src/manual_qc/analysis/
  __init__.py
  models.py              查询、维度、指标和结果领域模型
  catalog.py             页面名称、口径、单位和允许操作
  repository.py          白名单 SQL 片段、JSONB 展开和聚合查询
  analysis_service.py    校验查询、选择统计路径并组织结果

src/api/
  schemas/analysis.py
  routers/analysis.py
```

仍然遵守 `Router → Service → Repository → PGConnector → PostgreSQL`。SQL 只出现在
`repository.py`，`catalog.py` 不包含可由外部输入拼接的 SQL。

## 5. 统一查询设计

### 5.1 查询描述

表格、总览和图表都提交同一种受控查询。实现类名建议为 `AnalysisQuery`：

```json
{
  "sourceId": "manual_qc.snapshot.v20260709",
  "scope": {
    "dateStart": "2026-07-20",
    "dateEnd": "2026-07-26",
    "projectNames": [],
    "taskNames": [],
    "groupNames": [],
    "employeeIds": []
  },
  "groupBy": ["project", "task"],
  "measures": [
    { "id": "annotation.submitted" },
    { "id": "annotation.good_rate" },
    { "id": "acceptance.completion_rate" }
  ],
  "filters": [
    {
      "target": { "id": "acceptance.completion_rate" },
      "operator": "less_than",
      "value": 80
    }
  ],
  "sort": [
    {
      "target": { "id": "acceptance.completion_rate" },
      "direction": "ascending"
    }
  ],
  "page": { "number": 1, "size": 50 }
}
```

允许的操作由目录决定：

- 文本维度：等于、包含、属于多个值；
- 日期：等于、早于、晚于、区间；
- 数量和比例：等于、大于、小于、区间；
- 排序：维度自然顺序或指标升降序。

服务端拒绝未知标识、未知参数、不兼容的操作、过多分组或超出上限的分页。

### 5.2 查询响应

返回平坦、可用于多种视图的统计结果：

```json
{
  "sourceId": "manual_qc.snapshot.v20260709",
  "groupBy": ["project", "task"],
  "rows": [
    {
      "key": "城区/高速::城区交互任务-A",
      "dimensions": {
        "project": "城区/高速",
        "task": "城区交互任务-A"
      },
      "measures": {
        "annotation.submitted": 447,
        "annotation.good_rate": 75.4,
        "acceptance.completion_rate": 93.2
      }
    }
  ],
  "total": 4,
  "page": { "number": 1, "size": 50 },
  "computedAt": "2026-07-26T10:00:00+08:00",
  "warnings": []
}
```

指标值保持数字或 `null`，单位和格式来自目录，不在后端返回“93.2%”这类不可排序字符串。

### 5.3 服务端执行顺序

```text
校验数据源、维度、指标和操作
      ↓
把原始维度条件放入 WHERE
      ↓
按请求粒度 GROUP BY
      ↓
计算数量和比率
      ↓
把聚合指标条件放入 HAVING
      ↓
排序和分页
      ↓
返回结果、口径与更新时间
```

这使“通过率低于 80%”“CUT_IN 占比高于 20%”在完整数据集上执行，而不是只筛浏览器
已经加载的部分行。

### 5.4 JSONB 问题标签的安全处理

`option_metrics` 的读取按使用方式分开处理：

```text
快照行
  └─ 问题标签
      └─ 问题选项
          └─ 指标对象
```

必须防止一个问题标签有多个选项时把顶层标注量重复相加。**切片一**查询某个已经指定的
问题选项时，直接从 JSONB 路径读取该选项的指标对象，并与顶层、Good、Bad 指标在同一
基础快照聚合中计算；不会产生一行拆成多行的重复计数。候选值接口才使用 JSONB 横向展开，
它只返回标签或选项名称，不参与数量汇总。

后续若支持按“问题标签 / 问题选项”作为结果行分组，再采用独立的选项聚合结果与基础指标
按维度键合并；禁止先展开选项、再直接汇总顶层数量。

### 5.5 接口

新增接口：

| 接口 | 用途 |
|---|---|
| `GET /api/manual-qc/analysis/catalog` | 读取可用维度、指标、格式和操作 |
| `POST /api/manual-qc/analysis/query` | 执行受控聚合、筛选、排序和分页 |
| `POST /api/manual-qc/analysis/facets` | 为项目、任务、组、人员、问题标签等筛选器读取候选值 |

现有 `/api/snapshots/*` 在迁移期间保留，V2 页面完成并验证后再决定是否退役，不在第一步
直接删除。

## 6. 任务优先明细表

### 6.1 默认层级

```text
标注任务（选定周期汇总）
└─ 日期
   └─ 组
      └─ 标注员
```

- 根节点实际按“项目 + 标注任务”查询；
- 日期子节点继承当前任务和全页范围；
- 组继承任务与日期；
- 标注员继承任务、日期与组；
- 子节点继续懒加载，但筛选和排序由服务端在各自粒度上完成。

### 6.2 默认表头和列

| 表头分组 | 默认显示列 | 默认隐藏的详情 |
|---|---|---|
| 任务信息 | 标注任务、项目、统计周期 | 组、人员只在下钻层显示 |
| 标注情况 | 标注提交量、Good 占比 | Good 数、Bad 数、问题标签和选项 |
| 验收进度 | 实际分配量、分配覆盖率、完成量、完成率 | 预期分配、分配达成率、Good/Bad 分配与完成 |
| 验收结果 | 通过率 | 通过数、打回数、Good/Bad 和问题选项通过情况 |

数量和比例列全部从指标目录生成筛选与排序能力。展开按钮、层级标识和操作列没有业务
筛选意义，不显示筛选器。

### 6.3 点击指标后的详情

点击 Good 占比，打开任务详情侧栏：

1. Good/Bad 数量和比例；
2. 问题标签 → 问题选项分布；
3. 选定周期内的按日趋势；
4. 操作：添加为列、按此筛选、生成统计图。

点击完成率或通过率，侧栏显示：

1. 分配、完成、未完成或通过、打回；
2. Good/Bad 对比；
3. 问题标签和问题选项对应的验收情况；
4. 日期、组和人员下钻入口。

对具体问题选项执行“添加为列”后，表格配置增加带参数的指标引用。该列立即具备
比例范围筛选、升降序和趋势入口。

### 6.4 表格配置

建议定义独立的 `TableViewSpec`，而不是把表格伪装成卡片：

```json
{
  "rootGroupBy": ["project", "task"],
  "drillPath": ["date", "group", "employee"],
  "columns": [
    {
      "id": "task",
      "target": { "id": "task" },
      "visible": true,
      "width": 220
    },
    {
      "id": "good-rate",
      "target": { "id": "annotation.good_rate" },
      "visible": true,
      "width": 120
    }
  ],
  "defaultSort": [
    {
      "target": { "id": "annotation.submitted" },
      "direction": "descending"
    }
  ]
}
```

列顺序、宽度、显隐和固定的问题选项列可以保存。临时筛选默认不保存，除非用户明确
选择“保存为默认筛选”。

### 6.5 顶部范围与表格筛选

两者使用同一种查询结构，但作用不同：

- 顶部范围定义总览、图表和表格共同使用的基础数据；
- 表头筛选只改变当前表格比较结果；
- 日期、项目、任务、组、人员等维度条件可由用户明确提升为全页范围；
- 完成率、通过率等条件依赖当前分组粒度，不能悄悄提升为其他图表的条件。

例如“任务通过率低于 80%”是任务粒度条件；如果直接应用到按日趋势，它会变成
“每天通过率低于 80%”，含义已经改变。因此页面应提供：

- “仅筛当前表格”；
- “应用可兼容条件到全页”；
- “按当前筛选生成图表”。

这里的“统一”是统一指标和查询语言，不是让所有局部筛选自动影响全页。

## 7. 可组合的总览卡片

### 7.1 组件边界

总览卡片继续作为独立类型 `MetricCardSpec`。一张卡片由有序内容块组成：

```text
总览卡片
├─ 标题和说明
├─ 指标块：一个数据指标
├─ 文字块：补充说明
├─ 拆分块：按项目、任务或组重复一组指标
└─ 点击动作：跳转到图表或明细
```

不支持任意深度的“卡片套卡片”。项目拆分使用一个受控的重复区域表示，第一版最多
一层拆分。这已经覆盖“全量 → 分项目”的使用方式，也避免配置结构无限递归。

### 7.2 配置结构

```json
{
  "id": "overview-annotation",
  "kind": "metric",
  "origin": {
    "type": "system-preset",
    "presetId": "manual-qc.annotation-overview",
    "presetVersion": 2
  },
  "title": "标注产出与质量构成",
  "description": "选定周期内的标注结果",
  "query": {
    "scopeMode": "inherit-page",
    "filters": []
  },
  "blocks": [
    {
      "id": "submitted",
      "kind": "metric-value",
      "metric": { "id": "annotation.submitted" },
      "label": "标注提交",
      "emphasis": "primary",
      "width": "full",
      "style": {
        "valueSize": 38,
        "valueColor": "#16233a",
        "labelSize": 12,
        "labelColor": "#667085"
      }
    },
    {
      "id": "good-rate",
      "kind": "metric-value",
      "metric": { "id": "annotation.good_rate" },
      "label": "Good 占比",
      "emphasis": "supporting",
      "width": "half",
      "style": {}
    },
    {
      "id": "by-project",
      "kind": "breakdown",
      "dimension": "project",
      "metrics": [
        { "id": "annotation.submitted" },
        { "id": "annotation.good_submitted" },
        { "id": "annotation.bad_submitted" },
        { "id": "annotation.good_rate" }
      ],
      "limit": 8
    }
  ],
  "action": {
    "type": "jump",
    "targetCardId": "chart-annotation-quality"
  },
  "layout": {}
}
```

规则：

- “主数字”由 `emphasis: "primary"` 明确指定；
- 一张卡最多有一个主指标块；
- 每个文字和数值块都有自己的样式，不再只提供整卡 `valueSize`；
- 内容块可以调整顺序和宽度，第一版宽度采用全宽、二分之一、三分之一三档；
- 拆分块可选项目、任务或组，不是总览卡片私有的“项目开关”；
- 数值必须来自指标，不允许手工输入一个看似真实但不会随数据更新的数字；
- 说明文字可以编辑，但不能覆盖指标帮助说明。

### 7.3 预设、编辑、复制和恢复

系统默认总览也是普通 `MetricCardSpec`，区别只在 `origin`：

- 直接编辑系统预设时，保存为用户覆盖版本；
- “恢复默认”重新载入当前预设版本；
- “复制”创建 `origin.type = "user"` 的独立卡片；
- 系统预设升级不自动覆盖用户已经编辑的版本；
- 保存配置，不保存计算后的数字。

## 8. 可叠加图层的统计图表

### 8.1 核心模型

第一版一张图表卡片使用一个横向分类维度，可以添加多个图层。所有图层共享同一个横轴，
但每个图层可以选择自己的指标、图形、坐标轴、分组和附加筛选。

```text
统计图表卡片
├─ 横轴：日期
├─ 图层 1：验收分配量，柱形，左侧数量轴
├─ 图层 2：验收完成量，柱形，左侧数量轴
├─ 图层 3：完成率，折线，右侧比例轴
└─ 图例、标签、排序和数据预览
```

不再存在特殊的 `combo` 图表类型。所谓“数量—比率组合图”只是柱形图层和折线图层
使用不同坐标轴的结果。

### 8.2 配置结构

```json
{
  "id": "chart-acceptance-progress",
  "kind": "chart",
  "origin": {
    "type": "system-preset",
    "presetId": "manual-qc.acceptance-progress",
    "presetVersion": 2
  },
  "title": "验收分配与完成趋势",
  "description": "按日查看分配、完成和完成率",
  "baseQuery": {
    "scopeMode": "inherit-page",
    "categoryDimension": "date",
    "timeGrain": "day",
    "filters": []
  },
  "axes": [
    {
      "id": "count-axis",
      "side": "left",
      "unit": "count",
      "minimum": 0
    },
    {
      "id": "rate-axis",
      "side": "right",
      "unit": "percent",
      "minimum": 0,
      "maximum": 100
    }
  ],
  "layers": [
    {
      "id": "allocated",
      "metric": { "id": "acceptance.allocated" },
      "renderAs": "bar",
      "axisId": "count-axis",
      "splitBy": null,
      "filters": [],
      "stackGroup": null,
      "style": { "color": "#4f73d9", "showLabels": false }
    },
    {
      "id": "completed",
      "metric": { "id": "acceptance.completed" },
      "renderAs": "bar",
      "axisId": "count-axis",
      "splitBy": null,
      "filters": [],
      "stackGroup": null,
      "style": { "color": "#2e9a72", "showLabels": false }
    },
    {
      "id": "completion-rate",
      "metric": { "id": "acceptance.completion_rate" },
      "renderAs": "line",
      "axisId": "rate-axis",
      "splitBy": null,
      "filters": [],
      "style": {
        "color": "#d47a2f",
        "smooth": true,
        "showLabels": false
      }
    }
  ],
  "presentation": {
    "showLegend": true,
    "legendPosition": "top",
    "categorySort": "natural",
    "categoryLimit": 31
  },
  "layout": {}
}
```

### 8.3 图层规则

- 轴图第一版支持柱形、折线和面积三种图层；
- 每个图层只能引用一个指标，添加第二个指标就是添加第二个图层；
- 一个图层可以用 `splitBy` 按项目、任务、组或问题选项拆成多条序列；
- 所有图层必须共享横轴维度，避免不同含义的坐标被强行叠加；
- 图层附加筛选只影响该图层；
- 同一张卡最多 8 个图层，防止无法阅读和请求失控；
- 饼图/环形图属于单指标构成图，第一版单独作为一个图表卡片，不和轴图层混用；
- 比例轴默认 0—100，但用户可以修改；覆盖率可能超过 100 时系统给出提示，不截断数据。

如果用户要把“按任务”和“按日期”放在同一张卡中，应复制卡片或新建卡片，而不是给
一张图配置两个互不相干的横轴。第一版不实现多面板嵌套。

### 8.4 编辑器

图表编辑器按下面顺序组织，编辑时持续显示实时预览：

1. 卡片名称和说明；
2. 页面范围继承方式和公共筛选；
3. 横轴维度与日期粒度；
4. 图层列表；
5. 当前图层的数据指标、分组、筛选、图形和坐标轴；
6. 图例、排序、分类数量等整体显示；
7. 聚合数据表与最终图表预览。

预览数据表直接展示后端返回的分类和指标值，帮助用户判断图形问题还是统计口径问题。

### 8.5 固定统计图迁移

当前 `SnapshotSummaryChart.vue` 中的固定统计不再作为不可编辑的特殊区域。达到功能
一致后，把它们转换为系统预设图表卡片：

- 标注量 + Good/Bad 占比；
- Bad 问题选项排行；
- 验收分配量 + 完成量 + 完成率；
- 通过量 + 打回量 + 通过率。

系统预设拥有和用户卡片相同的编辑、复制、拖动、缩放、保存和恢复能力。

当前卡片底部“查看图表数据”被固定来源栏挤压的问题，应通过明确的三段布局修复：

```text
卡片标题和操作
可滚动的图表与数据内容
固定但不遮挡内容的数据来源
```

来源栏不能覆盖内容区；卡片高度不足时，中间内容区滚动。

## 9. 页面配置与持久化

### 9.1 V2 配置

建议把总览、统计图和表格视图保存在同一份页面配置中，但保留三种独立结构：

```json
{
  "schemaVersion": "manual-qc-analysis-view-v2",
  "presetVersion": 2,
  "overviewCards": [],
  "chartCards": [],
  "table": {},
  "layout": {
    "sectionOrder": ["overview", "charts", "table"]
  }
}
```

统一保存的收益是：

- 页面只有一个“未保存更改”状态；
- 卡片跳转能稳定引用同一配置中的目标；
- 表格固定问题选项列和卡片可以一起恢复；
- 不再维护 `useMetricWorkspace` 与 `useDashboardWorkspace` 两套相似逻辑。

统一的是页面状态与持久化，不是把三种 Vue 组件合并。

### 9.2 数据库存储

继续使用 `t_portal_view_config.config` JSONB，不新增统计结果表。建议增加新的
`view_type = "analysis_workbench"` 和对应 API：

```text
GET /api/view-configs/analysis-workbench/{page_key}
PUT /api/view-configs/analysis-workbench/{page_key}
```

保存接口必须使用 Pydantic 对 V2 配置完整校验，不能接受任意 `dict`。至少限制：

- 卡片总数；
- 每卡内容块和图层数量；
- 标题、说明和文本长度；
- 布局范围；
- 颜色与字号范围；
- 引用的指标、维度和筛选操作；
- 配置总大小。

本地单用户阶段不增加权限和多人协作版本管理。

### 9.3 V1 迁移

迁移期间同时读取：

- `manual-qc-snapshot-overview` 的总览卡片；
- `manual-qc-snapshots` 的图表卡片。

转换规则：

1. 固定 `metricId` 转成多个 `metric-value` 和一个 `breakdown` 内容块；
2. 原 `dimensionId` 转成 `categoryDimension`；
3. 原 `measureIds` 逐个转成图层；
4. 原 `combo` 中数量指标转柱形、比例指标转折线；
5. 原卡片布局保持；
6. 转换失败的卡片跳过并给出可读原因，不能让整个页面无法打开。

第一次只在内存中转换。用户确认页面正常并点击保存后，写入新的 V2 `page_key`。试验期
不覆盖和删除 V1 配置，保证可以回退。

## 10. Vue 组件与状态边界

### 10.1 目录建议

```text
src/frontend/src/
  features/manual-qc/analysis/
    api/
      analysis.ts
    types/
      analysis.ts
      viewConfig.ts
    composables/
      useAnalysisCatalog.ts
      useAnalysisQuery.ts
      useManualQcAnalysisWorkspace.ts
      useTaskDetail.ts
    components/
      ManualQcAnalysisFilters.vue
      TaskAnalysisTable.vue
      TaskMetricDetailDrawer.vue
      ManualQcMetricCardEditor.vue
      ManualQcChartEditor.vue
    presets/
      manualQcPresets.ts

  shared/analysis/
    components/
      MetricCard.vue
      MetricBlock.vue
      BreakdownBlock.vue
      ChartCard.vue
      ChartLayerList.vue
      ChartLayerEditor.vue
      AnalysisDataPreview.vue
    types/
      view.ts
```

### 10.2 单一职责

| 组件或 composable | 单一职责 |
|---|---|
| `SnapshotPage.vue` | 组装页面区块和连接跳转事件，不计算指标 |
| `useAnalysisCatalog` | 读取并缓存维度和指标目录 |
| `useAnalysisQuery` | 执行查询、取消旧请求、维护加载与错误 |
| `useManualQcAnalysisWorkspace` | 恢复、迁移、编辑、保存整页 V2 配置 |
| `TaskAnalysisTable` | 根据目录和 `TableViewSpec` 渲染任务表 |
| `TaskMetricDetailDrawer` | 查询并展示当前指标的构成、趋势和可执行操作 |
| `MetricCard` | 按内容块渲染一个总览卡片 |
| `ManualQcMetricCardEditor` | 编辑人工质检总览卡片定义 |
| `ChartCard` | 把已解析图层渲染成 ECharts |
| `ManualQcChartEditor` | 编辑横轴、图层、筛选、坐标轴和预览 |

状态使用 Composition API 和 `<script setup lang="ts">`：

- 后端结果、卡片配置和打开的侧栏是最小源状态；
- 图表选项、显示标签和表格列由 `computed` 派生；
- 保存、加载和预览请求使用显式动作；
- `watch` 只处理请求、保存提示等副作用，并取消已经过期的异步请求；
- props 向下、typed events 向上；
- 路由页面不直接拼 API，不保存重复的派生统计值。

### 10.3 共享组件边界

`shared/analysis` 只保存不含人工质检公式的呈现组件。人工质检指标选择、问题标签参数和
预设留在 `features/manual-qc/analysis`。

只有第二个业务领域使用后证明稳定的部分，才继续下沉到共享层，不能因为“以后可能复用”
提前设计全行业语义引擎。

## 11. 实施切片

每个切片都必须产生可直接打开使用的页面结果，后一个切片不以前一个“写完代码”为完成
依据，而以前一个真实用户路径已经跑通为前提。

### 切片一：任务级查询与指标目录

**状态：已实现并验证。**

**实现：**

- 后端维度、指标目录；
- `catalog`、`query`、`facets` 三个接口；
- 任务跨日期汇总；
- 数量、比例和动态问题选项的服务端筛选与排序；
- 前端最小目录读取和查询客户端。

**页面结果：**

先用一个简洁的任务结果表替换现有“日期—项目”根节点。其他卡片继续用旧实现。

**必须跑通：**

1. 选定两天后，每个任务只出现一条根记录；
2. 任务标注提交量等于两天、全部组和员工之和；
3. “通过率低于 X”返回完整数据上的任务；
4. “某问题选项占 Bad 比例高于 X”可以筛选和倒排；
5. 同时查询顶层数量和问题选项时，顶层数量不被重复放大。

**2026-07-26 当前规模化种子结果：** 3024 条员工日快照汇总为 24 个跨周期任务；
通过率低于 80% 的任务返回“复杂掉头任务-12”“拥堵跟车任务-08”；23 个有 Bad 提交
的任务可查询 `驾驶行为分类 / CUT_IN` 占 Bad 比例，顶层数量与动态问题指标同时查询时
不会被 JSONB 选项展开放大。详细命令与边界见
[`verification-report.md`](verification-report.md)。

### 切片二：任务优先明细和指标详情

**状态：已实现并验证。**

**实现：**

- 任务 → 日期 → 组 → 标注员懒加载；
- 分组表头和默认列；
- 所有可见业务列按目录生成筛选；
- Good 占比、完成率和通过率详情侧栏；
- 问题选项添加为列；
- 表格配置保存。

**页面结果：**

用户能从任务列表定位异常，并在同一页面看到问题发生在哪一天、哪个组、哪个员工或哪个
问题选项。

**必须跑通：**

1. 默认页面不平铺 Good/Bad 和全部验收细项；
2. 点击 Good 占比可以看到完整问题标签和选项分布；
3. 固定一个问题选项为列后可筛选、排序；
4. 没有业务阈值时不把 80% 等任意数值标红。

**2026-07-26 实际结果：** 默认只加载 24 条任务根记录；展开“城区交互任务-01”后
得到 14 个日期节点，再展开 `2026-07-13` 得到 3 个组，展开“质检组-01”得到 3 名
标注员。点击“拥堵跟车任务-08”的完成率后，详情侧栏同时展示整体、Good、Bad、
14 天趋势以及 2 个问题标签下的 8 个选项。把“驾驶行为分类 / YIELD”的完成率固定
为列后，该列可做数值范围筛选和排序；保存表格并刷新页面后可恢复，且筛选与展开状态
不会被误保存。页面未引入未经确认的风险阈值或红色告警。

### 切片三：总览卡片 V2

**状态：已实现并验证。**

**实现：**

- 指标块、文字块和一层拆分块；
- 主指标和逐块样式；
- 项目/任务/组拆分；
- 编辑、复制、跳转、保存和恢复默认；
- 现有总览 V1 迁移。

**页面结果：**

用户无需改代码即可把总览改成“全量标注 → 分项目的 Good/Bad 和 Good 占比”，并让
点击动作进入对应细分统计。

**必须跑通：**

1. 主数字由用户选择；
2. 每个指标块可独立改名称和样式；
3. 项目拆分来自通用拆分配置；
4. 重开页面后配置恢复，数字用最新快照重算；
5. 系统预设可恢复，复制品不受恢复操作影响。

**2026-07-26 实际结果：** 旧的 3 张固定总览在打开页面时迁移为
`dashboard-v2` 内容块定义；默认标注卡由 4 个指标块和 1 个项目拆分块组成。
真实 Edge 中复制标注卡后，新增说明块、把拆分维度改为组并保存，刷新页面仍恢复
说明内容和质检组数据；删除副本不影响系统预设。原卡标题临时修改后可以恢复当前
系统预设。最终 PostgreSQL 保留 3 张 V2 系统卡，数值仍由 3024 条当前快照重算。

### 切片四：多图层统计图 V2

**实现：**

- 横轴、日期粒度、图层、分组、筛选、坐标轴和样式编辑；
- 多柱形/折线/面积叠加；
- 聚合数据表和图表实时预览；
- 预设编辑、复制、保存和恢复；
- 当前 V1 图表迁移；
- 卡片内容和来源栏布局修复。

**页面结果：**

用户不再选择“组合图”特例，而是添加“分配量柱形 + 完成量柱形 + 完成率折线”三个图层。

**必须跑通：**

1. 数量和比例同时可读，不因量纲不同被压扁；
2. 图层可分别选择指标、图形、轴和筛选；
3. 按任务改为按日期只需修改横轴；
4. “查看图表数据”在任意允许的卡片尺寸下可见；
5. 固定统计图转成预设后仍覆盖原来的业务信息。

### 切片五：收束和回归

**实现：**

- 删除已被 V2 替代的重复计算和编辑器；
- 收束 `useMetricWorkspace`、`useDashboardWorkspace`；
- 更新 README、组件边界、快照页说明和验证报告；
- V1 配置保留一个明确回退周期后再决定是否删除。

**页面结果：**

项目中只保留一套当前使用的指标口径和页面配置，不让实验迁移代码长期变成第二套实现。

## 12. 验收数据与验证方式

### 12.1 固定实验数据

当前确定性种子已经覆盖：

- 14 个连续日期、2 个项目、24 个任务；
- 12 个组和 120 名轮换标注员，共 3024 条员工日快照；
- 两个问题标签，每个标签 4 个问题选项；
- 一个低完成率选项、一个低通过率选项；
- 一个员工日记录有提交但未分配；
- 一个任务分配覆盖率超过 100%，用于确认系统不错误截断；
- 一个任务全部相关分母为零，用于确认页面显示 `—`。

数据仍是本地可手工核算的实验数据，不能复制材料中的生产数据。

### 12.2 后端验证

重点不是为每个函数写测试，而是验证业务口径：

1. 指标目录和查询请求的 Pydantic 校验；
2. 两天任务汇总与手工 SQL 结果一致；
3. 百分比使用总分子 ÷ 总分母，不是行百分比平均值；
4. 数量筛选进入聚合后条件；
5. 动态问题选项筛选、倒排正确；
6. JSONB 展开不会放大顶层数量；
7. 分母为零返回 `null`；
8. 未知指标、非法操作和超限请求被明确拒绝；
9. V1 转 V2 配置的固定样例结果正确。

### 12.3 前端验证

使用 Vitest 覆盖稳定的纯逻辑：

- 目录定义到表格筛选器的映射；
- 默认表头分组和列顺序；
- 动态问题选项列；
- V1 配置迁移；
- 图层到 ECharts option 的转换；
- 系统预设覆盖、复制和恢复。

### 12.4 真实页面验证

每个切片都使用本地 PostgreSQL、FastAPI 和 Vue 实际运行，至少完成下面的用户路径：

```text
选择两天
→ 按任务查看标注和验收
→ 筛出通过率最低的任务
→ 打开 Good/Bad 和问题选项详情
→ 固定某问题选项为表格列
→ 按该选项占比倒排
→ 生成一张按日趋势图
→ 保存
→ 重开页面
→ 验证配置恢复且数据重新计算
```

验证报告必须记录：

- 实际输入；
- 执行路径；
- 页面可观察结果；
- 手工核算结果；
- 失败和未覆盖项。

“测试通过”不能代替上述真实页面路径。

## 13. 明确不做的内容

本设计阶段不包含：

- 任意 SQL 或任意公式编辑器；
- 无限层卡片嵌套；
- 通用低代码页面搭建器；
- 同一图表内使用多个互不相干的横轴；
- 自动判断分配是否合理、人员是否淘汰等业务结论；
- 未经确认的完成率、通过率风险阈值；
- 多用户权限、共享看板和冲突合并；
- 服务端缓存、物化视图和大规模性能优化；
- 采样、任务下发、验收结论执行等后续业务页面。

只有真实数据量证明普通 PostgreSQL 聚合不够时，才增加缓存、物化视图或专用分析存储。

## 14. 确认后交给实施模型的起点

切片一、二已完成。后续实施模型应只进入**切片三：总览卡片 V2**，不得同时重写
统计图编辑器。开始前先：

1. 复用当前指标目录和受控查询，不继续扩建任务表或新建平行统计口径；
2. 把现有固定总览迁移为指标块、文字块和一层拆分块；
3. 跑通“选择主指标、逐块编辑、按项目拆分、保存并刷新恢复”的真实页面路径；
4. 保留当前总览 V1 的明确回退方式，完成真实浏览器验证后再决定是否替换；
5. 汇报实际修改、设计取舍、运行结果和仍然缺失的能力。

切片三通过后，才能进入多图层统计图 V2；不能因为最终设计已经写明，就一次性实现全部 V2。

## 15. 原始需求覆盖检查

| 用户提出的需求 | 本设计的处理 |
|---|---|
| 明细默认按任务，而不是按项目 | 根节点按“项目 + 标注任务”跨周期汇总，页面以任务为主；见第 6.1 节 |
| 所有业务列都能筛选和排序 | 由指标目录声明筛选类型，服务端对完整数据筛选；见第 4、5、6.2 节 |
| 默认只看标注提交和 Good 占比，点击再看 Good/Bad、问题标签和趋势 | 使用任务详情侧栏和动态固定列；见第 6.3 节 |
| 将来筛选某个 Bad 类别占比、倒排或看趋势 | 参数化问题选项指标支持筛选、排序、固定为列和生成图；见第 4.3、5.4、6.3 节 |
| 验收列按分配、完成、结果逐步呈现 | 分组表头和默认列顺序；见第 6.2 节 |
| 总览统计内容不再只有四个硬编码选项 | 总览使用任意已登记指标的内容块；见第 7 节 |
| 主数字、文字、数字样式可单独配置 | 主指标显式指定，每个内容块独立样式；见第 7.2 节 |
| 项目拆分可配置，总览卡片可以复用 | 使用通用拆分块，支持项目、任务或组；见第 7.1、7.2 节 |
| 不希望为了套娃做出失控的页面搭建器 | 拆分最多一层，不支持无限嵌套；见第 7.1、13 节 |
| 固定细分图也能编辑、复制 | 固定图转换成系统预设；见第 8.5 节 |
| 不再靠特殊“双图表”类型 | 一张轴图由多个柱形、折线或面积图层组成；见第 8.1—8.3 节 |
| 横轴、分组、指标、坐标轴、样式和筛选可配置 | 图表查询、坐标轴和图层分别配置；见第 8.2—8.4 节 |
| “按任务/按天”应是通用分组能力 | 它们成为横轴维度和日期粒度，不再是写死按钮；见第 8.2、8.3 节 |
| “查看图表数据”被底栏遮挡 | 卡片改为标题、可滚动内容、来源三段布局；见第 8.5 节 |
| 顶部筛选和表格筛选关系要清楚 | 统一查询语言、区分全页范围和当前粒度，显式提升；见第 6.5 节 |
| 卡片保存后重开页面直接显示 | V2 保存定义与布局，重新读取最新数据计算；见第 9 节 |

## 16. 需要业务方确认的关键取舍

下面八项是实施前真正需要确认的决定，其他字段名和文件名可以在实现时局部调整：

1. **指标统计移到后端：** 浏览器不再读取最多 1000 条快照后自行完成主要聚合；
2. **任务作为明细入口：** 默认层级采用任务 → 日期 → 组 → 标注员，项目作为任务属性；
3. **总览卡片有限组合：** 支持多个指标块和一层项目/任务/组拆分，不支持无限套娃；
4. **图表采用多图层：** 同一张轴图共享一个横轴，不再保留 `combo` 特殊类型；
5. **筛选不悄悄跨粒度：** 顶部范围作用全页，表格聚合条件默认只作用当前表格；
6. **整页配置统一保存：** 总览、图表和表格定义进入一份 V2 配置，V1 在试验期保留回退；
7. **区分两种分配比例：** 分配覆盖率为实际分配 ÷ 标注提交，分配达成率为实际分配 ÷ 预期分配；
8. **问题选项占比口径：** 默认用选项提交量 ÷ Bad 提交量，允许多选导致各选项占比之和超过 100%。
