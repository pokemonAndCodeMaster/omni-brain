import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from scripts import linear_views as app


class FakeClient:
    def __init__(self):
        self.views = {}
        self.favorites = []
        self.creates = []
        self.lose_create_response = False

    def __call__(self, query, variables=None):
        variables = variables or {}
        if 'customViewCreate(' in query:
            data = variables['input']
            self.creates.append(data['id'])
            if data['id'] not in self.views:
                self.views[data['id']] = {
                    **data, 'updatedAt': 'version1', 'owner': {'id': app.USER}, 'modelName': 'Issue',
                    'team': None, 'archivedAt': None, 'slugId': 'slug', 'userViewPreferences': None,
                    'organization': {'urlKey': app.WORKSPACE}, 'viewPreferencesValues': {}}
            if self.lose_create_response:
                self.lose_create_response = False
                raise app.ViewError('response lost after write')
            return {'customViewCreate': {'success': True, 'customView': {'id': data['id']}}}
        if 'viewPreferencesCreate(' in query:
            data = variables['input']
            view = self.views[data['customViewId']]
            view['userViewPreferences'] = {'id': 'pref-' + view['id'], 'preferences': copy.deepcopy(data['preferences'])}
            view['viewPreferencesValues'] = copy.deepcopy(data['preferences'])
            return {'viewPreferencesCreate': {'success': True}}
        if 'query PreferenceShape' in query:
            names = app.PREF_FIELDS.split() + ['fieldAssignee', 'fieldCycle']
            if 'includeDeprecated:true' in query:
                names.append('projectGroupOrdering')
            return {'__type': {'fields': [
                {'name': name, 'type': {'kind': 'SCALAR', 'name': 'String'}}
                for name in names
            ]}}
        if 'query AllPreferences' in query:
            view = copy.deepcopy(self.views[variables['id']])
            prefs = view['userViewPreferences']['preferences']
            view['userViewPreferences']['preferences'] = {
                k: v for k, v in prefs.items() if re.search(r'\b' + re.escape(k) + r'\b', query)}
            return {'customView': view}
        if 'viewPreferencesUpdate(' in query:
            view = next(v for v in self.views.values()
                        if v['userViewPreferences']['id'] == variables['id'])
            view['userViewPreferences']['preferences'] = copy.deepcopy(variables['input']['preferences'])
            view['viewPreferencesValues'] = copy.deepcopy(variables['input']['preferences'])
            return {'viewPreferencesUpdate': {'success': True}}
        if 'favoriteCreate(' in query:
            data = variables['input']
            self.favorites.append({**data, 'id': 'favorite-' + data['customViewId'],
                                   'customView': {'id': data['customViewId']}, 'parent': None,
                                   'owner': {'id': app.USER},
                                   'url': 'https://linear.app/' + app.WORKSPACE + '/view/' + data['customViewId']})
            return {'favoriteCreate': {'success': True}}
        if 'favoriteUpdate(' in query:
            target = next(f for f in self.favorites if f['id'] == variables['id'])
            target['sortOrder'] = variables['input']['sortOrder']
            target['parent'] = None
            return {'favoriteUpdate': {'success': True}}
        if 'result:favorites(' in query:
            return {'result': {'nodes': copy.deepcopy(self.favorites), 'pageInfo': {'hasNextPage': False}}}
        if 'customView(id:' in query:
            return {'customView': copy.deepcopy(self.views[variables['id']])}
        raise AssertionError(query)


