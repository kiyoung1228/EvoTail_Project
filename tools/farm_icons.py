"""밭 작물 성장 단계 24x24 (음식 아이콘과 같은 윤기 명암). 저장은 4배."""
from PIL import Image
import mon2 as M
from mon2 import Spr, E, R, P, L, U, pal
from food_icons import LEAFG, POT, TOM, ONI, WHEAT, _s

CAB = pal('#f0ffd8', '#c4ec9a', '#94d070', '#5ea44c', '#3a7034')
SOIL = pal('#d8a878', '#b07c4c', '#8a5a34', '#683e22', '#482814')
STEM = pal('#c8f08a', '#8fd86a', '#5cb24e', '#3a8a40', '#24602e')
RICEP = pal('#fffbe0', '#f6eaa8', '#e4cc74', '#b89a48', '#7c6430')
STAKE = pal('#e8c088', '#c08a52', '#9a6434', '#6e4220', '#4a2a14')


def _sp():
    M.OFF[0] = 0; M.SC[:] = [1.0, 0.0, 0.0]; return Spr(24)


def leaf(s, base, tip, w=2.2, P_=LEAFG):
    (x0, y0), (x1, y1) = base, tip
    dx, dy = x1 - x0, y1 - y0; n = (dx * dx + dy * dy) ** .5 or 1
    nx, ny = -dy / n * w, dx / n * w
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    s.part(P([(x0, y0), (mx + nx, my + ny), (x1, y1), (mx - nx, my - ny)]), P_, spec=False)


def mound(s):
    s.part(E((6, 19, 18, 24)), SOIL, spec=False)


def seeded():
    s = _sp(); mound(s); s.dot([(10, 20), (13, 21), (12, 19)], SOIL[0]); return s.done()


def sprout():
    s = _sp(); mound(s)
    s.flat(L([(12, 20), (12, 14)]), STEM[2])
    leaf(s, (12, 15), (6, 11), 2.4); leaf(s, (12, 15), (18, 10), 2.4)
    return s.done()


def growing():
    s = _sp(); mound(s)
    s.flat(L([(12, 20), (12, 8)]), STEM[2])
    leaf(s, (12, 18), (4, 14), 2.6); leaf(s, (12, 17), (20, 12), 2.6)
    leaf(s, (12, 12), (6, 6), 2.4); leaf(s, (12, 11), (18, 5), 2.4); leaf(s, (12, 9), (12, 2), 2.0)
    return s.done()


def ripe_wheat():
    s = _sp(); mound(s)
    for x, top in ((7, 5), (12, 2), (17, 5)):
        s.flat(L([(x, 21), (x, top + 6)]), WHEAT[3])
        s.part(E((x - 2, top, x + 2, top + 8)), WHEAT, spec=True)
        s.dot([(x, top + 2), (x, top + 5)], WHEAT[3])
    leaf(s, (8, 19), (3, 14), 1.8, WHEAT); leaf(s, (16, 19), (21, 14), 1.8, WHEAT)
    return s.done()


def ripe_potato():
    s = _sp()
    leaf(s, (12, 14), (3, 8), 3.0); leaf(s, (12, 14), (21, 8), 3.0); leaf(s, (12, 13), (12, 2), 3.0)
    mound(s)
    s.part(E((5, 17, 11, 22)), POT); s.part(E((13, 16, 19, 21)), POT)
    return s.done()


def ripe_tomato():
    s = _sp(); mound(s)
    s.part(R((16, 3, 17, 21)), STAKE, spec=False)
    s.flat(L([(11, 21), (11, 4)]), STEM[2])
    leaf(s, (11, 16), (3, 13), 2.4); leaf(s, (11, 9), (4, 4), 2.4); leaf(s, (11, 12), (19, 9), 2.2)
    for cx, cy in ((7, 9), (14, 6), (13, 14)):
        s.part(E((cx - 3, cy - 3, cx + 3, cy + 3)), TOM)
    return s.done()


def ripe_rice():
    s = _sp(); mound(s)
    for x, d in ((8, -1), (12, 1), (16, 1)):
        s.flat(L([(x, 21), (x, 8)]), STEM[3])
        s.part(P([(x, 6), (x + 5 * d, 9), (x + 6 * d, 15), (x + 2 * d, 10)]), RICEP)
    leaf(s, (10, 19), (3, 11), 1.8, STEM); leaf(s, (14, 19), (21, 11), 1.8, STEM)
    return s.done()


