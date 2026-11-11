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


_glyph_cache = {}
LAYOUT_LOG = None     # 점검 스크립트가 []로 바꾸면 text_in이 (글씨, 실제 글자 영역, 칸, 이름)을 모은다
TEXT_PAD = 2          # 칸 안 글씨의 최소 여백 (논리 px)


def glyph_box(msg, kind='body'):
    """실제 글자 모양이 차지하는 영역 (렌더 이미지 기준). 줄 높이·글자 앞뒤 빈칸은 빼고 잰다."""
    key = (str(msg), kind)
    if key not in _glyph_cache:
        mask = pygame.mask.from_surface(T.font(kind).render(str(msg), False, (0, 0, 0)))
        rects = mask.get_bounding_rects()
        _glyph_cache[key] = rects[0].unionall(rects[1:]) if rects else pygame.Rect(0, 0, 0, 0)
    return _glyph_cache[key]


def text_in(surface, msg, box, kind='body', color=T.TEXT, align='center', shadow=None, pad=TEXT_PAD, tag='',
            check=None, log=True):
    """칸(box, 테두리 안쪽 영역) 안에 글씨를 실제 글자 모양 기준으로 놓는다.

    세로는 항상 가운데, 가로는 align('center' / 'left' / 'right', left·right는 pad만큼 띄움).
    shadow가 있으면 1px 그림자(오른쪽 아래)까지 포함해서 가운데를 맞춘다. 실제 글자 영역을 돌려준다.
    check: 넘침 검사에 쓸 칸 (없으면 box). log=False면 기록하지 않음 (부르는 쪽이 따로 기록).
    """
    box = pygame.Rect(box)
    g = glyph_box(msg, kind)
    gw, gh = g.w + (1 if shadow else 0), g.h + (1 if shadow else 0)
    if align == 'left':
        gx = box.x + pad
    elif align == 'right':
        gx = box.right - pad - gw
    else:
        gx = box.x + (box.w - gw) // 2
    gy = box.y + (box.h - gh) // 2
    dest = (gx - g.x, gy - g.y)
    f = T.font(kind)
    if shadow:
        surface.blit(f.render(str(msg), False, shadow), (dest[0] + 1, dest[1] + 1))
    surface.blit(f.render(str(msg), False, color), dest)
    drawn = pygame.Rect(gx, gy, gw, gh)
    if log:
        record(str(msg), drawn, check or box, tag)
    return drawn


def record(msg, drawn, box, tag=''):
    """넘침 점검용 기록 (LAYOUT_LOG가 켜져 있을 때만)."""
    if LAYOUT_LOG is not None:
        LAYOUT_LOG.append((msg, pygame.Rect(drawn), pygame.Rect(box), tag))


def card_inner(rect):
    """card 조각의 안쪽 (테두리 2px 제외)."""
    return pygame.Rect(rect).inflate(-4, -4)


def button_face(rect, pressed=False):
    """버튼 조각의 몸통 (검은 1px 테두리 안, 아래 그림자 2줄 제외). 눌리면 1px 아래."""
    r = pygame.Rect(rect)
    return pygame.Rect(r.x + 1, r.y + 1 + (1 if pressed else 0), r.w - 2, r.h - 4)


# 칸 높이: 글자 높이(제목·본문 11, 작은 글씨 9) + 그림자 1 + 여백 2×2 + 테두리
BUTTON_H = 20          # 한 줄 버튼 최소 높이 (몸통 16 = 11 + 1 + 4)
CHIP_H = 16            # 칩 (안쪽 14 = 9 + 1 + 4)
CARD_LABEL_H = 20      # card 조각 + 제목 글씨 (안쪽 16)


def fit_width(msg, kind='body', extra=0, shadow=False):
    """글씨가 TEXT_PAD 여백을 두고 들어가는 칸 안쪽 폭 (+extra: 아이콘 등)."""
    return glyph_box(msg, kind).w + (1 if shadow else 0) + 2 * TEXT_PAD + extra


# ---------- 창·칸·리본·칩 ----------
def panel(surface, rect):
    nine(surface, 'panel', rect)


