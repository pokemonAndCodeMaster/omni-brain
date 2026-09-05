from __future__ import annotations

from copy import deepcopy

import pytest

from src.gongzuo.repository import ConcurrentUpdateError, GongzuoRepository
from src.gongzuo.service import GongzuoService


class MemoryRepository:
    def __init__(self) -> None:
        self.items: dict[tuple[str, str], dict] = {}
        self.entities: dict[tuple[str, str], dict] = {}
        self.evidence: dict[tuple[str, str], list[dict]] = {}
        self.contexts: dict[tuple[str, str], dict] = {}
        self.relation_rows: list[dict] = []
        self.snapshots: list[dict] = []
        self.meeting_row: dict | None = None
        self.state_rows: dict = {'items': [], 'topics': [], 'relations': [], 'meeting': None, 'meetingNotes': []}

    def create_item(self, ws: str, row: dict) -> dict:
        value = {'id': row['id'], 'workspace': ws, 'itemType': row['item_type'], 'title': row['title'], 'status': row['status'], 'payload': row['payload'], 'version': 1}
        self.items[ws, row['id']] = value; self.state_rows['items'].append(value); return value

    def get_item(self, ws: str, item_id: str) -> dict | None: return self.items.get((ws, item_id))

    def update_item(self, ws: str, item_id: str, expected: int, changes: dict, actor: str) -> dict:
        item = self.get_item(ws, item_id)
        if not item or item['version'] != expected: raise ConcurrentUpdateError('事项不存在或已被其他人更新')
        item.update(changes); item['version'] += 1; return item

    def list_items(self, ws: str, **_: object) -> tuple[list[dict], int]:
        rows=[value for (workspace,_),value in self.items.items() if workspace == ws]; return rows, len(rows)

    def create_entity(self, ws: str, row: dict) -> dict:
        value={'id':row['id'],'workspace':ws,'entityType':row['entity_type'],'title':row['title'],'payload':row['payload'],'version':1}; self.entities[ws,row['id']]=value; return value

    def get_entity(self, ws: str, entity_id: str) -> dict | None: return self.entities.get((ws,entity_id))

    def create_relation(self, ws: str, row: dict) -> dict: return {'workspace':ws, **row}

    def list_relations(self, ws: str, item_id: str | None = None) -> list[dict]:
        return [row for row in self.relation_rows if item_id is None or row['fromId'] == item_id or row['toId'] == item_id]

    def create_context(self, ws: str, context_id: str, version_id: str, item_id: str, content: dict, provenance: list, actor: str) -> dict:
        result={'id':context_id,'itemId':item_id,'currentVersionId':version_id,'version':1,'revisionNo':1,'content':deepcopy(content),'provenance':deepcopy(provenance),'acceptedBy':actor}; self.contexts[ws,item_id]=result; return result

    def context(self, ws: str, item_id: str) -> dict | None: return self.contexts.get((ws,item_id))

    def add_evidence(self, ws: str, row: dict) -> dict:
        value={'id':row['id'],'status':'submitted', **row}; self.evidence.setdefault((ws,row['item_id']),[]).append(value); return value

    def list_evidence(self, ws: str, item_id: str) -> list[dict]: return self.evidence.get((ws,item_id),[])

    def run_identity(self, ws: str, run_id: str) -> dict | None:
        return {'id': run_id, 'workspace': ws, 'itemId': 'item-run'} if run_id == 'owned-run' else None

    def review_evidence(self, ws: str, evidence_id: str, status: str, reason: str | None, actor: str) -> dict:
        for rows in self.evidence.values():
            for row in rows:
                if row['id'] == evidence_id: row['status']=status; return row
        raise KeyError(evidence_id)

    def append_activity(self, ws: str, item_id: str, row: dict) -> dict: return row

    def meeting(self, ws: str) -> dict | None: return self.meeting_row

    def save_meeting(self, ws: str, row: dict, expected: int | None, actor: str) -> dict:
        if self.meeting_row is None:
            if expected is not None: raise ConcurrentUpdateError('会议配置尚不存在')
            self.meeting_row={'id':row['id'],'workspace':ws,'config':deepcopy(row['config']),'version':1}
        else:
            if expected != self.meeting_row['version']: raise ConcurrentUpdateError('会议配置已被其他人更新')
            self.meeting_row['config']=deepcopy(row['config']); self.meeting_row['version']+=1
        self.state_rows['meeting']=self.meeting_row; return self.meeting_row

    def state(self, ws: str) -> dict: return deepcopy({**self.state_rows,'meeting':self.meeting_row})

    def freeze_meeting(self, ws: str, snapshot_id: str, actor: str, snapshot: dict) -> dict:
        result={'id':snapshot_id,'snapshot':deepcopy(snapshot)}; self.snapshots.append(result); return result

    def meeting_snapshot(self, ws: str, snapshot_id: str) -> dict | None:
        return next((snapshot for snapshot in self.snapshots if snapshot['id'] == snapshot_id), None)

    def meeting_snapshot_notes(self, ws: str, snapshot_id: str) -> list[dict]: return []

    def item_ids_with_open_proposals(self, ws: str) -> set[str]: return set()

    def add_meeting_note(self, ws: str, row: dict) -> dict: return {'id':row['id'], 'itemId':row['item_id'], 'body':row['body']}