def ripe_onion():
    s = _sp(); mound(s)
    for x0, x1 in ((10, 6), (12, 12), (14, 18)):
        leaf(s, (12, 15), (x1, 2), 1.6, STEM)
    s.part(U(E((6, 13, 18, 23)), P([(10, 14), (12, 10), (14, 14)])), ONI)
    return s.done()


def ripe_cabbage():
    s = _sp(); mound(s)
    s.part(E((2, 8, 22, 22)), CAB, spec=False)
    s.part(E((5, 6, 19, 19)), CAB)
    s.part(E((8, 8, 16, 15)), CAB, spec=False)
    s.dot([(12, 12), (11, 14), (13, 14)], CAB[3])
    return s.done()


RIPE = {'wheat': ripe_wheat, 'potato': ripe_potato, 'tomato': ripe_tomato, 'rice': ripe_rice, 'onion': ripe_onion, 'cabbage': ripe_cabbage}
STAGES = {'seeded': seeded, 'sprout': sprout, 'growing': growing}


def cabbage_icon():     # 재료 아이콘 (assets/food/cabbage.png, 16)
    s = _s(); s.part(E((1, 3, 15, 15)), CAB, spec=False); s.part(E((3, 2, 13, 13)), CAB)
    s.part(E((5, 4, 11, 10)), CAB, spec=False); s.dot([(8, 7), (7, 8), (9, 8)], CAB[3]); return s.done()


BAGC = {'potato': (200, 150, 90), 'tomato': (228, 84, 70), 'rice': (226, 200, 120), 'wheat': (232, 184, 70),
        'onion': (200, 140, 180), 'cabbage': (110, 190, 90)}


def seed_bag(crop):     # 씨앗 봉투 16: 종이 봉투 + 톱니 윗단(작물 색) + 가운데 작물 그림
    import food_icons as F
    from PIL import ImageDraw
    c = BAGC[crop]; c0 = tuple(min(255, v + 60) for v in c); c2 = tuple(int(v * .6) for v in c)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im); ink = (52, 34, 30)
    d.rectangle((2, 3, 13, 15), fill=(250, 240, 214), outline=ink)
    d.rectangle((3, 4, 12, 6), fill=c); d.line((3, 4, 12, 4), fill=c0)
    for x in range(2, 14, 2): d.point((x, 2), fill=ink); d.point((x + 1, 3), fill=ink)
    d.line((3, 14, 12, 14), fill=(220, 204, 170)); d.line((12, 7, 12, 14), fill=(220, 204, 170))
    ic = (cabbage_icon() if crop == 'cabbage' else getattr(F, crop)()).resize((10, 10), Image.NEAREST)
    im.alpha_composite(ic, (3, 6)); return im


# ================= v2: 손으로 다듬은 작물 (토마토·양배추·밀·쌀) =================
from PIL import ImageDraw
INK = (52, 34, 30)


def outline(im):
    src = im.copy().load(); px = im.load(); n = im.width
    for y in range(n):
        for x in range(n):
            if src[x, y][3]: continue
            nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= x + dx < n and 0 <= y + dy < n and src[x + dx, y + dy][3]]
            if nb:
                c = src[nb[0]][:3]; px[x, y] = tuple(int(c[i] * .25 + INK[i] * .75) for i in range(3)) + (255,)
    return im


def _mound(d):
    d.ellipse((5, 19, 18, 25), fill=(138, 90, 52)); d.line((8, 20, 15, 20), fill=(176, 124, 80)); d.point([(9, 22), (14, 22)], fill=(104, 64, 38))


