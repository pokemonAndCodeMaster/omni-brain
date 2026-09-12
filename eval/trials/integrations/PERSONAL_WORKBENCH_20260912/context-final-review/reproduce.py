import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROOT = OUT / 'fixture'
ROOT.mkdir(exist_ok=True)
LOG = []
ENV = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) if not isinstance(value, str) else value)

def run(name, args, expected=None):
    proc = subprocess.run(args, capture_output=True, text=True, env=ENV)
    record = {'case': name, 'command': args, 'returncode': proc.returncode,
              'stdout': proc.stdout, 'stderr': proc.stderr, 'expected': expected}
    LOG.append(record)
    save(OUT / 'execution.json', LOG)
    print(name, proc.returncode, (proc.stdout + proc.stderr).replace('\n', ' ')[:190])
    try: data = json.loads(proc.stdout)
    except ValueError: data = {}
    return proc, data

def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True)

git('init', '-q')
git('-c', 'user.name=Independent Review', '-c', 'user.email=review@example.invalid', 'commit', '--allow-empty', '-qm', 'fixture base')
local = {'AGENTS.md': '原入口\n', '.agents/skills/example/SKILL.md': '原技能\n',
         'harness.yaml': 'version: 1\n', 'config/public.json': '{"public":true}', 'scripts/example.py': 'VALUE = 1\n'}
for name, value in local.items(): save(ROOT / name, value)
config = {'workspace': 'reviewspace', 'team_id': 'team-review', 'publications': [
    {'key': 'knowledge-home', 'source': 'docs/index.md', 'title': '知识与成果'}]}
save(ROOT / 'config/linear-workbench.json', config)
navigation = '# 阅读目录\n\n[既有阅读路线](https://example.invalid/route)\n\n## 全部 Linear 文档\n\n旧文档列表\n\n## 目录怎样更新\n\n保持已有维护说明。\n'
save(ROOT / 'docs/index.md', navigation)
long_body = '目标：新会话保留上下文。\n\n' + ('完整段落：0123456789。\n' * 800) + '\n结尾不能丢。'
packet = {'workspace': 'reviewspace',
    'issue': {'id': 'YYH-71', 'uuid': 'issue-71', 'title': '完整接续', 'url': 'https://linear.app/reviewspace/issue/YYH-71',
              'description': long_body + '\n\n[实施方案](https://linear.app/reviewspace/document/设计-abcdef123456)',
              'documents': [{'id': 'doc-required'}], 'parentId': 'parent-70', 'projectId': 'project-7'},
    'documents': [{'id': 'doc-required', 'slugId': 'abcdef123456', 'title': '实施方案',
                   'url': 'https://linear.app/reviewspace/document/设计-abcdef123456', 'content': '方案全文\n\n```python\nprint("保留代码与限制")\n```\n\n尚未验收。'}],
    'parent': {'id': 'YYH-70', 'uuid': 'parent-70', 'title': '共同目标', 'url': 'https://linear.app/reviewspace/issue/YYH-70', 'description': '父目标全文：完整工作旅程。'},
    'project': {'id': 'project-7', 'name': '项目七', 'url': 'https://linear.app/reviewspace/project/p-seven', 'description': '项目背景：跨会话。'},
    'comments': {'comments': [{'id': 'comment-1', 'issueId': 'issue-71', 'body': '早期想法完整正文。', 'createdAt': '2026-09-12T01:00:00Z', 'author': {'name': '使用者'}},
        {'id': 'comment-2', 'issueId': 'YYH-71', 'body': '后续纠正：保留失败边界，未验收。', 'createdAt': '2026-09-12T02:00:00Z', 'quotedText': '已经成功', 'author': {'name': '使用者'}}], 'hasNextPage': False},
    'children': {'issues': [{'id': 'YYH-72', 'parentId': 'issue-71', 'title': '验证入口', 'description': '子事项全文：验证跨会话结果。', 'url': 'https://linear.app/reviewspace/issue/YYH-72'}], 'hasNextPage': False},
    'localFiles': list(local)}

def build(name, value, expected=None, output=None):
    path = OUT / 'inputs' / (name + '.json')
    save(path, value)
    return run(name, [sys.executable, str(BASE / 'scripts/workbench_context.py'), '--root', str(ROOT), 'build', '--input', str(path), '--output', output or '.derived/linear/contexts/' + name], expected)

