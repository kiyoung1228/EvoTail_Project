"""도트 UI 키트 위젯 (docs/UI_KIT.md). 좌표는 전부 640×360 논리 픽셀. 게임 규칙은 없다."""
import os
import pygame
from . import theme as T


def mouse_pos():
    """논리 화면 기준 마우스 좌표 (창 좌표 // 2)."""
    x, y = pygame.mouse.get_pos()
    return x // T.SCALE, y // T.SCALE


# ---------- 조각·아이콘 ----------
class Kit:
    """assets/ui/kit 조각을 읽고, 9-slice 결과를 (이름, w, h)로 캐시한다."""
    _raw, _sliced, _icons = {}, {}, {}

    @classmethod
    def piece(cls, name):
        if name not in cls._raw:
            cls._raw[name] = pygame.image.load(os.path.join(T.KIT_DIR, f'{name}.png')).convert_alpha()
        return cls._raw[name]

    @classmethod
    def nine(cls, name, w, h):
        key = (name, w, h)
        if key not in cls._sliced:
            img, m = cls.piece(name), T.KIT['nine_slice'][name]['margin']
            sw, sh = img.get_size()
            out = pygame.Surface((w, h), pygame.SRCALPHA)
            xs = [(0, m, 0, m), (m, sw - m, m, w - m), (sw - m, sw, w - m, w)]
            ys = [(0, m, 0, m), (m, sh - m, m, h - m), (sh - m, sh, h - m, h)]
            for sx0, sx1, dx0, dx1 in xs:
                for sy0, sy1, dy0, dy1 in ys:
                    if dx1 > dx0 and dy1 > dy0:
                        part = img.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
                        out.blit(pygame.transform.scale(part, (dx1 - dx0, dy1 - dy0)), (dx0, dy0))
            cls._sliced[key] = out
        return cls._sliced[key]

    @classmethod
    def icon(cls, name):
        if name not in cls._icons:
            cls._icons[name] = pygame.image.load(os.path.join(T.KIT_DIR, 'icons', f'{name}.png')).convert_alpha()
        return cls._icons[name]


def nine(surface, name, rect):
    rect = pygame.Rect(rect)
    surface.blit(Kit.nine(name, rect.w, rect.h), rect.topleft)


def icon(surface, name, pos):
    surface.blit(Kit.icon(name), pos)


def moon_icon():
    """밤 아이콘 (키트에 없어서 같은 스타일로 코드로 그림, 12×12)."""
    img = pygame.Surface((12, 12), pygame.SRCALPHA)
    pygame.draw.circle(img, T.INK, (6, 6), 5)
    pygame.draw.circle(img, (250, 204, 70), (6, 6), 4)
    pygame.draw.circle(img, (0, 0, 0, 0), (9, 4), 4)
    return img


# ---------- 글씨 ----------
def text(surface, msg, pos, kind='body', color=T.TEXT, anchor='topleft', shadow=None):
    """도트 글씨 (안티에일리어싱 없음). shadow=색 이면 1px 그림자(오른쪽 아래)."""
    f = T.font(kind)
    img = f.render(str(msg), False, color)
    rect = img.get_rect(**{anchor: pos})
    if shadow:
        surface.blit(f.render(str(msg), False, shadow), rect.move(1, 1))
    surface.blit(img, rect)
    return rect


def text_width(msg, kind='body'):
    return T.font(kind).size(str(msg))[0]


# ---------- 창·칸·리본·칩 ----------
def panel(surface, rect):
    nine(surface, 'panel', rect)


def card(surface, rect, selected=False):
    nine(surface, 'card_selected' if selected else 'card', rect)


def ribbon(surface, rect, label, color='red'):
    rect = pygame.Rect(rect)
    nine(surface, f'ribbon_{color}', rect)
    text(surface, label, rect.center, 'title', T.WHITE, 'center', shadow=T.shade(color, 0))


def chip(surface, pos, label, color, anchor='topleft'):
    """작은 태그: 본색 + 검은 1px 테두리 + 윗줄 밝은색 + 갈무리9 흰 글씨. 그린 rect를 돌려준다."""
    w = text_width(label, 'small') + 6
    rect = pygame.Rect(0, 0, w, 12)
    setattr(rect, anchor, pos)
    pygame.draw.rect(surface, T.shade(color, 2), rect)
    pygame.draw.line(surface, T.shade(color, 3), (rect.x + 1, rect.y + 1), (rect.right - 2, rect.y + 1))
    pygame.draw.rect(surface, T.INK, rect, 1)
    text(surface, label, (rect.centerx, rect.centery), 'small', T.WHITE, 'center', shadow=T.shade(color, 0))
    return rect