def ripe_tomato():
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    d.rectangle((18, 1, 19, 21), fill=(196, 140, 84)); d.line((18, 1, 18, 21), fill=(226, 180, 120))          # 지지대
    d.line((10, 21, 10, 3), fill=(62, 132, 62)); d.line((10, 7, 15, 4), fill=(62, 132, 62)); d.line((10, 13, 17, 11), fill=(62, 132, 62))
    d.line((15, 5, 18, 5), fill=(62, 132, 62)); d.line((16, 11, 18, 11), fill=(62, 132, 62))                  # 지지대에 묶임
    for pts in (((10, 3), (7, 0), (12, 1)), ((10, 9), (5, 8), (7, 5)), ((15, 4), (14, 1), (18, 2)), ((10, 14), (14, 16), (13, 13))):
        d.polygon(pts, fill=(104, 190, 84), outline=(40, 104, 52))
    for x0, y0 in ((2, 9), (12, 12), (4, 15)):                                                                # 토마토 7x7
        d.ellipse((x0, y0, x0 + 6, y0 + 6), fill=(232, 58, 48), outline=(132, 26, 30))
        d.arc((x0 + 1, y0 + 1, x0 + 5, y0 + 5), 20, 110, fill=(186, 36, 40))
        d.point([(x0 + 2, y0 + 2), (x0 + 2, y0 + 3)], fill=(255, 190, 176)); d.point((x0 + 3, y0 + 2), fill=(255, 236, 226))
        cx = x0 + 3; d.point([(cx, y0), (cx - 1, y0), (cx + 1, y0), (cx, y0 - 1)], fill=(70, 160, 70))        # 꼭지
    return outline(im)


def ripe_cabbage():
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    for box in ((0, 11, 11, 22), (12, 11, 23, 22), (3, 14, 20, 23)):                                          # 겉잎
        d.ellipse(box, fill=(98, 170, 82), outline=(44, 100, 50))
    for a, b in (((6, 21), (2, 15)), ((17, 21), (21, 15)), ((11, 22), (11, 17))):                             # 겉잎 잎맥
        d.line((a, b), fill=(150, 210, 120))
    d.ellipse((4, 4, 19, 19), fill=(178, 228, 140), outline=(72, 132, 62))                                    # 속통
    d.chord((4, 4, 19, 19), 20, 160, fill=(150, 206, 116))                                                    # 아래 그림자
    d.ellipse((4, 4, 19, 19), outline=(72, 132, 62))
    d.arc((2, 6, 15, 26), 280, 340, fill=(110, 170, 90)); d.arc((8, 6, 21, 26), 200, 260, fill=(110, 170, 90))  # 감싼 잎 선
    d.arc((6, 3, 17, 14), 200, 340, fill=(220, 250, 190))                                                     # 윗잎 테두리 하이라이트
    d.line((11, 8, 11, 16), fill=(206, 244, 170)); d.line((11, 12, 8, 9), fill=(206, 244, 170)); d.line((11, 12, 14, 9), fill=(206, 244, 170))
    d.point([(7, 7), (8, 6)], fill=(240, 255, 220))
    return outline(im)


def ripe_wheat():
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    G0, G1, G2 = (255, 236, 150), (234, 188, 76), (176, 128, 44)
    for x, top in ((6, 4), (11, 1), (16, 4)):
        d.line((x, 21, x, top + 9), fill=G2)
        for i in range(4):                                                                                    # 낟알: 좌우 번갈아
            y = top + 1 + i * 2
            d.rectangle((x - 2, y, x - 1, y + 1), fill=G1); d.point((x - 2, y), fill=G0)
            d.rectangle((x + 1, y + 1, x + 2, y + 2), fill=G1); d.point((x + 1, y + 1), fill=G0)
            d.point((x, y + 1), fill=G2)
        d.point((x, top), fill=G1); d.line((x, top - 1, x, top - 1), fill=G2)
        d.line((x - 3, top + 1, x - 4, top - 2), fill=G1); d.line((x + 3, top + 2, x + 4, top - 1), fill=G1)  # 까끄라기
    d.line((7, 18, 3, 12), fill=G1); d.line((15, 18, 20, 13), fill=G1)                                        # 잎
    return outline(im)


def ripe_rice():
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    GR, GL = (88, 160, 70), (130, 200, 96)
    Y0, Y1, Y2 = (255, 246, 196), (238, 214, 120), (190, 156, 70)
    for x, side in ((8, -1), (12, 1), (15, 1)):
        d.line((x, 21, x, 7), fill=GR)
        # 고개 숙인 이삭: 줄기 끝에서 옆으로 휘어 내려옴
        pts = [(x, 6), (x + side * 2, 5), (x + side * 4, 6), (x + side * 5, 8), (x + side * 6, 11), (x + side * 6, 14)]
        for i, (px_, py_) in enumerate(pts):
            d.rectangle((px_ - 1 if side < 0 else px_, py_, px_ if side < 0 else px_ + 1, py_ + 1), fill=Y1)
            d.point((px_, py_), fill=Y0 if i % 2 == 0 else Y1)
        d.point((pts[-1][0], pts[-1][1] + 2), fill=Y2)
    d.line((9, 19, 3, 10), fill=GL); d.line((13, 19, 20, 9), fill=GL); d.line((10, 20, 6, 13), fill=GR)
    return outline(im)


