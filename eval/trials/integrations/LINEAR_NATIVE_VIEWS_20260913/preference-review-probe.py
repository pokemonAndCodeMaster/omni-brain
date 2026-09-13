import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

root = Path('/home/yyh/project/.omni-brain-runs/linear-native-views-20260913')
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('candidate_linear_views', root / 'scripts/linear_views.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
sdl = Path('/home/yyh/project/omni-brain/.derived/linear/views-api/official-schema.graphql').read_text()
# Read the actual official preference type declarations; no candidate constants
# define the independent universe of preference fields.
types = {}
for name, body in re.findall(r'^type (ViewPreferences\w+)\s*\{(.*?)^\}', sdl, re.M | re.S):
    body = re.sub(r'""".*?"""', '', body, flags=re.S)
    fields = []
    for field, field_type, directive in re.findall(r'^\s*(\w+)\s*:\s*([\w\[\]!]+)([^\n]*)$', body, re.M):
        fields.append((field, field_type, '@deprecated' in directive))
    types[name] = fields
assert len(types['ViewPreferencesValues']) > 200

def typeref(value):
    if value.endswith('!'):
        return {'kind': 'NON_NULL', 'name': None, 'ofType': typeref(value[:-1])}
    if value.startswith('['):
        return {'kind': 'LIST', 'name': None, 'ofType': typeref(value[1:-1])}
    return {'kind': 'OBJECT' if value in types else 'SCALAR', 'name': value, 'ofType': None}

def selection(query):
    tokens = re.findall(r'\w+|[^\s,]', query)
    pos = tokens.index('{')
    def parse():
        nonlocal pos
        assert tokens[pos] == '{'
        pos += 1
        result = {}
        while tokens[pos] != '}':
            alias = name = tokens[pos]
            pos += 1
            if tokens[pos] == ':':
                pos += 1
                name = tokens[pos]
                pos += 1
            if tokens[pos] == '(':
                depth = 1
                pos += 1
                while depth:
                    if tokens[pos] == '(':
                        depth += 1
                    elif tokens[pos] == ')':
                        depth -= 1
                    pos += 1
            child = parse() if tokens[pos] == '{' else None
            assert alias not in result
            result[alias] = (name, child)
        pos += 1
        return result
    return parse()

def project(value, shape):
    if value is None:
        return None
    if isinstance(value, list):
        return [project(v, shape) for v in value]
    if shape is None:
        return copy.deepcopy(value)
    assert isinstance(value, dict)
    return {alias: project(value.get(name), child) for alias, (name, child) in shape.items()}

def validate_preferences(shape, typename='ViewPreferencesValues'):
    official = {name: value for name, value, _ in types[typename]}
    for alias, (name, child) in shape.items():
        assert name in official, ('Unknown GraphQL field', typename, name)
        leaf = official[name].strip('[]!')
        if leaf in types:
            assert child is not None, ('Missing child selection', name)
            validate_preferences(child, leaf)
        else:
            assert child is None, ('Scalar given child selection', name)

def values(typename):
    result = {}
    for index, (name, value, _) in enumerate(types[typename]):
        leaf = value.strip('[]!')
        if value.startswith('['):
            result[name] = [values(leaf), {**values(leaf), 'id': 'second-' + name}] if leaf in types else []
        elif leaf == 'Boolean':
            result[name] = False
        elif leaf in {'String', 'ID'}:
            result[name] = 'preserve-' + name
        elif leaf in {'Float', 'Int'}:
            result[name] = 0
        else:
            raise AssertionError((name, value))
    return result

class StrictClient:
    def __init__(self, prefs, spec):
        self.inputs = []
        self.queries = []
        self.shapes = []
        self.view = {
            'id': 'existing-view', 'name': spec['name'], 'slugId': 'existing-slug',
            'updatedAt': 'unchanged-version', 'archivedAt': None, 'modelName': 'Issue',
            'shared': False, 'filterData': copy.deepcopy(spec['filterData']),
            'owner': {'id': app.USER}, 'team': None,
            'organization': {'id': 'org', 'urlKey': app.WORKSPACE},
            'userViewPreferences': {'id': 'existing-preferences', 'preferences': copy.deepcopy(prefs)},
            'viewPreferencesValues': copy.deepcopy(prefs),
        }
    def __call__(self, query, variables=None):
        variables = variables or {}
        self.queries.append(query)
        if query.startswith('query PreferenceShape'):
            typename = variables['name']
            include_deprecated = bool(re.search(r'includeDeprecated\s*:\s*true', query))
            self.shapes.append((typename, include_deprecated))
            metadata = {'fields': [
                {'name': name, 'type': typeref(value)}
                for name, value, deprecated in types[typename]
                if include_deprecated or not deprecated
            ]}
            return project({'__type': metadata}, selection(query))
        if query.startswith('query '):
            shape = selection(query)
            # Validate preference selections against the official schema, then
            # return exactly requested keys at every nesting level.
            view_shape = shape['customView'][1]
            if 'userViewPreferences' in view_shape:
                pref_shape = view_shape['userViewPreferences'][1]['preferences'][1]
                validate_preferences(pref_shape)
            if 'viewPreferencesValues' in view_shape:
                validate_preferences(view_shape['viewPreferencesValues'][1])
            return project({'customView': self.view}, shape)
        if 'viewPreferencesUpdate(' in query:
            assert variables['id'] == 'existing-preferences'
            self.inputs.append(copy.deepcopy(variables['input']))
            # Model whole JSONObject replacement: omission must be observable.
            self.view['userViewPreferences']['preferences'] = copy.deepcopy(variables['input']['preferences'])
            self.view['viewPreferencesValues'] = copy.deepcopy(variables['input']['preferences'])
            return {'viewPreferencesUpdate': {'success': True, 'viewPreferences': {'id': variables['id']}}}
        raise AssertionError(query)

requested = app.definitions({'想法':'idea','需求':'requirement','任务':'task'})[0]
before = values('ViewPreferencesValues')
client = StrictClient(before, requested)
with tempfile.TemporaryDirectory(prefix='linear-prefs-probe-') as tmp:
    current = app.get_view(client, 'existing-view')
    assert 'fieldAssignee' not in current['userViewPreferences']['preferences']
    planned = app.plan_views([requested], [current])
    app.apply_views(client, planned, Path(tmp) / 'state.json')
after = client.view['userViewPreferences']['preferences']
expected = {**before, **requested['preferences']}
assert after == expected, {'missing': sorted(expected.keys()-after.keys()), 'changed': [k for k in expected if after.get(k) != expected[k]]}
assert len(client.inputs) == 1
assert client.view['userViewPreferences']['id'] == 'existing-preferences'
assert client.inputs[0].keys() == {'preferences'}
deprecated = [name for name, _, old in types['ViewPreferencesValues'] if old]
assert all(after[name] == before[name] for name in deprecated)
assert after['fieldAssignee'] is False
assert after['hiddenColumns'] == []
assert after['projectLabelGroupColumns'] == [{'active':False,'id':'preserve-id'}, {'active':False,'id':'second-projectLabelGroupColumns'}]
assert after['initiativeLabelGroupColumns'] == [{'active':False,'id':'preserve-id'}, {'active':False,'id':'second-initiativeLabelGroupColumns'}]
# A repeated run with the same target must avoid rewriting the preferences.
with tempfile.TemporaryDirectory(prefix='linear-prefs-probe-repeat-') as tmp:
    current = app.get_view(client, 'existing-view')
    app.apply_views(client, app.plan_views([requested], [current]), Path(tmp) / 'state.json')
assert len(client.inputs) == 1
assert client.view['userViewPreferences']['preferences'] == expected
report = {
    'result': 'pass_for_offline_strict_projection',
    'source_sha256': hashlib.sha256((root/'scripts/linear_views.py').read_bytes()).hexdigest(),
    'schema_sha256': hashlib.sha256(sdl.encode()).hexdigest(),
    'exposed_preference_fields': len(before),
    'unowned_fields_preserved': len(set(before)-set(requested['preferences'])),
    'deprecated_fields_preserved': deprecated,
    'false_preserved': after['fieldAssignee'],
    'empty_list_preserved': after['hiddenColumns'],
    'nested_object_arrays_preserved': {k:after[k] for k in ['projectLabelGroupColumns','initiativeLabelGroupColumns']},
    'introspection_shapes': client.shapes,
    'preference_write_count_after_second_run': len(client.inputs),
    'real_api': 'not_proven', 'browser': 'not_proven',
}
Path('/tmp/linear-preferences-independent-probe-result.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
