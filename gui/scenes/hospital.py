"""병원 (A안): 아픈 동물 탭 / 진료실 침대 / 정보 칸 / 포션 쟁반 → 치료 결과 창.

목업 docs/mockups/hospital/hospital_A_room.png, hospital_success.png, hospital_fail.png.
게임 규칙은 없다: 아픈 동물은 스냅샷 sick, 포션 효과(치료 확률·피로도)는 get_shop_catalog 값,
치료 결과는 use_item(item, key)의 success·fatigue. 상태 단계는 T.level(백엔드 status).
그림 순서: assets/hospital/room.png → 환자(원본 ×3, 논리 (236, 92)) → blanket.png (이불이 가슴까지 덮음).
"""
import json
import math
import os
import pygame

from .. import theme as T
from .. import widgets as W
from .. import items as I
from ..app import Scene, Overlay
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, chip_width, icon,
                       gauge, record, Button, BUTTON_H)
from .hatch import rays

with open(os.path.join(T.ROOT, 'assets', 'items', 'items_icons.json'), encoding='utf-8') as _f:
    _HOSP = json.load(_f).get('hospital', {})
PATIENT_XY = tuple(_HOSP.get('patient_xy', (236, 92)))
PATIENT_SCALE = _HOSP.get('patient_scale', 3)
INFO = pygame.Rect(457, 67, 172, 148)
TRAY = pygame.Rect(9, 252, 622, 100)
CURES = ('heal_basic', 'heal_advanced')
TAB_X0 = 160


def cure_text(spec):
    """'치료 50% · 피로도 -10' (상점 목록 값)."""
    s = f"치료 {round(spec.get('chance', 0) * 100)}%"
    if spec.get('fatigue'):
        s += f" · 피로도 {spec['fatigue']:+d}"
    return s