# ---------- 게이지 ----------
def gauge(surface, rect, value, maximum, color):
    """틀(gauge_frame 9-slice) + 안쪽 2px 채움(윗줄 밝게, 아랫줄 어둡게) + 10%마다 1px 눈금."""
    rect = pygame.Rect(rect)
    nine(surface, 'gauge_frame', rect)
    inner = rect.inflate(-4, -4)
    frac = max(0.0, min(1.0, value / maximum)) if maximum else 0.0
    w = int(inner.w * frac)
    if w > 0:
        dark, mid, base, light = T.PALETTE[color]
        pygame.draw.rect(surface, base, (inner.x, inner.y, w, inner.h))
        pygame.draw.line(surface, light, (inner.x, inner.y), (inner.x + w - 1, inner.y))
        if inner.h > 2:
            pygame.draw.line(surface, mid, (inner.x, inner.bottom - 1), (inner.x + w - 1, inner.bottom - 1))
    for i in range(1, 10):
        x = inner.x + inner.w * i // 10
        pygame.draw.line(surface, T.INK, (x, inner.bottom - 1), (x, inner.bottom - 1))


# ---------- 버튼 ----------
class Button:
    """키트 버튼. color: green orange purple red brown blue gray. sub가 있으면 두 줄 버튼."""

    def __init__(self, rect, label, on_click, color='green', enabled=True, icon=None, sub=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.color = color
        self.enabled = enabled
        self.icon = icon
        self.sub = sub

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            if self.enabled and self.on_click:
                self.on_click()
            return True
        return False

    def draw(self, surface):
        hover = self.rect.collidepoint(mouse_pos())
        if not self.enabled:
            state = 'disabled'
        elif hover and pygame.mouse.get_pressed()[0]:
            state = 'pressed'
        elif hover:
            state = 'hover'
        else:
            state = 'normal'
        color = self.color
        if self.color == 'gray':      # 회색은 normal 조각만 있음
            state = 'normal'
        nine(surface, f'button_{color}_{state}', self.rect)
        # 몸통(아래 2줄 그림자 제외) 가운데에 글씨. 눌리면 1px 아래
        body = pygame.Rect(self.rect.x, self.rect.y + (1 if state == 'pressed' else 0), self.rect.w, self.rect.h - 2)
        fg = (226, 220, 210) if state == 'disabled' else T.WHITE
        sh = T.shade('gray', 0) if state == 'disabled' else T.shade(color, 0)
        if self.sub:
            text(surface, self.label, (body.centerx, body.centery - 6), 'title', fg, 'center', shadow=sh)
            text(surface, self.sub, (body.centerx, body.centery + 6), 'small', fg, 'center', shadow=sh)
            return
        w = text_width(self.label, 'title') + (14 if self.icon else 0)
        x = body.centerx - w // 2
        if self.icon:
            icon(surface, self.icon, (x, body.centery - 6))
            x += 14
        text(surface, self.label, (x, body.centery), 'title', fg, 'midleft', shadow=sh)


# ---------- 도트 캐릭터 ----------
class SpriteCache:
    """assets/sprites(112×112 = 원본 28×28의 4배)를 원본 28로 줄인 뒤 정수배로만 키운다."""

    def __init__(self):
        self._base = {}
        self._scaled = {}

    def _load(self, rel_path):
        if rel_path not in self._base:
            path = os.path.join(T.ROOT, rel_path) if rel_path else ''
            if path and os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                self._base[rel_path] = pygame.transform.scale(img, (w * 28 // 112, h * 28 // 112))
            else:
                ph = pygame.Surface((28, 28), pygame.SRCALPHA)
                pygame.draw.rect(ph, T.shade('gray', 2), (6, 6, 16, 16))
                self._base[rel_path] = ph
        return self._base[rel_path]

    def get(self, rel_path, size):
        """size는 28의 배수 (28 = 원본, 56 = 2배, 84 = 3배)."""
        key = (rel_path, size)
        if key not in self._scaled:
            base = self._load(rel_path)
            n = max(1, size // 28)
            self._scaled[key] = pygame.transform.scale(base, (base.get_width() * n, base.get_height() * n))
        return self._scaled[key]

    def silhouette(self, rel_path, size):
        """도감에서 아직 없는 동물: 어두운 실루엣."""
        key = (rel_path, size, 'sil')
        if key not in self._scaled:
            img = self.get(rel_path, size).copy()
            img.fill((60, 54, 50, 255), special_flags=pygame.BLEND_RGBA_MIN)
            self._scaled[key] = img
        return self._scaled[key]
