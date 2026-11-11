"""양파·밀·감자 v8: 손으로 찍는 도장(잎 한 장, 낟알 한 줄) 방식"""
from PIL import Image, ImageDraw

C = {'k': (36, 86, 44), 'G': (62, 134, 60), 'g': (104, 180, 80), 'l': (170, 224, 118), 'L': (208, 240, 150),
     'h': (150, 170, 70), 'w': (255, 255, 255), 'y': (250, 206, 70), 'v': (196, 170, 230),
     's': (140, 92, 54), 'S': (178, 126, 80), 'd': (100, 62, 36), 'o': (70, 44, 28),
     'p': (218, 172, 108), 'P': (168, 118, 64), 'a': (244, 214, 160),
     'Y': (255, 238, 160), 'u': (236, 192, 84), 'U': (196, 144, 50), 'b': (140, 96, 34), 'e': (190, 196, 96),
     'n': (250, 214, 150), 'N': (226, 160, 86), 'M': (170, 102, 50), 'm': (120, 66, 34)}


def put(px, x, y, ch):
    if ch != '.' and 0 <= x < 24 and 0 <= y < 24: px[x, y] = C[ch] + (255,)


def stamp(px, x, y, rows):
    for j, r in enumerate(rows):
        for i, ch in enumerate(r): put(px, x + i, y + j, ch)


def soil(px, x0=3, x1=20, y=19):
    """흙더미: 둥근 봉긋한 모양 (위 밝은 줄, 아래 진한 점)"""
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    d.ellipse((x0, y, x1, y + 7), fill=C['s'] + (255,), outline=C['o'] + (255,))
    d.line((x0 + 3, y + 1, x1 - 3, y + 1), fill=C['S'] + (255,))
    for x in range(x0 + 4, x1 - 2, 4): d.point((x, y + 3), fill=C['d'] + (255,))
    sp = im.load()
    for yy in range(24):
        for xx in range(24):
            if sp[xx, yy][3] and not px[xx, yy][3]: px[xx, yy] = sp[xx, yy]


LEAF_R = ['.kk.', 'klgk', 'kggk', '.kk.']          # 잎 한 장 (밝은 쪽 왼위)
LEAF_Y = ['.kk.', 'kLlk', 'klhk', '.kk.']          # 다 자라 끝이 노릇한 잎


def potato():
    im = Image.new('RGBA', (24, 24)); px = im.load()
    soil(px, 2, 21, 19)
    for x, y in ((11, 18), (11, 17), (11, 16), (10, 15), (12, 15)): put(px, x, y, 'G')    # 줄기
    leaves = [(10, 3, LEAF_R), (6, 5, LEAF_R), (14, 5, LEAF_Y), (3, 8, LEAF_R), (8, 8, LEAF_R), (12, 7, LEAF_R),
              (16, 8, LEAF_R), (1, 12, LEAF_Y), (5, 11, LEAF_R), (10, 11, LEAF_R), (14, 11, LEAF_R), (18, 12, LEAF_R),
              (6, 14, LEAF_R), (13, 14, LEAF_Y)]
    for x, y, L_ in leaves: stamp(px, x, y, L_)
    stamp(px, 10, 0, ['.w.', 'wyw', '.w.']); stamp(px, 16, 2, ['.v.', 'vyv', '.v.'])    # 감자꽃
    stamp(px, 15, 19, ['.oo.', 'opPo'])                                                    # 흙 사이로 살짝
    stamp(px, 5, 20, ['oaPo'])
    return im


def onion():
    im = Image.new('RGBA', (24, 24)); px = im.load()
    # 잎: 대롱 3개를 넓게 벌림 (사이 틈), 1칸 밝음 + 1칸 그림자, 끝은 바깥으로 휨
    tubes = [((10, 12), (4, 2), -1), ((12, 12), (12, 0), 0), ((14, 12), (20, 2), 1)]
    for (x0, y0), (x1, y1), bend in tubes:
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1):
            x = round(x0 + (x1 - x0) * t / n); y = round(y0 + (y1 - y0) * t / n)
            put(px, x - 1, y, 'k'); put(px, x, y, 'l' if t > n * .45 else 'g'); put(px, x + 1, y, 'G'); put(px, x + 2, y, 'k')
        put(px, x1 + bend, y1 - 1, 'k'); put(px, x1, y1 - 1, 'k'); put(px, x1 + 1, y1 - 1, 'k')
    for (x, y) in ((8, 8), (16, 8)): put(px, x, y, 'L')
    stamp(px, 7, 11, ['...oooo...', '..onnNNo..', '.onnNNNMo.', 'onnNNNNNMo', 'onYNNNNMMo', 'onNNNNMMMo', '.oNNMMMMo.', '..oooooo..'])
    soil(px, 2, 21, 17)
    return im