def service() -> tuple[GongzuoService, MemoryRepository]:
    repo=MemoryRepository(); return GongzuoService(repo), repo  # type: ignore[arg-type]


def test_personal_and_team_items_are_isolated() -> None:
    app, _ = service()
    personal=app.create_item('personal',item_type='learning',title='Learn',status='open',payload={},actor_id='me')
    team=app.create_item('team',item_type='requirement',title='Ship',status='open',payload={},actor_id='admin')
    assert app.get_item('personal',personal['id'])['title'] == 'Learn'
    with pytest.raises(KeyError): app.get_item('personal',team['id'])


def test_create_completed_formal_item_cannot_bypass_acceptance() -> None:
    app, _ = service()
    with pytest.raises(ValueError, match='不能在创建时直接完成'):
        app.create_item('team',item_type='requirement',title='Bypass',status='completed',payload={},actor_id='a')
    with pytest.raises(ValueError, match='completionKind'):
        app.create_item('personal',item_type='learning',title='Light bypass',status='completed',payload={},actor_id='a')
    assert app.create_item('personal',item_type='learning',title='Light done',status='completed',payload={'completionKind':'self_checked'},actor_id='a')['status'] == 'completed'


class AtomicCreateConnection:
    def __init__(self) -> None: self.inserted: list[str] = []
    def __enter__(self) -> 'AtomicCreateConnection': return self
    def __exit__(self, exc_type: object, *_: object) -> bool:
        if exc_type: self.inserted.clear()
        return False
    def execute(self, statement: str, _: object = None) -> None:
        if 't_gongzuo_item' in statement: self.inserted.append('item')
        if 't_gongzuo_context' in statement: raise RuntimeError('context write failed')


class AtomicCreatePostgres:
    schema = 'manual_qc_lab'
    def __init__(self) -> None: self.connection = AtomicCreateConnection()
    def transaction(self) -> AtomicCreateConnection: return self.connection


def test_item_and_initial_context_roll_back_together() -> None:
    postgres=AtomicCreatePostgres(); repository=GongzuoRepository(postgres)  # type: ignore[arg-type]
    with pytest.raises(RuntimeError, match='context write failed'):
        repository.create_item('team', {'id':'item-1','item_type':'requirement','title':'Atomic','status':'open','payload':{},'actor':'a','context_id':'ctx-1','context_version_id':'ctxv-1','initial_context':{},'provenance':[]})
    assert postgres.connection.inserted == []


def test_item_lost_update_is_rejected() -> None:
    app, _ = service(); item=app.create_item('team',item_type='fix',title='Bug',status='open',payload={},actor_id='a')
    app.update_item('team',item['id'],version=1,title='Bug fixed',status=None,payload=None,actor_id='a')
    with pytest.raises(ConcurrentUpdateError): app.update_item('team',item['id'],version=1,title='stale',status=None,payload=None,actor_id='b')


def test_multi_topic_relations_are_not_collapsed() -> None:
    app, _ = service(); item=app.create_item('team',item_type='research',title='Q',status='open',payload={},actor_id='a')
    one=app.create_entity('team',entity_type='topic',title='T1',payload={},actor_id='a'); two=app.create_entity('team',entity_type='topic',title='T2',payload={},actor_id='a')
    first=app.create_relation('team',from_kind='item',from_id=item['id'],to_kind='entity',to_id=one['id'],relation_type='serves',actor_id='a')
    second=app.create_relation('team',from_kind='item',from_id=item['id'],to_kind='entity',to_id=two['id'],relation_type='serves',actor_id='a')
    assert {first['to_id'],second['to_id']} == {one['id'],two['id']}