RIPE.update({'tomato': ripe_tomato, 'cabbage': ripe_cabbage, 'wheat': ripe_wheat, 'rice': ripe_rice})


def cabbage_icon():     # 재료 아이콘 16: 겉잎 + 속통 + 잎맥
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    for box in ((0, 6, 8, 15), (7, 6, 15, 15)): d.ellipse(box, fill=(98, 170, 82), outline=(44, 100, 50))
    d.ellipse((2, 1, 13, 13), fill=(178, 228, 140), outline=(72, 132, 62))
    d.chord((2, 1, 13, 13), 20, 160, fill=(150, 206, 116)); d.ellipse((2, 1, 13, 13), outline=(72, 132, 62))
    d.line((7, 4, 7, 11), fill=(206, 244, 170)); d.line((7, 8, 5, 6), fill=(206, 244, 170)); d.line((7, 8, 9, 6), fill=(206, 244, 170))
    d.point([(4, 4), (5, 3)], fill=(240, 255, 220)); d.line((3, 13, 1, 9), fill=(150, 210, 120)); d.line((12, 13, 14, 9), fill=(150, 210, 120))
    return outline(im)


# ================= v3: 쌀 다시 (벼 이삭 + 쌀 자루) =================
def _grain(d, x, y, c0, c1, c2):
    """낟알 하나 2x3: 밝은 위, 진한 아래"""
    d.rectangle((x, y, x + 1, y + 2), fill=c1); d.point((x, y), fill=c0); d.point((x + 1, y + 2), fill=c2)


def ripe_rice():
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    GR, GD, GL = (96, 168, 74), (58, 122, 56), (150, 206, 104)
    Y0, Y1, Y2 = (255, 244, 176), (236, 196, 84), (184, 136, 48)
    d.line((5, 20, 2, 11), fill=GL); d.line((18, 20, 22, 10), fill=GL); d.line((7, 20, 5, 14), fill=GD)   # 긴 잎
    # 줄기 3개: 위로 올라가다 끝에서 옆으로 휘고, 이삭이 아래로 늘어짐
    for sx, top, side in ((8, 6, -1), (12, 3, 1), (16, 7, 1)):
        d.line((sx, 21, sx, top + 1), fill=GR)
        d.line((sx, top + 1, sx + side, top), fill=GR); d.line((sx + side, top, sx + side * 2, top), fill=Y2)
        hx = sx + side * 3                                                                               # 늘어진 이삭 줄기
        d.line((sx + side * 2, top, hx, top + 1), fill=Y2); d.line((hx, top + 1, hx, top + 9), fill=Y2)
        for i in range(4):                                                                               # 낟알: 이삭 양옆으로
            y = top + 1 + i * 2
            _grain(d, hx - 2, y, Y0, Y1, Y2); _grain(d, hx + 1, y + 1, Y0, Y1, Y2)
        _grain(d, hx - 1 if side > 0 else hx, top + 9, Y0, Y1, Y2)
    return outline(im)


RIPE['rice'] = ripe_rice


def rice_icon():        # 재료 아이콘 16: 열린 삼베 자루 + 흰 쌀 + 흘린 낟알
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    S0, S1, S2 = (232, 204, 150), (204, 168, 108), (156, 120, 70)
    d.polygon([(3, 6), (12, 6), (14, 14), (1, 14)], fill=S1)                                           # 자루 몸통
    d.line((2, 13, 13, 13), fill=S2); d.line((12, 7, 13, 13), fill=S2); d.line((3, 7, 2, 12), fill=S0)
    for x, y in ((5, 9), (9, 11), (7, 12)): d.point((x, y), fill=S2)                                  # 삼베 결
    d.rectangle((2, 5, 13, 6), fill=S0); d.line((2, 6, 13, 6), fill=S2)                                 # 접힌 입구
    d.ellipse((3, 1, 12, 7), fill=(250, 250, 246))                                                     # 쌀 더미
    for x, y in ((5, 3), (8, 2), (10, 4), (6, 5), (9, 5)): d.point((x, y), fill=(214, 214, 206))      # 낟알 결
    d.point([(5, 2), (6, 2)], fill=(255, 255, 255))
    for x, y in ((14, 15), (12, 15), (0, 15)): d.point((x, y), fill=(250, 250, 246))                  # 흘린 쌀
    return outline(im)


