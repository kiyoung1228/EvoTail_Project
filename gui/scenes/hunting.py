"""사냥터 (A안): 사냥터 4곳(2×2 풍경 칸) + 오른쪽 칸(보낼 동물 / 사냥 중 / 보상 받기).

목업 docs/mockups/hunt/hunt_A1_send.png, hunt_A2_ready.png, hunt_A3_running.png. 배경 assets/hunt/hunt.png.
게임 규칙은 없다: 사냥터 이름·시간·보상(item, count)은 get_hunts()['areas'], 진행 상태는 스냅샷 hunts
(animal, end, ready), 보낼 수 있는지는 스냅샷 participation / participation_reason (백엔드 _available, start_hunting과
같은 검사). 보내기·불러오기·보상 받기 = start_hunting / cancel_hunting / collect_hunt.
"다녀오면" 상태 변화와 질병 확률은 API에 없어 GUI 표시값(HUNT_DISPLAY)으로 둔다 (CLAUDE.md).
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
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, chip_width, icon,
                       gauge, select_frame, nine, record, wrap2, wrap_lines, Button, BUTTON_H)
from .hatch import rays
from .settings import ConfirmOverlay
from .farm import mmss

# 백엔드 service._finish_animal_job · config.DISEASE_CHANCE와 같은 값 (API에 없어 GUI 표시값. 백엔드를 바꾸면 같이 바꿀 것)
HUNT_DISPLAY = {
    'after': {1800: {'fullness': -10, 'mood': -5, 'fatigue': 20},
              3600: {'fullness': -20, 'mood': -10, 'fatigue': 35}},
    'disease': 0.30,
}
HUNT_DIR = os.path.join(T.ROOT, 'assets', 'hunt')
with open(os.path.join(HUNT_DIR, 'spots.json'), encoding='utf-8') as _f:
    SPOTS = json.load(_f)
ZONE = (10, 60, 212, 144, 4, 6)          # 첫 칸 x, y, 칸 폭, 칸 높이, 가로 사이, 세로 사이 (2×2)
PANEL = pygame.Rect(444, 58, 188, 298)
ART = pygame.Rect(PANEL.x + 12, 96, PANEL.w - 24, 80)
STAGE = pygame.Rect(PANEL.x + 13, 92, 162, 84)           # 오른쪽 칸 무대 (사냥 중·완료)
# 무대 = 풍경 그림(208×140)에서 자를 자리: 가로 시작 x, 아래 울타리 위 18px (tools/hunt_mock.py stage_box()와 같음)
# 상자 왼쪽·오른쪽 끝에 잘리는 소품이 없게 고른 값 (최대 208 - 162 = 46): 달토끼 절구(x 22~44)는 상자 밖, 닭장(6~90)·여물통(8~58)은
# 통째로 안, 목장은 건초(14~)와 풍차 기둥(~175)이 딱 들어가게
STAGE_CROP_X = {'rabbit_hill': 46, 'chicken_coop': 5, 'pig_pen': 4, 'ranch': 14}
# 세로 시작 y (높이는 상자 그대로 84): 4곳 모두 상자 아래가 울타리 위(y 104 이하)에서 끝나고 위쪽 소품(지붕·사과·쉼터·풍차)이 안 잘리게
STAGE_CROP_Y = {'chicken_coop': 12, 'pig_pen': 20, 'ranch': 8, 'rabbit_hill': 8}
ROW_H, ROW_STEP, ROWS = 32, 33, 3
LIST_Y = 198
ACTIVITY_LABEL = {'training': '훈련 중'}


class HuntScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.selected = None          # 고른 사냥터 (area)
        self.send_key = None          # 보낼 동물
        self.scroll = 0
        self.areas = {}
        self.catalog = {}
        self.icons = I.ItemIcons()
        self._img = {}
        self.buttons = []
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.areas = (self.app.call('get_hunts') or {}).get('areas', self.areas)
        self.catalog = self.app.call('get_shop_catalog') or self.catalog
        if self.selected not in self.areas:
            self.selected = next(iter(self.areas), None)
        self.scroll = 0
        self._fix_send()

    # ---------- 그림 ----------
    def image(self, kind, area, n=1, flip=False):
        """zones/<area>.png(2배 → ½), animals/<area>.png(4배 → 원본 → ×n)."""
        key = (kind, area, n, flip)
        if key not in self._img:
            img = pygame.image.load(os.path.join(HUNT_DIR, kind, f'{area}.png')).convert_alpha()
            w, h = img.get_size()
            d = 2 if kind == 'zones' else 4
            img = pygame.transform.scale(img, (w // d * n, h // d * n))
            if flip:
                img = pygame.transform.flip(img, True, False)
            self._img[key] = img
        return self._img[key]

    # ---------- 백엔드 값 ----------
    def job(self, area):
        return (self.app.state.get('hunts') or {}).get(area)

    def remaining(self, job):
        if not job or job.get('ready'):
            return 0
        return max(0.0, job['end'] - self.app.now()) if job.get('end') is not None else job.get('remaining_seconds', 0)

    def label(self, item):
        return I.item_label(item, self.catalog)

    def animals(self):
        return self.app.state.get('animals', [])

    def send_reason(self, a):
        """보낼 수 없는 이유 (없으면 None). 사냥 중이면 어디인지."""
        act = a.get('activity') or {}
        if act.get('kind') == 'hunt':
            return f"사냥 중 · {self.areas.get(act.get('area'), {}).get('label', '')}"
        if act.get('kind') in ACTIVITY_LABEL:
            return ACTIVITY_LABEL[act['kind']]
        if not a.get('participation'):
            return a.get('participation_reason') or '보낼 수 없음'
        return None

    def _fix_send(self):
        ok = [a['id'] for a in self.animals() if not self.send_reason(a)]
        if self.send_key not in ok:
            self.send_key = ok[0] if ok else None

    @staticmethod
    def zone_rect(i):
        x, y, w, h, gx, gy = ZONE
        return pygame.Rect(x + (i % 2) * (w + gx), y + (i // 2) * (h + gy), w, h)

    def row_rect(self, i):
        return pygame.Rect(PANEL.x + 12, LIST_Y + getattr(self, 'list_shift', 0) + i * ROW_STEP, PANEL.w - 24, ROW_H)

    # ---------- 명령 ----------
    def send(self):
        a = self.app.animal(self.send_key)
        if a and self.app.act('start_hunting', f"{T.josa(a['name'], '을')} 보냈다", icon='meat',
                              key=a['id'], area=self.selected) is not None:
            self._fix_send()

    def ask_recall(self):
        area = self.selected
        job = self.job(area)
        name = self.app.name_of(job['animal']) if job else ''
        self.app.open_overlay(ConfirmOverlay(
            self.app, '불러올까?', f"지금 {T.josa(name, '을')} 부르면 보상 없음", '불러오기', 'brown',
            lambda: self.app.act('cancel_hunting', f"{T.josa(name, '을')} 불러왔다", icon='back', area=area)))

    def collect(self):
        self.app.act('collect_hunt', lambda d: f"{self.label(d['item'])} +{d['count']}", icon='meat',
                     area=self.selected)

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
        elif event.type == pygame.MOUSEWHEEL and PANEL.collidepoint(W.mouse_pos()):
            n = len(self.animals())
            self.scroll = max(0, min(max(0, n - ROWS), self.scroll - event.y))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, area in enumerate(self.areas):
                if self.zone_rect(i).collidepoint(event.pos):
                    self.selected = area
                    return
            if not self.job(self.selected):
                for i, a in enumerate(self.animals()[self.scroll:self.scroll + ROWS]):
                    if self.row_rect(i).collidepoint(event.pos) and not self.send_reason(a):
                        self.send_key = a['id']
                        return

    def update(self, dt):
        self._fix_send()
        self.buttons = []
        area = self.selected
        if area not in self.areas:
            return
        spec = self.areas[area]
        job = self.job(area)
        r = (PANEL.x + 12, 300, PANEL.w - 24, 40)
        meat = self.label(spec['item'])
        if not job:
            a = self.app.animal(self.send_key)
            if a:
                self.buttons.append(Button(r, f"{a['name']} 보내기", self.send, 'green', icon='heart',
                                           sub=f"{spec['duration'] // 60}분 뒤 {meat} {spec['count']}개"))
            else:
                self.buttons.append(Button(r, '보낼 동물 없음', None, 'gray', enabled=False,
                                           sub='쉬거나 치료한 뒤 보내기'))
        elif job.get('ready'):
            self.buttons.append(Button(r, '보상 받기', self.collect, 'orange', icon='heart',
                                       sub=f"{meat} {spec['count']}개"))
        else:
            self.buttons.append(Button(r, '불러오기', self.ask_recall, 'brown', icon='back', sub='보상 없음'))

    # ---------- 그리기 ----------
    def draw(self, surface):
        surface.blit(W.background('assets/hunt/hunt.png'), (0, 0))
        self.back.draw(surface)
        ribbon(surface, (78, 33, 80, 18), '사냥터', 'red')
        info = '사냥터마다 1마리씩'
        box = pygame.Rect(166, 32, fit_width(info, extra=14) + 4 + 8, 22)
        card(surface, box)
        inner = card_inner(box)
        icon(surface, 'heart', (inner.x + 4, inner.y + 3))
        text_in(surface, info, (inner.x + 18, inner.y, inner.w - 18, inner.h), 'body', tag='hunt')
        for i, area in enumerate(self.areas):
            self._draw_zone(surface, i, area)
        self._draw_panel(surface)
        for b in self.buttons:
            b.draw(surface)

    def _sign(self, surface, pos, msg):
        """나무 간판 (키트 갈색 버튼 조각 + 흰 글씨)."""
        r = pygame.Rect(pos, (Button.width_for(msg) + 4, BUTTON_H))
        nine(surface, 'button_brown_normal', r)
        face = pygame.Rect(r.x + 1, r.y + 1, r.w - 2, r.h - 4)
        text_in(surface, msg, face, 'body', T.WHITE, shadow=T.WOOD[0], tag='hunt')
        return r

    def _draw_zone(self, surface, i, area):
        z = self.zone_rect(i)
        spec = self.areas[area]
        pygame.draw.rect(surface, T.WOOD[1], z)
        pygame.draw.rect(surface, T.INK, z, 1)
        ox, oy = z.x + 2, z.y + 2                         # 풍경 그림(208×140) 왼쪽 위
        surface.blit(self.image('zones', area), (ox, oy))
        t = time.time()
        for k, (cx, cy) in enumerate(SPOTS['critters'].get(area, [])):
            sway = round(math.sin(t * 1.3 + k * 1.7 + i) * 1.5)          # 천천히 좌우 1~2px
            surface.blit(self.image('animals', area, 2, flip=k == 1), (ox + cx - 28 + sway, oy + cy - 28))
        job = self.job(area)
        if job:
            a = self.app.animal(job['animal'])
            ax, ay = SPOTS['animal']
            if a:
                surface.blit(self.app.sprites.get(a['sprite'], 56), (ox + ax, oy + ay - 28))
            cxp, cyp = SPOTS['chip']
            if job.get('ready'):
                chip(surface, (ox + cxp, oy + cyp), '사냥 완료!', 'green')
                self._meat_bubble(surface, (ox + ax + 28, oy + ay - 30), spec)
            else:
                rem = self.remaining(job)
                chip(surface, (ox + cxp, oy + cyp), f"남은 {mmss(rem)}", 'brown')
                gy = oy + 140 - SPOTS.get('gauge_from_bottom', 24)
                gauge(surface, (ox + 6, gy, 208 - 12, 8), spec['duration'] - rem, spec['duration'], 'green')
        self._sign(surface, (ox + 4, oy + 4), f"{spec['label']} · {spec['duration'] // 60}분")
        if area == self.selected:
            select_frame(surface, z.inflate(4, 4))

    def _meat_bubble(self, surface, midbottom, spec):
        """보낸 동물 머리 위 말풍선: 고기 그림 + ×3."""
        n = f"×{spec['count']}"
        box = pygame.Rect(0, 0, 4 + 16 + 2 + fit_width(n, 'title') + 4, 22)
        box.midbottom = (midbottom[0], midbottom[1] - 4)
        card(surface, box)
        inner = card_inner(box)
        surface.blit(self.icons.get(spec['item'], 1), (inner.x + 2, inner.centery - 8))
        text_in(surface, n, (inner.x + 20, inner.y, inner.w - 20, inner.h), 'title', tag='hunt')
        tail = [(box.centerx - 3, box.bottom - 1), (box.centerx + 3, box.bottom - 1), (box.centerx, box.bottom + 3)]
        pygame.draw.polygon(surface, (252, 240, 214), tail)
        pygame.draw.lines(surface, T.INK, False, [tail[0], tail[2], tail[1]])

    def _title(self, surface, name, chip_label, chip_color):
        x = PANEL.x + 12
        r = text(surface, name, (x, 66), 'big')
        chip(surface, (r.right + 4, r.centery), chip_label, chip_color, anchor='midleft')

    def _draw_panel(self, surface):
        panel(surface, PANEL)
        area = self.selected
        if area not in self.areas:
            return
        spec = self.areas[area]
        job = self.job(area)
        x, right = PANEL.x + 12, PANEL.right - 12
        meat = self.label(spec['item'])
        if not job:
            self._title(surface, spec['label'], f"{spec['duration'] // 60}분", 'brown')
            text(surface, '받는 것', (x, 90), 'small', T.TEXT_SOFT)
            surface.blit(self.icons.get(spec['item'], 2), (x, 102))
            # 고기 이름: 그림 옆 폭에 안 들어가면 두 줄 ("행운의" / "토끼고기 ×3"). 글자 크기는 그대로
            lines = wrap2(f"{meat} ×{spec['count']}", right - (x + 38), 'big')
            top = 118 - (len(lines) * 16 - 2) // 2
            for k, line in enumerate(lines):
                self._line(surface, line, (x + 38, top + k * 16), 'big', T.TEXT, right)
            bottom = top + len(lines) * 16 - 2
            dy = max(0, bottom - 134)                     # 그림(102~134)보다 길어지면 아래 줄을 그만큼 내림
            self.list_shift = dy
            after = HUNT_DISPLAY['after'].get(spec['duration'], {})
            text(surface, '다녀오면', (x, 140 + dy), 'small', T.TEXT_SOFT)
            self._line(surface, f"포만감 {after.get('fullness', 0):+d} · 기분 {after.get('mood', 0):+d}", (x, 152 + dy),
                       'body', T.TEXT, right)
            self._line(surface, f"피로도 {after.get('fatigue', 0):+d} · 질병 {round(HUNT_DISPLAY['disease'] * 100)}%",
                       (x, 166 + dy), 'body', T.BAD, right)
            text(surface, '보낼 동물', (x, 183 + dy), 'title')
            animals = self.animals()
            for i, a in enumerate(animals[self.scroll:self.scroll + ROWS]):
                self._draw_row(surface, self.row_rect(i), a)
            if len(animals) > ROWS:
                more = f"{self.scroll + 1}-{min(len(animals), self.scroll + ROWS)} / {len(animals)} · 휠"
                text(surface, more, (right, 185 + dy), 'small', T.TEXT_SOFT, anchor='topright')
            return
        a = self.app.animal(job['animal'])
        name = a['name'] if a else self.app.name_of(job['animal'])
        if job.get('ready'):
            self._title(surface, spec['label'], '사냥 완료', 'green')
            self._draw_return(surface, area, spec, a, name, meat, x, right)
        else:
            self._title(surface, spec['label'], '사냥 중', 'brown')
            self._draw_running(surface, area, spec, job, a, name, meat, x, right)

    # ---------- 오른쪽 칸 무대 (목업 hunt_A4_running_v2 / hunt_A5_return_v2) ----------
    def stage_bg(self, area):
        """무대 배경 = 그 사냥터 풍경을 무대 크기로 자른 것. 자리는 사냥터마다 STAGE_CROP_X·STAGE_CROP_Y
        (tools/hunt_mock.py stage_box()와 같은 값)."""
        key = ('stage', area)
        if key not in self._img:
            z = self.image('zones', area)
            cx = STAGE_CROP_X.get(area, 30)
            y0 = STAGE_CROP_Y.get(area, 12)
            self._img[key] = z.subsurface((cx, y0, STAGE.w, STAGE.h)).copy()
        return self._img[key]

    def _flipped(self, path, size):
        key = ('flip', path, size)
        if key not in self._img:
            self._img[key] = pygame.transform.flip(self.app.sprites.get(path, size), True, False)
        return self._img[key]

    def _stage(self, surface, area):
        surface.blit(self.stage_bg(area), STAGE)
        pygame.draw.rect(surface, T.INK, STAGE.inflate(2, 2), 1)

    def _draw_running(self, surface, area, spec, job, a, name, meat, x, right):
        t = time.time()
        bob, bob2 = int(t * 6) % 2, int(t * 6 + 1) % 2        # 1px씩 통통
        self._stage(surface, area)
        clip = surface.get_clip()
        surface.set_clip(STAGE)
        surface.blit(self.image('animals', area, 2), (STAGE.x + 89, STAGE.y + 26 - bob2))     # 도망가는 사냥감
        for i in range(3):                                                                 # 흰 속도선 3줄
            yy = STAGE.y + 40 + i * 5
            pygame.draw.line(surface, T.WHITE, (STAGE.x + 85 - i * 3, yy), (STAGE.x + 79 - i * 3, yy))
        if a:                                                                              # 쫓아가는 내 동물 (오른쪽 보게)
            surface.blit(self._flipped(a['sprite'], 56), (STAGE.x + 19, STAGE.y + 26 - bob))
        phase = (t * 3) % 1                                                                # 흙먼지: 뒤로 흩어짐
        for dx, dy, r in ((0, 0, 3), (-6, 2, 2), (-11, 1, 1)):
            px, py = STAGE.x + 25 + dx - int(phase * 4), STAGE.y + 78 + dy
            pygame.draw.circle(surface, (250, 244, 230), (px, py), r)
            pygame.draw.circle(surface, (200, 186, 160), (px, py), r, 1)
        surface.set_clip(clip)
        bubble = pygame.Rect(STAGE.x + 41, STAGE.y + 6, 22, 20)                            # "!" 말풍선
        card(surface, bubble)
        text_in(surface, '!', card_inner(bubble), 'title', T.BAD, tag='hunt')
        # 이름 + 진행 길 (출발 깃발 → 발자국 → 동물 얼굴 → 고기)
        y = 192 + self._text_lines(surface, f"{name} 사냥 중", x, 192, 'title', T.TEXT, right, 13)
        dur = spec['duration']
        rem = self.remaining(job)
        py_, x0, x1 = y + 22, x + 6, right - 20
        pygame.draw.line(surface, T.WOOD[1], (x0, py_), (x1, py_), 3)
        p = max(0.0, min(1.0, 1 - rem / dur)) if dur else 1.0
        px = int(x0 + (x1 - x0) * p)
        for fx in range(x0 + 6, px - 8, 9):                                                # 지나온 자리 발자국
            surface.set_at((fx, py_ - 4), T.WOOD[0])
            surface.set_at((fx + 2, py_ - 5), T.WOOD[0])
        pygame.draw.rect(surface, T.INK, (x0 - 3, py_ - 10, 2, 12))                         # 출발 깃발
        pygame.draw.polygon(surface, T.shade('green', 2), [(x0 - 2, py_ - 10), (x0 + 5, py_ - 8), (x0 - 2, py_ - 6)])
        surface.blit(self.icons.get(spec['item'], 1), (x1 - 2, py_ - 14))                  # 도착 = 고기
        if a:
            face = self._flipped(a['sprite'], 28).subsurface((2, 2, 24, 24))
            surface.blit(face, (px - 12, py_ - 22))
        y = py_ + 22
        text(surface, '남은 시간', (x, y), 'small', T.TEXT_SOFT, anchor='midleft')
        text(surface, mmss(rem), (right, y), 'big', anchor='midright')
        surface.blit(self.icons.get(spec['item'], 1), (x, y + 16))
        y += 24 + self._text_lines(surface, f"다녀오면 {meat} ×{spec['count']}", x + 20, y + 24, 'small', T.TEXT,
                                   right, 12)
        after = HUNT_DISPLAY['after'].get(dur, {})
        self._text_lines(surface, f"다녀오면 피로도 {after.get('fatigue', 0):+d} · 질병 "
                                  f"{round(HUNT_DISPLAY['disease'] * 100)}%", x, y + 20, 'small', T.BAD, right, 12)

    def _draw_return(self, surface, area, spec, a, name, meat, x, right):
        t = time.time()
        self._stage(surface, area)
        rays(surface, STAGE, (STAGE.x + 81, STAGE.y + 58), t * 0.3, (255, 240, 170), 70, n=12, width=0.76)
        for dx, dy in ((0, 0), (14, -6), (28, 0)):                                        # 바구니 속 고기 3개
            surface.blit(self.icons.get(spec['item'], 2), (STAGE.x + 75 + dx, STAGE.y + 36 + dy))
        basket = pygame.Rect(STAGE.x + 77, STAGE.y + 60, 58, 18)
        pygame.draw.rect(surface, (206, 152, 88), basket)
        for xx in range(basket.x + 6, basket.right - 2, 6):
            pygame.draw.line(surface, (170, 116, 60), (xx, basket.y + 1), (xx, basket.bottom - 2))
        pygame.draw.line(surface, (232, 186, 120), (basket.x + 1, basket.y + 4), (basket.right - 2, basket.y + 4))
        pygame.draw.rect(surface, T.INK, basket, 1)
        if a:
            surface.blit(self.app.sprites.get(a['sprite'], 56), (STAGE.x + 17, STAGE.y + 26))
        for k, (sx, sy) in enumerate(((13, 20), (71, 12), (147, 18), (143, 48))):         # 반짝이 깜빡임
            if int(t * 2 + k) % 3:
                sx, sy = STAGE.x + sx, STAGE.y + sy
                pygame.draw.line(surface, (255, 236, 120), (sx - 3, sy), (sx + 3, sy))
                pygame.draw.line(surface, (255, 236, 120), (sx, sy - 3), (sx, sy + 3))
                surface.set_at((sx, sy), T.WHITE)
        ribbon(surface, (STAGE.x + 17, STAGE.y - 6, 64, 18), '귀환!', 'green')
        y = 192 + self._text_lines(surface, f"{name} 귀환", x, 192, 'title', T.TEXT, right, 13)
        # "행운의 토끼고기 ×3" (왼쪽) + 초록 "가방 1 → 4" (오른쪽). 한 줄에 안 들어가면 두 줄
        have = self.have(spec['item'])
        left, bag = f"{meat} ×{spec['count']}", f"가방 {have} → {have + spec['count']}"
        y += 16
        if glyph_box(left, 'small').w + 8 + glyph_box(bag, 'small').w <= right - x:
            self._text_lines(surface, left, x, y, 'small', T.TEXT, right, 12)
        else:
            y += self._text_lines(surface, left, x, y, 'small', T.TEXT, right, 12) + 12
        g = text(surface, bag, (right, y), 'small', T.OK, anchor='midright')
        record(bag, g, pygame.Rect(x - 2, g.y - 2, right - x + 4, g.h + 4), 'hunt-panel')
        # 다녀온 결과 칩 (HUNT_DISPLAY) + 지금 상태 칩. 칩이 칸 폭을 넘으면 다음 줄로
        y += 18
        text(surface, '다녀온 결과', (x, y), 'small', T.TEXT_SOFT, anchor='midleft')
        after = HUNT_DISPLAY['after'].get(spec['duration'], {})
        sick = bool(a and a.get('sick'))
        rows = [[(f"피로도 {after.get('fatigue', 0):+d}", 'orange'), (f"포만감 {after.get('fullness', 0):+d}", 'orange')],
                [(f"기분 {after.get('mood', 0):+d}", 'orange'),
                 ('아픔 · 병원 치료', 'red') if sick else ('건강함', 'green')]]
        cy = y + 8
        for row in rows:
            cx = x
            for label, color in row:
                if cx > x and cx + chip_width(label) > right:
                    cx, cy = x, cy + 20
                r = chip(surface, (cx, cy), label, color)
                cx = r.right + 3
            cy += 20
        if a:
            lv = T.level(a, 'fatigue')
            text(surface, f"지금 피로도 {a['fatigue']} {lv}", (x, cy + 12), 'small', T.TEXT_SOFT, anchor='midleft')

    def _text_lines(self, surface, msg, x, y_mid, kind, color, right, step):
        """글씨를 칸 폭(right까지)에 맞게 띄어쓰기 단위로 줄을 나눠 그림 (첫 줄 가운데 = y_mid, 글자 크기 그대로).
        늘어난 높이(step × (줄 수 - 1))를 돌려줌 → 아래 줄들을 그만큼 내림. 줄마다 넘침 점검 기록."""
        lines = wrap_lines(msg, right - x, kind) or ['']
        for k, line in enumerate(lines):
            g = text(surface, line, (x, y_mid + k * step), kind, color, anchor='midleft')
            record(line, g, pygame.Rect(x - 2, g.y - 2, right - x + 4, g.h + 4), 'hunt-panel')
        return step * (len(lines) - 1)

    def _line(self, surface, msg, pos, kind, color, right):
        """오른쪽 칸 안 글씨 한 줄 + 넘침 점검 기록 (칸 오른쪽 끝 right를 넘으면 check_text_fit 위반)."""
        g = text(surface, msg, pos, kind, color)
        record(msg, g, pygame.Rect(pos[0] - 2, g.y - 2, right - pos[0] + 4, g.h + 4), 'hunt-panel')
        return g

    def have(self, item):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(item, 0)

    def _draw_row(self, surface, r, a):
        reason = self.send_reason(a)
        card(surface, r, selected=a['id'] == self.send_key and not reason)
        img = self.app.sprites.get(a['sprite'], 28)
        if reason:
            img = img.copy()
            img.fill((150, 150, 150, 140), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(img, (r.x + 2, r.y + 2))
        inner = card_inner(r)
        tx = r.x + 32
        text_in(surface, a['name'], (tx, inner.y, inner.right - tx, 15), 'title', T.TEXT_SOFT if reason else T.TEXT,
                align='left', tag='hunt')
        text_in(surface, reason or '보낼 수 있음', (tx, inner.y + 14, inner.right - tx, 13), 'small',
                T.TEXT_SOFT if reason else T.OK, align='left', tag='hunt')
