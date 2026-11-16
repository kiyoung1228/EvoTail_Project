"""처음 안내 (튜토리얼) 5단계. 지도·내 동물 위에 뜨는 창 (목업 docs/mockups/title/n5_tut_bag.png ~ n8_done.png).

화면을 어둡게 하고 강조 칸만 뚫어 노란 테두리 2줄 + 통통 튀는 화살표, 테크모 대화 상자(강조 칸이 아래쪽이면 위로).
"처음 안내 N / 5" 진행 칸과 건너뛰기는 대화 상자 안 오른쪽 위 (이름 칩과 같은 줄, 진행 칸 → 건너뛰기), 상자가 위든 아래든 같은 자리. 강조 칸 좌표는 실제 화면에서 가져온다 (숫자 X):
  1 가방 = 지도 menu_rect('bag') / 2 내 동물 = menu_rect('my_animals') → 누르면 내 동물 화면
  3 훈련 버튼 = 내 동물 화면 쉬움·중간·어려움 버튼을 합친 칸 → 지도로 / 4 전투장 = 지도 places['battle'] / 5 마무리
대화 상자나 강조 칸을 누르면 다음 단계, 그 밖은 막음. 끝내거나 건너뛰면 settings.json tutorial_done = true.
"""
import math
import pygame

from . import map_scene as M

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
YELLOW = (255, 214, 80)
PROGRESS = '처음 안내'
DONE_SCALE = 3                 # 마무리 큰 테크모 (원본 ×3)


class TutorialOverlay(Overlay):
    close_outside = False
    dim = False                    # 뒤는 이 창이 직접 어둡게 (강조 칸만 뚫음)

    def __init__(self, app, step=0):
        super().__init__(app, (0, 0, T.WIDTH, T.HEIGHT))
        self.step = step
        self.t = 0.0
        self.dialog = G.Dialog()
        self.skip_btn = Button(G.SKIP_RECT, '건너뛰기', self.finish, 'brown')
        self._done_pos = None
        self._say()
        self.layout()

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

    def layout(self):
        """대화 상자 안 오른쪽 위: 진행 칸 → 건너뛰기 (이름 칩과 같은 줄). (진행 칸 왼쪽 위, 건너뛰기 rect)."""
        r = self.dialog.rect(self.top())
        skip = pygame.Rect(r.right - 12 - G.SKIP_RECT.w, r.y + 6, G.SKIP_RECT.w, G.SKIP_RECT.h)
        self.skip_btn.rect = skip
        last = self.step == len(STEPS) - 1
        right = r.right - 12 if last else skip.x - 6               # 마무리는 건너뛰기 없이 진행 칸만
        return (right - G.progress_width(PROGRESS, len(STEPS)), r.y + 5), skip

    def done_rect(self):
        """마무리 큰 테크모 자리: 마당·장소 이름표·오른쪽 메뉴·대화 상자·상단 바와 겹치지 않는 곳 중
        마당 위쪽 가운데에 가장 가까운 곳 (그림 실제 영역 기준). 한 번 정하면 그대로."""
        if self._done_pos is None:
            m = self.app.scenes['map']
            img = G.art().get('idle', DONE_SCALE)
            art = img.get_bounding_rect()
            blocks = [m.yard.inflate(8, 8), M.MENU_PANEL.inflate(8, 8), self.dialog.rect(False).inflate(0, 8),
                      pygame.Rect(0, 0, T.WIDTH, T.HEADER_H + 4)] + [r.inflate(6, 6) for r in m.signs.values()]
            goal = (m.yard.centerx, m.yard.top - art.h // 2 - 8)
            best = None
            for y in range(T.HEADER_H, T.HEIGHT - art.h, 2):
                for x in range(0, T.WIDTH - art.w, 2):
                    r = pygame.Rect(x, y, art.w, art.h)
                    if r.collidelist(blocks) != -1:
                        continue
                    d = (r.centerx - goal[0]) ** 2 + (r.centery - goal[1]) ** 2
                    if best is None or d < best[0]:
                        best = (d, r)
            r = best[1] if best else pygame.Rect(goal[0] - art.w // 2, goal[1] - art.h // 2, art.w, art.h)
            self._done_pos = (r.x - art.x, r.y - art.y)            # 그림 왼쪽 위
        img = G.art().get('idle', DONE_SCALE)
        art = img.get_bounding_rect()
        return pygame.Rect(self._done_pos[0] + art.x, self._done_pos[1] + art.y, art.w, art.h)

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
        self.layout()
        if not last and self.skip_btn.handle(event):           # 건너뛰기가 대화 상자 클릭(다음)보다 먼저
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
        prog_pos, _ = self.layout()
        if last:                                               # 다른 단계처럼 어둡게 (강조 칸 없이)
            shade = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
            shade.fill(SHADE)
            surface.blit(shade, (0, 0))
            body = self.done_rect()
            img = G.art().get(G.art().flap(self.t, talk=not self.dialog.done), DONE_SCALE)
            art = img.get_bounding_rect()
            surface.blit(img, (body.x - art.x, body.y - art.y))
            for dx, dy in ((-10, 6), (body.w + 8, 14), (-6, body.h - 10), (body.w + 4, body.h - 4)):
                if int(self.t * 3 + dx) % 3:
                    G.sparkle(surface, body.x + dx, body.y + dy)
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
        self.dialog.draw(surface, top=self.top())
        G.progress(surface, PROGRESS, self.step + 1, len(STEPS), prog_pos)       # 대화 상자 안 오른쪽 위
        if not last:
            self.skip_btn.draw(surface)

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