def card(surface, rect, selected=False):
    nine(surface, 'card_selected' if selected else 'card', rect)


def ribbon(surface, rect, label, color='red'):
    rect = pygame.Rect(rect)
    nine(surface, f'ribbon_{color}', rect)
    # 리본 안쪽: 양 끝 V자 홈(5px)과 위아래 테두리 제외
    inner = pygame.Rect(rect.x + 5, rect.y + 1, rect.w - 10, rect.h - 2)
    text_in(surface, label, inner, 'title', T.WHITE, shadow=T.shade(color, 0), tag='ribbon')


def chip(surface, pos, label, color, anchor='topleft'):
    """작은 태그: 본색 + 검은 1px 테두리 + 윗줄 밝은색 + 갈무리9 흰 글씨. 그린 rect를 돌려준다."""
    rect = pygame.Rect(0, 0, chip_width(label), CHIP_H)
    setattr(rect, anchor, pos)
    pygame.draw.rect(surface, T.shade(color, 2), rect)
    pygame.draw.line(surface, T.shade(color, 3), (rect.x + 1, rect.y + 1), (rect.right - 2, rect.y + 1))
    pygame.draw.rect(surface, T.INK, rect, 1)
    text_in(surface, label, rect.inflate(-2, -2), 'small', T.WHITE, shadow=T.shade(color, 0), tag='chip')
    return rect


def chip_width(label):
    return fit_width(label, 'small', shadow=True) + 2      # + 테두리 1px × 2


def tooltip(surface, msg, target, side='right', bounds=None):
    """설명 말풍선 (키트 card 조각 + 같은 테두리 색 꼬리). target 옆에 붙인다.

    side: 'right' / 'left' / 'above' / 'below'. 화면(bounds) 밖으로 나가면 반대쪽으로.
    """
    target = pygame.Rect(target)
    bounds = pygame.Rect(bounds or (0, T.HEADER_H, T.WIDTH, T.HEIGHT - T.HEADER_H))
    box = pygame.Rect(0, 0, fit_width(msg) + 4 + 4, CARD_LABEL_H)     # 글씨 + 여백 + card 테두리 2px×2

    def place(s):
        if s == 'right':
            box.midleft = (target.right + 6, target.centery)
        elif s == 'left':
            box.midright = (target.left - 6, target.centery)
        elif s == 'above':
            box.midbottom = (target.centerx, target.top - 5)
        else:
            box.midtop = (target.centerx, target.bottom + 5)
    place(side)
    if not bounds.contains(box):
        side = {'right': 'left', 'left': 'right', 'above': 'below', 'below': 'above'}[side]
        place(side)
    box.clamp_ip(bounds)
    card(surface, box)
    edge, fill = (120, 80, 50), (252, 240, 214)        # card 조각의 테두리·안쪽 색
    if side in ('right', 'left'):
        x = box.left if side == 'right' else box.right - 1
        d = -1 if side == 'right' else 1
        cy = max(box.top + 5, min(box.bottom - 6, target.centery))
        pts = [(x, cy - 3), (x, cy + 3), (x + d * 4, cy)]
    else:
        y = box.bottom - 1 if side == 'above' else box.top
        d = 1 if side == 'above' else -1
        cx = max(box.left + 5, min(box.right - 6, target.centerx))
        pts = [(cx - 3, y), (cx + 3, y), (cx, y + d * 4)]
    pygame.draw.polygon(surface, fill, pts)
    pygame.draw.lines(surface, T.INK, False, [pts[0], pts[2], pts[1]])
    text_in(surface, msg, card_inner(box), 'body', T.TEXT, tag='tooltip')
    return box


