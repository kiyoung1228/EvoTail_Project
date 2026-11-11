"""메인 화면: 떠 있는 섬 마을 (목업 docs/mockups/main_day.png, main_night.png, 키트 docs/UI_KIT.md).

- 배경: assets/map/map_day.png / map_night.png (백엔드 clock.night에 따라). 640×360 논리 화면에 ½로
- 건물 클릭 영역·문·마당: assets/map/map.json (1280×720 기준 좌표 → ½로 읽음)
- 간판: 키트 card 조각 + 굵은 글씨, 문 아래. 마우스를 올리면 card_selected + 건물 노란 테두리 + 설명 말풍선
- 오른쪽 메뉴 5개: 키트 panel 안에 card 버튼 + assets/ui/icon_*.png
- 마당 동물: 스냅샷 yard(플레이어가 고른 동물) + 빈자리 자동 채우기, 최대 yard_max마리.
  활동 중인 동물은 그 장소 앞에 작게 (사냥터 / 집 / 병원)
게임 규칙은 없다. 동물 상태·자율행동은 app.state, app.auto(백엔드 값)를 그대로 읽는다.
"""
import json
import math
import os
import random
import pygame

from .. import theme as T
from ..app import Scene
from ..widgets import text, text_width, panel, card, tooltip, select_frame, Kit

MAP_DIR = os.path.join(T.ROOT, 'assets', 'map')
UI_DIR = os.path.join(T.ROOT, 'assets', 'ui')

# map.json 키 → (간판, 설명 말풍선, 이동할 화면)
PLACES = {
    'home': ('집', '요리 · 휴식', 'home'),
    'shop': ('상점', '먹이 · 장난감 · 장비 · 알', 'shop'),
    'hospital': ('병원', '질병 치료 · 회복 포션', 'hospital'),
    'farm': ('밭', '작물 심기 · 수확', 'farm'),
    'battle': ('전투장', '스테이지 · 대회', 'battle'),
    'hunting': ('사냥터', '고기 재료 자동 사냥', 'hunting'),
}

# 오른쪽 메뉴: (아이콘 키, 라벨, 이동할 화면)
MENU = [
    ('my_animals', '내 동물', 'animals'),
    ('pokedex', '도감', 'pokedex'),
    ('bag', '가방', 'bag'),
    ('my_room', '마이룸', 'my_room'),
    ('settings', '설정', 'settings'),
]
MENU_PANEL = pygame.Rect(589, 40, 46, 270)
MENU_BTN = 36          # 버튼 한 변
MENU_STEP = 51         # 버튼 간격

YARD_SIZE = 56         # 마당 동물: 원본 28px 도트 × 2 (지도와 같은 배율)
PLACE_SIZE = 28        # 장소 앞에 작게: 원본 그대로
FEET = 4               # 스프라이트 상자 바닥과 발 사이 여백 (투명 영역)

BUBBLE_EDGE = T.INK
MIN_GAP = 26           # 마당 동물 발 사이 최소 거리 (논리 px). 그림 폭 ≈ 32라 말풍선이 안 겹침

# 마우스를 올렸을 때 글씨 말풍선 (밤에는 문구만 바꾼다. 표시 문구, 규칙 아님)
NIGHT_LABEL = {'rest': '잠자는 중 zZ', 'idle': '꾸벅꾸벅…', 'play': '밤 산책', 'eat': '야식 찾는 중'}
DAY_LABEL = {'rest': '휴식 중 z'}

# 활동 → 그 활동을 보여줄 장소
ACTIVITY_PLACE = {'hunting': 'hunting', 'training': 'home'}


