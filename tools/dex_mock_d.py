"""도감 D안: 펼친 책 + 가방처럼 책 오른쪽 옆에 천 태그(일반 / 특급).
태그 하나 = 한 등급 15마리만 (왼쪽 쪽), 칸을 누르면 오른쪽 쪽에 정보."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import battle_mock as B
import bag_mock as BM
import dex_mock as D
from ui_mock import paste, chip, ribbon, text_mid

INK = K.INK
TAGS = (('normal', '일반', 'egg_basic', (240, 230, 208)), ('special', '특급', 'egg_special', (255, 226, 150)))
SHIFT = -22          # 오른쪽 쪽 내용(A안 좌표)을 왼쪽으로 옮김


LEATHER = [(70, 36, 30), (104, 54, 40), (134, 74, 52), (166, 100, 70)]   # 표지 가죽 어두움→밝음
GOLDC = [(120, 80, 20), (196, 146, 50), (240, 200, 90), (255, 236, 160)]
PAGE_L, PAGE_R, SPINE = (14, 300), (306, 598), 303


def _paper(x, x0, x1):
    """종이 색: 가운데 접힌 곳일수록·바깥 가장자리일수록 살짝 어둡게"""
    r, g, b = K.PAPER[2]
    dist = abs(x - SPINE)
    k = max(0, 24 - dist) ** 1.5 * 0.33 + (4 if x in (x0 + 1, x1 - 1) else 0)
    return (int(r - k), int(g - k * 1.1), int(b - k * 1.3))


def book(base):
    d = ImageDraw.Draw(base)
    # ① 표지 (가죽) + 금박 테두리
    d.rectangle((4, 54, 607, 358), fill=LEATHER[1], outline=INK)
    d.line((5, 55, 606, 55), fill=LEATHER[3]); d.line((5, 357, 606, 357), fill=LEATHER[0])
    for x in range(10, 602, 6):                                  # 금박 점선
        d.point((x, 57), fill=GOLDC[1]); d.point((x, 355), fill=GOLDC[1])
    # ② 종이 묶음 두께 (쪽 아래·바깥에 겹친 종이 3장)
    for (x0, x1), side in ((PAGE_L, -1), (PAGE_R, 1)):
        for i in (3, 2, 1):
            ox = side * i; c = (206 - i * 14, 186 - i * 14, 150 - i * 14)
            ex0 = x0 + (ox if side < 0 else 0); ex1 = x1 + (ox if side > 0 else 0)
            d.rectangle((ex0, 62 + i, ex1, 350 + i), fill=c, outline=K.WOOD[0])
    # ③ 펼친 두 쪽: 가운데로 갈수록 위아래가 살짝 말려 들어감 + 접힌 그림자
    for (x0, x1) in (PAGE_L, PAGE_R):
        for x in range(x0, x1 + 1):
            dist = abs(x - SPINE); dip = max(0, (24 - dist) // 5)
            top, bot = 62 + dip, 350 - dip
            if x in (x0, x1): d.line((x, top, x, bot), fill=K.WOOD[0]); continue
            d.line((x, top, x, bot), fill=_paper(x, x0, x1))
            d.point((x, top), fill=K.WOOD[0]); d.point((x, bot), fill=K.WOOD[0])
            d.point((x, top + 1), fill=K.PAPER[3])
    d.line((SPINE - 1, 62, SPINE - 1, 350), fill=(150, 112, 76)); d.line((SPINE, 60, SPINE, 352), fill=INK)
    d.line((SPINE + 1, 62, SPINE + 1, 350), fill=(150, 112, 76))
    # ④ 쪽 모서리 장식 (바깥 네 귀퉁이에 꺾인 줄)
    orn = (214, 186, 140)
    for (cx, cy, sx, sy) in ():
        d.line((cx, cy, cx + sx * 10, cy), fill=orn); d.line((cx, cy, cx, cy + sy * 10), fill=orn)
        d.point((cx + sx * 3, cy + sy * 3), fill=orn)
    # ⑤' 왼쪽 쪽 아래 귀퉁이 접힘 (책장 넘기는 느낌)
    fx, fy, n = PAGE_L[0], 350, 14
    d.polygon([(fx - 1, fy - n), (fx - 1, fy + 1), (fx + n, fy + 1)], fill=(192, 172, 136))       # 접혀서 드러난 아래 종이
    d.polygon([(fx, fy - n), (fx + n, fy), (fx + n, fy - n)], fill=(232, 212, 172), outline=K.WOOD[0])  # 접힌 종이 뒷면
    d.line((fx + 2, fy - n + 1, fx + n - 1, fy - n + 1), fill=(250, 236, 206))
    # ⑤ 표지 네 귀퉁이 금속 모서리
    for (cx, cy, sx, sy) in ((4, 54, 1, 1), (607, 54, -1, 1), (4, 358, 1, -1), (607, 358, -1, -1)):
        pts = [(cx, cy), (cx + sx * 13, cy), (cx, cy + sy * 13)]
        d.polygon(pts, fill=GOLDC[1], outline=INK)
        d.line((cx + sx * 2, cy + sy * 2, cx + sx * 8, cy + sy * 2), fill=GOLDC[3])
        d.point((cx + sx * 4, cy + sy * 4), fill=GOLDC[0])
    # ⑥ 책갈피 끈 (접힌 곳에서 아래로 늘어짐, 끝은 V자)
    rx = SPINE - 6
    d.rectangle((rx, 60, rx + 4, 356), fill=(196, 52, 60), outline=INK)
    d.line((rx + 1, 61, rx + 1, 355), fill=(236, 96, 100))
    d.polygon([(rx, 356), (rx + 4, 356), (rx + 4, 360), (rx + 2, 358), (rx, 360)], fill=(196, 52, 60))


def tags(base, cur):
    """가방 천 탭과 같은 모양: 고른 태그는 8px 더 튀어나옴, 색 = 등급 색"""
    d = ImageDraw.Draw(base)
    for i, (rar, lab, egg, tint) in enumerate(TAGS):
        y = 86 + i * 62; on = rar == cur; x1 = 639 if on else 635
        d.rectangle((600, y, x1, y + 56), fill=tint if on else tuple(int(v * .82) for v in tint), outline=INK)
        d.line((601, y + 1, x1 - 1, y + 1), fill=(255, 255, 255) if on else tint)
        for yy in range(y + 4, y + 54, 4): d.point((x1 - 3, yy), fill=K.WOOD[2])   # 바느질 점선
        cx = (607 + x1) // 2 + 1
        paste(base, BM.icon(egg, 1), (cx - 8, y + 4))
        text_mid(base, cx, y + 30, lab, K.F_TITLE(), (150, 96, 10) if rar == 'special' else K.TEXT)
        n = sum(1 for k in D.OWNED if D.CH[k]['rarity'] == rar)
        text_mid(base, cx, y + 45, f'{n}/15', K.F_SMALL(), K.TEXT_SOFT)


def tags_front(base, cur):
    """표지 위로 나온 부분만 다시 그림 (태그가 표지 안쪽에서 나오는 것처럼)"""
    full = base.copy(); tags(full, cur)
    base.alpha_composite(full.crop((608, 80, 640, 220)), (608, 80))


def left_page(base, rar, sel):
    n = sum(1 for k in D.OWNED if D.CH[k]['rarity'] == rar)
    title = '특급' if rar == 'special' else '일반'
    K.draw_text(base, (24, 77), title, K.F_TITLE(), (176, 110, 20) if rar == 'special' else K.TEXT, 'lm')
    K.draw_text(base, (28 + D.tl(title, K.F_TITLE()), 78), '3단계까지' if rar == 'special' else '2단계까지', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (290, 78), f'{n} / 15', K.F_SMALL(), K.TEXT, 'rm')
    dd = ImageDraw.Draw(base); dd.line((22, 88, 292, 88), fill=(214, 186, 140))
    dd.polygon([(157, 85), (160, 88), (157, 91), (154, 88)], fill=(214, 186, 140))
    for r, role in enumerate(('dealer', 'tank', 'healer')):
        y = 94 + r * 80
        keys = [k for k in D.ORDER if D.CH[k]['role'] == role and D.CH[k]['rarity'] == rar]
        el = D.CH[keys[0]]['element']
        chip(base, 20, y + 14, D.ROLE[role], D.ROLE_C[role]); chip(base, 20, y + 34, D.ELEM[el], D.ELEM_C[el])
        own = sum(1 for k in keys if k in D.OWNED)
        K.draw_text(base, (22, y + 60), f'{own}/5', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        for c, k in enumerate(keys):
            D.cell(base, 56 + c * 48, y, 45, 74, k, sel=(k == sel), gold=(rar == 'special'))
    K.draw_text(base, (157, 339), '동물을 눌러 확인하자!', K.F_SMALL(), K.TEXT_SOFT, 'mm')


def right_page(base, key):
    tmp = Image.new('RGBA', (640, 360), (0, 0, 0, 0))
    (D.right_page_owned if key in D.OWNED else D.right_page_missing)(tmp, key)
    base.alpha_composite(tmp.crop((320, 62, 630, 350)), (320 + SHIFT, 62))


def screen(rar, sel, out):
    base = BM.bg(); ribbon(base, 78, 33, 70, '도감', 'red')
    D.progress(base, 454, 31)
    tags(base, rar); book(base); tags_front(base, rar); left_page(base, rar, sel); right_page(base, sel)
    BM.save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = D.REPO / 'assets' / 'fonts'; B.SPR = D.REPO / 'assets' / 'sprites'
    o = Path(sys.argv[1] if len(sys.argv) > 1 else '../dex'); o.mkdir(exist_ok=True)
    screen('normal', 'tank_normal_02', o / 'dex_D1_normal.png')
    screen('special', 'dealer_special_02', o / 'dex_D2_special.png')
    screen('special', 'healer_special_04', o / 'dex_D3_missing.png')
    print('ok')


def _menu_icon(name, size=16):
    im = Image.open(D.REPO / 'assets' / 'ui' / f'icon_{name}.png').convert('RGBA'); im = im.crop(im.getbbox())
    f = max(1, -(-max(im.size) // size)); return im.resize((im.width // f, im.height // f), Image.NEAREST)


def _star(d, cx, cy, fill=(255, 210, 60)):
    pts = [(0, -6), (2, -2), (6, -2), (3, 1), (4, 6), (0, 3), (-4, 6), (-3, 1), (-6, -2), (-2, -2)]
    d.polygon([(cx + x, cy + y) for x, y in pts], fill=fill, outline=INK)


def _scene_frame(base, x0, y0, x1, y1):
    """액자 속 그림: 하늘·구름·언덕·풀밭 위에 가진 동물들"""
    d = ImageDraw.Draw(base)
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=K.WOOD[1], outline=INK)
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=K.WOOD[3])
    W_, H_ = x1 - x0 + 1, y1 - y0 + 1
    pic = Image.new('RGBA', (W_, H_)); p = ImageDraw.Draw(pic)
    sky = [(150, 206, 240), (170, 218, 244), (190, 228, 246), (208, 236, 248)]
    for y in range(H_): p.line((0, y, W_, y), fill=sky[min(3, y * 4 // max(1, H_ * 2 // 3))])
    for (cx, cy, w) in ((40, 12, 22), (W_ - 60, 9, 28), (150, 18, 16)):                       # 구름
        p.rectangle((cx - w // 2, cy, cx + w // 2, cy + 4), fill=(255, 255, 255))
        p.rectangle((cx - w // 4, cy - 3, cx + w // 4, cy), fill=(255, 255, 255))
    p.ellipse((-40, H_ - 46, 150, H_ + 30), fill=(140, 198, 116))                               # 언덕
    p.ellipse((110, H_ - 40, W_ + 40, H_ + 30), fill=(126, 188, 104))
    p.rectangle((0, H_ - 20, W_, H_), fill=(118, 186, 92)); p.line((0, H_ - 20, W_, H_ - 20), fill=(150, 210, 110))
    for gx in range(3, W_ - 2, 9): p.line((gx, H_ - 22, gx + 1, H_ - 20), fill=(90, 150, 70))
    for fx in range(14, W_, 37): p.point((fx, H_ - 8), fill=(255, 240, 120)); p.point((fx + 17, H_ - 4), fill=(255, 170, 190))
    base.alpha_composite(pic, (x0, y0))
    faces = [k for k in D.ORDER if k in D.OWNED][:5]
    step = (x1 - x0) // (len(faces) + 1)
    for i, k in enumerate(faces):
        im = D.spr(k, D.OWNED[k], 2, crop=True); cx = x0 + step * (i + 1)
        d.ellipse((cx - 18, y1 - 12, cx + 18, y1 - 6), fill=(90, 150, 70))
        paste(base, im, (cx - im.width // 2, y1 - 9 - im.height))


def _stat_card(base, x, y, w, icon, big, lab, col=K.TEXT):
    B.card(base, x, y, w, 46)
    paste(base, icon, (x + 6, y + 7))
    K.draw_text(base, (x + 26, y + 15), big, K.F_BIG(), col, 'lm')
    text_mid(base, x + w // 2, y + 35, lab, K.F_SMALL(), K.TEXT_SOFT)


def summary_page(base, rar):
    """아무도 안 골랐을 때 오른쪽 쪽 = 도감 첫 장 (전체 현황)"""
    from ui_mock import gauge
    x0, x1 = 312, 594; cx = (x0 + x1) // 2 + 2; d = ImageDraw.Draw(base)
    # 제목 + 양옆 장식
    text_mid(base, cx, 80, 'EvoTail 동물 도감', K.F_BIG(), K.TEXT)
    for sx in (-1, 1):
        ex = cx + sx * 74
        d.line((ex, 80, ex + sx * 40, 80), fill=(196, 160, 110)); d.line((ex, 82, ex + sx * 30, 82), fill=(214, 186, 140))
        d.polygon([(ex + sx * 44, 77), (ex + sx * 47, 80), (ex + sx * 44, 83), (ex + sx * 41, 80)], fill=(196, 146, 50), outline=INK)
    text_mid(base, cx, 96, '섬 마을에서 만난 동물 기록', K.F_SMALL(), K.TEXT_SOFT)
    # 액자 그림
    _scene_frame(base, x0 + 10, 108, x1 - 8, 178)
    # 현황 카드 4개
    tot = len(D.OWNED); nn = sum(1 for k in D.OWNED if D.CH[k]['rarity'] == 'normal'); ns = tot - nn
    done = sum(1 for k, st in D.OWNED.items() if st == D.CH[k]['max_stage'])
    star = Image.new('RGBA', (16, 16)); _star(ImageDraw.Draw(star), 8, 8)
    cw = 66
    cards = [(_menu_icon('pokedex'), f'{tot}', '전체 / 30', K.TEXT), (BM.icon('egg_basic'), f'{nn}', '일반 / 15', K.TEXT),
             (BM.icon('egg_special'), f'{ns}', '특급 / 15', (176, 110, 20)), (star, f'{done}', '최종 진화', (120, 80, 170))]
    for i, (ic, big, lab, col) in enumerate(cards):
        _stat_card(base, x0 + 8 + i * (cw + 4), 192, cw, ic, big, lab, col)
    # 속성별 모은 수
    K.draw_text(base, (x0 + 10, 252), '속성별', K.F_TITLE(), K.TEXT, 'lm')
    for r, (role, el) in enumerate((('dealer', 'fire'), ('tank', 'water'), ('healer', 'wind'))):
        y = 262 + r * 13
        own = sum(1 for k in D.OWNED if D.CH[k]['role'] == role)
        K.draw_text(base, (x0 + 12, y + 5), f'{D.ROLE[role]} · {D.ELEM[el]}', K.F_SMALL(), K.TEXT, 'lm')
        gauge(base, x0 + 76, y, 150, 10, own, 10, D.ELEM_C[el])
        K.draw_text(base, (x1 - 12, y + 5), f'{own} / 10', K.F_SMALL(), K.TEXT, 'rm')
    d.rectangle((x0 + 8, 310, x1 - 8, 340), fill=(255, 246, 224), outline=K.WOOD[2])
    paste(base, BM.icon('egg_basic'), (x0 + 16, 317))
    K.draw_text(base, (x0 + 38, 319), '왼쪽 동물을 눌러 확인하자!', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (x0 + 38, 332), '옆 태그로 일반 · 특급 넘기기', K.F_SMALL(), K.TEXT_SOFT, 'lm')


def screen_empty(rar, out):
    base = BM.bg(); ribbon(base, 78, 33, 70, '도감', 'red')
    D.progress(base, 454, 31)
    tags(base, rar); book(base); tags_front(base, rar); left_page(base, rar, None); summary_page(base, rar)
    BM.save(base, out)


if __name__ == '__main__':
    o = Path(sys.argv[1] if len(sys.argv) > 1 else '../dex')
    screen_empty('normal', o / 'dex_D0_first.png')
