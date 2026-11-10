"""Names and sprites the GUI shows must follow the evolution stage."""
import os
import tempfile
import unittest

from roc import GameService
from roc import config as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DisplayInfoTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.g = GameService(os.path.join(self.tmp.name, 'game.db'))

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_stage_sprite_exists(self):
        for key, info in self.g.characters.items():
            for stage in range(1, info['max_stage'] + 1):
                look = self.g.display_info(key, stage)
                self.assertTrue(os.path.exists(os.path.join(ROOT, look['sprite'])), look['sprite'])
                self.assertTrue(look['name'].endswith(info['species']))

    def test_evolution_changes_name_and_sprite(self):
        key = 'dealer_normal_01'
        before = next(a for a in self.g.get_animals() if a['id'] == key)
        self.assertEqual(before['name'], '불씨여우')
        caps = self.g.get_evolution_status(key)['caps']
        self.g._mutate(lambda s: (s.update(coins=10000), s['animals'][key]['stats'].update(dict(caps))))
        self.g.evolve(key)
        after = next(a for a in self.g.get_animals() if a['id'] == key)
        self.assertEqual(after['name'], '불꽃여우')
        self.assertTrue(after['sprite'].endswith('_s2.png'))
        snap = next(a for a in self.g.get_snapshot()['animals'] if a['id'] == key)
        self.assertEqual(snap['name'], '불꽃여우')
        dex = next(d for d in self.g.get_pokedex() if d['id'] == key)
        self.assertEqual(dex['name'], '불꽃여우')

    def test_enemies_have_wild_animal_look(self):
        preview = self.g.preview_stage('tutorial')
        for enemy in preview['enemy']:
            self.assertTrue(enemy['name'].startswith('야생 '))
            self.assertTrue(os.path.exists(os.path.join(ROOT, enemy['sprite'])))

    def test_battle_fighters_carry_name_and_sprite(self):
        team = [a['id'] for a in self.g.get_animals()][:3]
        battle = self.g.start_battle('tutorial', team)
        for fighter in battle['player'] + battle['enemy']:
            self.assertIn('name', fighter)
            self.assertIn('sprite', fighter)


if __name__ == '__main__':
    unittest.main()
