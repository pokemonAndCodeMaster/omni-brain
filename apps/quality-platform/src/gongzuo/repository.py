from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from src.database import PGConnector


class ConcurrentUpdateError(ValueError):
    pass


class GongzuoRepository:
    """Persistence owner for Gongzuo. All workspace scoping is enforced in SQL."""

    def __init__(self, postgres: PGConnector) -> None:
        self._postgres = postgres
        s = postgres.schema
        self.items = f'{s}.t_gongzuo_item'; self.entities = f'{s}.t_gongzuo_entity'; self.relations = f'{s}.t_gongzuo_relation'
        self.contexts = f'{s}.t_gongzuo_context'; self.versions = f'{s}.t_gongzuo_context_version'; self.proposals = f'{s}.t_gongzuo_context_proposal'
        self.discussions = f'{s}.t_gongzuo_discussion'; self.evidence = f'{s}.t_gongzuo_evidence'; self.activities = f'{s}.t_gongzuo_activity'
        self.preferences = f'{s}.t_gongzuo_preference'; self.meetings = f'{s}.t_gongzuo_meeting'; self.snapshots = f'{s}.t_gongzuo_meeting_snapshot'; self.notes = f'{s}.t_gongzuo_meeting_note'
        self.runs = f'{s}.t_gongzuo_run'

    @staticmethod
    def _camel(row: dict[str, Any]) -> dict[str, Any]:
        names = {'workspace_key':'workspace','item_type':'itemType','entity_type':'entityType','created_by':'createdBy','updated_by':'updatedBy','created_at':'createdAt','updated_at':'updatedAt','from_kind':'fromKind','from_id':'fromId','to_kind':'toKind','to_id':'toId','relation_type':'relationType','current_version_id':'currentVersionId','revision_no':'revisionNo','base_version':'baseVersion','proposed_content':'proposedContent','artifact_ref':'artifactRef','artifact_version':'artifactVersion','environment_ref':'environmentRef','run_id':'runId','reviewed_by':'reviewedBy','reviewed_at':'reviewedAt','review_reason':'reviewReason','actor_id':'actorId','item_id':'itemId','entity_id':'entityId','meeting_id':'meetingId','meeting_version':'meetingVersion','preference_key':'preferenceKey'}
        return {names.get(k,k): v for k,v in row.items()}

    def _one(self, sql: str, p: dict[str, Any]) -> dict[str, Any] | None:
        row = self._postgres.fetch_one(sql, p); return self._camel(row) if row else None

    def list_items(self, workspace: str, *, query: str | None = None, status: str | None = None, item_type: str | None = None, limit: int | None = 100, offset: int = 0) -> tuple[list[dict[str, Any]], int]:
        where = ['workspace_key=%(workspace)s']; p: dict[str,Any] = {'workspace':workspace,'offset':offset}
        if query: where.append("title ILIKE %(query)s"); p['query'] = f'%{query}%'
        if status: where.append('status=%(status)s'); p['status']=status
        if item_type: where.append('item_type=%(item_type)s'); p['item_type']=item_type
        page = 'LIMIT %(limit)s OFFSET %(offset)s' if limit is not None else ''
        if limit is not None: p['limit'] = limit
        rows=self._postgres.fetch_all(f"SELECT id,workspace_key,item_type,title,status,payload,version,created_by,created_at,updated_by,updated_at,count(*) OVER() total FROM {self.items} WHERE {' AND '.join(where)} ORDER BY updated_at DESC,id DESC {page}",p)
        return [self._camel({k:v for k,v in r.items() if k!='total'}) for r in rows], int(rows[0]['total']) if rows else 0

    def get_item(self, workspace: str, item_id: str) -> dict[str, Any] | None:
        return self._one(f'SELECT id,workspace_key,item_type,title,status,payload,version,created_by,created_at,updated_by,updated_at FROM {self.items} WHERE workspace_key=%(workspace)s AND id=%(id)s', {'workspace':workspace,'id':item_id})

    def create_item(self, workspace: str, row: dict[str, Any]) -> dict[str, Any]:
        with self._postgres.transaction() as connection:
            connection.execute(f'INSERT INTO {self.items}(id,workspace_key,item_type,title,status,payload,created_by,updated_by) VALUES (%(id)s,%(workspace)s,%(item_type)s,%(title)s,%(status)s,%(payload)s,%(actor)s,%(actor)s)', {**row,'workspace':workspace,'payload':Jsonb(row['payload'])})
            if row.get('context_id'):
                connection.execute(f'INSERT INTO {self.contexts}(id,workspace_key,item_id) VALUES (%s,%s,%s)', (row['context_id'],workspace,row['id']))
                connection.execute(f"INSERT INTO {self.versions}(id,context_id,revision_no,status,content,provenance,accepted_by,accepted_at,created_by) VALUES (%s,%s,1,'accepted',%s,%s,%s,now(),%s)", (row['context_version_id'],row['context_id'],Jsonb(row['initial_context']),Jsonb(row['provenance']),row['actor'],row['actor']))
                connection.execute(f'UPDATE {self.contexts} SET current_version_id=%s WHERE id=%s',(row['context_version_id'],row['context_id']))
        return self.get_item(workspace,row['id']) or (_ for _ in ()).throw(RuntimeError('item readback failed'))

    def update_item(self, workspace: str, item_id: str, expected: int, changes: dict[str, Any], actor: str) -> dict[str, Any]:
        sets=[]; p={'workspace':workspace,'id':item_id,'expected':expected,'actor':actor}
        for key in ('title','status','payload'):
            if key in changes:
                sets.append(f'{key}=%({key})s'); p[key]=Jsonb(changes[key]) if key=='payload' else changes[key]
        sets += ['version=version+1','updated_by=%(actor)s','updated_at=now()']
        count=self._postgres.execute(f"UPDATE {self.items} SET {','.join(sets)} WHERE workspace_key=%(workspace)s AND id=%(id)s AND version=%(expected)s",p)
        if count != 1: raise ConcurrentUpdateError('事项不存在或已被其他人更新')
        return self.get_item(workspace,item_id) or (_ for _ in ()).throw(RuntimeError('item readback failed'))

    def create_entity(self, workspace: str, row: dict[str, Any]) -> dict[str, Any]:
        self._postgres.execute(f'INSERT INTO {self.entities}(id,workspace_key,entity_type,title,payload,created_by,updated_by) VALUES (%(id)s,%(workspace)s,%(entity_type)s,%(title)s,%(payload)s,%(actor)s,%(actor)s)',{**row,'workspace':workspace,'payload':Jsonb(row['payload'])})
        return self.get_entity(workspace,row['id']) or (_ for _ in ()).throw(RuntimeError('entity readback failed'))

    def get_entity(self, workspace: str, entity_id: str) -> dict[str, Any] | None:
        return self._one(f'SELECT id,workspace_key,entity_type,title,payload,version,created_by,created_at,updated_by,updated_at FROM {self.entities} WHERE workspace_key=%(workspace)s AND id=%(id)s',{'workspace':workspace,'id':entity_id})

    def update_entity(self, workspace: str, entity_id: str, expected: int, changes: dict[str, Any], actor: str) -> dict[str, Any]:
        sets=[]; p={'workspace':workspace,'id':entity_id,'expected':expected,'actor':actor}
        for key in ('title','payload'):
            if key in changes:
                sets.append(f'{key}=%({key})s'); p[key]=Jsonb(changes[key]) if key=='payload' else changes[key]
        if not sets: raise ValueError('至少提交一个要更新的字段')
        sets += ['version=version+1','updated_by=%(actor)s','updated_at=now()']
        count=self._postgres.execute(f"UPDATE {self.entities} SET {','.join(sets)} WHERE workspace_key=%(workspace)s AND id=%(id)s AND version=%(expected)s",p)
        if count != 1: raise ConcurrentUpdateError('实体不存在或已被其他人更新')
        return self.get_entity(workspace,entity_id) or (_ for _ in ()).throw(RuntimeError('entity readback failed'))

    def list_entities(self, workspace: str, entity_type: str | None = None) -> list[dict[str, Any]]:
        rows=self._postgres.fetch_all(f'SELECT id,workspace_key,entity_type,title,payload,version,created_by,created_at,updated_by,updated_at FROM {self.entities} WHERE workspace_key=%(workspace)s {"AND entity_type=%(entity_type)s" if entity_type else ""} ORDER BY updated_at DESC,id DESC',{'workspace':workspace,'entity_type':entity_type})
        return [self._camel(r) for r in rows]

    def create_relation(self, workspace: str, row: dict[str, Any]) -> dict[str, Any]:
        self._postgres.execute(f'INSERT INTO {self.relations}(id,workspace_key,from_kind,from_id,to_kind,to_id,relation_type,created_by) VALUES (%(id)s,%(workspace)s,%(from_kind)s,%(from_id)s,%(to_kind)s,%(to_id)s,%(relation_type)s,%(actor)s) ON CONFLICT(workspace_key,from_kind,from_id,to_kind,to_id,relation_type) DO NOTHING',{**row,'workspace':workspace})
        result=self._one(f'SELECT id,workspace_key,from_kind,from_id,to_kind,to_id,relation_type,created_by,created_at FROM {self.relations} WHERE workspace_key=%(workspace)s AND from_kind=%(from_kind)s AND from_id=%(from_id)s AND to_kind=%(to_kind)s AND to_id=%(to_id)s AND relation_type=%(relation_type)s',{**row,'workspace':workspace})
        return result or (_ for _ in ()).throw(RuntimeError('relation readback failed'))

    def list_relations(self, workspace: str, item_id: str | None = None) -> list[dict[str, Any]]:
        suffix=' AND (from_id=%(item_id)s OR to_id=%(item_id)s)' if item_id else ''
        rows=self._postgres.fetch_all(f'SELECT id,workspace_key,from_kind,from_id,to_kind,to_id,relation_type,created_by,created_at FROM {self.relations} WHERE workspace_key=%(workspace)s{suffix}',{'workspace':workspace,'item_id':item_id})
        return [self._camel(r) for r in rows]

    def delete_relation(self, workspace: str, relation_id: str) -> None:
        if self._postgres.execute(f'DELETE FROM {self.relations} WHERE workspace_key=%s AND id=%s', (workspace, relation_id)) != 1:
            raise KeyError(relation_id)

    def add_discussion(self, workspace: str, row: dict[str, Any]) -> dict[str, Any]:
        self._postgres.execute(f'INSERT INTO {self.discussions}(id,workspace_key,item_id,entity_id,anchor,body,payload,created_by) VALUES (%(id)s,%(workspace)s,%(item_id)s,%(entity_id)s,%(anchor)s,%(body)s,%(payload)s,%(actor)s)',{**row,'workspace':workspace,'payload':Jsonb(row.get('payload',{}))})
        return self._one(f'SELECT * FROM {self.discussions} WHERE id=%(id)s AND workspace_key=%(workspace)s',{'id':row['id'],'workspace':workspace}) or (_ for _ in ()).throw(RuntimeError('discussion readback failed'))

    def list_discussions(self, workspace: str, item_id: str | None = None, entity_id: str | None = None) -> list[dict[str, Any]]:
        col,val=('item_id',item_id) if item_id else ('entity_id',entity_id)
        rows=self._postgres.fetch_all(f'SELECT * FROM {self.discussions} WHERE workspace_key=%(workspace)s AND {col}=%(subject)s ORDER BY created_at',{'workspace':workspace,'subject':val})
        return [self._camel(r) for r in rows]

    def context(self, workspace: str, item_id: str) -> dict[str, Any] | None:
        return self._one(f'SELECT c.id,c.workspace_key,c.item_id,c.current_version_id,c.version,c.created_at,c.updated_at,v.revision_no,v.content,v.provenance,v.accepted_at,v.accepted_by FROM {self.contexts} c LEFT JOIN {self.versions} v ON v.id=c.current_version_id WHERE c.workspace_key=%(workspace)s AND c.item_id=%(item)s',{'workspace':workspace,'item':item_id})

    def create_context(self, workspace: str, context_id: str, version_id: str, item_id: str, content: dict[str,Any], provenance: list[dict[str,Any]], actor: str) -> dict[str,Any]:
        with self._postgres.transaction() as c:
            c.execute(f'INSERT INTO {self.contexts}(id,workspace_key,item_id) VALUES (%s,%s,%s)',(context_id,workspace,item_id))
            c.execute(f"INSERT INTO {self.versions}(id,context_id,revision_no,status,content,provenance,accepted_by,accepted_at,created_by) VALUES (%s,%s,1,'accepted',%s,%s,%s,now(),%s)",(version_id,context_id,Jsonb(content),Jsonb(provenance),actor,actor))
            c.execute(f'UPDATE {self.contexts} SET current_version_id=%s WHERE id=%s',(version_id,context_id))
        return self.context(workspace,item_id) or (_ for _ in ()).throw(RuntimeError('context readback failed'))

    def add_proposal(self, workspace: str, row: dict[str,Any]) -> dict[str,Any]:
        self._postgres.execute(f'INSERT INTO {self.proposals}(id,context_id,base_version,title,proposed_content,provenance,created_by) VALUES (%(id)s,%(context_id)s,%(base_version)s,%(title)s,%(proposed_content)s,%(provenance)s,%(actor)s)',{**row,'proposed_content':Jsonb(row['proposed_content']),'provenance':Jsonb(row['provenance'])})
        return self._one(f'SELECT p.*,c.workspace_key,c.item_id FROM {self.proposals} p JOIN {self.contexts} c ON c.id=p.context_id WHERE p.id=%(id)s AND c.workspace_key=%(workspace)s',{'id':row['id'],'workspace':workspace}) or (_ for _ in ()).throw(RuntimeError('proposal readback failed'))

    def resolve_proposal(self, workspace: str, proposal_id: str, expected: int, accepted: bool, reason: str | None, version_id: str | None, actor: str) -> dict[str,Any]:
        with self._postgres.transaction() as c:
            proposal=c.execute(f'SELECT p.*,ctx.id context_id,ctx.item_id,ctx.version,ctx.current_version_id FROM {self.proposals} p JOIN {self.contexts} ctx ON ctx.id=p.context_id WHERE p.id=%s AND ctx.workspace_key=%s FOR UPDATE',(proposal_id,workspace)).fetchone()
            if proposal is None: raise KeyError(proposal_id)
            if proposal['status']!='open' or proposal['version'] != expected or proposal['base_version'] != expected: raise ConcurrentUpdateError('上下文已更新或提案已处理')
            if accepted:
                c.execute(f"INSERT INTO {self.versions}(id,context_id,revision_no,status,content,provenance,proposal_id,accepted_by,accepted_at,created_by) VALUES (%s,%s,%s,'accepted',%s,%s,%s,%s,now(),%s)",(version_id,proposal['context_id'],expected+1,Jsonb(proposal['proposed_content']),Jsonb(proposal['provenance']),proposal_id,actor,actor))
                c.execute(f'UPDATE {self.contexts} SET current_version_id=%s,version=version+1,updated_at=now() WHERE id=%s',(version_id,proposal['context_id']))
            c.execute(f"UPDATE {self.proposals} SET status=%s,reason=%s,resolved_by=%s,resolved_at=now() WHERE id=%s",('accepted' if accepted else 'rejected',reason,actor,proposal_id))
        return self.context(workspace,proposal['item_id']) or (_ for _ in ()).throw(RuntimeError('context readback failed'))

    def context_history(self, workspace: str, item_id: str) -> list[dict[str,Any]]:
        rows=self._postgres.fetch_all(f'SELECT v.* FROM {self.versions} v JOIN {self.contexts} c ON c.id=v.context_id WHERE c.workspace_key=%(workspace)s AND c.item_id=%(item)s ORDER BY v.revision_no DESC',{'workspace':workspace,'item':item_id})
        return [self._camel(r) for r in rows]

    def list_proposals(self, workspace: str, item_id: str) -> list[dict[str, Any]]:
        rows=self._postgres.fetch_all(f'SELECT p.* FROM {self.proposals} p JOIN {self.contexts} c ON c.id=p.context_id WHERE c.workspace_key=%(workspace)s AND c.item_id=%(item)s ORDER BY p.created_at DESC', {'workspace':workspace,'item':item_id})
        return [self._camel(r) for r in rows]

    def item_ids_with_open_proposals(self, workspace: str) -> set[str]:
        rows=self._postgres.fetch_all(f"SELECT c.item_id FROM {self.proposals} p JOIN {self.contexts} c ON c.id=p.context_id WHERE c.workspace_key=%(workspace)s AND p.status='open'", {'workspace':workspace})
        return {str(row['item_id']) for row in rows}

    def add_evidence(self, workspace:str,row:dict[str,Any]) -> dict[str,Any]:
        self._postgres.execute(f'INSERT INTO {self.evidence}(id,workspace_key,item_id,artifact_ref,artifact_version,environment_ref,summary,run_id,payload,created_by) VALUES (%(id)s,%(workspace)s,%(item_id)s,%(artifact_ref)s,%(artifact_version)s,%(environment_ref)s,%(summary)s,%(run_id)s,%(payload)s,%(actor)s)',{**row,'workspace':workspace,'payload':Jsonb(row.get('payload',{}))})
        return self._one(f'SELECT * FROM {self.evidence} WHERE id=%(id)s AND workspace_key=%(workspace)s',{'id':row['id'],'workspace':workspace}) or (_ for _ in ()).throw(RuntimeError('evidence readback failed'))

    def run_identity(self, workspace: str, run_id: str) -> dict[str, Any] | None:
        """A run is evidence only when its persisted owner matches this evidence scope."""
        return self._one(
            f'SELECT id, workspace, item_id FROM {self.runs} WHERE workspace=%(workspace)s AND id=%(id)s',
            {'workspace': workspace, 'id': run_id},
        )

    def list_evidence(self,workspace:str,item_id:str)->list[dict[str,Any]]:
        return [self._camel(r) for r in self._postgres.fetch_all(f'SELECT * FROM {self.evidence} WHERE workspace_key=%(workspace)s AND item_id=%(item)s ORDER BY created_at DESC',{'workspace':workspace,'item':item_id})]

    def review_evidence(self,workspace:str,evidence_id:str,status:str,reason:str|None,actor:str)->dict[str,Any]:
        count=self._postgres.execute(f'UPDATE {self.evidence} SET status=%(status)s,reviewed_by=%(actor)s,reviewed_at=now(),review_reason=%(reason)s WHERE id=%(id)s AND workspace_key=%(workspace)s',{'status':status,'actor':actor,'reason':reason,'id':evidence_id,'workspace':workspace})
        if count!=1: raise KeyError(evidence_id)
        return self._one(f'SELECT * FROM {self.evidence} WHERE id=%(id)s AND workspace_key=%(workspace)s',{'id':evidence_id,'workspace':workspace}) or (_ for _ in ()).throw(RuntimeError('evidence readback failed'))

    def append_activity(self,workspace:str,item_id:str,row:dict[str,Any])->dict[str,Any]:
        self._postgres.execute(f'INSERT INTO {self.activities}(id,workspace_key,item_id,kind,body,payload,actor_id) VALUES (%(id)s,%(workspace)s,%(item)s,%(kind)s,%(body)s,%(payload)s,%(actor)s)',{**row,'workspace':workspace,'item':item_id,'payload':Jsonb(row.get('payload',{}))})
        return self._one(f'SELECT * FROM {self.activities} WHERE id=%(id)s',{'id':row['id']}) or (_ for _ in ()).throw(RuntimeError('activity readback failed'))

    def list_activities(self,workspace:str,item_id:str)->list[dict[str,Any]]:
        return [self._camel(r) for r in self._postgres.fetch_all(f'SELECT * FROM {self.activities} WHERE workspace_key=%(workspace)s AND item_id=%(item)s ORDER BY created_at DESC',{'workspace':workspace,'item':item_id})]

    def save_preference(self,workspace:str,key:str,payload:dict[str,Any],expected:int|None,actor:str)->dict[str,Any]:
        existing=self._one(f'SELECT workspace_key,preference_key,payload,version,updated_by,updated_at FROM {self.preferences} WHERE workspace_key=%(workspace)s AND preference_key=%(key)s',{'workspace':workspace,'key':key})
        if existing is None:
            if expected is not None: raise ConcurrentUpdateError('偏好尚不存在')
            self._postgres.execute(f'INSERT INTO {self.preferences}(workspace_key,preference_key,payload,updated_by) VALUES (%s,%s,%s,%s)',(workspace,key,Jsonb(payload),actor))
        else:
            if expected != existing['version']: raise ConcurrentUpdateError('偏好已被其他人更新')
            self._postgres.execute(f'UPDATE {self.preferences} SET payload=%s,version=version+1,updated_by=%s,updated_at=now() WHERE workspace_key=%s AND preference_key=%s',(Jsonb(payload),actor,workspace,key))
        return self._one(f'SELECT workspace_key,preference_key,payload,version,updated_by,updated_at FROM {self.preferences} WHERE workspace_key=%(workspace)s AND preference_key=%(key)s',{'workspace':workspace,'key':key}) or (_ for _ in ()).throw(RuntimeError('pref readback failed'))

    def meeting(self,workspace:str)->dict[str,Any]|None:
        return self._one(f'SELECT id,workspace_key,config,version,updated_by,updated_at FROM {self.meetings} WHERE workspace_key=%(workspace)s',{'workspace':workspace})

    def save_meeting(self,workspace:str,row:dict[str,Any],expected:int|None,actor:str)->dict[str,Any]:
        current=self.meeting(workspace)
        if current is None:
            if expected is not None: raise ConcurrentUpdateError('会议配置尚不存在')
            self._postgres.execute(f'INSERT INTO {self.meetings}(id,workspace_key,config,updated_by) VALUES (%s,%s,%s,%s)',(row['id'],workspace,Jsonb(row['config']),actor))
        else:
            if expected != current['version']: raise ConcurrentUpdateError('会议配置已被其他人更新')
            self._postgres.execute(f'UPDATE {self.meetings} SET config=%s,version=version+1,updated_by=%s,updated_at=now() WHERE id=%s',(Jsonb(row['config']),actor,current['id']))
        return self.meeting(workspace) or (_ for _ in ()).throw(RuntimeError('meeting readback failed'))

    def freeze_meeting(self,workspace:str,snapshot_id:str,actor:str,snapshot:dict[str,Any])->dict[str,Any]:
        meeting=self.meeting(workspace)
        if meeting is None: raise KeyError('meeting')
        self._postgres.execute(f'INSERT INTO {self.snapshots}(id,meeting_id,meeting_version,snapshot,created_by) VALUES (%s,%s,%s,%s,%s)',(snapshot_id,meeting['id'],meeting['version'],Jsonb(snapshot),actor))
        return self._one(f'SELECT * FROM {self.snapshots} WHERE id=%(id)s',{'id':snapshot_id}) or (_ for _ in ()).throw(RuntimeError('snapshot readback failed'))

    def meeting_snapshot(self, workspace: str, snapshot_id: str) -> dict[str, Any] | None:
        return self._one(f'SELECT s.* FROM {self.snapshots} s JOIN {self.meetings} m ON m.id=s.meeting_id WHERE s.id=%(id)s AND m.workspace_key=%(workspace)s', {'id':snapshot_id, 'workspace':workspace})

    def add_meeting_note(self,workspace:str,row:dict[str,Any])->dict[str,Any]:
        meeting=self.meeting(workspace)
        if meeting is None: raise KeyError('meeting')
        self._postgres.execute(f'INSERT INTO {self.notes}(id,meeting_id,item_id,body,snapshot_id,created_by) VALUES (%s,%s,%s,%s,%s,%s)',(row['id'],meeting['id'],row['item_id'],row['body'],row.get('snapshot_id'),row['actor']))
        return self._one(f'SELECT n.*,m.workspace_key FROM {self.notes} n JOIN {self.meetings} m ON m.id=n.meeting_id WHERE n.id=%(id)s AND m.workspace_key=%(workspace)s',{'id':row['id'],'workspace':workspace}) or (_ for _ in ()).throw(RuntimeError('note readback failed'))

    def meeting_snapshot_notes(self, workspace: str, snapshot_id: str) -> list[dict[str, Any]]:
        rows=self._postgres.fetch_all(f'SELECT n.* FROM {self.notes} n JOIN {self.meetings} m ON m.id=n.meeting_id WHERE m.workspace_key=%(workspace)s AND n.snapshot_id=%(snapshot)s ORDER BY n.created_at', {'workspace':workspace,'snapshot':snapshot_id})
        return [self._camel(row) for row in rows]

    def state(self,workspace:str)->dict[str,Any]:
        items,_=self.list_items(workspace,limit=None); entities=self.list_entities(workspace); meeting=self.meeting(workspace)
        prefs=[self._camel(r) for r in self._postgres.fetch_all(f'SELECT workspace_key,preference_key,payload,version,updated_by,updated_at FROM {self.preferences} WHERE workspace_key=%(workspace)s',{'workspace':workspace})]
        notes=[self._camel(r) for r in self._postgres.fetch_all(f'SELECT n.* FROM {self.notes} n JOIN {self.meetings} m ON m.id=n.meeting_id WHERE m.workspace_key=%(workspace)s ORDER BY n.created_at DESC',{'workspace':workspace})]
        return {'workspace':workspace,'items':items,'ideas':[x for x in entities if x['entityType']=='idea'],'topics':[x for x in entities if x['entityType']=='topic'],'domains':[x for x in entities if x['entityType']=='domain'],'resources':[x for x in entities if x['entityType']=='resource'],'artifacts':[x for x in entities if x['entityType']=='artifact'],'improvements':[x for x in entities if x['entityType']=='improvement'],'relations':self.list_relations(workspace),'meeting':meeting,'meetingNotes':notes,'preferences':prefs}
