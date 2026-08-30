from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


METRIC_NUMBER_KEYS = (
    "annotation_total",
    "annotation_submitted",
    "expect_alloc",
    "actual_alloc",
    "actual_complete",
    "correct",
    "incorrect",
    "expect_pass",
    "expect_reject",
    "actual_pass",
    "actual_reject",
)


@dataclass(frozen=True)
class SnapshotFilter:
    stat_date_start: date | None = None
    stat_date_end: date | None = None
    scene_name: str | None = None
    group_name: str | None = None
    employee_id: str | None = None
    project_name: str | None = None


def empty_metric() -> dict[str, Any]:
    """Return the documented JSONB metric shape for tests and local fixtures."""
    return {
        **{key: 0 for key in METRIC_NUMBER_KEYS},
        "conclusion": None,
        "exec_status": None,
    }
