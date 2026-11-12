"""내 동물: 동물 목록과 상세 정보. 간식 주기, 훈련, 진화, 마당에 내보내기.

목업 docs/mockups/animals_v2.png, 키트 docs/UI_KIT.md. 좌표는 640×360 논리 픽셀.
"""
import pygame

from .. import theme as T
from ..app import Scene, Overlay
from ..widgets import (text, text_width, text_in, panel, card, card_inner, ribbon, chip, gauge, icon, tooltip,
                       Button, Kit, mouse_pos, shorten, fit_width, wrap2, record, BUTTON_H)

LIST = pygame.Rect(9, 56, 174, 298)          # 왼쪽 목록 창
LIST_INNER = LIST.inflate(-18, -18)          # 칸이 놓이는 영역 (창 테두리 안)
DETAIL = pygame.Rect(191, 56, 443, 298)      # 오른쪽 상세 창
CARD_H, CARD_STEP = 32, 35
PORTRAIT = pygame.Rect(204, 70, 94, 94)
INFO_X = 308
STAT_Y0, STAT_STEP = 197, 20


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m // 60}:{m % 60:02d}:{s:02d}" if m >= 60 else f"{m}:{s:02d}"


class AnimalsScene(Scene):
    music = 'map'         # 배경음: 지도 곡 (낮·밤). 지도에서 오면 같은 곡이라 이어짐
    def __init__(self, app):
        super().__init__(app)
        self.selected = None
        self.train_stat = 'attack'
        self.scroll = 0
        self.rules = app.call('get_rules') or {}
        self.buttons = []

    def enter(self):
        ids = [a['id'] for a in self.app.state.get('animals', [])]
        if self.selected not in ids:
            self.selected = ids[0] if ids else None
        else:   # 고른 동물이 보이게 목록 스크롤
            i = ids.index(self.selected)
            top, bottom = i * CARD_STEP, i * CARD_STEP + CARD_H
            if top < self.scroll or bottom > self.scroll + LIST_INNER.h:
                self.scroll = max(0, min(self._max_scroll(), top - CARD_STEP))

    def _max_scroll(self):
        return max(0, len(self.app.state.get('animals', [])) * CARD_STEP - 3 - LIST_INNER.h)

    def _card_rect(self, i):
        return pygame.Rect(LIST_INNER.x, LIST_INNER.y + i * CARD_STEP - self.scroll, LIST_INNER.w - 6, CARD_H)

    # ---------- 입력 ----------
    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return
        if event.type == pygame.MOUSEWHEEL and LIST.collidepoint(mouse_pos()):
            self.scroll = max(0, min(self._max_scroll(), self.scroll - event.y * CARD_STEP))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if LIST_INNER.collidepoint(event.pos):
                for i, a in enumerate(self.app.state.get('animals', [])):
                    if self._card_rect(i).collidepoint(event.pos):
                        self.selected = a['id']
            for stat, rect in self._stat_rows():
                if rect.collidepoint(event.pos):
                    self.train_stat = stat

    # ---------- 버튼은 상태에 따라 매 프레임 다시 만든다 ----------
    def update(self, dt):
        app, a = self.app, self.app.animal(self.selected)
        self.buttons = [Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                               lambda: app.go('map'), 'brown', icon='back')]
        if not a:
            return
        key = a['id']
        busy = a.get('activity') is not None

        # 마당에 내보내기 / 들이기 (세이브에 저장되는 마당 목록)
        yard = list(app.state.get('yard', []))
        yard_max = app.state.get('yard_max') or 0
        if key in yard:
            yard_label = '마당에서 들이기'
        elif len(yard) >= yard_max:
            yard_label = f'마당 가득 {len(yard)}/{yard_max}'
        else:
            yard_label = '마당에 내보내기'
        bw = Button.width_for(yard_label, icon=True)          # 글씨 + 아이콘이 2px 여백을 두고 들어가는 폭
        yard_btn = pygame.Rect(DETAIL.right - 13 - bw, DETAIL.y + 10, bw, BUTTON_H)
        if key in yard:
            self.buttons.append(Button(yard_btn, yard_label,
                                       lambda: app.act('set_yard_animals', f"{T.josa(app.name_of(key), '을')} 집으로 들였다",
                                                       icon='home', keys=[k for k in yard if k != key]),
                                       'brown', icon='home'))
        else:
            full = len(yard) >= yard_max
            self.buttons.append(Button(yard_btn, yard_label,
                                       lambda: app.act('set_yard_animals', f"{T.josa(app.name_of(key), '을')} 마당에 내보냈다",
                                                       icon='home', keys=yard + [key]),
                                       'green', enabled=not full, icon='home'))

        # 간식
        snacks = app.state.get('inventory', {}).get('stackable', {}).get('snack', 0)
        self.buttons.append(Button((204, 322, 129, 24), f'간식 주기 ×{snacks}',
                                   lambda: app.act('use_item', '간식을 줬다', icon='snack', item='snack', key=key),
                                   'orange', enabled=snacks > 0 and not busy, icon='snack'))
        # 장비 (장착·해제 = equip(key, item) / equip(key, None). 전투 중·활동 중이면 백엔드가 거절)
        eq_label = self._equip_label(a)
        eq_rect = pygame.Rect(339, 322, 143, 24)
        self.buttons.append(Button(eq_rect, eq_label, lambda: app.open_overlay(EquipOverlay(app, key, eq_rect)),
                                   'blue', enabled=not busy, icon='shield'))
        # 진화
        ready = a['stage'] < a['max_stage'] and all(a['stats'][s] >= a['caps'][s] for s in T.STATS)
        costs = self.rules.get('evolution_cost', {})
        cost = costs.get(a['stage'] + 1, costs.get(str(a['stage'] + 1)))
        label = '최종 진화' if a['stage'] >= a['max_stage'] else (f'진화 {cost:,}' if cost else '진화')
        self.buttons.append(Button((486, 322, 134, 24), label,
                                   lambda: app.act('evolve', lambda d: f"{T.josa(d.get('name') or app.name_of(key), '으로')} 진화했다!", icon='heart',
                                                   key=key),
                                   'purple', enabled=ready and not busy, icon='coin' if cost else None))
        # 훈련
        if busy and a['activity'].get('kind') == 'training':
            self.buttons.append(Button((516, 280, 102, 32), '훈련 취소',
                                       lambda: app.act('cancel_training', '훈련 취소', icon='sword', key=key),
                                       'red'))
        else:
            stat = self.train_stat
            for i, diff in enumerate(('easy', 'medium', 'hard')):
                dur, gain, _ = self.rules.get('training', {}).get(diff, (0, 0, 0))
                self.buttons.append(Button(
                    (300 + i * 108, 280, 102, 32), T.DIFFICULTY_LABEL[diff],
                    lambda d=diff, s=stat: app.act('start_training', f"{T.STAT_LABEL[s]} 훈련 시작", icon='sword',
                                                   key=key, stat=s, difficulty=d),
                    'green', sub=f'{dur // 60}분 · +{gain}',
                    enabled=not busy and a['participation'] and a['stats'][stat] < a['caps'][stat]))

    def _equip_label(self, a):
        if not a.get('equip'):
            return '장비 없음'
        cat = self._catalog()
        name = (cat.get(a['equip']) or {}).get('label', a['equip'])
        return shorten(name, 143 - 2 - 14 - 2 * 2 - 1, 'title')

    def _catalog(self):
        if not getattr(self, '_cat', None):
            self._cat = self.app.call('get_shop_catalog') or {}
        return self._cat

    def _stat_rows(self):
        return [(stat, pygame.Rect(DETAIL.x + 15, STAT_Y0 + i * STAT_STEP, DETAIL.w - 30, 19))
                for i, stat in enumerate(T.STATS)]

    # ---------- 그리기 ----------
    def draw(self, surface):
        self._tip = None
        self.app.backdrop(surface)
        ribbon(surface, (78, 33, 92, 18), '내 동물', 'red')
        self._draw_list(surface)
        panel(surface, DETAIL)
        a = self.app.animal(self.selected)
        if a:
            self._draw_detail(surface, a)
        for b in self.buttons:
            b.draw(surface)
        if self._tip:      # 상태 아이콘 설명 (마우스를 올렸을 때)
            tooltip(surface, self._tip[0], self._tip[1], 'right')

    def _status_icon(self, a):
        """목록 오른쪽 상태 아이콘 (아이콘, 회색 여부, 설명). 표시만, 규칙 아님. 지도 말풍선과 같은 뜻.

        아픔 회색 heart / 훈련 중 sword / 사냥 중 wing / 배고픔 meat / 피곤함 zzz /
        기분 나쁨 frown(회색 찡그린 얼굴) / 그 밖에 쉬어야 함 회색 heart / 건강 heart
        """
        act = a.get('activity') or {}
        left = fmt_time(act.get('end', 0) - self.app.now()) if act else ''
        if a.get('sick'):
            return 'heart', True, '아픔 · 병원에서 치료 필요'
        if act.get('kind') == 'training':
            return 'sword', False, f"훈련 중 · 남은 시간 {left}"
        if act.get('kind') == 'hunting':
            return 'wing', False, f"사냥 나감 · 남은 시간 {left}"
        if T.level(a, 'fullness') == '나쁨':
            return 'meat', False, f"배고픔 · 포만감 {a['fullness']}"
        if T.level(a, 'fatigue') == '나쁨':
            return 'zzz', False, f"피곤함 · 피로도 {a['fatigue']}"
        if T.level(a, 'mood') == '나쁨':
            return 'frown', False, f"기분 나쁨 · 기분 {a['mood']}"
        if not a.get('participation'):
            return 'heart', True, f"휴식 필요 · {a.get('participation_reason') or '상태 확인'}"
        return 'heart', False, '건강함 · 훈련·전투 가능'

    def _draw_list(self, surface):
        panel(surface, LIST)
        animals = self.app.state.get('animals', [])
        yard = set(self.app.state.get('yard', []))
        clip = surface.get_clip()
        surface.set_clip(LIST_INNER)
        for i, a in enumerate(animals):
            r = self._card_rect(i)
            if r.bottom < LIST_INNER.y or r.top > LIST_INNER.bottom:
                continue
            card(surface, r, a['id'] == self.selected)
            surface.blit(self.app.sprites.get(a.get('sprite'), 28), (r.x + 3, r.y + 2))
            inner = card_inner(r)
            right = r.right - 17                                 # 상태 아이콘 자리 앞까지
            if a['id'] in yard:
                right = chip(surface, (r.right - 17 - 2, r.y + 3), '마당', 'green', anchor='topright').x - 2
            # 이름 줄 15 (글자 11 + 여백 4) + 역할 줄 13 (글자 9 + 여백 4) = card 안쪽 28
            text_in(surface, a['name'], (r.x + 31, inner.y, right - r.x - 31, 15), 'title', align='left',
                    tag='list')
            role = T.ROLE_KIT[a['role']]
            text_in(surface, f"{T.ROLE_LABEL[a['role']]} · {a['stage']}단계",
                    (r.x + 31, inner.y + 15, r.right - 17 - r.x - 31, inner.h - 15), 'small', T.shade(role, 1),
                    align='left', tag='list')
            ic, gray, tip = self._status_icon(a)
            spot = pygame.Rect(r.right - 15, r.bottom - 15, 12, 12)
            surface.blit(self._gray_icon(ic) if gray else Kit.icon(ic), spot)
            if spot.inflate(4, 4).collidepoint(mouse_pos()) and LIST_INNER.collidepoint(mouse_pos()):
                self._tip = (tip, spot)
        surface.set_clip(clip)
        # 스크롤 막대
        track = pygame.Rect(LIST_INNER.right - 4, LIST_INNER.y, 4, LIST_INNER.h)
        pygame.draw.rect(surface, T.WOOD[1], track)
        total = max(1, len(animals) * CARD_STEP)
        if total > LIST_INNER.h:
            h = max(12, track.h * LIST_INNER.h // total)
            y = track.y + (track.h - h) * self.scroll // max(1, self._max_scroll())
            pygame.draw.rect(surface, T.WOOD[3], (track.x, y, 4, h))
            pygame.draw.line(surface, T.WOOD[4], (track.x, y), (track.x + 3, y))

    def _gray_icon(self, name):
        img = Kit.icon(name).copy()
        img.fill((150, 150, 150, 255), special_flags=pygame.BLEND_RGBA_MULT)
        return img

    def _draw_detail(self, surface, a):
        # 초상화: 풀밭 위에 3배 크기
        pygame.draw.rect(surface, (206, 230, 176), PORTRAIT)
        pygame.draw.rect(surface, T.INK, PORTRAIT, 1)
        pygame.draw.ellipse(surface, (150, 196, 112), (PORTRAIT.x + 14, PORTRAIT.bottom - 30, PORTRAIT.w - 28, 16))
        img = self.app.sprites.get(a.get('sprite'), 84)
        surface.blit(img, img.get_rect(midbottom=(PORTRAIT.centerx, PORTRAIT.bottom - 2)))

        x = INFO_X
        text(surface, a['name'], (x, 70), 'big', T.TEXT)
        # 칩: 역할 · 속성 · 등급 · 단계 · 성격
        cx = x
        for label, color in ((T.ROLE_LABEL[a['role']], T.ROLE_KIT[a['role']]),
                             (T.ELEMENT_LABEL[a['element']], T.ELEMENT_KIT[a['element']]),
                             ('특급' if a['rarity'] == 'special' else '일반', 'purple' if a['rarity'] == 'special' else 'gray'),
                             (f"{a['stage']}/{a['max_stage']}단계", 'brown'),
                             (T.NATURE_LABEL.get(a['nature'], a['nature']), 'blue')):
            cx = chip(surface, (cx, 88), label, color).right + 3

        auto = self.app.auto.get(a['id'], {})
        act = a.get('activity')
        now = self.app.now()
        if act:
            kind = '훈련 중' if act.get('kind') == 'training' else '사냥 중'
            what = T.STAT_LABEL.get(act.get('stat'), '') if act.get('kind') == 'training' else ''
            line = f"지금: {kind} {what} · 남은 시간 {fmt_time(act.get('end', 0) - now)}"
        else:
            line = f"지금: {auto.get('label', '-')} — {auto.get('reason', '')}"
        # 자율행동 설명은 길면 두 줄 (글자 크기 그대로). 두 줄 자리를 늘 비워 둬서 동물마다 아래 줄이 흔들리지 않게
        info_w = DETAIL.right - 13 - x
        for i, part in enumerate(wrap2(line, info_w, 'body')):
            g = text(surface, part, (x, 104 + i * 13), 'body', T.TEXT_SOFT)
            record(part, g, pygame.Rect(x - 2, g.y - 2, info_w + 4, g.h + 4), 'animal-info')
        if act:
            msg, color = '활동이 끝나면 다시 훈련·전투 가능', T.TEXT_SOFT
        elif a.get('participation'):
            msg, color = '훈련 · 전투 가능', T.OK
        else:
            msg, color = f"휴식 필요: {a.get('participation_reason') or '상태 확인'}", T.BAD
        icon(surface, 'heart', (x, 133))
        text(surface, msg, (x + 15, 139), 'title', color, 'midleft')

        # 상태 3종
        for i, (kind, label, ic) in enumerate((('fullness', '포만감', 'meat'), ('mood', '기분', 'smile'),
                                               ('fatigue', '피로도', 'zzz'))):
            y = 147 + i * 11
            value = a[kind]
            level = T.level(a, kind)
            icon(surface, ic, (x, y - 1))
            text(surface, label, (x + 14, y + 4), 'small', T.TEXT, 'midleft')
            gauge(surface, (364, y, 190, 9), value, 100, T.LEVEL_KIT[level])
            text(surface, f"{value} {level}", (558, y + 4), 'small', T.shade(T.LEVEL_KIT[level], 1), 'midleft')

        # 능력치
        ribbon(surface, (204, 176, 70, 18), '능력치', 'brown')
        text(surface, '줄을 눌러 훈련할 능력치 선택 · 막대 끝 = 이번 단계 MAX', (282, 185), 'small', T.TEXT_SOFT, 'midleft')
        hover = mouse_pos()
        for stat, r in self._stat_rows():
            if stat == self.train_stat:
                card(surface, r, True)
            elif r.collidepoint(hover):
                card(surface, r)
            value, cap = a['stats'][stat], a['caps'][stat]
            eff = a.get('effective_stats', {}).get(stat, value)
            icon(surface, T.STAT_ICON[stat], (r.x + 6, r.y + 3))
            text(surface, T.STAT_LABEL[stat], (r.x + 21, r.centery), 'title', T.TEXT, 'midleft')
            done = value >= cap
            gauge(surface, (282, r.y + 4, 252, 11), value, cap, 'green' if done else T.STAT_KIT[stat])
            extra = f" +{eff - value}" if eff > value else ''
            text(surface, f"{value} / {cap}{' MAX' if done else ''}{extra}", (544, r.centery), 'body',
                 T.OK if done else T.TEXT, 'midleft')

        # 훈련
        if act and act.get('kind') == 'training':
            total = max(1, act.get('end', 0) - act.get('start', 0))
            left = act.get('end', 0) - now
            text(surface, f"{T.STAT_LABEL.get(act.get('stat'), '')} 훈련 중", (206, 285), 'title', T.TEXT)
            text(surface, f"남은 시간 {fmt_time(left)}", (206, 300), 'small', T.TEXT_SOFT)
            gauge(surface, (300, 290, 208, 11), total - left, total, 'green')
        else:
            text(surface, f"{T.STAT_LABEL[self.train_stat]} 훈련", (206, 285), 'title', T.TEXT)
            text(surface, '피로도↑ 포만감↓', (206, 300), 'small', T.TEXT_SOFT)

        if a['stage'] < a['max_stage']:
            ready = all(a['stats'][s] >= a['caps'][s] for s in T.STATS)
            hint = '진화 가능!' if ready else '능력치를 모두 MAX로!'
            text(surface, hint, (479, 334), 'body', T.OK if ready else T.TEXT_SOFT, 'midright')


class EquipOverlay(Overlay):
    """장비 고르기: 가방에 있는 장비 장착 / 지금 장비 해제. 숫자·이름은 get_shop_catalog 값."""
    ROW_H, W = 40, 220

    def __init__(self, app, key, anchor=None):
        self.key = key
        self.catalog = app.call('get_shop_catalog') or {}
        self.app = app
        rows = len(self._rows())
        h = 30 + max(1, rows) * self.ROW_H + 8
        rect = pygame.Rect(0, 0, self.W, h)
        if anchor:          # "장비" 버튼 바로 위, 버튼 가운데에 맞춤
            rect.midbottom = (anchor.centerx, anchor.y - 4)
        else:
            rect.midbottom = (T.WIDTH // 2, 318)
        rect.clamp_ip(pygame.Rect(4, T.HEADER_H + 4, T.WIDTH - 8, T.HEIGHT - T.HEADER_H - 8))   # 화면 밖으로 안 나가게
        super().__init__(app, rect)
        self.buttons = []

    def _rows(self):
        a = self.app.animal(self.key) or {}
        stack = self.app.state.get('inventory', {}).get('stackable', {})
        rows = []
        if a.get('equip'):
            rows.append(('off', a['equip']))
        rows += [('on', k) for k, v in self.catalog.items() if v.get('kind') == 'equip' and stack.get(k, 0) > 0]
        return rows

    def update(self, dt):
        self.buttons = []
        x, w = self.rect.x + 10, self.rect.w - 20
        for i, (mode, item) in enumerate(self._rows()):
            spec = self.catalog.get(item, {})
            sub = f"{T.STAT_LABEL.get(spec.get('stat'), '')} +{spec.get('amount', 0)}"
            r = (x, self.rect.y + 28 + i * self.ROW_H, w, self.ROW_H - 4)
            if mode == 'off':
                self.buttons.append(Button(r, f"해제: {spec.get('label', item)}", lambda: self._equip(None), 'brown',
                                           sub=sub))
            else:
                self.buttons.append(Button(r, f"장착: {spec.get('label', item)}", lambda it=item: self._equip(it),
                                           'blue', sub=sub))

    def _equip(self, item):
        name = self.app.name_of(self.key)
        label = (self.catalog.get(item) or {}).get('label', '')
        msg = f"{T.josa(name, '이')} {T.josa(label, '을')} 장착했다" if item else f"{name} 장비 해제"
        if self.app.act('equip', msg, icon='shield', key=self.key, item=item) is not None:
            self.close()

    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return True
        return False

    def draw(self, surface):
        panel(surface, self.rect)
        text_in(surface, '장비 고르기 · 전투 중 교체 불가', (self.rect.x + 8, self.rect.y + 8, self.rect.w - 16, 16),
                'title', tag='equip')
        if not self.buttons:
            text_in(surface, '가방에 장비 없음 · 상점에서 구매', (self.rect.x + 8, self.rect.y + 30, self.rect.w - 16, 26),
                    'body', T.TEXT_SOFT, tag='equip')
        for b in self.buttons:
            b.draw(surface)
