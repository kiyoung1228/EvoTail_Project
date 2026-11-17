"""태풍 연출 · 2배 이벤트 표시 (목업 docs/mockups/storm/, tools/storm_mock.py).

판단은 스냅샷 clock.storm 하나만 본다 (시간 02~06시를 GUI에서 계산하지 않음).
백엔드(roc, 팀 확정): 태풍 중 "시작한" 훈련 능력치 2배, 태풍 중 일반(mode normal) 스테이지 승리 보상 2배. 대회·뉴비는 해당 없음.
"""
import math
import random
import pygame

from . import theme as T
from .widgets import text_in, glyph_box, fit_width, chip, chip_width, nine, record, Kit, CHIP_H

# 백엔드가 배수를 따로 주지 않음 → roc 훈련·전투 보상 2배(service.start_training·_settle_battle)와 맞출 것
STORM_MULTIPLIER = 2

# ---------- 표시 문구 (한 곳) ----------
BAND_TITLE = '태풍'
BAND_EVENT = '2배 이벤트'
BAND_CHIPS = (f'훈련 효과 ×{STORM_MULTIPLIER}', f'일반 전투 보상 ×{STORM_MULTIPLIER}')
HEADER_CHIP = '태풍'
HEADER_TIP = f'{STORM_MULTIPLIER}배 이벤트 · 훈련 효과·일반 전투 보상 {STORM_MULTIPLIER}배'
TOAST_START = ('태풍이 왔다! 2배 이벤트 시작', f'훈련 효과 {STORM_MULTIPLIER}배 · 일반 전투 보상 {STORM_MULTIPLIER}배')
TOAST_END = ('태풍이 지나갔다', '2배 이벤트 끝')
GOLD = (255, 236, 120)          # 2배가 된 숫자 (훈련 버튼·스테이지 보상)
EVENT_GOLD = ((255, 226, 110), (255, 250, 210))   # 띠의 "2배 이벤트": 밝게 ↔ 연하게

# ---------- 지도 연출 ----------
SHADE = (18, 26, 64, 70)            # 지도 영역 남색 그늘
FLASH = (236, 240, 255)             # 번개 번쩍
FLASH_ALPHA = 60
BOLT_SECONDS, FLASH_SECONDS = 0.15, 0.3
BOLT_EVERY = (6.0, 10.0)            # 번개 간격 (초, 무작위)
NEAR = ((196, 214, 250, 190), 7, 300)    # 앞쪽 빗줄기: 색, 길이, 속도(px/초)
FAR = ((150, 170, 220, 120), 4, 190)     # 뒤쪽 빗줄기
NEAR_SHARE = 0.35
SPLASH = (200, 220, 255)
ISLAND = (8, 40, 592, 312)          # 섬 타원 (지도 그림 기준, tools/storm_mock.py storm_clouds) — 먹구름은 이 밖에만
CLUMPS = ((22, 46, 18), (46, 40, 20), (70, 50, 16), (34, 62, 14), (8, 70, 14), (96, 42, 13),
          (500, 38, 14), (526, 46, 16), (552, 40, 18), (570, 58, 14), (12, 300, 14), (30, 316, 12))


def is_storm(app):
    return bool((app.state.get('clock') or {}).get('storm'))


