"""병원 진료실 배경 (도트, 논리 640x360). 침대·환자·이불은 장면에서 겹쳐 그림."""
from PIL import Image, ImageDraw
import uikit as K
INK = K.INK; W, H = 640, 360
WD = K.WOOD


def box(d, b, fill, hi=None, lo=None, out=INK):
    x0, y0, x1, y1 = b
    d.rectangle(b, fill=fill, outline=out)
    if hi: d.line((x0 + 1, y0 + 1, x1 - 1, y0 + 1), fill=hi); d.line((x0 + 1, y0 + 1, x0 + 1, y1 - 1), fill=hi)
    if lo: d.line((x0 + 1, y1 - 1, x1 - 1, y1 - 1), fill=lo); d.line((x1 - 1, y0 + 1, x1 - 1, y1 - 1), fill=lo)


def bottle(d, x, y, c, tall=False):
    h = 16 if tall else 12
    c0 = tuple(min(255, v + 70) for v in c); c2 = tuple(int(v * .62) for v in c)
    d.rectangle((x + 3, y, x + 6, y + 3), fill=(176, 120, 72), outline=INK)            # 코르크
    d.rectangle((x, y + 3, x + 9, y + h), fill=c, outline=INK)
    d.line((x + 1, y + h - 1, x + 8, y + h - 1), fill=c2); d.line((x + 8, y + 4, x + 8, y + h - 1), fill=c2)
    d.line((x + 2, y + 5, x + 2, y + h - 3), fill=c0); d.point((x + 3, y + 5), fill=(255, 255, 255))
    d.rectangle((x + 2, y + h - 7, x + 7, y + h - 4), fill=(250, 246, 236))               # 라벨


