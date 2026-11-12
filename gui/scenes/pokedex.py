"""도감 (D안): 펼친 가죽 책 + 책 옆 천 태그(일반 / 특급). 왼쪽 쪽 = 고른 등급 15마리, 오른쪽 쪽 = 고른 동물 정보.

목업 docs/mockups/dex/dex_D0_first.png ~ dex_D3_missing.png. 책·태그·칸·현황 쪽 모양은 tools/dex_mock_d.py
(book, tags, tags_front, left_page, summary_page)와 tools/dex_mock.py(cell, chips, evo_line, stat_rows)와 같게 코드 도트.
게임 규칙은 없다: 가진 동물·단계·능력치는 get_pokedex, 설명·종·유형·강점·단계별 이름·그림은 get_catalog,
지금 단계 MAX는 get_evolution_status(key)의 caps. 도감 번호 = get_pokedex 순서(characters.json 순서).
"""
import math
import os
import pygame

from .. import theme as T
from .. import widgets as W
from .. import items as I
from ..app import Scene
from ..widgets import (text, text_in, glyph_box, fit_width, card, card_inner, ribbon, chip, icon, gauge,
                       select_frame, record, wrap_lines, Button, BUTTON_H)

# ---- 책 모양 (tools/dex_mock_d.py와 같은 값) ----
LEATHER = [(70, 36, 30), (104, 54, 40), (134, 74, 52), (166, 100, 70)]     # 표지 가죽 어두움→밝음
GOLDC = [(120, 80, 20), (196, 146, 50), (240, 200, 90), (255, 236, 160)]
PAPER = [(214, 190, 150), (236, 216, 178), (250, 236, 206), (255, 246, 224)]   # tools/uikit.py PAPER
PAGE_L, PAGE_R, SPINE = (14, 300), (306, 598), 303
ORN = (214, 186, 140)
SIL = (54, 44, 60)
QMARK = (150, 136, 160)
TAGS = (('normal', '일반', 'egg_basic', (240, 230, 208)), ('special', '특급', 'egg_special', (255, 226, 150)))
GOLD_TEXT = (150, 96, 10)
ROLES = ('dealer', 'tank', 'healer')
CELL = (45, 74)
RX, RR = 312, 594                       # 오른쪽 쪽 글씨 왼쪽·오른쪽 끝
STAT_SHORT = {'hp': '체력', 'attack': '공격', 'defense': '방어', 'agility': '민첩'}
FRAME = pygame.Rect(322, 108, 265, 71)  # 현황 쪽 액자 그림 (안쪽)


def _r(x0, y0, x1, y1):
    """PIL식 양끝 포함 좌표 → pygame Rect."""
    return pygame.Rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def _paper(x, x0, x1):
    """종이 색: 가운데 접힌 곳일수록·바깥 가장자리일수록 살짝 어둡게."""
    r, g, b = PAPER[2]
    k = max(0, 24 - abs(x - SPINE)) ** 1.5 * 0.33 + (4 if x in (x0 + 1, x1 - 1) else 0)
    return (int(r - k), int(g - k * 1.1), int(b - k * 1.3))


