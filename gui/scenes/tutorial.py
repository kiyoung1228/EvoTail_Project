"""처음 안내 (튜토리얼) 5단계. 지도·내 동물 위에 뜨는 창 (목업 docs/mockups/title/n5_tut_bag.png ~ n8_done.png).

화면을 어둡게 하고 강조 칸만 뚫어 노란 테두리 2줄 + 통통 튀는 화살표, 왼쪽 위 "처음 안내 N / 5", 오른쪽 위 건너뛰기,
테크모 대화 상자(강조 칸이 아래쪽이면 위로). 강조 칸 좌표는 실제 화면에서 가져온다 (숫자 X):
  1 가방 = 지도 menu_rect('bag') / 2 내 동물 = menu_rect('my_animals') → 누르면 내 동물 화면
  3 훈련 버튼 = 내 동물 화면 쉬움·중간·어려움 버튼을 합친 칸 → 지도로 / 4 전투장 = 지도 places['battle'] / 5 마무리
대화 상자나 강조 칸을 누르면 다음 단계, 그 밖은 막음. 끝내거나 건너뛰면 settings.json tutorial_done = true.
"""
import math
import pygame

from .. import theme as T
from .. import guide as G
from ..app import Overlay
from ..widgets import Button

STEPS = (                     # (화면, 강조, 화살표)
    ('map', 'bag', 'left'),
    ('map', 'my_animals', 'left'),
    ('animals', 'train', 'down'),
    ('map', 'battle', 'down'),
    ('map', None, None),
)
SHADE = (10, 8, 20, 150)
DONE_SHADE = (10, 8, 20, 80)
YELLOW = (255, 214, 80)


class TutorialOverlay(Overlay):
    close_outside = False
    dim = False                    # 뒤는 이 창이 직접 어둡게 (강조 칸만 뚫음)

    def __init__(self, app, step=0):
        super().__init__(app, (0, 0, T.WIDTH, T.HEIGHT))
        self.step = step
        self.t = 0.0
        self.dialog = G.Dialog()
        self.skip_btn = Button(G.SKIP_RECT, '건너뛰기', self.finish, 'brown')
        self._say()

    # ---------- 단계 ----------
    def _say(self):
        n = self.app.state.get('training_max_concurrent', 0)
        self.dialog.say(tuple(line.format(n=n) for line in G.TUTORIAL[self.step]))
        self.t = 0.0

    def target(self):
        """지금 단계의 강조 칸 (실제 화면 좌표). 없으면 None."""
        what = STEPS[self.step][1]
        scenes = self.app.scenes
        if what in ('bag', 'my_animals'):
            return scenes['map'].menu_rect(what)
        if what == 'battle':
            return scenes['map'].places['battle']['rect']
        if what == 'train':
            labels = set(T.DIFFICULTY_LABEL.values())
            rects = [b.rect for b in getattr(self.app.scene, 'buttons', []) if b.label in labels]
            return rects[0].unionall(rects[1:]) if rects else None
        return None

    def top(self):
        r = self.target()
        return bool(r and r.bottom > G.BOX_BOTTOM - 12)      # 강조 칸이 아래쪽이면 대화 상자를 위로

    def advance(self):
        if self.step == 1:
            self.app.go('animals')                            # 2 → 3만 화면 이동
        elif self.step == 2:
            self.app.go('map')
        self.step += 1
        if self.step >= len(STEPS):
            self.finish()
        else:
            self._say()

    def finish(self):
        """끝 · 건너뛰기: tutorial_done = true (settings.json), 지도로."""
        self.app.audio.set_tutorial_done(True)
        self.app.close_overlay(self)
        if self.app.scene is not self.app.scenes.get('map'):
            self.app.go('map')

    def close(self):
        """ESC로는 닫지 않음 (건너뛰기 버튼으로)."""

    # ---------- 입력 ----------
    def handle(self, event):
        last = self.step == len(STEPS) - 1
        if not last and self.skip_btn.handle(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            r = self.target()
            if r and r.collidepoint(event.pos):
                self.dialog.shown = self.dialog.total
                self.advance()
            elif self.dialog.rect(self.top()).collidepoint(event.pos):
                if self.dialog.click():
                    self.advance()
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.dialog.click():
                self.advance()
        return True                                   # 그 밖은 막음

    def update(self, dt):
        self.t += dt
        self.dialog.update(dt)

    # ---------- 그리기 ----------
    def draw(self, surface):
        last = self.step == len(STEPS) - 1
        if last:
            shade = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
            shade.fill(DONE_SHADE)
            surface.blit(shade, (0, 0))
            img = G.art().get(G.art().flap(self.t, talk=not self.dialog.done), 3)
            surface.blit(img, (320 - 48, 120))
            for x, y in ((280, 120), (370, 130), (290, 190), (360, 196)):
                if int(self.t * 3 + x) % 3:
                    G.sparkle(surface, x, y)
        else:
            r = self.target()
            shade = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
            shade.fill(SHADE)
            if r:
                pygame.draw.rect(shade, (0, 0, 0, 0), r, border_radius=6)
            surface.blit(shade, (0, 0))
            if r:
                for i in range(2):
                    pygame.draw.rect(surface, YELLOW, r.inflate(4 + 2 * i, 4 + 2 * i), 1, border_radius=7)
                self._arrow(surface, r, STEPS[self.step][2])
            self.skip_btn.draw(surface)
        G.progress(surface, '처음 안내', self.step + 1, len(STEPS))
        self.dialog.draw(surface, top=self.top())

    def _arrow(self, surface, r, kind):
        b = round(3 * math.sin(self.t * math.pi * 2 / 0.6))          # 통통
        if kind == 'left':                                            # 왼쪽에서 오른쪽을 가리킴
            cy = r.centery
            x = r.x - 6 + b
            tip = [(x, cy), (x - 12, cy - 9), (x - 12, cy + 9)]
            body = pygame.Rect(x - 28, cy - 4, 17, 9)
        else:                                                         # 위에서 아래로
            cx = r.centerx
            y = r.y - 6 + b
            tip = [(cx, y), (cx - 9, y - 12), (cx + 9, y - 12)]
            body = pygame.Rect(cx - 4, y - 26, 9, 15)
        pygame.draw.rect(surface, YELLOW, body)
        pygame.draw.rect(surface, T.INK, body, 1)
        pygame.draw.polygon(surface, YELLOW, tip)
        pygame.draw.polygon(surface, T.INK, tip, 1)