def test_accepted_evidence_is_required_before_item_acceptance() -> None:
    app, _ = service(); item=app.create_item('team',item_type='requirement',title='Deliver',status='awaiting_acceptance',payload={},actor_id='a')
    with pytest.raises(ValueError,match='已接受'): app.accept_item('team',item['id'],version=1,actor_id='a')
    evidence=app.add_evidence('team',item['id'],artifact_ref='repo://x',artifact_version='abc123',environment_ref='local://test',summary='ok',run_id=None,payload={},actor_id='a')
    with pytest.raises(ValueError,match='已接受'): app.accept_item('team',item['id'],version=1,actor_id='a')
    app.review_evidence('team',evidence['id'],status='accepted',reason='reviewed',actor_id='a')
    assert app.accept_item('team',item['id'],version=1,actor_id='a')['status'] == 'completed'


def test_evidence_run_must_belong_to_its_workspace_and_item() -> None:
    app, _ = service(); item=app.create_item('team',item_type='requirement',title='Deliver',status='open',payload={},actor_id='a')
    with pytest.raises(ValueError, match='不属于当前工作区和事项'):
        app.add_evidence('team',item['id'],artifact_ref='repo://x',artifact_version='1',environment_ref='local://x',summary=None,run_id='other-workspace-run',payload={},actor_id='a')


def test_frozen_meeting_snapshot_does_not_follow_later_item_edits() -> None:
    app, _ = service(); item=app.create_item('team',item_type='personal',title='Before',status='open',payload={},actor_id='a')
    app.save_meeting('team',config={'title':'Weekly','sections':[{'key':'decisions','title':'Decisions','enabled':True,'mode':'generic'}]},version=None,actor_id='a')
    frozen=app.freeze_meeting('team',actor_id='a')
    app.update_item('team',item['id'],version=1,title='After',status=None,payload=None,actor_id='a')
    assert frozen['snapshot']['projection']['sections'][0]['entries'][0]['values']['title'] == 'Before'
    assert 'Before' in app.export_meeting_markdown('team', frozen['id'])


def test_meeting_section_keys_are_deduplicated() -> None:
    app, _ = service()
    with pytest.raises(ValueError,match='唯一'):
        app.save_meeting('team',config={'sections':[{'key':'same'},{'key':'same'}]},version=None,actor_id='a')


def test_meeting_projection_collapses_repeat_progress_but_preserves_section_decision() -> None:
    app, _ = service()
    item=app.create_item('team',item_type='research',title='Shared',status='in_progress',payload={'decisions':[{'sectionKey':'second','body':'Needs a distinct decision'}]},actor_id='a')
    app.save_meeting('team',config={'sections':[{'key':'first','title':'First','enabled':True},{'key':'second','title':'Second','enabled':True}]},version=None,actor_id='a')
    projection=app.meeting_projection('team')
    assert projection['sections'][0]['entries'][0]['presentation'] == 'full'
    repeated=projection['sections'][1]['entries'][0]
    assert repeated['presentation'] == 'decision'
    assert repeated['decisions'][0]['body'] == 'Needs a distinct decision'


def test_default_topic_projection_exports_topic_and_shared_item_decisions() -> None:
    app, repo = service()
    item=app.create_item('team',item_type='research',title='Shared',status='in_progress',payload={'decisions':[{'topicId':'topic-1','body':'Shared decision'}]},actor_id='a')
    repo.state_rows['topics']=[{'id':'topic-1','title':'Topic','payload':{'goal':'Goal','decisions':[{'body':'Topic decision'}]}}]
    repo.state_rows['relations']=[{'fromKind':'item','fromId':item['id'],'toKind':'entity','toId':'topic-1'}]
    app.save_meeting('team',config={'sections':[{'key':'topics','title':'Topics','enabled':True}]},version=None,actor_id='a')
    projection=app.meeting_projection('team')
    assert [d['body'] for d in projection['sections'][0]['entries'][0]['decisions']] == ['Topic decision','Shared decision']
    assert 'Topic decision' in app.export_meeting_markdown('team')


