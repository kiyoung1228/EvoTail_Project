"""Pygame main loop.

멀티스레딩 구조
- 메인 스레드: 이 파일의 루프. 화면 그리기와 입력만 담당.
- 월드 스레드: roc.worker.GameWorker. 게임 시간을 흘려보내고(자율행동, 훈련·사냥 완료,
  날씨) 이벤트 큐에 알림만 넣는다. 화면은 절대 직접 건드리지 않는다.
- 메인 루프는 매 프레임 큐를 확인하고, 알림이 오면 백엔드에서 최신 상태를 다시 읽는다.
게임 규칙은 전부 백엔드에 있고, 화면은 bridge.call(...)로만 읽고 명령한다.

화면 (docs/UI_KIT.md): 모든 장면은 640×360 논리 화면(self.screen)에 그리고,
매 프레임 창(1280×720)에 2배로 붙인다. 마우스 이벤트 좌표는 논리 좌표로 바꿔서 장면에 넘긴다.
"""
import os
import time
import pygame

from roc import GameService
from roc.bridge import GameBridge
from roc.worker import GameWorker
from . import theme as T
from .widgets import text, text_width, card, chip, icon, moon_icon, SpriteCache

EVENT_TEXT = {
    'training_complete': lambda e, n: f"{n(e.get('animal'))} 훈련 완료! {T.STAT_LABEL.get(e.get('stat'), '')} +{e.get('gain', '')}",
    'hunt_complete': lambda e, n: f"{n(e.get('animal'))} 사냥 완료! 사냥터에서 보상을 받으세요",
    'disease': lambda e, n: f"{T.josa(n(e.get('animal')), '이')} 아파요. 병원에 데려가 주세요",
    'evolve': lambda e, n: f"{T.josa(n(e.get('animal')), '으로')} 진화했어요!",
    'hatch': lambda e, n: f"알에서 {T.josa(n(e.get('animal')), '이')} 태어났어요!",
    'crop_ready': lambda e, n: "밭의 작물을 수확할 수 있어요",
    'random_bonus': lambda e, n: f"행운 이벤트! 코인 +{e.get('coins', e.get('amount', ''))}",
    'battle_end': lambda e, n: "전투 승리!" if e.get('win') else "전투 패배...",
}
EVENT_ICON = {'training_complete': 'sword', 'hunt_complete': 'meat', 'disease': 'heart', 'evolve': 'heart',
              'hatch': 'heart', 'crop_ready': 'meat', 'random_bonus': 'coin', 'battle_end': 'sword'}
