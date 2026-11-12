"""전투장 쪽 코드 도트 배경: 전투 바닥, 출전 준비의 상대 칸(적 진영)·내 팀 칸(우리 진영)."""
import random
import pygame
from .. import theme as T

_cache = {}
INK = T.INK


def _px(s, x, y, c):
    if 0 <= x < s.get_width() and 0 <= y < s.get_height():
        s.set_at((x, y), c)


def pebble(s, x, y, rng):
    c = rng.choice([(176, 150, 112), (160, 140, 116), (190, 170, 140)])
    w = rng.choice((2, 3, 4))
    pygame.draw.rect(s, c, (x, y, w, 2))
    _px(s, x, y, (226, 210, 176)); pygame.draw.line(s, (130, 108, 80), (x, y + 2), (x + w - 1, y + 2))


def tuft(s, x, y, dark=(92, 150, 70), light=(130, 188, 92)):
    for dx, h, c in ((0, 3, dark), (1, 5, light), (2, 4, dark), (3, 2, light)):
        pygame.draw.line(s, c, (x + dx, y), (x + dx, y - h + 1))


def flower(s, x, y, petal):
    for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): _px(s, x + dx, y + dy, petal)
    _px(s, x, y, (255, 230, 90)); _px(s, x, y + 2, (80, 140, 60)); _px(s, x, y + 3, (80, 140, 60))


def floor(s, top, rng, w=None, h=None):
    """모래 바닥: 깊이 따라 조금씩 진해지는 띠 + 모래 결 + 자갈 + 발자국 + 벽 밑 그림자·풀"""
    W, H = w or s.get_width(), h or s.get_height()
    sand = [(240, 216, 164), (236, 210, 156), (232, 204, 148), (228, 198, 142)]
    for y in range(top, H):
        t = (y - top) / max(1, H - top)
        pygame.draw.line(s, sand[min(3, int(t * 4))], (0, y), (W, y))
    for i in range(4):                                                # 벽 밑 그림자
        pygame.draw.line(s, (206 - i * 6 + 18, 178 - i * 6 + 18, 126 - i * 6 + 18), (0, top + i), (W, top + i))
    pygame.draw.line(s, (196, 166, 116), (0, top), (W, top))
    for _ in range(int(W * (H - top) / 90)):                          # 모래 점
        x, y = rng.randrange(W), rng.randrange(top + 3, H)
        _px(s, x, y, (214, 182, 126) if rng.random() < .65 else (250, 232, 192))
    for _ in range(int(W * (H - top) / 900)):                         # 모래 결 (짧은 가로 줄)
        x, y = rng.randrange(W), rng.randrange(top + 6, H)
        L = rng.randrange(4, 9)
        pygame.draw.line(s, (220, 190, 136), (x, y), (x + L, y)); pygame.draw.line(s, (248, 228, 186), (x + 1, y - 1), (x + L - 1, y - 1))
    for _ in range(int(W * (H - top) / 1400)):
        pebble(s, rng.randrange(W - 4), rng.randrange(top + 6, H - 3), rng)
    for x in range(4, W, rng.randrange(18, 30)):                      # 벽 밑 잡초
        if rng.random() < .55: tuft(s, x, top + 4, (150, 160, 90), (176, 186, 110))


def hay(s, x, y):
    """건초 더미 (벽 앞 소품)"""
    pygame.draw.rect(s, INK, (x, y, 22, 14)); pygame.draw.rect(s, (236, 196, 92), (x + 1, y + 1, 20, 12))
    pygame.draw.line(s, (255, 228, 140), (x + 1, y + 1), (x + 20, y + 1))
    for yy in (y + 4, y + 9): pygame.draw.line(s, (196, 150, 60), (x + 1, yy), (x + 20, yy))
    for xx in (x + 6, x + 15): pygame.draw.line(s, (150, 96, 50), (xx, y + 1), (xx, y + 12))
    for i in range(0, 20, 3): _px(s, x + 1 + i, y, (236, 196, 92))


def barrel(s, x, y):
    pygame.draw.rect(s, INK, (x, y, 14, 18)); pygame.draw.rect(s, (168, 110, 64), (x + 1, y + 1, 12, 16))
    pygame.draw.line(s, (200, 140, 86), (x + 3, y + 1), (x + 3, y + 16))
    for yy in (y + 4, y + 13): pygame.draw.line(s, (96, 92, 102), (x + 1, yy), (x + 12, yy))
    pygame.draw.line(s, (120, 76, 44), (x + 11, y + 1), (x + 11, y + 16))


def rack(s, x, y):
    """나무 무기 걸이 (목검 2개 + 방패)"""
    pygame.draw.rect(s, (130, 86, 50), (x, y + 4, 26, 3)); pygame.draw.rect(s, INK, (x, y + 4, 26, 3), 1)
    for xx in (x + 1, x + 23): pygame.draw.rect(s, (130, 86, 50), (xx, y + 4, 2, 16))
    for xx in (x + 7, x + 12):
        pygame.draw.line(s, (220, 200, 160), (xx, y - 4), (xx, y + 14)); pygame.draw.line(s, (120, 80, 50), (xx - 1, y + 2), (xx + 1, y + 2))
    pygame.draw.ellipse(s, INK, (x + 15, y + 7, 9, 11)); pygame.draw.ellipse(s, (90, 150, 220), (x + 16, y + 8, 7, 9))
    _px(s, x + 19, y + 12, (250, 204, 70))