def build_book():
    """펼친 책 한 장 (Surface 하나로 만들어 둠)."""
    s = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
    # ① 가죽 표지 + 금박 점선
    cover = _r(4, 54, 607, 358)
    pygame.draw.rect(s, LEATHER[1], cover)
    pygame.draw.rect(s, T.INK, cover, 1)
    pygame.draw.line(s, LEATHER[3], (5, 55), (606, 55))
    pygame.draw.line(s, LEATHER[0], (5, 357), (606, 357))
    for x in range(10, 602, 6):
        s.set_at((x, 57), GOLDC[1])
        s.set_at((x, 355), GOLDC[1])
    # ② 종이 묶음 두께 (쪽 아래·바깥에 겹친 종이 3장)
    for (x0, x1), side in ((PAGE_L, -1), (PAGE_R, 1)):
        for i in (3, 2, 1):
            ox = side * i
            c = (206 - i * 14, 186 - i * 14, 150 - i * 14)
            r = _r(x0 + (ox if side < 0 else 0), 62 + i, x1 + (ox if side > 0 else 0), 350 + i)
            pygame.draw.rect(s, c, r)
            pygame.draw.rect(s, T.WOOD[0], r, 1)
    # ③ 펼친 두 쪽: 가운데로 갈수록 위아래가 말려 들어감 + 접힌 그림자
    for x0, x1 in (PAGE_L, PAGE_R):
        for x in range(x0, x1 + 1):
            dip = max(0, (24 - abs(x - SPINE)) // 5)
            top, bot = 62 + dip, 350 - dip
            if x in (x0, x1):
                pygame.draw.line(s, T.WOOD[0], (x, top), (x, bot))
                continue
            pygame.draw.line(s, _paper(x, x0, x1), (x, top), (x, bot))
            s.set_at((x, top), T.WOOD[0])
            s.set_at((x, bot), T.WOOD[0])
            s.set_at((x, top + 1), PAPER[3])
    pygame.draw.line(s, (150, 112, 76), (SPINE - 1, 62), (SPINE - 1, 350))
    pygame.draw.line(s, T.INK, (SPINE, 60), (SPINE, 352))
    pygame.draw.line(s, (150, 112, 76), (SPINE + 1, 62), (SPINE + 1, 350))
    # ④ 왼쪽 쪽 아래 귀퉁이 접힘
    fx, fy, n = PAGE_L[0], 350, 14
    pygame.draw.polygon(s, (192, 172, 136), [(fx - 1, fy - n), (fx - 1, fy + 1), (fx + n, fy + 1)])
    fold = [(fx, fy - n), (fx + n, fy), (fx + n, fy - n)]
    pygame.draw.polygon(s, (232, 212, 172), fold)
    pygame.draw.polygon(s, T.WOOD[0], fold, 1)
    pygame.draw.line(s, (250, 236, 206), (fx + 2, fy - n + 1), (fx + n - 1, fy - n + 1))
    # ⑤ 표지 네 귀퉁이 금속 모서리
    for cx, cy, sx, sy in ((4, 54, 1, 1), (607, 54, -1, 1), (4, 358, 1, -1), (607, 358, -1, -1)):
        pts = [(cx, cy), (cx + sx * 13, cy), (cx, cy + sy * 13)]
        pygame.draw.polygon(s, GOLDC[1], pts)
        pygame.draw.polygon(s, T.INK, pts, 1)
        pygame.draw.line(s, GOLDC[3], (cx + sx * 2, cy + sy * 2), (cx + sx * 8, cy + sy * 2))
        s.set_at((cx + sx * 4, cy + sy * 4), GOLDC[0])
    # ⑥ 책갈피 끈 (접힌 곳에서 아래로, 끝은 V자)
    rx = SPINE - 6
    pygame.draw.rect(s, (196, 52, 60), _r(rx, 60, rx + 4, 356))
    pygame.draw.rect(s, T.INK, _r(rx, 60, rx + 4, 356), 1)
    pygame.draw.line(s, (236, 96, 100), (rx + 1, 61), (rx + 1, 355))
    pygame.draw.polygon(s, (196, 52, 60), [(rx, 356), (rx + 4, 356), (rx + 4, 360), (rx + 2, 358), (rx, 360)])
    return s


def star_icon():
    """별 16px (현황 카드 '최종 진화')."""
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    pts = [(0, -6), (2, -2), (6, -2), (3, 1), (4, 6), (0, 3), (-4, 6), (-3, 1), (-6, -2), (-2, -2)]
    pts = [(8 + x, 8 + y) for x, y in pts]
    pygame.draw.polygon(s, (255, 210, 60), pts)
    pygame.draw.polygon(s, T.INK, pts, 1)
    return s


class PokedexScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.rarity = 'normal'
        self.selected = None            # 고른 동물 (None = 현황 쪽)
        self.dex = []
        self.catalog = {}
        self.evo = {}                   # get_evolution_status 캐시 (가진 동물)
        self.icons = I.ItemIcons()
        self._img = {}
        self._book = None
        self._frame = None
        self._frame_key = None
        self.buttons = []
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.dex = self.app.call('get_pokedex') or self.dex
        self.catalog = self.app.call('get_catalog') or self.catalog
        self.evo = {}
        self.selected = None
        if self._book is None:
            self._book = build_book()

    # ---------- 백엔드 값 ----------
    def number(self, key):
        return next((i + 1 for i, d in enumerate(self.dex) if d['id'] == key), 0)

    def entry(self, key):
        return next((d for d in self.dex if d['id'] == key), None)

    def owned(self, rarity=None):
        return [d for d in self.dex if d.get('owned') and (rarity is None or d['rarity'] == rarity)]

    def info(self, key):
        return self.catalog.get(key) or {}

    def max_stage(self, key):
        return self.info(key).get('max_stage', 1)

    def evolution(self, key):
        if key not in self.evo:
            self.evo[key] = self.app.call('get_evolution_status', key=key) or {}
        return self.evo[key]

    def stage_sprite(self, key, stage):
        sprites = self.info(key).get('stage_sprites') or []
        return sprites[min(len(sprites), max(1, stage)) - 1] if sprites else (self.entry(key) or {}).get('sprite')

    # ---------- 그림 ----------
    def crop(self, path, n):
        """도트 그림의 투명 여백을 잘라 × n (정수배)."""
        key = ('crop', path, n)
        if key not in self._img:
            base = self.app.sprites.get(path, 28)
            sub = base.subsurface(base.get_bounding_rect()).copy()
            self._img[key] = pygame.transform.scale(sub, (sub.get_width() * n, sub.get_height() * n))
        return self._img[key]

    def silhouette(self, path, n, color=SIL):
        key = ('sil', path, n, color)
        if key not in self._img:
            img = self.crop(path, n).copy()
            img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
            img.fill((*color, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self._img[key] = img
        return self._img[key]

    def menu_icon(self, name):
        key = ('menu', name)
        if key not in self._img:
            img = pygame.image.load(os.path.join(T.ROOT, 'assets', 'ui', f'icon_{name}.png')).convert_alpha()
            img = img.subsurface(img.get_bounding_rect()).copy()
            f = max(1, -(-max(img.get_size()) // 16))
            self._img[key] = pygame.transform.scale(img, (img.get_width() // f, img.get_height() // f))
        return self._img[key]

    @staticmethod
    def blit_in(surface, img, box, center):
        """칸 안에만 그림 (3단계 반짝이가 칸 밖으로 나가지 않게)."""
        old = surface.get_clip()
        surface.set_clip(box.clip(old) if old else box)
        surface.blit(img, img.get_rect(center=center))
        surface.set_clip(old)

    def _qmark(self, surface, center, kind='big'):
        text(surface, '?', center, kind, QMARK, 'center', shadow=T.INK)

    # ---------- 칸 위치 ----------
    @staticmethod
    def tag_rect(i, on):
        y = 86 + i * 62
        return _r(600, y, 639 if on else 635, y + 56)

    @staticmethod
    def cell_rect(row, col):
        return pygame.Rect(56 + col * 48, 94 + row * 80 + 0, *CELL)

    def page_keys(self, role):
        return [d['id'] for d in self.dex if d['role'] == role and d['rarity'] == self.rarity]

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, (rar, *_rest) in enumerate(TAGS):
                if self.tag_rect(i, rar == self.rarity).collidepoint(event.pos):
                    if rar != self.rarity:
                        self.rarity = rar
                        self.selected = None          # 태그를 바꾸면 현황 쪽으로
                    return
            for row, role in enumerate(ROLES):
                for col, key in enumerate(self.page_keys(role)):
                    if self.cell_rect(row, col).collidepoint(event.pos):
                        self.selected = None if key == self.selected else key   # 같은 칸 다시 = 현황 쪽
                        return

    def update(self, dt):
        self.buttons = []
        key = self.selected
        if not key:
            return
        r = pygame.Rect(RX, 326, RR - RX, 20)
        e = self.entry(key) or {}
        if e.get('owned'):
            self.buttons.append(Button(r, '내 동물에서 보기', lambda: self.app.go('animals', selected=key), 'green',
                                       icon='heart'))
        else:
            self.buttons.append(Button(r, '상점에서 알 사기', lambda: self.app.go('shop', tab='egg'), 'orange',
                                       icon='coin'))

    # ---------- 그리기 ----------
    def draw(self, surface):
        self.app.backdrop(surface)
        self.back.draw(surface)
        ribbon(surface, (78, 33, 70, 18), '도감', 'red')
        self._draw_progress(surface)
        tags = self._tags_surface()
        surface.blit(tags, (0, 0))                                  # 태그 (표지 뒤)
        surface.blit(self._book, (0, 0))
        surface.blit(tags, (608, 80), pygame.Rect(608, 80, 32, 140))  # 표지 밖으로 나온 부분만 앞에
        self._draw_left(surface)
        if self.selected and self.entry(self.selected):
            if self.entry(self.selected).get('owned'):
                self._draw_owned(surface, self.selected)
            else:
                self._draw_missing(surface, self.selected)
        else:
            self._draw_summary(surface)
        for b in self.buttons:
            b.draw(surface)

    def _draw_progress(self, surface):
        n = len(self.owned())
        box = pygame.Rect(454, 31, 150, 22)
        card(surface, box)
        inner = card_inner(box)
        label = f"등록 {n} / {len(self.dex)}"
        lw = fit_width(label, 'small')
        text_in(surface, label, (inner.x + 2, inner.y, lw, inner.h), 'small', tag='dex')
        gauge(surface, (inner.x + lw + 6, inner.y + 4, inner.right - inner.x - lw - 8, 10), n, len(self.dex) or 1,
              'green')

    def _tags_surface(self):
        s = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        for i, (rar, label, egg, tint) in enumerate(TAGS):
            on = rar == self.rarity
            r = self.tag_rect(i, on)
            col = tint if on else tuple(int(v * .82) for v in tint)
            pygame.draw.rect(s, col, r)
            pygame.draw.rect(s, T.INK, r, 1)
            pygame.draw.line(s, T.WHITE if on else tint, (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
            for yy in range(r.y + 4, r.y + 54, 4):                 # 바느질 점선
                s.set_at((r.right - 4, yy), T.WOOD[2])
            cx = (607 + r.right - 1) // 2 + 1
            s.blit(self.icons.get(egg, 1), (cx - 8, r.y + 4))
            vis = pygame.Rect(608, r.y, r.right - 608, r.h)          # 표지 밖으로 보이는 부분
            text_in(s, label, (vis.x, r.y + 22, vis.w, 16), 'title', GOLD_TEXT if rar == 'special' else T.TEXT,
                    tag='dex')
            n = len(self.owned(rar))
            total = sum(1 for d in self.dex if d['rarity'] == rar)
            text_in(s, f"{n}/{total}", (vis.x, r.y + 39, vis.w, 14), 'small', T.TEXT_SOFT, tag='dex')
        return s

    # ----- 왼쪽 쪽 -----
    def _draw_left(self, surface):
        rar = self.rarity
        title = '특급' if rar == 'special' else '일반'
        g = text(surface, title, (24, 77), 'title', (176, 110, 20) if rar == 'special' else T.TEXT, 'midleft')
        ms = max((self.max_stage(d['id']) for d in self.dex if d['rarity'] == rar), default=1)
        text(surface, f"{ms}단계까지", (g.right + 4, 78), 'small', T.TEXT_SOFT, 'midleft')
        total = sum(1 for d in self.dex if d['rarity'] == rar)
        text(surface, f"{len(self.owned(rar))} / {total}", (290, 78), 'small', T.TEXT, 'midright')
        pygame.draw.line(surface, ORN, (22, 88), (292, 88))
        pygame.draw.polygon(surface, ORN, [(157, 85), (160, 88), (157, 91), (154, 88)])
        for row, role in enumerate(ROLES):
            keys = self.page_keys(role)
            if not keys:
                continue
            y = 94 + row * 80
            el = self.entry(keys[0])['element']
            chip(surface, (20, y + 14), T.ROLE_LABEL[role], T.ROLE_KIT[role])
            chip(surface, (20, y + 34), T.ELEMENT_LABEL[el], T.ELEMENT_KIT[el])
            own = sum(1 for k in keys if self.entry(k).get('owned'))
            text(surface, f"{own}/{len(keys)}", (22, y + 60), 'small', T.TEXT_SOFT, 'midleft')
            for col, key in enumerate(keys):
                self._draw_cell(surface, self.cell_rect(row, col), key)
        text(surface, '동물을 눌러 확인하자!', (157, 339), 'small', T.TEXT_SOFT, 'center')

    def _draw_cell(self, surface, r, key):
        e = self.entry(key)
        own = e.get('owned')
        band = pygame.Rect(r.x + 1, r.bottom - 14, r.w - 2, 13)
        if own:
            pygame.draw.rect(surface, (255, 246, 224), r)
            pygame.draw.line(surface, T.WHITE, (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
            pygame.draw.rect(surface, (236, 216, 178), band)
        else:
            pygame.draw.rect(surface, (150, 128, 104), r)
            pygame.draw.rect(surface, (132, 110, 88), band)
        pygame.draw.rect(surface, T.INK, r, 1)
        if e['rarity'] == 'special':
            pygame.draw.rect(surface, (240, 188, 60), r.inflate(-2, -2), 1)
        center = (r.centerx, r.y + (r.h - 14) // 2 + 1)
        if own:
            self.blit_in(surface, self.crop(e['sprite'], 2), r.inflate(-2, -2), center)
        else:
            img = self.silhouette(self.stage_sprite(key, 1), 2)
            surface.blit(img, img.get_rect(center=center))
            self._qmark(surface, center)
        text(surface, f"{self.number(key):02d}", (r.x + 4, r.bottom - 8), 'small', T.TEXT if own else (226, 210, 190),
             'midleft')
        mx = self.max_stage(key)
        cur = e.get('stage') if own else 0
        x0 = r.right - 5 - mx * 6 + 1
        for i in range(mx):
            on = bool(cur) and i < cur
            d = pygame.Rect(x0 + i * 6, r.bottom - 10, 5, 5)
            pygame.draw.rect(surface, (255, 206, 60) if on else (110, 88, 74), d)
            pygame.draw.rect(surface, T.INK, d, 1)
            if on:
                surface.set_at((d.x + 1, d.y + 1), (255, 246, 200))
        if key == self.selected:
            select_frame(surface, r.inflate(4, 4))

    # ----- 오른쪽 쪽 공통 -----
    def _line(self, surface, msg, pos, kind, color, anchor='midleft'):
        """오른쪽 쪽 글씨 한 줄 + 넘침 점검 기록 (RX~RR을 넘으면 check_text_fit 위반)."""
        g = text(surface, msg, pos, kind, color, anchor)
        record(msg, g, pygame.Rect(RX - 4, g.y - 2, RR - RX + 6, g.h + 4), 'dex-page')
        return g

    def _chips(self, surface, x, y, key, strength=True):
        e, info = self.entry(key), self.info(key)
        rows = [('특급', 'gold') if e['rarity'] == 'special' else ('일반', 'gray'),
                (T.ROLE_LABEL[e['role']], T.ROLE_KIT[e['role']]),
                (T.ELEMENT_LABEL[e['element']], T.ELEMENT_KIT[e['element']])]
        if strength:
            s = (info.get('strength') or '').strip()
            rows.append((f"강점 {'균형' if s in ('', '기준') else s}", 'brown'))
        for label, color in rows:
            r = chip(surface, (x, y), label, color)
            record(label, r, pygame.Rect(RX - 4, r.y - 2, RR - RX + 6, r.h + 4), 'dex-page')
            x = r.right + 3

    def _evo_line(self, surface, key, cur):
        """진화 줄: 지나온 단계는 그림 + 이름, 지금 단계 꺾쇠, 못 간 단계는 실루엣 + ? + '???'. 사이 ▶."""
        info = self.info(key)
        mx = info.get('max_stage', 1)
        names = info.get('stage_names') or []
        step = 84 if mx == 3 else 100
        x, y = RX + 34, 208
        for i in range(mx):
            st = i + 1
            cx = x + i * step + 28
            box = _r(cx - 30, y, cx + 29, y + 58)
            pygame.draw.rect(surface, (255, 248, 230) if st <= cur else (196, 176, 150), box)
            pygame.draw.rect(surface, T.WOOD[2], box, 1)
            if st == cur:
                select_frame(surface, box.inflate(4, 4))
            path = self.stage_sprite(key, st)
            if st <= cur:
                self.blit_in(surface, self.crop(path, 2), box.inflate(-2, -2), box.center)
            else:
                self.blit_in(surface, self.silhouette(path, 2, (90, 76, 92)), box.inflate(-2, -2), box.center)
                self._qmark(surface, box.center, 'title')
            name = names[i] if st <= cur and i < len(names) else '???'
            self._line(surface, name, (box.centerx, box.bottom + 9), 'small', T.TEXT if st <= cur else T.TEXT_SOFT,
                       'center')
            if i < mx - 1:
                ax = box.right + (step - box.w) // 2
                text(surface, '▶', (ax + 1, box.centery), 'small', T.WOOD[2], 'center')

    def _stat_rows(self, surface, key, known):
        e = self.entry(key)
        stats = e.get('stats') or {}
        caps = self.evolution(key).get('caps', {}) if known else {}
        colw, gap = 144, 16
        for i, st in enumerate(T.STATS):
            cx, cy = RX + (i % 2) * colw, 290 + (i // 2) * gap
            text(surface, STAT_SHORT[st], (cx, cy + 5), 'small', T.TEXT_SOFT, 'midleft')
            bar = (cx + 24, cy, colw - 80, 10)
            right = (cx + colw - 6, cy + 5)
            if known:
                v, mx = stats.get(st, 0), caps.get(st, 0)
                gauge(surface, bar, v, mx or 1, T.ROLE_KIT[e['role']])
                self._line(surface, f"{v}/{mx}", right, 'small', T.TEXT, 'midright')
            else:
                gauge(surface, bar, 0, 1, 'gray')
                self._line(surface, '???', right, 'small', T.TEXT_SOFT, 'midright')

    # ----- 가진 동물 (D1·D2) -----
    def _draw_owned(self, surface, key):
        e, info = self.entry(key), self.info(key)
        stage = e.get('stage') or 1
        self._line(surface, f"No.{self.number(key):02d}", (RX, 74), 'small', T.TEXT_SOFT)
        self._line(surface, e['name'], (RX + 34, 76), 'big', T.TEXT)
        chip(surface, (RR - 24, 68), f"{stage}단계", 'brown', anchor='topright')
        self._chips(surface, RX, 90, key)
        art = _r(RX, 112, RX + 90, 200)
        pygame.draw.rect(surface, (255, 250, 236), art)
        pygame.draw.rect(surface, T.WOOD[2], art, 1)
        pygame.draw.ellipse(surface, (236, 216, 178), _r(RX + 17, 178, RX + 73, 190))
        self.blit_in(surface, self.crop(e['sprite'], 3), art.inflate(-2, -2), (RX + 45, 152))
        for i, line in enumerate(wrap_lines(info.get('description', ''), RR - (RX + 100) - 2, 'small')[:4]):
            self._line(surface, line, (RX + 100, 120 + i * 14), 'small', T.TEXT)
        self._line(surface, f"{info.get('species', '')} · {info.get('type', '')}", (RX + 100, 190), 'small',
                   T.TEXT_SOFT)
        text(surface, '진화', (RX, 214), 'title', T.TEXT, 'midleft')
        self._evo_line(surface, key, stage)
        self._stat_rows(surface, key, True)

    # ----- 없는 동물 (D3) -----
    def _draw_missing(self, surface, key):
        e = self.entry(key)
        self._line(surface, f"No.{self.number(key):02d}", (RX, 74), 'small', T.TEXT_SOFT)
        self._line(surface, '???', (RX + 34, 76), 'big', T.TEXT_SOFT)
        self._chips(surface, RX, 90, key, strength=False)
        art = _r(RX, 112, RX + 90, 200)
        pygame.draw.rect(surface, (196, 176, 150), art)
        pygame.draw.rect(surface, T.WOOD[2], art, 1)
        img = self.silhouette(self.stage_sprite(key, 1), 3)
        surface.blit(img, img.get_rect(center=(RX + 45, 152)))
        self._qmark(surface, (RX + 45, 152))
        self._line(surface, '아직 만나지 못한 동물', (RX + 100, 122), 'title', T.TEXT)
        self._line(surface, '부화하면 그림·이름·설명이', (RX + 100, 140), 'small', T.TEXT_SOFT)
        self._line(surface, '도감에 등록된다', (RX + 100, 154), 'small', T.TEXT_SOFT)
        box = _r(RX + 100, 168, RR, 198)
        pygame.draw.rect(surface, (255, 246, 224), box)
        pygame.draw.rect(surface, T.WOOD[2], box, 1)
        special = e['rarity'] == 'special'
        surface.blit(self.icons.get('egg_special' if special else 'egg_basic', 1), (RX + 106, 175))
        self._line(surface, '만나는 곳: 상점 알 부화', (RX + 126, 178), 'small', T.TEXT)
        if special:
            egg = 'egg_special'
            where = f"{self.icons_label(egg)} 특급 {I.EGG_SPECIAL_RATE.get(egg, 0)}%"
        else:
            where = f"{self.icons_label('egg_basic')} · {self.icons_label('egg_special')}"
        self._line(surface, where, (RX + 126, 191), 'small', T.TEXT_SOFT)
        text(surface, '진화', (RX, 214), 'title', T.TEXT, 'midleft')
        self._evo_line(surface, key, 0)
        self._stat_rows(surface, key, False)

    def icons_label(self, item):
        if not hasattr(self, '_shop'):
            self._shop = self.app.call('get_shop_catalog') or {}
        return I.item_label(item, self._shop)

    # ----- 아무도 안 고름 (D0, 현황 쪽) -----
    def _draw_summary(self, surface):
        x0, x1 = RX, RR
        cx = (x0 + x1) // 2 + 2
        self._line(surface, 'EvoTail 동물 도감', (cx, 80), 'big', T.TEXT, 'center')
        for sx in (-1, 1):
            ex = cx + sx * 74
            pygame.draw.line(surface, (196, 160, 110), (ex, 80), (ex + sx * 40, 80))
            pygame.draw.line(surface, ORN, (ex, 82), (ex + sx * 30, 82))
            dia = [(ex + sx * 44, 77), (ex + sx * 47, 80), (ex + sx * 44, 83), (ex + sx * 41, 80)]
            pygame.draw.polygon(surface, GOLDC[1], dia)
            pygame.draw.polygon(surface, T.INK, dia, 1)
        self._line(surface, '섬 마을에서 만난 동물 기록', (cx, 96), 'small', T.TEXT_SOFT, 'center')
        # 액자 그림 (가진 동물이 바뀔 때만 다시 그림)
        outer = FRAME.inflate(8, 8)
        pygame.draw.rect(surface, T.WOOD[1], outer)
        pygame.draw.rect(surface, T.INK, outer, 1)
        pygame.draw.rect(surface, T.WOOD[3], FRAME.inflate(4, 4), 1)
        surface.blit(self._scene_frame(), FRAME)
        # 현황 카드 4개
        owned = self.owned()
        nn = len(self.owned('normal'))
        ns = len(self.owned('special'))
        done = sum(1 for d in owned if d.get('stage') == self.max_stage(d['id']))
        tn = sum(1 for d in self.dex if d['rarity'] == 'normal')
        tsp = sum(1 for d in self.dex if d['rarity'] == 'special')
        cards = [(self.menu_icon('pokedex'), f"{len(owned)}", f"전체 / {len(self.dex)}", T.TEXT),
                 (self.icons.get('egg_basic', 1), f"{nn}", f"일반 / {tn}", T.TEXT),
                 (self.icons.get('egg_special', 1), f"{ns}", f"특급 / {tsp}", (176, 110, 20)),
                 (self._star(), f"{done}", '최종 진화', (120, 80, 170))]
        cw = 66
        for i, (ic, big, label, color) in enumerate(cards):
            r = pygame.Rect(x0 + 8 + i * (cw + 4), 192, cw, 46)
            card(surface, r)
            surface.blit(ic, (r.x + 6, r.y + 7))
            text(surface, big, (r.x + 26, r.y + 15), 'big', color, 'midleft')
            text_in(surface, label, (r.x + 2, r.y + 28, r.w - 4, 14), 'small', T.TEXT_SOFT, tag='dex')
        # 속성별 (가진 수 / 그 역할 전체)
        text(surface, '속성별', (x0 + 10, 252), 'title', T.TEXT, 'midleft')
        for row, role in enumerate(ROLES):
            y = 262 + row * 13
            keys = [d for d in self.dex if d['role'] == role]
            el = keys[0]['element'] if keys else 'fire'
            own = sum(1 for d in keys if d.get('owned'))
            self._line(surface, f"{T.ROLE_LABEL[role]} · {T.ELEMENT_LABEL[el]}", (x0 + 12, y + 5), 'small', T.TEXT)
            gauge(surface, (x0 + 76, y, 150, 10), own, len(keys) or 1, T.ELEMENT_KIT[el])
            self._line(surface, f"{own} / {len(keys)}", (x1 - 12, y + 5), 'small', T.TEXT, 'midright')
        guide = _r(x0 + 8, 310, x1 - 8, 340)
        pygame.draw.rect(surface, (255, 246, 224), guide)
        pygame.draw.rect(surface, T.WOOD[2], guide, 1)
        surface.blit(self.icons.get('egg_basic', 1), (x0 + 16, 317))
        self._line(surface, '왼쪽 동물을 눌러 확인하자!', (x0 + 38, 319), 'small', T.TEXT)
        self._line(surface, '옆 태그로 일반 · 특급 넘기기', (x0 + 38, 332), 'small', T.TEXT_SOFT)

    def _star(self):
        if 'star' not in self._img:
            self._img['star'] = star_icon()
        return self._img['star']

    def _scene_frame(self):
        """액자 속 그림: 하늘·구름·언덕·풀밭 위에 가진 동물 앞에서 5마리 (×2). 가진 동물이 바뀔 때만 다시 그림."""
        faces = [(d['id'], d['sprite']) for d in self.dex if d.get('owned')][:5]
        if self._frame is not None and self._frame_key == faces:
            return self._frame
        w, h = FRAME.size
        pic = pygame.Surface((w, h), pygame.SRCALPHA)
        sky = [(150, 206, 240), (170, 218, 244), (190, 228, 246), (208, 236, 248)]
        for y in range(h):
            pygame.draw.line(pic, sky[min(3, y * 4 // max(1, h * 2 // 3))], (0, y), (w, y))
        for cx, cy, cw in ((40, 12, 22), (w - 60, 9, 28), (150, 18, 16)):                 # 구름
            pygame.draw.rect(pic, T.WHITE, _r(cx - cw // 2, cy, cx + cw // 2, cy + 4))
            pygame.draw.rect(pic, T.WHITE, _r(cx - cw // 4, cy - 3, cx + cw // 4, cy))
        pygame.draw.ellipse(pic, (140, 198, 116), _r(-40, h - 46, 150, h + 30))            # 언덕
        pygame.draw.ellipse(pic, (126, 188, 104), _r(110, h - 40, w + 40, h + 30))
        pygame.draw.rect(pic, (118, 186, 92), _r(0, h - 20, w, h))
        pygame.draw.line(pic, (150, 210, 110), (0, h - 20), (w, h - 20))
        for gx in range(3, w - 2, 9):
            pygame.draw.line(pic, (90, 150, 70), (gx, h - 22), (gx + 1, h - 20))
        for fx in range(14, w, 37):
            pic.set_at((fx, h - 8), (255, 240, 120))
            if fx + 17 < w:
                pic.set_at((fx + 17, h - 4), (255, 170, 190))
        if faces:
            step = w // (len(faces) + 1)
            for i, (key, path) in enumerate(faces):
                im = self.crop(path, 2)
                cx = step * (i + 1)
                pygame.draw.ellipse(pic, (90, 150, 70), _r(cx - 18, h - 12, cx + 18, h - 6))
                pic.blit(im, (cx - im.get_width() // 2, h - 9 - im.get_height()))
        self._frame, self._frame_key = pic, faces
        return pic
