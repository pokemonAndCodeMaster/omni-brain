from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = Path(
    os.environ.get("OMNI_BRAIN_AGENT_REGISTRY", PROJECT_ROOT / "config" / "agent-registry.yaml")
).resolve()
STATE_ROOT = Path(
    os.environ.get("OMNI_BRAIN_CONSOLE_STATE", PROJECT_ROOT / ".derived" / "agent-console")
).resolve()
RUN_SITES_ROOT = Path(
    os.environ.get("OMNI_BRAIN_RUN_SITES", PROJECT_ROOT.parent / ".omni-brain-runs")
).resolve()
FRONTEND_DIST = Path(
    os.environ.get("OMNI_BRAIN_CONSOLE_DIST", PROJECT_ROOT / "apps" / "agent-console" / "dist")
).resolve()
