from pathlib import Path
from types import SimpleNamespace

import pytest

from src.gongzuo_knowledge.service import GongzuoKnowledgeService, digest


@pytest.fixture
def knowledge(tmp_path):
    personal=tmp_path/'personal'; team=tmp_path/'team'
    personal.mkdir(); team.mkdir()
    (personal/'study.md').write_text('# 学习\n实际材料',encoding='utf-8')
    (team/'business.md').write_text('# 团队\n团队专用',encoding='utf-8')
    rows={'personal':[], 'team':[]}
    def get(workspace,candidate_id):
        result=next((r for r in rows[workspace] if r['id']==candidate_id),None)
        if result is None: raise KeyError(candidate_id)
        return result
    repository=SimpleNamespace(list=lambda workspace:rows[workspace],get=get)
    service=GongzuoKnowledgeService(repository,{'personal':personal,'team':team},SimpleNamespace())
    return service,rows,personal,team


def test_knowledge_catalog_keeps_workspaces_and_source_versions(knowledge):
    service,_,_,_=knowledge
    assert [r['path'] for r in service.catalog('personal')['items']]==['study.md']
    assert service.catalog('personal','团队')['total']==0
    with pytest.raises(KeyError): service.document('personal','business.md')
    doc=service.document('team','business.md')
    assert doc['version']==digest('# 团队\n团队专用') and doc['source']=='git-file'


def test_knowledge_path_escape_and_symlink_are_denied(knowledge):
    service,_,personal,team=knowledge
    (personal/'leak.md').symlink_to(team/'business.md')
    assert [r['path'] for r in service.catalog('personal')['items']]==['study.md']
    for path in ('../team/business.md',str(team/'business.md'),'leak.md'):
        with pytest.raises((ValueError,KeyError)): service.document('personal',path)


def test_raw_not_promoted_into_current_catalog(knowledge):
    service,_,personal,_=knowledge
    (personal/'raw').mkdir(); (personal/'raw'/'feedback.md').write_text('# 原始反馈')
    assert [r['path'] for r in service.catalog('personal')['items']]==['study.md']


def test_published_knowledge_is_explicit_release_with_original_source(knowledge):
    service,rows,personal,_=knowledge
    original=service.document('personal','study.md')
    rows['personal'].append({'id':'cap-one','target':'knowledge','sourcePath':'study.md','title':'学习',
        'status':'published','version':digest('# 学习\n已审修订'),'content':'# 学习\n已审修订',
        'baseVersion':original['version'],'sourceRevision':original['sourceVersion']})
    current=service.document('personal','study.md')
    assert current['content']=='# 学习\n已审修订' and current['source']=='workspace-release'
    assert current['sourceChanged'] is False and (personal/'study.md').read_text()=='# 学习\n实际材料'
    (personal/'study.md').write_text('# 学习\n来源随后改变')
    assert service.document('personal','study.md')['sourceChanged'] is True
    assert service.published_context('personal')==[]


def test_trial_context_replaces_release_only_for_matching_target(knowledge):
    service,rows,_,_=knowledge
    rows['personal'].extend([
        {'id':'old','title':'规则','target':'harness','status':'published','version':'v1','content':'旧规则'},
        {'id':'new','title':'规则','target':'harness','status':'candidate','version':'v2','content':'新规则'},
        {'id':'other','title':'别的能力','target':'agent','status':'published','version':'a1','content':'职责'}])
    frozen=service.published_context('personal','new')
    assert {r['id'] for r in frozen}=={'new','other'}
    assert next(r for r in frozen if r['id']=='new')['isCandidate'] is True
    assert {r['id'] for r in service.published_context('personal')}=={'old','other'}
    with pytest.raises(KeyError): service.published_context('team','new')


@pytest.mark.parametrize('state,capabilities,message',[
    ('failed',[{'id':'candidate','version':'v1','isCandidate':True}],'成功结束'),
    ('succeeded',[{'id':'candidate','version':'v0','isCandidate':True}],'没有采用'),
    ('succeeded',[{'id':'candidate','version':'v1','isCandidate':False}],'没有采用'),
])
def test_verification_cannot_be_faked_by_a_status_toggle(knowledge,state,capabilities,message):
    service,rows,_,_=knowledge
    rows['personal'].append({'id':'candidate','version':'v1','status':'candidate'})
    service.run_reader=lambda workspace,run_id:{'state':state,'capabilities':capabilities}
    with pytest.raises(ValueError,match=message):
        service.verify('personal','candidate',{'runId':'run-one','evidenceId':'proof','result':'accepted','assessment':'ok'},'admin')


def test_stale_knowledge_cannot_be_published(knowledge):
    service,rows,personal,_=knowledge
    original=service.document('personal','study.md')
    rows['personal'].append({'id':'candidate','title':'学习','status':'verified','target':'knowledge',
        'sourcePath':'study.md','baseVersion':original['version'],'sourceRevision':original['sourceVersion'],'version':'v2'})
    (personal/'study.md').write_text('# 学习\n并发编辑')
    with pytest.raises(ValueError,match='来源已变化'): service.publish('personal','candidate','v2','admin')
