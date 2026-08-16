from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class HarnessContractTest(unittest.TestCase):
    def test_opencode_uses_native_project_conventions(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        runtime = manifest["runtime"]
        self.assertEqual("release", manifest["release_channel"])
        self.assertEqual("omni-brain-harness", manifest["release_id"])
        self.assertEqual("release/harness", manifest["release_branch"])
        self.assertEqual("opencode", runtime["primary"])
        self.assertEqual("native_file_conventions", runtime["adapter"])
        self.assertFalse(runtime["opencode_specific_config_required"])
        self.assertTrue((ROOT / runtime["instructions"]).exists())
        self.assertTrue((ROOT / manifest["roadmap"]).exists())

    def test_integrated_release_keeps_ingestion_scoped_verification(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        self.assertEqual("M4", manifest["current_stage"]["id"])
        self.assertEqual(
            "integrated_release_with_scoped_verification_through_m4_and_local_review",
            manifest["current_stage"]["status"],
        )
        ingestion = manifest["capabilities"]["knowledge_ingestion"]
        self.assertEqual(
            "verified_at_cross_model_incremental_slice",
            ingestion["adoption"],
        )
        self.assertIn(".agents/skills/ingest-knowledge/SKILL.md", ingestion["entrypoints"])
        self.assertIn("scripts/ingestion_workspace.py", ingestion["entrypoints"])
        self.assertIn("cross_model", ingestion["adoption"])

    def test_startup_context_does_not_expose_eval_history(self) -> None:
        startup = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ("harness.yaml", "docs/now.md", "docs/roadmap.md")
        )
        for leaked_term in (
            "GLM",
            "Luna",
            "Kimi",
            "MiniMax",
            "Batch 1",
            "batch-1",
        ):
            self.assertNotIn(leaked_term, startup)
        self.assertIsNone(re.search(r"\bV\d+(?:\.\d+)?\b", startup))
        self.assertIsNone(re.search(r"\b\d+/\d+\b", startup))

    def test_root_contract_keeps_ingestion_source_reads_in_current_packet(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("先用工作台 `next` 取得当前材料单元、主题或聚焦小批", contract)
        self.assertIn("不得绕过它递归搜索", contract)
        self.assertIn("临时 Git worktree", contract)

    def test_existing_knowledge_queries_do_not_trigger_ingestion(self) -> None:
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("加载 `answer-from-knowledge`", contract)
        self.assertIn("不加载 `ingest-knowledge`", contract)

    def test_trusted_query_skill_is_stateless_and_bounded(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            "verified_at_quality_check_trusted_query_slices",
            manifest["capabilities"]["knowledge_query_and_context"]["adoption"],
        )
        skill = (ROOT / ".agents/skills/answer-from-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不创建工作区、账本、YAML", skill)
        self.assertIn("最多三篇", skill)
        self.assertIn("没有搜到", skill)
        self.assertIn("任务上下文额外给出一个紧凑交接", skill)
        self.assertIn("没有用户授权时不创建文件", skill)
        self.assertIn("不运行 `rg --files`", skill)
        self.assertIn("不能用“等、等等、诸如此类”", skill)
        self.assertIn("绝对文件路径", skill)
        self.assertIn("相对于包含该链接的文档解析", skill)
        self.assertIn("先只读取最直接的一篇", skill)
        self.assertIn("硬上限而不是建议目标", skill)
        self.assertIn("knowledge_route.py", skill)
        self.assertIn("先只读取 `PRIMARY`", skill)

    def test_skill_frontmatter_is_discoverable(self) -> None:
        for name in (
            "ingest-knowledge", "answer-from-knowledge", "form-solution",
            "develop-with-knowledge", "review-work",
        ):
            path = ROOT / f".agents/skills/{name}/SKILL.md"
            match = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
            self.assertIsNotNone(match, name)
            self.assertEqual(name, yaml.safe_load(match.group(1))["name"])

    def test_declared_entrypoints_exist(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        for capability in manifest["capabilities"].values():
            for entrypoint in capability["entrypoints"]:
                self.assertTrue((ROOT / entrypoint).exists(), entrypoint)

    def test_readme_exposes_the_concrete_component_map(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for capability in manifest["capabilities"].values():
            for entrypoint in capability["entrypoints"]:
                self.assertIn(entrypoint, readme, entrypoint)
        self.assertIn("workspaces/knowledge-ingestion/<case-id>/", readme)
        self.assertIn("`AGENTS.md` 负责选 Skill，Skill 指导模型", readme)
        self.assertIn("release/harness", readme)
        self.assertIn("唯一正式入口", readme)

    def test_retired_task_ledger_is_not_shipped(self) -> None:
        self.assertFalse((ROOT / ".agents/skills/task-knowledge-prep").exists())
        self.assertFalse((ROOT / "scripts/task_case.py").exists())
        self.assertFalse((ROOT / "scripts/source_run.py").exists())
        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        manifest = (ROOT / "harness.yaml").read_text(encoding="utf-8")
        self.assertNotIn("task-knowledge-prep", contract)
        self.assertNotIn("task_case:", manifest)
        self.assertNotIn("local_git_source_run:", manifest)

    def test_development_workflow_is_verified_in_scoped_and_composite_slices(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        capability = manifest["capabilities"]["knowledge_guided_development"]
        self.assertEqual(
            "verified_at_four_manual_qc_development_and_one_trusted_context_composite_slice",
            capability["adoption"],
        )
        self.assertEqual(
            [
                ".agents/skills/develop-with-knowledge/SKILL.md",
                ".agents/skills/answer-from-knowledge/scripts/knowledge_route.py",
            ],
            capability["entrypoints"],
        )
        self.assertEqual(
            ["knowledge_query_and_context"],
            capability["dependencies"],
        )

        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / capability["entrypoints"][0]).read_text(encoding="utf-8")
        self.assertIn("加载 `develop-with-knowledge`", contract)
        self.assertIn("用户仅声称“方案已批准”不等于存在批准证据", contract)
        self.assertIn("没有用户路径时只检查该目录一次", contract)
        self.assertIn("不得遍历产品树、Git 历史、运行产物", contract)
        self.assertIn("最低充分上下文", skill)
        self.assertIn("## 0. 核对实施依据", skill)
        self.assertIn("用户口头声称“已经批准”是查找线索，不是批准证据", skill)
        self.assertIn("只检查一次当前 Harness", skill)
        self.assertIn("不得为找方案遍历产品树、Git 历史、运行产物", skill)
        self.assertIn("不得自行新建方案后把它标为已批准", skill)
        self.assertIn("实施依据：", skill)
        self.assertIn("用**原始用户请求**调用知识入口路由", skill)
        self.assertIn("knowledge_route.py", skill)
        self.assertIn("只读 `PRIMARY`", skill)
        self.assertIn("三篇是硬上限，不是阅读目标", skill)
        self.assertIn("## 实现前快照", skill)
        self.assertIn("固定项 + 用户可追加项 + 隐式项 - 去重 = 最大合法总量", skill)
        self.assertIn("组合审计", skill)
        self.assertIn("最大合法状态的完整构成", skill)
        self.assertIn("最大合法状态通过、再多一项失败", skill)
        self.assertIn("副作用基线", skill)
        self.assertIn("冲突样本", skill)
        self.assertIn("行数相同", skill)
        self.assertIn("不能继续写入", skill)
        self.assertIn("实际输出证据", skill)
        self.assertIn("真实路径验证", skill)
        self.assertIn("知识变化候选", skill)
        self.assertIn("来源身份", skill)
        self.assertIn("页面默认范围不能冒充固定工况", skill)
        self.assertIn("具体结果值", skill)
        self.assertIn("强范围声明", skill)
        self.assertIn("最可能失败的反例", skill)
        self.assertIn("页面变化不能自动证明导出、弹窗、图表或批量动作", skill)
        self.assertIn("旧行为 → 新 owner → 替代测试或真实证据", skill)
        self.assertIn("不能在实现后重新解释批准条件", skill)
        self.assertIn("用户动作闭环", skill)
        self.assertIn("从全新的真实入口运行默认旅程", skill)
        self.assertIn("缺少入口等于功能未实现", skill)
        self.assertIn("结构化产物不能只检查文件存在", skill)
        self.assertIn("最容易漏掉的合法状态", skill)
        self.assertIn("依赖审计命令非零", skill)
        self.assertIn("视觉或状态样式也要匹配业务语义", skill)
        self.assertIn("规范落点不能只写当前工程", skill)

    def test_writeback_is_verified_only_at_the_declared_slice(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        capability = manifest["capabilities"]["knowledge_writeback"]
        self.assertEqual(
            "verified_at_manual_qc_same_system_adjacent_writeback_slice",
            capability["adoption"],
        )
        self.assertEqual(
            ["knowledge_base", "knowledge_ingestion", "knowledge_guided_development"],
            capability["dependencies"],
        )
        limits = "\n".join(capability["limits"])
        self.assertIn("人工审查", limits)
        self.assertIn("跨系统", limits)
        self.assertIn("第二领域", limits)

    def test_solution_formation_is_routed_before_complex_development(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        capability = manifest["capabilities"]["solution_formation"]
        self.assertEqual("verified_at_deepseek_complex_solution_and_routing_slice", capability["adoption"])
        self.assertEqual([], capability["dependencies"])
        self.assertTrue(any("两个独立重放" in item for item in capability["limits"]))
        self.assertTrue(any("25–40" in item for item in capability["limits"]))
        self.assertEqual(
            [
                ".agents/skills/form-solution/SKILL.md",
                ".agents/skills/form-solution/references/software-solution.md",
                ".opencode/agents/r1-requirements-reviewer.md",
            ],
            capability["entrypoints"],
        )

        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / capability["entrypoints"][0]).read_text(encoding="utf-8")
        reference = (ROOT / capability["entrypoints"][1]).read_text(encoding="utf-8")
        self.assertLess(contract.index("加载 `form-solution`"), contract.index("加载 `develop-with-knowledge`"))
        self.assertIn("先形成并确认 R1 需求", contract)
        self.assertIn("方案获批前不修改产品代码", skill)
        self.assertIn("此时在 `review.md` 中只开放 `R1`", skill)
        self.assertIn("连续两次读取没有改变", skill)
        self.assertIn("不要凭经验硬编码分页量", skill)
        self.assertIn("当前实现只证明“现在怎样做”", skill)
        self.assertIn("不因“风险低”默认让新旧两套职责长期并存", skill)
        self.assertIn("集合不自动变成有序列表", skill)
        self.assertIn("由提供方保证完整或整体失败", skill)
        self.assertIn("不要机械默认 CSV", skill)
        self.assertIn("“存在多个技术选项”本身不构成人工待决", skill)
        self.assertIn("R2 是可施工方案，不是方向清单", skill)
        self.assertIn("R2 不能悄悄削弱已经确认的 R1", skill)
        self.assertIn("一边声称“无需新增查询/已有数据直接生成”", skill)
        self.assertIn("不再叫“仍需用户决定”", skill)
        self.assertIn("不能用“例如某某查询”", skill)
        self.assertIn("接口表是方案的完整施工清单", skill)
        self.assertIn("也包含客户端聚合、指标计算、导出", skill)
        self.assertIn("它的消费者只能是尚未迁移的旧调用方", skill)
        self.assertIn("视为责任冲突，R2 不可交接", skill)
        self.assertIn("动作极性必须一致", skill)
        self.assertIn("不是把变长记录作为额外行混进同一张", skill)
        self.assertIn("一对多或变长数据放入可关联的独立", skill)
        self.assertIn("每个待决项都能说明为何只能由", skill)
        self.assertIn("已经收敛的选择换个说法再次提问", skill)
        self.assertIn("其他方案基本合理", skill)
        self.assertIn("R2 待整体确认，当前", skill)
        self.assertIn("待决项数量必须相同", skill)
        self.assertIn("同一完整任务的实现顺序", skill)
        self.assertIn("交给 `develop-with-knowledge`", skill)
        self.assertIn("从 R1 中的日常工作反推结构", skill)
        self.assertIn("至少两个存在实质差异的真实", skill)
        self.assertIn("产品写入白名单只有这张 `review.md`", skill)
        self.assertIn("`.env.example`、`.gitignore`", skill)

        reference = (ROOT / ".agents/skills/form-solution/references/software-solution.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("### 从日常工作反推架构", reference)
        self.assertIn("### 配置与秘密", reference)
        self.assertIn("### 数据结构与访问方式", reference)
        self.assertIn("目录仍不足以证明软件设计成立", reference)
        self.assertIn("业务配置变化不能被误写成", reference)
        self.assertIn("形成候选表以后逐表反证", reference)
        self.assertIn("一个业务名词不自动获得一张表", reference)
        self.assertIn("图片、附件、模型文件等大对象", reference)
        self.assertIn("只能来自本轮保存的命令或运行输出", reference)
        self.assertIn("需求尚未确认时只写 R1", reference)
        self.assertIn("迁移后退出", reference)
        self.assertIn("无序选择使用集合语义", reference)
        self.assertIn("不能把“每次操作分别查询、各自复用结果”写成一次取数", reference)
        self.assertIn("业务对象和责任 owner", reference)
        self.assertIn("同属一个业务模块不等于共用一个万能 Service", reference)
        self.assertIn("独立变化、独立验证和", reference)
        self.assertIn("不要用“都围绕同一批数据”", reference)
        self.assertIn("把每个 Service 的公开方法按用户工作流分组", reference)
        self.assertIn("保留同一领域目录，但把应用责任拆给更具体的 owner", reference)
        self.assertIn("目标软件真实打开", reference)
        self.assertIn("把本轮确定会建设的接口列成表", reference)
        self.assertIn("不要在表外说“另有独立用例”", reference)
        self.assertIn("在基础明细中追加另一类行", reference)
        self.assertIn("无新增后端接口", reference)
        self.assertIn("当前兼容入口", reference)
        self.assertIn("目标业务用例", reference)
        self.assertIn("目标链路的消费者不得继续把泛化兼容入口", reference)
        self.assertIn("重叠的用户页面或工作流也属于两套职责", reference)
        self.assertIn("可追溯的底层明细", reference)
        self.assertIn("如果它只影响内部技术实现", reference)

        r1_agent = (ROOT / ".opencode/agents/r1-requirements-reviewer.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("mode: subagent", r1_agent)
        self.assertIn("`src/`", r1_agent)
        self.assertIn('"workspaces/reviews/**": allow', r1_agent)
        self.assertIn("bash: deny", r1_agent)
        self.assertIn("glob: deny", r1_agent)
        self.assertIn("grep: deny", r1_agent)
        self.assertIn('"form-solution": allow', r1_agent)
        self.assertIn("只负责复杂任务的 **R1 需求理解**", r1_agent)
        self.assertIn("R2 只写“等待 R1 通过”", r1_agent)

    def test_solution_skill_has_no_quality_check_answer_leakage(self) -> None:
        content = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                ".agents/skills/form-solution/SKILL.md",
                ".agents/skills/form-solution/references/software-solution.md",
                ".agents/skills/form-solution/agents/openai.yaml",
            )
        )
        for leaked_term in (
            "Good通过率",
            "Bad通过率",
            "1000 行",
            "10000 行",
            "manual_qc/snapshot",
            "人工质检标注验收",
        ):
            self.assertNotIn(leaked_term, content)

    def test_local_work_review_declares_only_scoped_verification(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        capability = manifest["capabilities"]["local_work_review"]
        self.assertEqual(
            "verified_at_deepseek_software_review_positive_mismatch_no_trigger_slice",
            capability["adoption"],
        )
        self.assertEqual([], capability["dependencies"])
        self.assertEqual(
            [
                ".agents/skills/review-work/SKILL.md",
                ".agents/skills/review-work/references/software-development.md",
            ],
            capability["entrypoints"],
        )

        contract = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / capability["entrypoints"][0]).read_text(encoding="utf-8")
        software = (ROOT / capability["entrypoints"][1]).read_text(encoding="utf-8")
        self.assertIn("加载 `review-work`", contract)
        self.assertIn("设计与 Harness 审查尚未作为正式能力发布", contract)
        self.assertIn("简单问答", skill)
        self.assertIn("workspaces/reviews/<task-id>/review.md", skill)
        self.assertIn("先核对任务对象", skill)
        self.assertIn("错位", skill)
        self.assertIn("停止要求用户继续批准", skill)
        self.assertIn("立即停止继续读取 Diff、源码、运行历史", skill)
        self.assertIn("先只取得**任务身份包**", skill)
        self.assertIn("此时\n不要读取 Git Diff、源码、运行记录", skill)
        self.assertIn("阶段 A：任务对象工具边界", skill)
        self.assertIn("访问产品或知识产物目录，运行 Git", skill)
        self.assertIn("阶段 A 就是终点", skill)
        self.assertIn("不得自行扩展文件数、实现细节或验证结论", skill)
        self.assertIn("批准状态优先于 Agent", skill)
        self.assertIn("不得用这种可能性反复重开对齐判断", skill)
        self.assertIn("只有任务对象确认对齐后", skill)
        self.assertIn("错位报告不加载该参考", skill)
        self.assertIn("不代替模糊需求的方案形成", skill)
        self.assertIn("不用于知识摄入、设计/Harness 审查", skill)
        self.assertIn("报告体验单独用 `D1`", skill)
        self.assertIn("不得建议跳到 `R5`", skill)
        self.assertIn("产品", software)
        self.assertIn("业务模块", software)
        self.assertIn("前端、后端、数据或外部系统", software)
        self.assertIn("不要使用“结构化需求理解”之类抽象分类", software)
        self.assertIn("只能开放第一个尚未确认的 `R`", software)
        self.assertIn("怎样使用", software)
        self.assertIn("内容导航", software)
        self.assertIn("至少用一张 Mermaid", software)
        self.assertIn("审查目的", software)
        self.assertIn("当前待审内容", software)
        self.assertIn("处理结果", software)
        self.assertIn("你的反馈", software)
        self.assertIn("不要为了“发现问题”制造低价值待决点", software)
        self.assertIn("批准关闭条件覆盖", software)
        self.assertIn("公共复用", software)
        self.assertIn("旧 owner 没有活跃消费者", software)
        self.assertIn("剩余测试全绿不能替代这张映射", software)
        self.assertIn("报告内部是否自相矛盾", software)
        self.assertIn("总体决定保持关闭", software)
        self.assertIn("报告若一面承认必需项未完成", skill)
        self.assertFalse((ROOT / ".agents/skills/review-work/scripts").exists())

    def test_complex_delivery_uses_read_only_independent_review(self) -> None:
        develop = (ROOT / ".agents/skills/develop-with-knowledge/SKILL.md").read_text(encoding="utf-8")
        protocol = (ROOT / ".agents/skills/review-work/references/independent-delivery-check.md").read_text(encoding="utf-8")
        agent = (ROOT / ".opencode/agents/delivery-reviewer.md").read_text(encoding="utf-8")

        self.assertIn("复杂施工的独立完成复核", develop)
        self.assertIn("只读 `delivery-reviewer`", develop)
        self.assertIn("不要先告诉它“已经通过”", develop)
        self.assertIn("没有可用的独立上下文", develop)
        self.assertIn("不得声明复杂原始任务已经", develop)
        self.assertIn("从修改前 commit 读取批准条件", protocol)
        self.assertIn("从全新的用户入口", protocol)
        self.assertIn("下游消费者", protocol)
        self.assertIn("pass / fail / not_proven", protocol)
        self.assertIn("mode: subagent", agent)
        self.assertIn("write: false", agent)
        self.assertIn("edit: false", agent)

    def test_knowledge_bundle_matches_declared_adoption(self) -> None:
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        domains = yaml.safe_load(
            (ROOT / "config/knowledge-domains.yaml").read_text(encoding="utf-8")
        )
        substantive = [
            path
            for area in ("domains", "capabilities", "systems", "sources")
            for path in (ROOT / "knowledge" / area).rglob("*.md")
            if path.name not in {"index.md", "log.md"}
        ]
        adoption = manifest["capabilities"]["knowledge_base"]["adoption"]
        if adoption == "implemented_empty_okf_scaffold":
            self.assertEqual([], domains["domains"])
            self.assertEqual([], substantive)
        else:
            self.assertTrue(domains["domains"])
            self.assertTrue(substantive)
        self.assertFalse((ROOT / "knowledge/index.md").read_text(encoding="utf-8").startswith("---"))

    def test_release_surface_contains_only_runtime_assets(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review.md", skill)
        self.assertIn("领域/旅程视图都存在", skill)
        self.assertIn("python scripts/knowledge_check.py", skill)
        self.assertIn("python scripts/ingestion_workspace.py", skill)
        self.assertFalse((ROOT / "eval").exists())
        self.assertFalse((ROOT / "docs/experiments").exists())
        manifest = yaml.safe_load((ROOT / "harness.yaml").read_text(encoding="utf-8"))
        for capability in manifest["capabilities"].values():
            self.assertTrue(all(not path.startswith("eval/") for path in capability["entrypoints"]))

    def test_ingestion_workflow_is_content_first(self) -> None:
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## 知识内容优先", agents)
        self.assertIn("每项发现只表达一个可复用结论", agents)
        self.assertIn("一个明确读者问题为最小交付单位", agents)

        expected_steps = (
            "## 1. 选择最低充分路径",
            "## 2. 宽范围完整整理",
            "### 2.1 固定用户承诺与材料范围",
            "### 2.2 审视材料地图并形成读后发现",
            "### 2.3 规划并复核知识目录",
            "### 2.4 按目录形成规范知识和产品视图",
            "## 3. 代码变化回写",
            "### 3.1 先固定读者问题与系统身份",
            "### 3.2 从影响面规划，不从仓库目录规划",
            "### 3.3 把发现重构成知识，而不是更新摘要",
            "### 3.4 完成父知识融合与审查",
            "## 4. 聚焦代码或问题整理",
            "## 5. 人工审查与发布",
        )
        positions = [skill.index(step) for step in expected_steps]
        self.assertEqual(sorted(positions), positions)
        self.assertLess(
            skill.index("审视材料地图并形成读后发现"),
            skill.index("规划并复核知识目录"),
        )
        self.assertIn("保留父知识不等于逐字冻结", skill)
        self.assertIn("没有当前态表述与新发现互相矛盾", skill)

    def test_ingestion_assets_drive_questions_sources_and_reading_routes(self) -> None:
        assets = ROOT / ".agents/skills/ingest-knowledge/assets"
        product_view = (assets / "product-view.md").read_text(encoding="utf-8")
        software_architecture = (assets / "software-architecture.md").read_text(
            encoding="utf-8"
        )
        shared_capability = (assets / "shared-capability-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## 推荐路线：从全貌到细节", product_view)
        self.assertIn("## 按问题查找", product_view)
        self.assertIn("最小充分路线", product_view)
        self.assertIn("draft/knowledge/views/by-domain/<slug>.md", product_view)
        self.assertIn("不要另建 `draft/views/`", product_view)
        self.assertIn("## 代码地图与职责", software_architecture)
        self.assertIn("## 核心对象和数据变化", software_architecture)
        self.assertIn("## 一次具体修改路径", software_architecture)
        self.assertIn("不要求先出现第二个外部领域", shared_capability)
        self.assertIn("draft/knowledge/capabilities/", shared_capability)
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不在开始时加载全部资产", skill)
        self.assertIn("只读取 `next` 返回的 `absolute_path`", skill)
        self.assertIn("每题规划一至四个", skill)
        self.assertIn("需要更多时先收束问题或调整知识地图", skill)
        self.assertIn("不恢复逐文件 `mark`", skill)
        self.assertIn("目标覆盖", skill)
        self.assertIn("stop-search", skill)
        self.assertIn("从项目根可复制执行的命令", skill)
        self.assertIn("绑定旧 commit、分支、版本或能力状态", skill)
        self.assertIn("新增消费者与责任边界", skill)
        self.assertIn("id/title/parent/scope/excludes", (assets / "domain-overview.md").read_text(encoding="utf-8"))
        retired_assets = (
            "brief.md", "completion.yaml", "inventory.md", "questions.md",
            "reader-answers.md", "review.md",
        )
        self.assertTrue(all(not (assets / name).exists() for name in retired_assets))

    def test_ingestion_keeps_complete_and_focused_reading_bounded(self) -> None:
        skill = (ROOT / ".agents/skills/ingest-knowledge/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("不维护逐文件阅读打卡", skill)
        self.assertIn("同一个当前审视单元", skill)
        self.assertIn("每项发现保存决定理解或行动的关键细节", skill)
        self.assertIn("正文中的真实章节标题", skill)
        self.assertIn("只读取 `next` 返回的 `absolute_path`", skill)
        self.assertIn("正文必须充分内化", skill)
        self.assertIn("只把候选知识、产品视图和根 `review.md` 交给用户", skill)

    def test_retired_knowledge_layout_is_absent(self) -> None:
        retired_paths = (
            "knowledge/hubs",
            "knowledge/concepts",
            "knowledge/playbooks",
            "knowledge/code",
            "knowledge/taxonomy.yaml",
        )
        self.assertTrue(all(not (ROOT / path).exists() for path in retired_paths))

    def test_skill_asset_markdown_table_headers_match_separators(self) -> None:
        assets = ROOT / ".agents/skills/ingest-knowledge/assets"
        for path in assets.glob("*.md"):
            lines = path.read_text(encoding="utf-8").splitlines()
            for previous, current in zip(lines, lines[1:]):
                if re.fullmatch(r"\|(?:\s*:?-+:?\s*\|)+", current):
                    self.assertEqual(
                        previous.count("|"),
                        current.count("|"),
                        f"malformed Markdown table in {path.name}: {previous!r}",
                    )


if __name__ == "__main__":
    unittest.main()
