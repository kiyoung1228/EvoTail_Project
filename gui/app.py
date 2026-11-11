"""Pygame main loop.

멀티스레딩 구조
- 메인 스레드: 이 파일의 루프. 화면 그리기와 입력만 담당.
- 월드 스레드: roc.worker.GameWorker. 게임 시간을 흘려보내고(자율행동, 훈련·사냥 완료,
  날씨) 이벤트 큐에 알림만 넣는다. 화면은 절대 직접 건드리지 않는다.
- 메인 루프는 매 프레임 큐를 확인하고, 알림이 오면 백엔드에서 최신 상태를 다시 읽는다.
게임 규칙은 전부 백엔드에 있고, 화면은 bridge.call(...)로만 읽고 명령한다.
"""
import time
import pygame

from roc import GameService
from roc.bridge import GameBridge
from roc.worker import GameWorker
from . import theme as T
from .widgets import text, SpriteCache

EVENT_TEXT = {
    'training_complete': lambda e, n: f"{n(e.get('animal'))} 훈련 완료! {T.STAT_LABEL.get(e.get('stat'), '')} +{e.get('gain', '')}",
    'hunt_complete': lambda e, n: f"{n(e.get('animal'))} 사냥 완료! 사냥터에서 보상을 받으세요",
    'disease': lambda e, n: f"{n(e.get('animal'))}이(가) 아파요. 병원에 데려가 주세요",
    'evolve': lambda e, n: f"{n(e.get('animal'))}(으)로 진화했어요!",
    'hatch': lambda e, n: f"알에서 {n(e.get('animal'))}이(가) 태어났어요!",
    'crop_ready': lambda e, n: "밭의 작물을 수확할 수 있어요",
    'random_bonus': lambda e, n: f"행운 이벤트! 코인 +{e.get('coins', e.get('amount', ''))}",
    'battle_end': lambda e, n: "전투 승리!" if e.get('win') else "전투 패배...",
}


class Scene:
    """화면 하나. handle → update → draw 순서로 매 프레임 불린다."""

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


