# 从任何本地项目接着个人工作台做事

在这台电脑的新 Codex 会话里，可以直接说“继续个人工作台的视图设计”或“看看 YYH-11 的下一步”。用户级入口会提醒 Codex 使用 `personal-workbench`，读取 Linear 当前事项和必要正文后继续。无需记住仓库内的脚本命令，也不需要复制登录凭据。

这套入口由三部分组成：官方 Linear MCP 负责连接账号；用户级 `AGENTS.md` 提醒 Codex 何时进入工作台；仓库里唯一的一份 Skill 负责找到事项、按任务推进并留下可接手的上下文。Skill 是工作方法，不是另一个自动执行全部待办的后台 Agent。

## 日常怎么说

| 想做什么 | 可以直接说 |
| --- | --- |
| 随手记录 | “记录一个想法：我想每周知道哪些事情真正有进展，先保留现有例子和不清楚的问题。” |
| 接着做 | “继续个人工作台的视图设计，先看当前目标和进展，再推进下一步。” |
| 只看进度 | “YYH-11 现在做到了哪里，接下来做什么？这次只查看。” |
| 读已有资料 | “看看工作台里金铲铲的资料，说明现在哪些内容可用、哪些还不确定。” |
| 审阅结果 | “审阅这项工作，对照我原来要的效果，说明成果在哪里、哪些已经验证。” |

Codex 不应因为换了会话新建同名事项，也不应把“看看”解释成实施。执行中仍以本次请求、已有授权和目标代码仓的规则为准。

## 安装或换到新的仓库位置

在正式 Omni-Brain 仓运行：

```bash
python scripts/install_personal_workbench.py --repo /home/yyh/project/omni-brain
python scripts/install_personal_workbench.py --repo /home/yyh/project/omni-brain --check
```

安装器只做两件事：

- 将 `~/.agents/skills/personal-workbench` 链接到指定仓的 `.agents/skills/personal-workbench`，以后更新源文件即可，不复制第二份 Skill。
- 在 `~/.codex/AGENTS.md` 合并一段有边界标记的入口，保留前后全部已有内容。每次实际修改前保存原文及旧链接信息，返回备份目录；重复运行不新增内容。

若已有 Skill 链接需要从临时验证仓切回主仓，核对目标后加 `--replace-link`。已有独立目录不会被覆盖。存在非空 `AGENTS.override.md` 时安装器停止，因为它会使新入口不生效；先把入口合并到实际生效的指引，不能把安装文件存在当作 Codex 已采用。

安装器不修改 MCP 配置、不登录账号、不接触 token。使用自定义 `CODEX_HOME` 时沿用该目录，也可显式传入 `--codex-home`。在隔离用户目录验证时同时指定 `--user-home` 和 `--codex-home`，避免误用真实用户配置。

回退时先读返回备份目录中的 `before.json`：确认原来的 `AGENTS.md` 是否存在、旧 Skill 链接指向哪里。若此后没有其他修改，可恢复该目录里的原文；有新修改时只撤回 `personal-workbench:begin` 到 `personal-workbench:end` 之间的入口，保留后来内容。恢复旧链接；原先没有链接则只删除本安装器创建的符号链接，不能递归删除 Skill 源目录。

## 哪些位置可以接上

本机新 Codex 会话会读取用户级入口；在另一个项目打开时，也能发现用户级 Skill。事项涉及别的代码仓时，Codex 会先定位真正的仓库，再遵守那个仓库的规则。工作台工具的所在位置不决定代码应改在哪里。

已经打开很久的会话不保证重新读取 `AGENTS.md`。可以说“使用 $personal-workbench 继续这件事，重新读取当前 Skill 和线上正文”；若该会话没有加载 Linear 工具，需要重开连接可用的会话。不会因为文件更新就声称所有旧会话已获得新能力。

另一台机器或云端环境还需要单独安装入口并连接 Linear。ChatGPT 使用它自己的连接和指令入口；本安装器不配置 ChatGPT，也不能证明它可访问本地代码。不同位置共同接续的依据是[线上首页](https://linear.app/yyhpokemonmaster/document/abed03cc1da2)、事项当前正文和明确的材料链接。

无 MCP 时可以依据用户提供的全文或带时间的快照讨论，并完成不依赖线上状态的本地工作；必须说明没有读取实时状态，不能宣称已同步或已改状态。恢复连接后重新读取并合并，不能直接把旧草稿覆盖线上。

## 如何验证与继续改进

安装器检查：

```bash
python -m unittest discover -s tests -p test_personal_workbench_install.py -v
```

这组检查验证原文保留、重复安装、显式切换、拒绝覆盖已有内容和失败时恢复。它不证明 Agent 能接续工作；行为验证需要在另一个独立代码仓的新 Codex 会话里，不提供事项编号，只说“看看个人工作台的视图设计”。检查它是否找到原事项、读取当前全文、给出有依据的下一步，以及有没有误改线上状态。再用普通代码问答检查它没有滥用工作台。

2026-09-12 已用 Codex CLI 0.154.0 完成上述真实验证：新会话自动读取用户级 Skill，搜索并找到 YYH-12，取得事项及视图文档全文，正确说明目录和界面配置仍待完成；全过程只有读取。另一个新会话直接回答普通 Python 加法函数，没有读取 Skill 或调用 Linear。安装器的六项检查同时通过。本次证明了新会话的只读接续与触发边界，尚未验证所有任务类型的自动执行、既有长会话热更新或其他机器的连接。

Skill 变更与实际行为证据一起由 Git 和相关事项跟踪。详细工作流程只维护在[事项全生命周期](issue-lifecycle.md)，发布与快照操作见 [README](README.md)。不把每次使用反馈都堆进全局 `AGENTS.md`。

官方依据（2026-09-12 核对）：[技能发现与符号链接](https://learn.chatgpt.com/docs/build-skills)、[AGENTS.md 的读取顺序与新会话边界](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。

补充非交互检查：2026-09-13 的新 Codex 已读取前一会话的新结果并准备精确补丁，但以 read-only 启动的 codex exec 在保存时遇到工具审批要求，非交互会话策略为 never，实际写回被拒绝；回读确认线上未变化。默认交互配置仍为 on-request。此失败不属于 OAuth 失效，也不能被记为新会话写回成功；YYH-11 保留该待验证边界。未为绕过拒绝而调整工具审批策略。
