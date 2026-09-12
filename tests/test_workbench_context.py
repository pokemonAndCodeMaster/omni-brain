"""Context handoff must preserve evidence and fail clearly on missing material."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from workbench_context import build, check, WorkbenchError


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Test', '-c',
                        'user.email=test@example.invalid', 'commit', '--allow-empty', '-qm', 'base'], check=True)
        (self.root / 'docs').mkdir()
        (self.root / 'docs/rules.md').write_text('Original skill behavior\n')
        self.issue = {'id': 'YYH-1', 'uuid': 'issue-1', 'title': '接上原事项',
                      'description': '目标与成功例子：不用搬聊天。\n\n[方案](https://linear.app/yyhpokemonmaster/document/设计-abcdef123456)',
                      'documents': [{'id': 'document-1'}], 'url': 'https://linear.app/yyhpokemonmaster/issue/YYH-1',
                      'updatedAt': '2026-09-12T00:00:00Z'}
        self.doc = {'id': 'document-1', 'slugId': 'abcdef123456', 'title': '接续设计',
                    'content': '当前决定：先读完整资料。\n\n未验证：另一台电脑。',
                    'url': 'https://linear.app/yyhpokemonmaster/document/设计-abcdef123456'}
        self.packet = {'workspace': 'yyhpokemonmaster', 'issue': self.issue, 'documents': [self.doc],
                       'comments': {'comments': [{'id': 'comment-1', 'body': '用户纠正：只需要 Codex。',
                                    'createdAt': '2026-09-12T01:00:00Z', 'quotedText': '支持两个工具',
                                    'author': {'name': '用户'}}], 'hasNextPage': False},
                       'children': {'issues': [], 'hasNextPage': False}, 'localFiles': ['docs/rules.md']}
        self.source = self.root / 'packet.json'

    def write_packet(self, packet=None):
        self.source.write_text(json.dumps(packet or self.packet, ensure_ascii=False))

    def test_real_reading_packet_preserves_context_and_detects_later_changes(self):
        self.write_packet()
        result = build(self.root, self.source)
        body = Path(result['context']).read_text()
        for expected in ['不用搬聊天', '当前决定：先读完整资料', '未验证：另一台电脑',
                         '用户纠正：只需要 Codex', '引用位置：支持两个工具', 'docs/rules.md']:
            self.assertIn(expected, body)
        self.assertNotIn('Original skill behavior', body)
        manifest = Path(result['manifest'])
        self.assertTrue(check(self.root, manifest)['unchangedCapturedInputs'])
        (self.root / 'docs/rules.md').write_text('Changed instructions')
        self.assertIn('docs/rules.md', check(self.root, manifest)['changes'])
        self.issue['description'] += '\n新的用户反馈'
        self.write_packet()
        self.assertIn('captured Linear input changed or is missing', check(self.root, manifest)['changes'])

    def test_missing_or_partial_comments_children_documents_fail_before_output(self):
        variants = []
        p = copy.deepcopy(self.packet); p['comments']['hasNextPage'] = True; variants.append(p)
        p = copy.deepcopy(self.packet); del p['comments']; variants.append(p)
        p = copy.deepcopy(self.packet); p['children']['hasNextPage'] = True; variants.append(p)
        p = copy.deepcopy(self.packet); p['documents'] = []; variants.append(p)
        p = copy.deepcopy(self.packet); del p['documents'][0]['content']; variants.append(p)
        p = copy.deepcopy(self.packet); del p['issue']['description']; variants.append(p)
        for packet in variants:
            with self.subTest(packet=packet):
                self.write_packet(packet)
                with self.assertRaises(WorkbenchError): build(self.root, self.source)
                self.assertFalse((self.root / '.derived').exists())

    def test_parent_children_and_project_are_bound_to_the_right_work(self):
        self.issue['parentId'] = 'parent-1'
        self.issue['projectId'] = 'project-1'
        self.packet['parent'] = {'id': 'YYH-2', 'uuid': 'parent-1', 'title': '共同目标', 'description': '父目标不能丢失', 'url':'https://linear.app/yyhpokemonmaster/issue/YYH-2'}
        self.packet['project'] = {'id': 'project-1', 'name': '工作台', 'description': '首版成功例子', 'url': 'https://linear.app/yyhpokemonmaster/project/workbench-123456abcdef'}
        self.packet['children']['issues'] = [{'id': 'YYH-3', 'parentId': 'issue-1', 'title': '子工作', 'description': '验证一个真实入口', 'url':'https://linear.app/yyhpokemonmaster/issue/YYH-3'}]
        self.write_packet()
        result = build(self.root, self.source)
        body = Path(result['context']).read_text()
        for text in ['父目标不能丢失', '首版成功例子', '验证一个真实入口']: self.assertIn(text, body)
        self.packet['project']['url'] = 'https://linear.app/other/project/foreign-123456abcdef'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'Project URL'): build(self.root, self.source)
        self.packet['project']['url'] = 'https://linear.app/yyhpokemonmaster/project/workbench-123456abcdef'
        self.packet['children']['issues'][0]['parentId'] = 'another-issue'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'Child issue'): build(self.root, self.source)

    def test_linked_document_and_workspace_cannot_be_substituted(self):
        self.doc['id'] = 'unrelated'
        self.doc['slugId'] = '111111111111'
        self.doc['url'] = 'https://linear.app/yyhpokemonmaster/document/unrelated-111111111111'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'documents in full'): build(self.root, self.source)
        self.doc['url'] = 'https://linear.app/other/document/unrelated-111111111111'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'different workspace'): build(self.root, self.source)

    def test_raw_secrets_symlinks_and_output_escape_are_rejected(self):
        for source in ['../outside', '/etc/passwd', 'knowledge/raw/record.md', 'apps/.env', '.codex/auth.json']:
            self.packet['localFiles'] = [source]
            self.write_packet()
            with self.subTest(source=source), self.assertRaises(WorkbenchError): build(self.root, self.source)
        self.packet['localFiles'] = ['docs/rules.md']
        self.write_packet()
        with self.assertRaises(WorkbenchError): build(self.root, self.source, Path('../outside'))
        with self.assertRaises(WorkbenchError): build(self.root, self.source, Path('docs/context'))
        (self.root / 'docs/link.md').symlink_to(self.root / 'docs/rules.md')
        self.packet['localFiles'] = ['docs/link.md']
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'Symlink'): build(self.root, self.source)

    def test_does_not_overwrite_prior_handoff(self):
        self.write_packet()
        out = Path('.derived/linear/contexts/YYH-1/first')
        first = build(self.root, self.source, out)
        before = Path(first['context']).read_bytes()
        with self.assertRaisesRegex(WorkbenchError, 'already exists'): build(self.root, self.source, out)
        self.assertEqual(before, Path(first['context']).read_bytes())

    def test_changed_reading_file_cannot_pass_as_an_intact_handoff(self):
        self.write_packet()
        result = build(self.root, self.source)
        Path(result['context']).write_text('A lossy summary')
        self.assertIn('context reading file changed or is missing', check(self.root, Path(result['manifest']))['changes'])

    def test_bare_document_link_requires_full_body_but_code_sample_does_not(self):
        self.issue['documents'] = []
        self.issue['description'] = '材料 https://linear.app/yyhpokemonmaster/document/abcdef123456'
        self.packet['documents'] = []
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError, 'documents in full'): build(self.root, self.source)
        self.issue['description'] = '`https://linear.app/yyhpokemonmaster/document/abcdef123456` 是示例语法。'
        self.write_packet()
        build(self.root, self.source)

    def test_unbound_relations_and_wrong_issue_url_are_rejected(self):
        variants=[]
        p=copy.deepcopy(self.packet); p['parent']={'id':'YYH-2','description':'unrelated'}; variants.append(p)
        p=copy.deepcopy(self.packet); del p['issue']['uuid']; p['children']['issues']=[{'id':'YYH-3','description':'wrong'}]; variants.append(p)
        p=copy.deepcopy(self.packet); p['comments']['comments'][0]['issueId']='other'; variants.append(p)
        p=copy.deepcopy(self.packet); p['issue']['url']='https://linear.app/yyhpokemonmaster/issue/YYH-999'; variants.append(p)
        for packet in variants:
            self.write_packet(packet)
            with self.subTest(packet=packet), self.assertRaises(WorkbenchError): build(self.root, self.source)

    def test_actual_agent_entry_and_public_workspace_config_are_fingerprinted(self):
        (self.root/'AGENTS.md').write_text('entry')
        (self.root/'config').mkdir()
        (self.root/'config/linear-workbench.json').write_text('{"workspace":"test"}')
        self.packet['localFiles'] += ['AGENTS.md','config/linear-workbench.json']
        self.write_packet()
        result=build(self.root,self.source)
        (self.root/'AGENTS.md').write_text('changed entry')
        self.assertIn('AGENTS.md',check(self.root,Path(result['manifest']))['changes'])

    def test_comment_requirements_and_document_identity_are_not_silently_lost(self):
        self.packet['comments']['comments'][0]['body']='这次必须按[新验收条件](https://linear.app/yyhpokemonmaster/document/new-111111111111)执行。'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError,'documents in full'):build(self.root,self.source)
        self.packet['comments']['comments'][0]['body']='只用Codex'
        self.doc['url']='https://linear.app/yyhpokemonmaster/document/wrong-999999999999'
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError,'contradicts'):build(self.root,self.source)

    def test_declared_parent_with_a_different_issue_link_is_rejected(self):
        self.issue['parentId']='parent-1'
        self.packet['parent']={'id':'YYH-2','uuid':'parent-1','description':'共同目标','url':'https://linear.app/other/issue/OTH-9'}
        self.write_packet()
        with self.assertRaisesRegex(WorkbenchError,'Parent issue URL'):build(self.root,self.source)


if __name__ == '__main__': unittest.main()