def ripe_rice():        # v4: 가늘게 휘어 늘어진 이삭 + 작은 낟알(1x2) 사이사이 띄움
    import math
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    GR, GD, GL = (104, 172, 76), (60, 124, 56), (156, 210, 108)
    Y0, Y1, Y2 = (255, 246, 190), (234, 200, 96), (176, 132, 52)
    d.line((6, 20, 1, 12), fill=GL); d.line((17, 20, 23, 12), fill=GL); d.line((9, 20, 7, 15), fill=GD)
    for sx, top, side, r in ((7, 8, -1, 5), (12, 4, 1, 6), (16, 9, 1, 5)):
        d.line((sx, 21, sx, top + r), fill=GR)
        cx, cy = sx + side * r, top + r                                                         # 휘는 중심
        pts = []
        for i in range(0, 13):
            a = math.pi * (1 + i / 12 * .5) if side > 0 else math.pi * (2 - i / 12 * .5)
            x = round(cx + r * math.cos(a)) if side > 0 else round(cx + r * math.cos(a))
            y = round(cy + r * math.sin(a)); pts.append((x, y))
        # 반원 위쪽 → 옆으로 → 아래로 늘어진 꼬리
        arc = [(round(cx - side * r * math.cos(t)), round(cy - r * math.sin(t))) for t in [k * math.pi / 2 / 8 for k in range(9)]][::-1]
        tail = [(arc[-1][0], arc[-1][1] + k) for k in range(1, 6)]
        path = [(sx, top + r)] + arc + tail
        for (x0, y0), (x1, y1) in zip(path, path[1:]): d.line((x0, y0, x1, y1), fill=Y2)
        for k, (x, y) in enumerate(path[3:], 3):                                                # 낟알: 2칸마다 바깥쪽
            if k % 2: continue
            gx = x + (1 if side > 0 else -1)
            d.point((gx, y), fill=Y0); d.point((gx, y + 1), fill=Y1)
            d.point((x - (1 if side > 0 else -1), y + 1), fill=Y1)
    return outline(im)


RIPE['rice'] = ripe_rice


# ================= v5: 밀·감자 다시 =================
def ripe_wheat():       # 가는 줄기 3개 + 날씬한 이삭(낟알 V자 무늬) + 긴 까끄라기
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    G0, G1, G2 = (255, 238, 160), (232, 190, 80), (170, 122, 40)
    d.line((8, 20, 4, 13), fill=(200, 170, 80)); d.line((15, 20, 20, 14), fill=(200, 170, 80))        # 잎
    for x, top in ((8, 5), (12, 2), (16, 5)):
        d.line((x, 21, x, top + 8), fill=G2)
        for i in range(4):                                                                              # V자 낟알
            y = top + i * 2
            d.point((x - 1, y), fill=G1); d.point((x + 1, y), fill=G1); d.point((x, y + 1), fill=G0)
            d.point((x - 1, y + 1), fill=G2); d.point((x + 1, y + 1), fill=G2)
        d.point((x, top - 1), fill=G1)
        d.line((x - 1, top - 1, x - 2, top - 4), fill=G0); d.line((x + 1, top - 1, x + 2, top - 4), fill=G0)  # 까끄라기
        d.line((x, top - 2, x, top - 4), fill=G0)
    return outline(im)


