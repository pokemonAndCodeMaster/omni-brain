from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
import yaml

from .repository import GongzuoKnowledgeRepository


def digest(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class GongzuoKnowledgeService:
    """Git source reading and immutable, reviewed capability releases.

    Releases are overlays owned by this service; original source files remain the
    source revision referenced by the proposal. Neither raw material nor Git files
    are silently rewritten. The UI and every new Run resolve the same active release.
    """

    def __init__(self, repository: GongzuoKnowledgeRepository, roots: dict[str, Path | None], gongzuo_service: Any) -> None:
        self.repository=repository
        self.roots={key:value.resolve() if value else None for key,value in roots.items()}
        self.gongzuo_service=gongzuo_service
        self.run_reader: Callable[[str,str],dict[str,Any]] | None=None

    def root(self, workspace: str) -> Path:
        if workspace not in ('personal','team'): raise ValueError('未知工作区')
        root=self.roots.get(workspace)
        if root is None or not root.is_dir(): raise ValueError('此工作区尚未配置知识目录')
        return root

    def source_file(self, workspace: str, relative: str) -> Path:
        root=self.root(workspace)
        if not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
            raise ValueError('知识路径必须是目录内的相对路径')
        path=(root/relative).resolve()
        if not path.is_relative_to(root) or path.suffix.lower()!='.md' or not path.is_file(): raise KeyError(relative)
        if path.stat().st_size>2_000_000: raise ValueError('材料超过单页阅读上限，请打开原始文件')
        return path

    @staticmethod
    def title(content: str, fallback: str) -> str:
        match=re.search(r'^#\s+(.+)$',content,re.MULTILINE)
        return match.group(1).strip() if match else fallback

    def catalog(self, workspace: str, query: str='') -> dict[str,Any]:
        root=self.root(workspace)
        releases={r['sourcePath']:r for r in self.repository.list(workspace) if r['status']=='published' and r['target']=='knowledge'}
        entries=[]
        for file in sorted(root.rglob('*.md')):
            if not file.resolve().is_relative_to(root) or file.stat().st_size>2_000_000: continue
            relative=file.relative_to(root).as_posix()
            # Raw material is provenance, not silently mixed into published current knowledge.
            if any(part in {'raw','.git','.runtime','node_modules'} for part in file.relative_to(root).parts): continue
            source=file.read_text(encoding='utf-8')
            released=releases.get(relative)
            body=released['content'] if released else source
            title=self.title(body,file.stem)
            if query.casefold() not in f'{title}\n{relative}\n{body}'.casefold(): continue
            entries.append({'path':relative,'title':title,'version':digest(body),'sourceVersion':digest(source),
                            'source':'workspace-release' if released else 'git-file','releaseId':released['id'] if released else None,
                            'excerpt':re.sub(r'\s+',' ',body)[:180]})
        return {'items':entries,'total':len(entries),'sourceRootConfigured':True}

    def document(self, workspace: str, relative: str) -> dict[str,Any]:
        path=self.source_file(workspace,relative)
        source=path.read_text(encoding='utf-8')
        released=next((r for r in self.repository.list(workspace) if r['status']=='published' and r['target']=='knowledge' and r['sourcePath']==relative),None)
        content=released['content'] if released else source
        return {'path':relative,'title':self.title(content,path.stem),'content':content,'version':digest(content),
                'sourceVersion':digest(source),'source':'workspace-release' if released else 'git-file',
                'releaseId':released['id'] if released else None,'readOnly':True,
                'sourceChanged':bool(released and released.get('sourceRevision')!=digest(source))}

    def create(self, workspace: str, body: dict[str,Any], actor: str) -> dict[str,Any]:
        self.root(workspace)
        if body.get('sourceItemId'): self.gongzuo_service.get_item(workspace,body['sourceItemId'])
        if body.get('sourceEntityId') and not self.gongzuo_service.repository.get_entity(workspace,body['sourceEntityId']): raise KeyError(body['sourceEntityId'])
        source_revision=None
        if body['target']=='knowledge':
            if not body.get('sourcePath') or not body.get('baseVersion'): raise ValueError('知识修订需要来源路径与读取版本')
            if 'raw' in Path(body['sourcePath']).parts: raise ValueError('原始资料仅作为依据，不能修订发布')
            current=self.document(workspace,body['sourcePath'])
            if current['version']!=body['baseVersion']: raise ValueError('知识已经变化，请重新阅读后提出修订')
            source_revision=current['sourceVersion']
        elif body['target']=='skill':
            parts=body['content'].split('---',2)
            if len(parts)!=3 or parts[0].strip(): raise ValueError('Skill 需要带 name 和 description 的 SKILL.md frontmatter')
            try: metadata=yaml.safe_load(parts[1])
            except yaml.YAMLError as exc: raise ValueError('Skill frontmatter 不是有效 YAML') from exc
            if not isinstance(metadata,dict) or not isinstance(metadata.get('name'),str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',metadata['name']):
                raise ValueError('Skill name 需要小写字母、数字及短横线')
            if not isinstance(metadata.get('description'),str) or not metadata['description'].strip(): raise ValueError('Skill 缺少 description')
        row={'id':'cap-'+uuid4().hex[:16], 'sourceItemId':None,'sourceEntityId':None,'sourcePath':None,'baseVersion':None,**body,'sourceRevision':source_revision}
        row['version']=digest(row['content'])
        return self.repository.create(workspace,row,actor)

    def published_context(self, workspace: str, candidate_id: str | None=None) -> list[dict[str,Any]]:
        rows=[r for r in self.repository.list(workspace) if r['status']=='published']
        eligible=[]
        for row in rows:
            if row['target']=='knowledge':
                try:
                    current=digest(self.source_file(workspace,row['sourcePath']).read_text(encoding='utf-8'))
                except (KeyError,ValueError,OSError):
                    continue
                if current!=row.get('sourceRevision'):
                    continue
            eligible.append(row)
        rows=eligible
        candidate=self.repository.get(workspace,candidate_id) if candidate_id else None
        if candidate:
            if candidate['status'] not in ('candidate','verified'): raise ValueError('只能试验尚未发布的候选')
            rows=[r for r in rows if (r['target'],r.get('sourcePath') or r['title'])!=(candidate['target'],candidate.get('sourcePath') or candidate['title'])]
            rows.append(candidate)
        return [{key:r.get(key) for key in ('id','title','target','version','content','sourcePath','baseVersion','validationPlan','desiredBehavior')} |
                {'isCandidate':bool(candidate and r['id']==candidate['id'])} for r in rows]

    def verify(self, workspace: str, candidate_id: str, body: dict[str,Any], actor: str) -> dict[str,Any]:
        candidate=self.repository.get(workspace,candidate_id)
        self._check_verification(workspace,candidate,body)
        return self.repository.verify(workspace,{'id':'check-'+uuid4().hex[:16], 'candidateId':candidate_id,
            'candidateVersion':candidate['version'], **body},actor)

    def _check_verification(self, workspace: str, candidate: dict[str,Any], body: dict[str,Any]) -> None:
        if not self.run_reader: raise ValueError('执行服务尚未接入，无法验证')
        run=self.run_reader(workspace,body['runId'])
        state=run.get('status',run.get('state'))
        if body['result']=='accepted' and state!='succeeded': raise ValueError('接受验证需要实际成功结束的运行')
        if body['result']=='rejected' and state not in ('succeeded','failed','unavailable'): raise ValueError('需等待试验实际结束后记录验证判断')
        capabilities=run.get('capabilities',run.get('payload',{}).get('capabilities',[]))
        if not any(c.get('id')==candidate['id'] and c.get('version')==candidate['version'] and c.get('isCandidate') for c in capabilities):
            raise ValueError('此运行没有采用当前候选版本；请在试验委托中选择该候选')
        item_id=run.get('itemId')
        evidence=next((e for e in self.gongzuo_service.repository.list_evidence(workspace,item_id) if e['id']==body['evidenceId']),None)
        if not evidence or evidence.get('runId')!=body['runId'] or evidence['status']!='accepted':
            raise ValueError('需要该运行关联并已人工接受的实际证据')

    def publish(self, workspace: str, candidate_id: str, version: str, actor: str) -> dict[str,Any]:
        candidate=self.repository.get(workspace,candidate_id)
        if candidate['status']=='published' and candidate['version']==version: return candidate
        if candidate['target']=='knowledge':
            current=self.document(workspace,candidate['sourcePath'])
            if current['version']!=candidate['baseVersion'] or current['sourceVersion']!=candidate['sourceRevision']:
                raise ValueError('知识来源已变化，本次候选需重新比较与验证')
        checks=candidate['verifications']
        if not checks or checks[0]['result']!='accepted' or checks[0]['candidateVersion']!=version:
            raise ValueError('当前版本尚无被接受的运行验证')
        self._check_verification(workspace,candidate,checks[0])
        return self.repository.publish(workspace,candidate_id,version,actor)
