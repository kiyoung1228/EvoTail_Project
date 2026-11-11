"""상점·병원 아이템 그림과 표시 글씨. 게임 규칙은 없다 (가격·효과·확률 숫자는 get_shop_catalog 값).

- 그림: assets/items/<백엔드 id>.png (원본 16×16, 파일 4배 64). 씨앗은 seed_<작물>.png, 없을 때만 seed.png.
  그림이 없으면 assets/food 그림(재료·요리), 그것도 없으면 키트 아이콘. 화면에서는 ×1~×3 정수배만.
- 다시 만들기: tools/shop_icons.py
"""
import os
import pygame

from . import theme as T
from .food import FoodIcons

ITEM_DIR = os.path.join(T.ROOT, 'assets', 'items')

# 상점 탭 (탭 id, 이름, 탭 그림, 들어가는 kind). 팔기 탭은 가방에 있고 sell이 있는 것
TABS = (
    ('food', '먹이·장난감', 'snack', ('snack', 'toy')),
    ('potion', '회복·포션', 'heal_basic', ('cure', 'prebattle', 'battle_item')),
    ('equip', '장비', 'equip_claw', ('equip',)),
    ('egg', '알', 'egg_special', ('egg',)),
    ('ingredient', '재료·씨앗', 'potato', ('ingredient', 'seed')),
    ('sell', '팔기', 'toy_ball', ()),
)
KIND_LABEL = {   # 종류 칩 (글씨, 색)
    'snack': ('먹이', 'orange'), 'toy': ('장난감', 'purple'), 'cure': ('치료', 'green'),
    'prebattle': ('전투 전 포션', 'blue'), 'battle_item': ('전투 아이템', 'red'), 'equip': ('장비', 'brown'),
    'egg': ('알', 'gold'), 'ingredient': ('재료', 'orange'), 'crop': ('작물', 'green'), 'seed': ('씨앗', 'green'),
    'food': ('요리', 'orange'),
}
# 알 탭: 특급 등장 확률. 백엔드(hatch_egg)에 숫자로 나오지 않아 GUI 표시 문구로 둔다 (CLAUDE.md 참고)
EGG_SPECIAL_RATE = {'egg_special': 60, 'egg_basic': 10}


def effect_lines(item, spec, catalog):
    """상세 칸 효과 줄 [(아이콘 또는 None, 글씨, 색)]. 숫자는 전부 상점 목록(spec) 값."""
    k = spec.get('kind')
    out = []
    good, soft = T.OK, T.TEXT_SOFT
    if k == 'snack':
        out.append(('meat', f"포만감 +{spec.get('fullness', 0)}", good))
    elif k == 'toy':
        out.append(('smile', f"기분 +{spec.get('mood', 0)}", good))
        out.append((None, f"{spec.get('charges', 0)}번 사용 · 안 쓴 것만 판매", soft))
    elif k == 'cure':
        out.append(('heart', f"질병 치료 확률 {round(spec.get('chance', 0) * 100)}%", good))
        if spec.get('fatigue'):
            out.append(('zzz', f"피로도 {spec['fatigue']:+d}", good))
        out.append((None, '병원에서 사용', soft))
    elif k in ('prebattle', 'equip'):
        stat = spec.get('stat')
        out.append((T.STAT_ICON.get(stat), f"{T.STAT_LABEL.get(stat, stat)} +{spec.get('amount', 0)}", T.WARN))
        if k == 'prebattle':
            out.append((None, '출전 준비에서 사용 · 전투 1번', soft))
        else:
            out.append((None, '내 동물 화면에서 장착', soft))
            out.append((None, '전투 중 교체 불가', soft))
    elif k == 'battle_item':
        out.append(('heart', f"체력 +{spec.get('heal', 0)}", good))
        out.append((None, '전투 중 사용 · 팀 행동 1번', soft))
    elif k == 'seed':
        crop = (catalog.get(spec.get('crop')) or {}).get('label', '')
        out.append(('snack', f"밭에 심으면 {crop}", good))
    elif k in ('ingredient', 'crop'):
        out.append((None, '요리 재료' + (' · 밭에서 수확' if k == 'crop' else ''), soft))
    elif k == 'food':
        for key, ic, label in (('fullness', 'meat', '포만감'), ('mood', 'smile', '기분'), ('fatigue', 'zzz', '피로도')):
            v = (spec.get('effects') or {}).get(key, 0)
            if v:
                ok = v < 0 if key == 'fatigue' else v > 0
                out.append((ic, f"{label} {v:+d}", good if ok else T.BAD))
    return out


class ItemIcons:
    """아이템 그림 캐시. get(item, n) = 원본 16×16 × n (정수)."""

    def __init__(self):
        self._base, self._out = {}, {}
        self.food = FoodIcons()

    def base(self, item):
        if item not in self._base:
            path = os.path.join(ITEM_DIR, f'{item}.png')
            if item.startswith('seed_') and not os.path.exists(path):      # 작물별 봉투가 없을 때만 공용 봉투
                path = os.path.join(ITEM_DIR, 'seed.png')
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                img = pygame.transform.scale(img, (w // 4, h // 4))         # 4배 저장 → 원본 16
            else:      # 재료·요리 그림 (없으면 FoodIcons가 키트 아이콘으로 대신)
                img = self.food.base(item)
            self._base[item] = img
        return self._base[item]

    def get(self, item, n=1, gray=False):
        key = (item, n, gray)
        if key not in self._out:
            img = self.base(item)
            img = pygame.transform.scale(img, (img.get_width() * n, img.get_height() * n))
            if gray:
                img = pygame.transform.grayscale(img)
            self._out[key] = img
        return self._out[key]


def item_label(item, catalog):
    return (catalog.get(item) or {}).get('label', item)
