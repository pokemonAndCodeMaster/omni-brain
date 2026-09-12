# 本地工作台：阅读与接续

这个页面把已经读到的 Linear 事项、全部挂载位置的文档，以及登记过的仓库材料放在一起。打开后，左边找内容，右边直接读全文；需要继续时，回到 Linear，或复制接续口令给 Codex、ChatGPT。

它是同一批事实的阅读副本。修改事项、同步文档、执行任务仍由已连接 Linear 的工具完成。

## 打开与使用

在仓库中运行：

```bash
python scripts/render_personal_workbench.py --local-index config/personal-workbench-assets.json
```

用浏览器打开生成的 `.derived/personal-workbench/index.html`。它是单个 HTML 文件，没有启动服务的要求，也不依赖网络字体、外部脚本或在线资源。若还没有本地材料目录，省略 `--local-index` 可先浏览 Linear 快照。

- **现在推进**：Todo 与正在进行的事项；每项显示当前正文，不以条目数量估算完成比例。
- **想法与未安排**：Backlog 和待分拣的事项。是否要实施、先讨论什么，以正文为准。
- **待看成果**：Linear 中标为 In Review 的事项。这里沿用线上状态，不擅自认定成果已经可审阅。
- **知识与文档**：团队、项目、事项等位置的全文文档，加上登记过的本地知识、说明和代码入口。
- **全部**：包括已完成、取消和重复的事项，便于追溯。

搜索会查标题和完整正文，并切到全部内容。可继续按领域、材料类型筛选。按 `/` 聚焦搜索框；Tab 在按钮、目录和正文链接之间移动。手机宽度下，点条目进入全文，用“返回目录”回到列表。

“记一个想法”打开 Linear 的新事项窗口，保存仍由你在 Linear 中完成。“交给 AI 接着做”生成可以修改的口令；复制失败时会选中全文供手动复制。口令本身不授予 Linear 权限。Codex 或 ChatGPT 需要已有连接和相应读取权限。

## 更新内容

对 Codex 说：“刷新个人工作台的 Linear 全文快照和本地阅读页。”它先重新读取线上资料，保存完整快照，再运行生成命令。页面上的“正文更新”来自线上材料；“本地快照保存”来自对应 JSON 文件保存时间。两者分开显示，避免把一次重新生成误认为资料已经更新。

生成器本身只读取 `.derived/linear/issues/*.json`、`documents/*.json` 和显式提供的本地目录，不访问 Linear API，也不会自动发现未读取的文档。准备快照时必须遍历所有可见文档挂载位置并处理分页，随后逐项取得全文；仅有列表摘要会报错。根代理的刷新流程负责完成这一步。页面中没有运行中的定时同步。

本地目录格式：

```json
{
  "items": [
    {
      "id": "knowledge-entry",
      "title": "质检知识阅读入口",
      "path": "knowledge/index.md",
      "kind": "knowledge",
      "domain": "Omni-Brain",
      "summary": "先从这里找到适用的正式知识。",
      "relatedIssues": [],
      "updatedAt": "",
      "inspectedAt": "2026-09-12T12:00:00Z",
      "status": "按正文说明使用",
      "authority": "规范来源的阅读入口"
    }
  ]
}
```

`path` 必须指向仓库内的明确入口；Markdown 文件读取全文，代码目录或其他文件仅显示 `summary` 和入口链接。不遍历源码，不摄入 `knowledge/raw/`，不读取仓库外文件。本地条目的 `updatedAt` 未提供时显示“未提供”；`inspectedAt` 只表示入口核对时间。只有线上链接的条目可省略 `path` 并提供 `url`；同一篇 Linear 文档按稳定地址去重。

## 验证范围

`tests/test_personal_workbench_view.py` 检查文档挂载不漏项、中文全文搜索、事项与文档互相阅读、复制失败回退、320px 宽度和危险内容。真实浏览器检查使用可选的 Playwright 与 Chromium；不可用时会明确跳过浏览器检查。

```bash
python -m unittest discover -s tests -p 'test_personal_workbench_view.py' -v
```

正文使用已有的 `markdown-it-py` 渲染，关闭原生 HTML，限制可打开的 URL。远程图片显示为阅读链接，不自动加载；页面内容不能发起网络请求。生成的 HTML 含所选材料的完整文本，仍是个人资料，分享它等于分享这些内容。
