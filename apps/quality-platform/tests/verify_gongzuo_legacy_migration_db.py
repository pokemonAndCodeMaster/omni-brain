"""Representative S0 bridge verification; creates and removes only __verify_legacy__ rows."""
from __future__ import annotations

from hashlib import md5
from pathlib import Path

from psycopg.types.json import Jsonb

from src.config import ConfigManager
from src.database import DatabaseManager


def legacy_item_id(value: str) -> str:
    return "legacy-rq-" + md5(value.encode()).hexdigest()


def main() -> None:
    idea_id = "__verify_legacy_idea__"
    accepted_id = "req-" + "a" * 60  # exactly 64 characters: verifies bounded bridge IDs
    rejected_id = "__verify_legacy_rejected__"
    revision_id = "__verify_legacy_revision__"
    accepted_item, rejected_item = legacy_item_id(accepted_id), legacy_item_id(rejected_id)
    config = ConfigManager(project_root=Path(".")); manager = DatabaseManager(config); pg = manager.postgres()
    try:
        with pg.transaction() as connection:
            connection.execute("INSERT INTO manual_qc_lab.t_collab_idea(id,title,raw_content,domain_key,created_by,owner_id) VALUES (%s,'legacy idea','original idea text','quality','legacy-author','legacy-owner')", (idea_id,))
            connection.execute("INSERT INTO manual_qc_lab.t_collab_requirement(id,source_type,source_idea_id,title,status,owner_id,created_by) VALUES (%s,'idea',%s,'accepted historical','candidate','legacy-owner','legacy-author')", (accepted_id, idea_id))
            connection.execute("INSERT INTO manual_qc_lab.t_collab_requirement_revision(id,requirement_id,revision_no,content,created_by) VALUES (%s,%s,1,%s,'legacy-author')", (revision_id, accepted_id, Jsonb({'current_problem':'old problem','expected_outcome':'old outcome','in_scope':['scope'],'acceptance_criteria':['criterion']})))
            connection.execute("UPDATE manual_qc_lab.t_collab_requirement SET status='accepted',current_revision_id=%s,accepted_revision_id=%s,commitment='NEXT',target_window='legacy-window' WHERE id=%s", (revision_id,revision_id,accepted_id))
            connection.execute("INSERT INTO manual_qc_lab.t_collab_requirement(id,source_type,title,status,owner_id,created_by) VALUES (%s,'direct','rejected historical','rejected','legacy-owner','legacy-author')", (rejected_id,))
        pg.execute_script((Path('migrations') / '008_gongzuo.sql').read_text(encoding='utf-8'))
        accepted = pg.fetch_one("SELECT id,status,payload FROM manual_qc_lab.t_gongzuo_item WHERE id=%s", (accepted_item,))
        rejected = pg.fetch_one("SELECT id,status,payload FROM manual_qc_lab.t_gongzuo_item WHERE id=%s", (rejected_item,))
        context = pg.fetch_one("SELECT v.content FROM manual_qc_lab.t_gongzuo_context c JOIN manual_qc_lab.t_gongzuo_context_version v ON v.id=c.current_version_id WHERE c.item_id=%s", (accepted_item,))
        assert accepted and accepted['id'] == accepted_item and accepted['status'] == 'planned'
        assert accepted['payload']['legacyRequirementId'] == accepted_id
        assert accepted['payload']['legacySourceIdea']['rawContent'] == 'original idea text'
        assert accepted['payload']['owner'] == 'legacy-owner' and context and context['content']['expected_outcome'] == 'old outcome'
        assert rejected and rejected['status'] == 'cancelled' and rejected['payload']['legacyStatus'] == 'rejected'
        pg.execute("UPDATE manual_qc_lab.t_gongzuo_item SET title='user changed title',version=version+1 WHERE id=%s", (accepted_item,))
        pg.execute_script((Path('migrations') / '008_gongzuo.sql').read_text(encoding='utf-8'))
        assert pg.fetch_one("SELECT title FROM manual_qc_lab.t_gongzuo_item WHERE id=%s", (accepted_item,))['title'] == 'user changed title'
        print('verified accepted/rejected S0 migration, source links, bounded ID, context provenance, and no overwrite on rerun')
    finally:
        with pg.transaction() as connection:
            connection.execute("DELETE FROM manual_qc_lab.t_gongzuo_item WHERE id = ANY(%s)", ([accepted_item,rejected_item],))
            connection.execute("DELETE FROM manual_qc_lab.t_collab_requirement WHERE id = ANY(%s)", ([accepted_id,rejected_id],))
            connection.execute("DELETE FROM manual_qc_lab.t_collab_idea WHERE id=%s", (idea_id,))
        manager.close()


if __name__ == '__main__':
    main()
