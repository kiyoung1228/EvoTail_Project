"""집(주방) 화면 목업: 요리 고르기 / 미니게임 A(막대) / 미니게임 B(온도계 바늘) / 결과."""
import sys, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
import food_icons as F
from ui_mock import paste, button, gauge, chip, ribbon

W, H = 640, 360
INK = K.INK
STAR = (250, 204, 70)


def kitchen(dim=False):
    rnd = random.Random(3)
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    wall = [(250, 232, 200), (238, 214, 176), (222, 196, 156)]
    d.rectangle((0, 26, W, 250), fill=wall[0])
    for x in range(0, W, 16):                                         # 벽지 줄무늬
        d.line((x, 26, x, 200), fill=wall[1])
    d.rectangle((0, 200, W, 250), fill=K.WOOD[3])                     # 아래 판자벽
    for x in range(0, W, 24): d.line((x, 201, x, 249), fill=K.WOOD[2])
    d.line((0, 200, W, 200), fill=K.WOOD[1]); d.line((0, 201, W, 201), fill=K.WOOD[4])
    # 창문
    d.rectangle((40, 50, 160, 150), fill=K.WOOD[1], outline=INK)
    d.rectangle((48, 58, 152, 142), fill=(170, 220, 246))
    d.rectangle((48, 110, 152, 142), fill=(150, 210, 120)); d.ellipse((60, 96, 110, 126), fill=(120, 190, 100))
    d.ellipse((112, 66, 132, 78), fill=(255, 255, 255)); d.ellipse((122, 62, 146, 76), fill=(255, 255, 255))
    d.line((100, 58, 100, 142), fill=K.WOOD[1], width=3); d.line((48, 100, 152, 100), fill=K.WOOD[1], width=3)
    d.rectangle((34, 150, 166, 156), fill=K.WOOD[2], outline=INK)
    for x, c in ((52, (230, 90, 90)), (70, (250, 204, 70)), (130, (140, 200, 120))):
        d.rectangle((x, 140, x + 10, 150), fill=(200, 120, 80), outline=INK); d.ellipse((x - 1, 132, x + 11, 142), fill=c, outline=INK)
    # 선반 + 병
    for y in (70, 116):
        d.rectangle((420, y, 600, y + 5), fill=K.WOOD[2], outline=INK)
        for i, x in enumerate(range(428, 596, 22)):
            c = [(230, 120, 90), (250, 204, 70), (140, 200, 230), (180, 140, 220), (140, 200, 120), (240, 160, 190), (230, 200, 160), (200, 120, 80)][(i + y) % 8]
            h = 16 + (i * 5 + y) % 8
            d.rectangle((x, y - h, x + 14, y - 1), fill=(240, 248, 252), outline=INK)
            d.rectangle((x + 2, y - h + 5, x + 12, y - 2), fill=c)
            d.rectangle((x + 3, y - h - 3, x + 11, y - h), fill=K.WOOD[2], outline=INK)
    # 냄비 걸이
    d.line((200, 52, 380, 52), fill=K.WOOD[1], width=2)
    for x, r in ((220, 12), (262, 10), (300, 14), (346, 9)):
        d.line((x, 52, x, 60), fill=INK); d.ellipse((x - r, 60, x + r, 60 + 2 * r), fill=(170, 176, 190), outline=INK)
        d.ellipse((x - r + 3, 63, x - r + 7, 67), fill=(230, 236, 246))
    # 조리대 + 화덕
    d.rectangle((0, 238, W, 250), fill=(200, 200, 210), outline=INK)
    d.rectangle((0, 250, W, 300), fill=K.WOOD[2]); d.line((0, 251, W, 251), fill=K.WOOD[4])
    for x in range(0, W, 80):
        d.rectangle((x + 6, 258, x + 74, 296), outline=K.WOOD[1]); d.rectangle((x + 36, 272, x + 44, 276), fill=GOLDC)
    d.rectangle((240, 170, 400, 250), fill=(80, 76, 90), outline=INK)
    d.rectangle((248, 178, 392, 196), fill=(60, 56, 70))
    d.rectangle((262, 214, 378, 246), fill=(40, 36, 46), outline=INK)
    for x in range(272, 372, 14):
        d.polygon([(x, 246), (x + 5, 226 - (x % 3) * 4), (x + 10, 246)], fill=(250, 150, 60))
        d.polygon([(x + 2, 246), (x + 5, 234), (x + 8, 246)], fill=(255, 226, 120))
    d.rectangle((300, 26, 340, 170), fill=(100, 96, 110), outline=INK)
    # 바닥
    d.rectangle((0, 300, W, H), fill=K.WOOD[3])
    for y in range(300, H, 12):
        d.line((0, y, W, y), fill=K.WOOD[2])
        for x in range((y // 12 % 2) * 30, W, 60): d.line((x, y, x, y + 11), fill=K.WOOD[2])
    if dim:
        im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.55)).enhance(.7)
    return im


