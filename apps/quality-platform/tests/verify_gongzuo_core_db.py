"""Run against the isolated local PostgreSQL; it creates and removes only __verify_core__ rows."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from psycopg.types.json import Jsonb

from src.api.app import create_app
from src.config import ConfigManager
from src.database import DatabaseManager


PREFIX = "__verify_core__"


def main() -> None:
    ids: list[str] = []
    run_id = f"{PREFIX}run"
    try:
        with TestClient(create_app()) as client:
            rejected = client.post(
                "/api/gongzuo/team/items",
                json={"itemType": "requirement", "title": PREFIX, "status": "completed"},
            )
            assert rejected.status_code == 400, rejected.text
            first = client.post(
                "/api/gongzuo/team/items",
                json={"itemType": "requirement", "title": PREFIX + " first", "payload": {"goal": "actual input goal", "scope": "actual scope"}},
            )
            second = client.post(
                "/api/gongzuo/team/items",
                json={"itemType": "research", "title": PREFIX + " second", "payload": {"parentId": first.json()["id"], "goal": "child focus"}},
            )
            personal = client.post(
                "/api/gongzuo/personal/items",
                json={"itemType": "learning", "title": PREFIX + " personal"},
            )
            assert all(response.status_code == 201 for response in (first, second, personal))
            first_id, second_id, personal_id = first.json()["id"], second.json()["id"], personal.json()["id"]
            ids.extend((first_id, second_id, personal_id))
            detail = client.get(f"/api/gongzuo/team/items/{first_id}")
            assert detail.status_code == 200 and detail.json()["context"]["content"] == {"goal": "actual input goal", "scope": "actual scope"}
            relation = client.post("/api/gongzuo/team/relations", json={"fromKind":"item","fromId":second_id,"toKind":"item","toId":first_id,"relationType":"contributes_to"})
            assert relation.status_code == 201, relation.text
            old_snapshot = client.app.state.gongzuo_service.current_context_snapshot("team", second_id)
            assert old_snapshot["content"]["goal"] == "actual input goal" and old_snapshot["focus"]["goal"] == "child focus"
            proposal = client.post(f"/api/gongzuo/team/items/{first_id}/context/proposals", json={"baseVersion":1,"title":"parent v2","proposedContent":{"goal":"parent v2"}})
            assert proposal.status_code == 201, proposal.text
            assert client.post(f"/api/gongzuo/team/context-proposals/{proposal.json()['id']}/accept", json={"version":1}).status_code == 200
            fresh_snapshot = client.app.state.gongzuo_service.current_context_snapshot("team", second_id)
            assert old_snapshot["revisionNo"] == 1 and fresh_snapshot["revisionNo"] == 2 and fresh_snapshot["content"]["goal"] == "parent v2"
            idea = client.post("/api/gongzuo/team/entities", json={"entityType": "idea", "title": PREFIX + " idea"})
            assert idea.status_code == 201, idea.text
            ids.append(idea.json()["id"])
            discussion = client.post(f"/api/gongzuo/team/entities/{idea.json()['id']}/discussions", json={"body": "persisted discussion"})
            assert discussion.status_code == 201, discussion.text
            idea_detail = client.get(f"/api/gongzuo/team/entities/{idea.json()['id']}")
            assert idea_detail.status_code == 200 and idea_detail.json()["discussions"][0]["body"] == "persisted discussion"
            config = ConfigManager(project_root=Path("."))
            manager = DatabaseManager(config)
            try:
                manager.postgres().execute(
                    """
                    INSERT INTO manual_qc_lab.t_gongzuo_run (
                        id, workspace, item_id, attempt, actor_id, instruction, prompt_snapshot,
                        item_snapshot, context_snapshot, context_version_id, context_revision_no,
                        engine, runtime, directory
                    ) VALUES (%s, 'team', %s, 1, 'verify', 'verify', 'verify', %s, %s,
                              'verify-context', 1, 'codex', 'native', '/tmp/verify')
                    """,
                    (run_id, first_id, Jsonb({}), Jsonb({})),
                )
            finally:
                manager.close()
            body = {"artifactRef": "verify://artifact", "artifactVersion": "1", "environmentRef": "verify://db", "runId": run_id}
            assert client.post(f"/api/gongzuo/team/items/{second_id}/evidence", json=body).status_code == 400
            assert client.post(f"/api/gongzuo/personal/items/{personal_id}/evidence", json=body).status_code == 400
            accepted = client.post(f"/api/gongzuo/team/items/{first_id}/evidence", json=body)
            assert accepted.status_code == 201, accepted.text
            print("verified create completion gate and run evidence workspace/item ownership")
    finally:
        config = ConfigManager(project_root=Path("."))
        manager = DatabaseManager(config)
        try:
            with manager.postgres().transaction() as connection:
                connection.execute("DELETE FROM manual_qc_lab.t_gongzuo_run WHERE id=%s", (run_id,))
                connection.execute("DELETE FROM manual_qc_lab.t_gongzuo_item WHERE id = ANY(%s)", (ids,))
                connection.execute("DELETE FROM manual_qc_lab.t_gongzuo_entity WHERE id = ANY(%s)", (ids,))
        finally:
            manager.close()


if __name__ == "__main__":
    main()
