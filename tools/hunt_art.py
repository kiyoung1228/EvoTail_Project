"""사냥터 동물 도트 (28x28, 동물 도트 크기) + 돼지고기 재료 아이콘."""
from PIL import Image, ImageDraw
import mon2 as M
from mon2 import Spr, E, R, P, L, U, pal, INK, W, PINK

FEATHER = pal('#ffffff', '#ffffff', '#fffaf2', '#fbf4e6', '#ddcdb2')
COMB = pal('#ffd0c8', '#ff7a6a', '#e8403a', '#b02630', '#741a24')
BEAK = pal('#fff6c0', '#ffd860', '#f4b03a', '#c8801e', '#8a5414')
PIGP = pal('#ffffff', '#ffe8ee', '#ffd6e0', '#ffc2d2', '#ee96b0')
SNOUT = pal('#fff0f4', '#ffccd8', '#ffb0c4', '#f79ab4', '#d8728e')
COWW = pal('#ffffff', '#ffffff', '#fbfbfd', '#f4f2f8', '#cdc8d8')
SPOT = (70, 60, 74)
MUZ = pal('#fff6f6', '#ffe0e0', '#ffcfd2', '#f7b8be', '#d8909a')
HORN = pal('#fffbe8', '#fff4d0', '#f6e2a8', '#ecd08c', '#c09c5c')
MOONR = pal('#ffffff', '#ffffff', '#f6f2ff', '#ece6fc', '#c4b8ec')
MOONG = pal('#fffbe0', '#fff0a0', '#ffd860', '#e8b030', '#a87418')


def _s():
    M.OFF[0] = 0; M.SC[:] = M.MINI; return Spr()


def chicken():            # 꼬꼬닭: 하얀 동글 몸 + 빨간 볏 + 노란 부리
    s = _s()
    s.part(U(E((10, 2, 13, 6)), E((12, 1, 15, 5)), E((14, 2, 17, 6))), COMB, spec=False)
    s.part(E((5, 12, 10, 20)), FEATHER, spec=False)                    # 날개 (뒤)
    s.part(E((17, 12, 22, 20)), FEATHER, spec=False)
    s.part(E((7, 4, 20, 24)), FEATHER)
    s.part(P([(12, 13), (16, 13), (14, 16)]), BEAK, spec=False)
    s.part(E((13, 16, 15, 19)), COMB, spec=False, rim=False)            # 육수
    s.eyes_cute(10, 10, 6, h=2)
    s.flat(U(L([(11, 24), (11, 26)]), L([(16, 24), (16, 26)]), L([(10, 26), (12, 26)]), L([(15, 26), (17, 26)])), BEAK[2])
    return s.done()


def pig():                # 꿀꿀돼지: 분홍 몸 + 큰 코 + 세모 귀
    s = _s()
    s.part(P([(6, 6), (10, 4), (10, 10)]), PIGP, spec=False); s.part(P([(21, 6), (17, 4), (17, 10)]), PIGP, spec=False)
    s.part(E((4, 6, 23, 24)), PIGP)
    s.part(E((9, 14, 18, 20)), SNOUT, spec=False)
    s.dot([(11, 16), (11, 17), (15, 16), (15, 17)], SNOUT[3])
    s.eyes_cute(9, 10, 8, h=2)
    s.part(U(E((7, 22, 11, 26)), E((16, 22, 20, 26))), PIGP, spec=False)
    s.dot([(23, 15), (24, 14), (24, 13), (23, 12)], PIGP[3])            # 꼬리 살짝
    return s.done()


def cow():                # 음매소: 하양+검은 무늬, 분홍 주둥이, 작은 뿔
    s = _s()
    s.part(P([(8, 5), (6, 1), (10, 4)]), HORN, spec=False); s.part(P([(19, 5), (21, 1), (17, 4)]), HORN, spec=False)
    s.part(E((2, 7, 8, 11)), COWW, spec=False); s.part(E((19, 7, 25, 11)), COWW, spec=False)   # 귀
    s.part(E((5, 3, 22, 24)), COWW)
    s.flat(U(E((6, 5, 11, 10)), E((17, 14, 21, 19)), E((7, 17, 10, 20))), SPOT)
    s.part(E((9, 16, 18, 22)), MUZ)
    s.dot([(11, 18), (16, 18)], MUZ[3])
    s.eyes_cute(9, 10, 7, h=2)
    s.part(U(E((7, 22, 11, 26)), E((16, 22, 20, 26))), COWW, spec=False)
    s.flat(U(R((13, 22, 15, 24))), BEAK[2])                              # 방울
    return s.done()


