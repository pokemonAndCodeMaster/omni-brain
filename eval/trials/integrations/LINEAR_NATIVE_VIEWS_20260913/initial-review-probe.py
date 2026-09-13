import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

ROOT = Path('/home/yyh/project/.omni-brain-runs/linear-native-views-20260913')
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('candidate_tests', ROOT / 'tests/test_linear_views.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app

class StrictFake(module.FakeClient):
    def __init__(self):
        super().__init__()
        self.operations = []
        self.lose_favorite_response = False
    def __call__(self, query, variables=None):
        variables = variables or {}
        self.operations.append((query, copy.deepcopy(variables)))
        if 'query PreferenceShape' in query:
            if variables['name'] == 'ViewPreferencesProjectLabelGroupColumn':
                return {'__type': {'fields': [
                    {'name': 'id', 'type': {'kind': 'SCALAR', 'name': 'String'}},
                    {'name': 'active', 'type': {'kind': 'SCALAR', 'name': 'Boolean'}}]}}
            fields = [
                {'name': key, 'type': {'kind': 'SCALAR', 'name': 'String'}}
                for key in app.PREF_FIELDS.split() + ['fieldAssignee', 'hiddenGroupsList']
            ]
            fields.append({'name': 'projectLabelGroupColumns', 'type': {'kind': 'LIST', 'name': None, 'ofType': {'kind': 'NON_NULL', 'name': None, 'ofType': {'kind': 'OBJECT', 'name': 'ViewPreferencesProjectLabelGroupColumn'}}}})
            if re.search(r'includeDeprecated\s*:\s*true', query):
                fields.append({'name': 'projectGroupOrdering', 'type': {'kind': 'SCALAR', 'name': 'String'}})
            return {'__type': {'fields': fields}}
        if 'query AllPreferences' in query:
            pref = copy.deepcopy(self.views[variables['id']]['userViewPreferences'])
            pref['preferences'] = {key: value for key, value in pref['preferences'].items()
                                   if re.search(r'\b' + re.escape(key) + r'\b', query)}
            return {'customView': {'userViewPreferences': pref}}
        result = super().__call__(query, variables)
        if 'favoriteCreate(' in query and self.lose_favorite_response:
            self.lose_favorite_response = False
            raise app.ViewError('favorite response lost after committed write')
        return result

def specs():
    return app.definitions({'想法': 'idea-label', '需求': 'requirement-label', '任务': 'task-label'})

report = {}
with tempfile.TemporaryDirectory(prefix='linear-review-') as tmp:
    fake = StrictFake()
    state = Path(tmp) / 'state.json'
    views = app.apply_views(fake, app.plan_views(specs(), []), state)
    fake.favorites.append({'id': 'unrelated-favorite', 'customView': None, 'parent': None,
                           'sortOrder': -7000, 'owner': {'id': app.USER}, 'url': 'https://linear.app/yyhpokemonmaster/issue/YYH-1'})
    other = copy.deepcopy(fake.favorites[0])
    fake.lose_favorite_response = True
    try:
        app.ensure_favorites(fake, views)
    except app.ViewError:
        pass
    recovered_id = fake.favorites[-1]['id']
    app.ensure_favorites(fake, views)
    assert len(fake.favorites) == 6
    assert fake.favorites[0] == other
    assert fake.favorites[1]['id'] == recovered_id
    assert [f['customView']['id'] for f in sorted(fake.favorites, key=lambda x: x['sortOrder'])[:5]] == [v['id'] for v in views]
    before = copy.deepcopy((fake.views, fake.favorites))
    fake.operations.clear()
    views = app.apply_views(fake, app.plan_views(specs(), list(fake.views.values())), state)
    app.ensure_favorites(fake, views)
    writes = [q for q, v in fake.operations if q.lstrip().startswith('mutation ')]
    assert not writes and (fake.views, fake.favorites) == before
    report['favorites_lost_response_recovery_identity_and_order'] = 'pass in fake, unrelated favorite unchanged'
    report['second_apply_no_mutation'] = 'pass in fake'

    view = next(iter(fake.views.values()))
    view['userViewPreferences']['preferences'].update({
        'layout': 'board', 'fieldAssignee': False, 'hiddenGroupsList': [],
        'projectLabelGroupColumns': [{'id': 'group-old', 'active': False}],
        'projectGroupOrdering': 'name'})
    plan = app.plan_views(specs(), copy.deepcopy(list(fake.views.values())))
    app.apply_views(fake, plan, state)
    saved = view['userViewPreferences']['preferences']
    assert saved['fieldAssignee'] is False
    assert saved['hiddenGroupsList'] == []
    assert saved['projectLabelGroupColumns'] == [{'id': 'group-old', 'active': False}]
    report['unowned_false_empty_nested_values'] = 'pass in strict projection fake'
    report['deprecated_unowned_projectGroupOrdering_preserved'] = 'pass' if saved.get('projectGroupOrdering') == 'name' else 'fail: absent after preference replacement'
    report['all_preferences_selection'] = fake.preference_selection
print(json.dumps(report, ensure_ascii=False, indent=2))
