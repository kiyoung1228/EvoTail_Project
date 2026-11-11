"""전투 화면 (목업 docs/mockups/battle/battle_A*.png, 팀 결정 = A안 + A2_1~3) + 결과 화면.

- 아군 왼쪽, 적 오른쪽. 머리 위엔 체력바만, 이름은 마우스를 올리면. 보스는 크게(원본 46 × 2)
- 아래 명령창: 고른 동물 정보 + 공격 / 특수기(탱커 절대방어·힐러 회복) / 방어 / 턴 넘기기.
  get_battle_actions가 준 행동만 켠다. 딜러의 공격은 백엔드에서 적 전체 공격이라 대상 고르기 없음
- 대상 고르기: 위에 안내 띠 + 꺾쇠(적 빨강, 아군 초록, 마우스 올린 대상 노랑). 회복은 체력바에 미리보기. ESC 취소
- 피해·회복 숫자, 쓰러진 동물 회색, 적 차례는 기록을 0.6초 간격으로 하나씩
- 전투 기록: 작은 칸, 마우스를 올리면 위로 펼침. 도망가기 = forfeit_battle (확인 창)
- 피해 계산 등 규칙은 계산하지 않는다: 체력·피해·회복은 전부 백엔드가 준 값과 기록(events)으로 그린다.
  전투 중 아이템(응급 붕대 battle_bandage)은 "아이템" 버튼 → 목록 → 아군 고르기 (팀 확정: 전투 중 아이템 요구사항).
  get_battle_actions(아이템)의 battle_item 행동만 쓰고, 쓰면 팀 행동 1번(백엔드 use_battle_item)
"""
import random
import time
import pygame

from .. import theme as T
from ..app import Scene
from .. import enemies as E
from ..widgets import (text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, chip_width, icon, tooltip,
                       select_frame, gauge, nine, button_face, Button, mouse_pos, BUTTON_H, CARD_LABEL_H)
from .settings import ConfirmOverlay

ALLY_FEET = [(66, 214), (136, 240), (206, 214)]
ENEMY_FEET = [(434, 214), (504, 240), (574, 214)]
FIELD_BOTTOM = 270
CMD = pygame.Rect(8, 272, 624, 84)
INFO = pygame.Rect(16, 280, 154, 68)
LOG_SMALL = pygame.Rect(478, 280, 146, 68)
LOG_BIG = pygame.Rect(392, 60, 240, 296)
ENEMY_STEP = 0.6                 # 적 차례 기록 간격 (초)
FLOAT_TIME = 0.9

# 회복량 미리보기 (힐러 단계별, CLAUDE.md 규칙 표의 값). 미리보기 표시에만 쓰고, 실제 회복은 백엔드 기록 값.
# TODO: 백엔드 get_battle_actions가 회복량(amount)을 주면 이 표를 지운다 (기영님께 요청)
HEAL_PREVIEW = {1: 100, 2: 300, 3: 500}
# 특수기: 역할 상관없이 보라색 버튼 (방어 버튼 파랑과 헷갈리지 않게)
SPECIAL = {'tank': ('절대방어', 'shield'), 'healer': ('회복', 'heart')}
SPECIAL_NOTE = ('아군 1마리', '쓰면 다음 턴 1번 쉼')      # 버튼 아래 설명 (두 줄)


def cooldown_label(cd):
    """쿨타임 중 특수기 버튼 글씨 (팀 확정: 특수기를 쓰면 다음 자기 팀 턴 1번만 쉼).
    백엔드 cooldown이 0보다 크면 이번 턴엔 못 씀 → 버튼은 회색(disabled)으로 막는다."""
    return '재사용 대기: 1턴'


def shorten(msg, width, kind='small'):
    """width 안에 들어가게 끝을 …으로 줄인다 (글자 크기는 그대로)."""
    if glyph_box(msg, kind).w <= width:
        return msg
    while msg and glyph_box(msg + '…', kind).w > width:
        msg = msg[:-1]
    return msg + '…'


_arena = None