def arena_floor(s, top, rng):
    """전투 바닥 장식: 고르게 긁은 경기장 원(안쪽 모래·결), 테두리 두 줄, 가운데 문장, 양 진영 출발선, 발자국, 벽 앞 소품"""
    import math
    W, H = s.get_size()
    cx, cy, rx, ry = W // 2, 214, 250, 73
    # 안쪽: 갈퀴로 고른 모래 (동심원 결)
    inner = pygame.Surface((rx * 2, ry * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(inner, (226, 194, 138, 110), inner.get_rect())
    s.blit(inner, (cx - rx, cy - ry))
    for k in range(1, 6):
        r2x, r2y = rx * k / 6, ry * k / 6
        for i in range(0, 360, 3):
            if (i // 3 + k) % 4 == 0: continue
            a = math.radians(i)
            _px(s, int(cx + r2x * math.cos(a)), int(cy + r2y * math.sin(a)), (216, 182, 124))
    chalk, chalk2 = (252, 240, 214), (204, 170, 116)
    pygame.draw.ellipse(s, chalk2, (cx - rx - 3, cy - ry - 2, rx * 2 + 6, ry * 2 + 4), 2)
    pygame.draw.ellipse(s, chalk, (cx - rx, cy - ry, rx * 2, ry * 2), 2)
    # 가운데 문장: 발바닥 (흰 분필)
    pygame.draw.ellipse(s, chalk, (cx - 30, cy - 12, 60, 24), 1)
    pygame.draw.ellipse(s, (240, 220, 180), (cx - 9, cy - 2, 18, 9))
    for dx, dy in ((-13, -7), (-5, -10), (5, -10), (13, -7)):
        pygame.draw.ellipse(s, (240, 220, 180), (cx + dx - 3, cy + dy - 1, 6, 4))
    # 양 진영 출발선 (아군 파랑 · 적 빨강, 원 안쪽 호)
    for side, col, dk in ((-1, (110, 160, 224), (70, 116, 180)), (1, (230, 104, 94), (180, 64, 60))):
        for i in range(-34, 35, 2):
            a = math.radians(i)
            x = int(cx + side * (rx - 46) * math.cos(a)); y = int(cy + (ry - 10) * math.sin(a))
            pygame.draw.rect(s, col, (x, y, 2, 2)); _px(s, x + 1, y + 2, dk)
    # 발자국
    for fx, fy in ((150, 238), (166, 232), (182, 240), (198, 234), (214, 242)):
        pygame.draw.ellipse(s, (208, 174, 120), (fx, fy, 4, 3))
        for t in range(3): _px(s, fx - 1 + t * 2, fy - 2, (208, 174, 120))
    for fx, fy in ((470, 172), (456, 178), (442, 170), (428, 176)):
        pygame.draw.ellipse(s, (208, 174, 120), (fx, fy, 4, 3))
    # 벽 앞 소품 (원 밖)
    hay(s, 10, top + 6); hay(s, 26, top + 12)
    rack(s, 90, top + 4)
    barrel(s, W - 34, top + 6); barrel(s, W - 50, top + 10)
    hay(s, W - 112, top + 8)
    # 흩어진 깃털·나무 창
    pygame.draw.line(s, (240, 240, 250), (88, 262), (96, 256)); pygame.draw.line(s, (200, 200, 220), (89, 263), (97, 257))
    pygame.draw.line(s, (130, 92, 60), (560, 256), (584, 250)); pygame.draw.line(s, (100, 70, 44), (560, 257), (584, 251))


def foe_backdrop(w, h):
    """출전 준비 상대 칸: 적 진영 (돌벽·빨간 깃발·횃불 + 모래 바닥)"""
    key = ('foe', w, h)
    if key in _cache: return _cache[key]
    s = pygame.Surface((w, h)); rng = random.Random(11)
    s.fill((70, 56, 64))
    wall_b = 44
    pygame.draw.rect(s, (112, 100, 108), (0, 0, w, wall_b))
    for row, y in enumerate(range(0, wall_b, 7)):
        pygame.draw.line(s, (84, 74, 82), (0, y), (w, y))
        for x in range((row % 2) * 9, w, 18): pygame.draw.line(s, (84, 74, 82), (x, y), (x, y + 6))
        for x in range((row % 2) * 9 + 1, w, 18): pygame.draw.line(s, (136, 124, 132), (x, y + 1), (x + 15, y + 1))
    pygame.draw.line(s, INK, (0, wall_b), (w, wall_b))
    for i, x in enumerate(range(24, w, 70)):                          # 빨간 깃발 (적 진영)
        pygame.draw.rect(s, INK, (x - 8, 2, 17, 26)); pygame.draw.rect(s, (200, 64, 64), (x - 7, 3, 15, 22))
        pygame.draw.rect(s, (232, 100, 90), (x - 7, 3, 15, 3))
        pygame.draw.polygon(s, (200, 64, 64), [(x - 7, 25), (x + 7, 25), (x, 31)])
        pygame.draw.lines(s, INK, False, [(x - 8, 25), (x, 32), (x + 8, 25)])
        pygame.draw.rect(s, (250, 204, 70), (x - 2, 11, 5, 5)); pygame.draw.rect(s, INK, (x - 2, 11, 5, 5), 1)  # 문장
        tx = x + 35
        if tx < w - 4:                                                 # 횃불 + 빛
            glow = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 190, 90, 60), (12, 12), 11); s.blit(glow, (tx - 11, 2))
            pygame.draw.rect(s, (90, 60, 40), (tx - 1, 12, 3, 18)); pygame.draw.rect(s, INK, (tx - 2, 11, 5, 2))
            pygame.draw.rect(s, (255, 150, 60), (tx - 2, 5, 5, 6)); pygame.draw.rect(s, (255, 236, 150), (tx - 1, 7, 3, 3))
    floor(s, wall_b + 1, rng)
    # 적 쪽 바닥: 빨간 출발선
    for x in range(6, w - 6, 6): pygame.draw.line(s, (220, 110, 100), (x, h - 30), (x + 2, h - 30))
    _cache[key] = s
    return s


def team_backdrop(w, h, avoid=()):
    """출전 준비 내 팀 칸: 우리 진영 (하늘·언덕·울타리·깃발 줄 + 꽃 핀 풀밭).
    avoid = 깃발을 걸지 않을 가로 범위 [(x0, x1), ...] (칸 왼쪽 기준, 예: ✕ 빼기 버튼 자리)"""
    key = ('team', w, h, tuple(avoid))
    if key in _cache: return _cache[key]
    s = pygame.Surface((w, h)); rng = random.Random(5)
    sky = [(176, 222, 244), (190, 230, 246), (206, 236, 248)]
    for y in range(h): pygame.draw.line(s, sky[min(2, y * 3 // 40)], (0, y), (w, y))
    for cx, cy, cw in ((40, 12, 22), (200, 8, 28), (130, 18, 14)):
        pygame.draw.rect(s, (255, 255, 255), (cx - cw // 2, cy, cw, 4)); pygame.draw.rect(s, (255, 255, 255), (cx - cw // 4, cy - 3, cw // 2, 3))
    pygame.draw.ellipse(s, (150, 204, 120), (-40, 26, 180, 60)); pygame.draw.ellipse(s, (136, 196, 108), (110, 22, 220, 70))
    gy = 46
    pygame.draw.rect(s, (156, 212, 120), (0, gy, w, h - gy))
    for y in range(gy, h):
        if (y - gy) % 9 == 0: pygame.draw.line(s, (148, 204, 112), (0, y), (w, y))
    pygame.draw.line(s, (186, 232, 146), (0, gy), (w, gy))
    # 울타리
    fy = gy - 6
    pygame.draw.rect(s, (176, 124, 76), (0, fy + 2, w, 2)); pygame.draw.rect(s, (176, 124, 76), (0, fy + 6, w, 2))
    pygame.draw.line(s, (120, 80, 50), (0, fy + 4), (w, fy + 4)); pygame.draw.line(s, (120, 80, 50), (0, fy + 8), (w, fy + 8))
    for x in range(6, w, 22):
        pygame.draw.rect(s, (196, 140, 88), (x, fy - 2, 4, 12)); pygame.draw.rect(s, (110, 72, 44), (x, fy - 2, 4, 12), 1)
    # 파란 깃발 줄 (우리 팀)
    pts = [(x, 4 + int(6 * (1 - ((x - w / 2) / (w / 2)) ** 2))) for x in range(0, w + 1, 2)]
    pygame.draw.lines(s, (110, 80, 60), False, pts)
    cols = [(90, 150, 220), (250, 204, 70), (110, 190, 110)]
    for i, x in enumerate(range(10, w - 6, 18)):
        if any(a0 - 5 <= x <= a1 + 5 for a0, a1 in avoid): continue
        y = 4 + int(6 * (1 - ((x - w / 2) / (w / 2)) ** 2))
        c = cols[i % 3]
        pygame.draw.polygon(s, c, [(x - 4, y), (x + 4, y), (x, y + 8)]); pygame.draw.lines(s, INK, True, [(x - 4, y), (x + 4, y), (x, y + 8)])
    # 풀·꽃
    for _ in range(w * (h - gy) // 60):
        x, y = rng.randrange(w), rng.randrange(gy + 2, h)
        _px(s, x, y, (128, 186, 94) if rng.random() < .6 else (182, 230, 140))
    for _ in range(w // 9): tuft(s, rng.randrange(w - 4), rng.randrange(gy + 6, h), (104, 168, 80), (140, 200, 100))
    for _ in range(w // 14):
        flower(s, rng.randrange(3, w - 3), rng.randrange(gy + 6, h - 4), rng.choice([(255, 255, 255), (255, 170, 190), (255, 220, 110), (190, 170, 255)]))
    _cache[key] = s
    return s
