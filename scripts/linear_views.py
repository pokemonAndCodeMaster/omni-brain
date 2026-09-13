#!/usr/bin/env python3
"""Configure the five personal Linear views through the official GraphQL API.

Credentials come only from explicit Linear environment variables or a private
local key file. Codex MCP credentials are deliberately not used by this tool.
"""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import stat
import sys
import urllib.error
import urllib.request
import uuid

WORKSPACE = 'yyhpokemonmaster'
TEAM = '4a838ade-2fd2-401f-860e-8926c3acf32c'
USER = 'f6bb509e-7703-4055-a83a-71530efe04c3'
KEY_FILE = Path.home() / '.config/omni-brain/linear-api-key'
PREF_FIELDS = ('layout issueGrouping viewOrdering viewOrderingDirection '
               'fieldId fieldStatus fieldPriority fieldProject fieldLabels '
               'showCompletedIssues showSubIssues')
VIEW_FIELDS = ('''id name slugId updatedAt archivedAt modelName shared filterData
 owner { id } team { id } organization { id urlKey }
 userViewPreferences { id preferences { ''' + PREF_FIELDS + ''' } }
 viewPreferencesValues { ''' + PREF_FIELDS + ''' }''')
ISSUE_FIELDS = '''id identifier title completedAt updatedAt
 assignee { id } team { id } state { name type }
 labels { nodes { id name } pageInfo { hasNextPage endCursor } }'''


class ViewError(Exception):
    pass


