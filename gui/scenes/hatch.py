"""알 부화 연출 + 결과 창 (목업 docs/mockups/shop/hatch_1_storyboard.png, hatch_2_result.png, hatch_3_duplicate.png).

연출 2.6초 (클릭·Space·ESC로 건너뛰기):
  ① 0~1.2초 흔들흔들(좌우 ±4px, 점점 빠르게) + 뒤 은은한 빛
  ② 1.2~2.2초 금이 1줄 → 여러 줄, 금에서 빛이 새어 나오고 빛줄기가 천천히 회전
  ③ 2.2~2.6초 하얀 빛 폭발, 껍질 위·아래 조각이 튀어 나감, 반짝이
  ④ 2.6초~ 결과 창
hatch_egg(egg)는 연출을 시작할 때 한 번 부른다 (실패하면 연출 없이 알림만).
결과 창 숫자는 전부 백엔드 값: 이름·그림·중복·보유 수(hatch_egg), 능력치·MAX(get_evolution_status),
등급·역할·속성·설명·강점(get_catalog).
"""
import math
import random
import pygame

from .. import theme as T
from .. import items as I
from ..app import Overlay
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, icon, gauge,
                       wrap_lines, Button, BUTTON_H)

SHAKE_END, CRACK_END, BURST_END = 1.2, 2.2, 2.6
GOLD = (236, 184, 52)
LIGHT = (255, 240, 170)
WINDOW = pygame.Rect(58, 46, 524, 304)
STAGE = pygame.Rect(74, 68, 200, 200)
EGG_CENTER = (320, 190)
# 금 (알 그림 80×80 안 좌표, 차례로 하나씩 늘어남)
CRACKS = [
    [(22, 40), (32, 34), (38, 42), (46, 33), (54, 41)],
    [(38, 42), (40, 52), (34, 58)],
    [(46, 33), (50, 24), (58, 22)],
    [(54, 41), (60, 50), (58, 58)],
    [(32, 34), (26, 26)],
]


def rays(surface, rect, center, angle, color, alpha, n=12, width=0.55, length=None):
    """빛줄기: center에서 n개의 쐐기. rect 밖은 그리지 않는다 (도트 느낌, 안티에일리어싱 없음)."""
    rect = pygame.Rect(rect)
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    cx, cy = center[0] - rect.x, center[1] - rect.y
    L = length or math.hypot(rect.w, rect.h) * 1.2
    for k in range(n):
        a0 = angle + k * 2 * math.pi / n
        a1 = a0 + width * math.pi / n
        pygame.draw.polygon(layer, (*color, alpha), [(cx, cy), (cx + math.cos(a0) * L, cy + math.sin(a0) * L),
                                                     (cx + math.cos(a1) * L, cy + math.sin(a1) * L)])
    surface.blit(layer, rect.topleft)


def glow(surface, center, radius, color, alpha):
    """은은한 빛: 동심원 3겹 (바깥일수록 옅게)."""
    layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i, f in enumerate((1.0, 0.75, 0.5)):
        pygame.draw.circle(layer, (*color, int(alpha * (i + 1) / 3)), (radius, radius), int(radius * f))
    surface.blit(layer, (center[0] - radius, center[1] - radius))


def sparkle(surface, pos, size=2, color=(255, 236, 140)):
    x, y = pos
    pygame.draw.line(surface, color, (x - size, y), (x + size, y))
    pygame.draw.line(surface, color, (x, y - size), (x, y + size))