def check(name, manifest, expected=None):
    return run(name, [sys.executable, str(BASE / 'scripts/workbench_context.py'), '--root', str(ROOT), 'check', '--manifest', str(manifest)], expected)

_, valid = build('full_context', packet, 'complete reading content')
body = Path(valid['context']).read_text()
texts = [packet['issue']['description'], packet['documents'][0]['content'], packet['parent']['description'], packet['project']['description'], packet['children']['issues'][0]['description']] + [c['body'] for c in packet['comments']['comments']]
save(OUT / 'reading-assertions.json', {'all_full_bodies_verbatim': all(t in body for t in texts), 'quoted_text_preserved': '已经成功' in body, 'old_source_body_not_copied': '原技能' not in body})
check('intact_offline_check', valid['manifest'], 'unchanged captured inputs; online freshness unknown')
for name in local:
    save(ROOT / name, local[name] + '\nCHANGED')
    check('changed_declared_' + name.replace('/', '_'), valid['manifest'], 'reject changed declared source')
    save(ROOT / name, local[name])
Path(valid['context']).write_text('只剩摘要')
check('changed_reading_file', valid['manifest'], 'reject tampering')
Path(valid['context']).unlink()
check('deleted_reading_file', valid['manifest'], 'reject deletion')
save(Path(valid['context']), body)
source = OUT / 'inputs/full_context.json'
before = source.read_text()
save(source, packet | {'extra': 'new capture'})
check('changed_capture', valid['manifest'], 'reject changed input')
save(source, before)
git('-c', 'user.name=Independent Review', '-c', 'user.email=review@example.invalid', 'commit', '--allow-empty', '-qm', 'new version')
check('changed_repository_commit', valid['manifest'], 'reject changed code commit')

variants = {}
for key in ('comments', 'children'):
    p = copy.deepcopy(packet); p[key]['hasNextPage'] = True; variants['incomplete_' + key] = p
p = copy.deepcopy(packet); p['documents'] = []; variants['missing_issue_document'] = p
p = copy.deepcopy(packet); p['documents'][0].pop('content'); variants['document_summary_only'] = p
p = copy.deepcopy(packet); p['parent']['uuid'] = 'another'; variants['wrong_parent'] = p
p = copy.deepcopy(packet); p['project']['id'] = 'another'; variants['wrong_project'] = p
p = copy.deepcopy(packet); p['children']['issues'][0]['parentId'] = 'another'; variants['wrong_child_parent'] = p
p = copy.deepcopy(packet); p['comments']['comments'][0]['issueId'] = 'another'; variants['wrong_comment_issue'] = p
p = copy.deepcopy(packet); p['documents'][0]['url'] = 'https://linear.app/other/document/设计-abcdef123456'; variants['wrong_document_workspace'] = p
p = copy.deepcopy(packet); p['issue']['description'] += '\n必读 https://linear.app/reviewspace/document/111111111111'; variants['missing_direct_bare_link'] = p
for name, p in variants.items(): build(name, p, 'reject')

p = copy.deepcopy(packet)
p['comments']['comments'][1]['body'] += '\n本轮实施必须先读[刚修改的验收条件](https://linear.app/reviewspace/document/new-111111111111)。'
build('missing_required_comment_document', p, 'reject or explicitly disclose missing required comment document')
p = copy.deepcopy(packet)
p['documents'][0]['slugId'] = '999999999999'
p['documents'][0]['url'] = 'https://linear.app/reviewspace/document/unrelated-999999999999'
p['issue']['description'] = '继续明确挂载的当前文档。'
build('conflicting_document_identity', p, 'same-workspace wrong document must not satisfy required attachment ID silently')
p = copy.deepcopy(packet)
p['issue']['description'] = '必读[方案](https://linear.app/reviewspace/document/abcdef123456)'
p['issue']['documents'] = []
p['documents'][0]['slugId'] = 'abcdef123456'
p['documents'][0]['url'] = 'https://linear.app/reviewspace/document/wrong-999999999999'
build('contradictory_slug_url', p, 'reject internal slugId/URL contradiction')
p = copy.deepcopy(packet)
p['children']['issues'][0]['url'] = 'https://linear.app/other/issue/OTH-999'
build('contradictory_child_url', p, 'reject contradictory child link ownership')
p = copy.deepcopy(packet)
p['parent']['url'] = 'https://linear.app/other/issue/OTH-999'
build('contradictory_parent_url', p, 'reject contradictory parent link ownership')

