from __future__ import annotations

from typing import Any

from .repository import ViewConfigRepository


class ViewConfigService:
    """Application boundary for the current local user's saved views."""

    LOCAL_OWNER_ID = "local-user"
    DEFAULT_VIEW_NAME = "默认视图"
    DATA_WORKBENCH_VIEW_NAME = "数据工作台"

    def __init__(self, repository: ViewConfigRepository) -> None:
        self._repository = repository

    def get_dashboard(self, page_key: str) -> dict[str, Any] | None:
        return self._repository.get(
            owner_id=self.LOCAL_OWNER_ID,
            page_key=page_key,
            view_name=self.DEFAULT_VIEW_NAME,
        )

    def save_dashboard(
        self,
        page_key: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        return self._repository.save(
            owner_id=self.LOCAL_OWNER_ID,
            page_key=page_key,
            view_name=self.DEFAULT_VIEW_NAME,
            view_type="dashboard",
            config=config,
        )

    def get_data_workbench(self, page_key: str) -> dict[str, Any] | None:
        return self._repository.get(
            owner_id=self.LOCAL_OWNER_ID,
            page_key=page_key,
            view_name=self.DATA_WORKBENCH_VIEW_NAME,
        )

    def save_data_workbench(
        self,
        page_key: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        return self._repository.save(
            owner_id=self.LOCAL_OWNER_ID,
            page_key=page_key,
            view_name=self.DATA_WORKBENCH_VIEW_NAME,
            view_type="data_workbench",
            config=config,
        )
