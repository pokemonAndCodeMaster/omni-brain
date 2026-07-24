# 04. 后端联调与 API

## 一、前后端契约原则

前端 TypeScript 类型应对齐 FastAPI 的 Pydantic/OpenAPI 响应，不直接使用数据库字段模型。

推荐链路：

```text
Pydantic Schema
  → FastAPI OpenAPI
  → 自动或人工生成 TypeScript 类型
  → features/*/api
  → 页面
```

## 二、Starter 当前期望的 API

### 查询交付任务

```http
GET /api/v1/manual-qc/deliveries
```

响应示例：

```json
[
  {
    "id": "delivery-001",
    "name": "城区路口交互 July-W3",
    "project": "城区",
    "scene": "路口交互",
    "owner": "张晨",
    "status": "验收中",
    "priority": "P0",
    "targetCount": 3200,
    "completedCount": 2520,
    "goodRate": 0.962,
    "updatedAt": "2026-07-18 18:20",
    "children": []
  }
]
```

### 修改普通字段

```http
PATCH /api/v1/manual-qc/deliveries/{id}
Content-Type: application/json
```

请求：

```json
{
  "owner": "李珊"
}
```

## 三、不要把高风险操作做成普通 PATCH

负责人、优先级、备注等普通字段可以 PATCH。

验收分配、通过、打回应使用：

```text
POST /assignment/preview
POST /assignment/execute
POST /execution/preview
POST /execution/execute
GET  /execution/status
```

前端状态：

```text
idle
→ previewing
→ preview_ready
→ executing
→ executed
→ refreshing
```

任何筛选、选择、规则变化都应使旧 preview 失效。

## 四、服务端筛选建议

数据量大后，不应把全表传到浏览器再筛选。推荐请求体：

```json
{
  "query": {
    "dataSourceId": "manual-qc-deliveries",
    "filters": {
      "type": "group",
      "logic": "and",
      "children": [
        {
          "type": "condition",
          "field": "project",
          "operator": "in",
          "value": ["城区", "高速"]
        }
      ]
    },
    "sorts": [
      { "field": "priority", "direction": "asc" }
    ],
    "groupBy": []
  },
  "page": {
    "cursor": null,
    "size": 50
  }
}
```

## 五、跨页全选

浏览器不要接收全部 ID。推荐：

```json
{
  "selection": {
    "mode": "filter",
    "filterSnapshot": { "...": "..." },
    "excludedIds": ["task-103"]
  }
}
```

或者：

```json
{
  "selection": {
    "mode": "explicit",
    "explicitIds": ["task-1", "task-2"]
  }
}
```

## 六、分析接口

正式分析构建器不应只在浏览器做聚合。建议：

```http
POST /api/v1/analytics/query
```

请求：

```json
{
  "dataSourceId": "manual-qc-deliveries",
  "query": { "...": "QuerySpec" },
  "dimensions": ["project"],
  "metrics": [
    {
      "key": "good_pass_rate",
      "aggregation": "ratio_of_sums"
    }
  ]
}
```

通过率等指标必须由后端指标注册表控制口径，不能让前端任意平均百分比。

## 七、保存视图与看板 API

当前使用 localStorage。接后端后建议：

```text
GET    /api/v1/view-configs
POST   /api/v1/view-configs
PUT    /api/v1/view-configs/{id}
DELETE /api/v1/view-configs/{id}
POST   /api/v1/view-configs/{id}/publish
```

配置类型：

```text
QUERY
TABLE_VIEW
CHART
CARD
DASHBOARD
```