class HospitalScene(Scene):
    music = 'hospital'    # 배경음: gui/audio.py TRACKS
    def __init__(self, app):
        super().__init__(app)
        self.selected = None
        self.potion = 'heal_advanced'
        self.catalog = {}
        self.icons = I.ItemIcons()
        self.buttons = []
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.catalog = self.app.call('get_shop_catalog') or self.catalog
        self._fix()

    def patients(self):
        return [a for a in self.app.state.get('animals', []) if a.get('sick')]

    def have(self, item):
        return self.app.state.get('inventory', {}).get('stackable', {}).get(item, 0)

    def _fix(self):
        ids = [a['id'] for a in self.patients()]
        if self.selected not in ids:
            self.selected = ids[0] if ids else None
        if self.have(self.potion) == 0:          # 고른 포션이 없으면 가진 쪽으로
            owned = [c for c in CURES if self.have(c) > 0]
            if owned:
                self.potion = owned[-1]

    # ---------- 칸 ----------
    def tab_rects(self):
        out, x = [], TAB_X0
        for a in self.patients():
            w = 4 + 16 + 4 + fit_width(a['name'], 'body') + 4
            out.append((a, pygame.Rect(x, 32, w, BUTTON_H)))
            x += w + 4
        return out

    @staticmethod
    def potion_rect(i):
        return pygame.Rect(TRAY.x + 10 + i * 210, TRAY.y + 28, 204, 46)

    # ---------- 입력 ----------
    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for a, r in self.tab_rects():
                if r.collidepoint(event.pos):
                    self.selected = a['id']
                    return
            for i, c in enumerate(CURES):
                if self.potion_rect(i).collidepoint(event.pos):
                    self.potion = c
                    return
            if self._shop_link().collidepoint(event.pos):
                self.app.go('shop', tab='potion')

    def _shop_link(self):
        msg = '포션 사러 가기 ▶ 상점'
        g = glyph_box(msg, 'body')
        return pygame.Rect(TRAY.right - 14 - g.w - 4, TRAY.bottom - 22, g.w + 4, 15)

    # ---------- 치료 ----------
    def treat(self, key=None, item=None):
        key, item = key or self.selected, item or self.potion
        a = self.app.animal(key)
        if not a:
            return
        before = a['fatigue']
        res = self.app.call('use_item', item=item, key=key)
        self.app.refresh()
        self._fix()
        if res is None:
            return
        self.app.open_overlay(CureResult(self, a, item, before, res))

    def update(self, dt):
        self._fix()
        a = self.app.animal(self.selected)
        n = self.have(self.potion)
        label = I.item_label(self.potion, self.catalog)
        r = pygame.Rect(TRAY.x + 434, TRAY.y + 26, 178, 46)
        self.buttons = [Button(r, '치료하기', self.treat, 'green' if (a and n) else 'gray', enabled=bool(a and n),
                               icon='heart',
                               sub='환자 없음' if not a else (f"{label} 1개 사용" if n else f"{label} 없음"))]

    # ---------- 그리기 ----------
    def draw(self, surface):
        surface.blit(W.background('assets/hospital/room.png'), (0, 0))
        a = self.app.animal(self.selected)
        if a:
            sprite = self.app.sprites.get(a['sprite'], 28 * PATIENT_SCALE)
            surface.blit(sprite, PATIENT_XY)
        surface.blit(W.background('assets/hospital/blanket.png'), (0, 0))
        self.back.draw(surface)
        ribbon(surface, (78, 33, 72, 18), '병원', 'red')
        self._draw_tabs(surface)
        if a:
            self._draw_patient_marks(surface, a)
            self._draw_info(surface, a)
        else:
            box = pygame.Rect(0, 0, fit_width('아픈 동물 없음', 'title', shadow=True) + 16, 24)
            box.center = (320, 120)
            card(surface, box)
            text_in(surface, '아픈 동물 없음', card_inner(box), 'title', T.TEXT, shadow=T.WHITE, tag='hospital')
        self._draw_tray(surface)
        for b in self.buttons:
            b.draw(surface)

    def _draw_tabs(self, surface):
        for a, r in self.tab_rects():
            card(surface, r, selected=a['id'] == self.selected)
            face = self.app.sprites.fit(a['sprite'], 16, 16, max_n=1)
            surface.blit(face, (r.x + 4, r.y + 2))
            text_in(surface, a['name'], (r.x + 22, r.y + 2, r.w - 24, r.h - 4), 'body', align='left', tag='hospital')

    def _draw_patient_marks(self, surface, a):
        t = pygame.time.get_ticks() / 1000
        art = pygame.Rect(PATIENT_XY, (28 * PATIENT_SCALE, 28 * PATIENT_SCALE))
        # 땀방울 (위아래로 1px)
        dy = int(t * 2) % 2
        drop = (art.right - 12, art.y + 30 + dy)
        pygame.draw.circle(surface, T.INK, drop, 4)
        pygame.draw.circle(surface, T.shade('blue', 3), drop, 3)
        # "아픔" 말풍선
        msg = '아픔'
        box = pygame.Rect(art.right, art.y + 2, 14 + fit_width(msg, 'title') + 8, 20)
        card(surface, box)
        inner = card_inner(box)
        icon(surface, 'zzz', (inner.x + 2, inner.y + 2))
        text_in(surface, msg, (inner.x + 16, inner.y, inner.w - 16, inner.h), 'title', T.BAD, align='left',
                tag='hospital')
        tail = [(box.x + 6, box.bottom - 1), (box.x + 12, box.bottom - 1), (box.x + 4, box.bottom + 4)]
        pygame.draw.polygon(surface, (252, 240, 214), tail)
        pygame.draw.lines(surface, T.INK, False, [tail[0], tail[2], tail[1]])

    def _draw_info(self, surface, a):
        panel(surface, INFO)
        x, right = INFO.x + 12, INFO.right - 12
        text(surface, a['name'], (x, INFO.y + 10), 'big')
        r = chip(surface, (x, INFO.y + 30), '아픔', 'red')
        chip(surface, (r.right + 3, INFO.y + 30), '출전 불가', 'gray')
        y = INFO.y + 54
        for kind, label in (('fatigue', '피로도'), ('fullness', '포만감')):
            lv = T.level(a, kind)
            text(surface, label, (x, y), 'body')
            show = f"{a[kind]} {lv}" if kind == 'fatigue' else lv
            text(surface, show, (right, y), 'body', T.shade(T.LEVEL_KIT[lv], 1), anchor='topright')
            gauge(surface, (x, y + 15, right - x, 10), a[kind], 100, T.LEVEL_KIT[lv])
            y += 34
        text(surface, '훈련·사냥·전투 불가', (x, y + 2), 'body', T.TEXT_SOFT)

    def _draw_tray(self, surface):
        panel(surface, TRAY)
        text(surface, '치료할 포션 선택', (TRAY.x + 12, TRAY.y + 10), 'title')
        text(surface, '실패 시 포션만 소모', (TRAY.x + 424, TRAY.y + 12), 'body', T.TEXT_SOFT, anchor='topright')
        for i, c in enumerate(CURES):
            spec = self.catalog.get(c, {})
            r = self.potion_rect(i)
            card(surface, r, selected=c == self.potion)
            surface.blit(self.icons.get(c, 2), (r.x + 6, r.y + 7))
            inner = card_inner(r)
            n = self.have(c)
            own = f"보유 {n}"
            ow = fit_width(own, 'body')
            text_in(surface, own, (inner.right - ow - 2, inner.y + 2, ow, 17), 'body', T.BAD if n == 0 else T.TEXT,
                    tag='hospital')
            text_in(surface, spec.get('label', c), (r.x + 44, inner.y + 2, inner.right - ow - r.x - 48, 17), 'title',
                    align='left', tag='hospital')
            text_in(surface, cure_text(spec), (r.x + 44, inner.y + 21, inner.right - r.x - 46, 17), 'body',
                    T.TEXT_SOFT, align='left', tag='hospital')
        link = self._shop_link()
        hover = link.collidepoint(W.mouse_pos())
        text_in(surface, '포션 사러 가기 ▶ 상점', link, 'body', T.shade('orange', 0 if hover else 1), pad=2,
                tag='hospital', log=False)