MOUSE_EVENTS = (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
TOAST_BAR = {'ok': 'green', 'bad': 'red', 'info': 'orange'}


class Scene:
    """화면 하나. handle → update → draw 순서로 매 프레임 불린다. 좌표는 논리 픽셀."""

    def __init__(self, app):
        self.app = app

    def enter(self):
        pass

    def handle(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def toast_anchor(self):
        """알림 자리 (anchor 이름, 논리 좌표). 기본: 상단 바 바로 아래 가운데. 화면마다 바꿀 수 있다."""
        return 'midtop', (T.WIDTH // 2, T.HEADER_H + 4)


TOAST_SECONDS = 3.5


class App:
    def __init__(self, save_path='saves/game.db'):
        pygame.init()
        pygame.display.set_caption('EvoTail')
        self.window = pygame.display.set_mode(T.WINDOW)
        self.screen = pygame.Surface((T.WIDTH, T.HEIGHT))     # 논리 화면
        self.clock = pygame.time.Clock()
        self.sprites = SpriteCache()
        self.game = GameService(save_path)
        self.bridge = GameBridge(self.game)
        self.worker = GameWorker(self.game, interval=1.0)
        self.state = {}
        self.auto = {}
        self.toast_item = None    # (문구, 사라질 시각, 종류 ok/bad/info, 아이콘). 한 번에 1개만
        self._refreshed_at = time.time()
        self.last_seq = None
        self.running = True
        self.scenes = {}
        self.scene = None
        self._maps = {}
        self.refresh()
        self.last_seq = max([e.get('seq', 0) for e in self.call('recent_events') or []], default=0)

    # ---- backend ----
    def call(self, command, **params):
        """bridge 호출. 실패하면 이유를 알림으로 보여주고 None을 돌려준다."""
        res = self.bridge.call(command, **params)
        if not res['ok']:
            self.toast(res['error']['message'], 'bad')
            return None
        return res['data']

    def act(self, command, success=None, icon=None, **params):
        """상태를 바꾸는 명령. 성공하면 최신 상태를 다시 읽는다. icon: 성공 알림 아이콘."""
        data = self.call(command, **params)
        if data is not None:
            if success:
                self.toast(success(data) if callable(success) else success, 'ok', icon)
            self.refresh()
        return data

    def refresh(self):
        self.state = self.call('get_snapshot') or self.state
        self._refreshed_at = time.time()
        self.auto = {a['id']: a for a in (self.call('get_autonomous_state') or [])}

    def animal(self, key):
        return next((a for a in self.state.get('animals', []) if a['id'] == key), None)

    def name_of(self, key):
        a = self.animal(key)
        if a:
            return a['name']
        info = self.game.characters.get(key)
        return info['name'] if info else str(key)

    def now(self):
        """지금 게임 시각 (초). 스냅샷 시각 + 마지막으로 읽은 뒤 흐른 시간 × 배속.

        월드 스레드가 1초마다 상태를 다시 읽게 하지만, 그 사이에도 남은 시간·게이지가
        부드럽게 움직이도록 화면에서만 이어서 계산한다 (시연 모드 60배에서 1분씩 끊기지 않게).
        """
        clock = self.state.get('clock', {})
        elapsed = min(2.0, time.time() - self._refreshed_at)       # 멈춰 있을 때 너무 앞서가지 않게
        return clock.get('timestamp', 0) + elapsed * (clock.get('rate', 1) or 1)

    def toast(self, msg, kind='info', icon_name=None):
        """알림은 한 번에 1개만. 새 알림이 오면 바꿔 끼우고, TOAST_SECONDS 뒤 사라진다."""
        if icon_name is None:
            icon_name = {'ok': 'heart', 'info': 'sun'}.get(kind)
        self.toast_item = (msg, time.time() + TOAST_SECONDS, kind, icon_name)

    # ---- 배경 ----
    def map_image(self, night):
        """지도 그림 (논리 640×360, 원본 1280×720을 ½로. 지도는 2배로 그려져 있어 픽셀이 그대로)."""
        key = ('map', night)
        if key not in self._maps:
            path = os.path.join(T.ROOT, 'assets', 'map', 'map_night.png' if night else 'map_day.png')
            self._maps[key] = pygame.transform.scale(pygame.image.load(path).convert(), (T.WIDTH, T.HEIGHT))
        return self._maps[key]

    def backdrop(self, surface):
        """지도 화면이 아닌 화면의 배경: 지도를 어둡게 (밝기 55%, 채도 70%)."""
        night = bool(self.state.get('clock', {}).get('night'))
        key = ('dim', night)
        if key not in self._maps:
            color = self.map_image(night)
            out = pygame.transform.grayscale(color)
            tinted = color.copy()
            tinted.set_alpha(int(255 * 0.7))       # 색 70% + 회색 30% = 채도 70%
            out.blit(tinted, (0, 0))
            v = int(255 * 0.55)
            out.fill((v, v, v), special_flags=pygame.BLEND_MULT)
            self._maps[key] = out
        surface.blit(self._maps[key], (0, 0))

    # ---- scenes ----
    def register(self, name, scene):
        self.scenes[name] = scene

    def go(self, name, **kwargs):
        self.scene = self.scenes[name]
        for k, v in kwargs.items():
            setattr(self.scene, k, v)
        self.scene.enter()

    def toggle_speed(self, target):
        """F5: 보통 ↔ 빠르게(5배), F12: 보통 ↔ 시연 모드(60배)."""
        rate = self.state.get('clock', {}).get('rate', 1) or 1
        if rate == target:
            self.act('set_demo_mode', '시간: 보통 속도', icon='sun', enabled=False)
        else:
            label = '시연 모드 (60배)' if target == T.SPEED_DEMO else f'빠르게 ({target}배)'
            self.act('set_demo_mode', f'시간: {label}', icon='sun', enabled=True, rate=target)

    # ---- loop ----
    def _poll_worker(self):
        if not self.worker.poll():
            return
        self.refresh()
        events = self.call('recent_events') or []
        for e in events:
            if e.get('seq', 0) > (self.last_seq or 0):
                fmt = EVENT_TEXT.get(e.get('type'))
                if fmt:
                    self.toast(fmt(e, self.name_of), 'info', EVENT_ICON.get(e.get('type')))
        if events:
            self.last_seq = max(e.get('seq', 0) for e in events)

    def draw_header(self, surface):
        """나무 판자 상단 바: 로고 / 시간·날씨 칸 / 코인 칸."""
        h = T.HEADER_H
        pygame.draw.rect(surface, T.WOOD[2], (0, 0, T.WIDTH, h))
        pygame.draw.line(surface, T.WOOD[3], (0, 0), (T.WIDTH, 0))
        pygame.draw.line(surface, T.WOOD[1], (0, h - 2), (T.WIDTH, h - 2))
        pygame.draw.line(surface, T.INK, (0, h - 1), (T.WIDTH, h - 1))
        for x in range(40, T.WIDTH, 40):                       # 40px마다 판자 이음새
            pygame.draw.line(surface, T.WOOD[1], (x, 1), (x, h - 3))
        text(surface, 'EvoTail', (10, h // 2), 'title', T.WHITE, 'midleft', shadow=T.WOOD[0])
        clock = self.state.get('clock', {})
        night = bool(clock.get('night'))
        rate = clock.get('rate', 1.0) or 1.0
        # 목업 순서: "1일차 · 낮 14:20 · 맑음". day·time은 백엔드 clock (PR #6, 1일차 06:00 시작)
        when = f"{'밤' if night else '낮'} {clock['time']}" if clock.get('time') else ('밤' if night else '낮')
        day = f"{clock['day']}일차 · " if clock.get('day') else ''
        info = f"{day}{when} · {'태풍' if clock.get('storm') else '맑음'}"
        if 1 < rate < T.SPEED_DEMO:
            info += f" · {int(rate)}배속"
        box = pygame.Rect(0, 3, max(158, text_width(info) + 30), 19); box.centerx = T.WIDTH // 2
        card(surface, box)
        w = 14 + text_width(info)
        x = box.centerx - w // 2
        if night:
            surface.blit(moon_icon(), (x, box.y + 4))
        else:
            icon(surface, 'sun', (x, box.y + 4))
        text(surface, info, (x + 14, box.centery), 'body', T.TEXT, 'midleft')
        if rate >= T.SPEED_DEMO:
            chip(surface, (box.right + 6, box.centery), f'시연 모드 {int(rate)}배', 'red', anchor='midleft')
        coin = pygame.Rect(T.WIDTH - 98, 3, 90, 19)
        card(surface, coin)
        icon(surface, 'coin', (coin.x + 5, coin.y + 4))
        text(surface, f"{self.state.get('coins', 0):,}", (coin.right - 6, coin.centery), 'title', T.TEXT, 'midright')

    def draw_toasts(self, surface):
        """알림 1개: card 조각 + 왼쪽 4px 색 막대 + 아이콘 + 글씨. 자리는 화면이 정한다 (toast_anchor)."""
        if self.toast_item and self.toast_item[1] <= time.time():
            self.toast_item = None
        if not self.toast_item:
            return
        msg, _, kind, icon_name = self.toast_item
        w = text_width(msg) + 22 + (14 if icon_name else 0)
        box = pygame.Rect(0, 0, w, 20)
        anchor, pos = self.scene.toast_anchor() if self.scene else Scene.toast_anchor(None)
        setattr(box, anchor, pos)
        card(surface, box)
        color = TOAST_BAR.get(kind, 'orange')
        pygame.draw.rect(surface, T.shade(color, 2), (box.x + 2, box.y + 2, 4, box.h - 4))
        pygame.draw.line(surface, T.shade(color, 3), (box.x + 2, box.y + 2), (box.x + 5, box.y + 2))
        x = box.x + 11
        if icon_name:
            icon(surface, icon_name, (x, box.y + 4))
            x += 14
        text(surface, msg, (x, box.centery), 'body', T.TEXT, 'midleft')

    def _to_logical(self, event):
        if event.type in MOUSE_EVENTS:
            d = dict(event.dict)
            d['pos'] = (event.pos[0] // T.SCALE, event.pos[1] // T.SCALE)
            if 'rel' in d:
                d['rel'] = (event.rel[0] // T.SCALE, event.rel[1] // T.SCALE)
            return pygame.event.Event(event.type, d)
        return event

    def step(self, dt):
        """한 프레임: 입력 → 월드 알림 확인 → 갱신 → 논리 화면에 그리기 → 창에 2배로."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_F5, pygame.K_F12):
                self.toggle_speed(T.SPEED_DEMO if event.key == pygame.K_F12 else T.SPEED_FAST)
            else:
                self.scene.handle(self._to_logical(event))
        self._poll_worker()
        self.scene.update(dt)
        self.scene.draw(self.screen)
        self.draw_header(self.screen)
        self.draw_toasts(self.screen)
        pygame.transform.scale(self.screen, T.WINDOW, self.window)
        pygame.display.flip()

    def run(self):
        self.worker.start()
        try:
            while self.running:
                self.step(self.clock.tick(T.FPS) / 1000)
        finally:
            self.worker.stop()
            self.call('save_game')
            pygame.quit()
