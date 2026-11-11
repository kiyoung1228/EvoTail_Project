"""적 몬스터 그림 (data/enemies.json, assets/enemies): 졸개 원본 28, 보스 원본 46, 파일은 4배."""
import json
import os
import struct
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


class EnemySpriteTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, 'data', 'enemies.json'), encoding='utf-8') as f:
            self.data = json.load(f)

    def test_minions_are_28_times_4(self):
        self.assertEqual(len(self.data['minions']), 12)
        for m in self.data['minions']:
            self.assertEqual(png_size(os.path.join(ROOT, m['sprite'])), (112, 112), m['id'])

    def test_bosses_are_46_times_4_one_per_stage(self):
        self.assertEqual(len(self.data['bosses']), 9)
        self.assertEqual(len({b['stage'] for b in self.data['bosses']}), 9)
        for b in self.data['bosses']:
            self.assertTrue(b.get('boss'))
            self.assertEqual(png_size(os.path.join(ROOT, b['sprite'])), (184, 184), b['id'])


if __name__ == '__main__':
    unittest.main()