class CureResult(Overlay):
    """치료 결과 창: 성공(빛줄기, 피로도 전→후, 다음 환자/닫기) / 실패(어둡게, 아직 아픔, 다시 치료/닫기)."""

    def __init__(self, scene, animal, item, before, res):
        super().__init__(scene.app, (171, 70, 298, 240))
        self.scene, self.animal, self.item, self.before, self.res = scene, animal, item, before, res
        self.ok = bool(res.get('success'))
        self.t = 0.0
        self.buttons = []

    def update(self, dt):
        self.t += dt
        app, sc = self.app, self.scene
        y = self.rect.bottom - 56
        close = Button((self.rect.centerx + 6, y, 128, 40), '닫기', self.close, 'brown')
        if self.ok:
            nxt = next((a for a in sc.patients() if a['id'] != self.animal['id']), None)

            def go_next():
                self.close()
                sc.selected = nxt['id']
            self.buttons = [Button((self.rect.centerx - 134, y, 128, 40), '다음 환자', go_next,
                                   'green' if nxt else 'gray', enabled=bool(nxt), icon=None if not nxt else 'heart',
                                   sub=nxt['name'] if nxt else '없음'), close]
        else:
            left = sc.have(self.item)
            short = '고급' if self.item == 'heal_advanced' else '기본'

            def again():
                self.close()
                sc.treat(self.animal['id'], self.item)
            self.buttons = [Button((self.rect.centerx - 134, y, 128, 40), '다시 치료', again,
                                   'green' if left else 'gray', enabled=left > 0, icon='heart', sub=f"{short} {left}개 남음"), close]

    def handle(self, event):
        for b in self.buttons:
            if b.handle(event):
                return True
        return False

    def draw(self, surface):
        r = self.rect
        panel(surface, r)
        rib = '치료 성공!' if self.ok else '치료 실패...'
        rw = fit_width(rib, 'title', shadow=True) + 30
        ribbon(surface, (r.centerx - rw // 2, r.y - 8, rw, 18), rib, 'green' if self.ok else 'brown')
        art = pygame.Rect(r.centerx - 52, r.y + 18, 104, 84)
        name = self.animal['name']
        sprite = self.app.sprites.get(self.animal['sprite'], 84)
        if self.ok:
            pygame.draw.rect(surface, (222, 244, 210), art)
            rays(surface, art, art.center, self.t * 0.3, (196, 232, 176), 255, n=12)
            surface.blit(sprite, sprite.get_rect(center=art.center))
            for px, py in ((art.x + 14, art.y + 12), (art.right - 14, art.y + 18), (art.x + 18, art.bottom - 14),
                           (art.right - 16, art.bottom - 18)):
                pygame.draw.rect(surface, T.shade('green', 2), (px - 3, py - 1, 7, 3))
                pygame.draw.rect(surface, T.shade('green', 2), (px - 1, py - 3, 3, 7))
        else:
            pygame.draw.rect(surface, (234, 230, 240), art)
            gray = pygame.transform.grayscale(sprite)
            surface.blit(gray, gray.get_rect(center=art.center))
            pygame.draw.circle(surface, T.INK, (art.right - 14, art.y + 12), 8)
            pygame.draw.circle(surface, T.shade('blue', 3), (art.right - 14, art.y + 12), 7)
        pygame.draw.rect(surface, T.shade('green', 3) if self.ok else T.shade('gray', 2), art, 1)
        label = I.item_label(self.item, self.scene.catalog)
        y = art.bottom + 8
        if self.ok:
            text(surface, f"{name} 회복!", (r.centerx, y), 'big', T.TEXT, 'midtop')
            after = self.res.get('fatigue', self.before)
            parts = [('피로도 ', T.TEXT), (str(self.before), T.BAD), (' → ', T.TEXT), (str(after), T.OK)]
            total = sum(glyph_box(p, 'title').w + (3 if p.startswith(' ') else 0) for p, _ in parts)
            x = r.centerx - total // 2
            for p, color in parts:
                rr = text(surface, p, (x, y + 22), 'title', color)
                x = rr.right
            text(surface, f"{label} 1개 사용", (r.centerx, y + 40), 'body', T.TEXT_SOFT, 'midtop')
        else:
            text(surface, f"{name} 아직 아픔", (r.centerx, y + 4), 'big', T.TEXT, 'midtop')
            text(surface, f"{label} 1개 소모", (r.centerx, y + 26), 'body', T.TEXT_SOFT, 'midtop')
        for b in self.buttons:
            b.draw(surface)
