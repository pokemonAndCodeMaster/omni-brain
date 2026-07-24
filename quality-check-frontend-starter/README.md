# 质检一站式平台前端 Starter

这是一个可直接运行的 Vue 3 + TypeScript 示例工程，用于演示两项平台级共享能力：

1. **统一数据工作台**：筛选、排序、层级展开、父子选择、列显隐、列顺序、列宽、行内编辑、保存个人视图；
2. **可配置卡片看板**：从当前筛选结果生成统计图表，添加到看板，拖拽、缩放、复制、删除并记忆布局。

> 这是“第一纵切”：工程结构和扩展边界按正式项目设计，但数据暂时使用 Mock。高风险业务动作、服务端复杂筛选 AST、跨页全选 `SelectionSpec`、公共布局发布、权限和审计需要在后续接真实后端时补齐。

## 1. 最快启动

### Windows PowerShell

```powershell
cd quality-check-frontend-starter
node -v
npm -v
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

### Linux / macOS

```bash
cd quality-check-frontend-starter
node -v
npm -v
npm install
npm run dev
```

推荐 Node.js `22.18+` 或 Node.js `24.11+`。

## 2. 你可以立即操作什么

进入“人工质检 · 交付中心”后：

- 搜索任务、项目、Scene、负责人；
- 按项目和状态筛选；
- 点击表头排序；
- 展开任务到日期子行；
- 父行选择子行、半选；
- 在“列配置”里隐藏、显示、左右移动列；
- 拖动表头右侧调整列宽；
- 直接编辑负责人、状态、优先级和目标量；
- 保存当前筛选与表格布局为个人视图；
- 点击“一键统计分析”，选择维度、指标和图表类型；
- 将图表添加到个人看板。

进入“业务看板”后：

- 点击“编辑布局”；
- 拖动和缩放卡片；
- 复制个人卡片；
- 删除个人卡片；
- 新增备注卡片；
- 刷新浏览器，验证布局和卡片仍然存在。

## 3. 常用命令

```bash
npm run dev         # 开发服务器，端口 5173
npm run type-check  # TypeScript / Vue 类型检查
npm run build       # 类型检查 + 生产构建
npm run preview     # 本地预览 dist，端口 4173
npm run clean       # 删除 dist
```

## 4. 文档阅读顺序

如果你刚接触前端，请先读第 0 篇；它会用当前真实代码解释业务全链路、Vue、Vite、组件、数据流和部署分别位于哪里。

1. [`docs/00-零基础全景拆解.md`](docs/00-零基础全景拆解.md)
2. [`docs/01-整体架构与目录.md`](docs/01-整体架构与目录.md)
3. [`docs/02-逐文件导读.md`](docs/02-逐文件导读.md)
4. [`docs/03-本地开发与调试.md`](docs/03-本地开发与调试.md)
5. [`docs/04-后端联调与API.md`](docs/04-后端联调与API.md)
6. [`docs/05-构建与部署.md`](docs/05-构建与部署.md)
7. [`docs/06-下一阶段开发清单.md`](docs/06-下一阶段开发清单.md)

## 5. Mock 与真实 API 切换

开发环境默认：

```env
VITE_USE_MOCK=true
VITE_API_BASE_URL=/api/v1
```

接 FastAPI 时修改 `.env.development`：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=/api/v1
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

然后重启 `npm run dev`。

前端调用链：

```text
页面
  → features/manual-qc/api/deliveries.ts
  → shared/api/http.ts
  → Vite 开发代理 /api
  → FastAPI
```

## 6. Docker 启动

```bash
docker compose up --build
```

打开：

```text
http://localhost:8080
```

当前 Docker Compose 使用 Mock 数据，因此不依赖后端。

## 7. 当前验证结果

本工程已经执行：

```bash
npm install
npm run build
```

类型检查和生产构建均通过。构建产物在 `dist/`。
