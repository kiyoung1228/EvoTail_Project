"""마이룸: 업적 트로피 진열장 · 기록 칠판 · 일기장 · 방에서 지내는 동물 (목업 docs/mockups/my_room/room_C*.png).

게임 규칙은 없다 (백엔드에 이미 있는 명령만 읽음):
  업적 = get_achievement_details → [{id, label, achieved}] (순서 그대로), 기록 = get_statistics (counters),
  일기 = get_event_history (최근 일부터, 문장은 App.event_line = 알림과 같은 EVENT_TEXT·EVENT_ICON)
그림: assets/my_room/room_day·night.png (논리의 2배 → ½, 위 26px 투명), trophies/<id>.png·<id>_locked.png (원본 16의 4배 → ½ = 32).
자리 숫자는 전부 assets/my_room/room.json. 다시 만들기: python tools/room_assets.py, 목업 python tools/room_mock.py docs/mockups/my_room
"""
import json
import math
import os
import random
import time
import pygame

from .. import theme as T
from .. import widgets as W
from ..app import Scene
from ..widgets import text, text_in, card, ribbon, select_frame, tooltip, record, fit_width, Kit, Button, BUTTON_H
from .map_scene import NIGHT_TINT

ROOM_DIR = os.path.join(T.ROOT, 'assets', 'my_room')
with open(os.path.join(ROOM_DIR, 'room.json'), encoding='utf-8') as _f:
    ROOM = json.load(_f)

# 트로피 얻는 법 (GUI 표시 문구 표, 백엔드에 없음). 표에 없는 업적 id는 말풍선 3줄째 없이
HOWTO = {
    'first_win': '전투에서 한 번 이기기', 'first_training': '훈련을 한 번 끝내기',
    'first_hunt': '사냥터에서 한 번 돌아오기', 'first_crop': '밭에서 한 번 수확하기',
    'first_cooking': '요리를 한 번 성공하기', 'cooking_master': '요리 레벨 5 달성',
    'pokedex_10': '동물 10종 모으기', 'pokedex_complete': '동물 30종 모두 모으기',
    'first_evolution': '동물 한 마리 진화시키기', 'fully_evolved': '최종 단계까지 진화시키기',
    'max_stats': '네 능력치를 모두 MAX로', 'champion': '다이아몬드 대회 우승',
    'rank_bronze': '브론즈 대회 우승', 'rank_silver': '실버 대회 우승',
    'rank_gold': '골드 대회 우승', 'rank_diamond': '다이아몬드 대회 우승',
}
# 칠판 6칸 (cells 순서대로): (counters 키, 이름, 키트 아이콘)
STATS = (('battles_won', '전투 승리', 'sword'), ('trainings_completed', '훈련 완료', 'heart'),
         ('hunts_completed', '사냥 다녀옴', 'meat'), ('crops_harvested', '작물 수확', 'snack'),
         ('cooks_succeeded', '요리 성공', 'home'), ('items_purchased', '물건 구매', 'coin'))
DIARY_LIMIT = 40            # 일기장: 최근 일을 이만큼 읽어서 EVENT_TEXT에 있는 것만 6줄
WALK_SPEED = 10             # 깔개 안에서 돌아다니는 속도 (px/초)