def room(dim=False):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    # 벽: 연한 민트 + 작은 십자 무늬 벽지
    d.rectangle((0, 26, W, 198), fill=(228, 242, 232))
    for y in range(36, 196, 20):
        for x in range((y // 20 % 2) * 10, W, 20):
            d.line((x - 1, y, x + 1, y), fill=(210, 232, 216)); d.line((x, y - 1, x, y + 1), fill=(210, 232, 216))
    # 걸레받이 패널 + 몰딩
    d.rectangle((0, 198, W, 242), fill=(208, 228, 240))
    for x in range(4, W, 52):
        box(d, (x, 206, x + 46, 236), (214, 234, 246), (236, 246, 252), (180, 204, 222), out=(160, 184, 204))
    d.rectangle((0, 195, W, 201), fill=WD[3], outline=INK); d.line((0, 196, W, 196), fill=WD[4])
    d.rectangle((0, 242, W, 246), fill=WD[2], outline=INK)
    # 바닥 타일
    for y in range(247, H, 14):
        for x in range(-(y // 14 % 2) * 14, W, 28):
            d.rectangle((x, y, x + 27, y + 13), fill=(234, 222, 204) if (x // 28) % 2 else (222, 208, 188), outline=(196, 180, 158))
            d.line((x + 1, y + 1, x + 26, y + 1), fill=(244, 236, 222))
    # 창문 (커튼 포함)
    wx0, wy0, wx1, wy1 = 330, 62, 432, 128
    d.rectangle((wx0, wy0, wx1, wy1), fill=(150, 214, 248))
    d.rectangle((wx0, wy0 + 40, wx1, wy1), fill=(178, 226, 250))
    for cx, cy in ((352, 80), (400, 72)):                                                   # 구름
        d.ellipse((cx - 10, cy - 4, cx + 10, cy + 6), fill=(255, 255, 255)); d.ellipse((cx - 4, cy - 9, cx + 8, cy + 3), fill=(255, 255, 255))
    d.rectangle((wx0, wy0, wx1, wy1), outline=INK, width=1)
    for b in ((wx0 + 1, wy0 + 1, wx1 - 1, wy0 + 3), (wx0 + 1, wy0 + 1, wx0 + 3, wy1 - 1), (wx1 - 3, wy0 + 1, wx1 - 1, wy1 - 1),
              ((wx0 + wx1) // 2 - 1, wy0, (wx0 + wx1) // 2 + 1, wy1), (wx0, (wy0 + wy1) // 2 - 1, wx1, (wy0 + wy1) // 2 + 1)):
        d.rectangle(b, fill=(255, 255, 255))
    d.rectangle((wx0 - 4, wy1, wx1 + 4, wy1 + 4), fill=(250, 250, 252), outline=INK)       # 창틀
    d.rectangle((wx0 - 8, wy0 - 6, wx1 + 8, wy0 - 4), fill=WD[1], outline=INK)             # 커튼 봉
    for side, x in ((1, wx0 - 6), (-1, wx1 - 12)):
        for i in range(3):
            xx = x + i * 6
            d.rectangle((xx, wy0 - 4, xx + 6, wy1 + 14 - i * 3), fill=(250, 196, 210) if i % 2 == 0 else (236, 166, 186), outline=INK)
        d.rectangle((x, wy0 + 30, x + 18, wy0 + 33), fill=(230, 120, 140), outline=INK)    # 커튼 끈
    # 십자 간판
    box(d, (226, 64, 286, 108), (255, 255, 255), (255, 255, 255), (214, 222, 230))
    d.rectangle((250, 70, 262, 102), fill=(232, 72, 84)); d.rectangle((234, 80, 278, 92), fill=(232, 72, 84))
    d.line((251, 71, 251, 79), fill=(255, 140, 150)); d.line((235, 81, 249, 81), fill=(255, 140, 150))
    # 약장
    box(d, (18, 64, 138, 238), WD[2], WD[3], WD[1])
    box(d, (24, 70, 132, 176), (190, 222, 236), out=INK)
    cols = [(232, 96, 140), (246, 178, 50), (80, 160, 230), (100, 196, 110), (170, 120, 220)]
    for r, sy in enumerate((90, 124, 158)):
        d.rectangle((25, sy + 16, 131, sy + 18), fill=WD[3], outline=INK)
        for i in range(5):
            bottle(d, 30 + i * 20, sy - (4 if (i + r) % 2 else 0), cols[(i + r * 2) % 5], tall=(i + r) % 2 == 1)
    d.line((78, 70, 78, 176), fill=INK); d.line((26, 72, 34, 80), fill=(255, 255, 255)); d.line((82, 72, 90, 80), fill=(255, 255, 255))
    for x in (72, 84): d.rectangle((x, 120, x + 2, 128), fill=(250, 210, 90), outline=INK)
    for y in (182, 210):                                                                     # 서랍
        box(d, (26, y, 130, y + 22), WD[3], WD[4], WD[2])
        d.rectangle((72, y + 9, 84, y + 12), fill=(250, 210, 90), outline=INK)
    # 침대 옆 탁자 + 물컵 + 화분
    box(d, (148, 176, 184, 240), WD[3], WD[4], WD[2])
    box(d, (152, 190, 180, 208), WD[2], WD[3], WD[1]); d.rectangle((163, 197, 169, 200), fill=(250, 210, 90), outline=INK)
    d.rectangle((152, 164, 162, 176), fill=(214, 236, 250), outline=INK); d.rectangle((153, 169, 161, 175), fill=(150, 206, 244))
    d.rectangle((168, 166, 180, 176), fill=(214, 120, 80), outline=INK); d.line((169, 167, 179, 167), fill=(240, 160, 120))
    for a, b, c in (((174, 166), (170, 154), (110, 196, 110)), ((174, 166), (178, 152), (80, 170, 90)), ((174, 166), (182, 158), (110, 196, 110))):
        d.line((a, b), fill=c, width=2)
    d.ellipse((168, 150, 174, 156), fill=(255, 150, 180), outline=INK); d.point((171, 153), fill=(255, 240, 120))
    if dim:
        from PIL import ImageEnhance
        im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.55)).enhance(.7)
    return im


METAL = [(80, 90, 110), (150, 160, 180), (196, 204, 220), (236, 240, 248)]


def bed_back(base):
    """머리판·매트리스·베개 (환자보다 뒤)"""
    d = ImageDraw.Draw(base)
    ov = Image.new('RGBA', (W, H)); ImageDraw.Draw(ov).ellipse((196, 232, 450, 248), fill=(60, 50, 60, 70)); base.alpha_composite(ov)
    # 머리판
    for x in (194, 214):
        d.rectangle((x, 112, x + 5, 238), fill=METAL[2], outline=INK); d.line((x + 1, 113, x + 1, 237), fill=METAL[3])
        d.rectangle((x - 1, 108, x + 6, 113), fill=METAL[1], outline=INK)
    box(d, (198, 122, 216, 166), (200, 228, 244), (236, 248, 255), (160, 196, 220))
    for y in (130, 140, 150): d.line((200, y, 214, y), fill=(170, 206, 228))
    # 매트리스 옆면 + 프레임 + 다리
    box(d, (218, 170, 436, 198), (250, 250, 254), (255, 255, 255), (214, 220, 234))
    d.rectangle((216, 198, 440, 205), fill=METAL[2], outline=INK); d.line((217, 199, 439, 199), fill=METAL[3])
    for x in (226, 424):
        d.rectangle((x, 205, x + 4, 228), fill=METAL[1], outline=INK)
        d.ellipse((x - 3, 226, x + 7, 236), fill=(70, 70, 84), outline=INK); d.point((x + 2, 231), fill=(170, 170, 190))
    # 발판
    d.rectangle((432, 146, 438, 238), fill=METAL[2], outline=INK); d.line((433, 147, 433, 237), fill=METAL[3])
    d.rectangle((431, 142, 439, 147), fill=METAL[1], outline=INK)
    box(d, (424, 154, 432, 190), (200, 228, 244), (236, 248, 255), (160, 196, 220))
    # 베개
    d.rounded_rectangle((222, 146, 270, 174), 6, fill=(250, 250, 255), outline=INK)
    d.line((226, 150, 262, 150), fill=(255, 255, 255)); d.line((226, 170, 266, 170), fill=(214, 220, 236))
    d.line((262, 152, 266, 166), fill=(214, 220, 236)); d.line((244, 160, 250, 164), fill=(224, 228, 240))


def blanket(base):
    """이불 (환자 위에 덮음)"""
    d = ImageDraw.Draw(base)
    B0, B1, B2, B3 = (128, 176, 222), (160, 204, 238), (190, 224, 248), (226, 242, 255)
    d.polygon([(250, 168), (430, 164), (434, 206), (248, 210)], fill=B1, outline=INK)
    d.rectangle((250, 164, 432, 172), fill=(255, 255, 255), outline=INK)                     # 접힌 흰 시트
    d.line((251, 165, 431, 165), fill=(255, 255, 255)); d.line((251, 171, 431, 171), fill=(220, 228, 240))
    for y in (182, 186, 196, 200): d.line((251, y, 433, y), fill=B2 if y in (182, 196) else B3)
    for x0 in (318, 384):                                                                    # 부드러운 주름
        d.line((x0, 174, x0 + 4, 180), fill=B0); d.line((x0 + 1, 188, x0 + 5, 194), fill=B0)
    d.line((252, 174, 252, 208), fill=B3)
    d.line((250, 208, 432, 205), fill=B0)


if __name__ == '__main__':
    pass
