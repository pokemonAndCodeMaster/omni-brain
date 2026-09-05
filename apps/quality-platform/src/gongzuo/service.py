from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from .repository import ConcurrentUpdateError, GongzuoRepository


VALID_WORKSPACES = {'personal', 'team'}


def _json_snapshot(value: Any) -> Any:
    """JSONB accepts only values that can survive without a live DB row object."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_snapshot(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_json_snapshot(child) for child in value]
    return value


class GongzuoService:
    def __init__(self, repository: GongzuoRepository) -> None:
        self.repository = repository

    @staticmethod
    def _id(prefix: str) -> str:
        return f'{prefix}-{uuid4().hex[:16]}'

    @staticmethod
    def _workspace(workspace: str) -> str:
        if workspace not in VALID_WORKSPACES:
            raise ValueError('工作区必须是 personal 或 team')
        return workspace

    def get_state(self, workspace: str) -> dict[str, Any]:
        return self.repository.state(self._workspace(workspace))

    def create_item(self, workspace: str, *, item_type: str, title: str, status: str, payload: dict[str, Any], actor_id: str, initial_context: dict[str, Any] | None = None, provenance: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        workspace=self._workspace(workspace)
        if status == 'completed':
            if item_type not in {'personal','hobby','game','learning'}:
                raise ValueError('正式事项不能在创建时直接完成，必须经过验收')
            if not payload.get('completionKind'):
                raise ValueError('轻量事项创建为完成时必须写明 completionKind，不能冒充验收')
        if payload.get('parentId'):
            if self.repository.get_item(workspace, str(payload['parentId'])) is None:
                raise ValueError('payload.parentId 必须引用同一工作区已有事项；正式继承仍需建立 contributes_to 或 part_of 关系')
        # This is the user's submitted working intent, not inferred policy or a fabricated source.
        context = initial_context if initial_context is not None else {'goal': payload.get('goal', title.strip()), 'scope': payload.get('scope', '')}
        return self.repository.create_item(workspace, {'id':self._id('item'),'item_type':item_type,'title':title.strip(),'status':status,'payload':payload,'actor':actor_id,'context_id':self._id('context'),'context_version_id':self._id('ctxv'),'initial_context':context,'provenance':provenance or []})

    def list_items(self, workspace: str, **filters: Any) -> tuple[list[dict[str,Any]],int]:
        return self.repository.list_items(self._workspace(workspace), **filters)

    def get_item(self, workspace: str, item_id: str) -> dict[str, Any]:
        item=self.repository.get_item(self._workspace(workspace),item_id)
        if item is None: raise KeyError(item_id)
        return item

    def update_item(self, workspace: str, item_id: str, *, version:int, actor_id:str, **changes:Any)->dict[str,Any]:
        item=self.get_item(workspace,item_id)
        if changes.get('status') == 'completed':
            payload = changes.get('payload') if changes.get('payload') is not None else item['payload']
            light = item['itemType'] in {'personal','hobby','game','learning'}
            if not light:
                raise ValueError('正式事项只能通过验收动作完成')
            if not payload.get('completionKind'):
                raise ValueError('轻量事项完成时必须写明 completionKind，不能冒充验收')
        return self.repository.update_item(self._workspace(workspace),item_id,version,{k:v for k,v in changes.items() if v is not None},actor_id)

    def create_entity(self, workspace:str, *, entity_type:str,title:str,payload:dict[str,Any],actor_id:str)->dict[str,Any]:
        return self.repository.create_entity(self._workspace(workspace),{'id':self._id(entity_type),'entity_type':entity_type,'title':title.strip(),'payload':payload,'actor':actor_id})

    def update_entity(self, workspace:str, entity_id:str, *, version:int, title:str|None, payload:dict[str,Any]|None, actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace)
        if self.repository.get_entity(workspace,entity_id) is None: raise KeyError(entity_id)
        return self.repository.update_entity(workspace,entity_id,version,{k:v for k,v in {'title':title,'payload':payload}.items() if v is not None},actor_id)

    def create_relation(self,workspace:str,*,actor_id:str,**relation:Any)->dict[str,Any]:
        workspace=self._workspace(workspace)
        for kind, identity in ((relation['from_kind'],relation['from_id']),(relation['to_kind'],relation['to_id'])):
            exists=self.repository.get_item(workspace,identity) if kind=='item' else self.repository.get_entity(workspace,identity)
            if not exists: raise KeyError(identity)
        if relation['from_kind']==relation['to_kind'] and relation['from_id']==relation['to_id']:
            raise ValueError('关系不能指向自身')
        if relation['relation_type'] in {'part_of','contributes_to'} and (relation['from_kind'] != 'item' or relation['to_kind'] != 'item'):
            raise ValueError('part_of 与 contributes_to 必须从子事项指向父事项')
        return self.repository.create_relation(workspace,{'id':self._id('rel'),**relation,'actor':actor_id})

    def delete_relation(self, workspace: str, relation_id: str) -> None:
        self.repository.delete_relation(self._workspace(workspace), relation_id)

    def add_discussion(self,workspace:str,*,item_id:str|None=None,entity_id:str|None=None,body:str,anchor:str|None,payload:dict[str,Any],actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace)
        if bool(item_id) == bool(entity_id): raise ValueError('讨论必须且只能关联一个事项或实体')
        if item_id: self.get_item(workspace,item_id)
        elif self.repository.get_entity(workspace,str(entity_id)) is None: raise KeyError(str(entity_id))
        return self.repository.add_discussion(workspace,{'id':self._id('discussion'),'item_id':item_id,'entity_id':entity_id,'body':body.strip(),'anchor':anchor,'payload':payload,'actor':actor_id})

    def create_context(self,workspace:str,item_id:str,*,content:dict[str,Any],provenance:list[dict[str,Any]],actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); self.get_item(workspace,item_id)
        if self.repository.context(workspace,item_id): raise ValueError('事项已有共享上下文')
        return self.repository.create_context(workspace,self._id('context'),self._id('ctxv'),item_id,content,provenance,actor_id)

    def current_context_snapshot(self,workspace:str,item_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); own_context=self.repository.context(workspace,item_id)
        chain=[item_id]; current=item_id
        while True:
            parents=[relation['toId'] for relation in self.repository.list_relations(workspace,current) if relation['fromKind']=='item' and relation['fromId']==current and relation['toKind']=='item' and relation['relationType'] in {'part_of','contributes_to'}]
            if len(parents) > 1: raise ValueError('事项有多个父级上下文，必须先明确唯一父级关系')
            if not parents: break
            parent=parents[0]
            if parent in chain: raise ValueError('事项上下文继承关系存在循环')
            # list_relations is workspace-scoped; this explicit read also rejects stale/cross-scope records.
            if self.repository.get_item(workspace,parent) is None: raise ValueError('父事项不在当前工作区')
            chain.append(parent); current=parent
        context=self.repository.context(workspace,chain[-1]) if len(chain) > 1 else own_context
        if context is None or not context.get('currentVersionId'): raise ValueError('事项没有已接受的共享上下文')
        result={'itemId':item_id,'contextId':context['id'],'versionId':context['currentVersionId'],'revisionNo':context['revisionNo'],'content':context.get('content',{}),'sources':context.get('provenance',[]),'acceptedAt':context.get('acceptedAt'),'acceptedBy':context.get('acceptedBy')}
        if len(chain) > 1:
            result['inheritedFromItemId']=chain[-1]
            result['inheritancePath']=chain
            result['focus']=own_context.get('content',{}) if own_context else {}
            result['contextRefs']=[{'itemId':node,'contextId':(self.repository.context(workspace,node) or {}).get('id'),'versionId':(self.repository.context(workspace,node) or {}).get('currentVersionId')} for node in chain]
        return result

    def propose_context(self,workspace:str,item_id:str,*,base_version:int,title:str,proposed_content:dict[str,Any],provenance:list[dict[str,Any]],actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); context=self.repository.context(workspace,item_id)
        if context is None: raise KeyError(item_id)
        if context['version'] != base_version: raise ConcurrentUpdateError('上下文已更新，请刷新后再提交候选')
        return self.repository.add_proposal(workspace,{'id':self._id('ctxp'),'context_id':context['id'],'base_version':base_version,'title':title.strip(),'proposed_content':proposed_content,'provenance':provenance,'actor':actor_id})

    def resolve_context_proposal(self,workspace:str,proposal_id:str,*,version:int,accepted:bool,reason:str|None,actor_id:str)->dict[str,Any]:
        return self.repository.resolve_proposal(self._workspace(workspace),proposal_id,version,accepted,reason,self._id('ctxv') if accepted else None,actor_id)

    def context_history(self,workspace:str,item_id:str)->list[dict[str,Any]]:
        self.get_item(workspace,item_id); return self.repository.context_history(self._workspace(workspace),item_id)

    def add_evidence(self,workspace:str,item_id:str,*,artifact_ref:str,artifact_version:str,environment_ref:str,summary:str|None,run_id:str|None,payload:dict[str,Any],actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); self.get_item(workspace,item_id)
        if run_id:
            run=self.repository.run_identity(workspace,run_id)
            if run is None or run['itemId'] != item_id:
                raise ValueError('Run 不存在，或不属于当前工作区和事项')
        return self.repository.add_evidence(workspace,{'id':self._id('evidence'),'item_id':item_id,'artifact_ref':artifact_ref.strip(),'artifact_version':artifact_version.strip(),'environment_ref':environment_ref.strip(),'summary':summary,'run_id':run_id,'payload':payload,'actor':actor_id})

    def add_run_evidence_link(self,workspace:str,item_id:str,*,run_id:str,artifact_ref:str,artifact_version:str,environment_ref:str,actor_id:str,summary:str|None=None)->dict[str,Any]:
        return self.add_evidence(workspace,item_id,artifact_ref=artifact_ref,artifact_version=artifact_version,environment_ref=environment_ref,summary=summary,run_id=run_id,payload={'provenance':'agent_run'},actor_id=actor_id)

    def review_evidence(self,workspace:str,evidence_id:str,*,status:str,reason:str|None,actor_id:str)->dict[str,Any]:
        return self.repository.review_evidence(self._workspace(workspace),evidence_id,status,reason,actor_id)

    def accept_item(self,workspace:str,item_id:str,*,version:int,actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); item=self.get_item(workspace,item_id)
        if item['version'] != version: raise ConcurrentUpdateError('事项已更新，请刷新后再验收')
        evidence=self.repository.list_evidence(workspace,item_id)
        if not evidence or not any(row['status']=='accepted' for row in evidence):
            raise ValueError('至少需要一条已接受且带产物版本、环境引用的证据才能验收')
        return self.repository.update_item(workspace,item_id,version,{'status':'completed'},actor_id)

    def append_activity(self,workspace:str,item_id:str,*,kind:str,body:str,actor_id:str,payload:dict[str,Any]|None=None)->dict[str,Any]:
        workspace=self._workspace(workspace); self.get_item(workspace,item_id)
        return self.repository.append_activity(workspace,item_id,{'id':self._id('activity'),'kind':kind,'body':body,'payload':payload or {},'actor':actor_id})

    def save_preference(self,workspace:str,key:str,*,payload:dict[str,Any],version:int|None,actor_id:str)->dict[str,Any]:
        return self.repository.save_preference(self._workspace(workspace),key,payload,version,actor_id)

    def save_meeting(self,workspace:str,*,config:dict[str,Any],version:int|None,actor_id:str)->dict[str,Any]:
        sections=config.get('sections',[])
        keys=[section.get('key') for section in sections if isinstance(section,dict)]
        if len(keys)!=len(set(keys)) or any(not key for key in keys): raise ValueError('会议板块 key 必须非空且唯一')
        return self.repository.save_meeting(self._workspace(workspace),{'id':self._id('meeting'),'config':config},version,actor_id)

    def freeze_meeting(self,workspace:str,*,actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); meeting=self.repository.meeting(workspace)
        if meeting is None: raise KeyError('meeting')
        state=self.repository.state(workspace); projection=self.meeting_projection(workspace, state)
        # Frozen input is a database-owned JSON value, independent of later item edits.
        return self.repository.freeze_meeting(workspace,self._id('meeting-snapshot'),actor_id,_json_snapshot({'frozenAt':datetime.now().astimezone().isoformat(),'meetingConfig':meeting['config'],'projection':projection,'meetingNotes':state['meetingNotes']}))

    def add_meeting_note(self,workspace:str,*,item_id:str,body:str,snapshot_id:str|None=None,actor_id:str)->dict[str,Any]:
        workspace=self._workspace(workspace); self.get_item(workspace,item_id)
        if snapshot_id and self.repository.meeting_snapshot(workspace,snapshot_id) is None: raise KeyError(snapshot_id)
        note=self.repository.add_meeting_note(workspace,{'id':self._id('meeting-note'),'item_id':item_id,'body':body.strip(),'snapshot_id':snapshot_id,'actor':actor_id})
        self.append_activity(workspace,item_id,kind='meeting_note',body=body.strip(),actor_id=actor_id,payload={'meetingNoteId':note['id']})
        return note

    @staticmethod
    def _section_items(section: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        filters=section.get('filters',{}) if isinstance(section.get('filters',{}),dict) else {}
        wanted=set(filters.get('itemIds',[])); statuses=set(filters.get('statuses',[])); topic_ids=set(filters.get('topicIds',[])); owners=set(filters.get('owners',[])); domains=set(filters.get('domainIds',[])); types=set(filters.get('itemTypes',[]))
        topic_items={r['fromId'] for r in state['relations'] if r['fromKind']=='item' and r['toKind']=='entity' and r['toId'] in topic_ids}
        domain_items={r['fromId'] for r in state['relations'] if r['fromKind']=='item' and r['toKind']=='entity' and r['toId'] in domains}
        since=filters.get('updatedAfter'); until=filters.get('updatedBefore')
        result=[]
        for item in state['items']:
            if wanted and item['id'] not in wanted: continue
            if statuses and item['status'] not in statuses: continue
            if types and item['itemType'] not in types: continue
            if owners and item.get('payload',{}).get('owner') not in owners: continue
            if topic_ids and item['id'] not in topic_items: continue
            if domains and item['id'] not in domain_items: continue
            updated=str(item.get('updatedAt',''))
            if since and updated and updated < str(since): continue
            if until and updated and updated > str(until): continue
            result.append(item)
        return result

    def meeting_projection(self, workspace: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
        workspace=self._workspace(workspace); state=state or self.repository.state(workspace); meeting=state['meeting']
        if meeting is None: raise KeyError('meeting')
        seen:set[str]=set(); sections=[]; pending=self.repository.item_ids_with_open_proposals(workspace)
        for section in meeting['config'].get('sections',[]):
            if not section.get('enabled',True): continue
            key=section.get('key')
            if key == 'topics' and section.get('mode') != 'generic':
                filters=section.get('filters',{}) if isinstance(section.get('filters',{}),dict) else {}
                wanted=set(filters.get('topicIds',[]))
                entries=[]
                for topic in state['topics']:
                    if wanted and topic['id'] not in wanted: continue
                    related=[r['fromId'] for r in state['relations'] if r['fromKind']=='item' and r['toKind']=='entity' and r['toId']==topic['id']]
                    payload=topic.get('payload',{})
                    decisions=[d for d in payload.get('decisions',[]) if isinstance(d,dict)]
                    for related_id in related:
                        item=next((candidate for candidate in state['items'] if candidate['id']==related_id),None)
                        if item:
                            decisions.extend(d for d in item.get('payload',{}).get('decisions',[]) if isinstance(d,dict) and d.get('topicId')==topic['id'])
                    entries.append({'topicId':topic['id'],'presentation':'topic_summary','group':None,'decisions':decisions,'values':{'title':topic['title'],'goal':payload.get('goal',''),'gap':payload.get('gap',''),'owner':payload.get('owner',''),'relatedItems':related}})
                sections.append({'key':key,'title':section.get('title',key),'entries':entries}); continue
            entries=[]
            for item in self._section_items(section,state):
                payload=item.get('payload',{})
                if key == 'decisions' and section.get('mode') != 'generic':
                    has_open_decision=any(isinstance(d,dict) and d.get('status','open') != 'accepted' for d in payload.get('decisions',[]))
                    if not (payload.get('attention') or item['status']=='blocked' or item['id'] in pending or has_open_decision): continue
                if key == 'deliveries' and section.get('mode') != 'generic':
                    if item['status'] not in {'completed','awaiting_acceptance','in_progress'}: continue
                    days=(section.get('filters') or {}).get('recentDays',14)
                    updated=item.get('updatedAt')
                    if updated and isinstance(days,int):
                        timestamp=updated if isinstance(updated,datetime) else datetime.fromisoformat(str(updated).replace('Z','+00:00'))
                        if timestamp.tzinfo is None: timestamp=timestamp.replace(tzinfo=timezone.utc)
                        if timestamp < datetime.now(timezone.utc)-timedelta(days=days): continue
                decisions=[d for d in payload.get('decisions',[]) if isinstance(d,dict) and (d.get('sectionKey') in {None,key} or d.get('topicId') in set((section.get('filters') or {}).get('topicIds',[])))]
                already_seen=item['id'] in seen
                if key == 'deliveries' and section.get('mode') != 'generic' and already_seen and not decisions:
                    continue
                presentation='full' if not already_seen else ('decision' if decisions else 'summary')
                seen.add(item['id'])
                # Payload can be large and is not a presentation contract. Decisions are emitted separately.
                fields=section.get('fields') or ['title','status']
                values={field:(item.get(field) if field!='payload' else {key:payload[key] for key in (section.get('payloadFields') or payload.keys()) if key in payload}) for field in fields}
                entries.append({'itemId':item['id'],'presentation':presentation,'group':payload.get(section.get('groupBy',''),None) if section.get('groupBy') else None,'values':values,'decisions':decisions})
            sections.append({'key':key,'title':section.get('title',key),'entries':entries})
        return {'meetingId':meeting['id'],'meetingVersion':meeting['version'],'sections':sections}

    def export_meeting_markdown(self,workspace:str,snapshot_id:str|None=None)->str:
        workspace=self._workspace(workspace); state=self.repository.state(workspace); meeting=state['meeting']
        if meeting is None: raise KeyError('meeting')
        frozen = self.repository.meeting_snapshot(workspace,snapshot_id) if snapshot_id else None
        if snapshot_id and frozen is None: raise KeyError(snapshot_id)
        source = frozen['snapshot'] if frozen else {'meetingConfig':meeting['config'], 'projection':self.meeting_projection(workspace,state), 'meetingNotes':state['meetingNotes']}
        config = source['meetingConfig']; projection=source['projection']
        title=str(config.get('title','共作会议纪要'))
        lines=[f'# {title}','',f'> 导出时间：{datetime.now().astimezone().isoformat()}','']
        if frozen: lines += [f"> 冻结快照：{snapshot_id}", '']
        for section in projection['sections']:
            lines += [f"## {section['title']}",'']
            for entry in section['entries']:
                values=entry.get('values',{}); title=values.get('title') or entry.get('itemId') or entry.get('topicId','未命名条目')
                if entry['presentation'] == 'summary': lines += [f"- {title}（进展已在前文展开）",'']; continue
                lines += [f"### {title}",'']
                lines += [f"来源：{entry.get('itemId') or entry.get('topicId','未记录对象 ID')}",'']
                if entry.get('group') is not None: lines += [f"分组：{entry['group']}",'']
                for name,value in values.items():
                    if name == 'title': continue
                    if name == 'payload' and isinstance(value,dict):
                        labels={'goal':'目标','scope':'范围','owner':'责任人','due':'目标日期','update':'最新变化','latestChange':'最新变化'}
                        for payload_name,payload_value in value.items():
                            rendered=json.dumps(payload_value,ensure_ascii=False) if isinstance(payload_value,(dict,list)) else str(payload_value)
                            lines += [f"{labels.get(payload_name,payload_name)}：{rendered}",'']
                    elif name != 'payload': lines += [f'{name}：{value}','']
                for decision in entry.get('decisions',[]): lines += [f"决定：{decision.get('body',decision.get('title','未命名决定'))}",'']
        notes = self.repository.meeting_snapshot_notes(workspace,snapshot_id) if frozen else source['meetingNotes']
        if notes:
            lines += ['## 会中记录','']
            lines += [f"- {note['itemId']}: {note['body']}" for note in notes]
        return '\n'.join(lines).rstrip()+'\n'
