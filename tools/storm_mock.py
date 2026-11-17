"""태풍 연출 목업: 실제 화면(태풍 시간 스크린샷) 위에 비·그늘·먹구름·번개·상단 바 칩·알림·훈련 2배를 덧그림."""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import battle_mock as B
from ui_mock import paste, chip, text_mid

W, H = 640, 360
INK = K.INK
GAME = Path('/home/claude/evotail_project')
SHOTS = Path(__file__).resolve().parent.parent / 'storm' / 'shots'
MENU_X = 582                          # 지도 오른쪽 메뉴 판 시작 (논리)

K.ICON_ROWS['rain'] = ("............", "...OOOO.....", "..OGGGGOO...", ".OGWWGGGGO..", "OGWGGGGGGGO.", "OGGGGGGGGGO.",
                       ".OOOOOOOOO..", "..B..B..B...", ".B..B..B....", "............", "..B..B......", "............")


def shot(name):
    return Image.open(SHOTS / name).convert('RGBA').resize((W, H), Image.NEAREST)


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def tint(base, box, col=(18, 26, 64, 70)):
    lay = Image.new('RGBA', (box[2] - box[0], box[3] - box[1]), col); base.alpha_composite(lay, box[:2])


def rain(base, box, t=0, n=260, seed=3, splash=True):
    """빗줄기: 2px 아래 · 1px 왼쪽으로 기운 5~7px 선 (앞쪽은 밝고 김, 뒤쪽은 어둡고 짧음). t = 프레임"""
    x0, y0, x1, y1 = box
    lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
    rnd = random.Random(seed); hh = y1 - y0
    for i in range(n):
        near = rnd.random() < .35
        L = 7 if near else 4
        x = rnd.randrange(x0, x1 + 40); y = rnd.randrange(0, hh)
        sp = 14 if near else 9
        y = (y + t * sp) % hh + y0; x = x - int((y - y0) / 2) % (x1 - x0 + 40)
        x = x0 + (x - x0) % (x1 - x0)
        c = (196, 214, 250, 190) if near else (150, 170, 220, 120)
        d.line((x, y, x - L // 2, y + L), fill=c)
    if splash:
        for i in range(36):
            x = rnd.randrange(x0 + 4, x1 - 4); y = rnd.randrange(y0 + 40, y1 - 4)
            ph = (i + t) % 4
            if ph == 0: d.point([(x - 1, y), (x + 1, y)], fill=(200, 220, 255, 170))
            elif ph == 1: d.point([(x - 2, y - 1), (x + 2, y - 1), (x, y)], fill=(200, 220, 255, 140))
            elif ph == 2: d.ellipse((x - 3, y - 1, x + 3, y + 1), outline=(170, 196, 240, 90))
    base.alpha_composite(lay)


def storm_clouds(base, t=0):
    """섬 밖 하늘(왼쪽 위 달 자리, 오른쪽 위 구석)에만 먹구름 덩어리 - 달을 가림. 섬 위 건물은 안 가림"""
    lay = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(lay)
    clumps = [(22, 46, 18), (46, 40, 20), (70, 50, 16), (34, 62, 14), (8, 70, 14), (96, 42, 13),
              (500, 38, 14), (526, 46, 16), (552, 40, 18), (570, 58, 14), (12, 300, 14), (30, 316, 12)]
    for cx, cy, r in clumps:
        cx += (t // 3) % 3 - 1
        d.ellipse((cx - r, cy - r // 2 + 2, cx + r, cy + r // 2 + 3), fill=(40, 44, 70, 240))
        d.ellipse((cx - r + 2, cy - r // 2, cx + r - 2, cy + r // 2), fill=(66, 70, 100, 240))
        d.arc((cx - r + 4, cy - r // 2 + 1, cx + r - 6, cy + r // 2 - 2), 200, 300, fill=(96, 100, 134, 240))
    # 섬 모양 밖에만 (섬 = 지도 그림의 타원 안쪽)
    m = Image.new('L', (W, H), 255); ImageDraw.Draw(m).ellipse((8, 40, 600, 352), fill=0)
    base.alpha_composite(Image.composite(lay, Image.new('RGBA', (W, H)), m))


def bolt(base, x, y):
    """먹구름에서 섬 가장자리 쪽으로 꺾이는 번개 (3px 굵기, 노란 테두리)"""
    d = ImageDraw.Draw(base)
    pts = [(x, y), (x - 5, y + 10), (x + 1, y + 12), (x - 7, y + 24), (x - 1, y + 26), (x - 10, y + 40)]
    d.line(pts, fill=(255, 214, 90), width=4); d.line(pts, fill=(255, 252, 230), width=2)
    d.line(((x - 5, y + 10), (x - 11, y + 16)), fill=(255, 240, 180), width=1)


def flash(base, box, a=70):
    tint(base, box, (236, 240, 255, a))


def storm_pill(base, txt='1일차 · 밤 04:12'):
    """상단 바 가운데: 기존 판을 지우고 '…· [비구름]태풍' 파란 칩으로"""
    d = ImageDraw.Draw(base)
    x0, x1 = 242, 398
    moon = base.crop((246, 6, 258, 20)).copy()
    d.rectangle((x0 + 3, 4, x1 - 3, 21), fill=K.PAPER[2])
    f = K.F_BODY()
    paste(base, moon, (246, 6))
    K.draw_text(base, (260, 13), txt, f, K.TEXT, 'lm')
    cx = 262 + int(f.getlength(txt)) + 6
    w = 44
    d.rectangle((cx, 5, cx + w, 20), fill=K.BTN['blue'][2], outline=INK); d.line((cx + 1, 6, cx + w - 1, 6), fill=K.BTN['blue'][3])
    paste(base, K.icon('rain'), (cx + 3, 7))
    K.draw_text(base, (cx + 17, 13), '태풍', K.F_SMALL(), (255, 255, 255), 'lm', K.BTN['blue'][0])


def toast(base, x, y, lines, ic='rain', col='blue'):
    f1, f2 = K.F_TITLE(), K.F_SMALL()
    w = max(int(f1.getlength(lines[0])), int(f2.getlength(lines[1]))) + 34; h = 34
    B.card(base, x, y, w, h)
    d = ImageDraw.Draw(base); d.rectangle((x + 2, y + 2, x + 4, y + h - 3), fill=K.BTN[col][2])
    paste(base, K.icon(ic).resize((24, 24), Image.NEAREST) if False else K.icon(ic), (x + 9, y + 11))
    K.draw_text(base, (x + 26, y + 11), lines[0], f1, K.TEXT, 'lm')
    K.draw_text(base, (x + 26, y + 24), lines[1], f2, (60, 100, 170), 'lm')


def event_banner(base, x, y, t=0):
    """태풍 중 계속 떠 있는 2배 이벤트 띠: 파란 리본 + 금색 '2배 이벤트' + 효과 칩 2개"""
    from ui_mock import ribbon
    f = K.F_TITLE()
    title = '태풍 2배 이벤트'
    w = int(f.getlength(title)) + 40
    ribbon(base, x, y, w, '', 'blue')
    paste(base, K.icon('rain'), (x + 10, y + 3))
    K.draw_text(base, (x + 25, y + 8), '태풍', f, (255, 255, 255), 'lm', K.BTN['blue'][0])
    K.draw_text(base, (x + 25 + int(f.getlength('태풍 ')), y + 8), '2배 이벤트', f, (255, 226, 110) if t % 6 < 4 else (255, 250, 210), 'lm', K.BTN['blue'][0])
    cx = x + 4
    for txt in ('훈련 효과 ×2', '일반 전투 보상 ×2'):
        chip(base, cx, y + 21, txt, 'orange'); cx += int(K.F_SMALL().getlength(txt)) + 14


def storm_map(t=0, lightning=False, toast_on=True):
    base = shot('map.png')
    box = (0, 26, MENU_X, H)
    storm_clouds(base, t)
    tint(base, box)
    rain(base, box, t)
    if lightning:
        bolt(base, 60, 46); flash(base, box, 60)
    storm_pill(base)
    event_banner(base, 10, 32, t)
    if toast_on:
        toast(base, 10, 316, ['태풍이 왔다! 2배 이벤트 시작', '훈련 효과 2배 · 일반 전투 보상 2배'])
    return base


def storm_training():
    base = shot('animals.png')
    d = ImageDraw.Draw(base)
    storm_pill(base)
    # 훈련 칸: "공격력 훈련" 옆 칩
    for bx, base_txt, new in ((300, '10분 · +10', '+20'), (408, '30분 · +30', '+60'), (516, '60분 · +65', '+130')):
        sub_y = 300
        col = base.getpixel((bx + 4, sub_y))
        d.rectangle((bx + 4, sub_y - 6, bx + 96, sub_y + 6), fill=col)
        f = K.F_SMALL()
        a = base_txt.split('+')[0]
        wa = int(f.getlength(a)); wb = int(f.getlength(new))
        sx = bx + 50 - (wa + wb + 14) // 2
        K.draw_text(base, (sx, sub_y), a, f, (255, 255, 255), 'lm', K.BTN['green'][0])
        K.draw_text(base, (sx + wa, sub_y), new, f, (255, 236, 120), 'lm', K.BTN['green'][0])
        paste(base, K.icon('rain'), (sx + wa + wb + 2, sub_y - 6))
    return base


def storm_room():
    base = shot('room.png')
    win = (248, 40, 350, 114)
    lay = Image.new('RGBA', (W, H))
    rain(lay, win, 0, n=60, seed=7, splash=False)
    d = ImageDraw.Draw(lay)
    rnd = random.Random(4)
    for _ in range(14):                                           # 유리에 맺힌 물방울
        x, y = rnd.randrange(win[0] + 3, win[2] - 3), rnd.randrange(win[1] + 16, win[3] - 3)
        d.point((x, y), fill=(220, 236, 255, 220)); d.point((x, y + 1), fill=(140, 170, 220, 200))
        if rnd.random() < .4: d.line((x, y + 2, x, y + 5), fill=(170, 196, 240, 140))
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).rectangle(win, fill=255)
    base.alpha_composite(Image.composite(lay, Image.new('RGBA', (W, H)), m))
    storm_pill(base)
    return base


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else '.'); out.mkdir(parents=True, exist_ok=True)
    K.FONT_DIR = GAME / 'assets' / 'fonts'; B.SPR = GAME / 'assets' / 'sprites'
    save(storm_map(), out / 'storm_1_map.png')
    b = shot('map.png'); storm_pill(b); toast(b, 10, 316, ['태풍이 지나갔다', '2배 이벤트 끝'], 'sun', 'orange'); save(b, out / 'storm_5_end.png')
    save(storm_map(lightning=True, toast_on=False), out / 'storm_2_lightning.png')
    save(storm_training(), out / 'storm_3_training.png')
    save(storm_room(), out / 'storm_4_room.png')
    frames = []
    for t in range(16):
        im = storm_map(t, lightning=t in (9, 10), toast_on=False)
        frames.append(im.convert('RGB').resize((W * 2, H * 2), Image.NEAREST))
    frames[0].save(out / 'storm_map.gif', save_all=True, append_images=frames[1:], duration=[90] * 16, loop=0)