for name in ['../outside.md', '/etc/passwd', 'knowledge/raw/raw.md', 'config/token.json', 'apps/.env']:
    p = copy.deepcopy(packet); p['localFiles'] = [name]
    build('bad_source_' + name.replace('/', '_').replace('.', '_'), p, 'reject before reading prohibited source')
save(ROOT / 'knowledge/raw/raw.md', 'synthetic raw only')
(ROOT / 'docs/raw-link.md').symlink_to(ROOT / 'knowledge/raw/raw.md')
p = copy.deepcopy(packet); p['localFiles'] = ['docs/raw-link.md']
build('raw_symlink_source', p, 'reject')
build('escape_output', packet, 'reject', '../escape')
build('forbidden_output', packet, 'reject', 'knowledge/raw/context')
(ROOT / '.derived/linear/contexts/link').symlink_to(ROOT / 'docs', target_is_directory=True)
build('symlink_output', packet, 'reject', '.derived/linear/contexts/link/new')
build('no_overwrite', packet, 'reject existing context', '.derived/linear/contexts/full_context')

docs = []
for idx, kind in enumerate(['team', 'project', 'issue', 'initiative', None]):
    doc = {'id': 'document-' + str(idx), 'title': (kind or 'standalone') + ' 文档 | [特殊]', 'url': 'https://linear.app/reviewspace/document/doc-' + str(idx), 'updatedAt': '2026-09-12T00:00:00Z'}
    if kind: doc[kind] = {'id': 'YYH-71' if kind == 'issue' else kind + '-1', 'name': kind + ' 位置'}
    docs.append(doc)
inventory = {'documents': docs, 'hasNextPage': False}
def directory(name, value, expected=None, root=ROOT):
    path = OUT / 'inputs' / (name + '.json'); save(path, value)
    return run(name, [sys.executable, str(BASE / 'scripts/linear_workbench.py'), '--root', str(root), 'directory', '--inventory', str(path)], expected)
directory('directory_all_mounts', inventory, 'all documents and existing route retained')
directory_body = (ROOT / 'docs/index.md').read_text()
from markdown_it import MarkdownIt
tokens = MarkdownIt().enable('table').parse(directory_body)
links = [child.attrGet('href') for token in tokens for child in (token.children or []) if child.type == 'link_open']
save(OUT / 'directory-assertions.json', {'all_document_urls_readable': all(d['url'] in links for d in docs), 'all_owner_names_present': all((d.get('issue') or {}).get('id', (d.get('team') or d.get('project') or d.get('initiative') or {}).get('name', '独立资料')) in directory_body for d in docs), 'route_retained': 'https://example.invalid/route' in links, 'maintenance_text_retained': '保持已有维护说明。' in directory_body, 'rendered_table_rows': sum(t.type == 'tr_open' for t in tokens)})
for name, value in [('directory_partial', inventory | {'hasNextPage': True}), ('directory_duplicate', inventory | {'documents': docs + [docs[0]]}), ('directory_foreign', inventory | {'documents': [docs[0] | {'url': 'https://linear.app/other/document/doc-0'}]})]:
    before = (ROOT / 'docs/index.md').read_bytes()
    directory(name, value, 'reject and preserve existing directory')
    LOG[-1]['original_preserved'] = before == (ROOT / 'docs/index.md').read_bytes()
save(OUT / 'execution.json', LOG)

actual = OUT / 'actual-entry-fixture'
real_config = json.loads((BASE / 'config/linear-workbench.json').read_text())
save(actual / 'config/linear-workbench.json', real_config)
for publication in real_config['publications']:
    src = BASE / publication['source']
    if src.is_file(): save(actual / publication['source'], src.read_text())
actual_inventory = copy.deepcopy(inventory)
for doc in actual_inventory['documents']: doc['url'] = doc['url'].replace('reviewspace', real_config['workspace'])
directory('actual_declared_directory_entry', actual_inventory, 'default directory CLI works with actual declared source', actual)
identities = {name: hashlib.sha256((BASE / name).read_bytes()).hexdigest() for name in ['scripts/workbench_context.py', 'scripts/linear_workbench.py', 'docs/linear-workbench/knowledge.md', 'docs/linear-workbench/README.md', '.agents/skills/personal-workbench/SKILL.md']}
save(OUT / 'candidate-identities.json', identities)
