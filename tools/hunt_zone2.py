"""사냥터 구역 배경 v2: 하늘·먼 풍경·땅 질감·소품을 층으로 쌓은 도트."""
import random
from PIL import Image, ImageDraw
INK = (52, 34, 30)


def sh(c, f): return tuple(max(0, min(255, int(v * f))) for v in c)


def sky(d, w, h0, top, bot, bands=4):
    for i in range(bands):
        t = i / (bands - 1)
        c = tuple(int(top[k] * (1 - t) + bot[k] * t) for k in range(3))
        d.rectangle((0, i * h0 // bands, w, (i + 1) * h0 // bands), fill=c)


def cloud(d, x, y, s=1.0):
    for dx, dy, r in ((0, 0, 7), (9, -4, 8), (19, 0, 7), (9, 3, 7)):
        r *= s; d.ellipse((x + dx * s - r, y + dy * s - r * .6, x + dx * s + r, y + dy * s + r * .6), fill=(255, 255, 255))
    d.line((x - 6 * s, y + 4 * s, x + 25 * s, y + 4 * s), fill=(220, 236, 250))


def tree(d, x, y, s=1.0, c=(84, 160, 74)):
    d.rectangle((x - 2 * s, y, x + 2 * s, y + 12 * s), fill=(120, 80, 48), outline=INK)
    for bx, by, r in ((0, -4, 10), (-7, 2, 8), (7, 2, 8)):
        r *= s; d.ellipse((x + bx * s - r, y + by * s - r, x + bx * s + r, y + by * s + r), fill=c, outline=INK)
    for bx, by in ((-4, -8), (3, -6), (-8, 0)):
        d.ellipse((x + bx * s, y + by * s, x + bx * s + 5 * s, y + by * s + 3 * s), fill=sh(c, 1.3))


def grass_tex(d, w, y0, h, base, rnd):
    d.rectangle((0, y0, w, h), fill=base)
    for _ in range(int(w * (h - y0) / 40)):
        x = rnd.randrange(w); y = rnd.randrange(y0 + 2, h)
        d.line((x, y, x, y - 2), fill=sh(base, .82)); d.point((x + 1, y - 1), fill=sh(base, 1.15))


def flowers(d, w, y0, h, rnd, n=10, cols=((255, 255, 255), (255, 214, 90), (255, 160, 190))):
    for _ in range(n):
        x = rnd.randrange(4, w - 4); y = rnd.randrange(y0 + 4, h - 4); c = rnd.choice(cols)
        d.point([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], fill=c); d.point((x, y), fill=(250, 200, 60))


def fence(d, x0, y0, x1, c=(236, 200, 140)):
    for y in (y0 + 4, y0 + 10):
        d.rectangle((x0, y, x1, y + 2), fill=c, outline=INK); d.line((x0, y + 1, x1, y + 1), fill=sh(c, 1.08))
    for x in range(x0 + 2, x1, 16):
        d.rectangle((x, y0, x + 4, y0 + 17), fill=c, outline=INK)
        d.line((x + 1, y0 + 1, x + 1, y0 + 16), fill=(255, 236, 200)); d.line((x + 3, y0 + 2, x + 3, y0 + 16), fill=sh(c, .8))
        d.polygon([(x, y0), (x + 2, y0 - 2), (x + 4, y0)], fill=c, outline=INK)


def planks(d, box, c, vertical=False, step=5):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=c, outline=INK)
    if vertical:
        for x in range(x0 + step, x1, step): d.line((x, y0 + 1, x, y1 - 1), fill=sh(c, .82))
    else:
        for y in range(y0 + step, y1, step): d.line((x0 + 1, y, x1 - 1, y), fill=sh(c, .82))
    d.line((x0 + 1, y0 + 1, x1 - 1, y0 + 1), fill=sh(c, 1.12))


def zone(key, w, h):
    rnd = random.Random(key)
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    gy = 44                                                     # 지평선
    if key == 'rabbit_hill':
        sky(d, w, h, (30, 26, 70), (96, 80, 160), 6)
        for _ in range(26):
            x, y = rnd.randrange(w), rnd.randrange(h // 2)
            d.point((x, y), fill=rnd.choice([(255, 250, 220), (200, 210, 255), (255, 255, 255)]))
        for x, y in ((24, 16), (120, 10), (170, 36)):          # 큰 별
            d.point([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], fill=(255, 240, 170)); d.point((x, y), fill=(255, 255, 255))
        mx = w - 50                                            # 달 + 무리
        for r, a in ((34, (120, 100, 180)), (28, (150, 130, 200))): d.ellipse((mx - r, 30 - r, mx + r, 30 + r), fill=a)
        d.ellipse((mx - 22, 8, mx + 22, 52), fill=(255, 248, 210), outline=(230, 210, 150))
        for cx, cy, r in ((-8, 22, 4), (6, 34, 3), (8, 18, 2), (-4, 40, 2)): d.ellipse((mx + cx - r, cy - r, mx + cx + r, cy + r), fill=(240, 228, 176))
        d.ellipse((-60, 64, w * .75, h + 70), fill=(86, 110, 170)); d.ellipse((w * .25, 74, w + 70, h + 80), fill=(70, 94, 156))   # 언덕 2겹
        d.ellipse((-20, 84, w * .7, h + 90), fill=(104, 132, 190))
        for _ in range(40):
            x = rnd.randrange(w); y = rnd.randrange(90, h)
            d.point((x, y), fill=(130, 156, 210))
        for x, y in ((60, 106), (96, 124), (128, 112), (70, 130)):   # 빛나는 꽃
            d.ellipse((x - 3, y - 2, x + 3, y + 2), fill=(255, 236, 140)); d.point((x, y), fill=(255, 255, 255))
            d.line((x, y + 2, x, y + 5), fill=(90, 140, 120))
        # 떡 찧는 절구 + 공이
        bx, by = 22, 92
        d.polygon([(bx, by), (bx + 22, by), (bx + 18, by + 16), (bx + 4, by + 16)], fill=(176, 120, 72), outline=INK)
        d.line((bx + 2, by + 2, bx + 20, by + 2), fill=(214, 160, 104)); d.ellipse((bx + 4, by - 3, bx + 18, by + 3), fill=(255, 255, 250), outline=INK)
        d.line((bx + 16, by - 18, bx + 10, by - 2), fill=(196, 140, 84), width=3); d.line((bx + 14, by - 20, bx + 20, by - 16), fill=(196, 140, 84), width=4)
        return im
    if key == 'chicken_coop':
        sky(d, w, gy, (150, 214, 248), (206, 238, 252))
        cloud(d, 120, 14, .8); cloud(d, 170, 26, .6)
        d.ellipse((-30, 30, 120, 64), fill=(140, 200, 120)); d.ellipse((90, 34, w + 40, 66), fill=(126, 190, 110))
        tree(d, 182, 30, .8)
        grass_tex(d, w, gy, h, (150, 206, 104), rnd)
        d.polygon([(70, h), (96, gy + 10), (110, gy + 10), (120, h)], fill=(214, 186, 132))     # 흙길
        # 닭장: 받침 + 나무판 벽 + 빨간 지붕 + 창 + 문 + 경사로
        d.rectangle((10, 74, 70, 80), fill=(150, 104, 64), outline=INK)
        for x in (14, 62): d.rectangle((x, 80, x + 4, 92), fill=(130, 88, 54), outline=INK)
        planks(d, (12, 38, 68, 74), (240, 214, 162), vertical=True, step=6)
        d.polygon([(6, 40), (40, 16), (74, 40)], fill=(206, 72, 62), outline=INK)
        for i in range(4): d.line((12 + i * 7, 38 - i * 5, 68 - i * 7, 38 - i * 5), fill=(168, 52, 48))
        d.line((40, 16, 40, 17), fill=(240, 120, 100))
        d.rectangle((20, 46, 32, 56), fill=(140, 200, 240), outline=INK); d.line((26, 46, 26, 56), fill=INK); d.line((20, 51, 32, 51), fill=INK)
        d.rectangle((44, 54, 58, 74), fill=(110, 70, 44), outline=INK); d.ellipse((50, 48, 54, 52), fill=(255, 220, 120), outline=INK)
        d.polygon([(58, 74), (84, 94), (90, 92), (64, 72)], fill=(206, 166, 110), outline=INK)
        for i in range(3): d.line((64 + i * 7, 78 + i * 5, 68 + i * 7, 76 + i * 5), fill=(150, 110, 70))
        for _ in range(9):                                      # 모이
            x = rnd.randrange(96, w - 80); y = rnd.randrange(80, max(81, h - 30))
            d.point([(x, y), (x + 1, y)], fill=(250, 214, 100))
        d.ellipse((140, 52, 164, 61), fill=(236, 220, 160), outline=INK)                        # 짚 둥지 + 알
        d.ellipse((148, 51, 156, 57), fill=(255, 250, 236), outline=INK)
        flowers(d, w - 70, gy + 6, h - 20, rnd, 8)
        fence(d, 0, h - 20, w)
    elif key == 'pig_pen':
        sky(d, w, gy, (160, 214, 246), (210, 238, 250))
        cloud(d, 30, 16, .7)
        d.ellipse((-20, 32, 90, 62), fill=(132, 192, 112)); d.ellipse((60, 30, w + 30, 64), fill=(120, 184, 104))
        tree(d, w - 24, 26, .7, (72, 150, 70))
        grass_tex(d, w, gy, h, (146, 196, 100), rnd)
        # 진흙탕 (층 + 물웅덩이 반사 + 진흙 튐)
        d.ellipse((10, 60, w - 70, h - 18), fill=(120, 84, 54), outline=INK)
        d.ellipse((16, 62, w - 76, h - 22), fill=(148, 104, 68))
        d.ellipse((34, 72, w - 110, h - 36), fill=(132, 92, 58))
        d.ellipse((92, 82, 128, 94), fill=(170, 190, 200)); d.line((98, 86, 116, 86), fill=(230, 240, 246)); d.line((102, 90, 122, 90), fill=(200, 216, 226))
        for _ in range(14):
            x = rnd.randrange(24, w - 90); y = rnd.randrange(70, h - 26); d.point((x, y), fill=(98, 66, 42))
        # 여물통 + 사과 / 볏짚 지붕 쉼터
        planks(d, (8, 38, 58, 54), (196, 150, 96))
        d.rectangle((10, 36, 56, 40), fill=(120, 170, 90), outline=INK)
        for x in (16, 28, 42): d.ellipse((x, 32, x + 6, 38), fill=(232, 70, 60), outline=INK)
        d.polygon([(74, 22), (124, 22), (132, 36), (66, 36)], fill=(232, 196, 110), outline=INK)
        for x in range(70, 130, 5): d.line((x, 24, x - 2, 35), fill=(204, 160, 70))
        for x in (72, 124): d.rectangle((x, 36, x + 3, 58), fill=(140, 96, 60), outline=INK)
        fence(d, 0, h - 20, w)
    else:  # ranch
        sky(d, w, gy + 6, (140, 206, 250), (204, 236, 252))
        cloud(d, 24, 14, .9); cloud(d, 150, 20, .7)
        for i, (x0, c) in enumerate(((-40, (156, 214, 124)), (80, (140, 204, 112)), (140, (128, 196, 104)))):
            d.ellipse((x0, 30 + i * 2, x0 + 160, 74 + i * 2), fill=c)
        # 풍차
        mx, my = 168, 26
        d.polygon([(mx - 7, my + 30), (mx + 7, my + 30), (mx + 4, my), (mx - 4, my)], fill=(236, 230, 214), outline=INK)
        d.rectangle((mx - 2, my + 22, mx + 2, my + 30), fill=(140, 96, 60))
        for dx, dy in ((-14, -10), (14, 10), (-10, 14), (10, -14)):
            d.polygon([(mx, my), (mx + dx, my + dy), (mx + dx * .7 + dy * .25, my + dy * .7 - dx * .25)], fill=(250, 246, 236), outline=INK)
        d.ellipse((mx - 2, my - 2, mx + 2, my + 2), fill=(200, 70, 60), outline=INK)
        grass_tex(d, w, gy + 10, h, (132, 200, 100), rnd)
        # 건초 더미 (둥근 단면) + 물통
        for x, y in ((14, 58), (36, 62)):
            d.ellipse((x, y, x + 20, y + 18), fill=(240, 204, 100), outline=INK)
            d.ellipse((x + 5, y + 4, x + 15, y + 14), outline=(206, 160, 64)); d.point((x + 10, y + 9), fill=(206, 160, 64))
        flowers(d, w - 70, gy + 14, h - 20, rnd, 12, ((255, 255, 255), (255, 230, 120)))
        fence(d, 0, h - 20, w, (250, 250, 250))
    return im


if __name__ == '__main__':
    o = Image.new('RGBA', (2 * 216 + 8, 2 * 148 + 8), (60, 40, 30, 255))
    for i, k in enumerate(('chicken_coop', 'pig_pen', 'ranch', 'rabbit_hill')):
        o.alpha_composite(zone(k, 208, 140), (8 + (i % 2) * 216, 8 + (i // 2) * 148))
    o.resize((o.width * 2, o.height * 2), Image.NEAREST).save('../zones2.png')


# 칸 안 자리 (구역 그림 기준, 208x140): 사냥감 2마리 / 보낸 동물(오른쪽 아래, 소품 없음) / 남은 시간 칩
SPOTS = {'critters': {'chicken_coop': [[74, 76], [120, 84]], 'pig_pen': [[40, 74], [86, 84]],
                      'ranch': [[80, 84], [122, 90]], 'rabbit_hill': [[84, 76], [124, 86]]},
         'animal': [146, 76], 'chip': [6, 98], 'gauge': [6, 120]}
