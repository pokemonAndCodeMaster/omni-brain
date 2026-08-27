#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import uvicorn


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="启动 Omni-Brain Agent 能力工作台")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    uvicorn.run(
        "omni_brain_console.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(SRC_ROOT),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