def arena_surface():
    """전투장 배경 (하늘·관중석·벽·깃발·횃불·모래 바닥). 그림 파일이 없어 코드로 그린 도트, 한 번만 만든다."""
    global _arena
    if _arena is not None:
        return _arena
    W, H = T.WIDTH, T.HEIGHT
    s = pygame.Surface((W, H))
    rng = random.Random(7)
    s.fill((150, 206, 240))                                       # 하늘
    for cx, cy, w in ((96, 36, 28), (220, 30, 20), (520, 40, 30)):  # 구름
        pygame.draw.rect(s, (246, 250, 255), (cx, cy, w, 5)); pygame.draw.rect(s, (246, 250, 255), (cx + 6, cy - 3, w - 12, 3))
    # 관중석 (계단 4줄 + 관중 점)
    crowd = [(236, 104, 64), (90, 150, 220), (250, 204, 70), (98, 176, 98), (240, 150, 170), (255, 252, 240)]
    for i, y in enumerate(range(60, 96, 9)):
        pygame.draw.rect(s, (150, 142, 134) if i % 2 else (176, 168, 158), (0, y, W, 9))
        pygame.draw.line(s, (110, 104, 100), (0, y + 8), (W, y + 8))
        for x in range(2 + (i % 2) * 2, W, 4):
            if rng.random() < .8:
                c = rng.choice(crowd)
                pygame.draw.rect(s, c, (x, y + 2, 2, 3))
    # 벽돌 벽
    pygame.draw.rect(s, (128, 124, 132), (0, 96, W, 24))
    for row, y in enumerate(range(96, 120, 6)):
        pygame.draw.line(s, (96, 92, 102), (0, y), (W, y))
        for x in range((row % 2) * 8, W, 16):
            pygame.draw.line(s, (96, 92, 102), (x, y), (x, y + 5))
    pygame.draw.line(s, T.INK, (0, 120), (W, 120))
    # 깃발·횃불
    flags = [(220, 92, 80), (90, 150, 220), (250, 204, 70)]
    for i, x in enumerate(range(46, W, 112)):
        c = flags[i % 3]
        pygame.draw.rect(s, T.INK, (x - 7, 98, 14, 14)); pygame.draw.rect(s, c, (x - 6, 99, 12, 11))
        pygame.draw.polygon(s, c, [(x - 6, 110), (x + 5, 110), (x, 115)]); pygame.draw.lines(s, T.INK, False, [(x - 7, 111), (x, 116), (x + 6, 111)])
        tx = x + 56
        if tx < W:
            pygame.draw.rect(s, (90, 60, 40), (tx - 1, 92, 3, 22))
            pygame.draw.rect(s, (255, 190, 80), (tx - 2, 88, 5, 5)); pygame.draw.rect(s, (255, 236, 160), (tx - 1, 89, 3, 3))
    # 모래 바닥
    pygame.draw.rect(s, (234, 206, 150), (0, 121, W, H - 121))
    for _ in range(900):
        x, y = rng.randrange(W), rng.randrange(122, H)
        s.set_at((x, y), (218, 186, 128) if rng.random() < .7 else (246, 224, 178))
    pygame.draw.line(s, (220, 190, 136), (W // 2, 122), (W // 2, H))
    pygame.draw.ellipse(s, (220, 190, 136), (W // 2 - 190, 168, 380, 120), 1)
    _arena = s
    return s


class BattleScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.fresh = False
        self.view = None
        self.disp_hp = {}
        self.queue = []            # [(재생할 시각, 이벤트, 쪽 'player'|'enemy')]
        self.floats = []           # [(글씨, 색, x, y, 시작 시각)]
        self.log = []              # [(라벨 '1R'|'적'|'', 이벤트)] 글씨는 그릴 때 만든다
        self.selected = None
        self.mode = None           # None | 'attack' | 'special'
        self.actions = []
        self.result = None
        self.banner = None         # 적 차례 재생 중 보여줄 (라운드, '적')
        self.stage = {}
        self.ai_label = ''
        self.buttons = []
        self._tip = None
        self.log_open = False
        self._round_now = 1
        self._done_at = 0.0
        self.log_len = 0
        self.items = {}            # 상점 목록 (get_shop_catalog), 전투 아이템 이름·회복량
        self.item_menu = False     # 아이템 목록이 열려 있는지
        self.item_id = None        # 대상 고르는 중인 아이템
        self.item_actions = []     # get_battle_actions(아이템)이 준 battle_item 행동

    # ---------- 시작 ----------
    def enter(self):
        self.view = self.app.call('get_battle')
        if not self.view:
            self.app.go('battle')
            return
        self.disp_hp = {f['id']: f['hp'] for f in self._fighters()}
        self.queue, self.floats, self.result, self.banner, self.mode = [], [], None, None, None
        self.log_len = len(self.view.get('log', []))
        if self.fresh or not self.log:
            self.log = [('', e) for e in self.view.get('log', []) if self._describe(e)[0]]
        self.fresh = False
        stages = self.app.call('get_stages') or []
        self.stage = next((s for s in stages if s['id'] == self.view.get('stage')), {})
        self.items = self.app.call('get_shop_catalog') or {}
        self.item_menu, self.item_id, self.item_actions = False, None, []
        profiles = self.app.call('get_ai_profiles') or {}
        self.ai_label = profiles.get(self.view.get('ai'), {}).get('strategy', '')
        self.selected = None
        self._pick_next_actor()

    def _fighters(self):
        v = self.view or {}
        return v.get('player', []) + v.get('enemy', [])

    def _fighter(self, fid):
        return next((f for f in self._fighters() if f['id'] == fid), None)

    def _name(self, fid):
        f = self._fighter(fid)
        return f.get('name', fid) if f else fid

    def _busy(self):
        return bool(self.queue) or self.result is not None

    def _pick_next_actor(self):
        mine = [f for f in (self.view or {}).get('player', []) if f['hp'] > 0]
        cur = self._fighter(self.selected)
        if cur and cur['team'] == 'player' and cur['hp'] > 0 and not cur.get('acted'):
            pass
        else:
            nxt = next((f for f in mine if not f.get('acted')), mine[0] if mine else None)
            self.selected = nxt['id'] if nxt else None
        self._load_actions()

    def _load_actions(self):
        if self.selected and self.view and self.view.get('current') == 'player' and not self._busy():
            self.actions = self.app.call('get_battle_actions', actor=self.selected) or []
        else:
            self.actions = []

    # ---------- 기록 → 글씨 ----------
    def _describe(self, e):
        """이벤트 하나 → (기록 글씨, 색). 값은 전부 이벤트에 들어 있는 백엔드 값."""
        n = self._name
        t = e.get('type')
        if t == 'hit':
            extra = (' 치명타!' if e.get('critical') else '') + (' (방어)' if e.get('guarded') else '')
            return f"{n(e['actor'])} → {n(e['target'])} -{e['damage']}{extra}", T.TEXT
        if t == 'blocked':
            return f"{n(e['actor'])} → {n(e['target'])} 막힘 (절대방어)", T.shade('blue', 1)
        if t == 'dodged':
            return f"{n(e['target'])} 피함 ({n(e['actor'])} 공격)", T.TEXT_SOFT
        if t == 'guard':
            return f"{n(e['actor'])} 방어 자세", T.shade('blue', 1)
        if t == 'shield':
            return f"{n(e['actor'])} → {n(e['target'])} 절대방어", T.shade('blue', 1)
        if t == 'heal':
            return f"{n(e['actor'])} → {n(e['target'])} 회복 +{e['amount']}", T.shade('green', 1)
        if t == 'battle_item':
            return f"{self._item_label(e.get('item'))} → {n(e['target'])} 회복 +{e['amount']}", T.shade('green', 1)
        return None, None              # ai_decision 등은 기록에 안 씀

    @staticmethod
    def _short(name):
        """작은 기록 칸용 짧은 이름: "야생 " 빼기."""
        return name[3:] if name.startswith('야생 ') else name

    def _compact(self, e, width):
        """작은 기록 칸 한 줄: "주체 → 대상 숫자". 넓이가 모자라면 이름만 줄이고 화살표·숫자는 남긴다."""
        t = e.get('type')
        a = self._short(self._name(e.get('actor'))) if e.get('actor') else ''
        b = self._short(self._name(e.get('target'))) if e.get('target') else ''
        if t == 'hit':
            tail, color = f"-{e['damage']}" + ('!' if e.get('critical') else ''), T.TEXT
        elif t in ('heal', 'battle_item'):
            tail, color = f"+{e['amount']}", T.shade('green', 1)
            if t == 'battle_item':
                a = self._item_label(e.get('item'))
        elif t == 'blocked':
            tail, color = '막힘', T.shade('blue', 1)
        elif t == 'shield':
            tail, color = '절대방어', T.shade('blue', 1)
        elif t == 'dodged':
            a, b, tail, color = b, '', '피함', T.TEXT_SOFT
        elif t == 'guard':
            b, tail, color = '', '방어', T.shade('blue', 1)
        else:
            return '', T.TEXT

        def build(x, y):
            return f"{x} → {y} {tail}" if y else f"{x} {tail}"
        msg = build(a, b)
        n = max(len(a), len(b))
        while glyph_box(msg, 'small').w > width and n > 1:
            n -= 1
            msg = build(a if len(a) <= n else a[:n] + '…', b if len(b) <= n else b[:n] + '…')
        return msg, color

    # ---------- 이벤트 재생 ----------
    def _queue_events(self, events, side, start_delay=0.0):
        t = time.time() + start_delay
        for e in events:
            if e.get('type') == 'ai_decision':
                continue
            self.queue.append((t, e, side))
            if side == 'enemy':
                t += ENEMY_STEP

    def _apply(self, e, side):
        """재생 시각이 된 이벤트를 화면에 반영 (체력바·숫자·기록)."""
        t = e.get('type')
        target = e.get('target')
        if t == 'hit':
            self.disp_hp[target] = max(0, self.disp_hp.get(target, 0) - e['damage'])
            label = f"-{e['damage']}" + ('!' if e.get('critical') else '')
            self._float(target, label, T.shade('red', 1) if not e.get('critical') else T.shade('orange', 1))
        elif t in ('heal', 'battle_item'):
            f = self._fighter(target)
            mx = f['stats']['hp'] if f else 9999
            self.disp_hp[target] = min(mx, self.disp_hp.get(target, 0) + e['amount'])
            self._float(target, f"+{e['amount']}", T.shade('green', 1))
        elif t == 'blocked':
            self._float(target, '막힘', T.shade('blue', 1))
        elif t == 'dodged':
            self._float(target, '피함', T.TEXT_SOFT)
        elif t == 'guard':
            self._float(e.get('actor'), '방어', T.shade('blue', 1))
        elif t == 'shield':
            self._float(target, '절대방어', T.shade('blue', 1))
        if self._describe(e)[0]:
            label = '적' if side == 'enemy' else f"{self._round_now}R"
            self.log.append((label, e))            # 글씨는 그릴 때 칸에 맞춰 만든다 (작은 칸은 짧게)
            self.log = self.log[-60:]

    def _float(self, fid, msg, color):
        r = self._art_rect(fid)
        if r:
            self.floats.append((msg, color, r.centerx, r.top - 14, time.time()))

    # ---------- 행동 ----------
    def _send(self, command, **params):
        before_round = self.view.get('round', 1)
        res = self.app.call(command, **params)
        if res is None:
            return
        self._round_now = before_round
        battle = res.get('battle')
        result = res.get('result')
        full = (battle or {}).get('log') if battle else (result or {}).get('log', [])
        full = full or []
        new = full[self.log_len:] if len(full) >= self.log_len else full[-len(res.get('events', [])):]
        mine = len(res.get('events', [])) if command == 'battle_action' else 0
        self._queue_events(new[:mine], 'player')
        if len(new) > mine:
            self.banner = before_round
            self._queue_events(new[mine:], 'enemy', start_delay=0.4 if mine else 0.0)
        self.log_len = len(full)
        if battle:
            self.view = battle
        else:
            self.result = result
            self.view = {**self.view, 'current': 'done'}
        self.mode = None
        self.app.refresh()
        if not self.queue:
            self._after_queue()

    def _after_queue(self):
        self.banner = None
        if self.result is not None:
            self.app.go('battle_result', result=self.result, before=getattr(self.app, 'battle_before', {}))
            return
        self.disp_hp = {f['id']: f['hp'] for f in self._fighters()}      # 백엔드 값으로 맞추기
        self.selected = None
        self._pick_next_actor()

    def do_attack(self):
        acts = [a for a in self.actions if a['kind'] == 'attack']
        if not acts:
            return
        if acts[0]['target'] is None:                 # 딜러: 적 전체 공격 (백엔드)
            self._send('battle_action', actor=self.selected, kind='attack', target=None)
        else:
            self.mode = 'attack'

    def do_special(self):
        if any(a['kind'] == 'special' for a in self.actions):
            self.mode = 'special'

    # ---------- 전투 아이템 (응급 붕대 등, 팀 확정: 전투 중 사용) ----------
    def _item_label(self, item):
        label = self.items.get(item, {}).get('label', item or '')
        return label.replace('전투 ', '')                       # '전투 응급 붕대' → '응급 붕대'

    def _battle_items(self):
        """가방에 있는 전투 아이템 [(key, 개수)]. 종류는 상점 목록의 kind == 'battle_item'."""
        inv = self.app.state.get('inventory', {}).get('stackable', {})
        return [(k, inv.get(k, 0)) for k, v in self.items.items() if v.get('kind') == 'battle_item' and inv.get(k, 0) > 0]

    def toggle_items(self):
        self.item_menu = not self.item_menu
        self.mode = None

    def _item_rows(self):
        """아이템 목록 칸 (아이템 버튼 위로 쌓음)."""
        rows = self._battle_items()
        out = []
        for i, (key, n) in enumerate(rows):
            r = pygame.Rect(0, 0, 196, 34)
            r.bottomright = (472, 276 - i * 36)
            out.append((key, n, r))
        return out

    def pick_item(self, key):
        """아이템을 고르면 백엔드가 주는 대상(battle_item 행동)으로 아군 고르기."""
        acts = [a for a in (self.app.call('get_battle_actions', actor=key) or []) if a.get('kind') == 'battle_item']
        self.item_menu = False
        if not acts:
            self.app.toast('지금은 쓸 수 없어요 · 다친 아군이 없거나 행동이 남지 않았어요', 'bad', 'heart')
            return
        self.item_id, self.item_actions, self.mode = key, acts, 'item'

    def do_defend(self):
        if any(a['kind'] == 'defend' for a in self.actions):
            self._send('battle_action', actor=self.selected, kind='defend', target=self.selected)

    def end_turn(self):
        self._send('end_player_turn')

    def ask_forfeit(self):
        self.app.open_overlay(ConfirmOverlay(self.app, '도망갈까요?', '지는 것으로 처리돼요', '도망가기', 'red',
                                             self.forfeit))

    def forfeit(self):
        res = self.app.call('forfeit_battle')
        if res is not None:
            self.app.refresh()
            self.app.go('battle_result', result=res, before=getattr(self.app, 'battle_before', {}))

    def _targets(self):
        if not self.mode:
            return []
        if self.mode == 'item':
            return [a['target'] for a in self.item_actions if a.get('target')]
        return [a['target'] for a in self.actions if a['kind'] == self.mode and a['target']]

    def _heal_preview(self, target):
        """회복 대상 미리보기 양 (실제 회복은 백엔드 기록 값). 아이템은 상점 목록의 heal(백엔드 ITEMS),
        힐러는 HEAL_PREVIEW. 백엔드가 actions에 amount를 주면 그 값으로 바꿀 것."""
        if self.mode == 'item':
            return self.items.get(self.item_id, {}).get('heal', 0)
        healer = self._fighter(self.selected)
        if self.mode == 'special' and healer and healer['role'] == 'healer':
            return HEAL_PREVIEW.get(healer.get('stage', 1), 0)
        return 0

    # ---------- 입력 ----------
    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and (self.mode or self.item_menu):
            self.mode, self.item_menu = None, False
            return
        if self._busy():
            if self.buttons and self.buttons[0].handle(event):       # 도망가기는 언제나
                return
            return
        if self.item_menu and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, n, r in self._item_rows():
                if r.collidepoint(event.pos):
                    self.pick_item(key)
                    return
            if not any(b.label.startswith('아이템') and b.rect.collidepoint(event.pos) for b in self.buttons):
                self.item_menu = False                          # 목록 밖을 누르면 닫기
                return
        for b in self.buttons:
            if b.handle(event):
                return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and (self.mode or self.item_menu):
            self.mode, self.item_menu = None, False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        hit = self._fighter_at(event.pos)
        if self.mode:
            if hit and hit in self._targets():
                if self.mode == 'item':
                    self._send('battle_action', actor=self.item_id, kind='battle_item', target=hit)
                else:
                    self._send('battle_action', actor=self.selected, kind=self.mode, target=hit)
            return
        f = self._fighter(hit) if hit else None
        if f and f['team'] == 'player' and f['hp'] > 0:
            self.selected = hit
            self._load_actions()

    # ---------- 배치 ----------
    def _sprite(self, f):
        if f['team'] == 'enemy':
            _, sprite, _ = E.enemy_look(self.app.sprites, f)
            return self.app.sprites.scaled(sprite, 2)
        return self.app.sprites.get(f.get('sprite'), 56)

    def _feet(self, f):
        side = (self.view or {}).get('player' if f['team'] == 'player' else 'enemy', [])
        i = next((k for k, x in enumerate(side) if x['id'] == f['id']), 0)
        return (ALLY_FEET if f['team'] == 'player' else ENEMY_FEET)[min(i, 2)]

    def _pose(self, f):
        img = self._sprite(f)
        art = img.get_bounding_rect()
        fx, fy = self._feet(f)
        return img, (fx - art.centerx, fy - art.bottom)

    def _art_rect(self, fid):
        f = self._fighter(fid)
        if not f:
            return None
        img, pos = self._pose(f)
        return img.get_bounding_rect().move(pos)

    def _bar_rect(self, fid):
        """머리 위 체력바 자리."""
        art = self._art_rect(fid)
        return pygame.Rect(art.centerx - 22, art.top - 11, 44, 8) if art else None

    def _fighter_at(self, pos):
        best = None
        for f in self._fighters():
            r = self._art_rect(f['id'])
            if r and r.inflate(8, 8).collidepoint(pos):
                best = f['id']
        return best

    # ---------- 갱신 ----------
    def update(self, dt):
        now = time.time()
        while self.queue and self.queue[0][0] <= now:
            _, e, side = self.queue.pop(0)
            self._apply(e, side)
            if not self.queue:
                self._done_at = now
        if not self.queue and (self.banner is not None or self.result is not None) and \
                now - getattr(self, '_done_at', 0) > 0.5:
            self._after_queue()
            if self.app.scene is not self:
                return
        self.floats = [x for x in self.floats if now - x[4] < FLOAT_TIME]
        self._make_buttons()

    def _make_buttons(self):
        app = self
        busy = self._busy() or (self.view or {}).get('current') != 'player'
        f = self._fighter(self.selected)
        kinds = {a['kind'] for a in self.actions}
        role = f.get('role') if f else None
        flee_w = Button.width_for('도망가기', icon=True)
        btns = [Button((8, 32, flee_w, BUTTON_H), '도망가기', self.ask_forfeit, 'brown', icon='back')]
        atk_label = '공격'
        btns.append(Button((178, 280, 94, 26), atk_label, self.do_attack, 'orange',
                           enabled=not busy and 'attack' in kinds, icon='sword'))
        btns.append(Button((178, 314, 94, 26), '방어', self.do_defend, 'blue',
                           enabled=not busy and 'defend' in kinds, icon='shield'))
        if role in SPECIAL:
            name, ic = SPECIAL[role]
            if role == 'healer':
                name = f"회복 +{HEAL_PREVIEW.get(f.get('stage', 1), '')}"
            cd = f.get('cooldown', 0) if f else 0
            label = cooldown_label(cd) if cd > 0 else name          # 쿨타임이면 회색(disabled) + 재사용 대기
            btns.append(Button((276, 280, 112, 26), label, self.do_special, 'purple',
                               enabled=not busy and cd == 0 and 'special' in kinds, icon=None if cd > 0 else ic))
        # 아이템: 가방에 전투 아이템이 있을 때만 켜기, 개수 표시. 쓰면 팀 행동 1번 (백엔드 use_battle_item)
        total = sum(n for _, n in self._battle_items())
        btns.append(Button((392, 280, 80, 26), f'아이템 {total}', self.toggle_items, 'green',
                           enabled=not busy and total > 0, icon='snack'))
        btns.append(Button((392, 314, 80, 26), '턴 넘기기', self.end_turn, 'brown', enabled=not busy))
        self.buttons = btns

    # ---------- 그리기 ----------
    def toast_anchor(self):
        """전투: 명령창 바로 위 가운데 (위쪽 라운드 리본·안내 띠, 동물 발밑 칩을 피함)."""
        return 'midbottom', (T.WIDTH // 2, CMD.y - 3)

    def draw(self, surface):
        self._tip = None
        surface.blit(arena_surface(), (0, 0))
        hover = mouse_pos()
        targets = self._targets()
        hover_id = self._fighter_at(hover) if not self.log_open else None
        for f in sorted(self._fighters(), key=lambda f: self._feet(f)[1]):
            self._draw_fighter(surface, f, targets, hover_id)
        self._draw_top(surface)
        if self.mode:
            self._draw_hint(surface)
        self._draw_floats(surface)
        self._draw_command(surface)
        for b in self.buttons:
            b.draw(surface)
        if self.item_menu:
            self._draw_item_menu(surface, hover)
        self.log_open = LOG_SMALL.collidepoint(hover) or (self.log_open and LOG_BIG.collidepoint(hover))
        if self.log_open:
            self._draw_log_big(surface)
        if self._tip:
            # 다른 동물 체력바를 가리면 반대쪽(아래)으로
            msg, target, side = self._tip
            bars = [self._bar_rect(f['id']) for f in self._fighters()]
            bars = [b for b in bars if b and not b.colliderect(pygame.Rect(target).inflate(0, 30))]
            tooltip(surface, msg, target, side, bounds=(0, T.HEADER_H, T.WIDTH, FIELD_BOTTOM - T.HEADER_H), avoid=bars)

    def _draw_fighter(self, surface, f, targets, hover_id):
        img, pos = self._pose(f)
        hp = self.disp_hp.get(f['id'], f['hp'])
        down = hp <= 0
        art = img.get_bounding_rect().move(pos)
        fx, fy = self._feet(f)
        shadow = pygame.Rect(0, 0, max(28, art.w - 10), 8); shadow.center = (fx, fy)
        pygame.draw.ellipse(surface, (212, 180, 124), shadow)
        if down:                                           # 쓰러짐: 회색
            g = pygame.transform.grayscale(img); g.set_alpha(170)
            surface.blit(g, pos)
        else:
            surface.blit(img, pos)
        mx = f['stats']['hp']
        bar = pygame.Rect(art.centerx - 22, art.top - 11, 44, 8)
        ratio = hp / mx if mx else 0
        color = 'green' if ratio > .5 else ('orange' if ratio > .25 else 'red')
        preview = self._heal_preview(f['id']) if f['id'] == hover_id and f['id'] in targets else 0
        if preview:                                    # 회복 대상: 회복 뒤 체력을 옅게 + "+N"
            gain = min(preview, mx - hp)
            gauge(surface, bar, hp + gain, mx, 'green')
            inner = bar.inflate(-4, -4)
            w0 = int(inner.w * max(0, hp) / mx)
            pygame.draw.rect(surface, T.shade('green', 3), (inner.x + w0, inner.y, int(inner.w * (hp + gain) / mx) - w0, inner.h))
            pygame.draw.rect(surface, T.shade(color, 2), (inner.x, inner.y, w0, inner.h))
            text_in(surface, f'+{gain}', (art.centerx - 30, bar.y - 18, 60, 16), 'title', T.shade('green', 1),
                    shadow=T.WHITE, log=False)
        else:
            gauge(surface, bar, hp, mx, color)
        if down:
            text_in(surface, 'KO', (art.centerx - 20, bar.y - 18, 40, 16), 'title', T.shade('red', 1), shadow=T.WHITE,
                    log=False)
        # 상태 칩 (발 아래)
        chips = []
        if f.get('shield'):
            chips.append(('절대방어', 'blue'))
        if f.get('guard'):
            chips.append(('방어', 'blue'))
        if f.get('cooldown', 0) > 0 and not down:
            chips.append(('기술 쉼', 'gray'))
        if f['team'] == 'player' and f.get('acted') and not down and self.view.get('current') == 'player':
            chips.append(('행동 완료', 'gray'))
        total = sum(chip_width(c) for c, _ in chips) + 2 * max(0, len(chips) - 1)
        x = fx - total // 2
        for label, c in chips:
            x = chip(surface, (x, fy + 6), label, c).right + 2
        # 꺾쇠: 고른 동물 노랑 / 대상 적 빨강·아군 초록 / 마우스 올린 대상 노랑
        frame = art.inflate(16, 16)
        if f['id'] in targets:
            select_frame(surface, frame, None if f['id'] == hover_id else ('red' if f['team'] == 'enemy' else 'green'))
        elif f['id'] == self.selected and not self.mode and not self._busy():
            select_frame(surface, frame)
        if f['id'] == hover_id and not self.mode:
            role = T.ROLE_LABEL.get(f.get('role'), '')
            self._tip = (f"{f.get('name', '')} · {role} · 체력 {hp} / {mx}", art, 'above')
        elif f['id'] == hover_id and self.mode == 'attack' and f['id'] in targets:
            self._tip = (f"{f.get('name', '')} · 체력 {hp} / {mx}", art, 'below')      # 회복은 체력바 미리보기로 대신

    def _draw_top(self, surface):
        v = self.view or {}
        enemy_turn = self.banner is not None
        rnd = self.banner if enemy_turn else v.get('round', 1)
        label = f"{rnd}라운드 · {'적 차례' if enemy_turn else '내 차례'}"
        w = fit_width(label, 'title', shadow=True) + 18
        rb = pygame.Rect(0, 32, w, 18); rb.centerx = T.WIDTH // 2 - 20
        ribbon(surface, rb, label, 'brown' if enemy_turn else 'red')
        # 행동 칸: 쓴 행동 / 이번 턴 행동 수 (살아 있는 동물 수와 2 중 작은 값, 표시용)
        if not enemy_turn and v.get('current') == 'player':
            alive = sum(1 for f in v.get('player', []) if f['hp'] > 0)
            total, used = min(2, alive), v.get('actions', 0)
            x = rb.right + 8
            text_in(surface, '행동', (x, 33, 26, 16), 'small', T.TEXT, align='left', pad=0, log=False)
            x += 26
            for i in range(total):
                c = T.WOOD[0] if i < used else T.shade('orange', 2)
                pygame.draw.rect(surface, T.INK, (x, 37, 9, 9)); pygame.draw.rect(surface, c, (x + 1, 38, 7, 7))
                x += 11
            text_in(surface, f'{total - used}/{total} 남음', (x + 2, 33, 60, 16), 'small', T.TEXT, align='left', pad=0,
                    log=False)
        st = self.stage
        info = f"{st.get('label', '')}{' 대회' if st.get('mode') == 'rank' else ''} · 전투력 {st.get('power', '')}"
        text_in(surface, info, (T.WIDTH - 200, 33, 192, 16), 'small', T.TEXT, align='right', pad=0, log=False)

    def _draw_hint(self, surface):
        healer = (self._fighter(self.selected) or {}).get('role') == 'healer'
        if self.mode == 'attack':
            msg, ic = '공격할 적을 누르세요 · 취소는 ESC', 'sword'
        elif self.mode == 'item':
            msg, ic = f"{T.josa(self._item_label(self.item_id), '을')} 쓸 아군을 누르세요 · 취소는 ESC", 'heart'
        elif healer:
            msg, ic = '회복할 아군을 누르세요 · 취소는 ESC', 'heart'
        else:
            msg, ic = '절대방어할 아군을 누르세요 · 취소는 ESC', 'shield'
        w = fit_width(msg, extra=16) + 4
        box = pygame.Rect(0, 56, w, CARD_LABEL_H); box.centerx = T.WIDTH // 2
        card(surface, box)
        inner = card_inner(box)
        g = glyph_box(msg)
        x = inner.x + (inner.w - g.w - 16) // 2
        icon(surface, ic, (x, inner.y + 2))
        text_in(surface, msg, (x + 16, inner.y, g.w, inner.h), 'body', log=False)

    def _draw_item_menu(self, surface, hover):
        """전투 아이템 목록: 이름 ×개수 / 회복량 · 팀 행동 1번 사용 (백엔드 동작)."""
        for key, n, r in self._item_rows():
            card(surface, r, r.collidepoint(hover))
            inner = card_inner(r)
            spec = self.items.get(key, {})
            icon(surface, 'heart', (inner.x + 2, inner.y + 2))
            text_in(surface, f"{self._item_label(key)} ×{n}", (inner.x + 16, inner.y, inner.w - 16, 15), 'title',
                    align='left', pad=0, check=inner, tag='battle_item')
            text_in(surface, f"체력 +{spec.get('heal', '')} · 팀 행동 1번 사용", (inner.x + 16, inner.y + 15,
                    inner.w - 16, 13), 'small', T.TEXT_SOFT, align='left', pad=0, check=inner, tag='battle_item')

    def _draw_floats(self, surface):
        now = time.time()
        for msg, color, x, y, t0 in self.floats:
            k = (now - t0) / FLOAT_TIME
            g = glyph_box(msg, 'title')
            box = pygame.Rect(0, 0, g.w + 6, 16); box.midbottom = (x, int(y - 12 * k))
            text_in(surface, msg, box, 'title', color, shadow=T.WHITE, log=False)

    def _draw_command(self, surface):
        panel(surface, CMD)
        f = self._fighter(self.selected)
        card(surface, INFO, True)
        if f:
            inner = card_inner(INFO)
            surface.blit(self.app.sprites.get(f.get('sprite'), 28), (inner.x + 1, inner.y + 1))
            text_in(surface, f.get('name', ''), (inner.x + 32, inner.y, inner.w - 32, 15), 'title', align='left', pad=0,
                    check=inner, tag='battle')
            x = inner.x + 32
            role, el = f.get('role'), f.get('element')
            x = chip(surface, (x, inner.y + 15), T.ROLE_LABEL.get(role, ''), T.ROLE_KIT.get(role, 'gray')).right + 2
            chip(surface, (x, inner.y + 15), T.ELEMENT_LABEL.get(el, ''), T.ELEMENT_KIT.get(el, 'gray'))
            hp, mx = self.disp_hp.get(f['id'], f['hp']), f['stats']['hp']
            gauge(surface, (inner.x + 2, inner.y + 35, inner.w - 36, 9), hp, mx,
                  'green' if hp / mx > .5 else ('orange' if hp / mx > .25 else 'red'))
            text_in(surface, str(hp), (inner.right - 32, inner.y + 31, 32, 15), 'small', align='right', pad=2,
                    check=inner, tag='battle')
            st = f['stats']
            text_in(surface, f"공 {st['attack']} · 방 {st['defense']} · 민 {st['agility']}",
                    (inner.x + 2, inner.y + 46, inner.w - 4, 14), 'small', T.TEXT_SOFT, align='left', pad=0,
                    check=inner, tag='battle')
            note = SPECIAL_NOTE if role in SPECIAL else ('딜러 공격은', '적 전체에') if role == 'dealer' else ()
            for i, line in enumerate(note):
                text_in(surface, line, (278, 312 + i * 13, 110, 13), 'small', T.TEXT_SOFT, align='left', pad=0,
                        log=False)
        # 작은 기록 칸
        card(surface, LOG_SMALL)
        inner = card_inner(LOG_SMALL)
        text_in(surface, '전투 기록', (inner.x + 2, inner.y, 60, 15), 'title', align='left', pad=0, check=inner,
                tag='battle')
        text_in(surface, '자세히 ▲', (inner.x + 62, inner.y, inner.w - 62, 15), 'small', T.TEXT_SOFT, align='right',
                pad=2, check=inner, tag='battle')
        for i, (label, e) in enumerate(self.log[-3:]):
            msg, color = self._compact(e, inner.w - 6)
            text_in(surface, msg, (inner.x + 2, inner.y + 16 + i * 15, inner.w - 4, 15), 'small', color, align='left',
                    pad=0, log=False)

    def _draw_log_big(self, surface):
        R = LOG_BIG
        panel(surface, R)
        text_in(surface, '전투 기록', (R.x + 12, R.y + 10, 80, 16), 'title', align='left', pad=0, log=False)
        text_in(surface, self.ai_label, (R.x + 90, R.y + 10, R.w - 102, 16), 'small', T.TEXT_SOFT, align='right',
                pad=0, log=False)
        pygame.draw.line(surface, T.WOOD[3], (R.x + 10, R.y + 30), (R.right - 11, R.y + 30))
        rows = (R.h - 44) // 17
        lines = self.log[-rows:]
        for i, (label, e) in enumerate(lines):
            line, color = self._describe(e)
            y = R.y + 36 + i * 17
            if i % 2:
                pygame.draw.rect(surface, (244, 230, 200), (R.x + 9, y - 1, R.w - 18, 17))
            x = R.x + 12
            if label:
                x = chip(surface, (x, y), label, 'brown' if label != '적' else 'gray').right + 4
            text_in(surface, shorten(line, R.right - 14 - x), (x, y, R.right - 12 - x, 15), 'small', color,
                    align='left', pad=0, log=False)


# ======================================================================
class BattleResultScene(Scene):
    """결과: 승/패, 보상 코인, 첫 대회 우승·다음 단계 열림, 피로도 변화. 값은 백엔드 결과(battle_result)와 스냅샷."""
    W = 320
    ROW = 33

    def __init__(self, app):
        super().__init__(app)
        self.result = None
        self.before = {}
        self.buttons = []
        self.PANEL = pygame.Rect(0, 0, self.W, 200)

    def toast_anchor(self):
        """결과 화면: 왼쪽 위 (가운데 결과 리본을 가리지 않게)."""
        return 'topleft', (8, T.HEADER_H + 4)

    def enter(self):
        self.result = self.result or self.app.call('get_last_battle_result') or {}
        stages = sorted(self.app.call('get_stages') or [], key=lambda s: s.get('order', 0))
        self.stage = next((s for s in stages if s['id'] == self.result.get('stage')), {})
        r = self.result
        self.first = bool(r.get('win') and r.get('first_clear'))
        # 처음 깼으면 다음 단계 (백엔드가 방금 연 단계: order + 1, unlocked)
        nxt = next((s for s in stages if s.get('order') == self.stage.get('order', -9) + 1 and s.get('unlocked')), None)
        self.next_stage = nxt if self.first else None
        self.team = [k for k in (list(self.before.keys()) or list(self.app.state.get('last_team') or []))
                     if self.app.animal(k)][:3]
        # 패널 높이 = 들어가는 것만큼 (아래 빈 곳 없이)
        h = 20 + 24                                    # 리본 아래 여백 + 제목 줄
        h += (26 if self.first else 0) + (20 if self.next_stage else 0)
        h += 30 + 18 + self.ROW * len(self.team) + 8 + 26 + 14
        self.PANEL = pygame.Rect(0, 0, self.W, h)
        self.PANEL.center = (T.WIDTH // 2, T.HEADER_H + (T.HEIGHT - T.HEADER_H) // 2 + 4)
        P = self.PANEL
        bw = (P.w - 40) // 2
        self.buttons = [
            Button((P.x + 16, P.bottom - 40, bw, 26), '전투장으로', lambda: self.app.go('battle'), 'brown', icon='sword'),
            Button((P.x + 24 + bw, P.bottom - 40, bw, 26), '지도로', lambda: self.app.go('map'), 'green', icon='home'),
        ]

    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return

    def draw(self, surface):
        surface.blit(arena_surface(), (0, 0))
        dim = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA); dim.fill((24, 16, 24, 110))
        surface.blit(dim, (0, 0))
        P = self.PANEL
        panel(surface, P)
        r = self.result
        win = r.get('win')
        title = '승리!' if win else '패배…'
        rb = pygame.Rect(0, P.y - 6, fit_width(title, 'title', shadow=True) + 40, 18); rb.centerx = P.centerx   # 리본은 높이 18
        ribbon(surface, rb, title, 'green' if win else 'red')
        st = self.stage
        name = f"{st.get('label', '')}{' 대회' if st.get('mode') == 'rank' else ''}"
        text_in(surface, f"{name} · {r.get('rounds', 1)}라운드", (P.x, P.y + 20, P.w, 18), 'big', log=False)
        y = P.y + 44
        # 첫 대회 우승 / 처음 깸 + 다음 단계 열림
        if self.first:
            msg = '첫 대회 우승!' if st.get('mode') == 'rank' else '처음 깼어요!'
            cw = fit_width(msg, 'title', shadow=True) + 10
            box = pygame.Rect(0, y, cw, 20); box.centerx = P.centerx
            nine(surface, 'button_orange_normal', box)
            text_in(surface, msg, button_face(box), 'title', T.WHITE, shadow=T.shade('orange', 0), tag='result')
            y += 26
        if self.next_stage:
            ns = self.next_stage
            label = f"다음 단계 열림: {ns['label']}{' 대회' if ns.get('mode') == 'rank' else ''}"
            text_in(surface, label, (P.x, y, P.w, 16), 'title', T.OK, log=False)
            y += 20
        # 보상
        reward = r.get('reward', 0)
        box = pygame.Rect(P.x + 40, y, P.w - 80, 22)
        card(surface, box)
        inner = card_inner(box)
        msg = f"보상 +{reward:,} 코인" if reward else '보상 없음'
        g = glyph_box(msg, 'title')
        x = inner.x + (inner.w - g.w - 14) // 2
        icon(surface, 'coin', (x, inner.y + 3))
        text_in(surface, msg, (x + 14, inner.y, g.w + 1, inner.h), 'title', log=False)
        y += 30
        # 팀 피로도 변화 (전투 전 스냅샷 → 지금 스냅샷, 둘 다 백엔드 값)
        text_in(surface, '내 팀', (P.x + 20, y, 60, 16), 'title', align='left', pad=0, log=False)
        y += 18
        for key in self.team:
            a = self.app.animal(key)
            row = pygame.Rect(P.x + 20, y, P.w - 40, 30)
            card(surface, row)
            inner = card_inner(row)
            surface.blit(self.app.sprites.get(a.get('sprite'), 28), (inner.x, inner.y - 1))
            text_in(surface, a['name'], (inner.x + 32, inner.y, 90, inner.h), 'title', align='left', pad=0, check=inner,
                    tag='result')
            before = self.before.get(key)
            after = a['fatigue']
            if before is not None:
                diff = after - before
                msg = f"피로도 {before} → {after} ({'+' if diff >= 0 else ''}{diff})"
            else:
                msg = f"피로도 {after}"
            lvl = T.level(a, 'fatigue')
            text_in(surface, msg, (inner.x + 124, inner.y, inner.w - 124 - (34 if a.get('sick') else 0), inner.h),
                    'small', T.shade(T.LEVEL_KIT[lvl], 1), align='left', pad=0, check=inner, tag='result')
            if a.get('sick'):
                chip(surface, (inner.right, inner.centery), '아픔', 'gray', anchor='midright')
            y += self.ROW
        for b in self.buttons:
            b.draw(surface)
