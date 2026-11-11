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
from .widgets import (text, text_width, text_in, glyph_box, fit_width, record, card, card_inner, chip, icon,
                      moon_icon, SpriteCache)
from .display import setup_window_scale

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
        """알림 자리 (anchor 이름, 논리 좌표). 기본: 상단 바 아래 오른쪽 (왼쪽 위 ◀ 버튼·제목 리본을 피함).
        화면마다 바꿀 수 있다."""
        return 'topright', (T.WIDTH - 8, T.HEADER_H + 4)


class Overlay:
    """화면 위에 뜨는 창 (설정 창, 확인 창 등). 열려 있는 동안 입력은 맨 위 창만 받는다.

    rect 밖을 클릭하거나 ESC를 누르면 닫힌다 (close_outside=False면 밖 클릭은 무시).
    """
    close_outside = True

    def __init__(self, app, rect):
        self.app = app
        self.rect = pygame.Rect(rect)

    def handle(self, event):
        """창 안쪽 입력. 처리했으면 True."""
        return False

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def close(self):
        self.app.close_overlay(self)


TOAST_SECONDS = 3.5
DIM = (24, 16, 24, 120)        # 창이 열렸을 때 뒤 화면을 어둡게


class App:
    def __init__(self, save_path='saves/game.db'):
        setup_window_scale()              # DPI 인식 + 창 배율(정수배). pygame 창을 만들기 전에
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
        self.overlays = []        # 화면 위에 뜬 창들 (맨 뒤가 맨 위)
        self.speed_before_demo = 1  # 시연 모드를 켜기 직전 속도 (끄면 이 속도로 돌아감)
        self._maps = {}
        self._dim = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        self._dim.fill(DIM)
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
        """화면 이동. 앞 화면의 알림은 지운다 (다른 화면까지 남지 않게)."""
        self.toast_item = None
        self.scene = self.scenes[name]
        for k, v in kwargs.items():
            setattr(self.scene, k, v)
        self.scene.enter()

    def open_overlay(self, overlay):
        if hasattr(self.scene, 'hover'):      # 뒤 화면의 마우스 강조·툴팁은 끈다
            self.scene.hover = None
        self.overlays.append(overlay)

    def close_overlay(self, overlay=None):
        if overlay is None and self.overlays:
            overlay = self.overlays[-1]
        if overlay in self.overlays:
            self.overlays.remove(overlay)

    def _handle_overlay(self, event):
        top = self.overlays[-1]
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            top.close()
        elif (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
              and not top.rect.collidepoint(event.pos)):
            if top.close_outside:
                top.close()
        else:
            top.handle(event)

    def toggle_speed(self, target):
        """F5: 보통 ↔ 빠르게(5배), F12: 시연 모드(60배) 켜기 ↔ 켜기 직전 속도로 돌아가기.

        설정 창의 속도 버튼·시연 모드 스위치도 이 함수를 쓴다.
        """
        rate = self.state.get('clock', {}).get('rate', 1) or 1
        if rate == target:          # 끄기
            back = self.speed_before_demo if target == T.SPEED_DEMO else 1
            self._set_speed(back)
        else:                       # 켜기
            if target == T.SPEED_DEMO:
                self.speed_before_demo = rate
            self._set_speed(target)

    def _set_speed(self, rate):
        if rate == 1:
            self.act('set_demo_mode', '시간: 보통 속도', icon='sun', enabled=False)
        else:
            label = '시연 모드 (60배)' if rate == T.SPEED_DEMO else f'빠르게 ({int(rate)}배)'
            self.act('set_demo_mode', f'시간: {label}', icon='sun', enabled=True, rate=rate)

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
        # 상단 바의 작은 칸: 안쪽 17 = 글자 11(쉼표 등 아래로 내려오는 글자 13) + 여백 4 → card 21
        box = pygame.Rect(0, 2, max(158, fit_width(info, extra=14) + 4), 21); box.centerx = T.WIDTH // 2
        card(surface, box)
        inner = card_inner(box)
        w = 14 + glyph_box(info).w
        x = inner.x + (inner.w - w) // 2
        if night:
            surface.blit(moon_icon(), (x, inner.y + 2))
        else:
            icon(surface, 'sun', (x, inner.y + 2))
        g = text_in(surface, info, (x + 14, inner.y, w - 14, inner.h), 'body', log=False)
        record(info, pygame.Rect(x, g.y, w, g.h), inner, 'header')
        if rate >= T.SPEED_DEMO:
            chip(surface, (box.right + 6, box.centery), f'시연 모드 {int(rate)}배', 'red', anchor='midleft')
        coins = f"{self.state.get('coins', 0):,}"
        coin = pygame.Rect(0, 2, max(90, fit_width(coins, 'title', extra=16) + 4), 21)
        coin.right = T.WIDTH - 8
        card(surface, coin)
        inner = card_inner(coin)
        icon(surface, 'coin', (inner.x + 2, inner.y + 2))
        g = text_in(surface, coins, inner, 'title', align='right', log=False)
        record(coins, pygame.Rect(inner.x + 2, g.y, g.right - inner.x - 2, g.h), inner, 'header')

    def draw_toasts(self, surface):
        """알림 1개: card 조각 + 왼쪽 4px 색 막대 + 아이콘 + 글씨. 자리는 화면이 정한다 (toast_anchor)."""
        if self.toast_item and self.toast_item[1] <= time.time():
            self.toast_item = None
        if not self.toast_item:
            return
        msg, _, kind, icon_name = self.toast_item
        # 카드 테두리 2 + 색 막대 4 + 여백 5 + (아이콘 14) + 글씨 + 여백 + 테두리 2
        w = 2 + 4 + 5 + (14 if icon_name else 0) + fit_width(msg) - 2 + 2
        box = pygame.Rect(0, 0, w, 20)
        anchor, pos = self.scene.toast_anchor() if self.scene else Scene.toast_anchor(None)
        setattr(box, anchor, pos)
        card(surface, box)
        color = TOAST_BAR.get(kind, 'orange')
        pygame.draw.rect(surface, T.shade(color, 2), (box.x + 2, box.y + 2, 4, box.h - 4))
        pygame.draw.line(surface, T.shade(color, 3), (box.x + 2, box.y + 2), (box.x + 5, box.y + 2))
        inner = card_inner(box)
        content = pygame.Rect(box.x + 6, inner.y, inner.right - box.x - 6, inner.h)    # 색 막대 오른쪽
        x = box.x + 11
        if icon_name:
            icon(surface, icon_name, (x, inner.y + 2))
        g = text_in(surface, msg, (x + (14 if icon_name else 0), inner.y, glyph_box(msg).w, inner.h), 'body',
                    log=False)
        record(msg, pygame.Rect(x, g.y, g.right - x, g.h), content, 'toast')

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
            elif self.overlays:
                self._handle_overlay(self._to_logical(event))
            else:
                self.scene.handle(self._to_logical(event))
        self._poll_worker()
        self.scene.update(dt)
        for overlay in list(self.overlays):
            overlay.update(dt)
        self.scene.draw(self.screen)
        self.draw_header(self.screen)
        for overlay in self.overlays:         # 창마다 뒤를 한 번씩 어둡게 (위에 뜬 창이 잘 보이게)
            self.screen.blit(self._dim, (0, 0))
            overlay.draw(self.screen)
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
