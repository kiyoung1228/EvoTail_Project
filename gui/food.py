"""음식 그림·표시 글씨 (assets/food). 게임 규칙은 없다 (재료·효과·별·경험치는 백엔드 값).

- 그림: 원본 16×16, 파일은 4배(64×64). 원본으로 줄인 뒤 화면에서는 ×1~×4 정수배로만.
- 파일 이름 = 백엔드 아이템/레시피 id. 요리 아이템 food_<id>, food_perfect_<id>는 레시피 그림(<id>.png)을 쓰고,
  대성공은 그림을 가리지 않는 작은 별 배지로 따로 표시한다 (star_badge).
- 그림이 없는 재료(돼지고기·양배추 등)는 키트 아이콘으로 대신 그린다.
- 다시 만들기: tools/food_icons.py
"""
import json
import os
import pygame

from . import theme as T
from .widgets import Kit

FOOD_DIR = os.path.join(T.ROOT, 'assets', 'food')
with open(os.path.join(FOOD_DIR, 'food_icons.json'), encoding='utf-8') as _f:
    ICONS = json.load(_f)['icons']

# 레시피 한 줄 설명 (화면 표시 문구. 백엔드에 설명이 없어 GUI가 가진다)
DESCRIPTION = {
    'boiled_egg': '톡 까먹는 따끈한 달걀',
    'steamed_potato': '소금 솔솔 뿌린 포슬포슬 감자',
    'egg_roll': '양파를 넣어 돌돌 만 달걀',
    'tomato_soup': '우유를 넣어 부드러운 수프',
    'butter_potato': '버터를 녹여 노릇하게 구운 감자',
    'chicken_burger': '바삭한 닭고기 패티 버거',
    'beef_burger': '두툼한 소고기 패티 버거',
    'fried_chicken': '겉은 바삭, 속은 촉촉한 치킨',
    'carbonara': '버터와 달걀로 만든 크림 파스타',
    'omelette_rice': '달걀 이불을 덮은 볶음밥',
    'rabbit_stew': '행운이 깃든 귀한 스튜',
}

PERFECT_PREFIX = 'food_perfect_'
REGULAR_PREFIX = 'food_'
BURNED = 'burned_food'
FALLBACK_ICON = {'pork': 'meat'}       # 그림 파일이 없는 재료 → 키트 아이콘 (나머지는 snack)
STAR_GOLD = [(150, 100, 20), (250, 204, 70), (255, 236, 150)]     # [테두리, 본색, 밝은 점]
STAR_EMPTY = [(184, 176, 166), (226, 220, 210)]
_STAR_FILL = ('..#..', '.###.', '#####', '.###.', '.#.#.')       # 5×5 + 테두리 1px → 7×7


def recipe_of(item):
    """요리 아이템 id → 레시피 id (food_perfect_x / food_x → x). 그 밖은 그대로."""
    if item.startswith(PERFECT_PREFIX):
        return item[len(PERFECT_PREFIX):]
    if item.startswith(REGULAR_PREFIX):
        return item[len(REGULAR_PREFIX):]
    return item


def is_perfect(item):
    return item.startswith(PERFECT_PREFIX)


def is_dish(item):
    return item.startswith(REGULAR_PREFIX) or item == BURNED


def dish_name(item, catalog, recipes):
    """요리 이름 (목업: '대성공 감자버터구이'). 레시피 이름·아이템 이름은 백엔드 값."""
    r = recipes.get(recipe_of(item))
    if r and is_perfect(item):
        return f"대성공 {r['label']}"
    if r:
        return r['label']
    return (catalog.get(item) or {}).get('label') or ICONS.get(item, {}).get('name') or item


def item_name(item, catalog):
    """재료 이름: 백엔드 상점 목록의 label, 없으면 food_icons.json 이름."""
    return (catalog.get(item) or {}).get('label') or ICONS.get(item, {}).get('name') or item


class FoodIcons:
    """음식 그림 캐시. get(item, n): 원본 16×16 × n (정수)."""

    def __init__(self):
        self._base, self._out = {}, {}

    def base(self, item):
        key = recipe_of(item)
        if key not in self._base:
            path = os.path.join(FOOD_DIR, f'{key}.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                img = pygame.transform.scale(img, (w // 4, h // 4))          # 4배 저장 → 원본 16
            else:
                img = pygame.Surface((16, 16), pygame.SRCALPHA)
                img.blit(Kit.icon(FALLBACK_ICON.get(key, 'snack')), (2, 2))
            self._base[key] = img
        return self._base[key]

    def get(self, item, n=1, gray=False):
        key = (recipe_of(item), n, gray)
        if key not in self._out:
            img = self.base(item)
            img = pygame.transform.scale(img, (img.get_width() * n, img.get_height() * n))
            if gray:          # 아직 못 만드는 요리: 밝은 회색
                img = pygame.transform.grayscale(img)
                img.fill((20, 18, 16, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self._out[key] = img
        return self._out[key]


_stars = {}


def star(filled=True):
    """7×7 도트 별 (채움: 금색 + 진한 테두리, 빈 별: 연회색)."""
    if filled not in _stars:
        img = pygame.Surface((7, 7), pygame.SRCALPHA)
        fill = {(x + 1, y + 1) for y, row in enumerate(_STAR_FILL) for x, c in enumerate(row) if c == '#'}
        edge, body = (STAR_GOLD[0], STAR_GOLD[1]) if filled else STAR_EMPTY
        for x in range(7):
            for y in range(7):
                if (x, y) in fill:
                    img.set_at((x, y), body)
                elif any((x + dx, y + dy) in fill for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    img.set_at((x, y), edge)
        if filled:
            img.set_at((3, 2), STAR_GOLD[2])
        _stars[filled] = img
    return _stars[filled]


STARS_W = 5 * 8 - 1       # 별 5개 줄의 폭 (별 7 + 사이 1)


def stars(surface, pos, count, total=5):
    """별 total개 중 count개 채움. pos = 왼쪽 위."""
    for i in range(total):
        surface.blit(star(i < count), (pos[0] + i * 8, pos[1]))


def star_badge(surface, pos):
    """대성공 표시: 그림 옆에 붙이는 작은 별 배지 (9×9, 그림을 가리지 않게 칸 모서리에)."""
    x, y = pos
    pygame.draw.rect(surface, T.INK, (x, y, 9, 9))
    pygame.draw.rect(surface, T.shade('orange', 1), (x + 1, y + 1, 7, 7))
    surface.blit(star(True), (x + 1, y + 1))