class HatchOverlay(Overlay):
    close_outside = False

    def __init__(self, app, egg, on_again=None):
        super().__init__(app, (0, 0, T.WIDTH, T.HEIGHT))
        self.egg = egg
        self.on_again = on_again
        self.t = 0.0
        self.icons = I.ItemIcons()
        self.catalog = app.call('get_shop_catalog') or {}
        self.result = app.call('hatch_egg', egg=egg)
        self.info = {}
        self.evo = {}
        self.buttons = []
        self.jingled = False           # 부화 효과음악은 결과 창이 뜰 때 한 번
        self.sparks = [(random.randint(-70, 70), random.randint(-60, 60)) for _ in range(10)]
        if self.result is None:       # 실패 (알 없음 등): 알림은 app.call이 띄움
            return
        app.refresh()
        app.toast_item = None          # 앞 알림(구매 등)이 연출을 가리지 않게
        key = self.result['id']
        self.info = (app.call('get_catalog') or {}).get(key, {})
        self.total = len(app.call('get_catalog') or {})
        self.evo = app.call('get_evolution_status', key=key) or {}

    # ---------- 진행 ----------
    @property
    def done(self):
        return self.t >= BURST_END

    def skip(self):
        self.t = max(self.t, BURST_END)

    def close(self):
        """ESC: 연출 중이면 결과로 건너뛰고, 결과 창이면 닫는다."""
        if self.result is not None and not self.done:
            self.skip()
        else:
            super().close()

    def handle(self, event):
        if not self.done:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
                    (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self.skip()
            return True
        for b in self.buttons:
            if b.handle(event):
                return True
        return True

    def update(self, dt):
        if self.result is None:
            self.close()
            return
        self.t += dt
        if self.done:
            if not self.jingled:
                self.jingled = True
                self.app.audio.jingle('jingle_hatch')
            self._build_buttons()

    def _build_buttons(self):
        key = self.result['id']
        app = self.app
        left = app.state.get('inventory', {}).get('stackable', {}).get(self.egg, 0)
        egg_label = I.item_label(self.egg, self.catalog)

        def show_animal():
            super(HatchOverlay, self).close()
            app.go('animals', selected=key)

        def again():
            super(HatchOverlay, self).close()
            if self.on_again:
                self.on_again(self.egg)

        y = WINDOW.bottom - 58
        self.buttons = [
            Button((74, y, 150, 40), '내 동물 보기', show_animal, 'green', icon='heart'),
            Button((232, y, 170, 40), '한 번 더 부화', again, 'orange' if left else 'gray', enabled=left > 0,
                   icon='coin', sub=f'{egg_label} {left}개'),
            Button((410, y, 156, 40), '상점으로', lambda: super(HatchOverlay, self).close(), 'brown', icon='back'),
        ]

    # ---------- 그리기 ----------
    def draw(self, surface):
        if self.result is None:
            return
        if self.done:
            self._draw_result(surface)
        else:
            self._draw_anim(surface)

    def _egg_img(self, n=5):
        return self.icons.get(self.egg, n)

    def _draw_anim(self, surface):
        t = self.t
        cx, cy = EGG_CENTER
        screen = pygame.Rect(0, T.HEADER_H, T.WIDTH, T.HEIGHT - T.HEADER_H)
        egg = self._egg_img()
        shade = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        shade.fill((26, 16, 32, 215))                       # 연출 동안 화면 전체를 짙은 보라·검정으로 (스토리보드)
        surface.blit(shade, (0, 0))
        if t < SHAKE_END:                                   # ① 흔들흔들
            p = t / SHAKE_END
            freq = 2 + 8 * p                                 # 점점 빠르게
            dx = round(4 * math.sin(2 * math.pi * freq * t))
            glow(surface, (cx, cy), 70, LIGHT, 60 + int(40 * p))
            surface.blit(egg, egg.get_rect(center=(cx + dx, cy)))
            for k in range(3):                               # 흔들림 선
                if int(t * 8 + k) % 2:
                    pygame.draw.line(surface, T.WHITE, (cx - 52, cy - 10 + k * 8), (cx - 52, cy - 6 + k * 8))
                    pygame.draw.line(surface, T.WHITE, (cx + 52, cy - 10 + k * 8), (cx + 52, cy - 6 + k * 8))
            text(surface, '...!', (cx, 300), 'title', T.WHITE, 'center', shadow=T.INK)
        elif t < CRACK_END:                                 # ② 금 + 빛 새어 나옴
            p = (t - SHAKE_END) / (CRACK_END - SHAKE_END)
            rays(surface, screen, (cx, cy), t * 0.5, GOLD, 70 + int(50 * p), n=14)
            glow(surface, (cx, cy), 80, LIGHT, 90)
            r = egg.get_rect(center=(cx, cy))
            surface.blit(egg, r)
            for line in CRACKS[:1 + int(p * len(CRACKS))]:
                pts = [(r.x + x, r.y + y) for x, y in line]
                pygame.draw.lines(surface, T.INK, False, pts, 3)
                pygame.draw.lines(surface, LIGHT, False, pts, 1)        # 금에서 새는 빛
            for i, (sx, sy) in enumerate(self.sparks[:3 + int(p * 7)]):
                sparkle(surface, (cx + sx, cy + sy), 2)
            text(surface, '알에 금이 간다!', (cx, 300), 'title', T.WHITE, 'center', shadow=T.INK)
        else:                                               # ③ 빛 폭발 + 껍질 조각
            p = (t - CRACK_END) / (BURST_END - CRACK_END)
            rays(surface, screen, (cx, cy), t * 0.5, GOLD, 130, n=16, width=0.7)
            rays(surface, screen, (cx, cy), t * 0.5 + 0.1, LIGHT, 70, n=16, width=0.3)
            glow(surface, (cx, cy), int(50 + 70 * p), (255, 250, 220), 210)
            w, h = egg.get_size()
            top = pygame.transform.rotate(egg.subsurface((0, 0, w, h * 9 // 20)), 25 * p)
            bot = pygame.transform.rotate(egg.subsurface((0, h * 9 // 20, w, h - h * 9 // 20)), -20 * p)
            surface.blit(top, top.get_rect(center=(cx - 90 * p, cy - 20 - 70 * p)))
            surface.blit(bot, bot.get_rect(center=(cx + 90 * p, cy + 24 + 50 * p)))
            for sx, sy in self.sparks:
                sparkle(surface, (cx + int(sx * (1 + p)), cy + int(sy * (1 + p))), 2, T.WHITE)
            # 빛 폭발: 화면 전체를 하얗게 덮지 않고 알 자리에서 둥글게 (어두운 바탕은 그대로)
            glow(surface, (cx, cy), int(40 + 60 * p), (255, 255, 255), int(230 * (1 - abs(p - 0.3) / 0.7)))

    def _draw_result(self, surface):
        res, info, evo = self.result, self.info, self.evo
        panel(surface, WINDOW)
        rw = 136
        ribbon(surface, (WINDOW.centerx - rw // 2, WINDOW.y - 8, rw, 18), '부화 성공!', 'green')
        # 왼쪽 무대: 빛줄기 + 동물 원본 ×4 + 껍질 조각 + 반짝이
        pygame.draw.rect(surface, (255, 232, 160), STAGE)
        rays(surface, STAGE, STAGE.center, self.t * 0.15, (255, 210, 96), 255, n=16)
        sprite = self.app.sprites.get(res.get('sprite'), 112)
        sr = sprite.get_rect(center=(STAGE.centerx, STAGE.centery + 4))
        pygame.draw.ellipse(surface, (236, 184, 80), (sr.centerx - 34, sr.bottom - 26, 68, 12))
        surface.blit(sprite, sr)
        egg = self.icons.get(self.egg, 2)
        w, h = egg.get_size()
        surface.blit(pygame.transform.rotate(egg.subsurface((0, h * 9 // 20, w, h - h * 9 // 20)), -12),
                     (STAGE.x + 14, STAGE.bottom - 34))
        surface.blit(pygame.transform.rotate(egg.subsurface((0, 0, w, h * 9 // 20)), 18),
                     (STAGE.right - 50, STAGE.bottom - 40))
        for sx, sy in ((STAGE.x + 22, STAGE.y + 60), (STAGE.right - 24, STAGE.y + 30), (STAGE.x + 100, STAGE.y + 12),
                       (STAGE.right - 30, STAGE.y + 120), (STAGE.x + 26, STAGE.y + 124)):
            sparkle(surface, (sx, sy), 2 + int(self.t * 3) % 2, (255, 250, 220))
        pygame.draw.rect(surface, T.INK, STAGE, 1)
        if not res.get('duplicate'):
            ribbon(surface, (STAGE.x + 4, STAGE.y + 6, 48, 18), 'NEW', 'red')
        # 오른쪽 정보
        x, right = 290, WINDOW.right - 16
        text(surface, res.get('name', ''), (x, 68), 'big')
        cx = x
        rarity = info.get('rarity')
        strength = (info.get('strength') or '').replace('↑', '').strip()
        chips = [('특급' if rarity == 'special' else '일반', 'gold' if rarity == 'special' else 'gray'),
                 (T.ROLE_LABEL.get(info.get('role'), ''), T.ROLE_KIT.get(info.get('role'), 'gray')),
                 (T.ELEMENT_LABEL.get(info.get('element'), ''), T.ELEMENT_KIT.get(info.get('element'), 'gray')),
                 (f"강점 {'균형' if strength in ('', '기준') else strength}", 'green')]
        for label, color in chips:
            r = chip(surface, (cx, 88), label, color)
            cx = r.right + 3
        # 설명: 칩 줄(아래 끝 104)과 도감 칸(140) 사이 가운데 (한 줄 116, 두 줄 110 = 칩에서 4px 이상)
        lines = wrap_lines(info.get('description', ''), right - x, 'body')[:2]
        top = 104 + (36 - (11 + 13 * (len(lines) - 1))) // 2
        for i, line in enumerate(lines):
            text(surface, line, (x, top + i * 13), 'body', T.TEXT_SOFT)
        box = pygame.Rect(x, 140, right - x, 20)
        card(surface, box)
        if res.get('duplicate'):
            text_in(surface, '이미 보유한 동물 · 도감 변화 없음', card_inner(box), 'body', T.BAD, tag='hatch')
        else:
            inner = card_inner(box)
            icon(surface, 'heart', (inner.x + 4, inner.y + 2))
            text_in(surface, f"도감 등록! {res.get('owned', 0)} / {self.total}", (inner.x + 18, inner.y, inner.w - 18,
                                                                                inner.h), 'body', T.OK,
                    align='left', tag='hatch')
        stats, caps = evo.get('stats', {}), evo.get('caps', {})
        for i, stat in enumerate(T.STATS):
            y = 168 + i * 22
            icon(surface, T.STAT_ICON[stat], (x, y + 2))
            text(surface, T.STAT_LABEL[stat], (x + 15, y), 'body')
            text(surface, str(stats.get(stat, 0)), (x + 98, y), 'title', anchor='topright')
            gauge(surface, (x + 104, y + 2, 130, 10), stats.get(stat, 0), caps.get(stat, 1), T.STAT_KIT[stat])
            text(surface, f"/ {caps.get(stat, 0)}", (right, y + 1), 'small', T.TEXT_SOFT, anchor='topright')
        text(surface, f"{evo.get('stage', 1)}단계 MAX 기준 · 네 능력치 MAX면 진화", (x, 258), 'small', T.TEXT_SOFT)
        for b in self.buttons:
            b.draw(surface)
