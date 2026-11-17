"""새 게임 흐름: 인사(n1) → 첫 동료 고르기(n2·n3) → 한 마리씩 맞이(n4) → 지도 + 처음 안내(튜토리얼).

목업 docs/mockups/title/n1_welcome.png ~ n4_meet_3.png, 자리는 tools/tut_mock.py와 같게. 배경 = 표지 정원(로고·메뉴 없이).
게임 규칙은 없다: 동물 이름·역할·속성·강점·능력치는 get_catalog, 시작은 reset_game(confirm=True, starters=[3마리]).
팀 조합 칩은 고른 동물의 역할 개수만 세서 보여 줄 뿐 막지 않는다. 대사는 gui/guide.py 표.
"""
import random
import pygame

from .. import theme as T
from .. import guide as G
from ..app import Scene
from ..widgets import (text, text_in, panel, card, chip, gauge, select_frame, record, fit_width, mouse_pos, ribbon,
                       Button, BUTTON_H, tooltip)
from .title import ART, parade_keys, stage1_sprite

ROLES = ('dealer', 'tank', 'healer')
STAT_SHORT = (('hp', '체력'), ('attack', '공격'), ('defense', '방어'), ('agility', '민첩'))
LEFT = pygame.Rect(8, 58, 352, 298)       # 일반 15마리
RIGHT = pygame.Rect(364, 58, 268, 298)    # 내 팀 · 정보 · 조합
CELL = (65, 71)                # 이름(물방울개구리)이 2px 여백 안에 들어가게 (간격 68은 그대로)
PAPER = ((214, 190, 150), (236, 216, 178), (250, 236, 206), (255, 246, 224))   # tools/uikit.py PAPER
SLOT = (77, 63)


