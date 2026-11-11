"""메인 화면: 떠 있는 섬 마을 (목업 docs/mockups/main_day.png, main_night.png).

- 배경: assets/map/map_day.png / map_night.png (백엔드 clock.night에 따라)
- 건물 클릭 영역·문·마당: assets/map/map.json
- 간판(나무 판 + 글자)은 여기서 문 아래에 그린다. 마우스를 올리면 노란 테두리 + 설명 말풍선
- 오른쪽 메뉴 5개: assets/ui/icon_*.png
- 마당 동물: 스냅샷 yard(플레이어가 고른 동물) + 빈자리 자동 채우기, 최대 yard_max마리. 활동 중인 동물은 그 장소 앞에 작게 (사냥터 / 집 / 병원)
게임 규칙은 없다. 동물 상태·자율행동은 app.state, app.auto(백엔드 값)를 그대로 읽는다.
"""
import json
import math
import os
import random
import pygame

from .. import theme as T
from ..app import Scene
from ..widgets import text

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
MENU_PANEL = pygame.Rect(1180, 82, 88, 534)
MENU_BTN = 76          # 버튼 한 변
MENU_STEP = 104        # 버튼 간격

YARD_SIZE = 112        # 마당 동물: 스프라이트 파일 그대로 (28px 도트 × 4, 그림은 약 64px)
PLACE_SIZE = 56        # 장소 앞에 작게 (파일의 ½ = 28px 도트 × 2)
FEET = 8               # 스프라이트 상자 바닥과 발 사이 여백 (투명 영역)

SIGN_WOOD = (247, 236, 214)
SIGN_EDGE = (110, 74, 44)
SIGN_SHADOW = (88, 60, 36)
HOVER = (255, 226, 92)
TIP_BG = (52, 44, 38)
MENU_BG = (250, 240, 222)
MENU_EDGE = (176, 128, 84)

# 밤에는 말풍선 문구만 바꾼다 (표시 문구, 규칙 아님)
NIGHT_LABEL = {'rest': '잠자는 중 zZ', 'idle': '꾸벅꾸벅…', 'play': '밤 산책', 'eat': '야식 찾는 중'}
DAY_LABEL = {'rest': '휴식 중 z'}

# 활동 → 그 활동을 보여줄 장소
ACTIVITY_PLACE = {'hunting': 'hunting', 'training': 'home'}


def _load_map():
    with open(os.path.join(MAP_DIR, 'map.json'), encoding='utf-8') as f:
        data = json.load(f)
    places = {k: {'rect': pygame.Rect(v['rect'][0], v['rect'][1], v['rect'][2] - v['rect'][0],
                                      v['rect'][3] - v['rect'][1]),
                  'door': tuple(v['door'])} for k, v in data['places'].items()}
    x0, y0, x1, y1 = data['yard']
    return places, pygame.Rect(x0, y0, x1 - x0, y1 - y0)


class MapScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.places, self.yard = _load_map()
        self.bg = {False: pygame.image.load(os.path.join(MAP_DIR, 'map_day.png')).convert(),
                   True: pygame.image.load(os.path.join(MAP_DIR, 'map_night.png')).convert()}
        self.icons = {}
        for key, _, _ in MENU:
            path = os.path.join(UI_DIR, f'icon_{key}.png')
            self.icons[key] = pygame.image.load(path).convert_alpha() if os.path.exists(path) else None
        self.signs = {key: self._sign_rect(key) for key in self.places}
        self.walkers = {}      # 동물 id → 마당 안 위치·목표 (화면 연출용)
        self.hover = None      # ('place', key) / ('menu', key) / ('animal', key) / ('more', None)

    # ---------- 배치 ----------
    def _sign_rect(self, key):
        label = PLACES[key][0]
        w = T.font(20, True).size(label)[0] + 26
        dx, dy = self.places[key]['door']
        return pygame.Rect(dx - w // 2, dy + 8, w, 34)

    def menu_rect(self, key):
        i = [m[0] for m in MENU].index(key)
        return pygame.Rect(MENU_PANEL.centerx - MENU_BTN // 2, MENU_PANEL.y + 8 + i * MENU_STEP, MENU_BTN, MENU_BTN)

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
            return T.status_level('fullness', a['fullness']) == '나쁨' or T.status_level('mood', a['mood']) == '나쁨'
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

    def _walker(self, key, i, n):
        w = self.walkers.get(key)
        if w is None:
            rng = random.Random(key)
            # 처음 자리(발 위치): 앞줄·뒷줄 지그재그로 고르게
            cx, cy, rx, ry = self._feet_area()
            cols = (n + 1) // 2
            col, back = divmod(i, 2)
            x = cx - rx + (col + (0.25 if back else 0.75)) * 2 * rx / max(1, cols)
            y = cy + (-ry * 0.8 if back else ry * 0.8)
            w = self.walkers[key] = {'pos': [x, y], 'target': [x, y], 'rng': rng, 'wait': rng.uniform(0, 2)}
        return w

    def _feet_area(self):
        """동물 발이 다닐 수 있는 타원 (중심x, 중심y, 반지름x, 반지름y). 울타리 안쪽, 머리가 울타리 위로 안 나가게."""
        return self.yard.centerx, self.yard.centery + 20, self.yard.w / 2 - 20, self.yard.h / 2 - 36

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
            speed = 0 if action == 'rest' or night and action != 'play' else (40 if action == 'eat' else 22)
            px, py = w['pos']
            tx, ty = w['target']
            dist = math.hypot(tx - px, ty - py)
            if dist < 2:
                w['wait'] -= dt
                if w['wait'] <= 0:
                    for _ in range(20):
                        nx = w['rng'].uniform(self.yard.left, self.yard.right)
                        ny = w['rng'].uniform(self.yard.top, self.yard.bottom)
                        if self._inside_yard(nx, ny):
                            w['target'] = [nx, ny]
                            break
                    w['wait'] = w['rng'].uniform(1.5, 4)
            elif speed:
                step = min(dist, speed * dt)
                w['pos'] = [px + (tx - px) / dist * step, py + (ty - py) / dist * step]
        for key in list(self.walkers):
            if key not in keep:
                del self.walkers[key]

    def _sprite_box(self, key):
        """마당 동물의 스프라이트 상자 (발 위치 기준)."""
        x, y = self.walkers[key]['pos']
        box = pygame.Rect(0, 0, YARD_SIZE, YARD_SIZE)
        box.midbottom = (int(x), int(y) + FEET)
        return box

    def _animal_rect(self, key):
        """실제 그림이 있는 영역 (클릭·말풍선 기준)."""
        a = self.app.animal(key) or {}
        art = self.app.sprites.get(a.get('sprite'), YARD_SIZE).get_bounding_rect()
        return art.move(self._sprite_box(key).topleft)

    def _place_animal_rects(self, at_place):
        """장소 앞 작은 동물: 간판 오른쪽에 나란히. 반환 [(동물, 스프라이트 상자)]."""
        out = []
        for place, group in at_place.items():
            sign = self.signs[place]
            for j, a in enumerate(group):
                box = pygame.Rect(0, 0, PLACE_SIZE, PLACE_SIZE)
                box.bottomleft = (sign.right - 8 + j * 34, sign.bottom + 4)
                out.append((a, box))
        return out

    def _more_rect(self):
        return pygame.Rect(self.yard.x + 6, self.yard.bottom + 4, 92, 30)

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
    def draw(self, surface):
        night = bool(self.app.state.get('clock', {}).get('night'))
        surface.blit(self.bg[night], (0, 0))
        hover_place = self.hover[1] if self.hover and self.hover[0] == 'place' else None
        if hover_place:
            r = self.places[hover_place]['rect']
            pygame.draw.rect(surface, HOVER, r.inflate(4, 4), 3, border_radius=12)
        for key in self.places:
            self._draw_sign(surface, key)
        yard, at_place, hidden = self._layout()
        self._draw_yard_animals(surface, yard, night)
        for a, r in self._place_animal_rects(at_place):
            self._draw_small_animal(surface, a, r, night)
        if hidden > 0:
            self._draw_more(surface, hidden)
        self._draw_menu(surface)
        if hover_place:
            self._draw_tip(surface, PLACES[hover_place][1], self.places[hover_place]['rect'])

    def _draw_sign(self, surface, key):
        r = self.signs[key]
        pygame.draw.rect(surface, SIGN_SHADOW, r.move(0, 3), border_radius=8)
        pygame.draw.rect(surface, SIGN_WOOD, r, border_radius=8)
        pygame.draw.rect(surface, SIGN_EDGE, r, 2, border_radius=8)
        text(surface, PLACES[key][0], r.center, 20, T.INK, bold=True, anchor='center')

    def _tint(self, img, night, sick=False):
        if not (night or sick):
            return img
        img = img.copy()
        img.fill((150, 156, 196, 255) if night else (180, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return img

    def _bubble(self, surface, label, midbottom, size=14, avoid=None):
        """말풍선. ``avoid``(이미 그린 말풍선 목록)와 겹치면 위로 올린다."""
        img = T.font(size).render(label, True, T.INK)
        box = img.get_rect().inflate(16, 8)
        box.midbottom = midbottom
        box.clamp_ip(pygame.Rect(0, 56, MENU_PANEL.x - 6, T.HEIGHT - 56))
        if avoid is not None:
            for _ in range(4):
                hit = box.collidelist(avoid)
                if hit < 0:
                    break
                box.bottom = avoid[hit].top - 2
            avoid.append(box)
            if box.bottom < midbottom[1] - 2:     # 올라간 말풍선은 꼬리를 길게
                pygame.draw.line(surface, (120, 108, 96), (midbottom[0], box.bottom), midbottom, 1)
            midbottom = (midbottom[0], box.bottom + 1)
        pygame.draw.rect(surface, (255, 255, 255), box, border_radius=10)
        pygame.draw.rect(surface, (120, 108, 96), box, 1, border_radius=10)
        tx = max(box.left + 10, min(box.right - 10, midbottom[0]))
        tail = [(tx - 5, box.bottom - 1), (tx + 5, box.bottom - 1), (tx, box.bottom + 6)]
        pygame.draw.polygon(surface, (255, 255, 255), tail)
        pygame.draw.lines(surface, (120, 108, 96), False, [tail[0], tail[2], tail[1]], 1)
        surface.blit(img, img.get_rect(center=box.center))
        return box

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
            box = self._sprite_box(key)
            action = self.app.auto.get(key, {}).get('action', 'idle')
            if night or action == 'rest':
                dy = 0
            elif action == 'play':
                dy = -abs(math.sin(t * 6 + i)) * 10
            else:
                dy = math.sin(t * 2 + i) * 2
            img = self.app.sprites.get(a.get('sprite'), YARD_SIZE)
            img = self._tint(img, night)
            if self.walkers[key]['target'][0] < self.walkers[key]['pos'][0] - 1:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, box.move(0, int(dy)))
        # 이름(마우스를 올렸을 때)과 말풍선은 동물을 다 그린 뒤에 (가려지지 않게)
        placed = []
        for a in sorted(drawn, key=lambda a: -self.walkers[a['id']]['pos'][1]):   # 앞(아래) 동물부터 자리 잡기
            rect = self._animal_rect(a['id'])
            label = self._label(a, night)
            if self.hover == ('animal', a['id']):
                label = f"{a['name']} · {label}"
            self._bubble(surface, label, (rect.centerx, rect.top - 6), avoid=placed)

    def _draw_small_animal(self, surface, a, rect, night):
        img = self._tint(self.app.sprites.get(a.get('sprite'), PLACE_SIZE), night, a.get('sick'))
        surface.blit(img, rect)
        if self.hover == ('animal', a['id']):
            act = (a.get('activity') or {}).get('kind')
            what = '아파요' if a.get('sick') else ('사냥 중' if act == 'hunting' else '훈련 중')
            art = img.get_bounding_rect().move(rect.topleft)
            self._bubble(surface, f"{a['name']} · {what}", (art.centerx, art.top - 4), 13)

    def _draw_more(self, surface, hidden):
        r = self._more_rect()
        pygame.draw.rect(surface, SIGN_SHADOW, r.move(0, 3), border_radius=8)
        pygame.draw.rect(surface, SIGN_WOOD, r, border_radius=8)
        pygame.draw.rect(surface, HOVER if self.hover == ('more', None) else SIGN_EDGE, r, 2, border_radius=8)
        text(surface, f'+{hidden}마리', r.center, 16, T.INK, bold=True, anchor='center')

    def _draw_menu(self, surface):
        pygame.draw.rect(surface, MENU_BG, MENU_PANEL, border_radius=16)
        pygame.draw.rect(surface, MENU_EDGE, MENU_PANEL, 3, border_radius=16)
        for key, label, _ in MENU:
            r = self.menu_rect(key)
            hot = self.hover == ('menu', key)
            pygame.draw.rect(surface, (196, 160, 120), r.move(0, 3), border_radius=12)
            pygame.draw.rect(surface, (255, 246, 226) if hot else (255, 252, 244), r, border_radius=12)
            pygame.draw.rect(surface, HOVER if hot else MENU_EDGE, r, 3 if hot else 2, border_radius=12)
            icon = self.icons.get(key)
            if icon:
                surface.blit(icon, icon.get_rect(midtop=(r.centerx, r.y + 4)))
            text(surface, label, (r.centerx, r.bottom - 5), 13, T.INK, bold=True, anchor='midbottom')

    def _draw_tip(self, surface, msg, rect):
        img = T.font(16).render(msg, True, (255, 255, 255))
        box = img.get_rect().inflate(24, 14)
        box.midleft = (rect.right + 12, rect.y + 40)
        if box.right > MENU_PANEL.x - 6:
            box.midright = (rect.x - 12, rect.y + 40)
        pygame.draw.rect(surface, TIP_BG, box, border_radius=12)
        tail_x = box.left if box.left > rect.right else box.right
        sign = -1 if box.left > rect.right else 1
        pygame.draw.polygon(surface, TIP_BG, [(tail_x, box.centery - 6), (tail_x, box.centery + 6),
                                              (tail_x + sign * 8, box.centery)])
        surface.blit(img, img.get_rect(center=box.center))
