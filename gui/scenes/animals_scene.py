"""집: 내 동물 목록과 상세 정보. 간식 주기, 훈련, 진화를 여기서 한다."""
import pygame

from .. import theme as T
from ..app import Scene
from ..widgets import text, panel, bar, Button

LIST = pygame.Rect(40, 130, 340, 570)
DETAIL = pygame.Rect(400, 72, 840, 628)
CARD_H = 68


def fmt_time(seconds):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m // 60}:{m % 60:02d}:{s:02d}" if m >= 60 else f"{m}:{s:02d}"


class AnimalsScene(Scene):
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

    # ---------- 입력 ----------
    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return
        if event.type == pygame.MOUSEWHEEL and LIST.collidepoint(pygame.mouse.get_pos()):
            max_scroll = max(0, len(self.app.state.get('animals', [])) * CARD_H - LIST.h + 16)
            self.scroll = max(0, min(max_scroll, self.scroll - event.y * 40))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if LIST.collidepoint(event.pos):
                i = (event.pos[1] - LIST.y - 8 + self.scroll) // CARD_H
                animals = self.app.state.get('animals', [])
                if 0 <= i < len(animals):
                    self.selected = animals[i]['id']
            for stat, rect in self._stat_rows():
                if rect.collidepoint(event.pos):
                    self.train_stat = stat

    # ---------- 버튼은 상태에 따라 매 프레임 다시 만든다 ----------
    def update(self, dt):
        app, a = self.app, self.app.animal(self.selected)
        self.buttons = [Button((40, 72, 120, 44), '‹ 지도', lambda: app.go('map'), color=T.INK_SOFT)]
        if not a:
            return
        key = a['id']
        # 마당에 내보내기 / 들여보내기 (세이브에 저장되는 마당 목록)
        yard = list(app.state.get('yard', []))
        yard_max = app.state.get('yard_max') or 0
        if key in yard:
            self.buttons.append(Button((DETAIL.right - 224, DETAIL.y + 16, 200, 40), '마당에서 들여보내기',
                                       lambda: app.act('set_yard_animals', f"{app.name_of(key)}을(를) 들여보냈어요",
                                                       keys=[k for k in yard if k != key]),
                                       size=16, color=(140, 120, 100)))
        else:
            full = len(yard) >= yard_max
            self.buttons.append(Button((DETAIL.right - 224, DETAIL.y + 16, 200, 40),
                                       f'마당이 가득 찼어요 ({len(yard)}/{yard_max})' if full else '마당에 내보내기',
                                       lambda: app.act('set_yard_animals', f"{app.name_of(key)}을(를) 마당에 내보냈어요",
                                                       keys=yard + [key]),
                                       size=16 if not full else 14, color=(96, 168, 90), enabled=not full))
        y = DETAIL.bottom - 70
        snacks = app.state.get('inventory', {}).get('stackable', {}).get('snack', 0)
        busy = a.get('activity') is not None
        self.buttons.append(Button((DETAIL.x + 30, y, 170, 48), f'간식 주기 ({snacks})',
                                   lambda: app.act('use_item', '간식을 줬어요', item='snack', key=key),
                                   color=(236, 150, 92), enabled=snacks > 0 and not busy))
        # 진화
        ready = a['stage'] < a['max_stage'] and all(a['stats'][s] >= a['caps'][s] for s in T.STATS)
        costs = self.rules.get('evolution_cost', {})
        cost = costs.get(a['stage'] + 1, costs.get(str(a['stage'] + 1)))
        if a['stage'] >= a['max_stage']:
            label = '최종 진화'
        else:
            label = f'진화하기 ({cost:,}코인)' if cost else '진화하기'
        self.buttons.append(Button((DETAIL.right - 230, y, 200, 48), label,
                                   lambda: app.act('evolve', lambda d: f"{app.name_of(key)}(으)로 진화!", key=key),
                                   color=(150, 110, 220), enabled=ready and not busy))
        # 훈련
        if busy and a['activity'].get('kind') == 'training':
            self.buttons.append(Button((DETAIL.x + 220, y, 170, 48), '훈련 취소',
                                       lambda: app.act('cancel_training', '훈련을 취소했어요', key=key),
                                       color=T.BAD))
        else:
            bx = DETAIL.x + 250
            for i, diff in enumerate(('easy', 'medium', 'hard')):
                dur, gain, _ = self.rules.get('training', {}).get(diff, (0, 0, 0))
                stat = self.train_stat
                self.buttons.append(Button(
                    (bx + i * 190, DETAIL.y + 462, 178, 50),
                    f'{T.DIFFICULTY_LABEL[diff]} · {dur // 60}분 · +{gain}',
                    lambda d=diff, s=stat: app.act('start_training',
                                                   f"{T.STAT_LABEL[s]} 훈련 시작", key=key, stat=s, difficulty=d),
                    size=16, color=(84, 150, 110),
                    enabled=not busy and a['participation'] and a['stats'][stat] < a['caps'][stat]))

    def _stat_rows(self):
        return [(stat, pygame.Rect(DETAIL.x + 24, DETAIL.y + 286 + i * 40, DETAIL.w - 48, 36))
                for i, stat in enumerate(T.STATS)]

    # ---------- 그리기 ----------
    def draw(self, surface):
        surface.fill(T.BG)
        text(surface, '내 동물', (180, 94), 22, T.INK, bold=True, anchor='midleft')
        self._draw_list(surface)
        panel(surface, DETAIL)
        a = self.app.animal(self.selected)
        if a:
            self._draw_detail(surface, a)
        for b in self.buttons:
            b.draw(surface)

    def _draw_list(self, surface):
        panel(surface, LIST)
        clip = surface.get_clip()
        surface.set_clip(LIST.inflate(-6, -6))
        for i, a in enumerate(self.app.state.get('animals', [])):
            r = pygame.Rect(LIST.x + 8, LIST.y + 8 + i * CARD_H - self.scroll, LIST.w - 16, CARD_H - 6)
            if r.bottom < LIST.y or r.top > LIST.bottom:
                continue
            sel = a['id'] == self.selected
            pygame.draw.rect(surface, (255, 236, 214) if sel else (250, 246, 238), r, border_radius=10)
            if sel:
                pygame.draw.rect(surface, T.ACCENT, r, 2, border_radius=10)
            surface.blit(self.app.sprites.get(a.get('sprite'), 56), (r.x + 4, r.y + 3))
            text(surface, a['name'], (r.x + 68, r.y + 10), 17, T.INK, bold=True)
            role = T.ROLE_LABEL[a['role']]
            text(surface, f"{role} · {a['stage']}단계", (r.x + 68, r.y + 34), 14, T.ROLE_COLOR[a['role']])
            if a['id'] in self.app.state.get('yard', []):
                tag = pygame.Rect(r.right - 70, r.centery - 11, 42, 22)
                pygame.draw.rect(surface, (214, 236, 200), tag, border_radius=11)
                text(surface, '마당', tag.center, 13, (64, 120, 56), bold=True, anchor='center')
            dot = T.OK if a.get('participation') else (T.BAD if a.get('sick') else T.WARN)
            pygame.draw.circle(surface, dot, (r.right - 16, r.centery), 6)
        surface.set_clip(clip)

    def _draw_detail(self, surface, a):
        x, y = DETAIL.x + 24, DETAIL.y + 20
        pygame.draw.rect(surface, (244, 236, 222), (x, y, 200, 200), border_radius=16)
        surface.blit(self.app.sprites.get(a.get('sprite'), 196), (x + 2, y + 2))
        tx = x + 228
        text(surface, a['name'], (tx, y), 32, T.INK, bold=True)
        rarity = '특급' if a['rarity'] == 'special' else '일반'
        tags = (f"{T.ROLE_LABEL[a['role']]} · {T.ELEMENT_LABEL[a['element']]} · {rarity} · "
                f"{a['stage']}단계 / 최대 {a['max_stage']}단계 · 성격 {T.NATURE_LABEL.get(a['nature'], a['nature'])}")
        text(surface, tags, (tx, y + 46), 16, T.ROLE_COLOR[a['role']], bold=True)

        auto = self.app.auto.get(a['id'], {})
        act = a.get('activity')
        if act:
            left = act.get('end', 0) - self.app.state.get('clock', {}).get('timestamp', 0)
            kind = '훈련 중' if act.get('kind') == 'training' else '사냥 중'
            what = T.STAT_LABEL.get(act.get('stat'), '') if act.get('kind') == 'training' else ''
            now_line = f"지금: {kind} {what} · 남은 시간 {fmt_time(left)}"
        else:
            now_line = f"지금: {auto.get('label', '-')} — {auto.get('reason', '')}"
        text(surface, now_line, (tx, y + 76), 16, T.INK)
        if act:
            text(surface, '활동이 끝나면 다시 훈련·전투할 수 있어요', (tx, y + 102), 16, T.INK_SOFT, bold=True)
        elif a.get('participation'):
            text(surface, '훈련·전투 가능', (tx, y + 102), 16, T.OK, bold=True)
        else:
            text(surface, f"쉬어야 해요: {a.get('participation_reason') or '상태 확인'}", (tx, y + 102), 16, T.BAD, bold=True)

        # 상태 3종
        for i, (kind, label) in enumerate((('fullness', '포만감'), ('mood', '기분'), ('fatigue', '피로도'))):
            yy = y + 140 + i * 24
            value = a[kind]
            level = T.status_level(kind, value)
            text(surface, label, (tx, yy), 15, T.INK_SOFT)
            bar(surface, (tx + 70, yy + 4, 300, 12), value, 100, T.LEVEL_COLOR[level])
            text(surface, f"{value} {level}", (tx + 384, yy), 15, T.LEVEL_COLOR[level], bold=True)

        # 능력치: 이 동물의 이번 단계 max 기준 게이지 (진화 진행도)
        text(surface, '능력치  (게이지 = 이번 단계 MAX까지 진행도, 클릭해서 훈련할 능력치 선택)',
             (x, DETAIL.y + 258), 15, T.INK_SOFT)
        for stat, r in self._stat_rows():
            chosen = stat == self.train_stat
            if chosen:
                pygame.draw.rect(surface, (255, 238, 220), r, border_radius=8)
                pygame.draw.rect(surface, T.ACCENT, r, 2, border_radius=8)
            value, cap = a['stats'][stat], a['caps'][stat]
            eff = a.get('effective_stats', {}).get(stat, value)
            text(surface, T.STAT_LABEL[stat], (r.x + 12, r.y + 8), 17, T.INK, bold=True)
            done = value >= cap
            bar(surface, (r.x + 100, r.y + 12, 520, 14), value, cap, T.OK if done else T.ROLE_COLOR[a['role']])
            extra = f" (+장비 {eff - value})" if eff > value else ''
            text(surface, f"{value} / {cap}{' MAX' if done else ''}{extra}", (r.x + 636, r.y + 8), 16,
                 T.OK if done else T.INK)

        ready = all(a['stats'][s] >= a['caps'][s] for s in T.STATS)
        hint = ('모든 능력치가 MAX예요. 진화할 수 있어요!' if ready and a['stage'] < a['max_stage']
                else '위 능력치 줄을 눌러 고르고, 오른쪽 난이도 버튼을 누르세요')
        if act and act.get('kind') == 'training':
            total = max(1, act.get('end', 0) - act.get('start', 0))
            left = act.get('end', 0) - self.app.state.get('clock', {}).get('timestamp', 0)
            text(surface, f"{T.STAT_LABEL.get(act.get('stat'), '')} 훈련 중 · 남은 시간 {fmt_time(left)}",
                 (x, DETAIL.y + 462), 18, T.INK, bold=True)
            bar(surface, (x, DETAIL.y + 496, DETAIL.w - 48, 14), total - left, total, (84, 150, 110))
        else:
            text(surface, f"훈련할 능력치: {T.STAT_LABEL[self.train_stat]}", (x, DETAIL.y + 468), 18, T.INK, bold=True)
            text(surface, hint, (x, DETAIL.y + 520), 14, T.INK_SOFT)