class NewGameScene(Scene):
    music = 'map'

    def __init__(self, app):
        super().__init__(app)
        self.stage = 'welcome'
        self.t = 0.0
        self.dialog = G.Dialog()
        self.catalog = {}
        self.normal = []
        self.picked = []
        self.hover = None
        self.meet_i = 0
        self.buttons = []
        self.stat_scale = 1

    @property
    def header(self):                     # 고르기 화면만 상단 바 (코인은 '—')
        return 'blank' if self.stage == 'pick' else False

    def enter(self):
        self.catalog = self.app.call('get_catalog') or self.catalog
        self.normal = parade_keys(self.catalog)
        # 능력치 막대 끝 = 일반 동물 시작 능력치 중 가장 큰 값 (표시 크기만, 규칙 아님)
        self.stat_scale = max([v for k in self.normal for v in (self.catalog[k].get('base_stats') or {}).values()]
                              or [1])
        self.picked = []
        self.hover = None
        self.go_stage('welcome')

    # ---------- 단계 ----------
    def go_stage(self, stage):
        self.stage = stage
        self.t = 0.0
        if stage == 'welcome':
            self.dialog.say(G.WELCOME)
        elif stage == 'meet':
            self.meet_i = 0
            self._say_meet()

    def _say_meet(self):
        key = self.picked[self.meet_i]
        info = self.catalog.get(key, {})
        a, b = G.ROLE_LINES[info.get('role', 'dealer')]
        self.dialog.say((f"{T.josa(info.get('name', ''), '과')} 함께! {a}", b))

    def start_game(self, keys):
        """reset_game(starters) → 맞이. 실패하면 백엔드 이유 알림(app.call)."""
        res = self.app.call('reset_game', confirm=True, starters=list(keys))
        if res is None:
            return False
        self.app.reset_storm()
        self.app.refresh()
        events = self.app.call('recent_events') or []
        self.app.last_seq = max([e.get('seq', 0) for e in events], default=0)
        self.app.had_save = True
        self.picked = list(keys)
        self.go_stage('meet')
        return True

    def finish(self):
        """맞이가 끝나면 지도 + 처음 안내 (이미 끝냈으면 안내 없이)."""
        self.app.go('map')
        if not self.app.audio.settings.get('tutorial_done'):
            from .tutorial import TutorialOverlay
            self.app.open_overlay(TutorialOverlay(self.app))

    def skip(self):
        if self.stage == 'welcome':
            self.go_stage('pick')
        elif self.stage == 'pick':                              # 일반 15마리 중 무작위 3마리
            self.start_game(random.sample(self.normal, 3))
        else:
            self.finish()

    def next_line(self):
        if not self.dialog.click():
            return
        if self.stage == 'welcome':
            self.go_stage('pick')
        elif self.stage == 'meet':
            self.meet_i += 1
            if self.meet_i >= len(self.picked):
                self.finish()
            else:
                self.t = 0.0
                self._say_meet()

    # ---------- 고르기 ----------
    def cell_rect(self, key):
        info = self.catalog[key]
        row = ROLES.index(info['role'])
        col = [k for k in self.normal if self.catalog[k]['role'] == info['role']].index(key)
        return pygame.Rect(16 + col * 68, 66 + row * 95 + 19, *CELL)

    @staticmethod
    def slot_rect(i):
        return pygame.Rect(376 + i * 82, 82, *SLOT)

    def toggle(self, key):
        if key in self.picked:
            self.picked.remove(key)
        elif len(self.picked) < 3:
            self.picked.append(key)
        else:
            self.app.toast('3마리까지 · ✕로 빼고 고르기', 'bad', 'heart')

    def focus(self):
        return self.hover or (self.picked[-1] if self.picked else (self.normal[0] if self.normal else None))

    # ---------- 입력 ----------
    def handle(self, event):
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.MOUSEMOTION and self.stage == 'pick':
            self.hover = next((k for k in self.normal if self.cell_rect(k).collidepoint(event.pos)), None)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.stage == 'pick':
                key = next((k for k in self.normal if self.cell_rect(k).collidepoint(event.pos)), None)
                if key:
                    self.toggle(key)
            else:
                self.next_line()
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.stage != 'pick':
                self.next_line()

    def update(self, dt):
        self.t += dt
        self.dialog.update(dt)
        self.buttons = [Button(G.SKIP_RECT, '건너뛰기', self.skip, 'brown')]
        if self.stage == 'pick':
            for i, key in enumerate(self.picked):
                r = self.slot_rect(i)
                self.buttons.append(Button((r.x + 62, r.y - 4, 16, 14), '', lambda k=key: self.toggle(k), 'red'))
            n = len(self.picked)
            go = pygame.Rect(376, 318, 244, 30)
            if n == 3:
                self.buttons.append(Button(go, '이 동료들과 시작', lambda: self.start_game(self.picked), 'green',
                                           icon='heart'))
            else:
                self.buttons.append(Button(go, f'{3 - n}마리 더 고르기', lambda: None, 'gray', enabled=False))

    # ---------- 그리기 ----------
    def draw(self, surface):
        dim = {'welcome': 60, 'pick': 150, 'meet': 110}[self.stage]
        ART.garden(surface, self.t + 3, dim)
        getattr(self, f'_draw_{self.stage}')(surface)
        for b in self.buttons:
            b.draw(surface)
        for i in range(len(self.picked) if self.stage == 'pick' else 0):        # ✕ 그림
            r = self.slot_rect(i)
            x, y = r.x + 66, r.y
            pygame.draw.line(surface, T.WHITE, (x, y), (x + 7, y + 6))
            pygame.draw.line(surface, T.WHITE, (x + 7, y), (x, y + 6))

    def _draw_welcome(self, surface):
        glow = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 250, 220, 70), (240, 70, 161, 181))
        surface.blit(glow, (0, 0))
        pygame.draw.ellipse(surface, (60, 90, 60), (276, 222, 89, 13))
        img = G.art().get(G.art().flap(self.t, talk=not self.dialog.done), 4)
        surface.blit(img, (320 - 64, 96))
        for x, y in ((250, 110), (392, 128), (270, 200), (380, 196)):
            if int(self.t * 3 + x) % 3:
                G.sparkle(surface, x, y)
        self.dialog.draw(surface)

    def _draw_pick(self, surface):
        ribbon(surface, (12, 33, max(110, fit_width('첫 동료 고르기', 'title', shadow=True) + 14), 18),
               '첫 동료 고르기', 'red')
        surface.blit(G.art().get(G.TechmoArt.idle_kind(self.t), 1), (132, 26))
        hint = pygame.Rect(166, 32, 290, 22)
        card(surface, hint)
        text_in(surface, G.PICK_HINT, (hint.x + 4, hint.y + 1, hint.w - 8, hint.h - 2), 'body', align='left',
                tag='guide')
        # 왼쪽: 역할 3줄 × 5
        panel(surface, LEFT)
        hover = self.hover
        for row, role in enumerate(ROLES):
            y = 66 + row * 95
            keys = [k for k in self.normal if self.catalog[k]['role'] == role]
            el = self.catalog[keys[0]]['element'] if keys else 'fire'
            r = chip(surface, (16, y), T.ROLE_LABEL[role], T.ROLE_KIT[role])
            chip(surface, (r.right + 3, y), T.ELEMENT_LABEL[el], T.ELEMENT_KIT[el])
            for key in keys:
                self._draw_cell(surface, key, key == hover)
        # 오른쪽: 내 팀 · 정보 · 조합
        panel(surface, RIGHT)
        n = len(self.picked)
        text(surface, f'나의 첫 동료 {n} / 3', (376, 72), 'title', T.TEXT, 'midleft')
        for i in range(3):
            r = self.slot_rect(i)
            if i < n:
                key = self.picked[i]
                role = self.catalog[key]['role']
                pygame.draw.rect(surface, (214, 236, 196), r)
                pygame.draw.rect(surface, T.WOOD[2], r, 1)
                img = self.app.sprites.get(stage1_sprite(self.catalog[key]), 56)
                art = img.get_bounding_rect()
                surface.blit(img, (r.x + 38 - art.centerx, r.y + 25 - art.centery))
                chip(surface, (r.x + 38, r.y + 44), T.ROLE_LABEL[role], T.ROLE_KIT[role], anchor='midtop')
            else:
                for xx in range(r.x, r.right, 4):
                    surface.set_at((xx, r.y), T.WOOD[2]); surface.set_at((xx, r.bottom - 1), T.WOOD[2])
                for yy in range(r.y, r.bottom, 4):
                    surface.set_at((r.x, yy), T.WOOD[2]); surface.set_at((r.right - 1, yy), T.WOOD[2])
                text(surface, '빈 자리', r.center, 'small', T.TEXT_SOFT, 'center')
        pygame.draw.line(surface, PAPER[0], (374, 154), (622, 154))
        self._draw_focus(surface, self.focus())
        pygame.draw.line(surface, PAPER[0], (374, 214), (622, 214))
        text(surface, '팀 조합', (376, 225), 'title', T.TEXT, 'midleft')
        roles = [self.catalog[k]['role'] for k in self.picked]
        x = 376
        for role, count in G.team_counts(roles):
            x = chip(surface, (x, 234), f"{T.ROLE_LABEL[role]} {count}", T.ROLE_KIT[role]).right + 3
        y = 254
        warns = []
        if roles and 'healer' not in roles:
            warns.append('힐러 없음 · 회복 못 함')
        if roles and 'tank' not in roles:
            warns.append('탱커 없음 · 지켜 줄 동료 없음')
        for w in warns:
            chip(surface, (376, y), w, 'red')
            y += 18
        if not warns and n == 3:
            chip(surface, (376, y), '균형 잡힌 팀!', 'gold')
        text(surface, '조합은 나중에 알을 부화해서 바꿀 수 있어', (376, 302), 'small', T.TEXT_SOFT, 'midleft')

    def _draw_cell(self, surface, key, focused):
        r = self.cell_rect(key)
        on = key in self.picked
        pygame.draw.rect(surface, (255, 246, 224) if on else PAPER[2], r)
        pygame.draw.rect(surface, T.INK, r, 1)
        pygame.draw.line(surface, T.WHITE, (r.x + 1, r.y + 1), (r.right - 2, r.y + 1))
        img = self.app.sprites.get(stage1_sprite(self.catalog[key]), 56)
        art = img.get_bounding_rect()
        surface.blit(img, (r.x + 31 - art.centerx, r.y + 31 - art.centery))
        name = self.catalog[key].get('name', '')
        text_in(surface, name, (r.x + 1, r.y + 54, r.w - 2, 14), 'small', T.TEXT, tag='pick')
        if on:
            i = self.picked.index(key) + 1
            c = (r.x + 53, r.y + 10)
            pygame.draw.circle(surface, T.INK, c, 7)
            pygame.draw.circle(surface, (250, 196, 60), c, 6)
            text(surface, str(i), (c[0] + 1, c[1]), 'small', T.INK, 'center')
        if focused:
            select_frame(surface, r.inflate(4, 4))

    def _draw_focus(self, surface, key):
        if not key:
            return
        info = self.catalog[key]
        role = info['role']
        g = text(surface, info.get('name', ''), (376, 166), 'title', T.TEXT, 'midleft')
        x = chip(surface, (g.right + 6, 158), T.ROLE_LABEL[role], T.ROLE_KIT[role]).right + 3
        s = (info.get('strength') or '').strip()
        chip(surface, (x, 158), '균형' if s in ('', '기준') else s, 'brown')
        st = info.get('base_stats') or {}
        for i, (stat, label) in enumerate(STAT_SHORT):
            x, y = 376 + (i % 2) * 124, 180 + (i // 2) * 14
            text(surface, label, (x, y + 5), 'small', T.TEXT_SOFT, 'midleft')
            gauge(surface, (x + 24, y, 62, 9), st.get(stat, 0), self.stat_scale, T.ROLE_KIT[role])
            text(surface, str(st.get(stat, 0)), (x + 116, y + 5), 'small', T.TEXT, 'midright')

    def _draw_meet(self, surface):
        key = self.picked[self.meet_i] if self.meet_i < len(self.picked) else None
        if not key:
            return
        info = self.catalog[key]
        role = info['role']
        light = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)               # 스포트라이트
        pygame.draw.polygon(light, (255, 250, 220, 50), [(290, 26), (350, 26), (420, 250), (220, 250)])
        surface.blit(light, (0, 0))
        pygame.draw.ellipse(surface, (255, 246, 200), (248, 226, 145, 23))
        pygame.draw.ellipse(surface, (220, 196, 140), (248, 226, 145, 23), 1)
        img = self.app.sprites.get(stage1_sprite(info), 112)                       # 원본 ×4
        surface.blit(img, (320 - img.get_width() // 2, 236 - img.get_height() + 8))
        for x, y in ((248, 120), (398, 138), (262, 196), (386, 206)):
            if int(self.t * 3 + y) % 3:
                G.sparkle(surface, x, y)
        box = pygame.Rect(436, 96, 188, 118)
        panel(surface, box)
        text(surface, info.get('name', ''), (448, 114), 'big', T.TEXT, 'midleft')
        r = chip(surface, (448, 126), T.ROLE_LABEL[role], T.ROLE_KIT[role])
        e = chip(surface, (r.right + 3, 126), T.ELEMENT_LABEL[info['element']], T.ELEMENT_KIT[info['element']])
        a = self.app.animal(key)                     # 성격 = reset_game 뒤 스냅샷의 그 동물 nature
        nature = a.get('nature') if a else None
        nature_chip = chip(surface, (e.right + 3, 126), T.NATURE_LABEL.get(nature, nature), 'blue') if nature else None
        self.nature_chip = nature_chip
        record('칩 줄', r.union(nature_chip or e), (446, 124, box.right - 10 - 446, 20), 'meet-chips')
        st = info.get('base_stats') or {}
        for i, (stat, label) in enumerate(STAT_SHORT):
            y = 150 + i * 14
            text(surface, label, (448, y + 5), 'small', T.TEXT_SOFT, 'midleft')
            gauge(surface, (476, y, 100, 9), st.get(stat, 0), self.stat_scale, T.ROLE_KIT[role])
            text(surface, str(st.get(stat, 0)), (612, y + 5), 'small', T.TEXT, 'midright')
        surface.blit(G.art().get(G.art().flap(self.t), 2), (120, 172))
        G.progress(surface, '첫 동료', self.meet_i + 1, 3)
        self.dialog.draw(surface)
        if nature_chip and nature_chip.collidepoint(mouse_pos()):
            tooltip(surface, T.nature_tip(nature, T.nature_blocked(a)), nature_chip, 'below')
