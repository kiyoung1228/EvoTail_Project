"""PC 시계 역행 복구와 훈련장 동시 이용 제한을 검증한다.

임시 세이브만 사용하며 플레이어의 saves/game.db는 열지 않는다.
"""
import copy
import json
import random
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

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


class ClockTrainingLimitTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'game.db'
        self.clock = Clock()
        self.game = GameService(self.path, now=self.clock, rng=ReliableRandom(7))

        def prepare(s):
            extra = [key for key in self.game.characters if key not in s['animals']][:3]
            for key in extra:
                s['animals'][key] = self.game._new_animal(key, s['clock']['virtual'])
            for animal in s['animals'].values():
                animal.update(nature='balanced', fullness=100, mood=100, fatigue=0, sick=False)
        self.game._mutate(prepare)
        self.ids = list(self.game.state['animals'])

    def start(self, key, difficulty='easy'):
        return self.game.start_training(key, 'attack', difficulty)

    def count(self, game=None):
        state = (game or self.game).state
        return sum(bool(a['activity'] and a['activity']['kind'] == 'training')
                   for a in state['animals'].values())

    def assert_capacity_rejected_without_changes(self, key):
        before = copy.deepcopy(self.game.state)
        saved, revision = self.game.store.load_with_revision()
        response = GameBridge(self.game).call('start_training', key=key,
                                              stat='attack', difficulty='easy')
        self.assertFalse(response['ok'])
        self.assertIsNone(response['data'])
        self.assertEqual(response['error']['code'], 'RULE_REJECTED')
        self.assertIn('훈련장', response['error']['message'])
        self.assertEqual(self.game.state, before)
        self.assertEqual(self.game.store.load_with_revision(), (saved, revision))

    def assert_counts(self, expected, maximum=3, game=None):
        game = game or self.game
        for command in ('get_game_state', 'get_snapshot', 'get_active_jobs'):
            with self.subTest(command=command):
                response = GameBridge(game).call(command)
                self.assertTrue(response['ok'], response)
                fields = {key:response['data'][key]
                          for key in ('training_count', 'training_max_concurrent')}
                self.assertEqual(fields, {'training_count':expected,
                                          'training_max_concurrent':maximum})
                self.assertEqual(json.loads(json.dumps(fields)), fields)
        self.assertEqual(self.count(game), expected)

    def test_three_starts_and_fourth_rejection_are_atomic(self):
        self.assertEqual(C.TRAINING_MAX_CONCURRENT, 3)
        for count, key in enumerate(self.ids[:3], start=1):
            result = self.start(key)
            self.assertEqual(result['training_count'], count)
            self.assertEqual(result['training_max_concurrent'], 3)
        self.assert_capacity_rejected_without_changes(self.ids[3])
        self.assert_counts(3)

    def test_count_and_limit_views_are_independent_and_json_friendly(self):
        self.start(self.ids[0])
        self.start(self.ids[1])
        self.assert_counts(2)
        rules = self.game.get_rules()
        self.assertEqual(rules['training_max_concurrent'], 3)
        self.assertEqual(rules['training'], C.TRAINING)
        rules['training_max_concurrent'] = 100
        jobs = self.game.get_active_jobs()
        jobs['animal_jobs'][0]['kind'] = 'changed'
        snapshot = self.game.get_snapshot()
        snapshot['training_count'] = 0
        snapshot['animals'][0]['activity'] = None
        self.assert_counts(2)
        self.assertEqual(self.game.get_rules()['training_max_concurrent'], 3)

    def test_cancel_frees_one_slot_and_reports_current_counts(self):
        for key in self.ids[:3]:
            self.start(key)
        result = self.game.cancel_training(self.ids[1])
        self.assertTrue(result['cancelled'])
        self.assertEqual(result['reward'], 0)
        self.assertEqual(result['training_count'], 2)
        self.assertEqual(result['training_max_concurrent'], 3)
        self.start(self.ids[3])
        self.assert_counts(3)

    def test_due_completion_frees_slots_before_new_start(self):
        before = {key:self.game.state['animals'][key]['stats']['attack'] for key in self.ids[:3]}
        for key in self.ids[:3]:
            self.start(key)
        self.clock.value += 600
        self.start(self.ids[3])
        self.assert_counts(1)
        for key in self.ids[:3]:
            animal = self.game.state['animals'][key]
            self.assertIsNone(animal['activity'])
            self.assertEqual(animal['stats']['attack'], before[key] + 10)
        self.assertEqual(self.game.get_statistics()['trainings_completed'], 3)

    def test_hunting_does_not_use_training_slots(self):
        self.game.start_hunting(self.ids[0], 'chicken_coop')
        for key in self.ids[1:4]:
            self.start(key)
        self.assert_counts(3)
        self.assertEqual(len(self.game.get_active_jobs()['animal_jobs']), 4)
        self.assert_capacity_rejected_without_changes(self.ids[4])

    def test_simultaneous_requests_cannot_exceed_capacity(self):
        barrier = threading.Barrier(len(self.ids))

        def request(key):
            barrier.wait(timeout=5)
            try:
                self.start(key)
                return True
            except GameRuleError as exc:
                self.assertIn('훈련장', str(exc))
                return False

        with ThreadPoolExecutor(max_workers=len(self.ids)) as executor:
            results = list(executor.map(request, self.ids))
        self.assertEqual(results.count(True), 3)
        self.assertEqual(results.count(False), 3)
        self.assert_counts(3)
        stored = self.game.store.load()
        self.assertEqual(sum(bool(a['activity'] and a['activity']['kind'] == 'training')
                             for a in stored['animals'].values()), 3)

    def test_rules_and_enforcement_share_configured_limit(self):
        with patch.object(C, 'TRAINING_MAX_CONCURRENT', 2):
            self.assertEqual(self.game.get_rules()['training_max_concurrent'], 2)
            self.start(self.ids[0])
            self.start(self.ids[1])
            self.assert_capacity_rejected_without_changes(self.ids[2])
            self.assert_counts(2, maximum=2)

    def test_old_save_above_limit_keeps_jobs_and_blocks_new_starts(self):
        # 이전 버전에서 네 마리가 훈련 중이었던 세이브를 재현한다.
        with patch.object(C, 'TRAINING_MAX_CONCURRENT', 4):
            for key in self.ids[:4]:
                self.start(key)
        jobs = {key:copy.deepcopy(self.game.state['animals'][key]['activity'])
                for key in self.ids[:4]}
        self.game = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.assert_counts(4)
        self.assertEqual({key:self.game.state['animals'][key]['activity'] for key in self.ids[:4]}, jobs)
        self.assert_capacity_rejected_without_changes(self.ids[4])
        self.game.cancel_training(self.ids[0])
        self.assert_capacity_rejected_without_changes(self.ids[4])
        self.game.cancel_training(self.ids[1])
        self.start(self.ids[4])
        self.assert_counts(3)

    def test_clock_rollback_does_not_freeze_training_for_an_hour(self):
        key = self.ids[0]
        before = self.game.state['animals'][key]['stats']['attack']
        original_virtual = self.game.state['clock']['virtual']
        self.start(key)
        self.clock.value -= 3600
        self.game.tick()
        self.assertEqual(self.game.state['clock']['virtual'], original_virtual)
        self.assertEqual(self.game.state['clock']['last_real'], self.clock.value)
        self.clock.value += 599
        self.assert_counts(1)
        self.clock.value += 1
        self.assert_counts(0)
        self.assertEqual(self.game.state['animals'][key]['stats']['attack'], before + 10)
        self.assertEqual(self.game.get_statistics()['trainings_completed'], 1)

    def test_restart_with_future_saved_real_time_recovers_at_current_time(self):
        key = self.ids[0]
        self.start(key)
        original_virtual = self.game.state['clock']['virtual']
        self.clock.value -= 3600
        self.game = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.assertEqual(self.game.state['clock']['virtual'], original_virtual)
        self.assertEqual(self.game.state['clock']['last_real'], self.clock.value)
        self.clock.value += 600
        self.assert_counts(0)
        self.assertEqual(self.game.get_statistics()['trainings_completed'], 1)
        again = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.assertEqual(again.get_statistics()['trainings_completed'], 1)

    def test_repeated_clock_rollbacks_never_reverse_or_complete_twice(self):
        key = self.ids[0]
        before = self.game.state['animals'][key]['stats']['attack']
        original_virtual = self.game.state['clock']['virtual']
        self.start(key)
        previous_virtual = original_virtual
        for adjustment in (-3600, 200, -7200, 200, -60, 200):
            self.clock.value += adjustment
            self.game.tick()
            current = self.game.state['clock']['virtual']
            self.assertGreaterEqual(current, previous_virtual)
            previous_virtual = current
        self.assertEqual(previous_virtual, original_virtual + 600)
        self.assertEqual(self.game.state['animals'][key]['stats']['attack'], before + 10)
        self.assertEqual(self.game.get_statistics()['trainings_completed'], 1)
        self.game.tick()
        self.game.load_game()
        self.assertEqual(self.game.get_statistics()['trainings_completed'], 1)


if __name__ == '__main__':
    unittest.main()
