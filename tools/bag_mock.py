"""가방 후보 A(상점형 탭 + 상세 + 바로 쓰기) / B(배낭 슬롯 + 아래 정보 줄) / B2(누구에게? 창)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
from ui_mock import paste, button, gauge, chip, ribbon, text_mid

W, H = 640, 360
K.BTN.setdefault('gold', [(104, 62, 10), (184, 120, 24), (232, 170, 36), (255, 220, 110)])
INK = K.INK
RED = K.BTN['red'][1]; GREEN = K.BTN['green'][1]
REPO = Path('/home/claude/evotail_project/assets')

# (id, 이름, 개수, 분류, 보조 글)
ITEMS = [('snack', '기본 간식', 3, 'feed', '포만감 +35'),
         ('toy_ball', '장난감 공', 1, 'feed', '기분 +20 · 남은 3/5'),
         ('toy_doll', '인형', 1, 'feed', '기분 +35 · 남은 3/3'),
         ('food_butter_potato', '감자버터구이', 1, 'food', '포만감 +40 · 기분 +15'),
         ('food_perfect_rabbit_stew', '대성공 토끼고기 스튜', 1, 'food', '포만감 +150 · 기분 +75'),
         ('burned_food', '탄 요리', 2, 'food', '포만감 +5 · 기분 -10'),
         ('heal_basic', '기본 회복 포션', 2, 'potion', '치료 50% · 피로도 -10'),
         ('heal_advanced', '고급 회복 포션', 1, 'potion', '치료 90% · 피로도 -30'),
         ('potion_attack', '공격력 포션', 1, 'potion', '전투 전 공격력 +100'),
         ('battle_bandage', '전투 응급 붕대', 2, 'potion', '전투 중 체력 +80'),
         ('equip_shell', '등껍질 보호대', 1, 'gear', '방어력 +50'),
         ('egg_special', '특수 부화 알', 1, 'gear', '특급 60%'),
         ('potato', '감자', 4, 'mat', '요리 재료'), ('tomato', '토마토', 8, 'mat', '요리 재료'),
         ('beef', '소고기', 2, 'mat', '요리 재료'), ('pork', '돼지고기', 4, 'mat', '요리 재료'),
         ('lucky_rabbit', '행운의 토끼고기', 1, 'mat', '요리 재료'), ('milk', '우유', 2, 'mat', '요리 재료'),
         ('seed_potato', '감자 씨앗', 3, 'mat', '밭에 심기')]
TABS = [('전체', None, 'bag'), ('먹이', 'feed', 'snack'), ('요리', 'food', 'butter_potato'), ('포션', 'potion', 'heal_basic'),
        ('장비·알', 'gear', 'equip_claw'), ('재료', 'mat', 'potato')]


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def tl(t, f): return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(t, font=f)


def bag_icon():
    im = Image.open(REPO / 'ui' / 'icon_bag.png').convert('RGBA')
    bb = im.getbbox(); im = im.crop(bb)
    f = max(1, max(im.size) // 16 + (1 if max(im.size) % 16 else 0))
    return im.resize((im.width // f, im.height // f), Image.NEAREST)


def icon(k, n=1):
    import meat_icons as MI
    if k in MI.MEATS: return MI.MEATS[k]().resize((16 * n, 16 * n), Image.NEAREST)
    star = k.startswith('food_perfect_')
    base = k.replace('food_perfect_', '').replace('food_', '')
    for p in (REPO / 'items' / f'{k}.png', REPO / 'food' / f'{base}.png'):
        if p.exists():
            im = Image.open(p).convert('RGBA').resize((16, 16), Image.NEAREST)
            if star:
                d = ImageDraw.Draw(im); d.polygon([(12, 0), (13, 2), (15, 2), (13, 4), (14, 6), (12, 5), (10, 6), (11, 4), (9, 2), (11, 2)], fill=(255, 214, 60), outline=INK)
            return im.resize((16 * n, 16 * n), Image.NEAREST)
    return bag_icon()


def bg():
    base = B.backdrop() if hasattr(B, 'backdrop') else None
    if base is None:
        m = Image.open(REPO / 'map' / 'map_day.png').convert('RGBA').resize((W, H), Image.NEAREST)
        base = ImageEnhance.Brightness(m).enhance(.45)
    B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '가방', 'red')
    return base


# ---------------- A: 상점형 ----------------
def bag_A(out):
    base = bg()
    used = sum(1 for _ in ITEMS)
    B.card(base, 154, 32, 112, 22); paste(base, bag_icon(), (160, 37)); text_mid(base, 216, 43, f'아이템 {used}종', K.F_BODY(), K.TEXT)
    B.panel(base, 8, 58, 112, 298)
    for i, (t, cat, ic) in enumerate(TABS):
        y = 68 + i * 46; on = i == 1
        B.card(base, 16, y, 96, 40, on)
        paste(base, icon(ic) if ic != 'bag' else bag_icon(), (22, y + 12))
        n = sum(1 for it in ITEMS if cat is None or it[3] == cat)
        K.draw_text(base, (42, y + 15), t, K.F_TITLE() if on else K.F_BODY(), K.TEXT, 'lm')
        K.draw_text(base, (42, y + 29), f'{n}종', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    B.panel(base, 124, 58, 304, 298); B.panel(base, 432, 58, 200, 298)
    feed = [it for it in ITEMS if it[3] == 'feed']
    for i, (k, n, cnt, cat, sub) in enumerate(feed):
        x = 134 + (i % 3) * 96; y = 68 + (i // 3) * 84
        B.card(base, x, y, 92, 80, k == 'snack')
        paste(base, icon(k, 2), (x + 30, y + 6))
        chip(base, x + 58, y + 26, f'×{cnt}', 'gray')
        K.draw_text(base, (x + 46, y + 50), n, K.F_SMALL(), K.TEXT, 'mm')
        if k.startswith('toy'):
            gauge(base, x + 14, y + 62, 64, 8, int(sub.split('남은 ')[1].split('/')[0]), int(sub.split('/')[1]), 'orange')
    B.corners(base, 134, 68, 225, 147)
    K.draw_text(base, (276, 330), '먹이·장난감은 여기서 바로 먹이기', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    # 상세 + 누구에게 줄까?
    d = ImageDraw.Draw(base); d.rectangle((446, 72, 618, 120), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, icon('snack', 2), (516, 80))
    K.draw_text(base, (446, 134), '기본 간식', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 446, 144, '먹이', 'orange'); K.draw_text(base, (618, 152), '보유 3', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    paste(base, K.icon('meat'), (446, 168))
    K.draw_text(base, (464, 174), '포만감 +35', K.F_BODY(), GREEN, 'lm')
    K.draw_text(base, (446, 194), '누구에게 줄까?', K.F_TITLE(), K.TEXT, 'lm')
    rows = [('dealer_normal_01', '불씨여우', 80, False, None), ('tank_normal_01', '물방울수달', 10, True, None),
            ('healer_normal_01', '산들오리', 60, False, '사냥 중')]
    for i, (aid, n, f, sel, busy) in enumerate(rows):
        y = 204 + i * 30
        B.card(base, 446, y, 172, 28, sel)
        sp = B.spr(aid, 1, 1)
        if busy: sp = ImageEnhance.Brightness(ImageEnhance.Color(sp).enhance(0)).enhance(1.1)
        paste(base, sp.crop((2, 4, 26, 28)), (448, y + 2))
        K.draw_text(base, (474, y + 9), n, K.F_BODY(), K.TEXT_SOFT if busy else K.TEXT, 'lm')
        if busy: K.draw_text(base, (612, y + 9), busy, K.F_SMALL(), K.TEXT_SOFT, 'rm')
        elif f < 30 and not sel: chip(base, 572, y + 2, '배고픔', 'red')
        gauge(base, 474, y + 17, 90, 6, f, 100, 'red' if f < 30 else 'green')
        if sel:
            gauge(base, 474, y + 17, 90, 6, f + 35, 100, 'green')
            gauge(base, 474, y + 17, 90, 6, f, 100, 'red')
            K.draw_text(base, (612, y + 9), f'{f}→{f + 35}', K.F_SMALL(), GREEN, 'rm')
    button(base, 446, 300, 172, 40, '물방울수달에게 주기', 'green', icon='heart', sub='기본 간식 1개')
    save(base, out)


def bag_A2(out):
    """A안: 재료처럼 여기서 못 쓰는 아이템을 고른 모습"""
    base = bg()
    B.card(base, 154, 32, 112, 22); paste(base, bag_icon(), (160, 37)); text_mid(base, 216, 43, f'아이템 {len(ITEMS)}종', K.F_BODY(), K.TEXT)
    B.panel(base, 8, 58, 112, 298)
    for i, (t, cat, ic) in enumerate(TABS):
        y = 68 + i * 46; on = i == 5
        B.card(base, 16, y, 96, 40, on)
        paste(base, icon(ic) if ic != 'bag' else bag_icon(), (22, y + 12))
        n = sum(1 for it in ITEMS if cat is None or it[3] == cat)
        K.draw_text(base, (42, y + 15), t, K.F_TITLE() if on else K.F_BODY(), K.TEXT, 'lm')
        K.draw_text(base, (42, y + 29), f'{n}종', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    B.panel(base, 124, 58, 304, 298); B.panel(base, 432, 58, 200, 298)
    mats = [it for it in ITEMS if it[3] == 'mat']
    for i, (k, n, cnt, cat, sub) in enumerate(mats):
        x = 134 + (i % 3) * 96; y = 68 + (i // 3) * 84
        B.card(base, x, y, 92, 80, k == 'lucky_rabbit')
        paste(base, icon(k, 2), (x + 30, y + 6)); chip(base, x + 58, y + 26, f'×{cnt}', 'gray')
        lines = ['행운의', '토끼고기'] if k == 'lucky_rabbit' else [n]
        for j, ln in enumerate(lines): K.draw_text(base, (x + 46, y + 50 + j * 12), ln, K.F_SMALL(), K.TEXT, 'mm')
    B.corners(base, 228, 150, 321, 231)
    d = ImageDraw.Draw(base); d.rectangle((446, 72, 618, 120), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, icon('lucky_rabbit', 2), (516, 80))
    K.draw_text(base, (446, 134), '행운의 토끼고기', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 446, 144, '재료', 'brown'); K.draw_text(base, (618, 152), '보유 1', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    K.draw_text(base, (446, 176), '쓰는 곳', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    B.card(base, 446, 184, 172, 40)
    paste(base, icon('rabbit_stew'), (452, 196)); K.draw_text(base, (474, 198), '토끼고기 스튜', K.F_BODY(), K.TEXT, 'lm')
    K.draw_text(base, (474, 212), '주방 레시피 ★★★★★', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (446, 236), '얻는 곳: 사냥터 · 달토끼 언덕', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (446, 252), '판매가 170코인', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 446, 268, 82, 26, '주방으로', 'orange', icon='home', f=K.F_BODY())
    button(base, 536, 268, 82, 26, '상점에 팔기', 'red', icon='coin', f=K.F_SMALL())
    button(base, 446, 300, 172, 40, '여기서는 못 씀', 'gray', sub='요리 재료')
    save(base, out)


# ---------------- B: 배낭 슬롯 ----------------
def leather(base, x, y, w, h):
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((x, y, x + w, y + h), 10, fill=(150, 96, 56), outline=INK)
    d.rounded_rectangle((x + 4, y + 4, x + w - 4, y + h - 4), 8, outline=(196, 140, 86))
    for sx in range(x + 12, x + w - 8, 8):                                  # 바느질
        d.line((sx, y + 8, sx + 3, y + 8), fill=(236, 200, 140)); d.line((sx, y + h - 8, sx + 3, y + h - 8), fill=(236, 200, 140))
    d.rounded_rectangle((x + 12, y + 14, x + w - 12, y + h - 14), 6, fill=(96, 60, 36), outline=(70, 42, 24))


def bag_B(out, popup=False):
    base = bg()
    # 위: 분류 칩 (필터)
    cx = 156
    for i, (t, cat, ic) in enumerate(TABS):
        w = int(tl(t, K.F_BODY())) + 30
        B.card(base, cx, 32, w, 22, i == 0); paste(base, icon(ic) if ic != 'bag' else bag_icon(), (cx + 4, 35))
        K.draw_text(base, (cx + 22, 43), t, K.F_BODY(), K.TEXT, 'lm'); cx += w + 4
    leather(base, 8, 58, 624, 222)
    # 슬롯 10 x 4 (40칸)
    sx0, sy0, sz, gap = 30, 78, 54, 4
    cols = {'feed': (255, 236, 200), 'food': (255, 226, 214), 'potion': (226, 236, 255), 'gear': (236, 226, 255), 'mat': (232, 244, 214)}
    d = ImageDraw.Draw(base)
    for i in range(40):
        x = sx0 + (i % 10) * (sz + gap); y = sy0 + (i // 10) * 46
        hh = 42
        if i < len(ITEMS):
            k, n, cnt, cat, sub = ITEMS[i]
            d.rectangle((x, y, x + sz - 1, y + hh - 1), fill=cols[cat], outline=INK)
            d.line((x + 1, y + 1, x + sz - 2, y + 1), fill=(255, 255, 255))
            paste(base, icon(k, 2), (x + 11, y + 3))
            if cnt > 1 or k.startswith('toy'):
                t = f'{cnt}' if not k.startswith('toy') else sub.split('남은 ')[1].split('/')[0] + '회'
                text_mid(base, x + sz - 10, y + hh - 7, t, K.F_SMALL(), (255, 255, 255), INK)
        else:
            d.rectangle((x, y, x + sz - 1, y + hh - 1), fill=(120, 80, 50), outline=(70, 42, 24))
            d.line((x + 1, y + hh - 2, x + sz - 2, y + hh - 2), fill=(140, 96, 62))
    sel = 4
    x = sx0 + (sel % 10) * (sz + gap); y = sy0 + (sel // 10) * 46
    B.corners(base, x - 2, y - 2, x + sz + 1, y + 43)
    text_mid(base, 600, 268, f'{len(ITEMS)} / 40칸', K.F_SMALL(), (236, 210, 170))
    # 아래 정보 줄
    B.panel(base, 8, 284, 624, 72)
    d = ImageDraw.Draw(base); d.rectangle((18, 294, 70, 346), fill=(255, 226, 214), outline=K.WOOD[2])
    paste(base, icon('food_perfect_rabbit_stew', 3), (20, 296))
    K.draw_text(base, (80, 302), '대성공 토끼고기 스튜', K.F_BIG(), K.TEXT, 'lm')
    cw = chip(base, 80, 314, '요리', 'red'); chip(base, 80 + cw + 3, 314, '대성공 1.5배', 'gold')
    K.draw_text(base, (80, 342), '포만감 +150 · 기분 +75 · 피로도 -60', K.F_SMALL(), GREEN, 'lm')
    K.draw_text(base, (400, 302), '보유 1', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 464, 294, 158, 26, '동물에게 주기', 'green', icon='heart', f=K.F_BODY())
    button(base, 464, 324, 158, 22, '상점에 팔기 · 판매가 N', 'red', icon='coin', f=K.F_SMALL())
    if popup:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 110)); base.alpha_composite(ov)
        B.panel(base, 180, 70, 280, 220)
        ribbon(base, 250, 62, 140, '누구에게 줄까?', 'green')
        rows = [('dealer_normal_01', '불씨여우', 80, False, None), ('tank_normal_01', '물방울수달', 10, True, None),
                ('healer_normal_01', '산들오리', 60, False, '사냥 중'), ('dealer_normal_02', '불씨다람쥐', 80, False, '아픔')]
        for i, (aid, n, f, sel_, busy) in enumerate(rows):
            y = 88 + i * 36
            B.card(base, 194, y, 252, 32, sel_)
            sp = B.spr(aid, 1, 1)
            if busy == '사냥 중': sp = ImageEnhance.Brightness(ImageEnhance.Color(sp).enhance(0)).enhance(1.1)
            paste(base, sp, (198, y + 2))
            K.draw_text(base, (230, y + 10), n, K.F_BODY(), K.TEXT_SOFT if busy == '사냥 중' else K.TEXT, 'lm')
            gauge(base, 230, y + 20, 120, 7, min(100, f + 100) if sel_ else f, 100, 'green')
            if sel_: gauge(base, 230, y + 20, 120, 7, f, 100, 'red')
            K.draw_text(base, (440, y + 22), f'{f}→100' if sel_ else (busy or f'{f}'), K.F_SMALL(), GREEN if sel_ else (RED if busy == '아픔' else K.TEXT_SOFT), 'rm')
            if f < 30 and not sel_: chip(base, 396, y + 4, '배고픔', 'red')
        button(base, 194, 238, 160, 40, '물방울수달에게 주기', 'green', icon='heart', sub='포만감 10 → 100')
        button(base, 362, 238, 84, 40, '취소', 'brown')
    save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    bag_A(out / 'bag_A1_feed.png'); bag_A2(out / 'bag_A2_material.png')
    bag_B(out / 'bag_B1_slots.png'); bag_B(out / 'bag_B2_give.png', popup=True)
    print('ok')