GOLDC = (226, 182, 124)


def stars(base, x, y, n, total=5):
    d = ImageDraw.Draw(base)
    for i in range(total):
        cx = x + i * 9
        col = STAR if i < n else (200, 186, 160)
        d.polygon([(cx + 3, y), (cx + 4, y + 3), (cx + 7, y + 3), (cx + 5, y + 5), (cx + 6, y + 8), (cx + 3, y + 6), (cx, y + 8), (cx + 1, y + 5), (cx - 1, y + 3), (cx + 2, y + 3)], fill=col, outline=INK if i < n else None)


def top(base, title='집 · 주방'):
    B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 100, title, 'red')


def cook_level(base, x=420, y=31):
    B.card(base, x, y, 212, 22)
    K.draw_text(base, (x + 8, y + 11), '요리 Lv.2', K.F_TITLE(), K.TEXT, 'lm')
    gauge(base, x + 70, y + 7, 84, 8, 140, 300, 'orange')
    K.draw_text(base, (x + 160, y + 11), '140/300', K.F_SMALL(), K.TEXT_SOFT, 'lm')


RECIPES = [('boiled_egg', '삶은 달걀', 1, True), ('steamed_potato', '찐 감자', 1, True), ('egg_roll', '계란말이', 2, False),
           ('tomato_soup', '토마토수프', 2, True), ('butter_potato', '감자버터구이', 2, True), ('chicken_burger', '닭고기 햄버거', 3, False),
           ('beef_burger', '소고기 햄버거', 3, False), ('fried_chicken', '치킨', 4, False), ('carbonara', '까르보나라', 5, False)]


