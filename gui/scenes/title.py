"""시작: 로딩(LoadingScene) → 표지(TitleScene). 목업 docs/mockups/title/title_v5.png · title_v5_idle.gif · title_v5_newgame.gif.

그림은 assets/title/ (논리 크기의 2배 → ½로 그대로), 자리·속도는 assets/title/title.json에서 읽는다 (코드에 숫자 X).
그리는 순서: back → 구름(오른쪽으로 흐름) → 섬 2개(위아래 ±2px) → 새 떼 → mid → 동물 행렬 + 테크모(발 y 순서)
→ 매화 꽃잎 + 빛 알갱이 → front → 로고(+ 반짝이) → 메뉴.
다시 만들기: python tools/title_assets.py (tools/title5.py의 코드 도트를 그림으로 내보냄)
"""
import json
import math
import os
import random
import time
import pygame

from .. import theme as T
from .. import widgets as W
from .. import guide as G
from ..app import Scene
from ..widgets import text, text_in, record, card, gauge, mouse_pos

TITLE_DIR = os.path.join(T.ROOT, 'assets', 'title')
with open(os.path.join(TITLE_DIR, 'title.json'), encoding='utf-8') as _f:
    META = json.load(_f)
MENU = ('새 게임', '이어하기', '설정', '게임 종료')
MENU_W = 150                     # 한지 판 폭 (tools/title5.py menu())
HANJI = (255, 250, 238, 170)
HANJI_EDGE = (120, 86, 60, 220)
PETAL = ((255, 206, 222), (255, 244, 248))
MOTE = ((255, 250, 190), (210, 236, 255))