def wheat():
    im = Image.new('RGBA', (24, 24)); px = im.load()
    soil(px, 4, 19, 20)
    # 잎 (노릇한 초록)
    for (x0, y0), (x1, y1) in (((9, 20), (4, 12)), ((14, 20), (19, 12)), ((11, 20), (7, 15))):
        n = max(abs(x1 - x0), abs(y1 - y0))
        for t in range(n + 1): put(px, round(x0 + (x1 - x0) * t / n), round(y0 + (y1 - y0) * t / n), 'e')
    EAR = ['.Y.', 'YuY', 'uUu', 'YuY', 'uUu', 'YuY', 'uUu', '.U.']                # 이삭 3x8, 낟알 줄무늬
    for x, top in ((5, 4), (9, 1), (13, 2), (17, 5)):
        for y in range(top + 8, 21): put(px, x + 1, y, 'b')                              # 줄기
        stamp(px, x, top, EAR)
        for i in range(3): put(px, x - 1 - i // 2, top - 1 - i, 'Y'); put(px, x + 3 + i // 2, top - 1 - i, 'Y')   # 까끄라기
        put(px, x + 1, top - 1, 'Y')
        for j in range(8):                                                                # 이삭 테두리
            put(px, x - 1, top + j, 'b') if j not in (0, 7) else None
            put(px, x + 3, top + j, 'b') if j not in (0, 7) else None
    return im


if __name__ == '__main__':
    row = [potato(), onion(), wheat()]
    o = Image.new('RGBA', (3 * 200 + 16, 208), (132, 84, 50, 255))
    for i, im in enumerate(row): o.alpha_composite(im.resize((192, 192), Image.NEAREST), (8 + i * 200, 8))
    o.save('../v8.png')


# ================= v9: 동글동글 양파 / 감자 알 위주 =================
ONION_BULB = ['.....oooo.....', '...oonnnNoo...', '..onnnnNNNMo..', '.onnYnnNNNNMo.', '.onYYnNNNNNMo.',
              'onnYnnNNNNNMMo', 'onnnnNNNNNMMMo', 'onnnnNNNNNMMMo', '.onnNNNNNMMMo.', '.oNNNNNNMMMMo.',
              '..ooNNNMMMoo..', '....oooooo....']
POT_BIG = ['...ooooo...', '.oopppppoo.', 'oapppppppPo', 'oaappPppPPo', 'opppppppPPo', 'oppPpppPPPo', '.oPPPPPPPo.', '..ooooooo..']
POT_SMALL = ['..oooo..', '.oappPo.', 'oaapppPo', 'opPppPPo', '.oPPPPo.', '..oooo..']


def _soil_back(px, box):
    im = Image.new('RGBA', (24, 24)); d = ImageDraw.Draw(im)
    d.ellipse(box, fill=C['s'] + (255,), outline=C['o'] + (255,))
    d.line((box[0] + 3, box[1] + 1, box[2] - 3, box[1] + 1), fill=C['S'] + (255,))
    for x in range(box[0] + 4, box[2] - 2, 4): d.point((x, box[1] + 3), fill=C['d'] + (255,))
    sp = im.load()
    for y in range(24):
        for x in range(24):
            if sp[x, y][3]: px[x, y] = sp[x, y]


def onion():
    im = Image.new('RGBA', (24, 24)); px = im.load()
    _soil_back(px, (2, 17, 21, 24))
    # 짧은 초록 싹 3개 (4칸)
    for pts in (((11, 7), (10, 6), (9, 5), (8, 4)), ((12, 7), (12, 6), (12, 5), (12, 3)), ((13, 7), (14, 6), (15, 5), (16, 4))):
        for i, (x, y) in enumerate(pts):
            put(px, x, y, 'l' if i == len(pts) - 1 else 'g'); put(px, x + 1, y, 'G')
    stamp(px, 11, 7, ['oNo'])                                                                 # 마른 목
    stamp(px, 5, 8, ONION_BULB)
    for y in range(11, 18): put(px, 9 if y < 15 else 10, y, 'N')                             # 껍질 결
    for y in range(10, 18): put(px, 14, y, 'M')
    put(px, 8, 11, 'w')
    for x in (10, 12, 14): put(px, x, 20, 'a')                                               # 뿌리
    # 테두리 (싹)
    out = im.copy().load()
    for y in range(24):
        for x in range(24):
            if out[x, y][3]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < 24 and 0 <= y + dy < 24 and out[x + dx, y + dy][3] and out[x + dx, y + dy][:3] in (C['g'], C['G'], C['l']):
                    px[x, y] = C['k'] + (255,); break
    return im


def potato():
    im = Image.new('RGBA', (24, 24)); px = im.load()
    _soil_back(px, (1, 16, 22, 24))
    stamp(px, 8, 9, ['.kk.kk.', 'kllkglk', '.kgGgk.', '...G...', '...G...'])                 # 작은 싹
    stamp(px, 1, 13, POT_SMALL)
    stamp(px, 15, 12, [r[::-1] for r in POT_SMALL])
    stamp(px, 6, 14, POT_BIG)
    for x, y in ((3, 15), (17, 14)): put(px, x, y, 'a')
    return im


def potato():           # v10: 감자 색을 더 노랗게, 흙은 더 진하게, 알을 흙 위로
    C.update({'p': (236, 194, 116), 'P': (196, 140, 74), 'a': (252, 230, 176)})
    im = Image.new('RGBA', (24, 24)); px = im.load()
    keep = C['s'], C['S']
    C['s'], C['S'] = (110, 70, 42), (146, 98, 60)
    _soil_back(px, (1, 17, 22, 24))
    C['s'], C['S'] = keep
    stamp(px, 8, 6, ['.kk.kk.', 'kllkglk', '.kgGgk.', '...G...', '...G...'])
    stamp(px, 1, 11, POT_SMALL)
    stamp(px, 15, 10, [r[::-1] for r in POT_SMALL])
    stamp(px, 6, 12, POT_BIG)
    return im


# ================= 재료 아이콘 16 (밭 그림과 같은 모양) =================
def _outline16(im, col=(70, 44, 28)):
    src = im.copy().load(); px = im.load()
    for y in range(16):
        for x in range(16):
            if src[x, y][3]: continue
            if any(0 <= x + dx < 16 and 0 <= y + dy < 16 and src[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = col + (255,)
    return im


def onion_icon():
    im = Image.new('RGBA', (16, 16)); px = im.load()
    for pts in (((7, 3), (6, 2), (5, 1)), ((8, 3), (8, 2), (8, 0)), ((9, 3), (10, 2), (11, 1))):
        for i, (x, y) in enumerate(pts): put(px, x, y, 'l' if i == 2 else 'g')
    stamp(px, 1, 4, ONION_BULB)
    for y in range(7, 13): put(px, 5 if y < 10 else 6, y, 'N')
    for y in range(6, 14): put(px, 10, y, 'M')
    put(px, 4, 7, 'w')
    return im                         # 알 테두리는 지도에 이미 있음, 싹만 바깥 테두리 없음 (작아서 그대로)


def potato_icon():
    C.update({'p': (236, 194, 116), 'P': (196, 140, 74), 'a': (252, 230, 176)})
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.ellipse((1, 3, 14, 13), fill=C['p'] + (255,), outline=C['o'] + (255,))
    d.chord((1, 3, 14, 13), 350, 140, fill=C['P'] + (255,)); d.ellipse((1, 3, 14, 13), outline=C['o'] + (255,))
    d.chord((2, 3, 13, 12), 350, 140, fill=C['p'] + (255,))
    d.point([(4, 5), (5, 5), (4, 6)], fill=C['a'] + (255,))
    for x, y in ((7, 7), (10, 6), (5, 10), (10, 10)): d.point((x, y), fill=(150, 98, 50, 255))
    return im


def wheat_icon():
    im = Image.new('RGBA', (16, 16)); px = im.load()
    EAR = ['.Y.', 'YuY', 'uUu', 'YuY', 'uUu', 'YuY', '.U.']
    for x, top in ((2, 2), (6, 0), (10, 2)):
        for y in range(top + 7, 15): put(px, x + 1, y, 'b')
        stamp(px, x, top, EAR)
    for x in range(3, 13): put(px, x, 11, 'v' if False else 'b')
    for x in range(4, 12): px[x, 11] = (220, 70, 60, 255)                                  # 빨간 끈
    px[7, 12] = (220, 70, 60, 255); px[8, 12] = (220, 70, 60, 255)
    return _outline16(im)