class Rain:
    """빗줄기 (+ 땅 위 튀김). 좌표는 처음에 한 번 만들어 두고 이동만. 1px 선이 아래로 2 · 왼쪽으로 1."""

    def __init__(self, box, n=260, seed=3, splash=30):
        self.box = pygame.Rect(box)
        rng = random.Random(seed)
        self.drops = []
        for _ in range(n):
            near = rng.random() < NEAR_SHARE
            self.drops.append([rng.uniform(self.box.left, self.box.right), rng.uniform(self.box.top, self.box.bottom),
                               NEAR if near else FAR])
        self.splashes = [[rng.uniform(self.box.left + 4, self.box.right - 4),
                          rng.uniform(self.box.top + 40, self.box.bottom - 4), rng.uniform(0, 1)]
                         for _ in range(splash)]
        self.rng = rng
        self.layer = pygame.Surface(self.box.size, pygame.SRCALPHA)

    def update(self, dt):
        b = self.box
        for d in self.drops:
            sp = d[2][2] * dt
            d[1] += sp
            d[0] -= sp / 2
            if d[1] > b.bottom:
                d[1] -= b.h
            if d[0] < b.left:
                d[0] += b.w
        for s in self.splashes:                                     # 점 2개 → 점 3개 → 작은 타원 → 사라짐
            s[2] += dt / 0.5
            if s[2] >= 1:
                s[2] -= 1
                s[0] = self.rng.uniform(b.left + 4, b.right - 4)
                s[1] = self.rng.uniform(b.top + 40, b.bottom - 4)

    def draw(self, surface, mask=None):
        lay = self.layer
        lay.fill((0, 0, 0, 0))
        ox, oy = self.box.topleft
        for x, y, (color, length, _) in self.drops:
            x, y = int(x) - ox, int(y) - oy
            pygame.draw.line(lay, color, (x, y), (x - length // 2, y + length))
        for x, y, ph in self.splashes:
            x, y = int(x) - ox, int(y) - oy
            stage = int(ph * 4)
            if stage == 0:
                lay.set_at((x - 1, y), SPLASH + (170,)); lay.set_at((x + 1, y), SPLASH + (170,))
            elif stage == 1:
                for p in ((x - 2, y - 1), (x + 2, y - 1), (x, y)):
                    lay.set_at(p, SPLASH + (140,))
            elif stage == 2:
                pygame.draw.ellipse(lay, (170, 196, 240, 90), (x - 3, y - 1, 7, 3), 1)
        if mask is not None:
            lay.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(lay, self.box)


class Lightning:
    """6~10초마다 무작위로 한 번: 먹구름에서 섬 가장자리 쪽 꺾인 번개 0.15초 + 흰 번쩍 0.3초 페이드."""

    def __init__(self, seed=11):
        self.rng = random.Random(seed)
        self.t = 0.0
        self.next_at = self.rng.uniform(*BOLT_EVERY)
        self.at = None
        self.pos = None

    def update(self, dt):
        self.t += dt
        if self.t >= self.next_at:
            self.at = self.t
            cx, cy, _ = self.rng.choice(CLUMPS[:10])                # 위쪽 먹구름에서
            self.pos = (cx, cy + 4)
            self.next_at = self.t + self.rng.uniform(*BOLT_EVERY)

    def strike(self):
        """지금 번개를 치게 함 (스크린샷·점검용)."""
        self.next_at = self.t

    def draw(self, surface, box):
        if self.at is None:
            return
        e = self.t - self.at
        if e < FLASH_SECONDS:
            a = round(FLASH_ALPHA * (1 - e / FLASH_SECONDS))
            flash = pygame.Surface(box.size, pygame.SRCALPHA)
            flash.fill(FLASH + (a,))
            surface.blit(flash, box)
        if e < BOLT_SECONDS:
            x, y = self.pos
            pts = [(x, y), (x - 5, y + 10), (x + 1, y + 12), (x - 7, y + 24), (x - 1, y + 26), (x - 10, y + 40)]
            pygame.draw.lines(surface, (255, 214, 90), False, pts, 4)
            pygame.draw.lines(surface, (255, 252, 230), False, pts, 2)
            pygame.draw.line(surface, (255, 240, 180), pts[1], (pts[1][0] - 6, pts[1][1] + 6))


_cache = {}


def clouds():
    """섬 밖 하늘 먹구름 덩어리 (달 가림, 섬 위 건물은 안 가림). 한 번 만든 Surface 재사용."""
    if 'clouds' not in _cache:
        s = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        for cx, cy, r in CLUMPS:
            pygame.draw.ellipse(s, (40, 44, 70, 240), (cx - r, cy - r // 2 + 2, 2 * r, r + 1))
            pygame.draw.ellipse(s, (66, 70, 100, 240), (cx - r + 2, cy - r // 2, 2 * r - 4, r))
            pygame.draw.arc(s, (96, 100, 134, 240), (cx - r + 4, cy - r // 2 + 1, 2 * r - 10, r - 3),
                            math.radians(200), math.radians(300))
        pygame.draw.ellipse(s, (0, 0, 0, 0), ISLAND)                 # 섬 타원 안은 비움
        _cache['clouds'] = s
    return _cache['clouds']


def shade(size):
    key = ('shade', size)
    if key not in _cache:
        s = pygame.Surface(size, pygame.SRCALPHA)
        s.fill(SHADE)
        _cache[key] = s
    return _cache[key]


# ---------- 2배 이벤트 띠 ----------
def band_size(row=False):
    """띠 크기: 리본 + 칩 2개 (row = 한 줄로 옆에, 아니면 리본 아래 칩 줄)."""
    rw = ribbon_width()
    chips = sum(chip_width(c) for c in BAND_CHIPS) + 3
    if row:
        return rw + 6 + chips, 18
    return max(rw, chips + 4), 18 + 3 + CHIP_H


def ribbon_width():
    return 10 + 12 + 3 + fit_width(f'{BAND_TITLE} {BAND_EVENT}', 'title', shadow=True) + 10


def band(surface, pos, t, row=False):
    """파란 리본 + 비구름 + 흰 "태풍" + 금색 "2배 이벤트"(천천히 깜빡) / 주황 칩 2개. 그린 영역을 돌려줌."""
    x, y = pos
    rw = ribbon_width()
    r = pygame.Rect(x, y, rw, 18)
    nine(surface, 'ribbon_blue', r)
    surface.blit(Kit.icon('rain'), (x + 10, y + 3))
    edge = T.shade('blue', 0)
    tx = x + 10 + 12 + 3
    w1 = glyph_box(BAND_TITLE, 'title').w + 1
    a = text_in(surface, BAND_TITLE, (tx, y + 1, w1 + 2, 16), 'title', T.WHITE, shadow=edge, align='left', pad=0,
                log=False)
    gx = tx + w1 + glyph_box(' ', 'title').w + 4
    phase = (math.sin(t * math.pi * 2 / 1.6) + 1) / 2                 # 1.6초에 한 번 밝게 ↔ 연하게
    gold = tuple(round(c0 + (c1 - c0) * phase) for c0, c1 in zip(*EVENT_GOLD))
    b = text_in(surface, BAND_EVENT, (gx, y + 1, glyph_box(BAND_EVENT, 'title').w + 2, 16), 'title', gold,
                shadow=edge, align='left', pad=0, log=False)
    record(f'{BAND_TITLE} {BAND_EVENT}', a.union(b), pygame.Rect(x + 5, y + 1, rw - 10, 16).inflate(0, 0), 'storm-band')
    cx, cy = (r.right + 6, y + 1) if row else (x + 4, y + 21)
    area = r.copy()
    for label in BAND_CHIPS:
        c = chip(surface, (cx, cy), label, 'orange')
        area.union_ip(c)
        cx = c.right + 3
    return area


def header_chip(surface, pos):
    """상단 바 가운데 칸 안: 파란 칩(비구름 + 흰 "태풍"). 그린 칩 rect."""
    w = 2 + 1 + 12 + 2 + fit_width(HEADER_CHIP, 'small', shadow=True) + 1
    r = pygame.Rect(pos[0], pos[1], w, CHIP_H)
    pygame.draw.rect(surface, T.shade('blue', 2), r)
    pygame.draw.line(surface, T.shade('blue', 3), (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
    pygame.draw.rect(surface, T.INK, r, 1)
    surface.blit(Kit.icon('rain'), (r.x + 3, r.y + 2))
    text_in(surface, HEADER_CHIP, (r.x + 16, r.y + 1, r.w - 17, r.h - 2), 'small', T.WHITE,
            shadow=T.shade('blue', 0), tag='header')
    return r


def header_chip_width():
    return 2 + 1 + 12 + 2 + fit_width(HEADER_CHIP, 'small', shadow=True) + 1


# ---------- 마이룸 창문 ----------
def glass_mask(background, g):
    """마이룸 창 유리 마스크 (흰 = 비를 그림). 아치(위 반타원) + 사각형, 창살 색 픽셀·창턱 화분 자리는 뺌."""
    x0, y0, w, h, arch = g['x'], g['y'], g['w'], g['h'], g['arch']
    m = pygame.Surface((w, h + arch), pygame.SRCALPHA)
    pygame.draw.rect(m, (255, 255, 255, 255), (0, arch, w, h))
    pygame.draw.ellipse(m, (255, 255, 255, 255), (0, 0, w, arch * 2))
    bars = {tuple(c) for c in g['bar_colors']}
    for yy in range(h + arch):
        for xx in range(w):
            px = background.get_at((x0 + xx, y0 + yy))[:3]
            if px in bars or any(k[0] <= x0 + xx < k[2] and k[1] <= y0 + yy < k[3] for k in g['keepouts']):
                m.set_at((xx, yy), (0, 0, 0, 0))
    return m


class GlassDrops:
    """유리에 맺힌 물방울 14개 (가끔 아래로 흐르는 1px 줄)."""

    def __init__(self, g, n=14, seed=4):
        rng = random.Random(seed)
        self.drops = [(rng.randrange(g['x'] + 3, g['x'] + g['w'] - 3),
                       rng.randrange(g['y'] + g['arch'] + 2, g['y'] + g['arch'] + g['h'] - 3),
                       rng.uniform(0, 6), rng.random() < 0.4) for _ in range(n)]

    def draw(self, surface, t):
        for x, y, off, runs in self.drops:
            surface.set_at((x, y), (220, 236, 255))
            surface.set_at((x, y + 1), (140, 170, 220))
            if runs:                                                 # 가끔(6초에 1.5초) 아래로 흐르는 줄
                ph = (t + off) % 6
                if ph < 1.5:
                    n = 2 + int(ph * 3)
                    pygame.draw.line(surface, (170, 196, 240), (x, y + 2), (x, y + 1 + n))
