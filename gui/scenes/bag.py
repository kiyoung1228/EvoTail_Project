"""가방 (D안): 세워 둔 가죽 배낭(5×4 칸) + 옆구리 천 탭 6개 + 핀 꽂은 쪽지(고른 아이템 정보와 쓰기).

목업 docs/mockups/bag/bag_D1_feed.png, bag_D2_material.png, bag_D3_battle.png. 배낭·쪽지 모양은
tools/bag_mock2.py bag_D()·note_paper()와 같게 코드 도트로 그린다.
게임 규칙은 없다: 가진 것은 스냅샷 inventory(stackable, toys), 이름·효과·값은 get_shop_catalog, 쓰는 곳은
get_recipes, 얻는 곳은 get_hunts. 쓰기·팔기·장착·치료·부화는 백엔드 명령(use_item, sell_item, equip, hatch_egg).
"""
import os
import pygame

from .. import theme as T
from .. import widgets as W
from .. import items as I
from .. import food as F
from ..app import Scene
from ..widgets import (text, text_in, glyph_box, fit_width, card, card_inner, ribbon, chip, chip_width, icon,
                       gauge, select_frame, record, wrap2, Button, BUTTON_H)
from .hospital import CureResult
from .hatch import HatchOverlay
from .farm import FARM_DISPLAY

# ---- 배낭 모양 (tools/bag_mock2.py와 같은 값) ----
LE = [(92, 56, 32), (130, 82, 46), (164, 108, 62), (196, 140, 86), (226, 178, 118)]     # 가죽 어두움→밝음
LINING = (78, 50, 34)
STITCH = (236, 200, 140)
GOLD = (232, 196, 90)
BODY = pygame.Rect(10, 66, 317, 289)
FLAP_H = 46
SLOT = (32, 140, 56, 49, 52, 45)              # 첫 칸 x, y, 가로 간격, 세로 간격, 칸 폭, 칸 높이
COLS, ROWS = 5, 4
TAB_X, TAB_Y, TAB_STEP, TAB_H = 324, 116, 38, 34
NOTE = [(404, 66), (628, 62), (632, 350), (400, 354)]
NX, NR = 418, 620                              # 쪽지 안 글씨 왼쪽·오른쪽 끝

# 종류: 탭 id → (이름, 탭 그림, 칸 색, 들어가는 상점 목록 kind)
CATS = (
    ('all', '전체', None, (236, 220, 190), ()),
    ('feed', '먹이', 'snack', (255, 236, 200), ('snack', 'toy')),
    ('food', '요리', 'butter_potato', (255, 226, 214), ('food',)),
    ('potion', '포션', 'heal_basic', (226, 236, 255), ('cure', 'prebattle', 'battle_item')),
    ('gear', '장비·알', 'equip_claw', (236, 226, 255), ('equip', 'egg')),
    ('mat', '재료', 'potato', (232, 244, 214), ('ingredient', 'crop', 'seed')),
)
KIND_CAT = {k: c[0] for c in CATS for k in c[4]}
TINT = {c[0]: c[3] for c in CATS}
KIND_CHIP = {   # 종류 칩 (글씨, 색)
    'snack': ('먹이', 'orange'), 'toy': ('장난감', 'orange'), 'food': ('요리', 'red'), 'cure': ('치료', 'green'),
    'prebattle': ('전투 포션', 'blue'), 'battle_item': ('전투 아이템', 'blue'), 'equip': ('장비', 'purple'),
    'egg': ('알', 'gold'), 'ingredient': ('재료', 'brown'), 'crop': ('작물', 'brown'), 'seed': ('씨앗', 'green'),
}
ACTIVITY_LABEL = {'training': '훈련 중', 'hunt': '사냥 중', 'hunting': '사냥 중'}
ROW_H, ROW_STEP = 30, 34


class _CureHost:
    """병원 치료 결과 창(CureResult)을 가방에서 쓰기 위한 연결 (patients·have·catalog·treat·selected)."""

    def __init__(self, bag):
        self.bag = bag
        self.app = bag.app

    @property
    def catalog(self):
        return self.bag.catalog

    def patients(self):
        return [a for a in self.bag.animals() if a.get('sick')]

    def have(self, item):
        return self.bag.have(item)

    def treat(self, key, item):
        self.bag.target = key
        self.bag.use_cure(item)

    @property
    def selected(self):
        return self.bag.target

    @selected.setter
    def selected(self, key):
        self.bag.target = key


class BagScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.cat = 'all'
        self.selected = None            # 고른 칸 키 (아이템 id, 장난감은 'toy_ball#0'처럼 몇 번째인지)
        self.target = None              # 쪽지에서 고른 동물
        self.scroll = 0                 # 배낭 칸 줄 넘김
        self.list_scroll = 0            # 쪽지 동물 목록 넘김
        self.catalog = {}
        self.recipes = {}
        self.hunts = {}
        self.icons = I.ItemIcons()
        self.food_icons = F.FoodIcons()
        self.buttons = []
        self._bag_icon = None
        self.list_rect = None
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.catalog = self.app.call('get_shop_catalog') or self.catalog
        self.recipes = (self.app.call('get_recipes') or {}).get('recipes', self.recipes)
        self.hunts = (self.app.call('get_hunts') or {}).get('areas', self.hunts)
        self.scroll = self.list_scroll = 0
        self._fix()

    # ---------- 가방 내용 ----------
    def stack(self):
        return self.app.state.get('inventory', {}).get('stackable', {})

    def have(self, item):
        return self.stack().get(item, 0)

    def animals(self):
        return self.app.state.get('animals', [])

    def slots(self, cat=None):
        """[(칸 키, 아이템 id, 개수 글씨 또는 None, 종류 탭)] — 종류 순서, 그 안은 상점 목록 순서."""
        cat = cat or self.cat
        order = {k: i for i, k in enumerate(self.catalog)}
        rows = []
        for item, n in self.stack().items():
            if n <= 0:
                continue
            c = KIND_CAT.get((self.catalog.get(item) or {}).get('kind'), 'mat')
            rows.append((item, item, str(n) if n > 1 else None, c))
        seen = {}
        for toy in self.app.state.get('inventory', {}).get('toys', []):
            k = seen.get(toy['id'], 0)
            seen[toy['id']] = k + 1
            rows.append((f"{toy['id']}#{k}", toy['id'], f"{toy.get('charges', 0)}회", 'feed'))
        cat_order = [c[0] for c in CATS]
        rows.sort(key=lambda r: (cat_order.index(r[3]), order.get(r[1], 999), r[0]))
        return [r for r in rows if cat == 'all' or r[3] == cat]

    def current(self):
        return next((r for r in self.slots() if r[0] == self.selected), None)

    def _fix(self):
        keys = [r[0] for r in self.slots()]
        if self.selected not in keys:
            self.selected = keys[0] if keys else None
            self.list_scroll = 0
        rows = (len(keys) + COLS - 1) // COLS
        self.scroll = max(0, min(self.scroll, rows - ROWS))
        self._fix_target()

    def spec(self, item):
        return self.catalog.get(item) or {}

    def label(self, item):
        if F.is_dish(item):
            return F.dish_name(item, self.catalog, self.recipes)
        return I.item_label(item, self.catalog)

    def busy_reason(self, a):
        act = a.get('activity') or {}
        if act:
            return ACTIVITY_LABEL.get(act.get('kind'), '활동 중')
        battle = self.app.state.get('battle') or {}
        if a['id'] in [f.get('id') for f in battle.get('player', [])]:
            return '전투 중'
        return None

    def list_animals(self):
        """쪽지 동물 목록 (지금 고른 아이템에 맞게). 치료 포션이면 아픈 동물만."""
        r = self.current()
        if not r:
            return []
        kind = self.spec(r[1]).get('kind')
        if kind == 'cure':
            return [a for a in self.animals() if a.get('sick')]
        return list(self.animals())

    def _fix_target(self):
        animals = self.list_animals()
        ids = [a['id'] for a in animals]
        if self.target not in ids:
            free = [a['id'] for a in animals if not self.busy_reason(a)]
            self.target = (free or ids or [None])[0]

    # ---------- 칸 위치 ----------
    @staticmethod
    def slot_rect(i):
        x, y, dx, dy, w, h = SLOT
        return pygame.Rect(x + (i % COLS) * dx, y + (i // COLS) * dy, w, h)

    @staticmethod
    def tab_rect(i, label, on):
        w = max(30, fit_width(label, 'small') + 6) + (8 if on else 0)
        return pygame.Rect(TAB_X, TAB_Y + i * TAB_STEP, w, TAB_H)

    def row_rect(self, i):
        return pygame.Rect(416, self.list_rect.y + i * ROW_STEP, 204, ROW_H)

    # ---------- 명령 ----------
    def use_food(self):
        r = self.current()
        a = self.app.animal(self.target)
        if not r or not a:
            return
        item = r[1]
        name = self.label(item)
        data = self.app.act('use_item', None, item=item, key=a['id'])
        if data is None:
            return
        if data.get('refused'):
            self.app.toast(f"{T.josa(a['name'], '이')} {T.josa(name, '을')} 안 먹었다", 'bad', 'frown')
        elif self.spec(item).get('kind') == 'toy':
            self.app.toast(f"{T.josa(a['name'], '이')} {T.josa(name, '으로')} 놀았다 · 기분 {data.get('mood')}", 'ok',
                           'smile')
        else:
            self.app.toast(f"{T.josa(a['name'], '이')} {T.josa(name, '을')} 먹었다 · 포만감 {data.get('fullness')}",
                           'ok', 'heart')
        self._fix()

    def use_cure(self, item=None):
        r = self.current()
        item = item or (r[1] if r else None)
        a = self.app.animal(self.target)
        if not item or not a:
            return
        before = a['fatigue']
        res = self.app.call('use_item', item=item, key=a['id'])
        self.app.refresh()
        self._fix()
        if res is not None:
            self.app.open_overlay(CureResult(_CureHost(self), a, item, before, res))

    def equip(self):
        r = self.current()
        a = self.app.animal(self.target)
        if r and a:
            self.app.act('equip', f"{T.josa(a['name'], '이')} {T.josa(self.label(r[1]), '을')} 장착했다", icon='shield',
                         key=a['id'], item=r[1])
            self._fix()

    def hatch(self, egg=None):
        r = self.current()
        egg = egg or (r[1] if r else None)
        if egg:
            self.app.open_overlay(HatchOverlay(self.app, egg, on_again=self.hatch))

    def sell(self):
        r = self.current()
        if not r:
            return
        name = self.label(r[1])
        self.app.act('sell_item', lambda d: f"{T.josa(name, '을')} 팔았다 · +{d.get('earned', 0):,}코인", icon='coin',
                     item=r[1], quantity=1)
        self._fix()

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
        elif event.type == pygame.MOUSEWHEEL:
            pos = W.mouse_pos()
            if BODY.collidepoint(pos):
                self.scroll = max(0, self.scroll - event.y)
                self._fix()
            elif self.list_rect and self.list_rect.collidepoint(pos):
                n = len(self.list_animals())
                self.list_scroll = max(0, min(max(0, n - self._list_rows()), self.list_scroll - event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (cid, label, *_rest) in enumerate(CATS):
                if self.tab_rect(i, label, cid == self.cat).collidepoint(event.pos):
                    self.cat = cid
                    self.scroll = 0
                    self._fix()
                    return
            for i, r in enumerate(self.visible_slots()):
                if self.slot_rect(i).collidepoint(event.pos):
                    if r[0] != self.selected:
                        self.list_scroll = 0
                    self.selected = r[0]
                    self._fix_target()
                    return
            if self.list_rect:
                for i, a in enumerate(self.list_animals()[self.list_scroll:self.list_scroll + self._list_rows()]):
                    if self.row_rect(i).collidepoint(event.pos):
                        self.target = a['id']
                        return

    def visible_slots(self):
        return self.slots()[self.scroll * COLS:(self.scroll + ROWS) * COLS]

    def _list_rows(self):
        return max(1, self.list_rect.h // ROW_STEP) if self.list_rect else 0

    # ---------- 버튼 (쪽지 아래) ----------
    def update(self, dt):
        self._fix()
        self.buttons = []
        self.list_rect = None
        r = self.current()
        if not r:
            if not self.stack() and not self.app.state.get('inventory', {}).get('toys'):
                self.buttons.append(Button((416, 286, 204, 36), '상점에서 사기', lambda: self.app.go('shop'), 'orange',
                                           icon='coin'))
            return
        item = r[1]
        spec = self.spec(item)
        kind = spec.get('kind')
        sell = spec.get('sell')
        a = self.app.animal(self.target)
        big = (416, 286, 204, 36)
        if kind in ('snack', 'toy', 'food'):
            label = f"{a['name']}에게 주기" if a else '동물 선택'
            sub = '1회 사용' if kind == 'toy' else f"{self.label(item)} 1개"
            self.buttons.append(Button(big, label, self.use_food, 'green', enabled=bool(a and not self.busy_reason(a)),
                                       icon='heart', sub=sub))
        elif kind == 'cure':
            if a:
                self.buttons.append(Button(big, f"{a['name']} 치료하기", self.use_cure, 'green', icon='heart',
                                           enabled=not self.busy_reason(a), sub=f"{self.label(item)} 1개 사용"))
            else:
                self.buttons.append(Button(big, '치료할 동물 없음', None, 'gray', enabled=False, sub='아픈 동물 없음'))
        elif kind == 'equip':
            label = f"{a['name']}에게 장착" if a else '동물 선택'
            self.buttons.append(Button(big, label, self.equip, 'purple', enabled=bool(a and not self.busy_reason(a)),
                                       icon='shield', sub='전투 중 교체 불가'))
        elif kind == 'egg':
            self.buttons.append(Button(big, '지금 부화', self.hatch, 'green', icon='heart', sub=self.label(item)))
        elif kind in ('prebattle', 'battle_item'):
            self.buttons.append(Button((416, 246, 204, 26), '전투장으로', lambda: self.app.go('battle'), 'blue',
                                       icon='sword'))
            if sell is not None:
                self.buttons.append(Button((416, 278, 204, 22), f"상점에 팔기 · {sell:,}코인", self.sell, 'red',
                                           icon='coin'))
            return
        else:   # 재료·작물·고기·씨앗
            y = self._mat_layout(item)[1]
            if kind == 'seed':
                self.buttons.append(Button((416, y, 204, 26), '밭으로', lambda: self.app.go('farm'), 'green',
                                           icon='snack'))
            else:
                self.buttons.append(Button((416, y, 204, 26), '주방으로', lambda: self.app.go('home'), 'orange',
                                           icon='home'))
            if sell is not None:
                self.buttons.append(Button((416, y + 32, 204, 22), f"상점에 팔기 · {sell:,}코인", self.sell, 'red',
                                           icon='coin'))
            return
        if sell is not None:
            self.buttons.append(Button((416, 326, 204, 20), f"상점에 팔기 · {sell:,}코인", self.sell, 'red', icon='coin'))

    def _head(self, item):
        """쪽지 머리 배치: (이름 줄들, 첫 줄 y, 칩 y, 본문 시작 y)."""
        lines = wrap2(self.label(item), NR - 478, 'big')
        top = 92 - (len(lines) - 1) * 8
        cy = top + (len(lines) - 1) * 16 + 12
        return lines, top, cy, max(142, cy + 26)

    def _mat_uses(self, item):
        spec = self.spec(item)
        if spec.get('kind') == 'seed':
            crop = spec.get('crop')
            return [(f'seed_{crop}', '밭에 심기', f"다 자라면 {self.label(crop)} ×{FARM_DISPLAY['yield']}")]
        return [(key, r['label'], f"주방 레시피 ★{r['stars']}") for key, r in self.recipes.items()
                if item in r.get('ingredients', {})]

    def _mat_layout(self, item):
        """재료 쪽지: (쓰는 곳 카드 목록, 버튼 y)."""
        uses = self._mat_uses(item)
        y = self._head(item)[3] + 14 + (26 if not uses else 34 * min(2, len(uses))) + 14
        if self.spec(item).get('sell') is not None:
            y += 14
        return uses, min(y + 6, 270)

    # ---------- 그리기 ----------
    def draw(self, surface):
        self.app.backdrop(surface)
        self.back.draw(surface)
        ribbon(surface, (78, 33, 70, 18), '가방', 'red')
        self._draw_backpack(surface)
        self._draw_note(surface)
        for b in self.buttons:
            b.draw(surface)

    def bag_icon(self):
        """'전체' 탭 그림: 메뉴 가방 아이콘(48px)을 그림 부분만 잘라 16px 안으로 정수배 축소."""
        if self._bag_icon is None:
            img = pygame.image.load(os.path.join(T.ROOT, 'assets', 'ui', 'icon_bag.png')).convert_alpha()
            img = img.subsurface(img.get_bounding_rect()).copy()
            f = max(1, -(-max(img.get_size()) // 16))
            self._bag_icon = pygame.transform.scale(img, (img.get_width() // f, img.get_height() // f))
        return self._bag_icon

    def _draw_backpack(self, surface):
        # 손잡이
        pygame.draw.rect(surface, T.INK, (140, 54, 61, 19), 4, border_radius=8)
        pygame.draw.rect(surface, LE[1], (141, 55, 59, 17), 2, border_radius=8)
        # 탭 (몸통 뒤에서 옆으로 삐져나옴)
        for i, (cid, label, ic, col, _) in enumerate(CATS):
            on = cid == self.cat
            r = self.tab_rect(i, label, on)
            pygame.draw.rect(surface, col, r)
            pygame.draw.rect(surface, T.INK, r, 1)
            pygame.draw.line(surface, T.WHITE, (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
            img = self.bag_icon() if ic is None else self.icons.get(ic, 1)
            surface.blit(img, img.get_rect(midtop=(r.centerx, r.y + 2)))
            text_in(surface, label, (r.x + 1, r.y + 19, r.w - 2, 14), 'small', T.TEXT, tag='bag')
        # 몸통 + 덮개 + 끈·버클 + 바느질 + 안감
        pygame.draw.rect(surface, LE[2], BODY, border_radius=24)
        pygame.draw.rect(surface, T.INK, BODY, 1, border_radius=24)
        pygame.draw.rect(surface, LE[3], BODY.inflate(-8, -8), 1, border_radius=22)
        flap = pygame.Rect(BODY.x, BODY.y, BODY.w, FLAP_H + 1)
        pygame.draw.rect(surface, LE[1], flap, border_top_left_radius=24, border_top_right_radius=24)
        pygame.draw.rect(surface, T.INK, flap, 1, border_top_left_radius=24, border_top_right_radius=24)
        for bx in (80, 244):
            pygame.draw.rect(surface, LE[0], (bx, 80, 13, 49))
            pygame.draw.rect(surface, T.INK, (bx, 80, 13, 49), 1)
            pygame.draw.rect(surface, GOLD, (bx - 2, 118, 17, 11))
            pygame.draw.rect(surface, T.INK, (bx - 2, 118, 17, 11), 1)
            pygame.draw.rect(surface, LE[0], (bx + 2, 121, 9, 5))
        x0, y0, x1, y1 = 20, 116, 316, 344                                   # 바느질 점선
        for x in range(x0 + 4, x1 - 4, 7):
            pygame.draw.line(surface, STITCH, (x, y0), (x + 3, y0))
            pygame.draw.line(surface, STITCH, (x, y1), (x + 3, y1))
        for y in range(y0 + 4, y1 - 4, 7):
            pygame.draw.line(surface, STITCH, (x0, y), (x0, y + 3))
            pygame.draw.line(surface, STITCH, (x1, y), (x1, y + 3))
        lining = pygame.Rect(24, 132, 289, 209)
        pygame.draw.rect(surface, LINING, lining, border_radius=10)
        pygame.draw.rect(surface, (50, 30, 20), lining, 1, border_radius=10)
        # 칸 5×4
        vis = self.visible_slots()
        for i in range(COLS * ROWS):
            self._draw_slot(surface, self.slot_rect(i), vis[i] if i < len(vis) else None)
        rows = (len(self.slots()) + COLS - 1) // COLS
        if rows > ROWS:
            more = f"{self.scroll + 1}-{self.scroll + ROWS} / {rows}줄 · 휠"
            text(surface, more, (lining.right - 4, lining.y - 3), 'small', STITCH, 'bottomright')
        if not self.slots(cat='all'):
            box = pygame.Rect(0, 0, fit_width('가방이 비었다', 'title', shadow=True) + 16, 24)
            box.center = lining.center
            card(surface, box)
            text_in(surface, '가방이 비었다', card_inner(box), 'title', T.TEXT, shadow=T.WHITE, tag='bag')

    def _draw_slot(self, surface, r, row):
        if not row:
            pygame.draw.rect(surface, (104, 70, 46), r)
            pygame.draw.rect(surface, (64, 40, 24), r, 1)
            pygame.draw.line(surface, (124, 86, 58), (r.x + 1, r.bottom - 2), (r.right - 2, r.bottom - 2))
            return
        key, item, count, cat = row
        pygame.draw.rect(surface, TINT[cat], r)
        pygame.draw.rect(surface, T.INK, r, 1)
        pygame.draw.line(surface, T.WHITE, (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
        img = self.icons.get(item, 2)
        surface.blit(img, img.get_rect(center=(r.centerx, r.centery - 1)))
        if F.is_perfect(item):
            F.star_badge(surface, (r.x + 3, r.y + 3))
        if count:                                      # 개수: 흰 글씨 + 테두리 (오른쪽 아래)
            pos = (r.right - 3, r.bottom - 2)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                text(surface, count, (pos[0] + dx, pos[1] + dy), 'small', T.INK, 'bottomright')
            text(surface, count, pos, 'small', T.WHITE, 'bottomright')
        if key == self.selected:
            select_frame(surface, r.inflate(4, 4))

    # ---------- 쪽지 ----------
    def _draw_note(self, surface):
        pygame.draw.polygon(surface, (250, 240, 214), NOTE)
        pygame.draw.polygon(surface, T.INK, NOTE, 1)
        for y in range(92, 346, 14):
            pygame.draw.line(surface, (232, 216, 186), (410, y), (624, y - 1))
        pygame.draw.circle(surface, T.INK, (514, 62), 7)
        pygame.draw.circle(surface, (232, 72, 72), (514, 62), 6)
        surface.set_at((511, 59), (255, 200, 200))
        r = self.current()
        if not r:
            msg = '가방이 비었다' if not self.slots(cat='all') else '이 칸은 비었다'
            text(surface, msg, (518, 150), 'big', T.TEXT_SOFT, 'center')
            text(surface, '상점에서 사서 채우기', (518, 172), 'body', T.TEXT_SOFT, 'center')
            return
        key, item, count, cat = r
        spec = self.spec(item)
        kind = spec.get('kind')
        # 그림 칸 + 이름 + 종류 칩 + 보유
        box = pygame.Rect(418, 80, 53, 53)
        pygame.draw.rect(surface, TINT[cat], box)
        pygame.draw.rect(surface, T.WOOD[2], box, 1)
        surface.blit(self.icons.get(item, 3), (420, 82))
        if F.is_perfect(item):
            F.star_badge(surface, (box.right - 11, box.y + 2))
        lines, top, cy, y = self._head(item)
        for k, line in enumerate(lines):
            self._line(surface, line, (478, top + k * 16), 'big', T.TEXT)
        clabel, ccolor = KIND_CHIP.get(kind, ('물건', 'gray'))
        cr = chip(surface, (478, cy), clabel, ccolor)
        if F.is_perfect(item):
            chip(surface, (cr.right + 3, cy), '대성공 1.5배', 'gold')
        owned = count if kind == 'toy' else str(self.have(item))
        own = f"남은 {owned}" if kind == 'toy' else f"보유 {owned}"
        text(surface, own, (618, cy + 8), 'small', T.TEXT_SOFT, 'midright')
        if kind in ('snack', 'toy', 'food'):
            self._draw_use(surface, item, spec, y)
        elif kind == 'cure':
            self._draw_cure(surface, item, spec, y)
        elif kind == 'equip':
            self._draw_equip(surface, item, spec, y)
        elif kind == 'egg':
            self._draw_egg(surface, item, y)
        elif kind in ('prebattle', 'battle_item'):
            self._draw_battle(surface, item, spec, y)
        else:
            self._draw_material(surface, item, spec, y)

    def _line(self, surface, msg, pos, kind, color, anchor='midleft'):
        """쪽지 안 글씨 한 줄 + 넘침 점검 기록 (쪽지 글씨 칸 NX~NR을 넘으면 check_text_fit 위반)."""
        g = text(surface, msg, pos, kind, color, anchor)
        record(msg, g, pygame.Rect(NX - 4, g.y - 2, NR - NX + 6, g.h + 4), 'bag-note')
        return g

    def _effects(self, surface, item, spec, y, only_first=False):
        """효과 줄 (items.effect_lines, 숫자는 상점 목록). 마지막 줄 아래 y를 돌려준다."""
        lines = I.effect_lines(item, spec, self.catalog)
        if only_first:
            lines = lines[:1]
        for ic, msg, color in lines:
            if ic:
                icon(surface, ic, (NX, y))
            self._line(surface, msg, (NX + (15 if ic else 0), y + 6), 'body', color)
            y += 15
        return y

    def _animal_list(self, surface, y, title, value_of):
        """동물 목록 (쪽지). value_of(a) → (게이지 값, 게이지 색, 오른쪽 글씨, 글씨 색, 미리보기 값 또는 None)."""
        self._line(surface, title, (NX, y + 6), 'title', T.TEXT)
        top = y + 16
        self.list_rect = pygame.Rect(416, top, 204, max(ROW_STEP, 282 - top))
        animals = self.list_animals()
        rows = self._list_rows()
        for i, a in enumerate(animals[self.list_scroll:self.list_scroll + rows]):
            self._draw_animal_row(surface, self.row_rect(i), a, value_of)
        if len(animals) > rows:
            more = f"{self.list_scroll + 1}-{min(len(animals), self.list_scroll + rows)} / {len(animals)} · 휠"
            text(surface, more, (NR, y + 6), 'small', T.TEXT_SOFT, 'midright')

    def _draw_animal_row(self, surface, r, a, value_of):
        reason = self.busy_reason(a)
        sel = a['id'] == self.target and not reason
        card(surface, r, selected=sel)
        face = self.app.sprites.get(a['sprite'], 28).subsurface((2, 4, 24, 24))
        surface.blit(face, (r.x + 2, r.y + 3))
        val, color, right_text, right_color, after = value_of(a)
        if reason:
            right_text, right_color = reason, T.TEXT_SOFT
        rw = fit_width(right_text, 'small') if right_text else 0
        text_in(surface, a['name'], (r.x + 30, r.y + 2, r.w - 34 - rw, 15), 'body', T.TEXT_SOFT if reason else T.TEXT,
                align='left', tag='bag')
        if right_text:
            text_in(surface, right_text, (r.right - 4 - rw, r.y + 3, rw, 13), 'small', right_color, align='right',
                    tag='bag')
        bar = pygame.Rect(r.x + 30, r.y + 19, 110, 8)
        if val is not None:
            if sel and after is not None and after != val:
                gauge(surface, bar, after, 100, 'green')
                inner = bar.inflate(-4, -4)
                w = inner.w * max(0, min(100, val)) // 100
                pygame.draw.rect(surface, T.shade(color, 2), (inner.x, inner.y, w, inner.h))
            else:
                gauge(surface, bar, val, 100, color)
        if reason:
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((250, 240, 220, 110))
            surface.blit(veil, r.topleft)

    def _draw_use(self, surface, item, spec, y):
        y = self._effects(surface, item, spec, y, only_first=spec.get('kind') == 'toy')
        if item == F.BURNED:
            self._line(surface, '절반 확률로 거절', (NX, y + 6), 'small', T.TEXT_SOFT)
            y += 13
        stat = 'mood' if spec.get('kind') == 'toy' else 'fullness'
        gain = spec.get('mood', 0) if stat == 'mood' else (spec.get('fullness') or (spec.get('effects') or {}).get(
            'fullness', 0))

        def value_of(a):
            now = a[stat]
            lv = T.level(a, stat)
            if a['id'] == self.target:
                after = max(0, min(100, now + gain))
                return now, T.LEVEL_KIT[lv], f"{now}→{after}", T.OK, after
            return now, T.LEVEL_KIT[lv], str(now), T.TEXT_SOFT, None
        self._animal_list(surface, y + 4, '누구에게 줄까?', value_of)

    def _draw_cure(self, surface, item, spec, y):
        y = self._effects(surface, item, spec, y)
        if not self.list_animals():
            self._line(surface, '아픈 동물 없음', (518, y + 30), 'big', T.TEXT_SOFT, 'center')
            return

        def value_of(a):
            lv = T.level(a, 'fatigue')
            return a['fatigue'], T.LEVEL_KIT[lv], f"피로도 {a['fatigue']}", T.TEXT_SOFT, None
        self._animal_list(surface, y + 4, '누구를 치료할까?', value_of)

    def _draw_equip(self, surface, item, spec, y):
        y = self._effects(surface, item, spec, y, only_first=True)

        def value_of(a):
            eq = a.get('equip')
            txt = self.label(eq) if eq else '장비 없음'
            return None, 'gray', txt, T.TEXT_SOFT, None
        self._animal_list(surface, y + 4, '누구에게 장착할까?', value_of)

    def _draw_egg(self, surface, item, y):
        rate = I.EGG_SPECIAL_RATE.get(item, 0)
        self._line(surface, '특급 등장 확률', (NX, y + 6), 'body', T.TEXT)
        text(surface, f'{rate}%', (NR, y + 6), 'big', T.shade('gold', 1), 'midright')
        gauge(surface, (NX, y + 16, NR - NX, 10), rate, 100, 'gold')
        self._line(surface, '못 가진 동물 우선' if item == 'egg_special' else '중복이 나올 수 있음', (NX, y + 38), 'body',
                   T.TEXT_SOFT)
        self._line(surface, '사면 바로 부화 가능', (NX, y + 53), 'body', T.TEXT_SOFT)

    def _draw_battle(self, surface, item, spec, y):
        y = self._effects(surface, item, spec, y, only_first=True)
        self._line(surface, '쓰는 곳', (NX, y + 10), 'small', T.TEXT_SOFT)
        box = pygame.Rect(416, y + 18, 204, 36)
        card(surface, box)
        icon(surface, 'sword', (box.x + 6, box.y + 6))
        if spec.get('kind') == 'battle_item':
            where, sub, foot = '전투 중 아이템 버튼', '팀 행동 1번 사용', '전투 중이 아니면 못 씀'
        else:
            where, sub, foot = '전투장 · 출전 준비', '팀원에게 미리 먹이기', '출전 준비에서만 씀'
        text_in(surface, where, (box.x + 24, box.y + 2, box.w - 28, 16), 'body', align='left', tag='bag')
        text_in(surface, sub, (box.x + 24, box.y + 18, box.w - 28, 14), 'small', T.TEXT_SOFT, align='left', tag='bag')
        self._line(surface, foot, (518, 320), 'small', T.TEXT_SOFT, 'center')

    def _draw_material(self, surface, item, spec, y):
        kind = spec.get('kind')
        uses = self._mat_uses(item)
        self._line(surface, '쓰는 곳', (NX, y + 6), 'small', T.TEXT_SOFT)
        if len(uses) > 2:
            text(surface, f"외 {len(uses) - 2}개", (NR, y + 6), 'small', T.TEXT_SOFT, 'midright')
        y += 14
        if not uses:
            box = pygame.Rect(416, y, 204, 22)
            card(surface, box)
            text_in(surface, '아직 쓰는 요리 없음', card_inner(box), 'body', T.TEXT_SOFT, tag='bag')
            y += 26
        for key, title, sub in uses[:2]:
            box = pygame.Rect(416, y, 204, 32)
            card(surface, box)
            img = self.icons.get(key, 1) if key.startswith('seed_') else self.food_icons.get(key, 1)
            surface.blit(img, (box.x + 5, box.centery - 8))
            text_in(surface, title, (box.x + 24, box.y + 2, box.w - 28, 15), 'body', align='left', tag='bag')
            text_in(surface, sub, (box.x + 24, box.y + 16, box.w - 28, 13), 'small', T.TEXT_SOFT, align='left', tag='bag')
            y += 34
        self._line(surface, f"얻는 곳: {self.sources(item)}", (NX, y + 6), 'small', T.TEXT)
        y += 14
        if spec.get('sell') is not None:
            self._line(surface, f"판매가 {spec['sell']:,}코인", (NX, y + 6), 'small', T.TEXT_SOFT)
            y += 14
        foot = '밭에서 심기 · 여기서는 못 씀' if kind == 'seed' else '요리 재료 · 여기서는 못 씀'
        self._line(surface, foot, (518, 336), 'small', T.TEXT_SOFT, 'center')

    def sources(self, item):
        """얻는 곳 (주방과 같은 규칙, 백엔드 값): 작물 = 밭, 사냥 보상 = 사냥터 · 이름, 살 수 있으면 상점."""
        spec = self.spec(item)
        out = []
        if spec.get('kind') == 'crop':
            out.append('밭')
        areas = [a.get('label', k) for k, a in self.hunts.items() if a.get('item') == item]
        if areas:
            out.append('사냥터 · ' + '/'.join(areas))
        if spec.get('buy') is not None:
            out.append('상점')
        return ' / '.join(out) or '없음'
