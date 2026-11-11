"""Enemy catalog and stage descriptions for the merged battle GUI.

Run from the project root:
    python -m unittest discover -s tests -p "test_battle_backend_requests.py" -v

Only temporary databases are used; the player's saves/game.db is untouched.
"""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from roc import GameBridge, GameService
from roc import battle as B
from roc import config as C


ROOT = Path(__file__).resolve().parent.parent


class FakeClock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def __call__(self):
        return self.value


class ReliableRandom(random.Random):
    def random(self):
        return .99


class BattleBackendRequestTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root / 'game.db'
        self.clock = FakeClock()
        self.game = self.new_game(self.path)
        catalog = json.loads((ROOT / 'data' / 'enemies.json').read_text(encoding='utf-8'))
        self.bosses = {entry['stage']: entry for entry in catalog['bosses']}
        self.minions = {entry['id']: entry for entry in catalog['minions']}

    def new_game(self, path):
        return GameService(path, now=self.clock, rng=ReliableRandom(7))

    def test_every_stage_has_its_catalog_boss_and_two_catalog_minions(self):
        for stage in C.STAGE_ORDER:
            with self.subTest(stage=stage):
                preview = self.game.preview_stage(stage)
                enemies = preview['enemy']
                self.assertEqual(len(enemies), 3)
                self.assertEqual([e['id'] for e in enemies], ['enemy_0', 'enemy_1', 'enemy_2'])
                self.assertEqual([e['boss'] for e in enemies], [True, False, False])
                expected = [self.bosses[stage]] + [self.minions[e['species']] for e in enemies[1:]]
                for enemy, source in zip(enemies, expected):
                    self.assertEqual(enemy['species'], source['id'])
                    for field in ('name', 'sprite', 'role', 'element'):
                        self.assertEqual(enemy[field], source[field])
                    self.assertTrue((ROOT / enemy['sprite']).is_file())
                    self.assertEqual(enemy['stats'],
                                     {stat: C.STAGES[stage]['power'] for stat in C.STATS})

    def test_preview_and_started_battle_agree_for_all_stages(self):
        for stage in C.STAGE_ORDER:
            with self.subTest(stage=stage):
                game = self.new_game(self.root / (stage + '.db'))
                game._mutate(lambda s: s.update(progress=8))
                team = list(game.state['animals'])
                preview = game.preview_stage(stage)
                battle = game.start_battle(stage, team)
                self.assertEqual([f['id'] for f in battle['player']], team)
                for shown, actual in zip(preview['enemy'], battle['enemy']):
                    for field in ('id', 'species', 'name', 'sprite', 'boss',
                                  'role', 'element', 'stats'):
                        self.assertEqual(shown[field], actual[field])
                    self.assertEqual(actual['hp'], actual['stats']['hp'])
                self.assertEqual(game.get_snapshot()['last_team'], team)

    def test_previews_are_stable_across_reads_and_reopening(self):
        before = {stage: self.game.preview_stage(stage) for stage in C.STAGE_ORDER}
        self.game.get_game_state()
        self.game.get_snapshot()
        reopened = self.new_game(self.path)
        for stage in C.STAGE_ORDER:
            with self.subTest(stage=stage):
                self.assertEqual(before[stage], reopened.preview_stage(stage))

    def test_enemy_identity_and_boss_flags_survive_active_battle_restart(self):
        team = list(self.game.state['animals'])
        battle = self.game.start_battle('tutorial', team)
        reopened = self.new_game(self.path)
        self.assertEqual(reopened.get_battle(), battle)
        self.assertEqual(reopened.get_snapshot()['battle']['enemy'], battle['enemy'])

    def test_lookahead_counters_with_minions_without_replacing_stage_boss(self):
        for stage in ('extreme', 'diamond'):
            for previous_role in C.ROLES:
                with self.subTest(stage=stage, previous_role=previous_role):
                    self.game._mutate(lambda s, role=previous_role:
                                      s.update(last_team_roles=[role] * 3))
                    enemies = self.game.preview_stage(stage)['enemy']
                    self.assertEqual(enemies[0]['species'], self.bosses[stage]['id'])
                    previous_element = C.ROLE_ELEMENTS[previous_role]
                    counter = next(element for element, beaten in C.ELEMENT_BEATS.items()
                                   if beaten == previous_element)
                    self.assertEqual([e['element'] for e in enemies[1:]], [counter, counter])

    def test_preview_mutations_do_not_change_catalog_or_player_data(self):
        before = self.game.preview_stage('tutorial')
        players = copy.deepcopy(self.game.state['animals'])
        changed = self.game.preview_stage('tutorial')
        changed['enemy'][0].update(name='changed', boss=False, species='changed')
        changed['enemy'][0]['stats']['hp'] = 999999
        changed['enemy'].pop()
        self.assertEqual(self.game.preview_stage('tutorial'), before)
        self.assertEqual(self.game.state['animals'], players)

    def test_stage_ai_descriptions_match_profiles_in_every_public_view(self):
        stages = self.game.get_stages()
        snapshot_stages = self.game.get_snapshot()['stages']
        self.assertEqual([s['id'] for s in stages], list(C.STAGE_ORDER))
        self.assertEqual(stages, snapshot_stages)
        for stage in stages:
            with self.subTest(stage=stage['id']):
                expected = B.AI_PROFILES[stage['ai']]['summary']
                self.assertEqual(stage['ai_description'], expected)
                self.assertTrue(expected.strip())
                self.assertNotIn('\n', expected)
                self.assertEqual(self.game.preview_stage(stage['id'])['ai_description'], expected)
                for field, value in C.STAGES[stage['id']].items():
                    self.assertEqual(stage[field], value)

    def test_bridge_exposes_json_friendly_enemy_and_stage_metadata(self):
        bridge = GameBridge(self.game)
        for command, params in (('preview_stage', {'stage': 'tutorial'}),
                                ('get_stages', {}), ('get_snapshot', {})):
            with self.subTest(command=command):
                result = bridge.call(command, **params)
                self.assertTrue(result['ok'], result)
                self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
                if command == 'preview_stage':
                    self.assertEqual(result['data']['enemy'][0]['species'], 'boss_tutorial')
                    self.assertTrue(result['data']['enemy'][0]['boss'])
                else:
                    stages = result['data'] if command == 'get_stages' else result['data']['stages']
                    self.assertTrue(all(stage['ai_description'] for stage in stages))

    def test_invalid_enemy_catalog_is_rejected_instead_of_building_wrong_teams(self):
        original = json.loads((ROOT / 'data' / 'enemies.json').read_text(encoding='utf-8'))
        for invalid in ('missing_boss', 'duplicate_id', 'bad_element',
                        'missing_role', 'invalid_stage_type'):
            with self.subTest(invalid=invalid):
                data = copy.deepcopy(original)
                if invalid == 'missing_boss':
                    data['bosses'].pop()
                elif invalid == 'duplicate_id':
                    data['minions'][1]['id'] = data['minions'][0]['id']
                elif invalid == 'bad_element':
                    data['minions'][0]['element'] = 'water'
                elif invalid == 'missing_role':
                    data['minions'] = [e for e in data['minions'] if e['role'] != 'healer']
                else:
                    data['bosses'][0]['stage'] = []
                path = self.root / 'invalid-enemies.json'
                path.write_text(json.dumps(data), encoding='utf-8')
                with self.assertRaises(ValueError):
                    GameService._load_enemies(path)


if __name__ == '__main__':
    unittest.main()
