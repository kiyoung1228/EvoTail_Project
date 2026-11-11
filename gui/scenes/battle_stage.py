"""전투장 1·2단계: 스테이지 고르기 → 출전 준비. (목업 docs/mockups/battle/stage_pick.png, stage_team_prep.png)

- 스테이지 고르기: 9개 스테이지를 길로 잇고 동그라미 안에 보스 얼굴(data/enemies.json).
  깬 곳 초록 체크, 잠긴 곳 자물쇠, 대회는 메달 색 테두리. 누르면 오른쪽에 보스·대회·전투력·보상·상대 성향
- 출전 준비: 상대(preview_stage) vs 내 팀(last_team으로 미리 채움, ✕로 빼기),
  다른 동물(출전 불가는 흐리게 + 이유), 전투 전 포션, 출전(start_battle)
게임 규칙은 없다: 해금·출전 가능·보상·적 구성은 전부 백엔드 값.
"""
import pygame

from .. import theme as T
from ..app import Scene
from .. import enemies as E
from .battle_fight import shorten
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, icon, tooltip,
                       select_frame, nine, Button, Kit, mouse_pos, BUTTON_H, CARD_LABEL_H)

# 대회 메달 테두리 [어두움, 본색, 밝음] (메달 색은 키트 팔레트에 없어 여기서 정함)
MEDAL = {
    'bronze': [(122, 66, 34), (190, 116, 62), (232, 168, 104)],
    'silver': [(96, 104, 124), (176, 186, 204), (228, 234, 244)],
    'gold': [(150, 100, 20), (236, 184, 52), (255, 228, 120)],
    'diamond': [(40, 110, 160), (110, 196, 232), (200, 240, 255)],
}
WOOD_RING = [T.WOOD[0], T.WOOD[2], T.WOOD[3]]
LOCK_RING = [(96, 90, 86), (150, 142, 134), (184, 176, 166)]

# 상대 성향 (AI 종류 → 짧은 설명, 표시 문구. 자세한 설명은 백엔드 get_ai_profiles)
AI_SHORT = {
    'tutorial': '공격만 해요',
    'random': '아무거나 골라요',
    'rules': '약한 쪽부터 노려요',
    'heuristic': '이득을 계산해요',
    'lookahead': '앞수를 읽어요',
}

# 스테이지 지도 칸 (논리 좌표, 뱀 모양 길): 1줄 왼→오, 2줄 오→왼, 3줄 왼→오
NODE_POS = [(70, 112), (198, 112), (322, 112), (322, 206), (198, 206), (70, 206), (70, 300), (198, 300), (322, 300)]
NODE_R = 21
MAP_PANEL = pygame.Rect(9, 56, 404, 298)
INFO_PANEL = pygame.Rect(419, 56, 213, 298)


def stage_title(st):
    return f"{st['label']} 대회" if st.get('mode') == 'rank' else st['label']


def reward_text(st):
    """보상 문구. 대회·뉴비는 처음 깰 때만, 일반 스테이지는 이길 때마다 (백엔드 _settle_battle)."""
    if st.get('mode') == 'normal':
        return f"승리 {st['reward']:,}"
    if st.get('cleared'):
        return '받음 (처음만)'
    return f"{'첫 우승' if st.get('mode') == 'rank' else '첫 승리'} {st['reward']:,}"


def circle_clip(img, r):
    """그림을 지름 2r 동그라미 안으로 자른다."""
    size = r * 2
    out = pygame.Surface((size, size), pygame.SRCALPHA)
    out.blit(img, img.get_rect(midbottom=(r, size)) if img.get_height() < size else (0, 0))
    mask = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (r, r), r)
    out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return out


class StagePickScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.stages = []
        self.ai = {}
        self.selected = None
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')
        self.go_btn = None
        self._faces = {}

    def enter(self):
        if self.app.state.get('battle'):            # 진행 중인 전투가 있으면 바로 전투 화면
            self.app.go('battle_fight')
            return
        self.stages = self.app.call('get_stages') or []
        self.ai = self.app.call('get_ai_profiles') or {}
        ids = [s['id'] for s in self.stages]
        if self.selected not in ids or not self._stage(self.selected)['unlocked']:
            # 처음엔 아직 못 깬 열린 단계 중 첫 번째, 없으면 마지막 열린 단계
            todo = [s for s in self.stages if s['unlocked'] and not s['cleared']]
            opened = [s for s in self.stages if s['unlocked']]
            self.selected = (todo or opened or self.stages)[0 if todo else -1]['id'] if self.stages else None

    def _stage(self, sid):
        return next((s for s in self.stages if s['id'] == sid), None)

    def _node_rect(self, i):
        x, y = NODE_POS[i]
        return pygame.Rect(x - NODE_R, y - NODE_R, NODE_R * 2, NODE_R * 2)

    def _label_rect(self, i, st):
        x, y = NODE_POS[i]
        w = fit_width(st['label'], 'title') + 4 + 4
        return pygame.Rect(x - w // 2, y + NODE_R + 4, w, CARD_LABEL_H)

    # ---------- 입력 ----------
    def handle(self, event):
        self.back.handle(event)
        if self.go_btn and self.go_btn.handle(event):
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, st in enumerate(self.stages):
                if self._node_rect(i).inflate(6, 6).collidepoint(event.pos) or \
                        self._label_rect(i, st).collidepoint(event.pos):
                    if st['unlocked']:
                        self.selected = st['id']
                    else:
                        self.app.toast('아직 잠겨 있어요 · 앞 단계를 먼저 깨요', 'bad', 'lock')
                    return

    def update(self, dt):
        st = self._stage(self.selected)
        label = '팀 정하기'
        rect = pygame.Rect(INFO_PANEL.x + 13, INFO_PANEL.bottom - 40, INFO_PANEL.w - 26, 26)
        self.go_btn = Button(rect, label, lambda: self.app.go('battle_prep', stage_id=self.selected), 'red',
                             enabled=bool(st and st['unlocked']), icon='sword')

    # ---------- 그리기 ----------
    def draw(self, surface):
        self.app.backdrop(surface)
        self.back.draw(surface)
        ribbon(surface, (78, 33, 92, 18), '전투장', 'red')
        self._draw_map(surface)
        self._draw_info(surface)

    def _face(self, sid, r):
        key = (sid, r)
        if key not in self._faces:
            boss = E.boss_for_stage(sid)
            self._faces[key] = circle_clip(self.app.sprites.fit(boss['sprite'], r * 2, r * 2, max_n=1), r) \
                if boss else None
        return self._faces[key]

    def _draw_map(self, surface):
        panel(surface, MAP_PANEL)
        # 길: 점선 (깬 구간은 진하게)
        for i in range(len(self.stages) - 1):
            (x0, y0), (x1, y1) = NODE_POS[i], NODE_POS[i + 1]
            done = self.stages[i + 1]['unlocked']
            color = T.WOOD[1] if done else T.WOOD[3]
            n = max(1, int(max(abs(x1 - x0), abs(y1 - y0)) // 5))
            for k in range(1, n):
                px, py = x0 + (x1 - x0) * k // n, y0 + (y1 - y0) * k // n
                if (px - x0) ** 2 + (py - y0) ** 2 > (NODE_R + 2) ** 2 and \
                        (px - x1) ** 2 + (py - y1) ** 2 > (NODE_R + 2) ** 2:
                    pygame.draw.rect(surface, color, (px - 1, py - 1, 2, 2))
        hover = mouse_pos()
        for i, st in enumerate(self.stages):
            r = self._node_rect(i)
            cx, cy = r.center
            ring = LOCK_RING if not st['unlocked'] else MEDAL.get(st['id'], WOOD_RING) \
                if st.get('mode') == 'rank' else WOOD_RING
            pygame.draw.circle(surface, T.INK, (cx, cy), NODE_R)
            pygame.draw.circle(surface, ring[0], (cx, cy), NODE_R - 1)
            pygame.draw.circle(surface, ring[1], (cx, cy), NODE_R - 2)
            pygame.draw.circle(surface, ring[2], (cx - 1, cy - 1), NODE_R - 3, 1)
            inner = NODE_R - 5
            pygame.draw.circle(surface, T.INK, (cx, cy), inner + 1)
            if st['unlocked']:
                pygame.draw.circle(surface, (206, 230, 240), (cx, cy), inner)
                face = self._face(st['id'], inner)
                if face:
                    surface.blit(face, (cx - inner, cy - inner))
            else:
                pygame.draw.circle(surface, LOCK_RING[2], (cx, cy), inner)
                icon(surface, 'lock', (cx - 6, cy - 6))
            if st['cleared']:
                icon(surface, 'check', (r.right - 9, r.y - 2))
            selected = st['id'] == self.selected
            if selected:
                select_frame(surface, r.inflate(10, 10))
            elif st['unlocked'] and r.collidepoint(hover):
                select_frame(surface, r.inflate(6, 6), 'brown')
            # 이름: 대회는 간판, 일반은 글씨. 고른 단계는 주황 칸
            lr = self._label_rect(i, st)
            soft = not st['unlocked']
            if st.get('mode') == 'rank' or selected:
                card(surface, lr, selected)
                text_in(surface, st['label'], card_inner(lr), 'title', T.TEXT_SOFT if soft else T.TEXT, tag='stage')
            else:
                text_in(surface, st['label'], lr, 'title', T.TEXT_SOFT if soft else T.TEXT, tag='stage')

    def _draw_info(self, surface):
        panel(surface, INFO_PANEL)
        st = self._stage(self.selected)
        if not st:
            return
        P = INFO_PANEL
        pic = pygame.Rect(P.x + 13, P.y + 13, P.w - 26, 98)
        pygame.draw.rect(surface, (206, 226, 240), pic)
        for y in range(pic.y + 3, pic.bottom, 4):           # 옅은 가로줄 (하늘 무늬)
            pygame.draw.line(surface, (220, 236, 246), (pic.x + 1, y), (pic.right - 2, y))
        pygame.draw.rect(surface, T.WOOD[1], pic, 1)
        boss = E.boss_for_stage(st['id'])
        if boss:
            img = self.app.sprites.scaled(boss['sprite'], 2)
            surface.blit(img, img.get_rect(midbottom=(pic.centerx, pic.bottom - 2)))
        y = pic.bottom + 6
        text(surface, stage_title(st), (P.x + 13, y), 'big', T.TEXT)
        y += 21
        x = P.x + 13
        if st.get('mode') == 'rank':
            x = chip(surface, (x, y), '대회', 'purple').right + 3
        chip(surface, (x, y), f"전투력 {st['power']}", 'brown')
        y += 22
        rows = [('보스', boss['name'] if boss else '-', None),
                ('보상', reward_text(st), 'coin'),
                ('상대', AI_SHORT.get(st.get('ai'), self.ai.get(st.get('ai'), {}).get('strategy', '')), None)]
        for label, value, ic in rows:
            text_in(surface, label, (P.x + 13, y, 30, 15), 'small', T.TEXT_SOFT, align='left', pad=0, log=False)
            x = P.x + 48
            if ic:
                icon(surface, ic, (x, y + 2))
                x += 14
            kind = 'title' if label != '상대' else 'body'
            text_in(surface, shorten(value, P.right - 12 - x, kind), (x, y, P.right - 12 - x, 15), kind,
                    align='left', pad=0, log=False)
            y += 17
        self.go_btn.draw(surface)


# ======================================================================
class TeamPrepScene(Scene):
    """출전 준비: 상대 vs 내 팀, 다른 동물, 전투 전 포션, 출전."""
    TOP = pygame.Rect(9, 56, 622, 148)
    FOE_BOX = pygame.Rect(20, 82, 281, 110)
    TEAM_BOX = pygame.Rect(340, 82, 281, 110)
    OTHERS = pygame.Rect(9, 210, 410, 146)
    POTIONS = pygame.Rect(425, 210, 206, 146)
    PER_PAGE = 6

    def __init__(self, app):
        super().__init__(app)
        self.stage_id = None
        self.preview = None
        self.team = []            # 동물 key (최대 3)
        self.potions = {}         # 동물 key → 포션 아이템 key
        self.page = 0
        self.from_last = False
        self.items = {}
        self.buttons = []
        self._tip = None

    def enter(self):
        if self.app.state.get('battle'):
            self.app.go('battle_fight')
            return
        self.preview = self.app.call('preview_stage', stage=self.stage_id)
        self.items = self.app.call('get_shop_catalog') or {}
        owned = {a['id'] for a in self.app.state.get('animals', [])}
        last = [k for k in (self.app.state.get('last_team') or []) if k in owned]
        self.team = last[:3]
        self.from_last = bool(self.team)
        self.potions = {}
        self.page = 0

    # ---------- 데이터 ----------
    def _stage(self):
        return next((s for s in (self.app.call('get_stages') or []) if s['id'] == self.stage_id), {})

    def _others(self):
        return [a for a in self.app.state.get('animals', []) if a['id'] not in self.team]

    def _potion_keys(self):
        return [k for k, v in self.items.items() if v.get('kind') == 'prebattle']

    def _owned(self, item):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(item, 0)

    @staticmethod
    def _short_reason(a):
        """출전 불가 짧은 이유 (칩 글씨). 자세한 이유는 마우스를 올리면 백엔드 participation_reason."""
        if a.get('sick'):
            return '아픔'
        act = (a.get('activity') or {}).get('kind')
        if act:
            return '훈련 중' if act == 'training' else '사냥 중'
        if T.level(a, 'fatigue') == '나쁨':
            return '피곤'
        if T.level(a, 'fullness') == '나쁨':
            return '배고픔'
        if T.level(a, 'mood') == '나쁨':
            return '기분 나쁨'
        return '쉬어야 해요'

    # ---------- 배치 ----------
    def _team_slot(self, i):
        w = self.TEAM_BOX.w // 3
        return pygame.Rect(self.TEAM_BOX.x + i * w, self.TEAM_BOX.y, w, self.TEAM_BOX.h)

    def _x_rect(self, i):
        s = self._team_slot(i)
        return pygame.Rect(s.centerx + 21, s.y + 6, 12, 12)

    def _other_card(self, j):
        col, row = j % 3, j // 3
        return pygame.Rect(self.OTHERS.x + 13 + col * 130, self.OTHERS.y + 30 + row * 54, 124, 48)

    def _potion_card(self, k):
        col, row = k % 2, k // 2
        return pygame.Rect(self.POTIONS.x + 13 + col * 92, self.POTIONS.y + 30 + row * 35, 88, 32)

    def _foe_pos(self, i):
        """상대 3마리 발 위치 (가운데가 보스면 가운데)."""
        w = self.FOE_BOX.w // 3
        return self.FOE_BOX.x + w * i + w // 2, self.FOE_BOX.bottom - 22

    # ---------- 동작 ----------
    def add(self, a):
        if not a.get('participation'):
            self.app.toast(f"{T.josa(a['name'], '은')} 지금 출전할 수 없어요 · {a.get('participation_reason') or ''}",
                           'bad', 'heart')
            return
        if len(self.team) >= 3:
            self.app.toast('팀이 가득 찼어요 · ✕로 한 마리를 빼고 넣어요', 'bad', 'sword')
            return
        self.team.append(a['id'])
        self.from_last = False

    def remove(self, i):
        key = self.team.pop(i)
        self.potions.pop(key, None)
        self.from_last = False

    def cycle_potion(self, item):
        """포션 카드를 누를 때마다 팀원에게 차례로 (포션은 한 마리에 하나) → 다시 누르면 안 씀."""
        if not self.team or self._owned(item) <= 0:
            return
        holder = next((k for k, v in self.potions.items() if v == item), None)
        order = [k for k in self.team if k == holder or k not in self.potions]
        if holder:
            del self.potions[holder]
            nxt = order[order.index(holder) + 1] if order.index(holder) + 1 < len(order) else None
        else:
            nxt = order[0] if order else None
        if nxt:
            self.potions[nxt] = item

    def start(self):
        before = {a['id']: a['fatigue'] for a in self.app.state.get('animals', []) if a['id'] in self.team}
        data = self.app.act('start_battle', None, stage=self.stage_id, team=list(self.team),
                            prebattle_potions=dict(self.potions))
        if data is not None:
            self.app.battle_before = before        # 결과 화면에서 피로도 변화를 보여 주려고 (백엔드 값끼리 비교)
            self.app.go('battle_fight', fresh=True)

    # ---------- 입력 ----------
    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        for i in range(len(self.team)):
            if self._x_rect(i).inflate(4, 4).collidepoint(event.pos):
                self.remove(i)
                return
        others = self._others()[self.page * self.PER_PAGE:(self.page + 1) * self.PER_PAGE]
        for j, a in enumerate(others):
            if self._other_card(j).collidepoint(event.pos):
                self.add(a)
                return
        for k, item in enumerate(self._potion_keys()):
            if self._potion_card(k).collidepoint(event.pos):
                self.cycle_potion(item)
                return

    def update(self, dt):
        app = self.app
        st = self._stage()
        title = f"{st.get('label', '')} · 출전 준비"
        pages = max(1, -(-len(self._others()) // self.PER_PAGE))
        self.page = min(self.page, pages - 1)
        back_w = max(64, Button.width_for('스테이지', icon=True))
        self.title_w = fit_width(title, 'title', shadow=True) + 14
        self.title = title
        go = pygame.Rect(self.POTIONS.x + 13, self.POTIONS.bottom - 42, self.POTIONS.w - 26, 28)
        ready = len(self.team) == 3
        self.buttons = [
            Button((12, 32, back_w, BUTTON_H), '스테이지', lambda: app.go('battle'), 'brown', icon='back'),
            Button(go, '출전!' if ready else f'{3 - len(self.team)}마리 더 골라요', self.start, 'red',
                   enabled=ready, icon='sword' if ready else None),
        ]
        if pages > 1:
            y = self.OTHERS.y + 8
            self.buttons += [
                Button((self.OTHERS.right - 64, y, 24, BUTTON_H), '<', lambda: setattr(self, 'page', max(0, self.page - 1)),
                       'brown', enabled=self.page > 0),
                Button((self.OTHERS.right - 36, y, 24, BUTTON_H), '>',
                       lambda: setattr(self, 'page', min(pages - 1, self.page + 1)), 'brown', enabled=self.page < pages - 1),
            ]
        self.pages = pages

    # ---------- 그리기 ----------
    def draw(self, surface):
        self._tip = None
        self.app.backdrop(surface)
        ribbon(surface, (self.buttons[0].rect.right + 10, 33, max(92, self.title_w), 18), self.title, 'red')
        self._draw_top(surface)
        self._draw_others(surface)
        self._draw_potions(surface)
        for b in self.buttons:
            b.draw(surface)
        if self._tip:
            tooltip(surface, self._tip[0], self._tip[1], self._tip[2])

    def _draw_top(self, surface):
        panel(surface, self.TOP)
        text_in(surface, '상대', (self.FOE_BOX.x, self.TOP.y + 8, 60, 16), 'title', align='left', pad=0, log=False)
        text_in(surface, '내 팀', (self.TEAM_BOX.x, self.TOP.y + 8, 60, 16), 'title', align='left', pad=0, log=False)
        if self.from_last:
            text_in(surface, '지난번 팀으로 채웠어요', (self.TEAM_BOX.x, self.TOP.y + 8, self.TEAM_BOX.w, 16), 'small',
                    T.TEXT_SOFT, align='right', pad=0, log=False)
        text_in(surface, 'VS', (self.FOE_BOX.right, self.FOE_BOX.y, self.TEAM_BOX.x - self.FOE_BOX.right,
                                 self.FOE_BOX.h), 'big', T.shade('orange', 1), shadow=T.WOOD[3], tag='prep')
        # 상대
        box = self.FOE_BOX
        pygame.draw.rect(surface, (206, 226, 240), box)
        pygame.draw.rect(surface, T.WOOD[1], box, 1)
        hover = mouse_pos()
        foes = (self.preview or {}).get('enemy', [])
        clip = surface.get_clip()
        surface.set_clip(box)
        for i, e in enumerate(foes[:3]):
            name, sprite, boss = E.enemy_look(self.app.sprites, e)
            fx, fy = self._foe_pos(i)
            pygame.draw.ellipse(surface, (180, 200, 214), (fx - 18, fy - 4, 36, 8))
            img = self.app.sprites.scaled(sprite, 2)
            art = img.get_bounding_rect()
            pos = (fx - art.centerx, fy + 2 - art.bottom)
            surface.blit(img, pos)
            art = art.move(pos)
            role = e.get('role', '')
            chip(surface, (fx, box.bottom - 3), T.ROLE_LABEL.get(role, role), T.ROLE_KIT.get(role, 'gray'),
                 anchor='midbottom')
            if boss:
                chip(surface, (art.centerx, max(box.y + 2, art.y - 2)), '보스', 'red', anchor='midtop')
            if art.collidepoint(hover):
                stats = e.get('stats', {})
                self._tip = (f"{name} · 체력 {stats.get('hp', '-')} · 공 {stats.get('attack', '-')} · "
                             f"방 {stats.get('defense', '-')} · 민 {stats.get('agility', '-')}", art, 'below')
        surface.set_clip(clip)
        # 내 팀
        box = self.TEAM_BOX
        pygame.draw.rect(surface, (214, 236, 196), box)
        pygame.draw.rect(surface, T.WOOD[1], box, 1)
        for i in range(3):
            slot = self._team_slot(i)
            fx, fy = slot.centerx, slot.y + 70
            if i >= len(self.team):
                ghost = pygame.Rect(0, 0, 44, 44); ghost.midbottom = (fx, fy)
                for gx in range(ghost.x, ghost.right, 4):
                    surface.set_at((gx, ghost.y), T.WOOD[2]); surface.set_at((gx, ghost.bottom - 1), T.WOOD[2])
                for gy in range(ghost.y, ghost.bottom, 4):
                    surface.set_at((ghost.x, gy), T.WOOD[2]); surface.set_at((ghost.right - 1, gy), T.WOOD[2])
                text_in(surface, '비어 있어요', (slot.x, fy + 4, slot.w, 15), 'small', T.TEXT_SOFT, tag='prep')
                continue
            a = self.app.animal(self.team[i])
            if not a:
                continue
            pygame.draw.ellipse(surface, (186, 214, 166), (fx - 18, fy - 4, 36, 8))
            img = self.app.sprites.get(a.get('sprite'), 56)
            surface.blit(img, img.get_rect(midbottom=(fx, fy + 4)))
            text_in(surface, a['name'], (slot.x, fy + 4, slot.w, 15), 'title', tag='prep')
            role = a['role']
            cx = chip(surface, (fx, fy + 20), T.ROLE_LABEL[role], T.ROLE_KIT[role], anchor='midtop')
            pot = self.potions.get(a['id'])
            if pot:
                spec = self.items.get(pot, {})
                chip(surface, (cx.right + 2, cx.y), f"{T.STAT_LABEL.get(spec.get('stat'), '')[:1]}+{spec.get('amount', '')}",
                     'purple')
            # ✕ 빼기 (작은 빨간 버튼, 그림)
            xr = self._x_rect(i)
            nine(surface, 'button_red_hover' if xr.inflate(4, 4).collidepoint(mouse_pos()) else 'button_red_normal',
                 xr.inflate(0, 2).move(0, 0))
            for d in range(4):
                surface.set_at((xr.x + 4 + d, xr.y + 3 + d), T.WHITE); surface.set_at((xr.x + 7 - d, xr.y + 3 + d), T.WHITE)

    def _draw_others(self, surface):
        P = self.OTHERS
        panel(surface, P)
        text_in(surface, '다른 동물', (P.x + 13, P.y + 8, 80, 16), 'title', align='left', pad=0, log=False)
        hint_right = P.right - (70 if self.pages > 1 else 13)
        hint = f'누르면 팀에 넣어요' + (f' · {self.page + 1}/{self.pages}' if self.pages > 1 else '')
        text_in(surface, hint, (P.x + 90, P.y + 8, hint_right - P.x - 90, 16), 'small', T.TEXT_SOFT, align='right', pad=0,
                log=False)
        others = self._others()[self.page * self.PER_PAGE:(self.page + 1) * self.PER_PAGE]
        hover = mouse_pos()
        for j, a in enumerate(others):
            r = self._other_card(j)
            ok = a.get('participation')
            card(surface, r, ok and r.collidepoint(hover))
            img = self.app.sprites.get(a.get('sprite'), 28)
            if not ok:                       # 흐리게
                img = img.copy(); img.fill((150, 150, 150, 140), special_flags=pygame.BLEND_RGBA_MULT)
            inner = card_inner(r)
            surface.blit(img, img.get_rect(midleft=(inner.x + 2, inner.centery)))
            tx = inner.x + 34
            text_in(surface, a['name'], (tx, inner.y + 1, inner.right - tx, 15), 'title',
                    T.TEXT if ok else T.TEXT_SOFT, align='left', pad=0, tag='prep_card', check=inner)
            if ok:
                text_in(surface, '출전 가능', (tx, inner.y + 20, inner.right - tx, 15), 'small', T.OK, align='left',
                        pad=0, tag='prep_card', check=inner)
            else:
                chip(surface, (tx, inner.y + 21), self._short_reason(a), 'gray')
                if r.collidepoint(hover):
                    self._tip = (a.get('participation_reason') or '지금은 출전할 수 없어요', r, 'above')

    def _draw_potions(self, surface):
        P = self.POTIONS
        panel(surface, P)
        text_in(surface, '전투 전 포션', (P.x + 13, P.y + 8, P.w - 26, 16), 'title', align='left', pad=0, log=False)
        hover = mouse_pos()
        for k, item in enumerate(self._potion_keys()):
            r = self._potion_card(k)
            spec = self.items[item]
            n = self._owned(item)
            holder = next((key for key, v in self.potions.items() if v == item), None)
            card(surface, r, bool(holder) or (n > 0 and r.collidepoint(hover)))
            inner = card_inner(r)
            label = f"{T.STAT_LABEL.get(spec.get('stat'), '')[:2]} +{spec.get('amount', '')}"
            text_in(surface, label, (inner.x, inner.y, inner.w, 15), 'title', T.TEXT if n else T.TEXT_SOFT,
                    pad=0, tag='potion', check=inner)
            if n <= 0:
                sub = '없음'
            elif holder:
                sub = f"{n}개 · {self.app.name_of(holder)}"
            else:
                sub = f"{n}개 · 누르면 사용"
            text_in(surface, sub, (inner.x, inner.y + 15, inner.w, inner.h - 15), 'small', T.TEXT_SOFT, pad=0,
                    tag='potion', check=inner)