class App:
    def __init__(self, save_path='saves/game.db'):
        pygame.init()
        pygame.display.set_caption('EvoTail')
        self.screen = pygame.display.set_mode((T.WIDTH, T.HEIGHT))
        self.clock = pygame.time.Clock()
        self.sprites = SpriteCache()
        self.game = GameService(save_path)
        self.bridge = GameBridge(self.game)
        self.worker = GameWorker(self.game, interval=1.0)
        self.state = {}
        self.auto = {}
        self.toasts = []          # [(문구, 사라질 시각, 색)]
        self.last_seq = None
        self.running = True
        self.scenes = {}
        self.scene = None
        self.refresh()
        self.last_seq = max([e.get('seq', 0) for e in self.call('recent_events') or []], default=0)

    # ---- backend ----
    def call(self, command, **params):
        """bridge 호출. 실패하면 이유를 토스트로 보여주고 None을 돌려준다."""
        res = self.bridge.call(command, **params)
        if not res['ok']:
            self.toast(res['error']['message'], T.BAD)
            return None
        return res['data']

    def act(self, command, success=None, **params):
        """상태를 바꾸는 명령. 성공하면 최신 상태를 다시 읽는다."""
        data = self.call(command, **params)
        if data is not None:
            if success:
                self.toast(success(data) if callable(success) else success, T.OK)
            self.refresh()
        return data

    def refresh(self):
        self.state = self.call('get_snapshot') or self.state
        self.auto = {a['id']: a for a in (self.call('get_autonomous_state') or [])}

    def animal(self, key):
        return next((a for a in self.state.get('animals', []) if a['id'] == key), None)

    def name_of(self, key):
        a = self.animal(key)
        if a:
            return a['name']
        info = self.game.characters.get(key)
        return info['name'] if info else str(key)

    def toast(self, msg, color=T.INK):
        self.toasts.append((msg, time.time() + 3.5, color))
        self.toasts = self.toasts[-4:]

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
            self.act('set_demo_mode', '시간: 보통 속도', enabled=False)
        else:
            label = '시연 모드 (60배)' if target == T.SPEED_DEMO else f'빠르게 ({target}배)'
            self.act('set_demo_mode', f'시간: {label}', enabled=True, rate=target)

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
                    self.toast(fmt(e, self.name_of), T.ACCENT_DARK)
        if events:
            self.last_seq = max(e.get('seq', 0) for e in events)

    def draw_header(self, surface):
        pygame.draw.rect(surface, (255, 248, 236), (0, 0, T.WIDTH, 52))
        pygame.draw.line(surface, T.PANEL_EDGE, (0, 52), (T.WIDTH, 52), 2)
        text(surface, 'EvoTail', (20, 12), 24, T.ACCENT_DARK, bold=True)
        clock = self.state.get('clock', {})
        night = bool(clock.get('night'))
        when = '밤' if night else '낮'
        weather = '태풍' if clock.get('storm') else '맑음'
        rate = clock.get('rate', 1.0) or 1.0
        # TODO: 목업의 "1일차 · 14:20"(날짜·게임 시각)은 백엔드 clock에 값이 생기면 추가
        info = f"{when} · {weather}" + (f" · {int(rate)}배속" if 1 < rate < T.SPEED_DEMO else '')
        pill = pygame.Rect(0, 0, 290, 36); pill.center = (T.WIDTH // 2, 27)
        pygame.draw.rect(surface, (44, 48, 92) if night else (255, 252, 244), pill, border_radius=18)
        pygame.draw.rect(surface, (30, 32, 64) if night else T.PANEL_EDGE, pill, 2, border_radius=18)
        icon = (pill.x + 26, pill.centery)
        if night:   # 초승달
            pygame.draw.circle(surface, (255, 236, 160), icon, 11)
            pygame.draw.circle(surface, (44, 48, 92), (icon[0] + 6, icon[1] - 4), 10)
        else:       # 해
            pygame.draw.circle(surface, (255, 200, 64), icon, 11)
            pygame.draw.circle(surface, (226, 160, 40), icon, 11, 2)
        text(surface, info, (pill.centerx + 10, pill.centery), 17,
             (255, 255, 255) if night else T.INK, bold=True, anchor='center')
        if rate >= T.SPEED_DEMO:
            badge = pygame.Rect(0, 0, 150, 30); badge.midleft = (pill.right + 14, 27)
            pygame.draw.rect(surface, T.BAD, badge, border_radius=15)
            text(surface, f'시연 모드 {int(rate)}배', badge.center, 15, (255, 255, 255), bold=True, anchor='center')
        coin = pygame.Rect(T.WIDTH - 192, 9, 175, 36)
        pygame.draw.rect(surface, (255, 252, 244), coin, border_radius=18)
        pygame.draw.rect(surface, T.PANEL_EDGE, coin, 2, border_radius=18)
        c = (coin.x + 22, coin.centery)
        pygame.draw.circle(surface, (250, 196, 64), c, 12)
        pygame.draw.circle(surface, (196, 132, 28), c, 12, 2)
        text(surface, 'C', c, 14, (150, 96, 20), bold=True, anchor='center')
        text(surface, f"{self.state.get('coins', 0):,}", (coin.right - 14, coin.centery), 20, T.INK,
             bold=True, anchor='midright')

    def draw_toasts(self, surface):
        now = time.time()
        self.toasts = [t for t in self.toasts if t[1] > now]
        y = 64
        for msg, _, color in reversed(self.toasts):
            img = T.font(17).render(msg, True, (255, 255, 255))
            box = img.get_rect(midtop=(T.WIDTH // 2, y)).inflate(28, 14)
            box.top = y
            pygame.draw.rect(surface, color, box, border_radius=12)
            surface.blit(img, img.get_rect(center=box.center))
            y = box.bottom + 6

    def run(self):
        self.worker.start()
        try:
            while self.running:
                dt = self.clock.tick(T.FPS) / 1000
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN and event.key in (pygame.K_F5, pygame.K_F12):
                        self.toggle_speed(T.SPEED_DEMO if event.key == pygame.K_F12 else T.SPEED_FAST)
                    else:
                        self.scene.handle(event)
                self._poll_worker()
                self.scene.update(dt)
                self.scene.draw(self.screen)
                self.draw_header(self.screen)
                self.draw_toasts(self.screen)
                pygame.display.flip()
        finally:
            self.worker.stop()
            self.call('save_game')
            pygame.quit()
