"""갈무리 도트 글꼴은 정해진 픽셀 크기에서만 획이 픽셀 격자에 맞는다 (UI_KIT.md).

theme.FONTS의 크기에서 안티에일리어싱을 켜고 렌더했을 때 반투명 픽셀이 하나도 없어야 한다.
(크기를 ±1만 바꿔도 47~99%가 반투명이 됨 → 뿌옇고 획 굵기가 들쭉날쭉)
"""
import os
import unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
import pygame

from gui import theme as T

SAMPLE = '내 동물 마이룸 설정 상점 사냥터 쉬움 ABC 0123'


class FontPixelGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def test_kit_font_sizes_are_pixel_exact(self):
        for kind, (name, size) in T.FONTS.items():
            path = os.path.join(T.FONT_DIR, name)
            self.assertTrue(os.path.exists(path), path)
            img = pygame.font.Font(path, size).render(SAMPLE, True, (0, 0, 0))
            w, h = img.get_size()
            partial = sum(1 for y in range(h) for x in range(w) if 0 < img.get_at((x, y)).a < 255)
            self.assertEqual(partial, 0, f'{kind}: {name} {size}px 에서 반투명 픽셀 {partial}개')


if __name__ == '__main__':
    unittest.main()