def ripe_potato():      # 동글동글 잎 덤불 + 흰 꽃 + 흙 위로 보이는 감자 2알
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    L0, L1, L2, LD = (176, 226, 120), (112, 186, 82), (70, 140, 60), (40, 96, 46)
    for bx in ((3, 8, 11, 16), (13, 8, 21, 16), (7, 4, 17, 13), (5, 11, 13, 18), (11, 11, 19, 18)):
        d.ellipse(bx, fill=L1, outline=LD)
    for bx in ((8, 5, 12, 8), (14, 9, 18, 12), (4, 9, 8, 12)): d.ellipse(bx, fill=L0)
    for x, y in ((9, 13), (15, 14), (12, 10)): d.point((x, y), fill=L2)
    for x, y in ((9, 4), (15, 6)):                                                                       # 감자꽃
        d.point([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], fill=(255, 255, 255)); d.point((x, y), fill=(250, 210, 60))
    for bx in ((4, 18, 10, 22), (13, 18, 19, 22)):                                                       # 감자
        d.ellipse(bx, fill=(206, 160, 98), outline=(110, 72, 38)); d.point((bx[0] + 2, bx[1] + 1), fill=(240, 206, 150))
        d.point((bx[0] + 4, bx[1] + 2), fill=(150, 104, 58))
    return outline(im)


RIPE.update({'wheat': ripe_wheat, 'potato': ripe_potato})
# 밭 한 칸을 꽉 채우는 배치 (칸 안 좌표, 원본 ×2 = 48px 그림의 왼쪽 위). 뒷줄 먼저 그림
FILL = [(6, 14), (42, 12), (78, 14), (-2, 46), (34, 48), (70, 46)]


