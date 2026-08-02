---
type: Shared Capability
title: 质检统一数据工作台
description: 跨人工质检页面复用的表格、卡片、选择、预览和反馈契约候选。
tags: [quality, shared, workbench]
---

# 质检统一数据工作台

## 共享边界

只有至少两个模块复用、或平台级交互必须一致的能力才上提为公共工作台；人工质检特有的采样、通过规则和交付语义留在业务模块。候选组件包括 AppShell、FilterBar、DataTable、DetailDrawer、StatusBadge、AsyncActionPanel、ConfirmDialog、CardShell 和 DashboardLayout。

## 共同交互契约

```text
筛选/选择 → 预览（冻结范围与时间）→ 确认 → 执行 → 刷新 → 显示成功、跳过、失败、未知
```

表格支持虚拟滚动、固定表头/浮动横向滚动、键盘操作、可访问文本和可追溯时间戳。选择应以叶子任务为最终粒度，父级勾选只是选择规格；预览必须冻结范围，执行前重新校验，审计记录保存操作者、版本和结果。

目标技术材料提出 Vue Table/Virtual、GridStack、ECharts，首片暂不引入 ExcelJS；但这仍是目标方案，不是仓库依赖或部署事实。

## 安全边界

卡片只回答一个问题，布局可按权限、版本和用户保存；危险动作不能藏在布局配置中。加载、空态、部分失败、重复提交和重试都必须有明确反馈。数据工作台统一视觉和交互，不拥有各模块的业务规则。

# Citations

- [来源记录](../sources/index.md)

## 来源

直接材料：`batch-2:quality_check/质检一站式平台顶层架构.txt`、`batch-2:quality_check/质检平台可配置卡片布局组件设计.txt`、`batch-2:quality_check/质检平台开源数据工作台实现设计.txt`、`batch-2:quality_check/质检平台统一数据工作台组件设计.txt`、`batch-2:quality_check/质检平台-人工质检验收中心前端设计.txt`。
