"""밭 (A안): 텃밭 6칸(3열 × 2줄) + 오른쪽 칸(씨앗 고르기 / 자라는 중 / 수확 / 밭 넓히기). 다 자란 밭이 있으면 "모두 수확".

목업 docs/mockups/farm/farm_A_field.png, farm_A2_ready.png, farm_A3_all_ripe.png. 배경 assets/farm/farm.png.
게임 규칙은 없다: 밭 상태는 스냅샷 plots(crop, ready, end, remaining_seconds), 밭 가격은 get_rules()['plot_costs'],
씨앗 이름·값은 get_shop_catalog. 심기·수확·넓히기는 plant_crop / harvest_crop / expand_plot.
작물 자라는 시간(600초)과 수확 개수(3개)는 백엔드 API에 나오지 않아 GUI 표시값(FARM_DISPLAY)으로 둔다 (CLAUDE.md).
"""
import json
import math
import os
import time
import pygame

from .. import theme as T
from .. import widgets as W
from .. import items as I
from ..app import Scene
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, icon, gauge,
                       select_frame, record, Button, BUTTON_H)
from .settings import ConfirmOverlay

# 백엔드 config의 CROP_DURATION·CROP_YIELD와 같은 값 (API에 없어 GUI 표시값. 백엔드 값을 바꾸면 같이 바꿀 것)
FARM_DISPLAY = {'duration': 600, 'yield': 3}
GRID = (14, 124, 132, 108, 12)          # 시작 x, y, 칸 폭, 칸 높이, 사이
PANEL = pygame.Rect(444, 58, 188, 298)
ART = pygame.Rect(PANEL.x + 12, 110, PANEL.w - 24, 86)
PLANT_DIR = os.path.join(T.ROOT, 'assets', 'farm', 'plants')
with open(os.path.join(PLANT_DIR, 'plants.json'), encoding='utf-8') as _f:
    STAGES = {k: v for k, v in json.load(_f)['stages_by_progress'].items() if isinstance(v, list)}
SOIL = (132, 84, 50)
POP_SECONDS = 0.6
SPARK = (255, 240, 140)


def mmss(sec):
    sec = max(0, int(math.ceil(sec)))
    return f"{sec // 60}:{sec % 60:02d}"


