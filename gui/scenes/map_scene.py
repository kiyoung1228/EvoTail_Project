"""메인 지도. 장소로 이동하고, 마당에서 동물들의 자율행동을 보여준다."""
import math
import time
import pygame

from .. import theme as T
from ..app import Scene
from ..widgets import text, panel

# (장소 이름, 설명, 이동할 화면, 색)
PLACES = [
    ('집', '동물 돌보기 · 훈련 · 진화', 'animals', (236, 150, 92)),
    ('밭', '작물 심기 · 수확', 'farm', (150, 196, 92)),
    ('상점', '먹이 · 장난감 · 장비 · 알', 'shop', (232, 186, 72)),
    ('병원', '질병 치료 · 회복 포션', 'hospital', (226, 120, 140)),
    ('주방', '요리하기', 'kitchen', (214, 140, 90)),
    ('사냥터', '고기 재료 자동 사냥', 'hunting', (150, 120, 92)),
    ('전투장', '스테이지 · 대회', 'battle', (120, 132, 220)),
    ('도감', '모은 동물 30종', 'pokedex', (150, 120, 200)),
]

YARD = pygame.Rect(40, 420, T.WIDTH - 80, 270)


class MapScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.cards = []
        cols, w, h, gap = 4, 280, 150, 24
        x0 = (T.WIDTH - (cols * w + (cols - 1) * gap)) // 2
        for i, place in enumerate(PLACES):
            r = pygame.Rect(x0 + (i % cols) * (w + gap), 76 + (i // cols) * (h + 18), w, h)
            self.cards.append((r, place))
        self.hover = None

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = next((i for i, (r, _) in enumerate(self.cards) if r.collidepoint(event.pos)), None)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for r, (_, _, target, _) in self.cards:
                if r.collidepoint(event.pos):
                    self.app.go(target)
                    return
            for key, rect in self._animal_rects():
                if rect.collidepoint(event.pos):
                    self.app.go('animals', selected=key)
                    return

    def _animal_rects(self):
        animals = self.app.state.get('animals', [])
        n = max(1, len(animals))
        step = YARD.w // n if n <= 8 else YARD.w // 8
        out = []
        for i, a in enumerate(animals[:16]):
            row, col = divmod(i, 8)
            cx = YARD.x + step // 2 + col * step
            cy = YARD.y + 150 + row * 120
            out.append((a['id'], pygame.Rect(cx - 64, cy - 64, 128, 128)))
        return out

    def draw(self, surface):
        surface.fill(T.BG)
        for i, (r, (name, desc, _, color)) in enumerate(self.cards):
            lifted = r.move(0, -4) if i == self.hover else r
            panel(surface, lifted, fill=T.PANEL, edge=color, width=3)
            pygame.draw.rect(surface, color, (lifted.x, lifted.y, lifted.w, 46),
                             border_top_left_radius=14, border_top_right_radius=14)
            text(surface, name, (lifted.x + 18, lifted.y + 9), 24, (255, 255, 255), bold=True)
            text(surface, desc, (lifted.x + 18, lifted.y + 66), 16, T.INK_SOFT)
            text(surface, '들어가기 ›', (lifted.right - 16, lifted.bottom - 14), 15, color, bold=True,
                 anchor='bottomright')
        self._draw_yard(surface)

    def _draw_yard(self, surface):
        pygame.draw.rect(surface, T.GRASS, YARD, border_radius=18)
        pygame.draw.rect(surface, T.GRASS_DARK, YARD, 3, border_radius=18)
        text(surface, '마당 · 동물들이 스스로 행동해요 (클릭하면 집으로)', (YARD.x + 18, YARD.y + 12), 16, (60, 90, 40), bold=True)
        t = time.time()
        for i, (key, rect) in enumerate(self._animal_rects()):
            a = self.app.animal(key)
            auto = self.app.auto.get(key, {})
            action = auto.get('action', 'idle')
            # 행동에 따라 움직임을 다르게: 놀기는 통통, 휴식은 가만히, 나머지는 살짝 흔들림
            if action == 'play':
                dy = -abs(math.sin(t * 6 + i)) * 14
            elif action == 'rest':
                dy = 0
            else:
                dy = math.sin(t * 2 + i) * 3
            img = self.app.sprites.get(a.get('sprite'), 128)
            if a.get('sick'):
                img = img.copy()
                img.fill((180, 200, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(img, rect.move(0, int(dy)))
            label = auto.get('label', '')
            if a.get('sick'):
                label = '아파요'
            elif action == 'rest':
                label += ' z'
            bubble = T.font(14).render(label, True, T.INK)
            box = bubble.get_rect(midbottom=(rect.centerx, rect.top + 30)).inflate(14, 8)
            pygame.draw.rect(surface, (255, 255, 255), box, border_radius=10)
            surface.blit(bubble, bubble.get_rect(center=box.center))
            text(surface, a['name'], (rect.centerx, rect.bottom - 12), 15, (40, 70, 30), bold=True, anchor='midtop')
        if self.app.state.get('clock', {}).get('night'):
            shade = pygame.Surface(YARD.size, pygame.SRCALPHA)
            shade.fill(T.NIGHT_TINT)
            surface.blit(shade, YARD.topleft)
