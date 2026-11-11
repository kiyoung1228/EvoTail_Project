"""집(주방): 레시피 북 → 요리 미니게임 → 결과, 음식 주기. (목업 docs/mockups/home/)

- 레시피 북 (home_1_book, home_1b_missing): 책갈피 탭 "레시피 / 음식 주기". 왼쪽 레시피 그림·이름·별
  (재료가 모자라면 회색), 오른쪽 큰 그림·설명·재료(가진 수/필요 수, 모자라면 빨강 + 구하는 곳)·먹으면 효과·요리 시작
- 미니게임 (home_2_bar): 커서가 막대 끝에서 끝으로 레시피 travel_seconds 동안 움직이고, 목표 중심은
  target_center_min~max 중 무작위. 중심 ± good_half_width = Good, ± perfect_half_width = Perfect.
  Space(또는 클릭) 한 번에 판정, timeout_seconds 안에 안 누르면 miss → cook(recipe, judgment)
- 결과 (home_3_result): outcome(great / success / rescued / burnt)별 리본·그림·효과·경험치·레벨 게이지
- 음식 주기 (home_4_feed): 만든 요리 → 동물 고르기(포만감 미리보기) → use_item(item, key)
게임 규칙은 없다: 재료·효과·별·경험치·레벨·판정 숫자는 전부 백엔드 값 (get_recipes, get_rules()['cooking'],
get_shop_catalog, get_hunts, 스냅샷 inventory·animals).
"""
import math
import random
import pygame

from .. import theme as T
from .. import widgets as W
from .. import food as F
from ..app import Scene
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, chip_width, icon,
                       gauge, tooltip, record, Button, BUTTON_H, CARD_LABEL_H)
from ..widgets import wrap2, shorten

BOOK = pygame.Rect(14, 62, 612, 292)
LEFT = pygame.Rect(24, 70, 300, 276)          # 왼쪽 쪽 (책 panel 안)
RIGHT = pygame.Rect(340, 70, 276, 276)        # 오른쪽 쪽
LEVEL = pygame.Rect(420, 31, 212, 22)         # 요리 레벨 칸 (오른쪽 위)
CELL = (72, 83)                               # 레시피·요리 칸 (이름 두 줄까지: 그림 32 + 글씨 15×2 + 별/개수)
GRID = (LEFT.x + 3, 89, 74, 86)               # 시작 x, y, 가로 간격, 세로 간격 (4열 × 3줄)
COLS, GRID_ROWS = 4, 3
NAME_Y = 36                                   # 칸 안 이름 첫 줄 (두 줄 = 36~66)
ING = (RIGHT.x + 12, 166, 126, 32, 130, 34)   # 재료 칸 x, y, w, h, 가로 간격, 세로 간격 (2열)
LIST = pygame.Rect(RIGHT.x + 12, 150, 256, 32)   # 동물 줄 (첫 줄)
LIST_STEP, LIST_ROWS = 34, 4
BAR = pygame.Rect(120, 264, 400, 22)          # 미니게임 막대
BAR_PANEL = pygame.Rect(105, 246, 430, 70)
TITLE_CARD = pygame.Rect(210, 60, 220, 36)
TIME_CARD = pygame.Rect(520, 60, 106, 34)
RES = pygame.Rect(170, 66, 300, 284)          # 결과 창
YELLOW = (250, 204, 70)                       # Perfect 구간 (밤 아이콘과 같은 노랑)
BAR_BG = (88, 66, 58)
JUDGE_SHOW = 0.8                              # 판정 글씨를 보여 주는 시간(초) 뒤 결과 화면

EFFECTS = (('fullness', 'meat', '포만감'), ('mood', 'smile', '기분'), ('fatigue', 'zzz', '피로도'))
JUDGE_TEXT = {'perfect': 'PERFECT!', 'good': 'GOOD!', 'miss': 'MISS'}
JUDGE_COLOR = {'perfect': T.shade('orange', 1), 'good': T.shade('orange', 1), 'miss': T.shade('gray', 1)}
RESULT = {   # outcome → 리본 글씨, 리본 색, 큰 글씨, 아래 설명
    'great': ('대성공!', 'green', 'PERFECT', '효과 1.5배!'),
    'success': ('성공!', 'green', 'GOOD', '맛있게 완성!'),
    'rescued': ('아슬아슬 성공!', 'brown', 'MISS', '아슬아슬 성공! (경험치 없음)'),
    'burnt': ('탄 요리...', 'red', 'MISS', '재료가 타 버림 (경험치 없음)'),
}
ACTIVITY_LABEL = {'training': '훈련 중', 'hunting': '사냥 중'}


def effect_parts(effects):
    """[(아이콘, 글씨, 색)] — 0이 아닌 효과만. 피로도는 오르면 나쁨."""
    out = []
    for key, ic, label in EFFECTS:
        v = (effects or {}).get(key, 0)
        if not v:
            continue
        good = v < 0 if key == 'fatigue' else v > 0
        out.append((ic, f"{label} {v:+d}", T.OK if good else T.BAD))
    return out


EFFECT_GAP, EFFECT_LINE_H = 10, 13


