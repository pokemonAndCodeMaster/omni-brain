from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SnapshotFilter:
    stat_date_start: date | None = None
    stat_date_end: date | None = None
    scene_name: str | None = None
    group_name: str | None = None
    employee_id: str | None = None
