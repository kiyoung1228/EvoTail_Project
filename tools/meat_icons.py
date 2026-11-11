"""고기 재료 아이콘 16x16 v2 (소고기 스테이크, 닭다리, 삼겹살, 행운의 토끼고기)."""
from PIL import Image, ImageDraw
O = (84, 36, 40)


def _o(im, col=O):
    src = im.copy().load(); px = im.load()
    for y in range(16):
        for x in range(16):
            if src[x, y][3]: continue
            if any(0 <= x + a < 16 and 0 <= y + b < 16 and src[x + a, y + b][3] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = col + (255,)
    return im


def beef():               # 마블링 스테이크: 지방 테두리 + 진홍 살 + 흰 마블
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.polygon([(2, 6), (5, 2), (11, 2), (14, 5), (14, 10), (11, 14), (5, 14), (1, 11)], fill=(250, 236, 220))   # 지방
    d.polygon([(3, 6), (6, 3), (11, 3), (13, 6), (13, 10), (10, 13), (5, 13), (2, 10)], fill=(206, 52, 64))      # 살
    d.polygon([(8, 13), (10, 13), (13, 10), (13, 7)], fill=(160, 32, 48))                                          # 그림자
    d.line((5, 4, 9, 4), fill=(236, 96, 104)); d.point((4, 5), fill=(236, 96, 104))                                 # 하이라이트
    for pts in (((4, 8), (6, 7), (8, 8)), ((9, 5), (11, 6)), ((6, 11), (8, 10), (10, 11)), ((10, 8), (12, 9))):
        d.line(pts, fill=(255, 220, 220))                                                                          # 마블
    return _o(im)


def chicken():            # 생 닭다리: 살구빛 살 + 흰 뼈 끝
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.ellipse((1, 2, 11, 12), fill=(250, 200, 170))
    d.chord((1, 2, 11, 12), 330, 150, fill=(226, 160, 132)); d.ellipse((2, 3, 6, 6), fill=(255, 226, 206))
    d.point([(4, 8), (7, 6), (6, 9)], fill=(236, 176, 150))
    d.line((9, 10, 12, 13), fill=(250, 246, 236), width=2)                                                         # 뼈
    for x, y in ((12, 13), (14, 12), (13, 15)): d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(255, 252, 244))
    return _o(im)


def pork():               # 삼겹살: 껍질·지방·살 겹
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.polygon([(1, 6), (13, 3), (15, 11), (3, 14)], fill=(232, 112, 122))
    bands = [((1, 6), (13, 3), (226, 170, 132)), ((1, 7), (13, 4), (255, 240, 232)), ((2, 9), (14, 6), (255, 236, 226)),
             ((2, 10), (14, 7), (214, 92, 104)), ((2, 12), (15, 9), (255, 238, 230))]
    for a, b, c in bands: d.line((a, b), fill=c)
    d.line((3, 13, 15, 10), fill=(186, 72, 88))
    return _o(im)