class TitleArt:
    """표지 그림 묶음 (표지·새 게임 흐름 공용). ½ 축소는 한 번만."""

    def __init__(self):
        self._img = {}

    def half(self, name):
        if name not in self._img:
            img = pygame.image.load(os.path.join(TITLE_DIR, f'{name}.png')).convert_alpha()
            self._img[name] = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
        return self._img[name]

    def layer(self, name):
        return W.background(f'assets/title/{name}.png')

    def preload(self):
        for name in ('back', 'mid', 'front'):
            self.layer(name)
        for name in ['logo', 'island_left', 'island_right'] + [f'cloud_{i}' for i in range(len(META['clouds']))]:
            self.half(name)

    # ----- 뒤 (하늘·구름·섬·새) -----
    def sky(self, surface, t):
        surface.blit(self.layer('back'), (0, 0))
        span = T.WIDTH + 120
        for i, (x, y, speed) in enumerate(META['clouds']):
            img = self.half(f'cloud_{i}')
            cx = (x + t * speed) % span - 60                       # 화면 밖으로 나가면 왼쪽에서 다시
            surface.blit(img, (round(cx), y))
        for k, (name, (x, y)) in enumerate(META['islands'].items()):
            dy = round(2 * math.sin((t / 4 + k * 0.4) * math.pi * 2))    # 위아래 ±2px, 주기 4초
            surface.blit(self.half(name), (x, y + dy))
        for i in range(4):                                         # 새 떼
            bx = (430 - i * 12 + int(t * 220 / 3)) % 720 - 40
            y = 46 + (i % 2) * 5
            up = 2 if (int(t * 8) + i) % 2 else -1
            pygame.draw.lines(surface, (70, 80, 110), False, [(bx - 3, y - up), (bx, y), (bx + 3, y - up)])

    def ground(self, surface):
        surface.blit(self.layer('mid'), (0, 0))

    def front(self, surface):
        surface.blit(self.layer('front'), (0, 0))

    def garden(self, surface, t, dim=0):
        """표지 정원 (로고·메뉴·행렬 없이). 새 게임 흐름 배경."""
        self.sky(surface, t)
        self.ground(surface)
        self.front(surface)
        if dim:
            shade = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
            shade.fill((20, 14, 30, dim))
            surface.blit(shade, (0, 0))

    # ----- 날림 -----
    @staticmethod
    def petals(surface, t):
        """매화 꽃잎 (title.json blossoms_sample에서 날려 오른쪽 아래로)."""
        src = META['blossoms_sample']
        rng = random.Random(21)
        t = t / 3
        for i in range(46):
            sx, sy = src[rng.randrange(len(src))]
            ph = (t + i / 46) % 1
            x = int(sx + ph * 140 + 6 * math.sin(ph * math.pi * 6 + i))
            y = int(sy + ph * 120)
            if y > 350 or not (0 <= x < T.WIDTH - 1):
                continue
            c = PETAL[0] if i % 3 else PETAL[1]
            surface.set_at((x, y), c)
            surface.set_at((x + 1, y) if int(ph * 20 + i) % 2 else (x, y + 1), c)

    @staticmethod
    def motes(surface, t):
        """떠다니는 빛 알갱이."""
        rng = random.Random(9)
        t = t / 3
        for i in range(18):
            x0, y0 = rng.randrange(T.WIDTH), rng.randrange(150, 330)
            ph = (t + i / 18) % 1
            x, y = int(x0 + 8 * math.sin(ph * math.pi * 2 + i)), int(y0 - ph * 40)
            a = math.sin(ph * math.pi)
            if a > .3 and 0 <= x < T.WIDTH - 1 and 1 <= y < T.HEIGHT:
                c = MOTE[i % 2]
                surface.set_at((x, y), c)
                if a > .75:
                    surface.set_at((x + 1, y), c)
                    surface.set_at((x, y - 1), c)

    # ----- 로고 -----
    def logo(self, surface, t, jump=None):
        """로고 그림 + 반짝이. jump = (글자 번호, 높이): 그 글자 기둥만 위로 (부제 띠는 그대로)."""
        img = self.half('logo')
        lx, ly = META['logo_topleft']
        if jump is None:
            surface.blit(img, (lx, ly))
        else:
            i, h = jump
            x0, x1 = META['logo_letters'][i]
            bottom = META['logo_letters_bottom']
            surface.blit(img, (lx, ly), pygame.Rect(0, 0, x0, img.get_height()))
            surface.blit(img, (lx + x1, ly), pygame.Rect(x1, 0, img.get_width() - x1, img.get_height()))
            surface.blit(img, (lx + x0, ly + bottom), pygame.Rect(x0, bottom, x1 - x0, img.get_height() - bottom))
            surface.blit(img, (lx + x0, ly - h), pygame.Rect(x0, 0, x1 - x0, bottom))
        for i, (sx, sy) in enumerate(META['logo_sparkles']):        # 반짝이 깜빡
            ph = (t * 2 / 3 + i * .29) % 1
            if ph < .55:
                r = 1 + int(ph * 6) % 3
                pygame.draw.line(surface, (255, 255, 230), (sx - r, sy), (sx + r, sy))
                pygame.draw.line(surface, (255, 255, 230), (sx, sy - r), (sx, sy + r))
                surface.set_at((sx, sy), T.WHITE)

    @staticmethod
    def logo_hit(pos):
        """로고에서 누른 곳: ('tail', None) / ('letter', 번호) / None."""
        lx, ly = META['logo_topleft']
        x, y = pos[0] - lx, pos[1] - ly
        tx0, ty0, tx1, ty1 = META['logo_tail']
        if tx0 <= x < tx1 and ty0 <= y < ty1:
            return 'tail', None
        if 0 <= y < META['logo_letters_bottom']:
            for i, (x0, x1) in enumerate(META['logo_letters']):
                if x0 <= x < x1:
                    return 'letter', i
        return None


ART = TitleArt()


def techmo_topleft(img, feet):
    """발 가운데 좌표 → 그림 왼쪽 위 (그림 아래 투명 여백은 빼고 발이 딱 닿게)."""
    bb = img.get_bounding_rect()
    return feet[0] - img.get_width() // 2, feet[1] - bb.bottom


def parade_keys(catalog):
    """일반 15종 (도감 순서 = get_catalog 순서)."""
    return [k for k, v in catalog.items() if v.get('rarity') == 'normal']


def stage1_sprite(info):
    sprites = info.get('stage_sprites') or []
    return sprites[0] if sprites else info.get('sprite')