# ================= v6: 양파·밀·감자 다시 =================
def ripe_onion():       # 길쭉한 초록 잎 3갈래 + 반쯤 흙에 묻힌 황금빛 양파
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    g, G, D = (156, 218, 104), (86, 172, 74), (46, 112, 52)
    for pts in (((11, 12), (8, 6), (5, 2)), ((12, 12), (12, 6), (12, 0)), ((13, 12), (16, 7), (19, 3))):
        d.line(pts, fill=G); d.line([(x + 1, y) for x, y in pts], fill=D)
        d.point(pts[-1], fill=g); d.point(((pts[1][0] + pts[2][0]) // 2, (pts[1][1] + pts[2][1]) // 2), fill=g)
    Y0, Y1, Y2 = (255, 230, 168), (234, 178, 96), (178, 112, 54)
    d.polygon([(11, 9), (13, 9), (14, 12), (10, 12)], fill=Y1)                                  # 목
    d.ellipse((6, 11, 18, 22), fill=Y1, outline=Y2)
    d.chord((6, 11, 18, 22), 300, 60, fill=(206, 140, 70)); d.ellipse((6, 11, 18, 22), outline=Y2)   # 오른쪽 그림자
    d.arc((8, 11, 16, 23), 200, 260, fill=Y2); d.arc((8, 11, 16, 23), 280, 340, fill=Y2)       # 껍질 결
    d.ellipse((8, 13, 11, 17), fill=Y0); d.point((9, 14), fill=(255, 250, 230))
    d.ellipse((3, 19, 21, 25), fill=(138, 90, 52)); d.line((6, 20, 18, 20), fill=(176, 124, 80))   # 흙 (아래 반 덮음)
    d.point([(8, 22), (15, 22)], fill=(104, 64, 38))
    return outline(im)


def ripe_wheat():       # 이삭 4개 (3칸 폭, 낟알 줄무늬) + 까끄라기 + 금빛 잎
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    _mound(d)
    Y0, Y1, Y2, Y3 = (255, 240, 170), (240, 200, 90), (204, 150, 52), (150, 100, 34)
    d.line((9, 21, 4, 13), fill=(206, 182, 84)); d.line((14, 21, 20, 13), fill=(206, 182, 84))
    for cx, top, lean in ((6, 6, -1), (10, 3, 0), (14, 4, 0), (18, 7, 1)):
        d.line((cx - lean, 21, cx, top + 8), fill=Y3)
        for r in range(8):
            y = top + r
            row = (Y1, Y0, Y1) if r % 2 == 0 else (Y2, Y1, Y2)
            if r in (0, 7): row = (None, Y1, None)
            for i, c in enumerate(row):
                if c: d.point((cx - 1 + i, y), fill=c)
        d.point((cx, top - 1), fill=Y0); d.point((cx - 1, top - 2), fill=Y0); d.point((cx + 1, top - 2), fill=Y0)
        d.point((cx - 2, top - 1), fill=Y1); d.point((cx + 2, top), fill=Y1)
    return outline(im)


def ripe_potato():      # 작은 잎 덤불 + 흙 위로 드러난 감자 3알 (감자가 주인공)
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    L0, L1, LD = (170, 224, 116), (98, 178, 78), (48, 112, 52)
    d.line((12, 16, 9, 10), fill=LD); d.line((12, 16, 15, 9), fill=LD); d.line((12, 16, 12, 8), fill=LD)
    for bx in ((5, 6, 11, 11), (13, 5, 19, 10), (9, 2, 15, 8), (4, 10, 9, 14), (15, 10, 20, 14)):
        d.ellipse(bx, fill=L1, outline=LD); d.point((bx[0] + 2, bx[1] + 1), fill=L0); d.point((bx[0] + 1, bx[1] + 2), fill=L0)
    d.point([(12, 1), (11, 2), (13, 2), (12, 3)], fill=(255, 255, 255)); d.point((12, 2), fill=(250, 210, 60))   # 꽃
    d.ellipse((1, 15, 23, 25), fill=(138, 90, 52)); d.line((4, 16, 20, 16), fill=(176, 124, 80))
    for bx in ((2, 14, 10, 20), (14, 14, 22, 20), (8, 17, 16, 23)):                                       # 감자 3알
        d.ellipse(bx, fill=(214, 168, 104), outline=(112, 70, 36))
        d.arc((bx[0] + 1, bx[1] + 1, bx[2] - 1, bx[3] - 1), 10, 120, fill=(170, 120, 66))
        d.point((bx[0] + 2, bx[1] + 2), fill=(244, 214, 160)); d.point((bx[0] + 3, bx[1] + 2), fill=(244, 214, 160))
        d.point((bx[0] + 5, bx[1] + 3), fill=(140, 92, 48))
    return outline(im)


RIPE.update({'onion': ripe_onion, 'wheat': ripe_wheat, 'potato': ripe_potato})


def ripe_potato():      # v7: 잎을 따로따로(틈 있게) + 줄기 보이게
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    L0, L1, L2, LD = (176, 228, 120), (104, 182, 80), (70, 144, 62), (40, 100, 48)
    for a, b in (((12, 16), (6, 9)), ((12, 16), (18, 8)), ((12, 16), (12, 5)), ((12, 14), (4, 13)), ((12, 14), (20, 13))):
        d.line((a, b), fill=L2)
    for cx, cy in ((6, 8), (18, 7), (12, 4), (4, 12), (20, 12)):                                          # 잎 하나 = 4x3 타원
        d.ellipse((cx - 2, cy - 2, cx + 2, cy + 1), fill=L1, outline=LD)
        d.point((cx - 1, cy - 1), fill=L0); d.point((cx + 1, cy), fill=L2)
    for cx, cy in ((9, 10), (15, 10)):
        d.ellipse((cx - 2, cy - 1, cx + 1, cy + 1), fill=L1, outline=LD); d.point((cx - 1, cy), fill=L0)
    d.point([(12, 0), (11, 1), (13, 1), (12, 2)], fill=(255, 255, 255)); d.point((12, 1), fill=(250, 210, 60))
    d.ellipse((1, 15, 23, 25), fill=(138, 90, 52)); d.line((4, 16, 20, 16), fill=(176, 124, 80))
    for bx in ((2, 14, 10, 20), (14, 14, 22, 20), (8, 17, 16, 23)):
        d.ellipse(bx, fill=(214, 168, 104), outline=(112, 70, 36))
        d.arc((bx[0] + 1, bx[1] + 1, bx[2] - 1, bx[3] - 1), 10, 120, fill=(170, 120, 66))
        d.point((bx[0] + 2, bx[1] + 2), fill=(244, 214, 160)); d.point((bx[0] + 3, bx[1] + 2), fill=(244, 214, 160))
        d.point((bx[0] + 5, bx[1] + 3), fill=(140, 92, 48))
    return outline(im)


RIPE['potato'] = ripe_potato


# ================= v8: 손으로 찍은 감자·양파·밀 (crops_v8.py) =================
import crops_v8 as _V8
RIPE.update({'potato': _V8.potato, 'onion': _V8.onion, 'wheat': _V8.wheat})
