"""상점 (A안): 탭 6개 / 가운데 3열 상품 칸 / 오른쪽 상세 + 수량 + 구매·판매. 알은 바로 부화.

목업 docs/mockups/shop/shop_A1_potion.png, shop_A2_equip.png, shop_A3_egg.png.
게임 규칙은 없다: 상품 목록·가격·효과·종류는 get_shop_catalog 값, 구매·판매·부화는 백엔드 명령
(buy_item, sell_item, hatch_egg). 실패하면 백엔드가 준 이유가 알림으로 뜬다.
"""
import math
import pygame

from .. import theme as T
from .. import widgets as W
from .. import items as I
from ..app import Scene
from ..widgets import (text, text_in, glyph_box, fit_width, panel, card, card_inner, ribbon, chip, chip_width, icon,
                       gauge, tooltip, record, wrap2, Button, BUTTON_H)
from .hatch import HatchOverlay, rays

TAB_PANEL = pygame.Rect(9, 58, 112, 296)
GRID_PANEL = pygame.Rect(125, 58, 302, 296)
DETAIL = pygame.Rect(432, 58, 199, 296)
TAB_H, TAB_STEP = 38, 46
CELL = (91, 87)
GRID = (GRID_PANEL.x + 10, GRID_PANEL.y + 10, 96, 92)    # 시작 x, y, 가로 간격, 세로 간격
COLS, ROWS = 3, 3
ART = pygame.Rect(DETAIL.x + 12, DETAIL.y + 12, DETAIL.w - 24, 66)
QTY_MAX = 99


class ShopScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.tab = 'food'
        self.selected = {}            # 탭별 고른 상품
        self.qty = 1
        self.scroll = 0               # 상품 칸 줄 넘김
        self.catalog = {}
        self.icons = I.ItemIcons()
        self.buttons = []
        self.hover = None
        self.back = Button((12, 32, max(56, Button.width_for('지도', icon=True)), BUTTON_H), '지도',
                           lambda: app.go('map'), 'brown', icon='back')

    def enter(self):
        self.catalog = self.app.call('get_shop_catalog') or self.catalog
        self.scroll = 0
        self._fix_selection()

    # ---------- 백엔드 값 ----------
    def stack(self):
        return self.app.state.get('inventory', {}).get('stackable', {})

    def owned(self, item):
        """가진 개수 (장난감은 개별 물건 목록)."""
        if (self.catalog.get(item) or {}).get('kind') == 'toy':
            return sum(1 for t in self.app.state.get('inventory', {}).get('toys', []) if t.get('id') == item)
        return self.stack().get(item, 0)

    def products(self, tab=None):
        tab = tab or self.tab
        if tab == 'sell':
            return [k for k, v in self.catalog.items() if v.get('sell') is not None and self.owned(k) > 0]
        kinds = next(t[3] for t in I.TABS if t[0] == tab)
        return [k for k, v in self.catalog.items() if v.get('kind') in kinds and v.get('buy') is not None]

    def item(self):
        return self.selected.get(self.tab)

    def _fix_selection(self):
        items = self.products()
        if self.selected.get(self.tab) not in items:
            self.selected[self.tab] = items[0] if items else None
            self.qty = 1
        if self.tab == 'sell' and self.item():
            self.qty = max(1, min(self.qty, self.owned(self.item())))

    # ---------- 칸 위치 ----------
    @staticmethod
    def tab_rect(i):
        return pygame.Rect(TAB_PANEL.x + 8, TAB_PANEL.y + 9 + i * TAB_STEP, TAB_PANEL.w - 16, TAB_H)

    @staticmethod
    def cell_rect(i):
        return pygame.Rect(GRID[0] + (i % COLS) * GRID[2], GRID[1] + (i // COLS) * GRID[3], *CELL)

    def visible(self):
        items = self.products()
        rows = math.ceil(len(items) / COLS)
        self.scroll = max(0, min(self.scroll, rows - ROWS))
        return items[self.scroll * COLS:(self.scroll + ROWS) * COLS]

    # ---------- 입력 ----------
    def go_tab(self, tab):
        self.tab = tab
        self.scroll = 0
        self.qty = 1
        self._fix_selection()

    def handle(self, event):
        if self.back.handle(event):
            return
        for b in list(self.buttons):
            if b.handle(event):
                return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.go('map')
        elif event.type == pygame.MOUSEWHEEL and GRID_PANEL.collidepoint(W.mouse_pos()):
            self.scroll = max(0, self.scroll - event.y)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, t in enumerate(I.TABS):
                if self.tab_rect(i).collidepoint(event.pos):
                    self.go_tab(t[0])
                    return
            for i, item in enumerate(self.visible()):
                if self.cell_rect(i).collidepoint(event.pos):
                    if item != self.item():
                        self.qty = 1
                    self.selected[self.tab] = item
                    return

    # ---------- 명령 ----------
    def set_qty(self, n):
        top = self.owned(self.item()) if self.tab == 'sell' else QTY_MAX
        self.qty = max(1, min(max(1, top), n))

    def buy(self):
        item, n = self.item(), self.qty
        label = I.item_label(item, self.catalog)
        self.app.act('buy_item', f"{T.josa(label, '을')} {n}개 샀다", icon='coin', item=item, quantity=n)
        self._fix_selection()

    def sell(self):
        item, n = self.item(), self.qty
        label = I.item_label(item, self.catalog)
        self.app.act('sell_item', lambda d: f"{T.josa(label, '을')} {n}개 팔았다 · +{d.get('earned', 0):,}코인",
                     icon='coin', item=item, quantity=n)
        self._fix_selection()

    def hatch(self, egg=None):
        egg = egg or self.item()
        self.app.open_overlay(HatchOverlay(self.app, egg, on_again=self.hatch))

    def update(self, dt):
        self._fix_selection()
        self.buttons = []
        item = self.item()
        if not item:
            return
        spec = self.catalog[item]
        x, w = DETAIL.x + 12, DETAIL.w - 24
        selling = self.tab == 'sell'
        if spec.get('kind') == 'egg' and not selling:
            n = self.owned(item)
            self.buttons.append(Button((x, 272, w, 22), '지금 부화', self.hatch, 'green', enabled=n > 0, icon='heart'))
            price = spec['buy']
            self.buttons.append(Button((x, 300, w, 42), '구매', self.buy, 'orange',
                                       sub=f"1개 · {price:,}코인"))
            self.qty = 1
            return
        # 수량 - N +
        self.buttons.append(Button((x, 270, 22, BUTTON_H), '-', lambda: self.set_qty(self.qty - 1), 'brown',
                                   enabled=self.qty > 1))
        top = self.owned(item) if selling else QTY_MAX
        self.buttons.append(Button((x + 60, 270, 22, BUTTON_H), '+', lambda: self.set_qty(self.qty + 1), 'brown',
                                   enabled=self.qty < top))
        if selling:
            total = spec['sell'] * self.qty
            self.buttons.append(Button((x, 300, w, 42), '판매', self.sell, 'red',
                                       sub=f"{self.qty}개 · +{total:,}코인"))
        else:
            total = spec['buy'] * self.qty
            self.buttons.append(Button((x, 300, w, 42), '구매', self.buy, 'orange',
                                       sub=f"{self.qty}개 · {total:,}코인"))

    # ---------- 그리기 ----------
    def draw(self, surface):
        surface.blit(W.background('assets/shop/shop.png'), (0, 0))
        self.hover = None
        self.back.draw(surface)
        ribbon(surface, (78, 33, 92, 18), '상점', 'red')
        self._draw_tabs(surface)
        self._draw_grid(surface)
        self._draw_detail(surface)
        for b in self.buttons:
            b.draw(surface)
        if self.hover:
            tooltip(surface, self.hover[0], self.hover[1], 'below')

    def _draw_tabs(self, surface):
        panel(surface, TAB_PANEL)
        for i, (tid, label, ic, _) in enumerate(I.TABS):
            r = self.tab_rect(i)
            card(surface, r, selected=tid == self.tab)
            surface.blit(self.icons.get(ic, 1), (r.x + 6, r.centery - 8))
            color = T.BAD if tid == 'sell' else T.TEXT
            text_in(surface, label, (r.x + 25, r.y + 2, r.w - 27, r.h - 4), 'title' if tid == self.tab else 'body',
                    color, align='left', tag='shop')

    def _draw_grid(self, surface):
        panel(surface, GRID_PANEL)
        items = self.products()
        for i, item in enumerate(self.visible()):
            self._draw_cell(surface, self.cell_rect(i), item)
        rows = math.ceil(len(items) / COLS)
        if rows > ROWS:
            more = f"{self.scroll + 1}-{self.scroll + ROWS} / {rows}줄 · 휠"
            text(surface, more, (GRID_PANEL.right - 10, GRID_PANEL.bottom - 8), 'small', T.TEXT_SOFT,
                 anchor='bottomright')
        msg = None
        if not items:
            msg = '팔 수 있는 물건 없음' if self.tab == 'sell' else '파는 물건 없음'
        elif self.tab == 'egg':
            msg = '알은 사면 바로 부화 가능'
        elif self.tab == 'sell':
            msg = '장난감은 안 쓴 것만 판매'
        if msg and len(items) <= COLS * (ROWS - 1):
            text(surface, msg, (GRID_PANEL.centerx, GRID_PANEL.bottom - 64), 'body', T.TEXT_SOFT, 'center')

    def _draw_cell(self, surface, r, item):
        spec = self.catalog[item]
        card(surface, r, selected=item == self.item())
        img = self.icons.get(item, 2)
        ir = img.get_rect(midtop=(r.centerx, r.y + 6))
        surface.blit(img, ir)
        n = self.owned(item)
        if n > 0:                # 가진 개수 칩 (그림 오른쪽 아래)
            chip(surface, (ir.right + 10, ir.bottom + 2), f'×{n}', 'gray', anchor='bottomright')
        label = spec.get('label', item)
        lines = wrap2(label, r.w - 4 - 4, 'body')
        top = r.y + 40 + (15 if len(lines) == 1 else 0) // 2
        for k, line in enumerate(lines):
            text_in(surface, line, (r.x + 2, top + k * 15, r.w - 4, 15), 'body', tag='shop')
        if ''.join(lines).replace(' ', '') != label.replace(' ', '') and r.collidepoint(W.mouse_pos()):
            self.hover = (label, r)
        price = spec['sell'] if self.tab == 'sell' else spec['buy']
        ps = f"{price:,}"
        w = 14 + glyph_box(ps, 'title').w
        x = r.centerx - w // 2
        y = r.bottom - 17
        icon(surface, 'coin', (x, y + 1))
        box = pygame.Rect(r.x + 2, y - 2, r.w - 4, 17)          # 쉼표가 아래로 내려와 17
        g = text_in(surface, ps, (x + 14, box.y, glyph_box(ps, 'title').w + 4, box.h), 'title', T.TEXT, log=False)
        record(ps, pygame.Rect(x, g.y, w, g.h), box, 'shop')

    def _draw_detail(self, surface):
        panel(surface, DETAIL)
        item = self.item()
        if not item:
            return
        spec = self.catalog[item]
        x = DETAIL.x + 12
        # 그림 칸 (알은 진한 배경 + 빛줄기)
        if spec.get('kind') == 'egg':
            pygame.draw.rect(surface, T.WOOD[0], ART)
            rays(surface, ART, ART.center, 0.0, (236, 184, 52), 70, n=14)
            pygame.draw.rect(surface, T.INK, ART, 1)
        else:
            card(surface, ART)
        img = self.icons.get(item, 3)
        surface.blit(img, img.get_rect(center=ART.center))
        y = ART.bottom + 6
        text(surface, spec.get('label', item), (x, y), 'big')
        klabel, kcolor = I.KIND_LABEL.get(spec.get('kind'), ('물건', 'gray'))
        chip(surface, (x, y + 20), klabel, kcolor)
        y += 40
        if spec.get('kind') == 'egg' and self.tab != 'sell':
            self._draw_egg_rate(surface, item, x, y)
        else:
            for ic, msg, color in I.effect_lines(item, spec, self.catalog):
                if ic:
                    icon(surface, ic, (x, y + 1))
                text(surface, msg, (x + (15 if ic else 0), y), 'body', color)
                y += 15
        # 보유 / 수량 / 합계
        n = self.owned(item)
        text(surface, f"보유 {n}", (x, 254), 'body', T.TEXT_SOFT)
        if spec.get('kind') == 'egg' and self.tab != 'sell':
            return
        qbox = pygame.Rect(x + 24, 270, 34, BUTTON_H)
        card(surface, qbox)
        text_in(surface, str(self.qty), card_inner(qbox), 'title', tag='shop')
        price = spec['sell'] if self.tab == 'sell' else spec['buy']
        total = f"{'+' if self.tab == 'sell' else ''}{price * self.qty:,}"
        tw = glyph_box(total, 'title').w
        tx = DETAIL.right - 12 - tw
        icon(surface, 'coin', (tx - 14, 274))
        text_in(surface, total, (tx - 2, 270, tw + 4, BUTTON_H), 'title', log=False)

    def _draw_egg_rate(self, surface, item, x, y):
        rate = I.EGG_SPECIAL_RATE.get(item, 0)
        text(surface, '특급 등장 확률', (x, y), 'body')
        text(surface, f'{rate}%', (DETAIL.right - 12, y - 2), 'big', T.shade('gold', 1), anchor='topright')
        gauge(surface, (x, y + 16, DETAIL.w - 24, 10), rate, 100, 'gold')
        others = [f"{I.item_label(k, self.catalog)} {v}%" for k, v in I.EGG_SPECIAL_RATE.items() if k != item]
        if others:
            text(surface, others[0], (x, y + 32), 'body', T.TEXT_SOFT)
        text(surface, '못 가진 동물 우선' if item == 'egg_special' else '중복이 나올 수 있음', (x, y + 47), 'body',
             T.TEXT_SOFT)

    def toast_anchor(self):
        return 'topright', (T.WIDTH - 8, T.HEADER_H + 4)
