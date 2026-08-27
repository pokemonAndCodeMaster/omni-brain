from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from .storage import RunStore
from .utils import utc_now, write_json


JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "success": {"type": "boolean"},
        "completion_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "process_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "problems": {"type": "array", "items": {"type": "string"}},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
        "improvement_suggestion": {"type": "string"},
    },
    "required": [
        "success",
        "completion_score",
        "process_score",
        "summary",
        "strengths",
        "problems",
        "evidence_refs",
        "improvement_suggestion",
    ],
}


class JudgeService:
    def __init__(self, store: RunStore) -> None:
        self.store = store

    def _prompt(self, run: dict[str, Any]) -> str:
        events = self.store.events(run["id"])[-160:]
        event_lines = [
            f"event:{event.get('seq')} [{event.get('type')}] {event.get('summary', '')[:800]}"
            for event in events
        ]
        final_text = self.store.artifact_text(run["id"], "final.md", 24_000)
        patch = self.store.artifact_text(run["id"], "workspace.patch", 24_000)
        expected = run.get("expected")
        return f"""你是 Omni-Brain 当前唯一的独立任务评测 Judge。

请只根据下面提供的目标、最终结果、可见执行轨迹、代码差异和可选预期来评价。不要因为缺少 Ground Truth 就拒绝评价，也不要猜测隐藏思维过程。

只评两个顶层维度：
1. 任务完成：目标与约束是否满足，最终产物是否可用。
2. 执行过程：可见步骤、Skill、工具和证据使用是否合理，是否存在绕路、遗漏或错误。

任务：
{run.get('prompt', '')}

可选预期：
{json.dumps(expected, ensure_ascii=False, indent=2) if expected else '未提供'}

最终结果：
{final_text or '未捕获最终结果'}

代码差异：
{patch or '没有代码差异'}

可见轨迹：
{chr(10).join(event_lines) or '没有可见轨迹'}

evidence_refs 必须引用上面的 event:<seq>、final.md 或 workspace.patch。输出严格遵循 JSON Schema。"""

    async def evaluate(self, run: dict[str, Any], model: str | None = None) -> dict[str, Any]:
        run_dir = self.store.run_dir(run["id"])
        schema_path = run_dir / "judge-schema.json"
        output_path = run_dir / "evaluation.json"
        write_json(schema_path, JUDGE_SCHEMA)
        argv = [
            "codex",
            "exec",
            "--json",
            "--ephemeral",
            "--skip-git-repo-check",
            "-c",
            'approval_policy="never"',
            "-s",
            "read-only",
            "-C",
            str(run_dir),
            "--output-schema",
            str(schema_path),
            "-o",
            str(output_path),
        ]
        if model:
            argv.extend(["-m", model])
        argv.append("-")
        process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=run_dir,
        )
        stdout, stderr = await process.communicate(self._prompt(run).encode("utf-8"))
        (run_dir / "judge-events.jsonl").write_bytes(stdout)
        (run_dir / "judge-stderr.log").write_bytes(stderr)
        if process.returncode != 0:
            raise RuntimeError(stderr.decode("utf-8", errors="replace")[-4000:])
        result = json.loads(output_path.read_text(encoding="utf-8"))
        result["evaluated_at"] = utc_now()
        result["judge"] = "codex"
        result["judge_model"] = model or "default"
        write_json(output_path, result)
        return result