class MyRoomScene(Scene):
    music = 'map'

    def __init__(self, app):
        super().__init__(app)
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')
        self.achievements = []
        self.stats = {}
        self.diary = []
        self.hover = None
        self.walkers = {}           # 동물 id → {'pos': [x, 발 y], 'goal': [x, y], 'wait': 초}
        self.t = 0.0
        self._loaded_at = None
        self._img = {}

    # ---------- 백엔드 값 ----------
    def enter(self):
        self.walkers = {}
        self.hover = None
        self._load()

    def _load(self):
        app = self.app
        self.achievements = app.call('get_achievement_details') or []
        self.stats = app.call('get_statistics') or {}
        self.diary = app.call('get_event_history', limit=DIARY_LIMIT) or []
        self._loaded_at = getattr(app, '_refreshed_at', None)

    def night(self):
        return bool(self.app.state.get('clock', {}).get('night'))

    def roomies(self):
        """방에 있는 동물 = 지도 마당과 같은 규칙으로 고른 동물 (MapScene._layout 재사용)."""
        return self.app.scenes['map']._layout()[0]

    def resting_key(self, animals):
        """방석에 엎드릴 한 마리 = 자율행동 rest인 동물 중 첫째."""
        return next((a['id'] for a in animals if self.app.auto.get(a['id'], {}).get('action') == 'rest'), None)

    # ---------- 그림 ----------
    def trophy(self, code, achieved):
        key = (code, achieved)
        if key not in self._img:
            path = os.path.join(ROOM_DIR, 'trophies', f"{code}{'' if achieved else '_locked'}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self._img[key] = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
            else:                                               # 그림 없는 업적: 키트 아이콘으로 대신
                size = ROOM['shelf']['trophy_size']
                s = pygame.Surface((size, size), pygame.SRCALPHA)
                ic = Kit.icon('check' if achieved else 'lock')
                s.blit(ic, ic.get_rect(center=(size // 2, size // 2)))
                self._img[key] = s
        return self._img[key]

    def slot_rect(self, slot):
        n = ROOM['shelf']['trophy_size']
        return pygame.Rect(slot['x'], slot['y'], n, n)

    # ---------- 동물 ----------
    def _rug_point(self, rng):
        cx, cy = ROOM['rug']['center']
        rx, ry = ROOM['rug']['rx'] - 26, ROOM['rug']['ry'] - 8      # 깔개 안쪽 (그림 폭 반 + 여백)
        a, r = rng.uniform(0, math.tau), math.sqrt(rng.random())
        return [cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)]

    def _update_walkers(self, dt, animals, rest):
        keep = {a['id'] for a in animals}
        for k in list(self.walkers):
            if k not in keep:
                del self.walkers[k]
        cx, cy = ROOM['rug']['center']
        span = ROOM['rug']['rx'] - 26
        for i, a in enumerate(animals):
            w = self.walkers.get(a['id'])
            if w is None:                                  # 처음 자리: 깔개 가로로 고르게 (앞뒤 지그재그)
                rng = random.Random(a['id'])
                n = len(animals)
                p = [cx - span + 2 * span * (i + 1) / (n + 1), cy + (6 if i % 2 else -6)]
                w = self.walkers[a['id']] = {'pos': p, 'goal': list(p), 'wait': rng.uniform(0, 2), 'rng': rng}
            if a['id'] == rest or self.night():
                continue                                        # 엎드린 동물은 안 돌아다님
            if w['wait'] > 0:
                w['wait'] -= dt
                continue
            dx, dy = w['goal'][0] - w['pos'][0], w['goal'][1] - w['pos'][1]
            d = math.hypot(dx, dy)
            if d < 1:
                w['goal'] = self._rug_point(w['rng'])
                w['wait'] = w['rng'].uniform(1, 4)
                continue
            step = min(d, WALK_SPEED * dt)
            w['pos'][0] += dx / d * step
            w['pos'][1] += dy / d * step

    def animal_rect(self, a, rest):
        """동물 그림 영역 (클릭·겹침용). 방석 위 = cushion, 나머지 = 깔개 위 발 자리."""
        img = self.app.sprites.get(a.get('sprite'), 56)
        art = img.get_bounding_rect()
        if a['id'] == rest:
            fx, fy = ROOM['cushion']['center']
        else:
            fx, fy = self.walkers.get(a['id'], {}).get('pos', ROOM['rug']['center'])
        return pygame.Rect(round(fx) - art.w // 2, round(fy) - art.h, art.w, art.h)

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            animals = self.roomies()
            rest = self.resting_key(animals)
            for a in sorted(animals, key=lambda a: -self.animal_rect(a, rest).bottom):   # 앞에 있는 동물부터
                if self.animal_rect(a, rest).collidepoint(event.pos):
                    self.app.go('animals', selected=a['id'])
                    return
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')

    def update(self, dt):
        self.t += dt
        if getattr(self.app, '_refreshed_at', None) != self._loaded_at:   # 상태를 다시 읽었으면 업적·기록·일기도
            self._load()
        animals = self.roomies()
        self._update_walkers(dt, animals, self.resting_key(animals))
        pos = W.mouse_pos()
        slots = ROOM['shelf']['slots']
        self.hover = next((s['id'] for s in slots if self.slot_rect(s).collidepoint(pos)), None)

    # ---------- 그리기 ----------
    def draw(self, surface):
        night = self.night()
        surface.blit(W.background(f"assets/my_room/room_{'night' if night else 'day'}.png"), (0, 0))
        self._draw_shelf(surface)
        self._draw_board(surface)
        self._draw_diary(surface)
        self._draw_animals(surface, night)
        self.back.draw(surface)
        ribbon(surface, (self.back.rect.right + 10, 33, max(92, fit_width('마이룸', 'title', shadow=True) + 30), 18),
               '마이룸', 'red')
        self._draw_tip(surface)

    def _achieved(self):
        return {a['id']: a for a in self.achievements}

    def _draw_shelf(self, surface):
        sh = ROOM['shelf']
        done = self._achieved()
        shadow = sh['shadow']
        k = 0
        for slot in sh['slots']:
            r = self.slot_rect(slot)
            ok = bool(done.get(slot['id'], {}).get('achieved'))
            if ok:                                             # 달성한 트로피만 발밑 그림자 + 몇 개에 반짝이
                pygame.draw.ellipse(surface, shadow['color'], (r.x + shadow['dx0'], r.y + shadow['dy0'],
                                                               shadow['dx1'] - shadow['dx0'], shadow['dy1'] - shadow['dy0']))
            surface.blit(self.trophy(slot['id'], ok), r)
            if ok:
                k += 1
                if k % 3 == 1 and int(self.t * 1.5 + k) % 3 == 0:
                    x, y = r.right - 2, r.y + 3
                    for dx, dy in ((0, -2), (0, 2), (-2, 0), (2, 0)):
                        surface.set_at((x + dx, y + dy), (255, 250, 210))
                    surface.set_at((x, y), T.WHITE)
            if slot['id'] == self.hover:
                select_frame(surface, r.inflate(6, 6))
        got = sum(1 for a in self.achievements if a.get('achieved'))
        plate = pygame.Rect(ROOM['plate']['rect'])
        card(surface, plate)
        text_in(surface, ROOM['plate']['text'].format(got=got, total=len(self.achievements)), plate, 'body',
                tag='my-room-plate')

    def _draw_tip(self, surface):
        if not self.hover:
            return
        a = self._achieved().get(self.hover)
        if not a:
            return
        slot = next(s for s in ROOM['shelf']['slots'] if s['id'] == self.hover)
        ok = bool(a.get('achieved'))
        lines = [(a.get('label', self.hover), T.TEXT), ('달성!' if ok else '아직', T.OK if ok else T.TEXT_SOFT)]
        if self.hover in HOWTO:
            lines.append((HOWTO[self.hover], T.TEXT_SOFT))
        tooltip(surface, lines, self.slot_rect(slot), 'right', bounds=(0, 0, T.WIDTH, T.HEIGHT))

    def _draw_board(self, surface):
        b = ROOM['board']
        text(surface, b['title'], tuple(b['title_center']), 'title', tuple(b['title_color']), 'center')
        for (key, label, ic), cell in zip(STATS, b['cells']):
            surface.blit(Kit.icon(ic), tuple(cell['icon']))
            g = text(surface, label, tuple(cell['label_left']), 'small', tuple(b['text_color']), 'midleft')
            value = str(self.stats.get(key, 0))
            v = text(surface, value, tuple(cell['value_right']), 'title', tuple(b['value_color']), 'midright')
            # 숫자 칸 = 이름 끝 ~ 숫자 오른쪽 끝 + 2: 이름과 2px 미만으로 붙거나 겹치면 위반 (9999까지)
            record(value, v, pygame.Rect(g.right, v.y - 2, cell['value_right'][0] + 2 - g.right, v.h + 4),
                   'my-room-board')

    def diary_lines(self):
        """일기장 줄: 최근 일부터, EVENT_TEXT에 있는 것만, text_max_w를 넘는 줄은 빼고 다음 일. 최대 6줄."""
        d = ROOM['diary']
        out = []
        for e in self.diary:
            line = self.app.event_line(e)
            if not line:
                continue
            if W.glyph_box(line[0], 'small').w > d['text_max_w']:
                continue
            out.append(line)
            if len(out) >= len(d['lines']):
                break
        return out

    def _draw_diary(self, surface):
        d = ROOM['diary']
        tx, ty = d['title_left']
        text(surface, d['title'], (tx, ty), 'title', tuple(d['title_color']), 'midleft', shadow=tuple(d['title_shadow']))
        text(surface, d['sub'], tuple(d['sub_right']), 'small', tuple(d['sub_color']), 'midright')
        lines = self.diary_lines()
        if not lines:
            first = d['lines'][0]
            text(surface, '아직 기록이 없다', tuple(first['text_left']), 'small', T.TEXT_SOFT, 'midleft')
            return
        for (msg, ic), row in zip(lines, d['lines']):
            if ic:
                surface.blit(Kit.icon(ic), tuple(row['icon']))
            g = text(surface, msg, tuple(row['text_left']), 'small', T.TEXT, 'midleft')
            x0 = row['text_left'][0]
            record(msg, g, pygame.Rect(x0 - 2, g.y - 2, d['text_max_w'] + 4, g.h + 4), 'my-room-diary')

    def _bubble(self, surface, msg, midbottom):
        w = fit_width(msg, 'small') + 4
        box = pygame.Rect(0, 0, w, 16)
        box.midbottom = midbottom
        card(surface, box)
        text_in(surface, msg, box, 'small', T.TEXT, tag='my-room-bubble')

    def _draw_animals(self, surface, night):
        animals = self.roomies()
        rest = self.resting_key(animals)
        order = sorted(animals, key=lambda a: self.animal_rect(a, rest).bottom)      # 발 y 순서
        for a in order:
            r = self.animal_rect(a, rest)
            lying = a['id'] == rest or night
            img = self.app.sprites.lying(a.get('sprite'), 56) if lying else self.app.sprites.get(a.get('sprite'), 56)
            if night:
                img = img.copy()
                img.fill(NIGHT_TINT, special_flags=pygame.BLEND_RGBA_MULT)
            art = img.get_bounding_rect()
            foot = (r.centerx, r.bottom)
            sh = pygame.Surface((40, 8), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (60, 30, 20, 70), (2, 1, 36, 6))
            surface.blit(sh, (foot[0] - 20, foot[1] - 4))
            surface.blit(img, (foot[0] - art.centerx, foot[1] - art.bottom))
            top = foot[1] - art.h - 4
            action = self.app.auto.get(a['id'], {}).get('action')
            if lying:
                self._bubble(surface, 'zZ', (foot[0], top))
            elif action == 'play' and int(self.t / 2 + len(a['id'])) % 3 == 0:     # 신난 동물은 가끔 ♪
                self._bubble(surface, '♪', (foot[0], top))
