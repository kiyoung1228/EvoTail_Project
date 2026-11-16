"""표지 v4: 매화·향나무 정원 + 돌담·한옥 지붕 + 떠 있는 섬 + 정중앙 큰 로고 + 동물 행렬 + 안내원 테크모.
출력: 정지 화면 png, 가만히 있을 때 gif, '새 게임' 눌렀을 때 gif."""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
from ui_mock import text_mid
import techmo

W, H = 640, 360
INK = K.INK
GAME = Path(__file__).resolve().parent.parent      # 저장소 루트 (tools/ 위)


def tl(t, f): return f.getlength(t)


def spr(key, n=2, stage=1):
    im = Image.open(GAME / 'assets' / 'sprites' / f'{key}_s{stage}.png').convert('RGBA').resize((28, 28), Image.NEAREST)
    return im.resize((28 * n, 28 * n), Image.NEAREST)


def mix(a, b, t): return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


# ================= 하늘·구름·먼 산 =================
def sky(base):
    d = ImageDraw.Draw(base)
    stops = [(0, (112, 178, 236)), (110, (156, 206, 244)), (170, (206, 230, 248)), (205, (250, 232, 226))]
    for y in range(H):
        for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
            if y0 <= y <= y1:
                k = int((y - y0) / (y1 - y0) * 6) / 6           # 띠 모양 (도트 느낌)
                d.line((0, y, W, y), fill=mix(c0, c1, k)); break
        else:
            d.line((0, y, W, y), fill=stops[-1][1])