def draw_effects(surface, pos, effects, kind='body', center=False, max_w=None):
    """아이콘 + '포만감 +30' 들. center=True면 pos가 가운데.
    max_w를 주면 그 폭(오른쪽 2px 여백) 안에 들어가게 효과 단위로 줄을 나눈다 (글자 크기는 그대로).
    그린 줄 수를 돌려준다. max_w가 있으면 넘침 점검(check_text_fit)에도 기록한다."""
    parts = effect_parts(effects)
    widths = [15 + glyph_box(s, kind).w for _, s, _ in parts]
    lines, cur, cur_w = [], [], 0
    for part, w in zip(parts, widths):
        add = w + (EFFECT_GAP if cur else 0)
        if cur and max_w and cur_w + add > max_w - 2:
            lines.append((cur, cur_w))
            cur, cur_w, add = [], 0, w
        cur.append((part, w))
        cur_w += add
    if cur:
        lines.append((cur, cur_w))
    for li, (row, total) in enumerate(lines):
        y = pos[1] + li * EFFECT_LINE_H
        x = pos[0] - total // 2 if center else pos[0]
        start = x
        for (ic, s, color), w in row:
            icon(surface, ic, (x, y))
            text_in(surface, s, (x + 15, y - 2, w - 15, 16), kind, color, align='left', pad=0, log=False)
            x += w + EFFECT_GAP
        if max_w and not center:
            record(' · '.join(p[1] for p, _ in row), pygame.Rect(start, y, total, 12),
                   pygame.Rect(pos[0] - 2, y - 3, max_w + 2, 18), 'kitchen-effects')
    return max(1, len(lines))


def fill_part(surface, inner, x0, x1, color):
    """게이지 안쪽에 [x0, x1) 구간을 색으로 (gauge와 같은 윗줄 밝게 / 아랫줄 어둡게)."""
    if x1 <= x0:
        return
    dark, mid, base, light = T.PALETTE[color] if isinstance(color, str) else color
    pygame.draw.rect(surface, base, (x0, inner.y, x1 - x0, inner.h))
    pygame.draw.line(surface, light, (x0, inner.y), (x1 - 1, inner.y))
    if inner.h > 2:
        pygame.draw.line(surface, mid, (x0, inner.bottom - 1), (x1 - 1, inner.bottom - 1))


class KitchenScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.mode = 'book'          # 'book' / 'cook' / 'result'
        self.tab = 'recipe'         # 책갈피: 'recipe' / 'feed'
        self.recipe = None          # 고른 레시피 id
        self.dish = None            # 음식 주기: 고른 요리 아이템 id
        self.target = None          # 음식 주기: 고른 동물 id
        self.scroll = 0
        self.dish_scroll = 0        # 음식 주기: 요리 칸 줄 넘김 (3줄 넘을 때)
        self.info = {'level': 1, 'xp': 0, 'recipes': {}}
        self.rules = {}
        self.catalog = {}
        self.hunt_items = set()
        self.icons = F.FoodIcons()
        self.game = None            # 미니게임 상태
        self.result = None          # cook 결과
        self.before = None          # 요리 전 (레벨, 누적 경험치)
        self.hover = None
        self.buttons = []
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    # ---------- 백엔드 값 ----------
    def enter(self):
        self.mode = 'book'
        self.game = None
        self.result = None
        self.scroll = 0
        self._load()
        keys = list(self.recipes)
        if self.recipe not in keys:
            self.recipe = next((k for k in keys if self.can_cook(k)), keys[0] if keys else None)
        self._fix_feed_selection()

    def _load(self):
        self.info = self.app.call('get_recipes') or self.info
        if not self.rules:
            self.rules = (self.app.call('get_rules') or {}).get('cooking', {})
        if not self.catalog:
            self.catalog = self.app.call('get_shop_catalog') or {}
        if not self.hunt_items:
            areas = (self.app.call('get_hunts') or {}).get('areas', {})
            self.hunt_items = {a.get('item') for a in areas.values()}

    def _reload(self):
        """상태가 바뀐 뒤 (요리·음식 주기): 레시피 정보(레벨·경험치)를 다시 읽는다."""
        self.info = self.app.call('get_recipes') or self.info

    @property
    def recipes(self):
        return self.info.get('recipes', {})

    def have(self, item):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(item, 0)

    def missing(self, key):
        r = self.recipes.get(key)
        return [i for i, n in r['ingredients'].items() if self.have(i) < n] if r else []

    def can_cook(self, key):
        return bool(self.recipes.get(key)) and not self.missing(key)

    def sources(self, item):
        """재료를 구하는 곳 (백엔드 값으로 판단): 작물 = 밭, 사냥 보상 = 사냥터, 살 수 있으면 상점."""
        spec = self.catalog.get(item) or {}
        out = []
        if spec.get('kind') == 'crop':
            out.append('밭')
        if item in self.hunt_items:
            out.append('사냥터')
        if spec.get('buy') is not None:
            out.append('상점')
        return '/'.join(out) or '?'

    def level_span(self, xp):
        """누적 경험치 → (레벨, 이 레벨 시작 경험치, 다음 레벨 경험치 또는 None). 기준은 get_rules level_thresholds."""
        th = self.rules.get('level_thresholds') or [0]
        lv = max(i + 1 for i, t in enumerate(th) if xp >= t)
        return lv, th[lv - 1], (th[lv] if lv < len(th) else None)

    def dishes(self):
        """가진 요리 아이템 (레시피 순서, 대성공 먼저, 탄 요리 마지막)."""
        out = []
        for key, r in self.recipes.items():
            for item in (r.get('perfect_item'), r.get('regular_item')):
                if item and self.have(item) > 0:
                    out.append(item)
        if self.have(F.BURNED) > 0:
            out.append(F.BURNED)
        return out

    def visible_dishes(self):
        dishes = self.dishes()
        rows = (len(dishes) + COLS - 1) // COLS
        self.dish_scroll = max(0, min(self.dish_scroll, rows - GRID_ROWS))
        return dishes[self.dish_scroll * COLS:(self.dish_scroll + GRID_ROWS) * COLS]

    def animals(self):
        return self.app.state.get('animals', [])

    def busy_reason(self, a):
        """음식을 못 주는 이유 (백엔드 use_item 조건: 활동 중·전투 중). 없으면 None."""
        act = a.get('activity')
        if act:
            return ACTIVITY_LABEL.get(act.get('kind'), '활동 중')
        battle = self.app.state.get('battle') or {}
        if a['id'] in [f.get('id') for f in battle.get('player', [])]:
            return '전투 중'
        return None

    def _fix_feed_selection(self):
        dishes = self.dishes()
        if self.dish not in dishes:
            self.dish = dishes[0] if dishes else None
        ids = [a['id'] for a in self.animals()]
        if self.target not in ids:
            free = [a['id'] for a in self.animals() if not self.busy_reason(a)]
            self.target = (free or ids or [None])[0]

    # ---------- 칸 위치 ----------
    @staticmethod
    def cell_rect(i):
        return pygame.Rect(GRID[0] + (i % COLS) * GRID[2], GRID[1] + (i // COLS) * GRID[3], *CELL)

    @staticmethod
    def tab_rect(tab):
        w = Button.width_for('음식 주기') + 8
        x = 196 if tab == 'recipe' else 196 + w + 4
        return pygame.Rect(x, 42, w, 22)

    @staticmethod
    def ing_rect(i):
        x, y, w, h, dx, dy = ING
        return pygame.Rect(x + (i % 2) * dx, y + (i // 2) * dy, w, h)

    @staticmethod
    def row_rect(i):
        return LIST.move(0, i * LIST_STEP)

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if self.mode == 'cook':
            self._handle_cook(event)
        elif self.mode == 'result':
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.mode = 'book'
        else:
            self._handle_book(event)

    def _handle_book(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
            return
        if event.type == pygame.MOUSEWHEEL and self.tab == 'feed':
            n = len(self.animals())
            if pygame.Rect(LIST.x, LIST.y, LIST.w, LIST_STEP * LIST_ROWS).collidepoint(W.mouse_pos()):
                self.scroll = max(0, min(max(0, n - LIST_ROWS), self.scroll - event.y))
            elif LEFT.collidepoint(W.mouse_pos()):
                rows = (len(self.dishes()) + COLS - 1) // COLS
                self.dish_scroll = max(0, min(max(0, rows - GRID_ROWS), self.dish_scroll - event.y))
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for tab in ('recipe', 'feed'):
            if self.tab_rect(tab).collidepoint(event.pos):
                self.tab = tab
                self._fix_feed_selection()
                return
        if self.tab == 'recipe':
            for i, key in enumerate(self.recipes):
                if self.cell_rect(i).collidepoint(event.pos):
                    self.recipe = key
                    return
        else:
            for i, item in enumerate(self.visible_dishes()):
                if self.cell_rect(i).collidepoint(event.pos):
                    self.dish = item
                    return
            for i, a in enumerate(self.animals()[self.scroll:self.scroll + LIST_ROWS]):
                if self.row_rect(i).collidepoint(event.pos):
                    self.target = a['id']
                    return

    def _handle_cook(self, event):
        g = self.game
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and g['judgment'] is None:
            self.mode = 'book'          # 그만두기 (아직 cook을 안 불렀으니 재료는 그대로)
            self.game = None
            self.app.toast('요리 중단 · 재료는 그대로', 'info', 'snack')
            return
        pressed = (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or \
                  (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and BAR_PANEL.collidepoint(event.pos))
        if pressed and g['judgment'] is None:
            self._judge(self._judgment_at(g['pos']))

    # ---------- 요리 ----------
    def start_cooking(self, key=None):
        key = key or self.recipe
        if not self.can_cook(key):
            self.app.toast('재료 부족', 'bad', 'snack')
            return
        t = self.rules.get('timing', {})
        r = self.recipes[key]
        self.recipe = key
        self.game = {
            'recipe': key,
            'min': t.get('min_position', 0), 'max': t.get('max_position', 100),
            'center': random.uniform(t.get('target_center_min', 20), t.get('target_center_max', 80)),
            'perfect': t.get('perfect_half_width', 5), 'good': t.get('good_half_width', 15),
            'travel': r.get('travel_seconds') or 1.0, 'timeout': t.get('timeout_seconds', 5),
            'elapsed': 0.0, 'pos': t.get('min_position', 0), 'judgment': None, 'shown': 0.0,
        }
        self.mode = 'cook'
        self.app.toast_item = None

    def _judgment_at(self, pos):
        d = abs(pos - self.game['center'])
        if d <= self.game['perfect']:
            return 'perfect'
        if d <= self.game['good']:
            return 'good'
        return 'miss'

    def _judge(self, judgment):
        g = self.game
        g['judgment'] = judgment
        self.before = (self.info.get('level', 1), self.info.get('xp', 0))
        self.result = self.app.act('cook', None, recipe=g['recipe'], judgment=judgment)
        if self.result is None:         # 백엔드가 거절 (재료가 그새 없어짐 등) → 책으로
            self.mode = 'book'
            self.game = None
        self._reload()
        self._fix_feed_selection()

    def update(self, dt):
        if self.mode == 'cook' and self.game:
            g = self.game
            if g['judgment'] is None:
                g['elapsed'] += dt
                # 끝 → 끝 한 번 = travel 초 (삼각파로 왕복)
                phase = (g['elapsed'] / g['travel']) % 2
                frac = phase if phase <= 1 else 2 - phase
                g['pos'] = g['min'] + (g['max'] - g['min']) * frac
                if g['elapsed'] >= g['timeout']:
                    self._judge('miss')
            else:
                g['shown'] += dt
                if g['shown'] >= JUDGE_SHOW and self.result is not None:
                    self.mode = 'result'
        self._build_buttons()

    def _build_buttons(self):
        self.buttons = []
        if self.mode == 'book' and self.tab == 'recipe' and self.recipe in self.recipes:
            ok = self.can_cook(self.recipe)
            rect = pygame.Rect(RIGHT.x + 72, 316, 170, 26)
            if ok:
                self.buttons.append(Button(rect, '요리 시작!', self.start_cooking, 'orange', icon='snack'))
            else:
                self.buttons.append(Button(rect, '재료 부족', None, 'gray', enabled=False))
        elif self.mode == 'book' and self.tab == 'feed' and self.dish:
            a = self.app.animal(self.target)
            label = f"{a['name']}에게 주기" if a else '동물 선택'
            w = max(170, Button.width_for(label, icon=True) + 8)
            rect = pygame.Rect(RIGHT.centerx - w // 2, 316, w, 26)
            self.buttons.append(Button(rect, label, self.feed, 'green', enabled=bool(a and not self.busy_reason(a)),
                                       icon='heart'))
        elif self.mode == 'result' and self.result:
            key = self.game['recipe'] if self.game else self.recipe
            y = RES.y + 244
            self.buttons.append(Button((RES.x + 20, y, 124, 28), '한 번 더', lambda: self.start_cooking(key),
                                       'orange', enabled=self.can_cook(key), icon='snack'))
            self.buttons.append(Button((RES.x + 156, y, 124, 28), '동물에게 주기', self.feed_result, 'green',
                                       icon='heart'))

    def feed_result(self):
        """결과 → 음식 주기 탭 (방금 만든 요리를 골라 둔다)."""
        self.mode = 'book'
        self.tab = 'feed'
        self.dish = self.result.get('item') if self.result else None
        self._fix_feed_selection()

    # ---------- 음식 주기 ----------
    def feed(self):
        a = self.app.animal(self.target)
        item = self.dish
        if not a or not item:
            return
        name = F.dish_name(item, self.catalog, self.recipes)
        before = a['fullness']
        data = self.app.act('use_item', None, item=item, key=a['id'])
        if data is None:
            return
        if data.get('refused'):
            self.app.toast(f"{T.josa(a['name'], '이')} {T.josa(name, '을')} 안 먹었다", 'bad', 'frown')
        else:
            self.app.toast(f"{T.josa(a['name'], '이')} {T.josa(name, '을')} 먹었다! 포만감 {before}→{data['fullness']}",
                           'ok', 'heart')
        self._reload()
        self._fix_feed_selection()

    # ---------- 그리기 ----------
    def toast_anchor(self):
        if self.mode == 'cook':
            return 'midbottom', (T.WIDTH // 2, BAR_PANEL.y - 4)
        return 'topright', (T.WIDTH - 8, LEVEL.bottom + 4)

    def draw(self, surface):
        surface.blit(kitchen_image(), (0, 0))
        if self.mode == 'result':
            surface.blit(_dim(), (0, 0))
        title = {'book': '집 · 주방', 'cook': '요리 중', 'result': '요리 완성'}[self.mode]
        self.back.draw(surface)
        ribbon(surface, (78, 33, max(92, fit_width(title, 'title', shadow=True) + 14), 18), title, 'red')
        self._draw_level(surface)
        self.hover = None
        if self.mode == 'cook':
            self._draw_cook(surface)
        elif self.mode == 'result':
            self._draw_result(surface)
        else:
            self._draw_book(surface)
        for b in self.buttons:
            b.draw(surface)
        if self.hover:
            tooltip(surface, self.hover[0], self.hover[1], 'below')

    def _draw_level(self, surface, rect=LEVEL):
        lv, lo, hi = self.level_span(self.info.get('xp', 0))
        xp = self.info.get('xp', 0)
        card(surface, rect)
        inner = card_inner(rect)
        label = f'요리 Lv.{lv}'
        g = text_in(surface, label, (inner.x, inner.y, fit_width(label, 'title'), inner.h), 'title', align='left')
        nums = f'{xp}/{hi}' if hi else f'{xp} MAX'          # 목업: 누적 / 다음 레벨 기준
        nw = fit_width(nums, 'small')
        text_in(surface, nums, (inner.right - nw, inner.y, nw, inner.h), 'small', T.TEXT_SOFT, align='right')
        bar = pygame.Rect(g.right + 6, inner.centery - 5, inner.right - nw - 4 - g.right - 6, 10)
        gauge(surface, bar, (xp - lo) if hi else 1, (hi - lo) if hi else 1, 'orange')

    # ----- 책 -----
    def _draw_book(self, surface):
        for tab in ('recipe', 'feed') if self.tab == 'feed' else ('feed', 'recipe'):
            active = tab == self.tab
            r = self.tab_rect(tab)
            if not active:
                r = r.move(0, 4).inflate(0, -2)
            Button(r, '레시피' if tab == 'recipe' else '음식 주기', None, 'red' if tab == 'recipe' else 'green',
                   enabled=True).draw(surface)
        panel(surface, BOOK)
        # 가운데 책등 + 쪽 줄
        spine = pygame.Rect(LEFT.right + 3, BOOK.y + 6, RIGHT.x - LEFT.right - 6, BOOK.h - 12)
        pygame.draw.rect(surface, T.WOOD[1], spine)
        pygame.draw.line(surface, T.WOOD[0], spine.topleft, spine.bottomleft)
        pygame.draw.line(surface, T.WOOD[0], (spine.right - 1, spine.y), (spine.right - 1, spine.bottom - 1))
        for page in (LEFT, RIGHT):
            for y in range(page.y + 26, page.bottom - 4, 16):
                pygame.draw.line(surface, (240, 226, 198), (page.x + 4, y), (page.right - 5, y))
        if self.tab == 'recipe':
            self._draw_recipes(surface)
            self._draw_recipe_detail(surface)
        else:
            self._draw_dishes(surface)
            self._draw_feed_detail(surface)

    def _draw_cell(self, surface, i, item, name, selected, gray=False, sub=None, stars_n=None):
        r = self.cell_rect(i)
        card(surface, r, selected=selected)
        img = self.icons.get(item, 2, gray)
        surface.blit(img, img.get_rect(midtop=(r.centerx, r.y + 4)))
        if F.is_perfect(item):
            F.star_badge(surface, (r.x + 4, r.y + 4))
        # 이름: 칸에 안 들어가면 두 줄 (한 줄이면 두 줄 자리의 가운데)
        fixed = F.CELL_LINES.get(F.recipe_of(item)) if item != F.BURNED else None
        lines = list(fixed) if fixed else wrap2(name, r.w - 4 - 4, 'body')
        top = r.y + NAME_Y + (15 if len(lines) == 1 else 0) // 2
        for k, line in enumerate(lines):
            text_in(surface, line, (r.x + 2, top + k * 15, r.w - 4, 15), 'body', T.TEXT_SOFT if gray else T.TEXT,
                    tag='kitchen')
        bottom = r.y + NAME_Y + 30
        if stars_n is not None:
            F.stars(surface, (r.centerx - F.STARS_W // 2, bottom + 2), stars_n)
        if sub:
            text_in(surface, sub, (r.x + 2, bottom, r.w - 4, 15), 'title', tag='kitchen')
        if r.collidepoint(W.mouse_pos()) and ''.join(lines).replace(' ', '') != name.replace(' ', '').replace('…', ''):
            self.hover = (name, r)          # 칸에서 줄이거나 뺀 글자가 있을 때만 전체 이름

    def _draw_recipes(self, surface):
        text_in(surface, '레시피', (LEFT.x, LEFT.y + 2, LEFT.w, 16), 'title', tag='kitchen')
        for i, (key, r) in enumerate(self.recipes.items()):
            self._draw_cell(surface, i, key, r['label'], key == self.recipe, gray=not self.can_cook(key),
                            stars_n=r['stars'])

    def _draw_recipe_detail(self, surface):
        key = self.recipe
        r = self.recipes.get(key)
        if not r:
            return
        x0 = RIGHT.x + 12
        surface.blit(self.icons.get(key, 4), (x0, RIGHT.y + 8))
        tx = x0 + 72
        text(surface, r['label'], (tx, RIGHT.y + 12), 'big')
        F.stars(surface, (tx, RIGHT.y + 32), r['stars'])
        text(surface, F.DESCRIPTION.get(key, ''), (tx, RIGHT.y + 44), 'body', T.TEXT_SOFT)
        # 재료
        y = ING[1] - 16
        text(surface, '재료', (x0, y), 'title')
        missing = self.missing(key)
        if missing:
            text(surface, f'{len(missing)}가지 부족', (RIGHT.right - 12, y), 'title', T.BAD, anchor='topright')
        for i, (item, need) in enumerate(r['ingredients'].items()):
            self._draw_ingredient(surface, self.ing_rect(i), item, need)
        rows = (len(r['ingredients']) + 1) // 2
        y = ING[1] + rows * ING[5] + 4
        text(surface, '먹으면', (x0, y), 'title')
        effects = (self.catalog.get(r.get('regular_item')) or {}).get('effects', {})
        n = draw_effects(surface, (x0 + 48, y), effects, max_w=RIGHT.right - 8 - (x0 + 48))
        y += (n - 1) * EFFECT_LINE_H        # 효과가 두 줄이면 아래 글을 한 줄만큼 내림
        mult = self.rules.get('perfect_multiplier', 1.5)
        xp = (self.rules.get('xp_per_star') or {}).get(r['stars'], (self.rules.get('xp_per_star') or {}).get(
            str(r['stars']), 0))
        text(surface, f'대성공이면 {mult:g}배 · 경험치 +{xp}', (x0, y + 16), 'body', T.WARN)

    def _draw_ingredient(self, surface, rect, item, need):
        have = self.have(item)
        ok = have >= need
        card(surface, rect)
        if not ok:
            pygame.draw.rect(surface, T.shade('red', 2), rect.inflate(-2, -2), 2)
        surface.blit(self.icons.get(item, 1), (rect.x + 5, rect.y + 8))
        inner = card_inner(rect)
        nx = rect.x + 24
        count = f'{have}/{need}'
        cw = fit_width(count, 'title')
        text_in(surface, count, (inner.right - cw, inner.y, cw, 15), 'title', T.OK if ok else T.BAD, tag='kitchen')
        name = shorten(F.item_name(item, self.catalog), inner.right - cw - nx - 4, 'title')
        text_in(surface, name, (nx, inner.y, inner.right - cw - nx, 15), 'title', align='left', tag='kitchen')
        sub = '충분함!' if ok else f'구하기: {self.sources(item)}'
        text_in(surface, sub, (nx, inner.y + 15, inner.right - nx, 13), 'small', T.OK if ok else T.BAD,
                align='left', tag='kitchen')

    # ----- 음식 주기 -----
    def _draw_dishes(self, surface):
        text_in(surface, '만든 요리', (LEFT.x, LEFT.y + 2, LEFT.w, 16), 'title', tag='kitchen')
        dishes = self.dishes()
        for i, item in enumerate(self.visible_dishes()):
            self._draw_cell(surface, i, item, F.dish_name(item, self.catalog, self.recipes).replace('대성공 ', ''),
                            item == self.dish, sub=f'×{self.have(item)}')
        if not dishes:
            text(surface, '아직 만든 요리 없음', (LEFT.centerx, LEFT.y + 110), 'title', T.TEXT_SOFT, 'center')
            text(surface, '레시피 탭에서 요리하기', (LEFT.centerx, LEFT.y + 128), 'body', T.TEXT_SOFT, 'center')
        if len(dishes) > COLS * GRID_ROWS:       # 휠로 넘기기 표시
            rows = (len(dishes) + COLS - 1) // COLS
            more = f'{self.dish_scroll + 1}-{self.dish_scroll + GRID_ROWS} / {rows}줄 · 휠'
            text(surface, more, (LEFT.right - 6, LEFT.y + 4), 'small', T.TEXT_SOFT, anchor='topright')

    def _draw_feed_detail(self, surface):
        x0 = RIGHT.x + 12
        item = self.dish
        if item:
            surface.blit(self.icons.get(item, 3), (x0, RIGHT.y + 6))
            if F.is_perfect(item):
                F.star_badge(surface, (x0 + 44, RIGHT.y + 6))
            name = F.dish_name(item, self.catalog, self.recipes)
            text(surface, name, (x0 + 58, RIGHT.y + 10), 'big')
            effects = (self.catalog.get(item) or {}).get('effects', {})
            n = draw_effects(surface, (x0 + 58, RIGHT.y + 30), effects, max_w=RIGHT.right - 8 - (x0 + 58))
            if item == F.BURNED:
                text(surface, '절반 확률로 거절', (x0 + 58, RIGHT.y + 31 + n * EFFECT_LINE_H), 'body', T.TEXT_SOFT)
        else:
            text(surface, '줄 요리 없음', (x0, RIGHT.y + 14), 'big', T.TEXT_SOFT)
        text(surface, '누구에게 줄까?', (x0, LIST.y - 16), 'title')
        animals = self.animals()
        gain = ((self.catalog.get(item) or {}).get('effects') or {}).get('fullness', 0) if item else 0
        for i, a in enumerate(animals[self.scroll:self.scroll + LIST_ROWS]):
            self._draw_animal_row(surface, self.row_rect(i), a, gain)
        if len(animals) > LIST_ROWS:       # 휠로 넘기기 표시
            more = f'{self.scroll + 1}-{min(len(animals), self.scroll + LIST_ROWS)} / {len(animals)} · 휠'
            text(surface, more, (RIGHT.right - 12, LIST.y - 15), 'small', T.TEXT_SOFT, anchor='topright')

    def _draw_animal_row(self, surface, r, a, gain):
        selected = a['id'] == self.target
        reason = self.busy_reason(a)
        card(surface, r, selected=selected and not reason)
        sprite = self.app.sprites.get(a['sprite'], 28)
        surface.blit(sprite, (r.x + 4, r.y + 2))
        inner = card_inner(r)
        chip_label = reason or ('배고픔' if T.level(a, 'fullness') == '나쁨' else None)
        cw = chip_width(chip_label) if chip_label else 0
        nx = r.x + 36
        name = shorten(a['name'], inner.right - nx - cw - 8, 'title')
        text_in(surface, name, (nx, inner.y, inner.right - nx - cw - 4, 15), 'title', align='left', tag='kitchen')
        if chip_label:
            chip(surface, (inner.right - 2, inner.y + 1), chip_label, 'gray' if reason else 'red', anchor='topright')
        icon(surface, 'meat', (nx, r.y + 17))
        bar = pygame.Rect(nx + 14, r.y + 19, 104, 9)
        now = a['fullness']
        color = T.LEVEL_KIT[T.level(a, 'fullness')]
        if selected and gain and not reason:
            after = max(0, min(100, now + gain))           # 미리보기 (실제 값은 use_item 결과)
            gauge(surface, bar, 0, 100, color)
            inner_bar = bar.inflate(-4, -4)
            fill_part(surface, inner_bar, inner_bar.x, inner_bar.x + inner_bar.w * now // 100, color)
            fill_part(surface, inner_bar, inner_bar.x + inner_bar.w * now // 100, inner_bar.x + inner_bar.w * after // 100,
                      [T.shade('green', 1), T.shade('green', 2), T.shade('green', 3), (200, 236, 180)])
            label, col = f'{now}→{after}', T.OK
        else:
            gauge(surface, bar, now, 100, color)
            label, col = f'{now}', T.TEXT_SOFT
        text(surface, label, (bar.right + 5, bar.centery), 'small', col, anchor='midleft')
        if reason:
            veil = pygame.Surface(r.size, pygame.SRCALPHA)
            veil.fill((250, 240, 220, 120))
            surface.blit(veil, r.topleft)

    # ----- 미니게임 -----
    def _draw_cook(self, surface):
        g = self.game
        r = self.recipes[g['recipe']]
        # 제목 칸: 이름 + 별
        card(surface, TITLE_CARD)
        text_in(surface, r['label'], (TITLE_CARD.x + 2, TITLE_CARD.y + 3, TITLE_CARD.w - 4, 16), 'title', tag='kitchen')
        F.stars(surface, (TITLE_CARD.centerx - F.STARS_W // 2, TITLE_CARD.y + 21), r['stars'])
        # 남은 시간
        card(surface, TIME_CARD)
        inner = card_inner(TIME_CARD)
        text_in(surface, '남은 시간', (inner.x + 2, inner.y, inner.w - 4, 14), 'small', T.TEXT_SOFT, align='left',
                tag='kitchen')
        left = max(0.0, 1 - g['elapsed'] / g['timeout']) if g['timeout'] else 0
        gauge(surface, (inner.x + 2, inner.y + 15, inner.w - 4, 10), left, 1, 'red' if left < 0.3 else 'orange')
        # 프라이팬 + 재료
        self._draw_pan(surface, r)
        # 막대
        panel(surface, BAR_PANEL)
        pygame.draw.rect(surface, BAR_BG, BAR)
        span = g['max'] - g['min']
        to_x = lambda p: BAR.x + round((p - g['min']) / span * BAR.w)
        gl, gr = to_x(max(g['min'], g['center'] - g['good'])), to_x(min(g['max'], g['center'] + g['good']))
        pl, pr = to_x(max(g['min'], g['center'] - g['perfect'])), to_x(min(g['max'], g['center'] + g['perfect']))
        pygame.draw.rect(surface, T.shade('orange', 2), (gl, BAR.y, gr - gl, BAR.h))
        pygame.draw.rect(surface, YELLOW, (pl, BAR.y, pr - pl, BAR.h))
        pygame.draw.line(surface, T.shade('orange', 3), (gl, BAR.y), (gr - 1, BAR.y))
        pygame.draw.rect(surface, T.INK, BAR.inflate(2, 2), 1)
        lab_y = BAR.bottom + 3
        text(surface, 'Good', ((gl + pl) // 2, lab_y), 'small', T.WARN, 'midtop')
        text(surface, 'Perfect', ((pl + pr) // 2, lab_y), 'small', T.TEXT, 'midtop')
        text(surface, 'Good', ((pr + gr) // 2, lab_y), 'small', T.WARN, 'midtop')
        # 커서 (위 삼각형 + 세로줄)
        cx = to_x(g['pos'])
        pygame.draw.line(surface, T.WHITE, (cx, BAR.y - 2), (cx, BAR.bottom + 1))
        pygame.draw.line(surface, T.INK, (cx + 1, BAR.y - 2), (cx + 1, BAR.bottom + 1))
        tri = [(cx - 4, BAR.y - 9), (cx + 4, BAR.y - 9), (cx, BAR.y - 3)]
        pygame.draw.polygon(surface, T.WHITE, tri)
        pygame.draw.polygon(surface, T.INK, tri, 1)
        # 안내 / 판정
        if g['judgment'] is None:
            self._draw_space_hint(surface)
        else:
            j = g['judgment']
            msg = JUDGE_TEXT[j]
            box = pygame.Rect(0, 0, fit_width(msg, 'big', shadow=True) + 16, 26)
            box.midbottom = (cx if BAR.x + 40 < cx < BAR.right - 40 else T.WIDTH // 2, BAR.y - 12)
            box.clamp_ip(BAR_PANEL.inflate(0, 80))
            card(surface, box)
            text_in(surface, msg, card_inner(box), 'big', JUDGE_COLOR[j], shadow=T.WHITE, tag='kitchen')

    def _draw_pan(self, surface, r):
        t = self.game['elapsed']
        pan = pygame.Rect(272, 199, 96, 18)
        pygame.draw.line(surface, (120, 78, 48), (pan.right - 6, pan.y + 6), (pan.right + 34, pan.y - 2), 3)
        pygame.draw.ellipse(surface, T.INK, pan.inflate(2, 2))
        pygame.draw.ellipse(surface, (70, 70, 80), pan)
        pygame.draw.ellipse(surface, (96, 96, 108), pan.inflate(-8, -8))
        items = list(r['ingredients'])
        n = 2 if len(items) <= 3 else 1
        step = 26 if n == 2 else 16
        total = step * (len(items) - 1) + 16 * n
        x = pan.centerx - total // 2
        for i, item in enumerate(items):
            bob = 1 if (int(t * 4) + i) % 2 else 0          # 지글지글 1px
            img = self.icons.get(item, n)
            surface.blit(img, (x + i * step, pan.y + 6 - img.get_height() + bob))
        # 김 (흰 선 3줄, 위로 올라감)
        for i, sx in enumerate((300, 320, 340)):
            off = int((t * 10 + i * 5) % 14)
            for k in range(3):
                y = 168 - off + k * 6
                x = sx + (k + i) % 2
                pygame.draw.line(surface, (236, 232, 228), (x, y), (x, y + 3))

    def _draw_space_hint(self, surface):
        key, msg = 'SPACE', '지금 누르기!'
        kw = chip_width(key)
        w = 4 + 6 + kw + 6 + fit_width(msg, 'title', shadow=True) + 6
        box = pygame.Rect(0, 0, w, 24)
        box.midtop = (T.WIDTH // 2, BAR_PANEL.bottom + 6)
        card(surface, box)
        chip(surface, (box.x + 8, box.centery), key, 'gray', anchor='midleft')
        text_in(surface, msg, (box.x + 8 + kw + 4, box.y + 2, box.right - 2 - (box.x + 8 + kw + 4), box.h - 4),
                'title', T.TEXT, shadow=T.WHITE, tag='kitchen')

    # ----- 결과 -----
    def _draw_result(self, surface):
        res = self.result
        outcome = res.get('outcome', 'success')
        rib, rib_color, big, note = RESULT.get(outcome, RESULT['success'])
        panel(surface, RES)
        rw = max(100, fit_width(rib, 'title', shadow=True) + 16)
        ribbon(surface, (RES.centerx - rw // 2, RES.y - 8, rw, 18), rib, rib_color)
        # 그림 칸
        art = pygame.Rect(RES.centerx - 58, RES.y + 18, 116, 90)
        card(surface, art)
        item = res.get('item', '')
        if outcome == 'great':
            self._draw_rays(surface, art)
        img = self.icons.get(item, 4)
        surface.blit(img, img.get_rect(center=art.center))
        if F.is_perfect(item):
            F.star_badge(surface, (art.right - 14, art.y + 5))
        # 판정 글씨 · 요리 이름 · 효과 · 설명
        y = art.bottom + 4
        big_color = T.WARN if outcome in ('great', 'success') else T.shade('gray', 1)
        text(surface, big, (RES.centerx, y), 'big', big_color, 'midtop', shadow=T.WHITE)
        name = F.dish_name(item, self.catalog, self.recipes)
        text(surface, f'{name} ×1', (RES.centerx, y + 20), 'title', T.TEXT, 'midtop')
        draw_effects(surface, (RES.centerx, y + 37), res.get('effects', {}), center=True)
        text(surface, note, (RES.centerx, y + 54), 'body', T.WARN if outcome == 'great' else T.TEXT_SOFT, 'midtop')
        # 레벨 칸: 레벨 + 이번 경험치 + 게이지(이번에 오른 부분은 밝게)
        box = pygame.Rect(RES.x + 20, RES.y + 196, RES.w - 40, 40)
        card(surface, box)
        inner = card_inner(box)
        total, gained = res.get('total_xp', 0), res.get('xp', 0)
        lv, lo, hi = self.level_span(total)
        label = f'요리 Lv.{lv}'
        g = text_in(surface, label, (inner.x + 2, inner.y, fit_width(label, 'title'), 16), 'title', align='left',
                    tag='kitchen')
        if self.before and lv > self.before[0]:
            chip(surface, (g.right + 6, inner.y + 1), '레벨 업!', 'green')
        xp_label = f'경험치 +{gained}' if gained else '경험치 없음'
        xw = fit_width(xp_label, 'title')
        text_in(surface, xp_label, (inner.right - 2 - xw, inner.y, xw, 16), 'title',
                T.shade('purple', 1) if gained else T.TEXT_SOFT, align='right', tag='kitchen')
        bar = pygame.Rect(inner.x + 4, inner.y + 21, inner.w - 8, 10)
        if hi:
            gauge(surface, bar, total - lo, hi - lo, 'orange')
            ib = bar.inflate(-4, -4)
            start = max(lo, total - gained)
            x0 = ib.x + ib.w * (start - lo) // (hi - lo)
            x1 = ib.x + ib.w * (total - lo) // (hi - lo)
            fill_part(surface, ib, x0, x1, [T.shade('orange', 2), YELLOW, (255, 226, 120), (255, 246, 200)])
        else:
            gauge(surface, bar, 1, 1, 'orange')

    def _draw_rays(self, surface, art):
        """대성공: 그림 칸 안 노란 빛줄기 + 반짝이(+)."""
        inner = card_inner(art)
        clip = surface.get_clip()
        surface.set_clip(inner)
        c = art.center
        for k in range(12):
            a = k * math.pi / 6
            pygame.draw.line(surface, (255, 226, 140), c, (c[0] + math.cos(a) * 80, c[1] + math.sin(a) * 80))
        surface.set_clip(clip)
        for sx, sy in ((inner.x + 8, inner.y + 8), (inner.right - 12, inner.y + 10), (inner.x + 10, inner.bottom - 12),
                       (inner.right - 12, inner.bottom - 12)):
            pygame.draw.line(surface, (236, 184, 52), (sx - 2, sy), (sx + 2, sy))
            pygame.draw.line(surface, (236, 184, 52), (sx, sy - 2), (sx, sy + 2))


_kitchen = {}


def kitchen_image():
    """주방 배경 (assets/home/kitchen.png 1280×720 → 논리 640×360, 2배로 그려져 있어 픽셀이 그대로)."""
    if 'img' not in _kitchen:
        import os
        path = os.path.join(T.ROOT, 'assets', 'home', 'kitchen.png')
        _kitchen['img'] = pygame.transform.scale(pygame.image.load(path).convert(), (T.WIDTH, T.HEIGHT))
    return _kitchen['img']


def _dim():
    """결과 창 뒤를 어둡게."""
    if 'dim' not in _kitchen:
        s = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        s.fill((24, 16, 24, 110))
        _kitchen['dim'] = s
    return _kitchen['dim']
