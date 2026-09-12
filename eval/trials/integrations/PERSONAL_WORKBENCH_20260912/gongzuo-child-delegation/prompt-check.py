import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps/quality-platform"
sys.path[:0] = [str(APP), str(APP / "tests")]
from src.gongzuo.service import GongzuoService
from src.gongzuo_runtime.service import GongzuoRuntimeService
from test_gongzuo import MemoryRepository
from test_gongzuo_runtime import MemoryRuntimeRepository, ShellExecutor

OUT = Path(__file__).resolve().parent
browser = json.loads((OUT / "browser-evidence.json").read_text())
core_repo, runtime_repo = MemoryRepository(), MemoryRuntimeRepository()
core = GongzuoService(core_repo)
for identity, title, goal in [
    ("parent-1", "改善验收体验", "让验收人员看懂结果"),
    ("child-1", "解释分配缺口", "说明每个未分配原因"),
]:
    core_repo.create_item("personal", {
        "id": identity, "item_type": "research", "title": title, "status": "in_progress",
        "payload": {"goal": goal, "scope": "只解释，不改分配规则", **({"parentId": "parent-1"} if identity == "child-1" else {})},
    })
    core.create_context("personal", identity, content={"goal": goal, "scope": "只解释，不改分配规则"}, provenance=[], actor_id="fixture")
core_repo.contexts["personal", "parent-1"].update(revisionNo=7, currentVersionId="parent-version-7")
core_repo.relation_rows.append({
    "fromKind": "item", "fromId": "child-1", "toKind": "item", "toId": "parent-1", "relationType": "contributes_to",
})
runtime = GongzuoRuntimeService(
    repository=runtime_repo, gongzuo_service=core,
    executors={"codex": ShellExecutor()}, runtime_root=OUT / "runtime-fixture",
)
results = []
for observed in browser["results"]:
    for payload in observed["payloads"]:
        run = runtime.create_run(
            "personal", item_id=payload["itemId"], instruction=payload["instruction"],
            engine=payload["engine"], runtime=payload["runtime"], permission=payload["permission"],
        )
        snapshot = deepcopy(runtime.get_run_snapshot("personal", run["id"]))
        assert snapshot["item_id"] == payload["itemId"]
        assert payload["instruction"] in snapshot["prompt_snapshot"]
        if payload["itemId"] == "child-1":
            assert snapshot["context_snapshot"]["focus"]["goal"] == "说明每个未分配原因"
            assert snapshot["context_snapshot"]["content"]["goal"] == "让验收人员看懂结果"
            assert snapshot["context_snapshot"]["inheritedFromItemId"] == "parent-1"
            assert "工作事项：child-1" in snapshot["prompt_snapshot"]
            for text in ("说明每个未分配原因", "让验收人员看懂结果"):
                assert text in snapshot["prompt_snapshot"]
            old = snapshot
            core_repo.contexts["personal", "parent-1"].update(
                revisionNo=8, currentVersionId="parent-version-8", content={"goal": "更新后的父目标"},
            )
            newer = runtime.create_run("personal", item_id="child-1", instruction="按新背景继续", engine="codex")
            new = runtime.get_run_snapshot("personal", newer["id"])
            assert new["context_snapshot"]["content"]["goal"] == "更新后的父目标"
            assert runtime.get_run_snapshot("personal", run["id"])["prompt_snapshot"] == old["prompt_snapshot"]
            assert runtime.get_run_snapshot("personal", run["id"])["context_snapshot"] == old["context_snapshot"]
            assert runtime.get_run("personal", run["id"])["stale_context"]
        (OUT / (payload["itemId"] + "-prompt.md")).write_text(snapshot["prompt_snapshot"])
        results.append({
            "browserPayloadItemId": payload["itemId"], "storedItemId": snapshot["item_id"],
            "contextSourceItemId": snapshot["context_snapshot"].get("inheritedFromItemId", snapshot["item_id"]),
            "contextRevision": snapshot["context_revision_no"],
            "promptContainsInstruction": True, "promptFile": payload["itemId"] + "-prompt.md",
        })
report = {
    "implementation": str(sys.modules["src.gongzuo_runtime.service"].__file__),
    "source": "把真实浏览器发出的 itemId 和 instruction 原样交给候选代码的 GongzuoService + GongzuoRuntimeService。",
    "storage": "已有内存 Repository 测试替身；未连接用户 PostgreSQL，未调用外部 AI。",
    "results": results, "oldChildRunStayedPinned": True, "newChildRunUsesUpdatedParent": True,
}
(OUT / "prompt-evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))