def puff_cloud(base, x, y, w, t=0.0):
    """세 겹 구름: 그림자 · 몸 · 하이라이트, 아래는 평평"""
    d = ImageDraw.Draw(base); h = w // 3
    rnd = random.Random(int(x * 7 + y))
    lumps = [(x + w * f, y + h * .1 - h * (.5 + .5 * math.sin(f * math.pi)) * .9, h * (.45 + .35 * math.sin(f * math.pi)))
             for f in [i / 6 for i in range(7)]]
    for cx, cy, r in lumps: d.ellipse((cx - r, cy - r + 3, cx + r, cy + r + 3), fill=(206, 222, 240))
    for cx, cy, r in lumps: d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 252, 255))
    for cx, cy, r in lumps[1:-1]: d.arc((cx - r + 2, cy - r + 1, cx + r - 2, cy + r - 2), 200, 290, fill=(255, 255, 255), width=2)
    d.rectangle((x - 2, y + 2, x + w + 2, y + h // 2), fill=(250, 252, 255))
    d.line((x + 2, y + h // 2 + 1, x + w - 2, y + h // 2 + 1), fill=(206, 222, 240))


def mountains(base):
    d = ImageDraw.Draw(base)
    layers = [(178, [(28, .011, .3), (12, .03, 1.7)], (176, 204, 218), (196, 220, 230)),
              (196, [(18, .016, 2.1), (8, .05, .4)], (150, 190, 186), (172, 206, 196))]
    for by, waves, col, top in layers:
        pts = [(x, by - sum(a * math.sin(x * f + p) for a, f, p in waves) - 6) for x in range(0, W + 4, 2)]
        d.polygon(pts + [(W, H), (0, H)], fill=col)
        d.line(pts, fill=top)
        for i in range(0, len(pts) - 6, 23):                       # 산 주름
            x, y = pts[i]; d.line((x, y + 3, x + 5, y + 12), fill=mix(col, (120, 150, 150), .25))
    # 산 아래 옅은 안개 띠
    fog = Image.new('RGBA', (W, H)); fd = ImageDraw.Draw(fog)
    for i in range(4): fd.rectangle((0, 196 + i * 4, W, 200 + i * 4), fill=(255, 250, 246, 70 - i * 15))
    base.alpha_composite(fog)


# ================= 떠 있는 섬 =================
def float_island(base, cx, cy, t, s=1.0, flip=False):
    lay = Image.new('RGBA', base.size)
    _float_island(lay, cx, cy, t, s, flip)
    a = lay.getchannel('A')
    haze = Image.new('RGBA', base.size, (196, 224, 246, 255))
    lay = Image.blend(lay, haze, .32); lay.putalpha(a)                   # 먼 거리 = 하늘색 안개
    base.alpha_composite(lay)
    bob = round(2 * math.sin(t * math.pi * 2 + cx))
    for dx, w in ((-int(54 * s), int(40 * s)), (-int(20 * s), int(56 * s)), (int(22 * s), int(36 * s))):   # 아래 구름 받침
        puff_cloud(base, cx + dx, cy + int(30 * s) + bob, w)


def _float_island(base, cx, cy, t, s=1.0, flip=False):
    d = ImageDraw.Draw(base)
    cy += round(2 * math.sin(t * math.pi * 2 + cx))
    w = int(84 * s); h = int(16 * s)
    rock = [(150, 112, 88), (124, 90, 72), (100, 72, 60), (82, 58, 50)]
    pts = [(cx - w // 2, cy), (cx + w // 2, cy), (cx + w // 4, cy + 20 * s), (cx + 6 * s, cy + 40 * s), (cx - 4 * s, cy + 46 * s), (cx - w // 4, cy + 22 * s)]
    d.polygon(pts, fill=rock[1], outline=INK)
    for i in range(1, 4):                                           # 지층
        yy = cy + i * 9 * s
        d.line((cx - w // 2 + i * 9 * s, yy, cx + w // 2 - i * 11 * s, yy + 2), fill=rock[min(3, i)])
    d.polygon([(cx - w // 2 + 4, cy + 1), (cx - w // 4, cy + 20 * s), (cx - 6 * s, cy + 8)], fill=rock[0])
    d.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=(118, 188, 98), outline=INK)
    d.ellipse((cx - w // 2 + 4, cy - h // 2 + 1, cx + w // 2 - 4, cy + h // 2 - 5), fill=(152, 210, 118))
    for k in range(-w // 2 + 6, w // 2 - 4, 7):                   # 섬 가장자리 풀
        d.line((cx + k, cy + h // 2 - 1, cx + k + 1, cy + h // 2 + 2), fill=(96, 164, 84))
    # 섬 위 작은 매화 + 기와집
    tx = cx + (-w // 4 if not flip else w // 4)
    d.line((tx, cy - 2, tx - 3, cy - 12 * s), fill=(80, 56, 50), width=2); d.line((tx - 3, cy - 12 * s, tx + 4, cy - 16 * s), fill=(80, 56, 50))
    for dx, dy in ((-6, -14), (0, -17), (5, -14), (-2, -10), (6, -18)):
        d.point((tx + dx * s, cy + dy * s), fill=(255, 196, 214)); d.point((tx + dx * s + 1, cy + dy * s), fill=(255, 226, 236))
    hx = cx + (w // 6 if not flip else -w // 6)
    crystal(d, hx, cy - 1, int(16 * s), (150, 210, 255)); crystal(d, hx + 7, cy, int(10 * s), (214, 170, 255)); crystal(d, hx - 6, cy, int(8 * s), (150, 210, 255))
    # 폭포 + 물안개
    fx = cx + (w // 3 if not flip else -w // 3)
    for i, y in enumerate(range(int(cy + 4), int(cy + 64 * s), 2)):
        a = (y - cy) / (64 * s)
        c = mix((236, 248, 255), (206, 230, 248), a)
        d.line((fx + ((i + int(t * 16)) % 3 == 0), y, fx + 2, y), fill=c)
    for i in range(3):
        r = 2 + ((int(t * 12) + i * 3) % 5)
        d.ellipse((fx + 1 - r, cy + 64 * s - r // 2, fx + 1 + r, cy + 64 * s + r // 2), outline=(240, 248, 255))



# ================= 판타지 소품 =================
def crystal(d, x, y, h, col):
    """빛나는 수정 기둥 (아래 x,y 기준)"""
    w = max(3, h // 3)
    dark = mix(col, (40, 50, 110), .45); light = mix(col, (255, 255, 255), .55)
    pts = [(x - w // 2, y), (x - w // 2, y - h + w), (x, y - h), (x + w // 2, y - h + w), (x + w // 2, y)]
    d.polygon(pts, fill=col, outline=INK)
    d.polygon([(x, y - h + 1), (x + w // 2 - 1, y - h + w), (x + w // 2 - 1, y - 1), (x, y - 1)], fill=dark)
    d.line((x - w // 2 + 1, y - h + w, x - w // 2 + 1, y - 2), fill=light)
    d.point((x - 1, y - h + 2), fill=(255, 255, 255))


def rainbow(base):
    lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
    cols = [(255, 120, 120), (255, 190, 110), (255, 240, 130), (140, 220, 140), (130, 190, 255), (180, 150, 255)]
    for i, c in enumerate(cols):
        r = 300 - i * 6
        d.arc((600 - r, 250 - r, 600 + r, 250 + r), 228, 300, fill=c + (70,), width=6)
    base.alpha_composite(lay)


def far_tower(d, x, y):
    """먼 언덕 위 하얀 탑 (판타지 성)"""
    c, c2, roof = (232, 236, 246), (196, 204, 222), (110, 140, 214)
    for (tx, tw, th) in ((x - 12, 8, 26), (x, 12, 42), (x + 14, 8, 30)):
        d.rectangle((tx - tw // 2, y - th, tx + tw // 2, y), fill=c, outline=(120, 130, 160))
        d.line((tx + tw // 2 - 1, y - th + 1, tx + tw // 2 - 1, y - 1), fill=c2)
        d.polygon([(tx - tw // 2 - 2, y - th), (tx + tw // 2 + 2, y - th), (tx, y - th - tw - 6)], fill=roof, outline=(70, 90, 150))
        d.point((tx, y - th + 6), fill=(255, 220, 120))
        d.line((tx, y - th - tw - 6, tx, y - th - tw - 11), fill=(120, 130, 160)); d.point((tx + 1, y - th - tw - 10), fill=(240, 90, 90))


def float_rock(d, x, y, w):
    d.polygon([(x - w // 2, y), (x + w // 2, y), (x + w // 4, y + w // 2), (x - w // 6, y + w // 2 + 2)], fill=(132, 106, 96), outline=INK)
    d.ellipse((x - w // 2, y - 3, x + w // 2, y + 3), fill=(124, 190, 100), outline=INK)
    d.line((x - w // 2 + 3, y - 1, x + w // 4, y - 1), fill=(160, 214, 124))


def meadow(base):
    """돌담 대신: 겹겹이 언덕 + 언덕 위 수정·버섯"""
    d = ImageDraw.Draw(base)
    layers = [(222, [(10, .02, .3), (5, .05, 1.2)], (146, 204, 120), (176, 222, 146)),
              (240, [(8, .025, 2.2), (4, .06, .2)], (126, 192, 102), (156, 212, 124))]
    for by, waves, col, top in layers:
        pts = [(x, by - sum(a * math.sin(x * f + p) for a, f, p in waves)) for x in range(0, W + 4, 2)]
        d.polygon(pts + [(W, H), (0, H)], fill=col); d.line(pts, fill=top, width=2)


def ruin_arch(d, x, y, hh=46):
    """이끼 낀 옛 돌문 (테크모 자리). 꼭대기 = y - hh - 9"""
    st, st2, st3 = (196, 190, 176), (164, 158, 146), (226, 222, 210)
    for px in (x - 24, x + 14):                                    # 기둥 두 개
        for i, by in enumerate(range(y - hh, y, 9)):
            d.rectangle((px, by, px + 10, by + 8), fill=st if i % 2 else st3, outline=st2)
        d.rectangle((px - 2, y - 2, px + 12, y + 2), fill=st2, outline=INK)
    d.rectangle((x - 30, y - hh - 8, x + 30, y - hh), fill=st3, outline=INK)   # 윗돌
    d.line((x - 29, y - hh - 7, x + 29, y - hh - 7), fill=(246, 244, 236))
    for i in range(-28, 28, 10): d.line((x + i, y - hh - 8, x + i, y - hh), fill=st2)
    d.rectangle((x - 14, y - hh, x + 14, y - hh + 6), fill=st, outline=INK)
    for vx in (x - 26, x - 4, x + 20):                                 # 덩굴 + 작은 꽃
        for k in range(0, 22, 2):
            d.point((vx + int(2 * math.sin(k / 3)), y - hh + k), fill=(82, 150, 82))
        d.point((vx + 1, y - hh + 8), fill=(255, 190, 210)); d.point((vx - 1, y - hh + 16), fill=(255, 240, 150))
    for mx in range(x - 30, x + 31, 3):                                # 위 이끼
        d.point((mx, y - hh - 9), fill=(110, 176, 90)); d.point((mx + 1, y - hh - 10 + (mx % 2)), fill=(140, 200, 110))
    crystal(d, x + 36, y, 18, (150, 210, 255)); crystal(d, x + 44, y, 11, (214, 170, 255))


def mushroom(d, x, y, s=1, col=(236, 96, 120)):
    d.rectangle((x - s, y - 4 * s, x + s, y), fill=(250, 240, 220), outline=INK)
    d.ellipse((x - 5 * s, y - 9 * s, x + 5 * s, y - 3 * s), fill=col, outline=INK)
    d.point((x - 2 * s, y - 7 * s), fill=(255, 255, 255)); d.point((x + 2 * s, y - 6 * s), fill=(255, 255, 255))


def motes(base, t):
    """떠다니는 빛 알갱이 (반딧불처럼)"""
    d = ImageDraw.Draw(base); rng = random.Random(9)
    for i in range(18):
        x0, y0 = rng.randrange(W), rng.randrange(150, 330)
        ph = (t + i / 18) % 1
        x = x0 + 8 * math.sin(ph * math.pi * 2 + i); y = y0 - ph * 40
        a = math.sin(ph * math.pi)
        if a > .3:
            c = (255, 250, 190) if i % 2 else (210, 236, 255)
            d.point((x, y), fill=c)
            if a > .75: d.point((x + 1, y), fill=c); d.point((x, y - 1), fill=c)


# ================= (옛) 한옥 지붕·돌담 · 쓰지 않음 =================
ROOF = [(58, 64, 82), (78, 86, 106), (100, 110, 132), (128, 138, 160)]


def hanok(base, cx, y, w):
    """처마가 살짝 올라간 기와지붕 + 흰 벽·나무 기둥·창살 (아래는 담에 가려짐)"""
    d = ImageDraw.Draw(base)
    half = w // 2
    # 벽·기둥
    d.rectangle((cx - half + 10, y + 12, cx + half - 10, y + 44), fill=(246, 240, 228))
    for px in range(cx - half + 10, cx + half - 9, (w - 20) // 3):
        d.rectangle((px, y + 12, px + 3, y + 44), fill=(146, 96, 62)); d.line((px, y + 12, px, y + 44), fill=(110, 70, 44))
    d.rectangle((cx - half + 10, y + 12, cx + half - 10, y + 15), fill=(146, 96, 62))
    for k in range(2):                                              # 창살 창
        wx = cx - half + 20 + k * ((w - 40) // 2)
        d.rectangle((wx, y + 20, wx + 16, y + 34), fill=(250, 236, 200), outline=(110, 70, 44))
        for g in range(1, 4): d.line((wx + g * 4, y + 20, wx + g * 4, y + 34), fill=(176, 130, 90))
        for g in range(1, 3): d.line((wx, y + 20 + g * 5, wx + 16, y + 20 + g * 5), fill=(176, 130, 90))
    # 지붕: 아래 처마선이 양 끝에서 올라감
    def eave(x):
        u = (x - cx) / half
        return y + 12 - int(7 * u ** 4)
    top = [(cx - half + 18 + i, y - 8) for i in range(0, w - 35)]
    lower = [(x, eave(x)) for x in range(cx - half - 4, cx + half + 5)]
    pts = [(cx - half - 4, eave(cx - half - 4))] + [(cx - half + 14, y - 4), (cx - half + 20, y - 9)] + [(cx + half - 20, y - 9), (cx + half - 14, y - 4)] + lower[::-1]
    d.polygon(pts, fill=ROOF[1])
    for x in range(cx - half, cx + half + 1, 4):                  # 기와 골
        e = eave(x); d.line((x, max(y - 7, e - 18), x, e - 1), fill=ROOF[0])
        d.point((x + 2, e - 1), fill=ROOF[3])
    d.line((cx - half + 20, y - 9, cx + half - 20, y - 9), fill=ROOF[3], width=2)    # 용마루
    d.line((cx - half + 20, y - 8, cx + half - 20, y - 8), fill=ROOF[0])
    for lx, sgn in ((cx - half + 20, -1), (cx + half - 20, 1)):    # 용마루 끝 치미
        d.polygon([(lx, y - 9), (lx + 6 * sgn, y - 13), (lx + 4 * sgn, y - 8)], fill=ROOF[2], outline=INK)
    d.line(lower, fill=INK)
    d.line([(x, e - 2) for x, e in lower], fill=ROOF[3])
    d.line([pts[0], pts[1], pts[2]], fill=INK); d.line([pts[3], pts[4], lower[-1]], fill=INK)
    d.line((cx - half + 20, y - 10, cx + half - 20, y - 10), fill=INK)


def stone_wall(base, y0, y1, rng):
    """돌담 + 위 기와 지붕"""
    d = ImageDraw.Draw(base)
    d.rectangle((0, y0, W, y1), fill=(222, 212, 196))
    stones = [(196, 186, 172), (182, 172, 160), (206, 196, 182), (168, 160, 150), (190, 176, 156)]
    y = y0 + 9
    row = 0
    while y < y1:
        x = -rng.randrange(12)
        hh = min(9, y1 - y)
        while x < W:
            w = rng.randrange(12, 22)
            c = rng.choice(stones)
            d.rounded_rectangle((x + 1, y + 1, x + w - 1, y + hh - 1), 3, fill=c)
            d.line((x + 3, y + 2, x + w - 4, y + 2), fill=mix(c, (255, 255, 255), .35))
            d.line((x + 3, y + hh - 2, x + w - 4, y + hh - 2), fill=mix(c, (90, 80, 70), .3))
            x += w
        y += hh; row += 1
    # 기와 덮개
    d.rectangle((0, y0 - 2, W, y0 + 8), fill=ROOF[1])
    d.line((0, y0 - 3, W, y0 - 3), fill=INK); d.line((0, y0 - 2, W, y0 - 2), fill=ROOF[3])
    for x in range(0, W, 6):
        d.line((x, y0, x, y0 + 7), fill=ROOF[0])
        d.ellipse((x - 1, y0 + 6, x + 4, y0 + 10), fill=ROOF[2], outline=INK)
    d.line((0, y1, W, y1), fill=(150, 140, 128))


# ================= 매화 =================
def plum_tree(base, x, y, scale=1.0, seed=1, flip=False, blossoms=None, big=False, trunk_len=40):
    """굽은 검은 가지 + 분홍·흰 꽃송이. blossoms 리스트에 꽃 위치를 모아 줌(꽃잎 날리기용)"""
    d = ImageDraw.Draw(base); rng = random.Random(seed)
    BR = [(58, 40, 40), (84, 58, 54), (112, 80, 72)]
    flowers = []

    def branch(x0, y0, ang, ln, w, depth):
        pts = [(x0, y0)]
        cx, cy, a = x0, y0, ang
        for i in range(int(ln)):
            a += rng.uniform(-.18, .18)
            cx += math.cos(a); cy += math.sin(a)
            pts.append((cx, cy))
        ww = max(1, int(w))
        for i, (px, py) in enumerate(pts):
            r = max(1, ww * (1 - i / len(pts) * .5) / 2)
            d.ellipse((px - r, py - r, px + r, py + r), fill=BR[0])
        for i, (px, py) in enumerate(pts[::2]):                      # 위쪽 하이라이트
            if ww >= 3: d.point((px, py - ww // 2 + 1), fill=BR[2])
        if depth >= 1:
            for i, (px, py) in enumerate(pts):
                if i % 3 == 1 and rng.random() < .85:
                    for _ in range(rng.choice((1, 2, 2, 3))):
                        flowers.append((px + rng.randint(-4, 4), py + rng.randint(-5, 2)))
        if depth < 4 and ln > 6:
            for k in range(rng.choice((2, 2, 3))):
                na = a + rng.uniform(-.9, .9)
                branch(cx, cy, na, ln * rng.uniform(.5, .72), w * .6, depth + 1)
        else:
            flowers.extend([(cx + rng.randint(-5, 5), cy + rng.randint(-5, 4)) for _ in range(6)])

    sgn = -1 if flip else 1
    # 줄기: 굽은 몸통
    trunk = [(x, y)]
    for i in range(int(trunk_len * scale)):
        trunk.append((trunk[-1][0] + sgn * (.35 + .4 * math.sin(i / 7)), trunk[-1][1] - 1))
    for i, (px, py) in enumerate(trunk):
        r = (7 - i / len(trunk) * 3) * scale
        d.ellipse((px - r, py - r, px + r, py + r), fill=BR[0])
        if i % 3 == 0: d.point((px - sgn * r * .4, py), fill=BR[1])
    tx, ty = trunk[-1]
    branch(tx, ty, -math.pi / 2 - sgn * .9, 34 * scale, 6 * scale, 0)
    branch(tx, ty, -math.pi / 2 + sgn * .7, 30 * scale, 5 * scale, 0)
    branch(trunk[len(trunk) * 2 // 3][0], trunk[len(trunk) * 2 // 3][1], -math.pi / 2 + sgn * .75, 24 * scale, 4 * scale, 1)
    # 꽃: 5잎 (가운데 노랑) / 봉오리
    PET = [(255, 214, 228), (255, 186, 208), (255, 244, 248), (236, 132, 170)]
    for i, (fx, fy) in enumerate(flowers):
        fx, fy = int(fx), int(fy)
        if rng.random() < .18:
            d.point((fx, fy), fill=PET[3]); d.point((fx, fy - 1), fill=PET[1]); continue
        white = rng.random() < .3
        c = PET[2] if white else PET[0]; c2 = (255, 255, 255) if white else PET[1]; edge = (226, 150, 182) if not white else (232, 214, 224)
        if big and rng.random() < .65:                               # 큰 꽃: 5잎 (잎마다 2×2)
            for (dx, dy) in ((0, -2), (-2, -1), (2, -1), (-1, 1), (1, 1)):
                d.rectangle((fx + dx - 1, fy + dy - 1, fx + dx, fy + dy), fill=c)
            d.point((fx - 2, fy - 2), fill=c2); d.point((fx + 1, fy + 2), fill=edge)
            d.point((fx, fy), fill=(250, 196, 70)); d.point((fx - 1, fy), fill=(236, 120, 150))
            continue
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): d.point((fx + dx, fy + dy), fill=c)
        for dx, dy in ((-1, -1), (1, 1)): d.point((fx + dx, fy + dy), fill=c2)
        d.point((fx, fy), fill=(250, 200, 80))
    if blossoms is not None: blossoms.extend(flowers)


# ================= 향나무 =================
def juniper(base, x, y, scale=1.0, seed=2, flip=False, shape='bonsai'):
    """구불구불한 붉은 갈색 줄기 + 구름처럼 층진 짙은 초록 잎덩이"""
    d = ImageDraw.Draw(base); rng = random.Random(seed)
    TR = [(96, 56, 44), (132, 80, 58), (168, 108, 76)]
    LF = [(36, 78, 60), (52, 104, 72), (76, 132, 86), (112, 164, 104), (150, 194, 128)]
    sgn = -1 if flip else 1
    if shape == 'round':                                            # 동그랗게 다듬은 향나무 (담 앞)
        r = int(14 * scale)
        d.rectangle((x - 2, y - 6, x + 2, y), fill=TR[0])
        pads = [(0, -r - 4, r)]
        for k, col in enumerate(LF[:4]):
            for (dx, dy, rr) in pads:
                q = rr - k * 3
                d.ellipse((x + dx - q - k, y + dy - q - k, x + dx + q - k, y + dy + q - k), fill=col)
        for _ in range(int(20 * scale)):
            a = rng.uniform(0, math.pi * 2); rr = rng.uniform(0, r * .8)
            d.point((x + rr * math.cos(a), y - r - 4 + rr * math.sin(a)), fill=LF[4] if math.sin(a) < 0 else LF[0])
        return
    # 분재형: 굵고 꼬인 줄기 + 구름 같은 잎덩이 여러 층
    pts = []
    n = int(78 * scale)
    for i in range(n):
        u = i / n
        pts.append((x + sgn * (18 * math.sin(u * math.pi * 1.4) - 10 * u) * scale, y - i))
    for i, (px, py) in enumerate(pts):
        r = (9 - i / n * 5) * scale
        d.ellipse((px - r, py - r, px + r, py + r), fill=TR[0])
    for i, (px, py) in enumerate(pts):                                # 꼬인 결 (밝은 사선)
        r = (9 - i / n * 5) * scale
        if i % 6 < 3: d.point((px - r * .4 + (i % 6), py), fill=TR[1])
        if i % 9 == 0: d.line((px - r * .6, py, px + r * .3, py - 3), fill=TR[2])
    d.ellipse((x - 14 * scale, y - 4, x + 14 * scale, y + 4), fill=TR[0])   # 뿌리
    def pad(cx, cy, w):
        h = w * .45
        blobs = [(cx + w * f, cy - h * .5 * math.sin((f + .5) * math.pi), h * (.55 + .25 * math.sin((f + .5) * math.pi))) for f in (-.5, -.25, 0, .25, .5)]
        for k, col in enumerate(LF):
            for (bx, by, r) in blobs:
                q = r - k * 2.2
                if q <= 0: continue
                d.ellipse((bx - q - k * .8, by - q - k * 1.6, bx + q - k * .8, by + q - k * 1.6), fill=col)
        for _ in range(int(w * .9)):                                  # 잎 결
            bx, by, r = blobs[rng.randrange(5)]
            a = rng.uniform(math.pi * 1.05, math.pi * 1.95)
            d.point((bx + r * .8 * math.cos(a), by + r * .7 * math.sin(a)), fill=LF[4])
        for _ in range(int(w * .4)):
            bx, by, r = blobs[rng.randrange(5)]
            d.point((bx + rng.uniform(-r, r) * .8, by + rng.uniform(.2, .9) * r), fill=LF[0])
    tip = pts[-1]; mid = pts[int(n * .6)]; low = pts[int(n * .32)]
    for (fx, fy, tx, ty) in ((mid[0], mid[1], mid[0] + sgn * 30 * scale, mid[1] - 4), (low[0], low[1], low[0] - sgn * 30 * scale, low[1] + 2)):
        d.line((fx, fy, tx, ty), fill=TR[0], width=int(4 * scale))
    pad(low[0] - sgn * 34 * scale, low[1] - 2, 26 * scale)
    pad(mid[0] + sgn * 36 * scale, mid[1] - 6, 30 * scale)
    pad(tip[0] - sgn * 6 * scale, tip[1] - 8, 34 * scale)
    pad(tip[0] + sgn * 14 * scale, tip[1] - 26 * scale, 22 * scale)


# ================= 땅·길·소품 =================
def ground(base, rng):
    d = ImageDraw.Draw(base)
    d.rectangle((0, 250, W, H), fill=(128, 194, 100))
    for y in range(252, H, 6): d.line((0, y, W, y), fill=(120, 186, 94))
    for _ in range(700): d.point((rng.randrange(W), rng.randrange(252, H)), fill=rng.choice(((108, 174, 86), (156, 214, 120), (140, 204, 110))))
    # 흙길 (가로, 가장자리 풀 섞임)
    d.rectangle((0, 270, W, 302), fill=(230, 206, 156))
    for x in range(0, W, 3):
        d.point((x, 270 + (x * 7) % 3), fill=(150, 204, 112)); d.point((x, 301 - (x * 5) % 3), fill=(150, 204, 112))
    for _ in range(120):
        x, y = rng.randrange(W), rng.randrange(274, 298); d.point((x, y), fill=rng.choice(((214, 188, 138), (244, 224, 182))))
    for _ in range(14):                                                # 디딤돌
        x, y = rng.randrange(20, W - 40), rng.randrange(306, 340)
    for (x, y) in ((262, 312), (300, 322), (340, 314), (378, 324)):
        d.ellipse((x, y, x + 24, y + 9), fill=(184, 178, 170), outline=(120, 114, 108)); d.line((x + 4, y + 2, x + 16, y + 2), fill=(214, 208, 200))


def flower_spots(base, rng, y0, y1, n, cols=None):
    d = ImageDraw.Draw(base)
    cols = cols or [(255, 255, 255), (255, 186, 208), (255, 226, 110), (204, 186, 255)]
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(y0, y1); c = rng.choice(cols)
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)): d.point((x + dx, y + dy), fill=c)
        d.point((x, y), fill=(250, 210, 80)); d.line((x, y + 2, x, y + 3), fill=(84, 150, 70))


def rock(d, x, y, w, h):
    d.ellipse((x, y, x + w, y + h), fill=(168, 162, 158), outline=INK)
    d.ellipse((x + 3, y + 2, x + w - 6, y + h - 5), fill=(196, 190, 186))
    d.line((x + 6, y + 3, x + w // 2, y + 3), fill=(226, 222, 218))
    d.line((x + 6, y + h - 2, x + w - 6, y + h - 2), fill=(120, 114, 110))


def stone_lantern(d, x, y):
    """석등 (정원 소품)"""
    c, c2, c3 = (190, 186, 178), (154, 150, 144), (222, 218, 210)
    d.rectangle((x - 3, y - 18, x + 3, y), fill=c2, outline=INK)
    d.rectangle((x - 8, y - 2, x + 8, y + 2), fill=c, outline=INK)
    d.rectangle((x - 6, y - 30, x + 6, y - 18), fill=c, outline=INK); d.rectangle((x - 3, y - 27, x + 3, y - 21), fill=(255, 220, 140))
    d.polygon([(x - 11, y - 30), (x + 11, y - 30), (x + 4, y - 37), (x - 4, y - 37)], fill=c2, outline=INK)
    d.line((x - 9, y - 31, x + 9, y - 31), fill=c3)
    d.rectangle((x - 2, y - 41, x + 2, y - 37), fill=c, outline=INK)


def front_grass(base):
    d = ImageDraw.Draw(base)
    for x in range(-10, W + 20, 30):
        for k, col in enumerate(((60, 126, 70), (82, 152, 80), (108, 176, 92))):
            r = 15 - k * 3
            for dx in (-12, 0, 12):
                d.ellipse((x + dx - r, 356 - r - k * 2 + (x % 4), x + dx + r, 356 + r - k * 2), fill=col)
    for x in range(0, W, 4):
        h = 4 + (x * 13) % 5
        d.line((x, 346, x + 1, 346 - h), fill=(70, 140, 74))


# ================= 큰 로고 =================
GLYPH = {
    'E': ['XXXXXX', 'XXXXXX', 'XX....', 'XXXXX.', 'XXXXX.', 'XX....', 'XX....', 'XXXXXX', 'XXXXXX'],
    'v': ['......', '......', '......', 'XX..XX', 'XX..XX', 'XX..XX', '.XXXX.', '.XXXX.', '..XX..'],
    'o': ['......', '......', '......', '.XXXX.', 'XX..XX', 'XX..XX', 'XX..XX', 'XX..XX', '.XXXX.'],
    'T': ['XXXXXXXX', 'XXXXXXXX', '...XX...', '...XX...', '...XX...', '...XX...', '...XX...', '...XX...', '...XX...'],
    'a': ['......', '......', '......', '.XXXX.', '....XX', '.XXXXX', 'XX..XX', 'XX..XX', '.XXXXX'],
    'i': ['XX', 'XX', '..', 'XX', 'XX', 'XX', 'XX', 'XX', 'XX'],
    'l': ['XX.', 'XX.', 'XX.', 'XX.', 'XX.', 'XX.', 'XX.', 'XX.', 'XXX'],
}
EVO = [(255, 248, 176), (255, 228, 102), (252, 202, 64), (238, 170, 44)]
TAIL = [(255, 218, 156), (252, 168, 84), (240, 126, 56), (214, 94, 46)]
TAIL_ROWS = ['....OOO.', '..OOOOOO', '.OOOOOOW', 'OOOOOWWW', 'OOOOWWW.', '.OOO....']


def big_logo(base, cx, cy, cell=7, t=0.0, jump=None):
    """jump = (글자 번호, 높이) : 이스터에그용 글자 통통"""
    word = 'EvoTail'
    widths = [len(GLYPH[c][0]) for c in word]
    total = sum(widths) + len(word) - 1
    w, h = total * cell, 9 * cell
    full = Image.new('L', (w + 8 * cell, h + cell)); fd = ImageDraw.Draw(full)
    face = Image.new('RGBA', full.size); fc = ImageDraw.Draw(face)
    x = 0
    for i, c in enumerate(word):
        lift = jump[1] if jump and jump[0] == i else 0
        pal = EVO if i < 3 else TAIL
        for r, row in enumerate(GLYPH[c]):
            for k, ch in enumerate(row):
                if ch == 'X':
                    rx, ry = (x + k) * cell, r * cell - lift
                    fd.rectangle((rx, ry + cell, rx + cell - 1, ry + 2 * cell - 1), fill=255)
                    fc.rectangle((rx, ry + cell, rx + cell - 1, ry + 2 * cell - 1), fill=pal[min(3, r * 4 // 9)] + (255,))
                    if r == 0 or GLYPH[c][r - 1][k] != 'X':          # 윗면 하이라이트
                        fc.rectangle((rx, ry + cell, rx + cell - 1, ry + cell + cell // 3), fill=(255, 255, 236, 255))
        x += widths[i] + 1
    # 여우 꼬리 (l 끝)
    for r, row in enumerate(TAIL_ROWS):
        for k, ch in enumerate(row):
            if ch == '.': continue
            rx, ry = (total - 1 + k) * cell, (r + 4) * cell
            col = (255, 248, 236) if ch == 'W' else ((252, 168, 84) if r <= 1 else (240, 126, 56))
            fd.rectangle((rx, ry, rx + cell - 1, ry + cell - 1), fill=255); fc.rectangle((rx, ry, rx + cell - 1, ry + cell - 1), fill=col + (255,))
    x0, y0 = cx - full.width // 2 + 3 * cell, cy - full.height // 2
    ext, pad = 6, 4
    big = Image.new('L', (full.width + pad * 2 + ext, full.height + pad * 2 + ext))
    for e in range(ext + 1): big.paste(255, (pad + e, pad + e), full)
    ring = Image.new('L', big.size)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if abs(dx) + abs(dy) <= 4: ring.paste(255, (dx, dy), big)
    shadow = Image.new('RGBA', big.size, (40, 60, 90, 90))
    base.paste(shadow, (x0 - pad + 5, y0 - pad + 7), ring) if False else None
    base.alpha_composite(Image.composite(Image.new('RGBA', big.size, (30, 40, 70, 80)), Image.new('RGBA', big.size, (0, 0, 0, 0)), ring), (x0 - pad + 4, y0 - pad + 8))
    base.paste(Image.new('RGBA', ring.size, INK + (255,)), (x0 - pad, y0 - pad), ring)
    side = Image.new('L', big.size)
    for e in range(1, ext + 1): side.paste(255, (pad + e, pad + e), full)
    base.paste(Image.new('RGBA', side.size, (150, 66, 40, 255)), (x0 - pad, y0 - pad), side)
    side2 = Image.new('L', big.size)
    for e in range(1, 3): side2.paste(255, (pad + e, pad + e), full)
    base.paste(Image.new('RGBA', side2.size, (200, 100, 54, 255)), (x0 - pad, y0 - pad), side2)
    base.alpha_composite(face, (x0, y0))
    # 반짝이
    d = ImageDraw.Draw(base)
    for i, (sx, sy) in enumerate(((x0 - 12, y0 + 18), (x0 + full.width + 6, y0 + 22), (x0 + 110, y0 + 2), (x0 + 30, y0 + full.height + 6), (x0 + full.width - 60, y0 + 4))):
        ph = (t * 2 + i * .29) % 1
        if ph < .55:
            r = 1 + int(ph * 6) % 3
            d.line((sx - r, sy, sx + r, sy), fill=(255, 255, 230)); d.line((sx, sy - r, sx, sy + r), fill=(255, 255, 230)); d.point((sx, sy), fill=(255, 255, 255))
    return x0, y0, full.width, full.height


def subtitle(base, cx, y):
    f = K.F_TITLE(); t = '떠 있는 섬의 작은 친구들'
    w = int(tl(t, f)) + 26
    d = ImageDraw.Draw(base)
    d.polygon([(cx - w // 2 - 10, y + 2), (cx - w // 2, y + 2), (cx - w // 2, y + 16), (cx - w // 2 - 10, y + 16), (cx - w // 2 - 6, y + 9)], fill=(176, 50, 60), outline=INK)
    d.polygon([(cx + w // 2 + 10, y + 2), (cx + w // 2, y + 2), (cx + w // 2, y + 16), (cx + w // 2 + 10, y + 16), (cx + w // 2 + 6, y + 9)], fill=(176, 50, 60), outline=INK)
    d.rectangle((cx - w // 2, y, cx + w // 2, y + 14), fill=(214, 72, 78), outline=INK)
    d.line((cx - w // 2 + 1, y + 1, cx + w // 2 - 1, y + 1), fill=(240, 120, 120))
    text_mid(base, cx, y + 7, t, f, (255, 250, 236), (130, 30, 40))


# ================= 메뉴 =================
MENU = ['새 게임', '이어하기', '설정', '게임 종료']


def menu(base, sel, t, y0, flash=False):
    f = K.F_BIG(); d = ImageDraw.Draw(base)
    # 반투명 한지 판 (글씨가 풍경 위에서도 잘 읽히게)
    pw, ph = 150, len(MENU) * 19 + 10
    panel = Image.new('RGBA', (W, H)); pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle((320 - pw // 2, y0 - 12, 320 + pw // 2, y0 - 12 + ph), 6, fill=(255, 250, 238, 170), outline=(120, 86, 60, 220))
    base.alpha_composite(panel)
    cur = Image.new('RGBA', (9, 9)); cd = ImageDraw.Draw(cur)          # 커서 = 매화 한 송이
    for (dx, dy) in ((4, 1), (1, 3), (7, 3), (2, 7), (6, 7)): cd.ellipse((dx - 1, dy - 1, dx + 1, dy + 1), fill=(255, 196, 216), outline=(196, 90, 130))
    cd.point((4, 4), fill=(250, 200, 70)); cd.point((3, 4), fill=(236, 120, 150))
    for i, s in enumerate(MENU):
        y = y0 + i * 19
        on = i == sel
        col = (255, 216, 64) if on else (255, 255, 255)
        if on and flash: col = (255, 255, 255) if int(t * 24) % 2 else (255, 150, 60)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (2, 2), (1, 2)):
            K.draw_text(base, (320 + dx, y + dy), s, f, INK if on else (70, 52, 44), 'mm')
        K.draw_text(base, (320, y), s, f, col, 'mm')
        if on:
            tw = tl(s, f); bob = round(2 * math.sin(t * math.pi * 8))
            c2 = cur.resize((cur.width * 2, cur.height * 2), Image.NEAREST)
            base.alpha_composite(c2, (int(320 - tw / 2 - 26 + bob), y - c2.height // 2))
    K.draw_text(base, (8, 352), '© 2026 EvoTail 팀', K.F_SMALL(), (255, 255, 255), 'lm', INK)
    K.draw_text(base, (632, 352), 'v1.0', K.F_SMALL(), (255, 255, 255), 'rm', INK)


# ================= 장면 =================
_STATIC = {}


def static_layers():
    """움직이지 않는 뒤·앞 레이어 (한 번만 그림)"""
    if _STATIC: return _STATIC
    rng = random.Random(5)
    back = Image.new('RGBA', (W, H)); sky(back); mountains(back)
    mid = Image.new('RGBA', (W, H))
    blossoms = []
    rainbow(back)
    dd = ImageDraw.Draw(back)
    far_tower(dd, 446, 190)
    for (rx, ry, rw) in ((236, 120, 14), (420, 132, 10), (40, 160, 12), (612, 168, 10)):
        float_rock(dd, rx, ry, rw)
    meadow(mid)
    plum_tree(mid, 520, 236, 1.0, seed=7, flip=True, blossoms=blossoms)
    d = ImageDraw.Draw(mid)
    ruin_arch(d, 168, 266, 36)
    for (cx_, h_, c_) in ((300, 14, (150, 210, 255)), (312, 9, (214, 170, 255)), (430, 12, (214, 170, 255)), (440, 18, (150, 210, 255))):
        crystal(d, cx_, 258, h_, c_)
    for (mx, s_, c_) in ((360, 1, (236, 96, 120)), (372, 1, (250, 180, 70)), (604, 2, (236, 96, 120)), (586, 1, (180, 130, 230))):
        mushroom(d, mx, 264 if s_ == 1 else 268, s_, c_)
    ground(mid, rng)
    flower_spots(mid, rng, 254, 268, 26)
    flower_spots(mid, rng, 306, 344, 60)
    d = ImageDraw.Draw(mid)
    rock(d, 96, 326, 30, 12); rock(d, 548, 330, 26, 10)
    front = Image.new('RGBA', (W, H))                                  # 앞 큰 나무는 행렬보다 앞에
    plum_tree(front, 26, 318, 1.5, seed=3, blossoms=blossoms, big=True, trunk_len=64)
    plum_tree(front, 614, 318, 1.5, seed=34, flip=True, blossoms=blossoms, big=True, trunk_len=64)
    front_grass(front)
    _STATIC.update(back=back, mid=mid, front=front, blossoms=blossoms)
    return _STATIC


import json as _json
_CH = _json.load(open(GAME / 'data' / 'characters.json'))
PARADE = [k for k, v in _CH.items() if v['rarity'] == 'normal']        # 일반 15종 (도감 순서)
TECHMO_POS = (168 - 32, 266 - 44 - 62)                                  # 옛 돌문 위 (발 = 돌문 꼭대기)


def petals(base, t, src):
    d = ImageDraw.Draw(base); rng = random.Random(21)
    for i in range(46):
        sx, sy = src[rng.randrange(len(src))]
        ph = (t + i / 46) % 1
        x = sx + ph * 140 + 6 * math.sin(ph * math.pi * 6 + i)
        y = sy + ph * 120
        if y > 350: continue
        c = (255, 206, 222) if i % 3 else (255, 244, 248)
        if int(ph * 20 + i) % 2: d.point((x, y), fill=c); d.point((x + 1, y), fill=c)
        else: d.point((x, y), fill=c); d.point((x, y + 1), fill=c)


def actors(base, frame_i, t, surprise=0.0, techmo_kind=None):
    """발 위치(y) 순서로 그려서 앞뒤가 겹치지 않게"""
    items = []
    gap, speed = 64, 2
    for i, k in enumerate(PARADE):
        x = (i * gap + frame_i * speed) % (len(PARADE) * gap) - 60
        hop = -3 if ((frame_i // 3) + i) % 2 == 0 else 0
        if surprise: hop = -int(14 * math.sin(min(1, surprise) * math.pi))
        items.append((298, 'animal', (k, x, hop)))
    items.append((222, 'techmo', None))
    d = ImageDraw.Draw(base)
    for foot, kind, data in sorted(items, key=lambda v: v[0]):
        if kind == 'animal':
            k, x, hop = data
            d.ellipse((x + 12, 293, x + 44, 299), fill=(206, 180, 130))
            base.alpha_composite(spr(k, 2).transpose(Image.FLIP_LEFT_RIGHT), (x, 242 + hop))
            if surprise:
                d.rectangle((x + 26, 226 + hop, x + 30, 236 + hop), fill=(230, 60, 60), outline=INK); d.rectangle((x + 26, 238 + hop, x + 30, 241 + hop), fill=(230, 60, 60), outline=INK)
        else:
            FLAP = ['flap3', 'idle', 'flap1', 'flap2', 'flap1', 'idle']
            if techmo_kind == 'flap': kind2 = FLAP[frame_i % 6]
            elif techmo_kind == 'flap_talk': kind2 = FLAP[frame_i % 6] + ('_talk' if FLAP[frame_i % 6] != 'idle' else '')
            elif techmo_kind: kind2 = techmo_kind
            elif frame_i % 38 in (12, 13): kind2 = 'blink'
            elif 24 <= frame_i % 38 < 36: kind2 = FLAP[(frame_i % 38 - 24) % 6]
            else: kind2 = 'idle'
            base.alpha_composite(techmo.frame(kind2, 2), TECHMO_POS)


def butterflies(base, t):
    d = ImageDraw.Draw(base)
    for i, (bx, by, c) in enumerate(((210, 258, (255, 236, 120)), (470, 250, (255, 186, 210)))):
        fx = bx + round(14 * math.sin(t * math.pi * 2 + i)); fy = by + round(5 * math.sin(t * math.pi * 4 + i))
        flap = int(t * 18 + i) % 2
        d.rectangle((fx - 3, fy - (2 if flap else 1), fx - 1, fy + 1), fill=c); d.rectangle((fx + 1, fy - (2 if flap else 1), fx + 3, fy + 1), fill=c); d.point((fx, fy), fill=INK)


def frame(t, fi, sel=0, flash=False, surprise=0.0, techmo_kind=None, logo_jump=None):
    L = static_layers()
    base = L['back'].copy()
    for (x, y, w, sp) in ((24, 40, 70, 6), (470, 34, 96, 4), (300, 26, 50, 8), (560, 136, 56, 5), (150, 128, 44, 7)):
        puff_cloud(base, (x + t * sp * 6) % (W + 120) - 60, y, w)
    float_island(base, 84, 62, t, .8)
    float_island(base, 566, 56, (t + .4) % 1, .75, flip=True)
    d = ImageDraw.Draw(base)
    for i in range(4):
        bx = (430 - i * 12 + int(t * 220)) % 720 - 40
        y = 46 + (i % 2) * 5; flap = (int(t * 24) + i) % 2
        d.line((bx - 3, y - (2 if flap else -1), bx, y, bx + 3, y - (2 if flap else -1)), fill=(70, 80, 110))
    base.alpha_composite(L['mid'])
    actors(base, fi, t, surprise, techmo_kind)
    petals(base, t, L['blossoms'])
    motes(base, t)
    butterflies(base, t)
    base.alpha_composite(L['front'])
    big_logo(base, 320, 96, 7, t, logo_jump)
    subtitle(base, 320, 142)
    menu(base, sel, t, 182, flash)
    return base


def iris(base, cx, cy, r):
    m = Image.new('L', (W, H), 255); ImageDraw.Draw(m).ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
    base.paste(Image.new('RGBA', (W, H), (14, 10, 20, 255)), (0, 0), m)
    if r > 0: ImageDraw.Draw(base).ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 214, 80))


def gif(frames, out, ms=80, scale=2):
    fr = [f.convert('RGB').resize((W * scale, H * scale), Image.NEAREST).quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    fr[0].save(out, save_all=True, append_images=fr[1:], duration=ms, loop=0, optimize=False, disposal=1)


if __name__ == '__main__':
    K.FONT_DIR = GAME / 'assets' / 'fonts'
    o = Path(sys.argv[1]); o.mkdir(exist_ok=True)
    only_png = 'png' in sys.argv
    frame(0.1, 3).resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(o / 'title_v5.png')
    if only_png: sys.exit()
    N = 38
    gif([frame(i / N, i) for i in range(N)], o / 'title_v5_idle.gif')
    seq = []
    for i in range(10): seq.append(frame((N + i) / N, N + i, flash=True, techmo_kind='flap'))
    for i in range(8): seq.append(frame((N + 10 + i) / N, N + 10, flash=True, surprise=(i + 1) / 8, techmo_kind='flap_talk'))
    cx, cy = TECHMO_POS[0] + 32, TECHMO_POS[1] + 28
    for i in range(16):
        b = frame((N + 18 + i) / N, N + 10, techmo_kind='flap_talk'); r = int(420 * (1 - i / 15) ** 1.6) + (16 if i < 15 else 0)
        iris(b, cx, cy, max(0, r)); seq.append(b)
    for i in range(5): seq.append(Image.new('RGBA', (W, H), (14, 10, 20, 255)))
    gif(seq, o / 'title_v5_newgame.gif', ms=70)
    print('ok')
