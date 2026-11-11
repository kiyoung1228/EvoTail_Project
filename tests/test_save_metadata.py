"""Persistent GUI metadata: last battle IDs and real-world save time.

Run from the project root:
    python -m unittest discover -s tests -p "test_save_metadata.py" -v

Uses only temporary databases; never opens saves/game.db.
"""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roc import GameBridge, GameRuleError, GameService


class FakeClock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class ReliableRandom(random.Random):
    def random(self):
        return .99


class SaveMetadataTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'game.db'
        self.now = FakeClock()
        self.game = self.reopen()
        self.team = list(reversed(self.game.state['animals']))

    def reopen(self):
        return GameService(self.path, now=self.now, rng=ReliableRandom(7))

    def test_new_game_metadata_is_persisted_and_json_friendly(self):
        stored = self.game.store.load()
        self.assertEqual(stored['last_team'], [])
        self.assertEqual(stored['last_saved'], self.now())
        self.assertIsInstance(stored['last_saved'], float)
        for command in ('get_snapshot', 'get_game_state'):
            response = GameBridge(self.game).call(command)
            self.assertTrue(response['ok'])
            data = json.loads(json.dumps(response['data'], allow_nan=False))
            self.assertEqual(data['last_team'], [])
            self.assertEqual(data['last_saved'], self.now())

    def test_successful_battle_remembers_order_without_replacing_ai_roles(self):
        supplied = list(self.team)
        self.game.start_battle('tutorial', supplied)
        supplied.reverse()
        snapshot = self.game.get_snapshot()
        self.assertEqual(snapshot['last_team'], self.team)
        self.assertEqual(self.game.store.load()['last_team'], self.team)
        self.assertEqual(self.game.state['last_team_roles'],
                         [self.game.characters[key]['role'] for key in self.team])
        snapshot['last_team'].clear()
        self.assertEqual(self.game.get_snapshot()['last_team'], self.team)

    def test_forfeit_and_reload_preserve_team_and_next_battle_replaces_it(self):
        self.game.start_battle('tutorial', self.team)
        self.game.forfeit_battle()
        reopened = self.reopen()
        self.assertEqual(reopened.load_game()['last_team'], self.team)
        self.assertIsNone(reopened.get_snapshot()['battle'])
        next_team = list(reversed(self.team))
        reopened.start_battle('tutorial', next_team)
        self.assertEqual(reopened.get_snapshot()['last_team'], next_team)
        self.assertEqual(reopened.store.load()['last_team'], next_team)

    def test_active_battle_restart_preserves_team_and_order(self):
        self.game.start_battle('tutorial', self.team)
        self.now.advance(5)
        snapshot = self.reopen().get_snapshot()
        self.assertEqual(snapshot['last_team'], self.team)
        self.assertEqual([f['id'] for f in snapshot['battle']['player']], self.team)

    def test_victory_keeps_last_team_after_active_battle_is_cleared(self):
        self.game.start_battle('tutorial', self.team)
        # Accelerate a deterministic victory without changing the battle rules.
        self.game._mutate(lambda s: [f.update(hp=1) for f in s['battle']['enemy']])
        dealer = next(key for key in self.team
                      if self.game.characters[key]['role'] == 'dealer')
        self.game.battle_action(dealer)
        snapshot = self.game.get_snapshot()
        self.assertIsNone(snapshot['battle'])
        self.assertTrue(snapshot['battle_result']['win'])
        self.assertEqual(snapshot['last_team'], self.team)

    def test_enemy_victory_keeps_last_team_without_forfeiting(self):
        self.game.start_battle('tutorial', self.team)
        # Low HP lets real enemy actions finish the battle quickly.
        self.game._mutate(lambda s: [f.update(hp=1) for f in s['battle']['player']])
        for _ in range(20):
            if self.game.get_battle() is None:
                break
            self.game.end_player_turn()
        snapshot = self.game.get_snapshot()
        self.assertIsNone(snapshot['battle'])
        self.assertFalse(snapshot['battle_result']['win'])
        self.assertEqual(snapshot['battle_result']['winner'], 'enemy')
        self.assertEqual(snapshot['last_team'], self.team)
        self.assertEqual(self.game.store.load()['last_team'], self.team)

    def test_rejected_battle_does_not_replace_team_or_save_time(self):
        self.game.start_battle('tutorial', self.team)
        self.game.forfeit_battle()
        before = copy.deepcopy(self.game.state)
        stored = self.game.store.load()
        self.now.advance(10)
        with self.assertRaises(GameRuleError):
            self.game.start_battle('tutorial', [self.team[0]] * 3)
        self.assertEqual(self.game.state, before)
        self.assertEqual(self.game.store.load(), stored)

    def test_save_time_tracks_real_clock_during_demo_and_autosave(self):
        self.game.set_demo_mode(True, rate=60)
        self.now.advance(10)
        snapshot = self.game.get_snapshot()
        self.assertEqual(snapshot['last_saved'], self.now())
        self.assertNotEqual(snapshot['last_saved'], snapshot['clock']['timestamp'])
        self.assertEqual(snapshot['last_saved'], self.game.store.load()['last_saved'])
        self.now.advance(3)
        self.game.tick()
        self.assertEqual(self.game.store.load()['last_saved'], self.now())
        self.now.advance(1)
        self.game.buy_item('seed_wheat')
        stored = self.game.store.load()
        self.assertEqual(stored['last_saved'], self.now())
        self.assertEqual(stored['inventory']['seed_wheat'], 1)

    def test_explicit_save_returns_real_time_and_retains_virtual_timestamp(self):
        self.game.set_demo_mode(True, rate=60)
        self.now.advance(10)
        response = self.game.save_game()
        self.assertTrue(response['saved'])
        self.assertEqual(response['last_saved'], self.now())
        self.assertEqual(response['timestamp'], self.game.state['clock']['virtual'])
        self.assertNotEqual(response['timestamp'], response['last_saved'])
        self.assertEqual(response['last_saved'], self.game.store.load()['last_saved'])
        before_revision = self.game._revision
        self.game.save_game()
        self.assertEqual(self.game._revision, before_revision + 1)

    def test_old_save_without_metadata_migrates_without_guessing_ids_from_roles(self):
        legacy = self.game.store.load()
        legacy.pop('last_team')
        legacy.pop('last_saved')
        legacy['last_team_roles'] = ['dealer', 'tank', 'healer']
        self.game.store.commit(legacy, expected_revision=self.game._revision)
        self.now.advance(10)
        reopened = self.reopen()
        snapshot = reopened.get_snapshot()
        self.assertEqual(snapshot['last_team'], [])
        self.assertEqual(snapshot['last_saved'], self.now())
        self.assertEqual(reopened.store.load()['last_team'], [])
        self.assertEqual(reopened.state['last_team_roles'], legacy['last_team_roles'])
        self.assertEqual(snapshot['coins'], legacy['coins'])
        self.assertEqual(set(reopened.state['animals']), set(legacy['animals']))

    def test_failed_storage_write_does_not_publish_candidate_save_time(self):
        before = copy.deepcopy(self.game.state)
        stored = self.game.store.load()
        self.now.advance(10)
        with patch.object(self.game.store, 'commit', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                self.game.save_game()
        self.assertEqual(self.game.state, before)
        self.assertEqual(self.game.store.load(), stored)

    def test_conflicting_save_does_not_publish_candidate_metadata(self):
        other = self.reopen()
        before = copy.deepcopy(self.game.state)
        other.buy_item('seed_wheat')
        persisted = other.store.load()
        self.now.advance(10)
        with self.assertRaises(GameRuleError):
            self.game.save_game()
        self.assertEqual(self.game.state, before)
        self.assertEqual(self.game.store.load(), persisted)

    def test_reset_clears_last_team_and_records_new_save_time(self):
        self.game.start_battle('tutorial', self.team)
        self.game.forfeit_battle()
        self.now.advance(60)
        self.game.reset_game(confirm=True)
        snapshot = self.game.get_snapshot()
        self.assertEqual(snapshot['last_team'], [])
        self.assertEqual(snapshot['last_saved'], self.now())
        self.assertEqual(self.game.store.load()['last_saved'], self.now())


if __name__ == '__main__':
    unittest.main()