class Plants:
    """작물 그림 (원본 24×24, 파일 4배 96) → 원본 × n."""

    def __init__(self):
        self._c = {}

    def get(self, name, n=2, alpha=255):
        key = (name, n, alpha)
        if key not in self._c:
            img = pygame.image.load(os.path.join(PLANT_DIR, f'{name}.png')).convert_alpha()
            w, h = img.get_size()
            img = pygame.transform.scale(img, (w // 4 * n, h // 4 * n))
            if alpha < 255:
                img = img.copy()
                img.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
            self._c[key] = img
        return self._c[key]


_tiles = {}


def soil_tile(w, h):
    """나무 틀 텃밭 + 포슬포슬한 흙 (점 무늬). tools/farm_mock.py soil()과 같은 그림."""
    if (w, h) not in _tiles:
        s = pygame.Surface((w, h))
        s.fill(T.WOOD[2])
        pygame.draw.rect(s, T.INK, (0, 0, w, h), 1)
        pygame.draw.line(s, T.WOOD[4], (1, 1), (w - 2, 1))
        pygame.draw.line(s, T.WOOD[1], (1, h - 2), (w - 2, h - 2))
        for xx in range(24, w - 4, 32):
            s.set_at((xx, 2), T.WOOD[1])
            s.set_at((xx, h - 3), T.WOOD[1])
        pygame.draw.rect(s, SOIL, (4, 4, w - 8, h - 8))
        pygame.draw.rect(s, (84, 50, 28), (4, 4, w - 8, h - 8), 1)
        pygame.draw.line(s, (92, 56, 32), (5, 5), (w - 6, 5))
        for j, yy in enumerate(range(8, h - 6, 3)):
            for i in range((j * 7) % 11, w - 10, 11):
                xx = 6 + i
                if xx < w - 6:
                    s.set_at((xx, yy), (168, 112, 70))
                    s.set_at((xx + 1, yy + 1), (104, 64, 38))
        _tiles[(w, h)] = s
    return _tiles[(w, h)]


def grass_tile(w, h, bright):
    key = ('grass', w, h, bright)
    if key not in _tiles:
        s = pygame.Surface((w, h))
        s.fill((112, 176, 84) if bright else (98, 150, 76))
        pygame.draw.rect(s, (70, 120, 56), (0, 0, w, h), 1)
        for i in range(0, w, 8):
            s.set_at((i + 3, 6 + (i * 5) % (h - 12)), (150, 210, 110))
        _tiles[key] = s
    return _tiles[key]


def draw_sign(surface, rect, lines, bright):
    """팻말: 기둥 + 나무 판. lines = [(글씨, 글꼴, 색)] 또는 코인 가격 ('coin', 가격)."""
    cx = rect.centerx
    pygame.draw.rect(surface, T.WOOD[1], (cx - 1, rect.centery, 3, rect.bottom - 10 - rect.centery))
    pygame.draw.rect(surface, T.INK, (cx - 2, rect.centery, 5, rect.bottom - 10 - rect.centery), 1)
    sign = pygame.Rect(0, 0, 80, 32)
    sign.midbottom = (cx, rect.centery + 6)
    pygame.draw.rect(surface, T.WOOD[3] if bright else T.WOOD[2], sign)
    pygame.draw.rect(surface, T.INK, sign, 1)
    pygame.draw.line(surface, T.WOOD[4], (sign.x + 1, sign.y + 1), (sign.right - 2, sign.y + 1))
    inner = sign.inflate(-2, -2)
    if len(lines) == 1:
        msg, kind, color = lines[0]
        text_in(surface, msg, inner, kind, color, shadow=T.WOOD[0], tag='farm')
        return sign
    msg, kind, color = lines[0]
    text_in(surface, msg, (inner.x, inner.y, inner.w, 14), kind, color, shadow=T.WOOD[0], tag='farm')
    price = f"{lines[1][1]:,}"
    w = 14 + glyph_box(price, 'title').w + 1
    x = inner.centerx - w // 2
    box = pygame.Rect(inner.x, inner.y + 13, inner.w, inner.h - 13)
    icon(surface, 'coin', (x, box.y + (box.h - 12) // 2))
    g = text_in(surface, price, (x + 14, box.y, w - 14, box.h), 'title', (255, 236, 150), shadow=T.WOOD[0], log=False)
    record(price, pygame.Rect(x, g.y, w, g.h), box, 'farm')
    return sign


class FarmScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.selected = 0
        self.seed = None             # 고른 작물 (씨앗 = seed_<작물>)
        self.catalog = {}
        self.plot_costs = []
        self.plants = Plants()
        self.icons = I.ItemIcons()
        self.pops = []               # (칸 번호, 작물, 시작 시각) 수확 연출
        self.buttons = []
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.catalog = self.app.call('get_shop_catalog') or self.catalog
        self.plot_costs = (self.app.call('get_rules') or {}).get('plot_costs', self.plot_costs)
        self.pops = []
        crops = self.crops()
        if self.seed not in crops:
            self.seed = next((c for c in crops if self.seeds(c) > 0), crops[0] if crops else None)

    # ---------- 백엔드 값 ----------
    def plots(self):
        return self.app.state.get('plots', [])

    def crops(self):
        """씨앗을 파는 작물 (상점 목록 순서)."""
        return [v['crop'] for k, v in self.catalog.items() if v.get('kind') == 'seed' and v.get('crop')]

    def label(self, crop):
        return I.item_label(crop, self.catalog)

    def seeds(self, crop):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(f'seed_{crop}', 0)

    def have(self, item):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(item, 0)

    def remaining(self, plot):
        if not plot.get('crop') or plot.get('ready'):
            return 0
        if plot.get('end') is not None:
            return max(0.0, plot['end'] - self.app.now())
        return plot.get('remaining_seconds', 0)

    def stage(self, plot):
        if plot.get('ready'):
            return f"{plot['crop']}_ripe"
        p = 1 - self.remaining(plot) / FARM_DISPLAY['duration']
        for name, (lo, hi) in STAGES.items():
            if lo <= p < hi:
                return name
        return 'growing'

    def cell_kind(self, i):
        """'plot' / 'next'(바로 다음에 넓힐 칸) / 'locked'."""
        n = len(self.plots())
        if i < n:
            return 'plot'
        return 'next' if i == n and i < len(self.plot_costs) else 'locked'

    @staticmethod
    def cell_rect(i):
        x0, y0, w, h, gap = GRID
        return pygame.Rect(x0 + (i % 3) * (w + gap), y0 + (i // 3) * (h + gap), w, h)

    # ---------- 명령 ----------
    def plant(self):
        i, crop = self.selected, self.seed
        self.app.act('plant_crop', f"{T.josa(self.label(crop), '을')} 심었다", icon='snack', index=i, crop=crop)

    def harvest(self, i=None):
        i = self.selected if i is None else i
        res = self.app.act('harvest_crop', lambda d: f"{self.label(d['crop'])} +{d['count']}", icon='heart', index=i)
        if res:
            self.pops.append((i, res['crop'], time.time()))

    def harvest_all(self):
        got = {}
        for p in list(self.plots()):
            if p.get('ready'):
                res = self.app.call('harvest_crop', index=p['index'])
                if res:
                    got[res['crop']] = got.get(res['crop'], 0) + res['count']
                    self.pops.append((p['index'], res['crop'], time.time()))
        self.app.refresh()
        if got:
            self.app.toast(' · '.join(f"{self.label(c)} +{n}" for c, n in got.items()), 'ok', 'heart')

    def ask_expand(self):
        i = len(self.plots())
        cost = self.plot_costs[i]
        self.app.open_overlay(ConfirmOverlay(
            self.app, f'{i + 1}번 밭 넓히기', f'{cost:,}코인으로 밭 한 칸을 넓힐까?', '넓히기', 'green',
            lambda: self.app.act('expand_plot', f'{i + 1}번 밭을 넓혔다', icon='coin')))

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
            for i in range(len(self.plot_costs) or 6):
                if self.cell_rect(i).collidepoint(event.pos):
                    self.selected = i
                    return
            if self.cell_kind(self.selected) == 'plot' and not self.plots()[self.selected].get('crop'):
                for crop, r in self.seed_rects():
                    if r.collidepoint(event.pos):
                        self.seed = crop
                        return

    def seed_rects(self):
        return [(c, pygame.Rect(PANEL.x + 12 + (i % 2) * 86, 102 + (i // 2) * 52, 82, 48))
                for i, c in enumerate(self.crops()[:6])]

    def update(self, dt):
        self.pops = [p for p in self.pops if time.time() - p[2] < POP_SECONDS]
        self.buttons = []
        if any(p.get('ready') for p in self.plots()):
            w = Button.width_for('모두 수확', icon=True) + 40
            self.buttons.append(Button((154, 32, w, 22), '모두 수확', self.harvest_all, 'orange', icon='heart'))
        x, w = PANEL.x + 12, PANEL.w - 24
        r = (x, 300, w, 40)
        kind = self.cell_kind(self.selected)
        if kind == 'plot':
            p = self.plots()[self.selected]
            if not p.get('crop'):
                n = self.seeds(self.seed) if self.seed else 0
                label = f"{self.label(self.seed)} 심기" if self.seed else '씨앗 선택'
                mins = FARM_DISPLAY['duration'] // 60
                self.buttons.append(Button(r, label, self.plant, 'green' if n else 'gray', enabled=n > 0,
                                           icon='heart', sub=f"{mins}분 뒤 수확" if n else '씨앗 없음'))
            elif p.get('ready'):
                self.buttons.append(Button(r, '수확하기', self.harvest, 'orange', icon='heart',
                                           sub=f"{self.label(p['crop'])} {FARM_DISPLAY['yield']}개"))
            else:
                self.buttons.append(Button(r, '수확하기', None, 'gray', enabled=False,
                                           sub=f"{mmss(self.remaining(p))} 남음"))
        elif kind == 'next':
            cost = self.plot_costs[self.selected]
            self.buttons.append(Button(r, '밭 넓히기', self.ask_expand, 'green', icon='coin', sub=f"{cost:,}코인"))
        else:
            self.buttons.append(Button(r, '잠김', None, 'gray', enabled=False, sub='앞 밭부터 넓히기'))

    # ---------- 그리기 ----------
    def draw(self, surface):
        surface.blit(W.background('assets/farm/farm.png'), (0, 0))
        self.back.draw(surface)
        ribbon(surface, (78, 33, 70, 18), '밭', 'red')
        if not any(p.get('ready') for p in self.plots()):
            info = f"심고 {FARM_DISPLAY['duration'] // 60}분 · 수확 {FARM_DISPLAY['yield']}개"
            box = pygame.Rect(154, 32, fit_width(info, extra=14) + 4 + 8, 22)
            card(surface, box)
            inner = card_inner(box)
            icon(surface, 'sun', (inner.x + 4, inner.y + 3))
            text_in(surface, info, (inner.x + 18, inner.y, inner.w - 18, inner.h), 'body', tag='farm')
        for i in range(len(self.plot_costs) or 6):
            self._draw_cell(surface, i)
        self._draw_pops(surface)
        self._draw_panel(surface)
        for b in self.buttons:
            b.draw(surface)

    def _draw_cell(self, surface, i):
        r = self.cell_rect(i)
        kind = self.cell_kind(i)
        t = time.time()
        if kind != 'plot':
            surface.blit(grass_tile(r.w, r.h, kind == 'next'), r)
            if kind == 'next':
                draw_sign(surface, r, [('밭 넓히기', 'small', (255, 250, 236)), ('coin', self.plot_costs[i])], True)
            else:
                draw_sign(surface, r, [('잠김', 'body', (236, 220, 200))], False)
        else:
            p = self.plots()[i]
            surface.blit(soil_tile(r.w, r.h), r)
            pos = (r.x + (r.w - 48) // 2, r.bottom - 62)
            popping = any(pi == i for pi, _, _ in self.pops)
            if p.get('crop'):
                surface.blit(self.plants.get(self.stage(p), 2), pos)
                if p.get('ready'):
                    for k, (sx, sy) in enumerate(((r.x + 18, r.y + 16), (r.right - 20, r.y + 22),
                                                  (r.right - 30, r.y + 10))):
                        if int(t * 1.5 + k) % 3:          # 천천히 깜빡
                            pygame.draw.line(surface, SPARK, (sx - 3, sy), (sx + 3, sy))
                            pygame.draw.line(surface, SPARK, (sx, sy - 3), (sx, sy + 3))
                            surface.set_at((sx, sy), T.WHITE)
                    chip(surface, (r.x + 4, r.y + 4), '수확!', 'green')
                else:
                    rem = self.remaining(p)
                    chip(surface, (r.x + 4, r.y + 4), mmss(rem), 'brown')
                    gauge(surface, (r.x + 6, r.bottom - 12, r.w - 12, 8),
                          FARM_DISPLAY['duration'] - rem, FARM_DISPLAY['duration'], 'green')
            else:
                if i == self.selected and self.seed and self.seeds(self.seed) and not popping:   # 심을 자리 미리보기
                    surface.blit(self.plants.get('sprout', 2, 128), pos)
                text(surface, '빈 밭', (r.centerx, r.y + 10), 'small', (236, 210, 180), 'midtop', shadow=(90, 56, 30))
        if i == self.selected:
            select_frame(surface, r.inflate(4, 4))

    def _draw_pops(self, surface):
        """수확: 작물 아이콘 3개가 위로 톡 튀었다 사라짐 (0.6초)."""
        now = time.time()
        for i, crop, start in self.pops:
            p = min(1.0, (now - start) / POP_SECONDS)
            r = self.cell_rect(i)
            img = self.icons.get(crop, 2).copy()
            img.set_alpha(int(255 * (1 - max(0.0, p - 0.5) * 2)))
            for dx, peak in ((-18, 30), (2, 42), (22, 28)):
                y = r.centery - 8 - int(peak * math.sin(math.pi * min(1.0, p * 1.2)) + 10 * p)
                surface.blit(img, (r.centerx - 16 + dx, y))

    def _draw_panel(self, surface):
        panel(surface, PANEL)
        x, right = PANEL.x + 12, PANEL.right - 12
        i = self.selected
        kind = self.cell_kind(i)
        if kind != 'plot':
            title = f"{i + 1}번 밭 · {'빈 땅' if kind == 'next' else '잠김'}"
            text(surface, title, (x, 70), 'title')
            surface.blit(grass_tile(ART.w, ART.h, kind == 'next'), ART)
            pygame.draw.rect(surface, T.INK, ART, 1)
            if kind == 'next':
                cost = self.plot_costs[i]
                draw_sign(surface, ART, [('밭 넓히기', 'small', (255, 250, 236)), ('coin', cost)], True)
                text(surface, '밭 넓히기', (x, 208), 'big')
                icon(surface, 'coin', (x, 230))
                text(surface, f"{cost:,}코인", (x + 15, 229), 'title')
                text(surface, '넓히면 씨앗을 심을 수 있음', (x, 270), 'small', T.TEXT_SOFT)
                text(surface, '코인이 모자라면 넓힐 수 없음', (x, 284), 'small', T.TEXT_SOFT)
            else:
                draw_sign(surface, ART, [('잠김', 'body', (236, 220, 200))], False)
                text(surface, '앞 밭을 먼저 넓히기', (x, 208), 'body', T.TEXT_SOFT)
            return
        p = self.plots()[i]
        crop = p.get('crop')
        if not crop:
            text(surface, f"{i + 1}번 밭 · 빈 밭", (x, 70), 'title')
            text(surface, '심을 씨앗 선택', (x, 86), 'small', T.TEXT_SOFT)
            for c, r in self.seed_rects():
                n = self.seeds(c)
                card(surface, r, selected=c == self.seed)
                img = self.icons.get(f'seed_{c}', 2)
                if n == 0:
                    img = img.copy()
                    img.set_alpha(115)
                surface.blit(img, (r.x + 4, r.y + 8))
                text_in(surface, self.label(c), (r.x + 38, r.y + 6, r.w - 40, 17), 'body',
                        T.TEXT if n else T.TEXT_SOFT, align='left', tag='farm')
                text_in(surface, f"보유 {n}", (r.x + 38, r.y + 25, r.w - 40, 15), 'small',
                        T.TEXT_SOFT if n else T.BAD, align='left', tag='farm')
            if self.seed:
                text(surface, f"씨앗 1개 → {self.label(self.seed)} {FARM_DISPLAY['yield']}개", (x, 264), 'small')
                price = (self.catalog.get(f'seed_{self.seed}') or {}).get('buy')
                if price is not None:
                    text(surface, f"씨앗은 상점에서 {price:,}코인", (x, 280), 'small', T.TEXT_SOFT)
            return
        text(surface, f"{i + 1}번 밭 · {self.label(crop)}", (x, 70), 'title')
        surface.blit(soil_tile(ART.w, ART.h), ART)
        img = self.plants.get(self.stage(p), 3)
        surface.blit(img, img.get_rect(center=ART.center))
        if p.get('ready'):
            chip(surface, (x, 86), '수확 가능', 'green')
            text(surface, '받는 것', (x, 204), 'small', T.TEXT_SOFT)
            surface.blit(self.icons.get(crop, 2), (x, 218))
            text(surface, f"{self.label(crop)} ×{FARM_DISPLAY['yield']}", (x + 38, 234), 'big', anchor='midleft')
            have = self.have(crop)
            text(surface, f"가방 보유 {have} → {have + FARM_DISPLAY['yield']}", (x, 262), 'small')
            text(surface, '수확하면 빈 밭이 됨', (x, 278), 'small', T.TEXT_SOFT)
        else:
            rem = self.remaining(p)
            chip(surface, (x, 86), '자라는 중', 'brown')
            text(surface, '남은 시간', (x, 204), 'small', T.TEXT_SOFT)
            text(surface, mmss(rem), (x, 216), 'big')
            gauge(surface, (x, 238, right - x, 10), FARM_DISPLAY['duration'] - rem, FARM_DISPLAY['duration'], 'green')
            surface.blit(self.icons.get(crop, 1), (x, 260))
            text(surface, f"다 자라면 {self.label(crop)} ×{FARM_DISPLAY['yield']}", (x + 20, 262), 'small')