def lucky_rabbit():       # 행운의 토끼고기: 연보라빛 다리살 + 금 리본 + 반짝이
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.ellipse((1, 3, 11, 13), fill=(240, 186, 210))
    d.chord((1, 3, 11, 13), 330, 150, fill=(206, 140, 178)); d.ellipse((2, 4, 6, 7), fill=(255, 220, 236))
    d.line((9, 11, 12, 14), fill=(250, 246, 236), width=2)
    for x, y in ((12, 14), (14, 13)): d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(255, 252, 244))
    d.point([(9, 10), (10, 11), (8, 11), (10, 9)], fill=(250, 204, 70))                                            # 금 리본
    im = _o(im)
    px = im.load()
    for x, y in ((13, 2), (2, 1)):
        for a, b in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + a < 16 and 0 <= y + b < 16 and not px[x + a, y + b][3]:
                px[x + a, y + b] = ((255, 255, 255, 255) if (a, b) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS = {'beef': beef, 'chicken': chicken, 'pork': pork, 'lucky_rabbit': lucky_rabbit}

def beef():               # v2: 티본 스테이크 (콩팥 모양 + 오른쪽 지방 + 흰 T자 뼈 + 마블)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    shape = [(1, 6), (4, 2), (10, 1), (14, 4), (15, 9), (12, 13), (7, 14), (3, 13), (1, 10)]
    d.polygon(shape, fill=(250, 236, 220))                                                       # 지방 테두리
    d.polygon([(2, 6), (5, 3), (10, 2), (13, 5), (13, 9), (11, 12), (7, 13), (3, 12), (2, 10)], fill=(200, 46, 60))
    d.polygon([(7, 13), (11, 12), (13, 9), (13, 7), (10, 11)], fill=(156, 30, 46))
    d.line((5, 4, 8, 3), fill=(236, 92, 100)); d.point((4, 5), fill=(236, 92, 100))
    d.line((7, 4, 7, 11), fill=(255, 250, 240)); d.line((8, 4, 8, 11), fill=(232, 222, 206))      # T자 뼈
    d.line((5, 5, 10, 5), fill=(255, 250, 240))
    for pts in (((3, 8), (5, 9)), ((10, 7), (12, 8)), ((4, 11), (6, 10)), ((10, 10), (11, 11))):
        d.line(pts, fill=(255, 210, 214))
    return _o(im)


MEATS['beef'] = beef


def beef():               # v3: 가로로 긴 꽃등심 스테이크 (위쪽 지방 띠 + 진홍 살 + 마블)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    d.polygon([(0, 8), (2, 5), (6, 3), (11, 3), (15, 5), (15, 9), (12, 12), (7, 13), (2, 12)], fill=(250, 236, 222))
    d.polygon([(1, 8), (3, 6), (6, 5), (11, 5), (14, 7), (14, 9), (12, 11), (7, 12), (3, 11)], fill=(204, 48, 62))
    d.polygon([(7, 12), (12, 11), (14, 9), (14, 8), (9, 11)], fill=(158, 30, 46))
    d.line((4, 6, 8, 6), fill=(238, 98, 106))
    d.ellipse((8, 7, 11, 9), fill=(250, 214, 214))                                                 # 꽃등심 지방 눈
    for pts in (((3, 9), (5, 8), (6, 9)), ((11, 6), (13, 7)), ((5, 11), (7, 10)), ((11, 10), (12, 9))):
        d.line(pts, fill=(255, 206, 210))
    return _o(im)


MEATS['beef'] = beef


def lucky_rabbit():       # v2: 행운의 토끼발 (복슬한 발 + 분홍 발바닥 3개 + 금 고리 + 반짝이)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    F0, F1, F2 = (255, 255, 255), (238, 232, 252), (196, 184, 236)
    d.ellipse((3, 5, 12, 15), fill=F1)                                                             # 발
    d.polygon([(4, 7), (5, 3), (10, 3), (11, 7)], fill=F1)
    d.chord((3, 5, 12, 15), 330, 150, fill=F2)
    for x, y in ((5, 6), (6, 9), (4, 10)): d.point((x, y), fill=F0)                                # 털 결
    for bx in ((4, 12, 6, 14), (7, 13, 9, 15), (10, 12, 12, 14)): d.ellipse(bx, fill=(255, 160, 186))   # 발가락 콩
    d.ellipse((6, 9, 10, 12), fill=(255, 176, 198))                                                 # 발바닥
    d.rectangle((4, 2, 11, 3), fill=(250, 204, 70)); d.line((4, 2, 11, 2), fill=(255, 236, 150))   # 금 고리
    d.ellipse((6, 0, 9, 2), outline=(230, 170, 40))
    im = _o(im, (92, 64, 120)); px = im.load()
    for x, y in ((14, 4), (1, 9)):
        for a_, b_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + a_ < 16 and 0 <= y + b_ < 16 and not px[x + a_, y + b_][3]:
                px[x + a_, y + b_] = ((255, 255, 255, 255) if (a_, b_) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS['lucky_rabbit'] = lucky_rabbit


def lucky_rabbit():       # v3: 비스듬한 토끼발 (복슬한 털 + 끝에 분홍 발가락 콩 + 금 마개·고리)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    F0, F1, F2 = (255, 255, 255), (240, 234, 252), (200, 188, 236)
    body = [(4, 3), (7, 2), (11, 6), (14, 10), (14, 13), (12, 15), (9, 14), (5, 9), (3, 6)]
    d.polygon(body, fill=F1)
    d.polygon([(14, 10), (14, 13), (12, 15), (9, 14), (11, 12)], fill=F2)                         # 아래 그림자
    for x, y in ((5, 5), (7, 4), (6, 7), (8, 6), (9, 9)): d.point((x, y), fill=F0)                # 털
    for x, y in ((3, 7), (6, 10), (8, 12)): d.point((x, y), fill=F2)                              # 털 끝 삐침
    for bx in ((12, 9, 13, 10), (13, 11, 14, 12), (10, 13, 11, 14)): d.rectangle(bx, fill=(255, 150, 180))   # 발가락 콩
    d.point((11, 11), fill=(255, 176, 198))
    d.polygon([(3, 4), (6, 1), (8, 3), (5, 6)], fill=(250, 204, 70)); d.line((4, 3, 6, 1), fill=(255, 236, 150))   # 금 마개
    d.ellipse((1, 0, 4, 3), outline=(230, 170, 40))                                                # 고리
    im = _o(im, (92, 64, 120)); px = im.load()
    for x, y in ((14, 3), (2, 13)):
        for a_, b_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + a_ < 16 and 0 <= y + b_ < 16 and not px[x + a_, y + b_][3]:
                px[x + a_, y + b_] = ((255, 255, 255, 255) if (a_, b_) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS['lucky_rabbit'] = lucky_rabbit


RABBIT_FOOT = [               # 행운의 토끼발 v4: 금 고리·마개 + 복슬한 다리 + 발바닥(분홍 콩 4개 + 큰 패드)
    '......oooo......',
    '.....oyYYyo.....',
    '....oyYYYYyo....',
    '....oGGGGGGo....',
    '...o.wfffffo....',
    '....owfffffwo...',
    '...owffffffo....',
    '....offffffwo...',
    '..oowfffffffoo..',
    '.owfppfppfppffo.',
    '.ofpPPpPPpPPfwo.',
    'owffppfppfppfffo',
    'offffppppppffffo',
    'offffpPPPPpffffo',
    '.offffppppffffo.',
    '..oooooooooooo..']
RF = {'o': (92, 64, 120), 'w': (255, 255, 255), 'f': (238, 232, 252), 'p': (255, 168, 192), 'P': (236, 120, 156),
      'y': (255, 230, 130), 'Y': (250, 200, 60), 'G': (214, 150, 40)}


def lucky_rabbit():
    im = Image.new('RGBA', (16, 16)); px = im.load()
    for y, r in enumerate(RABBIT_FOOT):
        for x, ch in enumerate(r):
            if ch in RF: px[x, y] = RF[ch] + (255,)
    for x, y in ((14, 2), (1, 4)):                                                               # 반짝이
        for a_, b_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + a_ < 16 and 0 <= y + b_ < 16 and not px[x + a_, y + b_][3]:
                px[x + a_, y + b_] = ((255, 255, 255, 255) if (a_, b_) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS['lucky_rabbit'] = lucky_rabbit


def lucky_rabbit():       # v5: 발바닥이 보이는 토끼발 열쇠고리 (발자국 무늬 = 콩 4개 + 큰 패드)
    im = Image.new('RGBA', (16, 16)); d = ImageDraw.Draw(im)
    F, FS, W_ = (240, 234, 252), (206, 194, 238), (255, 255, 255)
    d.polygon([(8, 9), (12, 9), (14, 4), (11, 3)], fill=F)                                     # 다리 (오른쪽 위로)
    d.line((12, 9, 14, 4), fill=FS)
    d.ellipse((0, 6, 12, 15), fill=F)                                                          # 발
    d.chord((0, 6, 12, 15), 20, 120, fill=FS)
    d.point([(2, 8), (3, 7)], fill=W_)
    for x, y in ((2, 9), (4, 7), (7, 7), (9, 9)): d.rectangle((x, y, x + 1, y + 1), fill=(255, 150, 182))   # 발가락 콩
    d.polygon([(4, 11), (8, 11), (9, 13), (6, 14), (3, 13)], fill=(255, 150, 182))             # 큰 패드
    d.point((5, 12), fill=(255, 200, 216))
    d.polygon([(11, 3), (14, 4), (15, 2), (12, 1)], fill=(250, 200, 60))                       # 금 마개
    d.point((13, 2), fill=(255, 236, 150))
    im = _o(im, (92, 64, 120)); px = im.load()
    for x, y in ((14, 0), (15, 0)): px[x, y] = (214, 150, 40, 255)                             # 고리
    for x, y in ((1, 2),):
        for a_, b_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if not px[x + a_, y + b_][3]:
                px[x + a_, y + b_] = ((255, 255, 255, 255) if (a_, b_) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS['lucky_rabbit'] = lucky_rabbit


def lucky_rabbit():       # v6: 진짜 토끼발 부적 = 가늘고 긴 털 다리, 끝은 뾰족 + 작은 발톱, 금 마개 + 고리
    import math
    im = Image.new('RGBA', (32, 32)); d = ImageDraw.Draw(im)                                   # 2배로 그린 뒤 줄임(가장자리만 정리)
    x0, y0, x1, y1 = 23, 7, 5, 27                                                              # 마개 쪽 → 발끝
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L; nx, ny = -uy, ux
    prof = [(0, 4.2), (.25, 5.0), (.55, 5.0), (.8, 4.0), (.95, 2.4), (1, 1.0)]
    left = [(x0 + ux * L * t + nx * w, y0 + uy * L * t + ny * w) for t, w in prof]
    right = [(x0 + ux * L * t - nx * w, y0 + uy * L * t - ny * w) for t, w in prof]
    d.polygon(left + right[::-1], fill=(244, 238, 230))
    d.polygon([(x0 + ux * L * t - nx * w * .2, y0 + uy * L * t - ny * w * .2) for t, w in prof] + right[::-1], fill=(214, 200, 186))   # 그림자 쪽
    im = im.resize((16, 16), Image.NEAREST); d = ImageDraw.Draw(im)
    for a_, b_ in (((10, 7), (8, 9)), ((8, 10), (6, 12)), ((11, 9), (9, 11))): d.line((a_, b_), fill=(255, 255, 255))   # 털 결
    for x, y in ((7, 12), (10, 10)): d.point((x, y), fill=(196, 180, 164))
    d.point([(4, 12), (5, 13)], fill=(196, 180, 164)); d.point([(3, 11), (6, 14)], fill=(214, 200, 186))   # 발가락 사이 홈
    d.point([(2, 14), (3, 15), (1, 13)], fill=(120, 96, 90))                                    # 발톱
    d.polygon([(10, 3), (12, 2), (14, 5), (12, 6)], fill=(250, 200, 60)); d.line((11, 3, 12, 2), fill=(255, 236, 150))   # 금 마개
    d.line((12, 6, 14, 5), fill=(200, 140, 30))
    im = _o(im, (96, 72, 64)); px = im.load()
    for x, y in ((14, 1), (15, 2), (14, 3)): px[x, y] = (214, 150, 40, 255)                     # 고리
    px[15, 1] = (0, 0, 0, 0)
    for x, y in ((3, 3),):
        for a_, b_ in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if not px[x + a_, y + b_][3]:
                px[x + a_, y + b_] = ((255, 255, 255, 255) if (a_, b_) == (0, 0) else (255, 226, 110, 255))
    return im


MEATS['lucky_rabbit'] = lucky_rabbit


if __name__ == '__main__':
    old = []
    o = Image.new('RGBA', (4 * 112 + 8, 2 * 112 + 8), (250, 240, 214, 255))
    for i, k in enumerate(MEATS):
        try: old_im = Image.open(f'/home/claude/evotail_project/assets/food/{k}.png').convert('RGBA').resize((96, 96), Image.NEAREST); o.alpha_composite(old_im, (8 + i * 112, 8))
        except FileNotFoundError: pass
        o.alpha_composite(MEATS[k]().resize((96, 96), Image.NEAREST), (8 + i * 112, 120))
    o.save('../meats.png')