def test_default_deliveries_skip_repeat_progress_but_keep_its_decision() -> None:
    app, _ = service()
    item=app.create_item('team',item_type='research',title='Delivery',status='in_progress',payload={'decisions':[{'sectionKey':'deliveries','body':'Delivery decision'}]},actor_id='a')
    app.save_meeting('team',config={'sections':[{'key':'decisions','title':'Decisions','enabled':True,'mode':'generic'},{'key':'deliveries','title':'Deliveries','enabled':True}]},version=None,actor_id='a')
    projection=app.meeting_projection('team')
    entry=projection['sections'][1]['entries'][0]
    assert entry['presentation'] == 'decision' and entry['values'] == {'title':'Delivery','status':'in_progress'}
    app.update_item('team',item['id'],version=1,title=None,status=None,payload={'decisions':[]},actor_id='a')
    assert app.meeting_projection('team')['sections'][1]['entries'] == []


def test_export_preserves_selected_payload_fields_sources_and_full_decisions() -> None:
    app, _ = service()
    item=app.create_item('team',item_type='research',title='Exported',status='blocked',payload={'goal':'Goal','owner':'Owner','due':'2026-09-06','update':'Latest','decisions':[{'body':'Decision text'}]},actor_id='a')
    app.save_meeting('team',config={'sections':[{'key':'decisions','title':'Decisions','enabled':True,'mode':'generic','fields':['title','payload'],'payloadFields':['goal','owner','due','update']}]},version=None,actor_id='a')
    exported=app.export_meeting_markdown('team')
    for text in (item['id'],'目标：Goal','责任人：Owner','目标日期：2026-09-06','最新变化：Latest','决定：Decision text'):
        assert text in exported


def test_stale_context_proposal_is_rejected_before_write() -> None:
    app, repo = service(); item=app.create_item('team',item_type='research',title='Context',status='open',payload={},actor_id='a')
    app.create_context('team',item['id'],content={'goal':'v1'},provenance=[],actor_id='a')
    repo.contexts['team',item['id']]['version'] = 2
    with pytest.raises(ConcurrentUpdateError,match='上下文已更新'):
        app.propose_context('team',item['id'],base_version=1,title='stale',proposed_content={'goal':'v2'},provenance=[],actor_id='b')


def test_child_run_snapshot_inherits_parent_context_and_keeps_local_focus() -> None:
    app, repo = service()
    parent=app.create_item('team',item_type='requirement',title='Parent',status='open',payload={},actor_id='a')
    child=app.create_item('team',item_type='research',title='Child',status='open',payload={'parentId':parent['id']},actor_id='a')
    app.create_context('team',parent['id'],content={'goal':'parent v1'},provenance=[],actor_id='a')
    app.create_context('team',child['id'],content={'goal':'child focus'},provenance=[],actor_id='a')
    repo.relation_rows.append({'fromKind':'item','fromId':child['id'],'toKind':'item','toId':parent['id'],'relationType':'contributes_to'})
    snapshot=app.current_context_snapshot('team',child['id'])
    assert snapshot['content']['goal'] == 'parent v1'
    assert snapshot['focus']['goal'] == 'child focus'
    assert snapshot['inheritancePath'] == [child['id'],parent['id']]


def test_context_inheritance_rejects_multiple_parents_and_cycles() -> None:
    app, repo = service()
    one=app.create_item('team',item_type='research',title='One',status='open',payload={},actor_id='a'); two=app.create_item('team',item_type='research',title='Two',status='open',payload={},actor_id='a'); three=app.create_item('team',item_type='research',title='Three',status='open',payload={},actor_id='a')
    for item in (one,two,three): app.create_context('team',item['id'],content={'goal':item['title']},provenance=[],actor_id='a')
    repo.relation_rows.extend([{'fromKind':'item','fromId':one['id'],'toKind':'item','toId':two['id'],'relationType':'part_of'},{'fromKind':'item','fromId':one['id'],'toKind':'item','toId':three['id'],'relationType':'part_of'}])
    with pytest.raises(ValueError,match='多个父级'): app.current_context_snapshot('team',one['id'])
    repo.relation_rows=[{'fromKind':'item','fromId':one['id'],'toKind':'item','toId':two['id'],'relationType':'part_of'},{'fromKind':'item','fromId':two['id'],'toKind':'item','toId':one['id'],'relationType':'part_of'}]
    with pytest.raises(ValueError,match='循环'): app.current_context_snapshot('team',one['id'])