def outlined(surface, msg, center, kind, color, edge):
    """글자 테두리 (테두리 색으로 둘레를 찍고 위에 글씨)."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (2, 2), (1, 2)):
        text(surface, msg, (center[0] + dx, center[1] + dy), kind, edge, 'center')
    return text(surface, msg, center, kind, color, 'center')


def plum_cursor():
    """메뉴 커서 = 매화 한 송이 (9×9 → ×2)."""
    s = pygame.Surface((9, 9), pygame.SRCALPHA)
    for dx, dy in ((4, 1), (1, 3), (7, 3), (2, 7), (6, 7)):
        pygame.draw.circle(s, (196, 90, 130), (dx, dy), 2)
        pygame.draw.circle(s, (255, 196, 216), (dx, dy), 1)
    s.set_at((4, 4), (250, 200, 70))
    s.set_at((3, 4), (236, 120, 150))
    return pygame.transform.scale(s, (18, 18))


# ======================================================================
class LoadingScene(Scene):
    """게임을 켜면 맨 처음: 표지 하늘 위 테크모 파닥 + 게이지 + "섬으로 가는 중...". 그림·글꼴·소리를 조금씩 미리 읽음."""
    music = 'map'
    header = False
    MIN_SECONDS = 0.8

    def __init__(self, app):
        super().__init__(app)
        self.tasks = []
        self.total = 1
        self.t = 0.0

    def enter(self):
        self.t = 0.0
        app = self.app
        catalog = app.call('get_catalog') or {}
        tasks = [lambda k=k: T.font(k) for k in ('title', 'body', 'small', 'big')]
        tasks.append(ART.preload)
        tasks += [lambda k=k: G.art().get(k, n) for k in G.TECHMO['frames'] for n in (1, 2)]
        for info in catalog.values():
            for path in (info.get('stage_sprites') or [info.get('sprite')]):
                tasks.append(lambda p=path: (app.sprites.get(p, 28), app.sprites.get(p, 56)))
        tasks.append(app.audio.preload)
        self.tasks = tasks
        self.total = max(1, len(tasks))

    def update(self, dt):
        self.t += dt
        end = time.perf_counter() + 0.012                 # 한 프레임에 12ms까지만 읽음
        while self.tasks and time.perf_counter() < end:
            try:
                self.tasks.pop(0)()
            except Exception:
                pass                                       # 하나 못 읽어도 로딩은 계속 (화면에서 대신 그림)
        if not self.tasks and self.t >= self.MIN_SECONDS:
            self.app.go('title')

    def progress(self):
        done = 1 - len(self.tasks) / self.total
        return min(done, self.t / self.MIN_SECONDS)

    def draw(self, surface):
        surface.blit(ART.layer('back'), (0, 0))
        img = G.art().get(G.art().flap(self.t), 2)
        surface.blit(img, img.get_rect(center=(T.WIDTH // 2, 150)))
        bar = pygame.Rect(0, 0, 200, 12)
        bar.center = (T.WIDTH // 2, 214)
        gauge(surface, bar, int(self.progress() * 100), 100, 'gold')
        outlined(surface, '섬으로 가는 중...', (T.WIDTH // 2, 236), 'title', T.WHITE, T.INK)


# ======================================================================
class TitleScene(Scene):
    music = 'map'            # 표지·새 게임 흐름 = 지도 낮 곡
    header = False

    def __init__(self, app):
        super().__init__(app)
        self.t = 0.0
        self.sel = 0
        self.catalog = {}
        self.parade = []
        self.cursor = plum_cursor()
        self.anim = None             # ('newgame', 시작 시각)
        self.jump = None             # (글자 번호, 시작 시각)
        self.tail_hits = 0
        self.hearts_at = None

    def enter(self):
        self.catalog = self.catalog or (self.app.call('get_catalog') or {})
        self.parade = parade_keys(self.catalog)
        self.anim = None
        self.sel = 0
        self.tail_hits = 0

    # ---------- 메뉴 ----------
    def can_continue(self):
        return bool(getattr(self.app, 'had_save', False))

    def menu_rect(self, i):
        y = META['menu_y0'] + i * META['menu_gap']
        return pygame.Rect(T.WIDTH // 2 - MENU_W // 2, y - META['menu_gap'] // 2, MENU_W, META['menu_gap'])

    def enabled(self, i):
        return MENU[i] != '이어하기' or self.can_continue()

    def activate(self, i):
        if not self.enabled(i) or self.anim:
            return
        label = MENU[i]
        if label == '새 게임':
            if self.can_continue():
                from .settings import ConfirmOverlay
                self.app.open_overlay(ConfirmOverlay(self.app, '새 게임을 시작할까?', '지금 세이브는 사라진다',
                                                     '새 게임', 'red', self.start_new))
            else:
                self.start_new()
        elif label == '이어하기':
            self.app.go('map')
        elif label == '설정':
            from .settings import SettingsOverlay
            self.app.open_overlay(SettingsOverlay(self.app, on_title=True))
        else:
            self.app.running = False

    def start_new(self):
        self.sel = 0
        self.anim = ('newgame', self.t)

    # ---------- 입력 ----------
    def handle(self, event):
        if self.anim:
            return
        if event.type == pygame.MOUSEMOTION:
            for i in range(len(MENU)):
                if self.menu_rect(i).collidepoint(event.pos) and self.enabled(i):
                    self.sel = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(MENU)):
                if self.menu_rect(i).collidepoint(event.pos):
                    self.sel = i if self.enabled(i) else self.sel
                    self.activate(i)
                    return
            hit = ART.logo_hit(event.pos)
            if hit and hit[0] == 'letter':
                self.jump = (hit[1], self.t)
            elif hit and hit[0] == 'tail':
                self.tail_hits += 1
                if self.tail_hits >= 5:                    # 꼬리 5번: 행렬 동물 전부 하트 + 점프
                    self.tail_hits = 0
                    self.hearts_at = self.t
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_DOWN):
                step = -1 if event.key == pygame.K_UP else 1
                i = self.sel
                for _ in range(len(MENU)):
                    i = (i + step) % len(MENU)
                    if self.enabled(i):
                        break
                self.sel = i
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.activate(self.sel)

    # ---------- 시간 ----------
    NEWGAME = (0.5, 0.4, 0.8)        # 글자 깜빡 → 동물 깜짝 점프 → 아이리스 (title_v5_newgame.gif)

    def phase(self):
        """새 게임 연출 단계와 그 안 진행도 (0~1). 없으면 (None, 0)."""
        if not self.anim:
            return None, 0.0
        e = self.t - self.anim[1]
        for name, d in zip(('flash', 'surprise', 'iris'), self.NEWGAME):
            if e < d:
                return name, e / d
            e -= d
        return 'done', 1.0

    def update(self, dt):
        self.t += dt
        name, _ = self.phase()
        if name == 'done':
            self.anim = None
            self.app.go('new_game')

    # ---------- 그리기 ----------
    def techmo_center(self):
        img = G.art().get('idle', 2)
        x, y = techmo_topleft(img, META['techmo_feet'])
        return x + img.get_width() // 2, y + img.get_height() * 7 // 16

    def _techmo_kind(self, phase):
        if phase in ('flash',):
            return G.art().flap(self.t)
        if phase in ('surprise', 'iris'):
            return G.art().flap(self.t, talk=True)
        k = int(self.t * 30) % 38                          # title5.actors: 가끔 깜빡, 가끔 파닥
        if k in (12, 13):
            return 'blink'
        if 24 <= k < 36:
            return G.TECHMO['flap_cycle'][(k - 24) % 6]
        return 'idle'

    def _actors(self, surface, phase, p):
        frame = self.t * 30
        gap, speed, feet = META['parade_gap'], META['parade_speed'], META['parade_y']
        items = []
        surprise = math.sin(min(1, p) * math.pi) if phase == 'surprise' else 0.0
        hearts = self.hearts_at is not None and self.t - self.hearts_at < 0.8
        for i, key in enumerate(self.parade):
            x = (i * gap + frame * speed) % (len(self.parade) * gap) - 60
            hop = -3 if ((int(frame) // 3) + i) % 2 == 0 else 0
            if surprise:
                hop = -int(14 * surprise)
            elif hearts:
                hop = -int(14 * math.sin(min(1, (self.t - self.hearts_at) / 0.8) * math.pi))
            items.append((feet, 'animal', (key, int(x), hop)))
        items.append((META['techmo_feet'][1], 'techmo', None))
        for _, kind, data in sorted(items, key=lambda v: v[0]):            # 발 y 순서 (서로 안 통과)
            if kind == 'animal':
                key, x, hop = data
                pygame.draw.ellipse(surface, (206, 180, 130), (x + 12, feet - 5, 33, 7))
                img = self.app.sprites.get(stage1_sprite(self.catalog.get(key, {})), 56)
                surface.blit(pygame.transform.flip(img, True, False), (x, feet - 56 + hop))
                if phase == 'surprise':                                     # "!" 깜짝
                    pygame.draw.rect(surface, (230, 60, 60), (x + 26, feet - 72 + hop, 5, 11))
                    pygame.draw.rect(surface, T.INK, (x + 26, feet - 72 + hop, 5, 11), 1)
                    pygame.draw.rect(surface, (230, 60, 60), (x + 26, feet - 60 + hop, 5, 4))
                    pygame.draw.rect(surface, T.INK, (x + 26, feet - 60 + hop, 5, 4), 1)
                elif hearts:
                    W.icon(surface, 'heart', (x + 22, feet - 74 + hop))
            else:
                img = G.art().get(self._techmo_kind(phase), 2)
                surface.blit(img, techmo_topleft(img, META['techmo_feet']))

    def _menu(self, surface, phase):
        y0, gap = META['menu_y0'], META['menu_gap']
        board = pygame.Rect(0, 0, MENU_W, len(MENU) * gap + 14)
        board.midtop = (T.WIDTH // 2, y0 - 14)
        hanji = pygame.Surface(board.size, pygame.SRCALPHA)
        pygame.draw.rect(hanji, HANJI, hanji.get_rect(), border_radius=6)
        pygame.draw.rect(hanji, HANJI_EDGE, hanji.get_rect(), 1, border_radius=6)
        surface.blit(hanji, board)
        for i, label in enumerate(MENU):
            y = y0 + i * gap
            on = i == self.sel
            if not self.enabled(i):
                col, edge = (170, 160, 150), (90, 80, 76)
            elif on and phase == 'flash':
                col, edge = (T.WHITE if int(self.t * 24) % 2 else (255, 150, 60)), T.INK
            else:
                col, edge = ((255, 216, 64), T.INK) if on else (T.WHITE, (70, 52, 44))
            g = outlined(surface, label, (T.WIDTH // 2, y), 'big', col, edge)
            record(label, g.inflate(2, 2), board, 'title-menu')
            if on and self.enabled(i):
                bob = round(2 * math.sin(self.t * math.pi * 8 / 3))
                surface.blit(self.cursor, (g.x - 26 + bob, y - self.cursor.get_height() // 2))
        small = (T.WHITE, T.INK)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            text(surface, '© 2026 EvoTail 팀', (8 + dx, 352 + dy), 'small', small[1], 'midleft')
            text(surface, 'v1.0', (632 + dx, 352 + dy), 'small', small[1], 'midright')
        text(surface, '© 2026 EvoTail 팀', (8, 352), 'small', small[0], 'midleft')
        text(surface, 'v1.0', (632, 352), 'small', small[0], 'midright')

    def draw(self, surface):
        phase, p = self.phase()
        ART.sky(surface, self.t)
        ART.ground(surface)
        self._actors(surface, phase, p)
        ART.petals(surface, self.t)
        ART.motes(surface, self.t)
        ART.front(surface)
        jump = None
        if self.jump and self.t - self.jump[1] < 0.35:              # 글자 통: 위로 6px 갔다가 내려옴
            jump = (self.jump[0], round(6 * math.sin((self.t - self.jump[1]) / 0.35 * math.pi)))
        ART.logo(surface, self.t, jump)
        self._menu(surface, phase)
        if phase in ('iris', 'done'):                               # 테크모 중심으로 동그랗게 닫힘
            cx, cy = self.techmo_center()
            r = int(420 * (1 - min(1, p)) ** 1.6) if phase == 'iris' else 0
            iris(surface, (cx, cy), r)


def iris(surface, center, r):
    cover = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
    cover.fill((14, 10, 20, 255))
    if r > 0:
        pygame.draw.circle(cover, (0, 0, 0, 0), center, r)
    surface.blit(cover, (0, 0))
    if r > 0:
        pygame.draw.circle(surface, (255, 214, 80), center, r, 1)
