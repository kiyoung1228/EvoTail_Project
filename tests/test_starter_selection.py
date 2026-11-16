"""새 게임 시작 동물 선택과 잘못된 선택의 원자적 거절을 검증한다.

임시 세이브만 사용하며 플레이어의 saves/game.db는 열지 않는다.
"""
import copy
import itertools
import json
import random
import tempfile
import unittest
from pathlib import Path

from roc import GameBridge, GameRuleError, GameService
from roc import config as C


class Clock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def __call__(self):
        return self.value


class ReliableRandom(random.Random):
    def random(self):
        return .99


class StarterSelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'game.db'
        self.clock = Clock()
        self.game = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.normal = [key for key, animal in self.game.characters.items()
                       if animal['rarity'] == 'normal']
        self.special = [key for key, animal in self.game.characters.items()
                        if animal['rarity'] == 'special']
        self.default = [next(key for key in self.normal if self.game.characters[key]['role'] == role)
                        for role in C.ROLES]
        self.expected_result = {'reset':True, 'coins':300, 'animals':3, 'plots':1}

    def assert_selected(self, selected, game=None):
        game = game or self.game
        animals = game.get_animals()
        self.assertEqual([a['id'] for a in animals], list(selected))
        self.assertEqual(len(animals), 3)
        for animal in animals:
            info = game.characters[animal['id']]
            self.assertEqual(info['rarity'], 'normal')
            self.assertEqual(animal['stage'], 1)
            self.assertEqual(animal['stats'], info['base_stats'])
            self.assertEqual((animal['fullness'], animal['mood'], animal['fatigue']), (80, 80, 0))
            self.assertFalse(animal['sick'])
            self.assertIsNone(animal['activity'])
            self.assertIsNone(animal['equip'])
        self.assertEqual(game.get_game_state()['owned_count'], 3)

    def dirty_progress(self):
        """육성·사냥·전투·밭과 기존 이벤트가 있는 진행 상태를 준비한다."""
        def prepare(s):
            extra = [key for key in self.normal if key not in s['animals']][:3]
            for key in extra:
                s['animals'][key] = self.game._new_animal(key, s['clock']['virtual'])
            for animal in s['animals'].values():
                animal.update(nature='balanced')
            s.update(coins=9000, progress=0, rank='bronze', cook_xp=300,
                     cleared=['tutorial'], claimed_ranks=['bronze'], achievements=['first_training'])
            s['yard'] = list(self.default)
            s['jobs'] = {'old_job':{'kind':'old'}}
            s['counters'] = {'trainings_completed':2}
            s['battle_result'] = {'stage':'tutorial', 'win':True}
            self.game._emit(s, 'previous_progress')
        self.game._mutate(prepare)
        self.game.buy_item('toy_ball')
        self.game.buy_item('seed_potato')
        self.game.expand_plot()
        self.game.plant_crop(0, 'potato')
        self.game.start_training(self.default[0], 'attack', 'easy')
        self.game.start_hunting(self.default[1], 'chicken_coop')
        extra = [key for key in self.game.state['animals'] if key not in self.default]
        self.game.start_battle('tutorial', extra)
        self.assertTrue(self.game.store.recent_events())

    def assert_unchanged_after_rejection(self, starters, confirm=True):
        before = copy.deepcopy(self.game.state)
        saved = self.game.store.load_with_revision()
        history = self.game.store.recent_events(5000)
        rng_state = self.game.rng.getstate()
        response = GameBridge(self.game).call('reset_game', confirm=confirm, starters=starters)
        self.assertFalse(response['ok'])
        self.assertIsNone(response['data'])
        self.assertEqual(response['error']['code'], 'RULE_REJECTED')
        self.assertTrue(response['error']['message'])
        self.assertEqual(self.game.state, before)
        self.assertEqual(self.game.store.load_with_revision(), saved)
        self.assertEqual(self.game.store.recent_events(5000), history)
        self.assertEqual(self.game.rng.getstate(), rng_state)

    def test_omitted_and_none_starters_keep_default_animals_and_result_shape(self):
        self.assert_selected(self.default)
        for params in ({'confirm':True}, {'confirm':True, 'starters':None}):
            with self.subTest(params=params):
                result = self.game.reset_game(**params)
                self.assertEqual(result, self.expected_result)
                self.assert_selected(self.default)

    def test_same_role_teams_are_allowed_for_every_role(self):
        for role in C.ROLES:
            with self.subTest(role=role):
                selected = [key for key in self.normal if self.game.characters[key]['role'] == role][:3]
                self.assertEqual(self.game.reset_game(confirm=True, starters=selected), self.expected_result)
                self.assert_selected(selected)

    def test_explicit_order_and_base_stats_survive_restart(self):
        selected = [self.normal[-1], self.normal[4], self.normal[1]]
        self.game.reset_game(confirm=True, starters=selected)
        self.assert_selected(selected)
        restored = GameService(self.path, now=self.clock, rng=ReliableRandom(9))
        self.assert_selected(selected, restored)
        self.assertEqual(list(restored.store.load()['animals']), selected)

    def test_selected_starters_do_not_alias_callers_list(self):
        selected = self.normal[1:4]
        expected = list(selected)
        self.game.reset_game(confirm=True, starters=selected)
        selected.clear()
        selected.extend(self.normal[-3:])
        self.assert_selected(expected)

    def test_bridge_accepts_selected_starters_and_json_result(self):
        selected = self.normal[-3:]
        response = GameBridge(self.game).call('reset_game', confirm=True, starters=selected)
        self.assertEqual(response, {'ok':True, 'data':self.expected_result, 'error':None})
        self.assertEqual(json.loads(json.dumps(response)), response)
        self.assert_selected(selected)

    def test_selected_starters_reset_all_previous_progress_and_history(self):
        self.dirty_progress()
        self.clock.value += 123
        selected = self.normal[-3:]
        self.game.reset_game(confirm=True, starters=selected)
        self.assert_selected(selected)
        state = self.game.state
        expected = {
            'coins':300, 'inventory':{'snack':3}, 'toy_instances':[],
            'plots':[{'crop':None, 'end':None, 'ready':False}],
            'hunts':{}, 'jobs':{}, 'battle':None, 'battle_result':None,
            'battle_attempts':{}, 'last_team_roles':[], 'last_team':[],
            'yard':[], 'progress':-1, 'cleared':[], 'rank':'none',
            'claimed_ranks':[], 'cook_xp':0, 'events':[], 'event_seq':0,
            'achievements':[], 'counters':{},
        }
        for key, value in expected.items():
            with self.subTest(field=key):
                self.assertEqual(state[key], value)
        self.assertEqual(state['clock'], {'virtual':self.clock.value,
                                          'last_real':self.clock.value, 'rate':1.0})
        self.assertEqual(state['created'], self.clock.value)
        self.assertEqual(state['last_saved'], self.clock.value)
        self.assertEqual(self.game.store.recent_events(5000), [])
        self.assertEqual(self.game.store.load(), state)
        self.assertEqual(self.game.get_snapshot()['training_count'], 0)

    def test_invalid_selection_preserves_state_disk_history_and_rng(self):
        self.dirty_progress()
        good = self.normal[:3]
        invalid = [
            [], good[:1], good[:2], self.normal[:4],
            [good[0], good[0], good[1]],
            ['missing_animal', good[1], good[2]],
            self.special[:3], [good[0], self.special[0], good[2]],
            [None, good[1], good[2]], [1, good[1], good[2]], [True, good[1], good[2]],
            [[], good[1], good[2]], [{}, good[1], good[2]],
            good[0], 3, True, 3.0, set(good), {key:True for key in good},
        ]
        for selected in invalid:
            with self.subTest(selected=selected):
                self.assert_unchanged_after_rejection(selected)

    def test_invalid_selection_raises_game_rule_error_for_direct_callers(self):
        for selected in ([self.normal[0]] * 3, [[], self.normal[1], self.normal[2]], self.special[:3]):
            with self.subTest(selected=selected), self.assertRaises(GameRuleError):
                self.game.reset_game(confirm=True, starters=selected)

    def test_valid_selection_still_requires_explicit_confirmation(self):
        self.dirty_progress()
        for confirm in (False, None, 1, 'true'):
            with self.subTest(confirm=confirm):
                self.assert_unchanged_after_rejection(self.normal[:3], confirm=confirm)

    def test_all_455_normal_species_combinations_can_start_a_game(self):
        self.assertEqual(len(self.normal), 15)
        checked = 0
        for selected in itertools.combinations(self.normal, 3):
            with self.subTest(selected=selected):
                result = self.game.reset_game(confirm=True, starters=list(selected))
                self.assertEqual(result, self.expected_result)
                self.assertEqual(list(self.game.state['animals']), list(selected))
                self.assertTrue(all(a['stage'] == 1 for a in self.game.state['animals'].values()))
            checked += 1
        self.assertEqual(checked, 455)


if __name__ == '__main__':
    unittest.main()