def credential(path=None):
    if os.environ.get('LINEAR_API_KEY'):
        value = os.environ['LINEAR_API_KEY'].strip()
    elif os.environ.get('LINEAR_ACCESS_TOKEN'):
        value = 'Bearer ' + os.environ['LINEAR_ACCESS_TOKEN'].strip()
    else:
        key_path = Path(path or os.environ.get('LINEAR_API_KEY_FILE', KEY_FILE))
        try:
            with os.fdopen(os.open(key_path, os.O_RDONLY | os.O_NOFOLLOW)) as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
                    raise ViewError('API key must be a private regular file (mode 600).')
                value = stream.read().strip()
        except OSError:
            raise ViewError('No readable local Linear API key. Set LINEAR_API_KEY or use ' + str(key_path)) from None
    if not value or '\n' in value or '\r' in value:
        raise ViewError('Invalid empty or multiline API credential.')
    return value


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, authorization):
        self.authorization = authorization
        self.opener = urllib.request.build_opener(NoRedirect())

    def __call__(self, query, variables=None):
        request = urllib.request.Request(
            'https://api.linear.app/graphql', method='POST',
            data=json.dumps({'query': query, 'variables': variables or {}}).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': self.authorization})
        read_only = query.lstrip().startswith('query ') and 'mutation ' not in query
        attempts = 3 if read_only else 1
        for attempt in range(attempts):
            try:
                with self.opener.open(request, timeout=25) as response:
                    payload = json.load(response)
                break
            except urllib.error.HTTPError as error:
                raise ViewError(f'Linear HTTP {error.code}; no write retried. Read current state before continuing.') from None
            except (OSError, ValueError) as error:
                if attempt + 1 < attempts:
                    continue
                reason = type(getattr(error, 'reason', error)).__name__
                operation = 'read failed' if read_only else 'write outcome unknown; re-read before continuing'
                raise ViewError(f'Linear {operation} ({reason}); no write automatically retried.') from None
        if payload.get('errors'):
            message = '; '.join(str(e.get('message', 'GraphQL error')) for e in payload['errors'])
            for secret in [self.authorization, self.authorization.removeprefix('Bearer ')]:
                message = message.replace(secret, '[redacted]')
            raise ViewError(message[:700])
        if not isinstance(payload.get('data'), dict):
            raise ViewError('Linear returned no complete data object.')
        return payload['data']


def pages(client, query, variables=None, path=('result',)):
    values, cursor, seen, ids = [], None, set(), set()
    while True:
        data = client(query, {**(variables or {}), 'after': cursor})
        for key in path:
            data = data[key]
        for node in data['nodes']:
            if node['id'] in ids:
                raise ViewError('Repeated identity during pagination; re-read before writing.')
            ids.add(node['id'])
            values.append(node)
        info = data['pageInfo']
        if not info['hasNextPage']:
            return values
        cursor = info['endCursor']
        if not cursor or cursor in seen:
            raise ViewError('Incomplete or looping pagination.')
        seen.add(cursor)


def definitions(label_ids):
    common = {'team': {'id': {'eq': TEAM}}, 'assignee': {'id': {'eq': USER}}}
    specs = [
        ('现在推进', {'state': {'name': {'in': ['Todo', 'In Progress']}}}, 'status', 'priority',
         '跨领域查看准备做和正在做的事情；打开事项查看当前目标、结果和下一步。'),
        ('等我确认', {'state': {'name': {'eq': 'In Review'}}}, 'project', 'priority',
         '只放已有成果、确实需要本人判断的事项；没有待确认事项时保持为空。'),
        ('想法待澄清', {'labels': {'some': {'id': {'eq': label_ids['想法']}}},
                     'state': {'type': {'nin': ['completed', 'canceled', 'duplicate']}}},
         'none', 'updatedAt', '保留想法、真实例子和未决问题，讨论清楚后再决定怎样投入。'),
        ('以后安排', {'state': {'name': {'eq': 'Backlog'}},
                    'labels': {'some': {'id': {'in': [label_ids['需求'], label_ids['任务']]}}}},
         'project', 'priority', '已有目标或具体行动，但尚未安排；不混入尚待澄清的想法。'),
        ('近期成果', {'state': {'name': {'eq': 'Done'}}, 'completedAt': {'gte': '-P14D'}},
         'project', 'updatedAt', '查看实际完成于最近十四天的成果；窗口随当前日期滚动。'),
    ]
    result = []
    for name, filters, grouping, ordering, description in specs:
        prefs = {'layout': 'list', 'issueGrouping': grouping, 'viewOrdering': ordering,
                 'fieldId': True, 'fieldStatus': True, 'fieldPriority': True,
                 'fieldProject': True, 'fieldLabels': True, 'showSubIssues': True,
                 'showCompletedIssues': 'all' if name == '近期成果' else 'none'}
        result.append({'name': name, 'description': description,
                       'filterData': {**copy.deepcopy(common), **filters}, 'preferences': prefs})
    return result


def list_views(client):
    return pages(client, '''query Views($after: String) {
      result: customViews(first: 100, after: $after, includeArchived: true) {
        nodes { ''' + VIEW_FIELDS + ''' } pageInfo { hasNextPage endCursor }
      } }''')


def get_view(client, view_id):
    return client('query View($id: String!) { customView(id: $id) { ' + VIEW_FIELDS + ' } }',
                  {'id': view_id})['customView']


def all_personal_preferences(client, view_id):
    """Read every exposed preference before updating owned keys only."""
    def selection(type_name):
        metadata = client('''query PreferenceShape($name:String!) {
          __type(name:$name){fields(includeDeprecated:true){name type{kind name ofType{kind name ofType{kind name}}}}}
        }''', {'name': type_name})['__type']
        fields = []
        for field in metadata['fields']:
            leaf = field['type']
            while leaf['kind'] in {'LIST', 'NON_NULL'}:
                leaf = leaf['ofType']
            if leaf['kind'] in {'SCALAR', 'ENUM'}:
                fields.append(field['name'])
            elif leaf['kind'] == 'OBJECT' and leaf['name'].startswith('ViewPreferences'):
                fields.append(field['name'] + ' {' + selection(leaf['name']) + '}')
            else:
                raise ViewError('Unknown preference shape; refusing a partial preference update.')
        return ' '.join(fields)
    if not hasattr(client, 'preference_selection'):
        client.preference_selection = selection('ViewPreferencesValues')
    result = client('query AllPreferences($id:String!){customView(id:$id){userViewPreferences{id preferences{' +
                    client.preference_selection + '}}}}', {'id': view_id})['customView']['userViewPreferences']
    if result is None:
        raise ViewError('Personal preferences disappeared before update; re-plan.')
    return result


def snapshot(client):
    viewer = client('query Identity { viewer { id name organization { id urlKey } } }')['viewer']
    if viewer['id'] != USER or viewer['organization']['urlKey'] != WORKSPACE:
        raise ViewError('API identity does not match the authorized personal workspace and owner.')
    labels = pages(client, '''query Labels($after: String, $team: ID!) {
      result: issueLabels(first:100, after:$after, filter:{team:{id:{eq:$team}}}) {
        nodes { id name } pageInfo {hasNextPage endCursor}
      } }''', {'team': TEAM})
    label_ids = {}
    for name in ['想法', '需求', '任务']:
        matches = [label for label in labels if label['name'] == name]
        if len(matches) != 1:
            raise ViewError('Missing or ambiguous team label: ' + name)
        label_ids[name] = matches[0]['id']
    return {'viewer': viewer, 'labels': label_ids, 'views': list_views(client)}


def plan_views(specs, existing):
    plan = []
    for spec in specs:
        matches = [v for v in existing if v['name'] == spec['name']]
        if len(matches) > 1:
            raise ViewError('Multiple same-name views; no automatic merge: ' + spec['name'])
        old = matches[0] if matches else None
        if old and (old['owner']['id'] != USER or old['modelName'] != 'Issue'
                    or old.get('archivedAt') or (old.get('team') and old['team']['id'] != TEAM)):
            raise ViewError('Existing same-name view has a different owner, scope or lifecycle: ' + spec['name'])
        action = 'create' if old is None else ('noop' if old['filterData'] == spec['filterData'] else 'update')
        plan.append({'name': spec['name'], 'action': action,
                     'id': old['id'] if old else None, 'before': old, 'spec': spec})
    return plan


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    os.replace(temporary, path)


def mutate(client, query, variables, field):
    result = client(query, variables)[field]
    if not result.get('success'):
        raise ViewError(field + ' did not report success; re-read before retrying.')
    return result


def apply_views(client, plan, state_path):
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    identities = state.setdefault('createIds', {})
    completed = []
    for item in plan:
        spec, view_id = item['spec'], item['id']
        if item['before']:
            current = get_view(client, view_id)
            if current['updatedAt'] != item['before']['updatedAt'] or current['filterData'] != item['before']['filterData']:
                raise ViewError('View changed after planning; re-plan: ' + item['name'])
        if item['action'] == 'create':
            view_id = identities.setdefault(item['name'], str(uuid.uuid4()))
            write_json(state_path, state)  # Keep identity before an uncertain network write.
            mutate(client, '''mutation CreateView($input:CustomViewCreateInput!) {
              customViewCreate(input:$input) { success customView { id } } }''',
                   {'input': {'id': view_id, 'name': spec['name'], 'description': spec['description'],
                              'filterData': spec['filterData'], 'ownerId': USER, 'shared': False}}, 'customViewCreate')
        elif item['action'] == 'update':
            mutate(client, '''mutation UpdateView($id:String!, $input:CustomViewUpdateInput!) {
              customViewUpdate(id:$id,input:$input) {success customView{id}} }''',
                   {'id': view_id, 'input': {'filterData': spec['filterData']}}, 'customViewUpdate')
        saved = get_view(client, view_id)
        if saved['filterData'] != spec['filterData']:
            raise ViewError('Saved filter does not match requested conditions: ' + spec['name'])
        preferences = saved.get('userViewPreferences')
        if not preferences or any(preferences['preferences'].get(k) != v for k, v in spec['preferences'].items()):
            if preferences:
                current_preferences = all_personal_preferences(client, view_id)
                if current_preferences['id'] != preferences['id']:
                    raise ViewError('Preference identity changed before update.')
                merged = {k: v for k, v in current_preferences['preferences'].items() if v is not None}
                merged.update(spec['preferences'])
                mutate(client, '''mutation Preferences($id:String!, $input:ViewPreferencesUpdateInput!) {
                  viewPreferencesUpdate(id:$id,input:$input){success viewPreferences{id}} }''',
                       {'id': preferences['id'], 'input': {'preferences': merged}}, 'viewPreferencesUpdate')
            else:
                mutate(client, '''mutation Preferences($input:ViewPreferencesCreateInput!) {
                  viewPreferencesCreate(input:$input){success viewPreferences{id}} }''',
                       {'input': {'customViewId': view_id, 'type': 'user', 'viewType': 'customView',
                                  'preferences': spec['preferences']}}, 'viewPreferencesCreate')
        saved = get_view(client, view_id)
        stored = (saved.get('userViewPreferences') or {}).get('preferences') or {}
        if any(stored.get(k) != v for k, v in spec['preferences'].items()):
            raise ViewError('Stored display preferences did not match: ' + spec['name'])
        # Keep computed-display differences visible in verify(), while completing
        # the independently verifiable filters and favorites of the other views.
        completed.append(saved)
        write_json(state_path, {**state, 'lastSavedViews': completed})
    return completed


def list_favorites(client):
    return pages(client, '''query Favorites($after:String) {
      result:favorites(first:100,after:$after) {
        nodes{id url sortOrder parent{id} customView{id} owner{id}}
        pageInfo{hasNextPage endCursor}
      } }''')


def ensure_favorites(client, views):
    favorites = list_favorites(client)
    if any(f['owner']['id'] != USER for f in favorites):
        raise ViewError('Favorite owner does not match the authenticated user.')
    targets = {view['id'] for view in views}
    other = [f for f in favorites if (f.get('customView') or {}).get('id') not in targets and not f.get('parent')]
    start = min([f['sortOrder'] for f in other] + [0]) - 1000 * len(views)
    for index, view in enumerate(views):
        matches = [f for f in favorites if (f.get('customView') or {}).get('id') == view['id']]
        if len(matches) > 1:
            raise ViewError('Multiple favorites for ' + view['name'] + '; preserved for review.')
        if not matches:
            mutate(client, '''mutation Favorite($input:FavoriteCreateInput!) {
              favoriteCreate(input:$input){success favorite{id}} }''',
                   {'input': {'customViewId': view['id'], 'sortOrder': start + index * 1000}}, 'favoriteCreate')
        elif matches[0].get('parent') or matches[0]['sortOrder'] != start + index * 1000:
            mutate(client, '''mutation OrderFavorite($id:String!, $input:FavoriteUpdateInput!) {
              favoriteUpdate(id:$id,input:$input){success favorite{id}} }''',
                   {'id': matches[0]['id'], 'input': {'parentId': None, 'sortOrder': start + index * 1000}}, 'favoriteUpdate')
    return list_favorites(client)


def local_membership(issues, name, now):
    result = set()
    for issue in issues:
        if (issue.get('assignee') or {}).get('id') != USER or issue['team']['id'] != TEAM:
            continue
        if issue['labels']['pageInfo']['hasNextPage']:
            raise ViewError('Issue label list incomplete; membership cannot be verified.')
        state = issue['state']['name']
        labels = {v['name'] for v in issue['labels']['nodes']}
        closed = issue['state']['type'] in {'completed', 'canceled', 'duplicate'}
        match = (
            (name == '现在推进' and state in {'Todo', 'In Progress'}) or
            (name == '等我确认' and state == 'In Review') or
            (name == '想法待澄清' and '想法' in labels and not closed) or
            (name == '以后安排' and state == 'Backlog' and bool(labels & {'需求', '任务'})) or
            (name == '近期成果' and state == 'Done' and issue.get('completedAt') and
             datetime.fromisoformat(issue['completedAt'].replace('Z', '+00:00')) >= now - timedelta(days=14)))
        if match:
            result.add(issue['identifier'])
    return result


def verify(client, specs, favorites=None):
    existing = list_views(client)
    plan = plan_views(specs, existing)
    if any(p['action'] != 'noop' for p in plan):
        raise ViewError('One or more views are absent or have different filters.')
    scope = {'team': {'id': {'eq': TEAM}}, 'assignee': {'id': {'eq': USER}}}
    issues = pages(client, '''query Scope($after:String,$filter:IssueFilter!) {
      result:issues(first:100,after:$after,filter:$filter) {
        nodes{''' + ISSUE_FIELDS + '''} pageInfo{hasNextPage endCursor}
      } }''', {'filter': scope})
    now = datetime.now(timezone.utc)
    favorites = list_favorites(client) if favorites is None else favorites
    root_favorites = sorted([f for f in favorites if not f.get('parent')], key=lambda f: f['sortOrder'])
    expected_order = [item['id'] for item in plan]
    actual_order = [(f.get('customView') or {}).get('id') for f in root_favorites[:len(plan)]]
    if actual_order != expected_order:
        raise ViewError('The five views are not the first sidebar favorites in the requested order.')
    results = []
    for item in plan:
        view, spec = item['before'], item['spec']
        members = pages(client, '''query ViewMembers($id:String!,$after:String) {
          customView(id:$id) { issues(first:100,after:$after) {
            nodes{id identifier} pageInfo{hasNextPage endCursor}
          } } }''', {'id': view['id']}, path=('customView', 'issues'))
        actual = {v['identifier'] for v in members}
        expected = local_membership(issues, spec['name'], now)
        if actual != expected:
            raise ViewError('Actual view membership differs for ' + spec['name'] + ': ' + repr(sorted(actual ^ expected)))
        favorite = [f for f in favorites if (f.get('customView') or {}).get('id') == view['id']]
        if len(favorite) != 1 or favorite[0]['owner']['id'] != USER or favorite[0].get('parent'):
            raise ViewError('Sidebar favorite missing or ambiguous: ' + spec['name'])
        if not isinstance(favorite[0].get('url'), str) or not favorite[0]['url'].startswith('https://linear.app/' + WORKSPACE + '/'):
            raise ViewError('Favorite URL is absent or outside the expected workspace.')
        effective = view.get('viewPreferencesValues') or {}
        stored = (view.get('userViewPreferences') or {}).get('preferences') or {}
        if any(stored.get(k) != v for k, v in spec['preferences'].items()):
            raise ViewError('Stored display preferences changed: ' + spec['name'])
        differences = {k: {'requested': v, 'effective': effective.get(k)}
                       for k, v in spec['preferences'].items() if effective.get(k) != v}
        results.append({'name': spec['name'], 'id': view['id'], 'url': favorite[0]['url'],
                        'issues': sorted(actual), 'filterVerified': True, 'membershipVerified': True,
                        'favoriteId': favorite[0]['id'], 'sortOrder': favorite[0]['sortOrder'],
                        'preferences': effective, 'storedPreferencesVerified': True,
                        'effectivePreferencesVerified': not differences, 'displayDifferences': differences})
    return {'verifiedAt': now.isoformat(), 'views': results, 'filtersAndMembershipVerified': True,
            'favoritesAndOrderVerified': True,
            'effectivePreferencesVerified': all(v['effectivePreferencesVerified'] for v in results),
            'defaultHome': {'changed': False, 'verified': False,
                            'reason': 'Public UserSettings does not expose a readable personal default-home field.'},
            'uiVerified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'apply', 'verify'])
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--runtime', type=Path, default=Path('.derived/linear/native-views'))
    args = parser.parse_args()
    try:
        client = Client(credential(args.key_file))
        before = snapshot(client)
        specs = definitions(before['labels'])
        plan = plan_views(specs, before['views'])
        run = args.runtime / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
        write_json(run / 'before.json', before)
        write_json(run / 'plan.json', plan)
        if args.command == 'plan':
            result = {'plan': str(run / 'plan.json'), 'views': [{'name': p['name'], 'action': p['action'], 'id': p['id']} for p in plan]}
        else:
            if args.command == 'apply':
                views = apply_views(client, plan, args.runtime / 'state.json')
                ensure_favorites(client, views)
            result = verify(client, specs)
            write_json(run / 'verified.json', result)
            result['evidence'] = str(run / 'verified.json')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ViewError as error:
        print(json.dumps({'error': str(error), 'verified': False}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
