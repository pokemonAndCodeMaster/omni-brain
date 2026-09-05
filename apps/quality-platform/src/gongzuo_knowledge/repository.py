from __future__ import annotations

from typing import Any

from src.database import PGConnector


class GongzuoKnowledgeRepository:
    def __init__(self, postgres: PGConnector) -> None:
        self.postgres = postgres
        self.table = f'{postgres.schema}.t_gongzuo_capability'
        self.checks = f'{postgres.schema}.t_gongzuo_capability_verification'

    @staticmethod
    def wire(row: dict[str, Any]) -> dict[str, Any]:
        keys = {'workspace_key':'workspace', 'source_item_id':'sourceItemId', 'source_entity_id':'sourceEntityId',
                'source_path':'sourcePath', 'base_version':'baseVersion', 'source_revision':'sourceRevision', 'desired_behavior':'desiredBehavior',
                'validation_plan':'validationPlan', 'created_by':'createdBy', 'created_at':'createdAt',
                'published_by':'publishedBy', 'published_at':'publishedAt', 'candidate_id':'candidateId',
                'candidate_version':'candidateVersion', 'run_id':'runId', 'evidence_id':'evidenceId',
                'checked_by':'checkedBy', 'checked_at':'checkedAt'}
        return {keys.get(k,k):v for k,v in row.items()}

    def list(self, workspace: str) -> list[dict[str, Any]]:
        return [self.wire(r) for r in self.postgres.fetch_all(
            f'SELECT * FROM {self.table} WHERE workspace_key=%s ORDER BY created_at DESC', (workspace,))]

    def get(self, workspace: str, candidate_id: str) -> dict[str, Any]:
        row = self.postgres.fetch_one(f'SELECT * FROM {self.table} WHERE workspace_key=%s AND id=%s', (workspace,candidate_id))
        if not row:
            raise KeyError(candidate_id)
        result = self.wire(row)
        result['verifications'] = [self.wire(r) for r in self.postgres.fetch_all(
            f'SELECT * FROM {self.checks} WHERE workspace_key=%s AND candidate_id=%s ORDER BY checked_at DESC', (workspace,candidate_id))]
        return result

    def create(self, workspace: str, row: dict[str, Any], actor: str) -> dict[str, Any]:
        self.postgres.execute(f'''INSERT INTO {self.table}
            (id,workspace_key,title,target,source_item_id,source_entity_id,source_path,base_version,source_revision,
             content,desired_behavior,validation_plan,version,created_by)
            VALUES (%(id)s,%(workspace)s,%(title)s,%(target)s,%(sourceItemId)s,%(sourceEntityId)s,%(sourcePath)s,
                    %(baseVersion)s,%(sourceRevision)s,%(content)s,%(desiredBehavior)s,%(validationPlan)s,%(version)s,%(actor)s)''',
            {**row,'workspace':workspace,'actor':actor})
        return self.get(workspace,row['id'])

    def verify(self, workspace: str, row: dict[str, Any], actor: str) -> dict[str, Any]:
        with self.postgres.transaction() as conn:
            current = conn.execute(f'SELECT * FROM {self.table} WHERE id=%s AND workspace_key=%s FOR UPDATE', (row['candidateId'],workspace)).fetchone()
            if not current:
                raise KeyError(row['candidateId'])
            if current['version'] != row['candidateVersion'] or current['status'] not in ('candidate','verified'):
                raise ValueError('候选版本已改变或已经发布')
            conn.execute(f'''INSERT INTO {self.checks}
                (id,workspace_key,candidate_id,candidate_version,run_id,evidence_id,assessment,result,checked_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (row['id'],workspace,row['candidateId'],row['candidateVersion'],row['runId'],row['evidenceId'],row['assessment'],row['result'],actor))
            conn.execute(f'UPDATE {self.table} SET status=%s WHERE id=%s', ('verified' if row['result']=='accepted' else 'candidate',row['candidateId']))
        return self.get(workspace,row['candidateId'])

    def publish(self, workspace: str, candidate_id: str, version: str, actor: str) -> dict[str, Any]:
        with self.postgres.transaction() as conn:
            row=conn.execute(f'SELECT * FROM {self.table} WHERE id=%s AND workspace_key=%s', (candidate_id,workspace)).fetchone()
            if not row: raise KeyError(candidate_id)
            conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',
                (f"gongzuo:{workspace}:{row['target']}:{row['source_path'] or row['title']}",))
            row=conn.execute(f'SELECT * FROM {self.table} WHERE id=%s AND workspace_key=%s FOR UPDATE', (candidate_id,workspace)).fetchone()
            if row['status']=='published' and row['version']==version:
                return self.get(workspace,candidate_id)
            if row['status']!='verified' or row['version']!=version: raise ValueError('只能发布已验证的当前候选版本')
            active=conn.execute(f'''SELECT version FROM {self.table} WHERE workspace_key=%s AND target=%s
                AND COALESCE(source_path,title)=COALESCE(%s,%s) AND status='published' ''',
                (workspace,row['target'],row['source_path'],row['title'])).fetchone()
            if active and row['target']=='knowledge' and active['version']!=row['base_version']:
                raise ValueError('已存在更新的知识发布，请重新比较与验证')
            # A source has one active release in one workspace. Old runs keep their own snapshot.
            conn.execute(f'''UPDATE {self.table} SET status='superseded' WHERE workspace_key=%s AND status='published'
                AND target=%s AND COALESCE(source_path,title)=COALESCE(%s,%s)''', (workspace,row['target'],row['source_path'],row['title']))
            conn.execute(f"UPDATE {self.table} SET status='published',published_by=%s,published_at=now() WHERE id=%s", (actor,candidate_id))
        return self.get(workspace,candidate_id)
