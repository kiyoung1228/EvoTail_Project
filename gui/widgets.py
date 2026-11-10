"""Small drawing helpers and a clickable button. No game rules live here."""
import os
import pygame
from . import theme as T


def text(surface, msg, pos, size=18, color=T.INK, bold=False, anchor='topleft'):
    img = T.font(size, bold).render(str(msg), True, color)
    rect = img.get_rect(**{anchor: pos})
    surface.blit(img, rect)
    return rect


def panel(surface, rect, fill=T.PANEL, edge=T.PANEL_EDGE, radius=14, width=2):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if width:
        pygame.draw.rect(surface, edge, rect, width, border_radius=radius)


def bar(surface, rect, value, maximum, color, track=(232, 224, 210), cap=None, cap_max=None):
    """Gauge. ``cap``가 있으면 이 동물이 채울 수 있는 끝을 세로선으로 표시."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, track, rect, border_radius=rect.h // 2)
    scale = cap_max or maximum or 1
    w = int(rect.w * max(0, min(value, scale)) / scale)
    if w > 0:
        pygame.draw.rect(surface, color, (rect.x, rect.y, max(w, rect.h), rect.h), border_radius=rect.h // 2)
    if cap is not None and cap_max:
        x = rect.x + int(rect.w * min(cap, cap_max) / cap_max)
        pygame.draw.line(surface, T.INK, (x, rect.y - 3), (x, rect.bottom + 2), 2)


class Button:
    def __init__(self, rect, label, on_click, size=18, color=T.ACCENT, enabled=True, hint=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.size = size
        self.color = color
        self.enabled = enabled
        self.hint = hint
        self.hover = False

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            if self.enabled and self.on_click:
                self.on_click()
            return True
        return False

    def draw(self, surface):
        self.hover = self.rect.collidepoint(pygame.mouse.get_pos())
        if not self.enabled:
            fill = T.DISABLED
        elif self.hover:
            fill = tuple(max(0, c - 24) for c in self.color)
        else:
            fill = self.color
        shadow = self.rect.move(0, 3)
        pygame.draw.rect(surface, tuple(max(0, c - 60) for c in fill), shadow, border_radius=10)
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        text(surface, self.label, self.rect.center, self.size, (255, 255, 255), bold=True, anchor='center')


class SpriteCache:
    """도트 이미지를 정수배로만 키워서 픽셀이 뭉개지지 않게 보관."""

    def __init__(self):
        self._raw = {}
        self._scaled = {}

    def get(self, rel_path, size):
        key = (rel_path, size)
        if key in self._scaled:
            return self._scaled[key]
        if rel_path not in self._raw:
            path = os.path.join(T.ROOT, rel_path) if rel_path else ''
            if path and os.path.exists(path):
                self._raw[rel_path] = pygame.image.load(path).convert_alpha()
            else:
                ph = pygame.Surface((28, 28), pygame.SRCALPHA)
                pygame.draw.rect(ph, T.DISABLED, (4, 4, 20, 20), border_radius=4)
                self._raw[rel_path] = ph
        img = pygame.transform.scale(self._raw[rel_path], (size, size))
        self._scaled[key] = img
        return img

    def silhouette(self, rel_path, size):
        """도감에서 아직 없는 동물: 검은 실루엣."""
        key = (rel_path, size, 'sil')
        if key not in self._scaled:
            img = self.get(rel_path, size).copy()
            img.fill((60, 54, 50, 255), special_flags=pygame.BLEND_RGBA_MIN)
            self._scaled[key] = img
        return self._scaled[key]