def _load_map():
    """map.json은 1280×720 기준 → 논리 화면(½) 좌표로."""
    with open(os.path.join(MAP_DIR, 'map.json'), encoding='utf-8') as f:
        data = json.load(f)
    s = T.SCALE

    def rect(v):
        return pygame.Rect(v[0] // s, v[1] // s, (v[2] - v[0]) // s, (v[3] - v[1]) // s)
    places = {k: {'rect': rect(v['rect']), 'door': (v['door'][0] // s, v['door'][1] // s)}
              for k, v in data['places'].items()}
    return places, rect(data['yard'])


class MapScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.places, self.yard = _load_map()
        self.icons = {}
        for key, _, _ in MENU:      # 48×48(2배 도트) → 논리 24×24
            path = os.path.join(UI_DIR, f'icon_{key}.png')
            self.icons[key] = (pygame.transform.scale(pygame.image.load(path).convert_alpha(), (24, 24))
                               if os.path.exists(path) else None)
        self.signs = {key: self._sign_rect(key) for key in self.places}
        self.walkers = {}      # 동물 id → 마당 안 위치·목표 (화면 연출용)
        self.hover = None      # ('place', key) / ('menu', key) / ('animal', key) / ('more', None)

    # ---------- 배치 ----------
    def _sign_rect(self, key):
        w = text_width(PLACES[key][0], 'title') + 14
        dx, dy = self.places[key]['door']
        return pygame.Rect(dx - w // 2, dy + 4, w, 18)

    def menu_rect(self, key):
        i = [m[0] for m in MENU].index(key)
        return pygame.Rect(MENU_PANEL.centerx - MENU_BTN // 2, MENU_PANEL.y + 7 + i * MENU_STEP, MENU_BTN, MENU_BTN + 8)

    def _layout(self):
        """누가 마당에, 누가 장소 앞에 보이는지. 반환: (마당 목록, {장소: [동물]}, 안 보이는 수).

        1. 스냅샷 ``yard`` (플레이어가 "마당에 내보내기"로 고른 동물, 그 순서대로)
        2. ``yard_max``보다 적으면 빈자리는 화면에서만 채움 (세이브에는 안 씀):
           전투 팀 → 돌봐야 하는 동물(배고픔·기분 나쁨) → 최근에 얻은 동물
        활동 중인 동물(훈련·사냥)과 아픈 동물은 마당 대신 그 장소 앞에 작게 보인다.
        """
        state = self.app.state
        animals = state.get('animals', [])
        by_id = {a['id']: a for a in animals}
        yard_max = state.get('yard_max') or 0
        at_place = {}
        free = []
        for a in animals:
            act = (a.get('activity') or {}).get('kind')
            where = 'hospital' if a.get('sick') else ACTIVITY_PLACE.get(act)
            if where:
                at_place.setdefault(where, []).append(a)
            else:
                free.append(a['id'])
        free_set = set(free)
        chosen = [k for k in state.get('yard', []) if k in free_set]
        team = [f['id'] for f in (state.get('battle') or {}).get('player', [])]

        def needs_care(key):
            a = by_id[key]
            return T.level(a, 'fullness') == '나쁨' or T.level(a, 'mood') == '나쁨'
        recent = list(reversed(free))                       # 목록 뒤쪽이 최근에 얻은 동물
        fill = team + [k for k in recent if needs_care(k)] + recent
        shown = list(chosen)
        for key in fill:
            if len(shown) >= yard_max:
                break
            if key in free_set and key not in shown:
                shown.append(key)
        yard = [by_id[k] for k in shown[:yard_max]]
        hidden = len(free) - len(yard)
        for k, group in at_place.items():     # 장소 앞에는 3마리까지
            hidden += max(0, len(group) - 3)
            at_place[k] = group[:3]
        return yard, at_place, hidden

    def _slots(self, n):
        """처음 자리(발 위치) n개: 울타리 안 타원에 고르게, 앞줄·뒷줄 지그재그. 이웃끼리 MIN_GAP 이상."""
        cx, cy, rx, ry = self._feet_area()
        out = []
        for i in range(n):
            x = cx if n == 1 else cx - rx * 0.85 + i * (rx * 1.7) / (n - 1)
            y = cy + (ry * 0.6 if i % 2 == 0 else -ry * 0.6)
            out.append((x, y))
        return out

    def _too_close(self, key, x, y, gap=MIN_GAP):
        """다른 동물(지금 자리와 가려는 자리)과 gap보다 가까운지."""
        for other, w in self.walkers.items():
            if other == key:
                continue
            for ox, oy in (w['pos'], w['target']):
                if math.hypot(ox - x, oy - y) < gap:
                    return True
        return False

    def _walker(self, key, i, n):
        w = self.walkers.get(key)
        if w is None:
            rng = random.Random(key)
            # 비어 있는 자리 중 다른 동물과 가장 먼 곳
            slots = self._slots(n)
            def free_space(p):
                return min((math.hypot(p[0] - o['pos'][0], p[1] - o['pos'][1]) for o in self.walkers.values()),
                           default=999)
            x, y = slots[i] if not self.walkers else max(slots, key=free_space)
            w = self.walkers[key] = {'pos': [x, y], 'target': [x, y], 'rng': rng, 'wait': rng.uniform(0, 2)}
        return w

    def _feet_area(self):
        """동물 발이 다닐 수 있는 타원 (중심x, 중심y, 반지름x, 반지름y). 울타리 안쪽, 머리가 울타리 위로 안 나가게."""
        return self.yard.centerx, self.yard.centery + 10, self.yard.w / 2 - 10, self.yard.h / 2 - 18

    def _inside_yard(self, x, y):
        cx, cy, rx, ry = self._feet_area()
        dx, dy = (x - cx) / rx, (y - cy) / ry
        return dx * dx + dy * dy <= 1

    def update(self, dt):
        yard, _, _ = self._layout()
        night = self.app.state.get('clock', {}).get('night')
        keep = set()
        for i, a in enumerate(yard):
            key = a['id']
            keep.add(key)
            w = self._walker(key, i, len(yard))
            action = self.app.auto.get(key, {}).get('action', 'idle')
            if self._is_lying(a):                 # 누워 있는 동안은 돌아다니지 않음
                w['target'] = list(w['pos'])
                continue
            speed = 0 if night and action != 'play' else (20 if action == 'eat' else 11)
            px, py = w['pos']
            tx, ty = w['target']
            dist = math.hypot(tx - px, ty - py)
            if dist < 1:
                w['wait'] -= dt
                if w['wait'] <= 0:
                    # 새 목표: 울타리 안 + 다른 동물(자리·목표)과 MIN_GAP 이상. 짧게 짧게 이동
                    for _ in range(30):
                        nx = px + w['rng'].uniform(-30, 30)
                        ny = py + w['rng'].uniform(-12, 12)
                        if self._inside_yard(nx, ny) and not self._too_close(key, nx, ny):
                            w['target'] = [nx, ny]
                            break
                    w['wait'] = w['rng'].uniform(1.5, 4)
            elif speed:
                step = min(dist, speed * dt)
                nx, ny = px + (tx - px) / dist * step, py + (ty - py) / dist * step
                if self._too_close(key, nx, ny, MIN_GAP - 4) and not self._too_close(key, px, py, MIN_GAP - 4):
                    w['target'] = [px, py]              # 가다가 너무 가까워지면 멈추고 다음에 다른 곳으로
                else:
                    w['pos'] = [nx, ny]
        for key in list(self.walkers):
            if key not in keep:
                del self.walkers[key]

    def _sprite_box(self, key):
        """마당 동물의 스프라이트 상자 (발 위치 기준)."""
        x, y = self.walkers[key]['pos']
        box = pygame.Rect(0, 0, YARD_SIZE, YARD_SIZE)
        box.midbottom = (int(x), int(y) + FEET)
        return box

    def _is_lying(self, a):
        """드러눕기 표시 여부 (팀 결정, 임시). 규칙은 백엔드 값만 읽는다:
        자율행동 action이 'rest'이거나, 상태 단계(status) 중 하나라도 '나쁨'."""
        return self.app.auto.get(a['id'], {}).get('action') == 'rest' or T.any_bad(a)

    def _pose(self, a):
        """(그림, 왼쪽 위 좌표). 서 있으면 발 위치에 상자 바닥, 누우면 누운 그림의 바닥을 발 위치에 붙인다."""
        key = a['id']
        if self._is_lying(a):
            img = self.app.sprites.lying(a.get('sprite'), YARD_SIZE)
            x, y = self.walkers[key]['pos']
            art = img.get_bounding_rect()
            return img, (int(x) - art.centerx, int(y) - art.bottom)
        return self.app.sprites.get(a.get('sprite'), YARD_SIZE), self._sprite_box(key).topleft

    def _animal_rect(self, key):
        """실제 그림이 있는 영역 (클릭·말풍선 기준)."""
        a = self.app.animal(key)
        if not a:
            return pygame.Rect(0, 0, 0, 0)
        img, topleft = self._pose(a)
        return img.get_bounding_rect().move(topleft)

    def _place_animal_rects(self, at_place):
        """장소 앞 작은 동물: 간판 오른쪽에 나란히. 반환 [(동물, 스프라이트 상자)]."""
        out = []
        for place, group in at_place.items():
            sign = self.signs[place]
            for j, a in enumerate(group):
                box = pygame.Rect(0, 0, PLACE_SIZE, PLACE_SIZE)
                box.bottomleft = (sign.right - 4 + j * 17, sign.bottom + 2)
                out.append((a, box))
        return out

    def _more_rect(self):
        w = text_width('+99마리', 'title') + 12
        return pygame.Rect(self.yard.x + 3, self.yard.bottom + 2, w, 18)

    # ---------- 입력 ----------
    def _hit(self, pos):
        if MENU_PANEL.collidepoint(pos):
            for key, _, _ in MENU:
                if self.menu_rect(key).collidepoint(pos):
                    return ('menu', key)
            return None
        yard, at_place, hidden = self._layout()
        if hidden > 0 and self._more_rect().collidepoint(pos):
            return ('more', None)
        front_first = sorted((a['id'] for a in yard if a['id'] in self.walkers),
                             key=lambda k: -self.walkers[k]['pos'][1])   # 그리는 순서의 반대: 앞(아래) 동물부터
        for key in front_first:
            if self._animal_rect(key).collidepoint(pos):
                return ('animal', key)
        for a, r in self._place_animal_rects(at_place):
            if r.collidepoint(pos):
                return ('animal', a['id'])
        for key in self.places:
            if self.places[key]['rect'].collidepoint(pos) or self.signs[key].collidepoint(pos):
                return ('place', key)
        return None

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self._hit(event.pos)
            try:
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_HAND if self.hover else pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            hit = self._hit(event.pos)
            if not hit:
                return
            kind, key = hit
            try:
                pygame.mouse.set_system_cursor(pygame.SYSTEM_CURSOR_ARROW)
            except pygame.error:
                pass
            if kind == 'place':
                self.app.go(PLACES[key][2])
            elif kind == 'menu':
                self.app.go(next(m[2] for m in MENU if m[0] == key))
            elif kind == 'animal':
                self.app.go('animals', selected=key)
            elif kind == 'more':
                self.app.go('animals')

    # ---------- 그리기 ----------
    def toast_anchor(self):
        """지도에서는 알림을 왼쪽 아래(하늘·섬 가장자리)에 띄워 건물을 가리지 않는다."""
        return 'bottomleft', (6, T.HEIGHT - 6)

    def draw(self, surface):
        night = bool(self.app.state.get('clock', {}).get('night'))
        surface.blit(self.app.map_image(night), (0, 0))
        hover_place = self.hover[1] if self.hover and self.hover[0] == 'place' else None
        if hover_place:
            select_frame(surface, self.places[hover_place]['rect'].inflate(4, 4))
        for key in self.places:
            self._draw_sign(surface, key, key == hover_place)
        yard, at_place, hidden = self._layout()
        self._draw_yard_animals(surface, yard, night)
        for a, r in self._place_animal_rects(at_place):
            self._draw_small_animal(surface, a, r, night)
        if hidden > 0:
            self._draw_more(surface, hidden)
        self._draw_menu(surface)
        if hover_place:
            tooltip(surface, PLACES[hover_place][1], self.places[hover_place]['rect'], 'right',
                    bounds=(0, T.HEADER_H, MENU_PANEL.x - 3, T.HEIGHT - T.HEADER_H))
        elif self.hover and self.hover[0] == 'animal':
            self._draw_animal_tip(surface, self.hover[1], night)

    def _draw_sign(self, surface, key, hot=False):
        r = self.signs[key]
        card(surface, r, hot)
        text(surface, PLACES[key][0], r.center, 'title', T.TEXT, 'center')

    def _tint(self, img, night, sick=False, dim=False):
        """밤: 푸르게 어둡게 / 아픔: 푸르스름하게 / dim(상태 나쁨): 살짝 어둡게."""
        if not (night or sick or dim):
            return img
        img = img.copy()
        if night or sick:
            img.fill((150, 156, 196, 255) if night else (180, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        if dim:
            img.fill((200, 196, 196, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return img

    @staticmethod
    def _blit_breathing(surface, img, pos, inhale):
        """누운 도트 숨쉬기. 들이쉴 때 그림 윗부분을 1px 올리고 가운데 줄을 한 번 더 그려 몸이 부푼 것처럼."""
        x, y = pos
        if not inhale:
            surface.blit(img, pos)
            return
        art = img.get_bounding_rect()
        split = art.top + art.h // 2
        w, h = img.get_size()
        surface.blit(img.subsurface((0, split, w, h - split)), (x, y + split))
        surface.blit(img.subsurface((0, 0, w, split)), (x, y - 1))
        surface.blit(img.subsurface((0, split, w, 1)), (x, y + split - 1))

    # ---------- 마당 말풍선: 12×12 키트 아이콘 ----------
    def _mood_icon(self, a, night):
        """동물 머리 위 아이콘 (이름, 회색 여부) 또는 None. 표시만, 규칙 아님.

        아픔 회색 heart / 상태 하나라도 나쁨 → 회색 찡그린 얼굴 frown / 휴식·밤잠 zzz /
        먹이 찾기 meat / 혼자 놀기 heart. 평소 자유 행동은 말풍선 없음.
        """
        if a.get('sick'):
            return 'heart', True
        if T.any_bad(a):
            return 'frown', False        # 아이콘 자체가 회색
        action = self.app.auto.get(a['id'], {}).get('action', 'idle')
        if action == 'rest' or (night and action == 'idle'):
            return 'zzz', False
        if action == 'eat':
            return 'meat', False
        if action == 'play':
            return 'heart', False
        return None

    def _icon_bubble(self, surface, name, gray, midbottom, avoid):
        """아이콘 말풍선 16×16 (흰 칸 + 검은 1px 테두리 + 꼬리). 다른 말풍선과 겹치면 그리지 않는다."""
        box = pygame.Rect(0, 0, 16, 16)
        box.midbottom = (midbottom[0], midbottom[1] - 3)
        if box.collidelist(avoid) >= 0:
            return
        avoid.append(box.inflate(2, 2))
        pygame.draw.rect(surface, T.WHITE, box)
        pygame.draw.rect(surface, BUBBLE_EDGE, box, 1)
        tx = box.centerx
        pygame.draw.polygon(surface, T.WHITE, [(tx - 2, box.bottom - 1), (tx + 2, box.bottom - 1), (tx, box.bottom + 2)])
        pygame.draw.line(surface, BUBBLE_EDGE, (tx - 3, box.bottom - 1), (tx, box.bottom + 2))
        pygame.draw.line(surface, BUBBLE_EDGE, (tx + 3, box.bottom - 1), (tx, box.bottom + 2))
        img = Kit.icon(name)
        if gray:
            img = img.copy()
            img.fill((150, 150, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(img, (box.x + 2, box.y + 2))

    def _label(self, a, night):
        auto = self.app.auto.get(a['id'], {})
        action = auto.get('action', 'idle')
        if night and action in NIGHT_LABEL:
            return NIGHT_LABEL[action]
        return DAY_LABEL.get(action, auto.get('label', ''))

    def _draw_yard_animals(self, surface, yard, night):
        t = pygame.time.get_ticks() / 1000
        drawn = [a for a in yard if a['id'] in self.walkers]
        drawn.sort(key=lambda a: self.walkers[a['id']]['pos'][1])     # 뒤(위)에 있는 동물부터
        for i, a in enumerate(drawn):
            key = a['id']
            img, (x, y) = self._pose(a)
            img = self._tint(img, night, dim=T.any_bad(a))
            if self._is_lying(a):
                # 숨쉬기: 2.4초마다 몸 윗부분만 1px 올라갔다 내려옴 (바닥은 그대로)
                self._blit_breathing(surface, img, (x, y), (t + i * 0.7) % 2.4 < 1.2)
                continue
            action = self.app.auto.get(key, {}).get('action', 'idle')
            if night:
                dy = 0
            elif action == 'play':
                dy = -abs(math.sin(t * 6 + i)) * 5
            else:
                dy = round(math.sin(t * 2 + i))
            if self.walkers[key]['target'][0] < self.walkers[key]['pos'][0] - 1:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, (x, y + int(dy)))
        # 아이콘 말풍선은 동물을 다 그린 뒤에. 마우스를 올린 동물은 글씨 설명(툴팁)으로 대신
        placed = []
        if self.hover and self.hover[0] == 'animal':
            placed.append(self._animal_tip_rect(self.hover[1], night))
        for a in sorted(drawn, key=lambda a: -self.walkers[a['id']]['pos'][1]):   # 앞(아래) 동물부터 자리 잡기
            if self.hover == ('animal', a['id']):
                continue
            mood = self._mood_icon(a, night)
            if mood:
                rect = self._animal_rect(a['id'])
                self._icon_bubble(surface, mood[0], mood[1], (rect.centerx, rect.top), placed)

    def _animal_tip_text(self, a, night):
        if a.get('sick'):
            what = '아파요 · 병원에서 치료'
        else:
            act = (a.get('activity') or {}).get('kind')
            what = {'hunting': '사냥 중', 'training': '훈련 중'}.get(act) or self._label(a, night)
        return f"{a['name']} · {what}"

    def _animal_tip_target(self, key):
        """툴팁을 붙일 그림 영역 (마당 동물 또는 장소 앞 작은 동물)."""
        if key in self.walkers:
            return self._animal_rect(key)
        _, at_place, _ = self._layout()
        for a, r in self._place_animal_rects(at_place):
            if a['id'] == key:
                art = self.app.sprites.get(a.get('sprite'), PLACE_SIZE).get_bounding_rect()
                return art.move(r.topleft)
        return None

    def _animal_tip_rect(self, key, night):
        """마우스를 올린 동물의 툴팁이 차지할 자리 (아이콘 말풍선이 피하도록)."""
        a, target = self.app.animal(key), self._animal_tip_target(key)
        if not a or not target:
            return pygame.Rect(0, 0, 0, 0)
        box = pygame.Rect(0, 0, text_width(self._animal_tip_text(a, night)) + 14, 25)
        box.midbottom = (target.centerx, target.top)
        return box

    def _draw_animal_tip(self, surface, key, night):
        a, target = self.app.animal(key), self._animal_tip_target(key)
        if a and target:
            tooltip(surface, self._animal_tip_text(a, night), target, 'above',
                    bounds=(0, T.HEADER_H, MENU_PANEL.x - 3, T.HEIGHT - T.HEADER_H))

    def _draw_small_animal(self, surface, a, rect, night):
        img = self._tint(self.app.sprites.get(a.get('sprite'), PLACE_SIZE), night, a.get('sick'))
        surface.blit(img, rect)
        if a.get('sick') and self.hover != ('animal', a['id']):     # 아픔: 회색 하트 말풍선
            art = img.get_bounding_rect().move(rect.topleft)
            self._icon_bubble(surface, 'heart', True, (art.centerx, art.top), [])

    def _draw_more(self, surface, hidden):
        r = self._more_rect()
        card(surface, r, self.hover == ('more', None))
        text(surface, f'+{hidden}마리', r.center, 'title', T.TEXT, 'center')

    def _draw_menu(self, surface):
        panel(surface, MENU_PANEL)
        for key, label, _ in MENU:
            r = self.menu_rect(key)
            card(surface, r, self.hover == ('menu', key))
            img = self.icons.get(key)
            if img:
                surface.blit(img, img.get_rect(midtop=(r.centerx, r.y + 3)))
            text(surface, label, (r.centerx, r.bottom - 3), 'small', T.TEXT, 'midbottom')