def moon_rabbit():        # 달토끼: 연보라 하양, 긴 귀, 이마에 금빛 초승달
    s = _s()
    s.part(E((7, 0, 11, 12)), MOONR, spec=False); s.part(E((16, 0, 20, 12)), MOONR, spec=False)
    s.part(E((8, 2, 10, 10)), PIGP, spec=False, rim=False); s.part(E((17, 2, 19, 10)), PIGP, spec=False, rim=False)
    s.part(E((5, 8, 22, 25)), MOONR)
    s.part(U(E((12, 9, 16, 13))), MOONG, spec=False, rim=False)          # 초승달
    s.flat(E((13, 8, 17, 12)), MOONR[1])
    s.eyes_cute(9, 15, 7, h=2)
    s.dot([(13, 19), (14, 19)], PIGP[3]); s.dot([(13, 20)], INK)
    s.part(U(E((7, 23, 11, 26)), E((16, 23, 20, 26))), MOONR, spec=False)
    im = s.done(); px = im.load()
    for x, y in ((2, 4), (25, 6), (24, 18)):                             # 반짝이
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if not px[x + dx, y + dy][3]: px[x + dx, y + dy] = ((255, 240, 150, 255) if (dx, dy) != (0, 0) else (255, 255, 255, 255))
    return im


CRITTERS = {'chicken_coop': chicken, 'pig_pen': pig, 'ranch': cow, 'rabbit_hill': moon_rabbit}


def pork_icon():          # 돼지고기 16: 분홍 살코기 + 흰 지방 테두리 + 마블
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    o = (90, 40, 46)
    d.rounded_rectangle((1, 3, 14, 13), 3, fill=(250, 240, 236), outline=o)          # 지방
    d.rounded_rectangle((3, 5, 13, 12), 2, fill=(236, 120, 130))                       # 살
    d.line((4, 6, 11, 6), fill=(255, 168, 172)); d.line((4, 11, 12, 11), fill=(196, 84, 98))
    for x, y in ((6, 8), (9, 9), (11, 7), (7, 10)): d.point((x, y), fill=(255, 214, 214))
    d.point([(3, 4), (4, 4)], fill=(255, 255, 255))
    return im


if __name__ == '__main__':
    ims = [f() for f in CRITTERS.values()] + [pork_icon().resize((28, 28), Image.NEAREST)]
    o = Image.new('RGBA', (len(ims) * 176 + 8, 184), (150, 200, 120, 255))
    for i, im in enumerate(ims): o.alpha_composite(im.resize((168, 168), Image.NEAREST), (8 + i * 176, 8))
    o.save('../critters.png')


def pork_icon():          # v2: 뼈 붙은 돼지고기 (살 + 지방 테두리 + 흰 뼈)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im); o = (90, 40, 46)
    d.polygon([(2, 5), (6, 2), (12, 3), (14, 7), (13, 12), (8, 14), (3, 12), (1, 8)], fill=(252, 238, 230), outline=o)
    d.polygon([(3, 6), (6, 4), (11, 5), (12, 8), (11, 11), (7, 12), (4, 11), (3, 8)], fill=(234, 112, 124))
    d.line((5, 5, 10, 5), fill=(255, 160, 168)); d.line((5, 11, 10, 11), fill=(190, 76, 92))
    for x, y in ((6, 7), (9, 9), (10, 6)): d.point((x, y), fill=(255, 214, 214))
    d.ellipse((6, 7, 9, 10), fill=(255, 252, 240), outline=(200, 186, 170)); d.point((7, 8), fill=(255, 255, 255))
    return im


def pork_icon():          # v3: 삼겹살 한 덩이 (살·지방 겹 줄무늬 + 껍질)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im); o = (96, 44, 48)
    d.polygon([(1, 5), (13, 3), (15, 11), (3, 13)], fill=(240, 120, 128), outline=o)
    layers = [((2, 6), (13, 4), (255, 236, 228)), ((2, 8), (14, 6), (226, 100, 112)), ((2, 9), (14, 8), (255, 240, 232)),
              ((3, 11), (15, 9), (236, 116, 126))]
    for (a, b, c) in layers: d.line((a, b), fill=c); d.line(((a[0], a[1] + 1), (b[0], b[1] + 1)), fill=c) if c[0] > 250 else None
    d.line((2, 5, 13, 3), fill=(200, 140, 110))                                           # 껍질
    d.line((3, 12, 14, 10), fill=(186, 74, 90))
    d.polygon([(1, 5), (13, 3), (15, 11), (3, 13)], outline=o)
    return im
