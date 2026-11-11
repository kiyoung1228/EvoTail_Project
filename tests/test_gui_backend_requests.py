"""Regression tests for 2026-11-11 GUI/backend handoff.

Only idle autonomous actions are changed; ongoing player-initiated jobs still
show training/hunting/battle.  Clock values are derived from save-created game
world time (not the operating system's local clock).
"""
import random
import tempfile
import unittest
from pathlib import Path

from roc import GameService
from roc import autonomy as AUTO
from roc import config as C
from roc.bridge import GameBridge


class FakeClock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class NewGuiBackendRequirements(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = FakeClock()
        self.path = Path(self.temp.name) / 'test.db'
        self.game = GameService(self.path, now=self.now, rng=random.Random(7))
        self.key = self.game.get_animals()[0]['id']

    def test_fatigue_above_80_forces_rest_even_if_picky_hungry_and_sad(self):
        for nature in C.NATURES:
            with self.subTest(nature=nature):
                animal = {'fullness': 0, 'fatigue': 81, 'mood': 0, 'nature': nature}
                result = AUTO.evaluate(animal)
                self.assertEqual(result.action, 'rest')
                self.assertEqual(result.as_dict()['label'], '휴식')
                self.assertIn('강제 휴식', result.reason)

    def test_exactly_80_is_not_forced_rest_and_picky_can_refuse(self):
        animal = {'fullness': 0, 'fatigue': 80, 'mood': 0, 'nature': 'picky'}
        self.assertEqual(AUTO.evaluate(animal).action, 'refuse')

    def test_rest_shows_in_gui_autonomy_after_short_tick(self):
        self.game._mutate(lambda s: s['animals'][self.key].update(
            nature='picky', fullness=0, mood=0, fatigue=90, auto_action='idle'))
        self.now.advance(1)
        snapshot = self.game.get_snapshot()
        row = next(a for a in snapshot['animals'] if a['id'] == self.key)
        view = self.game.get_autonomous_state(self.key)
        self.assertEqual(row['auto_action'], 'rest')
        self.assertEqual(view['action'], 'rest')
        self.assertEqual(view['label'], '휴식')

    def test_busy_animal_still_shows_its_assigned_job(self):
        # A manual training job supersedes autonomous rest while busy.
        self.game.start_training(self.key, 'attack', 'easy')
        self.game._mutate(lambda s: s['animals'][self.key].update(fatigue=95))
        self.now.advance(1)
        self.assertEqual(self.game.get_autonomous_state(self.key)['action'], 'training')

    def test_animal_status_labels_match_existing_thresholds_in_both_apis(self):
        # Exactly the same 30/55 boundaries as GameService._status_label;
        # fatigue has the opposite direction from fullness and mood.
        cases = (
            ({'fullness': 29, 'mood': 30, 'fatigue': 55},
             {'fullness': 'bad', 'mood': 'normal', 'fatigue': 'normal'}),
            ({'fullness': 30, 'mood': 55, 'fatigue': 29},
             {'fullness': 'normal', 'mood': 'normal', 'fatigue': 'good'}),
            ({'fullness': 56, 'mood': 56, 'fatigue': 56},
             {'fullness': 'good', 'mood': 'good', 'fatigue': 'bad'}),
            ({'fullness': 0, 'mood': 100, 'fatigue': 100},
             {'fullness': 'bad', 'mood': 'good', 'fatigue': 'bad'}),
        )
        for values, expected in cases:
            with self.subTest(values=values):
                self.game._mutate(lambda s: s['animals'][self.key].update(values))
                snapshot_row = next(a for a in self.game.get_snapshot()['animals']
                                    if a['id'] == self.key)
                animals_row = next(a for a in self.game.get_animals()
                                   if a['id'] == self.key)
                for row in (snapshot_row, animals_row):
                    self.assertEqual(row['status'], expected)
                    for stat in ('fullness', 'mood', 'fatigue'):
                        self.assertEqual(row[stat], values[stat])
                        self.assertEqual(row['status'][stat], self.game._status_label(row, stat))

    def test_status_present_for_every_animal_and_bridge_is_json_compatible(self):
        from json import dumps, loads
        bridge = GameBridge(self.game)
        for command in ('get_snapshot', 'get_animals'):
            with self.subTest(command=command):
                response = bridge.call(command)
                self.assertTrue(response['ok'])
                payload = loads(dumps(response['data']))
                rows = payload['animals'] if command == 'get_snapshot' else payload
                self.assertEqual(len(rows), len(self.game.get_animals()))
                for a in rows:
                    self.assertEqual(set(a['status']), {'fullness','mood','fatigue'})
                    self.assertTrue(all(level in ('good','normal','bad')
                                        for level in a['status'].values()))

    def test_clock_day_and_time_start_at_0600_and_agree_across_apis(self):
        for call in (self.game.get_snapshot, self.game.get_game_state):
            with self.subTest(method=call.__name__):
                clock = call()['clock']
                self.assertEqual((clock['day'], clock['time']), (1, '06:00'))
                self.assertFalse(clock['night'])
                self.assertEqual(clock['timestamp'], self.now())
        bridge = GameBridge(self.game)
        self.assertEqual(bridge.call('get_snapshot')['data']['clock']['time'], '06:00')

    def test_clock_transitions_every_half_hour_and_rolls_over_after_full_day(self):
        checkpoints = (
            (1250, 1, '14:20', False),
            (1799, 1, '17:59', False),
            (1800, 1, '18:00', True),
            (2700, 1, '00:00', True),
            (3599, 1, '05:59', True),
            (3600, 2, '06:00', False),
        )
        elapsed = 0
        for target, day, time, is_night in checkpoints:
            self.now.advance(target - elapsed)
            elapsed = target
            snapshot_clock = self.game.get_snapshot()['clock']
            state_clock = self.game.get_game_state()['clock']
            for clock in (snapshot_clock, state_clock):
                with self.subTest(elapsed=target):
                    self.assertEqual((clock['day'], clock['time'], clock['night']),
                                     (day, time, is_night))

    def test_clock_persists_through_restart_and_offline_time(self):
        self.now.advance(1250)
        self.assertEqual(self.game.get_snapshot()['clock']['time'], '14:20')
        self.now.advance(550)  # game closed for 9m10s -> 18:00
        restarted = GameService(self.path, now=self.now, rng=random.Random(10))
        self.assertEqual(restarted.get_snapshot()['clock']['time'], '18:00')
        self.assertEqual(restarted.get_snapshot()['clock']['day'], 1)

    def test_demo_clock_increase_uses_virtual_time_and_keeps_day_counter(self):
        self.game.set_demo_mode(True, rate=60)
        self.now.advance(60)
        clock = self.game.get_snapshot()['clock']
        self.assertEqual((clock['day'], clock['time']), (2, '06:00'))
        self.assertEqual(clock['rate'], 60)


if __name__ == '__main__':
    unittest.main()