def select_frame(surface, rect, color=None):
    """선택·강조 표시: 네 모서리에 도트 꺾쇠 (검은 테두리 + 색 안쪽, 기본 노랑).
    color: 키트 색 이름(red, green, ...)이면 그 밝은색."""
    r = pygame.Rect(rect)
    gold = T.shade(color, 3) if color else T.shade('orange', 3)
    ink, n = T.INK, 6
    for (x, y, dx, dy) in ((r.left, r.top, 1, 1), (r.right - 1, r.top, -1, 1),
                           (r.left, r.bottom - 1, 1, -1), (r.right - 1, r.bottom - 1, -1, -1)):
        for off, col in ((0, ink), (1, gold), (2, ink)):
            pygame.draw.line(surface, col, (x + dx * off, y + dy * off), (x + dx * (n + 2), y + dy * off))
            pygame.draw.line(surface, col, (x + dx * off, y + dy * off), (x + dx * off, y + dy * (n + 2)))


# ---------- 게이지 ----------
def gauge(surface, rect, value, maximum, color):
    """틀(gauge_frame 9-slice) + 안쪽 2px 채움(윗줄 밝게, 아랫줄 어둡게) + 10%마다 1px 눈금."""
    rect = pygame.Rect(rect)
    nine(surface, 'gauge_frame', rect)
    inner = rect.inflate(-4, -4)
    frac = max(0.0, min(1.0, value / maximum)) if maximum else 0.0
    w = int(inner.w * frac)
    if frac > 0:
        w = max(1, w)          # 조금이라도 진행됐으면 1px은 보이게
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
        # 몸통(테두리 안, 아래 그림자 제외) 가운데에 글씨. 실제 글자 모양 기준. 눌리면 1px 아래
        face = button_face(self.rect, state == 'pressed')
        fg = (226, 220, 210) if state == 'disabled' else T.WHITE
        sh = T.shade('gray', 0) if state == 'disabled' else T.shade(color, 0)
        if self.sub:      # 두 줄: 위 굵은 글씨, 아래 작은 글씨. 두 줄을 한 덩어리로 가운데
            g1, g2 = glyph_box(self.label, 'title'), glyph_box(self.sub, 'small')
            block = g1.h + 1 + 1 + g2.h + 1                 # 그림자 1 + 줄 사이 1
            top = face.y + (face.h - block) // 2
            a = text_in(surface, self.label, (face.x, top, face.w, g1.h + 1), 'title', fg, shadow=sh, log=False)
            b = text_in(surface, self.sub, (face.x, top + g1.h + 2, face.w, g2.h + 1), 'small', fg, shadow=sh,
                        log=False)
            record(f'{self.label}/{self.sub}', a.union(b), face, 'button')
            return
        g = glyph_box(self.label, 'title')
        w = g.w + 1 + (14 if self.icon else 0)
        x = face.x + (face.w - w) // 2
        if self.icon:
            icon(surface, self.icon, (x, face.y + (face.h - 12) // 2))
        label = text_in(surface, self.label, (x + (14 if self.icon else 0), face.y, g.w + 1, face.h), 'title', fg,
                        shadow=sh, log=False)
        record(self.label, pygame.Rect(x, label.y, w, label.h), face, 'button')

    @staticmethod
    def width_for(label, icon=False):
        """글씨(+아이콘)가 여백을 두고 들어가는 버튼 폭."""
        return fit_width(label, 'title', extra=14 if icon else 0, shadow=True) + 2


# ---------- 도트 캐릭터 ----------
LYING_ROWS = 20         # 엎드린 모습: 원본 28줄 중 20줄만 남김

BOSS_MIN_ORIGINAL = 29     # 원본 폭이 이보다 크면 보스 (졸개·동물 28, 보스 46)


class SpriteCache:
    """도트 그림 파일(원본의 4배로 저장)을 원본 크기로 줄인 뒤 정수배로만 키운다.

    - 동물 assets/sprites: 112×112 → 원본 28
    - 적 assets/enemies: 졸개 112×112 → 원본 28, 보스 184×184 → 원본 46
    """

    def __init__(self):
        self._base = {}
        self._scaled = {}

    def _load(self, rel_path):
        if rel_path not in self._base:
            path = os.path.join(T.ROOT, rel_path) if rel_path else ''
            if path and os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                w, h = img.get_size()
                self._base[rel_path] = pygame.transform.scale(img, (w // 4, h // 4))     # 4배 저장 → 원본
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

    # ---------- 적 몬스터 (졸개·보스 공통) ----------
    def original_size(self, rel_path):
        """원본 도트 크기 (파일 ÷ 4). 졸개·동물 (28, 28), 보스 (46, 46)."""
        return self._load(rel_path).get_size()

    def is_boss(self, rel_path, flag=None):
        """보스인지. 백엔드가 boss를 주면 그 값, 아니면 그림 크기(원본 폭 46)로 판단."""
        if flag is not None:
            return bool(flag)
        return self.original_size(rel_path)[0] >= BOSS_MIN_ORIGINAL

    def scaled(self, rel_path, n=2):
        """원본 × n (정수). 전투 화면은 졸개·보스 모두 ×2 → 졸개 56, 보스 92 (논리 px)."""
        key = (rel_path, 'x', n)
        if key not in self._scaled:
            base = self._load(rel_path)
            self._scaled[key] = pygame.transform.scale(base, (base.get_width() * n, base.get_height() * n))
        return self._scaled[key]

    def fit(self, rel_path, box_w, box_h, max_n=2):
        """정해진 칸(도감·카드 등)에 들어가는 그림. 들어가는 가장 큰 정수배(최대 max_n)로,
        ×1도 안 들어가면(칸보다 큰 보스) ×1에서 그림 위쪽을 칸 크기만큼 잘라 초상으로."""
        key = (rel_path, 'fit', box_w, box_h, max_n)
        if key not in self._scaled:
            w, h = self.original_size(rel_path)
            n = min(max_n, box_w // w, box_h // h)
            if n >= 1:
                img = self.scaled(rel_path, n)
            else:
                base = self._load(rel_path)
                art = base.get_bounding_rect()
                cw, ch = min(box_w, w), min(box_h, h)
                x = max(0, min(w - cw, art.centerx - cw // 2))
                y = max(0, min(h - ch, art.top))                    # 머리부터 (위쪽 초상)
                img = base.subsurface((x, y, cw, ch)).copy()
            self._scaled[key] = img
        return self._scaled[key]

    def lying(self, rel_path, size):
        """엎드린(쉬는) 모습. 따로 그린 그림 <이름>_lying.png(예: dealer_normal_01_s1_lying.png)가 있으면 그걸,
        없으면 서 있는 도트를 세로로만 납작하게(원본 28줄 → 20줄) 만들어 쓴다.
        누운 도트를 새로 그리면 파일만 넣으면 바뀐다."""
        key = (rel_path, size, 'lying')
        if key not in self._scaled:
            drawn = rel_path[:-4] + '_lying.png' if rel_path and rel_path.endswith('.png') else None
            if drawn and os.path.exists(os.path.join(T.ROOT, drawn)):
                self._scaled[key] = self.get(drawn, size)
            else:
                flat = self._flatten(self._load(rel_path), LYING_ROWS)
                n = max(1, size // 28)
                self._scaled[key] = pygame.transform.scale(flat, (flat.get_width() * n, flat.get_height() * n))
        return self._scaled[key]

    @staticmethod
    def _flatten(base, rows):
        """원본 도트에서 줄을 고르게 빼서 세로 rows줄로 (가로·픽셀은 그대로). 크기는 원본과 같고 바닥에 붙인다."""
        w, h = base.get_size()
        out = pygame.Surface((w, h), pygame.SRCALPHA)
        top = h - rows
        for i in range(rows):
            src = i * h // rows               # 28줄 중 고르게 고른 줄 (8줄이 빠짐)
            out.blit(base, (0, top + i), (0, src, w, 1))
        return out

    def silhouette(self, rel_path, size):
        """도감에서 아직 없는 동물: 어두운 실루엣."""
        key = (rel_path, size, 'sil')
        if key not in self._scaled:
            img = self.get(rel_path, size).copy()
            img.fill((60, 54, 50, 255), special_flags=pygame.BLEND_RGBA_MIN)
            self._scaled[key] = img
        return self._scaled[key]