# ---------------- 1. 요리 고르기 ----------------
def pick(out):
    base = kitchen(dim=True); top(base); cook_level(base)
    # 탭
    for i, (t, on) in enumerate((('요리하기', True), ('음식 주기', False))):
        button(base, 190 + i * 84, 32, 80, 20, t, 'orange' if on else 'gray', 'normal', f=K.F_SMALL())
    # 왼쪽 목록
    B.panel(base, 8, 58, 236, 298)
    d = ImageDraw.Draw(base)
    for i, (key, name, st, ok) in enumerate(RECIPES):
        y = 68 + i * 31
        sel = key == 'butter_potato'
        B.card(base, 18, y, 216, 28, sel)
        paste(base, F.icon(key, 1), (24, y + 6))
        K.draw_text(base, (46, y + 10), name, K.F_TITLE(), K.TEXT if ok else K.TEXT_SOFT, 'lm')
        stars(base, 46, y + 16, st)
        if ok: chip(base, 186, y + 8, '가능', 'green')
        else: K.draw_text(base, (226, y + 14), '재료 부족', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    d.rectangle((236, 68, 238, 344), fill=K.PAPER[1]); d.rectangle((236, 68, 238, 200), fill=K.WOOD[2])
    # 오른쪽 상세
    B.panel(base, 250, 58, 382, 298)
    d.rectangle((264, 72, 344, 152), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, F.icon('butter_potato', 4), (272, 80))
    K.draw_text(base, (356, 82), '감자버터구이', K.F_BIG(), K.TEXT, 'lm')
    stars(base, 356, 94, 2)
    x = 356
    for t, c in (('커서 1.6초', 'brown'), ('경험치 +20', 'purple')):
        x += chip(base, x, 108, t, c) + 3
    K.draw_text(base, (356, 136), 'Miss가 나와도 10% 확률로 성공', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (356, 148), '(구제되면 경험치는 없어요)', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 재료
    ribbon(base, 264, 164, 60, '재료', 'brown')
    for i, (k, have, need) in enumerate((('potato', 3, 1), ('butter', 1, 1))):
        x = 264 + i * 112
        B.card(base, x, 186, 106, 30)
        paste(base, F.icon(k, 1), (x + 6, y := 193))
        K.draw_text(base, (x + 26, 201), F.INGREDIENTS[k][0], K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (x + 98, 201), f'{have}/{need}', K.F_TITLE(), K.BTN['green'][1], 'rm')
    # 효과
    ribbon(base, 264, 226, 60, '효과', 'brown')
    for i, (ic, label, v) in enumerate((('meat', '포만감', '+30'), ('smile', '기분', '+10'))):
        x = 264 + i * 112
        paste(base, K.icon(ic), (x, 250)); K.draw_text(base, (x + 16, 256), f'{label} {v}', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (264, 274), '대성공(Perfect)이면 효과 1.5배 요리가 나와요', K.F_SMALL(), K.BTN['orange'][1], 'lm')
    button(base, 440, 304, 180, 40, '요리 시작!', 'orange', icon='snack')
    K.draw_text(base, (264, 324), '타이밍 맞춰 스페이스바 한 번!', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- 2A. 미니게임: 막대 ----------------
def game_bar(out):
    base = kitchen(); top(base, '요리 중'); cook_level(base)
    d = ImageDraw.Draw(base)
    # 프라이팬 위 재료
    d.ellipse((274, 196, 366, 222), fill=(60, 60, 70), outline=INK); d.ellipse((280, 198, 360, 216), fill=(90, 90, 104))
    d.line((364, 206, 410, 196), fill=INK, width=5); d.line((366, 205, 408, 196), fill=K.WOOD[1], width=3)
    paste(base, F.icon('potato', 2), (296, 182)); paste(base, F.icon('butter', 2), (318, 180))
    for x in (300, 322, 344):
        d.line((x, 170, x - 2, 160), fill=(240, 244, 250)); d.line((x - 2, 160, x + 1, 152), fill=(240, 244, 250))
    # 위 카드
    B.card(base, 220, 60, 200, 34)
    K.draw_text(base, (320, 72), '감자버터구이', K.F_TITLE(), K.TEXT, 'mm')
    stars(base, 298, 80, 2)
    # 타이머
    B.card(base, 520, 60, 112, 34)
    K.draw_text(base, (530, 72), '남은 시간', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    gauge(base, 530, 80, 92, 8, 62, 100, 'orange')
    # 막대 (0~100 → 400px)
    gx, gy, gw = 120, 262, 400
    B.panel(base, gx - 16, gy - 18, gw + 32, 74)
    d.rectangle((gx, gy, gx + gw, gy + 22), fill=(90, 70, 60), outline=INK)
    c = 62                                                               # 목표 중심
    gl, gr = gx + (c - 15) * gw // 100, gx + (c + 15) * gw // 100
    pl, pr = gx + (c - 5) * gw // 100, gx + (c + 5) * gw // 100
    d.rectangle((gl, gy + 1, gr, gy + 21), fill=K.BTN['orange'][2]); d.line((gl, gy + 1, gr, gy + 1), fill=K.BTN['orange'][3])
    d.rectangle((pl, gy + 1, pr, gy + 21), fill=STAR); d.line((pl, gy + 1, pr, gy + 1), fill=(255, 246, 200))
    K.draw_text(base, ((gl + pl) // 2, gy + 30), 'Good', K.F_SMALL(), K.BTN['orange'][1], 'mm')
    K.draw_text(base, ((pl + pr) // 2, gy + 30), 'Perfect', K.F_SMALL(), K.BTN['orange'][0], 'mm')
    K.draw_text(base, ((pr + gr) // 2, gy + 30), 'Good', K.F_SMALL(), K.BTN['orange'][1], 'mm')
    cx = gx + 48 * gw // 100                                              # 커서
    d.rectangle((cx - 1, gy - 6, cx + 1, gy + 27), fill=(255, 255, 255), outline=INK)
    d.polygon([(cx - 6, gy - 12), (cx + 6, gy - 12), (cx, gy - 4)], fill=(255, 255, 255), outline=INK)
    # 안내
    B.card(base, 240, 330, 160, 24)
    d.rectangle((252, 335, 300, 349), fill=(240, 240, 246), outline=INK); d.line((253, 348, 299, 348), fill=(170, 170, 184))
    K.draw_text(base, (276, 341), 'SPACE', K.F_SMALL(), K.TEXT, 'mm')
    K.draw_text(base, (308, 342), '지금 누르기!', K.F_TITLE(), K.TEXT, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- 2B. 미니게임: 불 세기 바늘 ----------------
def game_dial(out):
    import math
    base = kitchen(); top(base, '요리 중'); cook_level(base)
    d = ImageDraw.Draw(base)
    d.ellipse((274, 196, 366, 222), fill=(60, 60, 70), outline=INK); d.ellipse((280, 198, 360, 216), fill=(90, 90, 104))
    d.line((364, 206, 410, 196), fill=INK, width=5); d.line((366, 205, 408, 196), fill=K.WOOD[1], width=3)
    paste(base, F.icon('potato', 2), (296, 182)); paste(base, F.icon('butter', 2), (318, 180))
    # 반원 게이지 (0~100 → 180°~0°)
    cx, cy, R0, R1 = 320, 160, 70, 92
    B.panel(base, cx - 112, 58, 224, 116)
    def ang(v): return math.radians(180 - v * 1.8)
    def arc(v0, v1, col):
        pts = []
        for i in range(31):
            a = ang(v0 + (v1 - v0) * i / 30); pts.append((cx + R1 * math.cos(a), cy - R1 * math.sin(a)))
        for i in range(31):
            a = ang(v1 - (v1 - v0) * i / 30); pts.append((cx + R0 * math.cos(a), cy - R0 * math.sin(a)))
        d.polygon(pts, fill=col)
    arc(0, 100, (90, 70, 60))
    c = 62
    arc(c - 15, c + 15, K.BTN['orange'][2]); arc(c - 5, c + 5, STAR)
    for v in range(0, 101, 10):
        a = ang(v); d.line((cx + (R0 - 4) * math.cos(a), cy - (R0 - 4) * math.sin(a), cx + R0 * math.cos(a), cy - R0 * math.sin(a)), fill=INK)
    d.arc((cx - R1, cy - R1, cx + R1, cy + R1), 180, 360, fill=INK); d.arc((cx - R0, cy - R0, cx + R0, cy + R0), 180, 360, fill=INK)
    a = ang(48)
    d.line((cx, cy, cx + (R1 + 4) * math.cos(a), cy - (R1 + 4) * math.sin(a)), fill=INK, width=4)
    d.line((cx, cy, cx + (R1 + 2) * math.cos(a), cy - (R1 + 2) * math.sin(a)), fill=(255, 255, 255), width=2)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=K.BTN['red'][2], outline=INK)
    K.draw_text(base, (cx - R1 + 12, cy + 8), '약불', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    K.draw_text(base, (cx + R1 - 12, cy + 8), '강불', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    K.draw_text(base, (cx, cy - R1 - 0), '', K.F_SMALL(), K.TEXT, 'mm')
    # 왼쪽 정보 / 오른쪽 타이머
    B.card(base, 40, 70, 150, 50)
    paste(base, F.icon('butter_potato', 2), (48, 78))
    K.draw_text(base, (86, 86), '감자버터구이', K.F_TITLE(), K.TEXT, 'lm'); stars(base, 86, 96, 2)
    B.card(base, 470, 70, 130, 50)
    K.draw_text(base, (480, 84), '남은 시간', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    gauge(base, 480, 96, 110, 10, 62, 100, 'orange')
    B.card(base, 220, 300, 200, 30)
    d.rectangle((232, 308, 280, 322), fill=(240, 240, 246), outline=INK)
    K.draw_text(base, (256, 315), 'SPACE', K.F_SMALL(), K.TEXT, 'mm')
    K.draw_text(base, (290, 316), '노란 칸에서 멈춰요!', K.F_TITLE(), K.TEXT, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- 3. 결과 ----------------
def result(out):
    base = kitchen(dim=True); top(base, '요리 완성'); cook_level(base)
    d = ImageDraw.Draw(base)
    B.panel(base, 170, 62, 300, 290)
    ribbon(base, 270, 54, 100, '대성공!', 'green')
    # 반짝이 접시
    d.rectangle((262, 84, 378, 176), fill=(255, 246, 214), outline=K.WOOD[2])
    for i in range(12):
        import math
        a = i * math.pi / 6
        d.line((320, 130, 320 + 50 * math.cos(a), 130 + 40 * math.sin(a)), fill=(255, 236, 170))
    paste(base, F.icon('butter_potato', 4), (288, 98))
    for x, y in ((276, 92), (362, 96), (366, 160), (272, 162)):
        d.line((x - 3, y, x + 3, y), fill=STAR); d.line((x, y - 3, x, y + 3), fill=STAR)
    K.draw_text(base, (320, 190), 'PERFECT', K.F_BIG(), K.BTN['orange'][1], 'mm')
    K.draw_text(base, (320, 208), '대성공 감자버터구이 ×1', K.F_TITLE(), K.TEXT, 'mm')
    for i, (ic, t) in enumerate((('meat', '포만감 +45'), ('smile', '기분 +15'))):
        x = 238 + i * 90
        paste(base, K.icon(ic), (x, 220)); K.draw_text(base, (x + 16, 226), t, K.F_TITLE(), K.BTN['green'][1], 'lm')
    K.draw_text(base, (320, 244), '효과 1.5배!', K.F_SMALL(), K.BTN['orange'][1], 'mm')
    # 경험치
    B.card(base, 190, 256, 260, 34)
    K.draw_text(base, (200, 267), '요리 Lv.2', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (440, 267), '경험치 +20', K.F_TITLE(), K.BTN['purple'][1], 'rm')
    gauge(base, 200, 276, 240, 8, 160, 300, 'orange')
    d.rectangle((202 + 236 * 140 // 300, 278, 201 + 236 * 160 // 300, 281), fill=(255, 246, 170))
    button(base, 190, 302, 124, 34, '한 번 더', 'orange', icon='snack')
    button(base, 326, 302, 124, 34, '동물에게 주기', 'green', icon='heart', f=K.F_SMALL())
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(exist_ok=True)
    pick(out / 'home_1_pick.png'); game_bar(out / 'home_2A_bar.png'); game_dial(out / 'home_2B_dial.png'); result(out / 'home_3_result.png')
    print('ok')