class ViewTests(unittest.TestCase):
    def specs(self):
        return app.definitions({'想法': 'idea-label', '需求': 'requirement-label', '任务': 'task-label'})

    def test_lost_response_recovers_existing_identity_without_duplicate(self):
        fake = FakeClient()
        fake.lose_create_response = True
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / 'state.json'
            with self.assertRaises(app.ViewError):
                app.apply_views(fake, app.plan_views(self.specs()[:1], []), state)
            saved_id = json.loads(state.read_text())['createIds']['现在推进']
            plan = app.plan_views(self.specs()[:1], list(fake.views.values()))
            saved = app.apply_views(fake, plan, state)
            self.assertEqual(saved[0]['id'], saved_id)
            self.assertEqual(len(fake.creates), 1)

    def test_five_views_idempotent_and_favorites_reordered_without_recreation(self):
        fake = FakeClient()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            views = app.apply_views(fake, app.plan_views(self.specs(), []), path)
            app.ensure_favorites(fake, views)
            ids = [f['id'] for f in fake.favorites]
            for index, f in enumerate(fake.favorites):
                f['sortOrder'] = 100 - index
                f['parent'] = {'id': 'old-folder'}
            plan = app.plan_views(self.specs(), list(fake.views.values()))
            views = app.apply_views(fake, plan, path)
            favorites = app.ensure_favorites(fake, views)
            self.assertEqual(len(fake.creates), 5)
            self.assertEqual([f['id'] for f in favorites], ids)
            self.assertTrue(all(f['parent'] is None for f in favorites))
            self.assertEqual([f['customView']['id'] for f in sorted(favorites, key=lambda f: f['sortOrder'])],
                             [v['id'] for v in views])

    def test_scope_and_collision_refused_before_mutation(self):
        spec = self.specs()[0]
        old = {'id': 'existing', 'name': spec['name'], 'owner': {'id': app.USER},
               'modelName': 'Issue', 'team': None, 'archivedAt': None, 'filterData': spec['filterData']}
        self.assertEqual(app.plan_views([spec], [old])[0]['action'], 'noop')
        with self.assertRaises(app.ViewError):
            app.plan_views([spec], [old, dict(old, id='duplicate')])
        for changes in [{'owner': {'id': 'other'}}, {'modelName': 'Project'},
                        {'team': {'id': 'other-team'}}, {'archivedAt': 'yesterday'}]:
            with self.assertRaises(app.ViewError):
                app.plan_views([spec], [{**old, **changes}])

    def test_views_changed_since_plan_are_not_overwritten(self):
        fake = FakeClient()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            app.apply_views(fake, app.plan_views(self.specs()[:1], []), path)
            plan = app.plan_views(self.specs()[:1], copy.deepcopy(list(fake.views.values())))
            next(iter(fake.views.values()))['updatedAt'] = 'newer'
            with self.assertRaises(app.ViewError):
                app.apply_views(fake, plan, path)

    def test_preference_update_preserves_exposed_unowned_values(self):
        fake = FakeClient()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'state.json'
            app.apply_views(fake, app.plan_views(self.specs()[:1], []), path)
            view = next(iter(fake.views.values()))
            view['userViewPreferences']['preferences'].update(
                layout='board', fieldAssignee=False, viewOrderingDirection='descending',
                fieldCycle=None, projectGroupOrdering='name')
            plan = app.plan_views(self.specs()[:1], copy.deepcopy(list(fake.views.values())))
            saved = app.apply_views(fake, plan, path)[0]['userViewPreferences']['preferences']
            self.assertEqual(saved['layout'], 'list')
            self.assertIs(saved['fieldAssignee'], False)
            self.assertEqual(saved['viewOrderingDirection'], 'descending')
            self.assertEqual(saved['projectGroupOrdering'], 'name')
            self.assertNotIn('fieldCycle', saved)  # Null means unset, not an owned value.

    def test_membership_distinguishes_idea_backlog_review_and_actual_completion(self):
        now = datetime(2026, 9, 13, tzinfo=timezone.utc)
        def issue(identifier, state, kind, labels=(), days=None):
            return {'id': identifier, 'identifier': identifier, 'assignee': {'id': app.USER},
                    'team': {'id': app.TEAM}, 'state': {'name': state, 'type': kind},
                    'labels': {'nodes': [{'name': x} for x in labels], 'pageInfo': {'hasNextPage': False}},
                    'completedAt': (now - timedelta(days=days)).isoformat() if days is not None else None,
                    'updatedAt': now.isoformat()}
        issues = [issue('idea', 'In Progress', 'started', ['想法']),
                  issue('later', 'Backlog', 'backlog', ['任务']),
                  issue('review', 'In Review', 'started', ['需求']),
                  issue('recent', 'Done', 'completed', ['任务'], 14),
                  issue('old-edited-today', 'Done', 'completed', ['任务'], 15),
                  issue('duplicate-idea', 'Duplicate', 'duplicate', ['想法'])]
        self.assertEqual(app.local_membership(issues, '现在推进', now), {'idea'})
        self.assertEqual(app.local_membership(issues, '等我确认', now), {'review'})
        self.assertEqual(app.local_membership(issues, '想法待澄清', now), {'idea'})
        self.assertEqual(app.local_membership(issues, '以后安排', now), {'later'})
        self.assertEqual(app.local_membership(issues, '近期成果', now), {'recent'})
        self.assertEqual(self.specs()[-1]['filterData']['completedAt'], {'gte': '-P14D'})

    def test_pagination_is_complete_or_rejected(self):
        replies = [ {'result': {'nodes': [{'id': 'one'}], 'pageInfo': {'hasNextPage': True, 'endCursor': 'c'}}},
                    {'result': {'nodes': [{'id': 'two'}], 'pageInfo': {'hasNextPage': False}}} ]
        self.assertEqual([x['id'] for x in app.pages(lambda *a: replies.pop(0), 'query')], ['one', 'two'])
        repeated = {'result': {'nodes': [], 'pageInfo': {'hasNextPage': True, 'endCursor': 'loop'}}}
        with self.assertRaises(app.ViewError):
            app.pages(lambda *a: repeated, 'query')

    def test_private_key_and_symlink_boundary(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {}, clear=True):
            target = Path(tmp) / 'key'
            target.write_text('test-key')
            target.chmod(0o600)
            self.assertEqual(app.credential(target), 'test-key')
            target.chmod(0o644)
            with self.assertRaises(app.ViewError): app.credential(target)
            target.chmod(0o600)
            link = Path(tmp) / 'link'
            link.symlink_to(target)
            with self.assertRaises(app.ViewError): app.credential(link)

    def test_graphql_partial_error_redacts_credential_and_does_not_retry(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'data': {}, 'errors': [{'message': 'bad secret-key'}]}).encode()
        client = app.Client('secret-key')
        with patch.object(client.opener, 'open', return_value=Response()) as call:
            with self.assertRaises(app.ViewError) as raised: client('query {}')
            self.assertNotIn('secret-key', str(raised.exception))
            self.assertEqual(call.call_count, 1)
        self.assertIsNone(app.NoRedirect().redirect_request(None))

    def test_transient_reads_retry_but_uncertain_writes_do_not(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"data":{"viewer":{"id":"expected"}}}'
        client = app.Client('secret-key')
        failure = urllib.error.URLError(OSError('connection interrupted'))
        with patch.object(client.opener, 'open', side_effect=[failure, Response()]) as call:
            self.assertEqual(client('query Identity { viewer { id } }')['viewer']['id'], 'expected')
            self.assertEqual(call.call_count, 2)
        with patch.object(client.opener, 'open', side_effect=failure) as call:
            with self.assertRaisesRegex(app.ViewError, 'write outcome unknown'):
                client('mutation CreateView { customViewCreate { success } }')
            self.assertEqual(call.call_count, 1)
        with patch.object(client.opener, 'open', side_effect=failure) as call:
            with self.assertRaisesRegex(app.ViewError, 'read failed'):
                client('query Identity { viewer { id } }')
            self.assertEqual(call.call_count, 3)


if __name__ == '__main__':
    unittest.main()
