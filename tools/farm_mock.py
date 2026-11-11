"""밭 화면 후보 A(밭 + 오른쪽 칸) / B(밭 + 아래 씨앗 줄) / C(목록) + 수확 결과."""
import sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
import food_icons as F
import farm_icons as FI
from ui_mock import paste, button, gauge, chip, ribbon, text_mid

W, H = 640, 360
INK = K.INK
RED = K.BTN['red'][1]; GREEN = K.BTN['green'][1]
CROPS = [('potato', '감자', 3), ('tomato', '토마토', 1), ('rice', '쌀', 2), ('wheat', '밀', 0), ('onion', '양파', 0), ('cabbage', '양배추', 0)]
NAME = {k: n for k, n, _ in CROPS}
# 지금 밭 상태 (4칸 보유, 다음 넓히기 900)
PLOTS = [('tomato', 'ripe', 0), ('potato', 'growing', 252), ('wheat', 'sprout', 510), (None, None, 0)]
NEXT_COST = 900


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def tl(t, f): return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(t, font=f)


def crop_icon(k):
    return FI.cabbage_icon() if k == 'cabbage' else getattr(F, k)()


def plant(k, st):
    im = FI.RIPE[k]() if st == 'ripe' else FI.STAGES[st]()
    return im.resize((48, 48), Image.NEAREST)


# ---------------- 배경 ----------------
def farm_bg(dim=False):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    for i, c in enumerate([(168, 220, 250), (184, 228, 252), (200, 236, 252)]):          # 하늘 3단
        d.rectangle((0, 26 + i * 18, W, 44 + i * 18), fill=c)
    d.rectangle((0, 80, W, 110), fill=(212, 240, 252))
    for cx, cy, r in ((90, 48, 1), (420, 40, 1.3), (560, 62, .9)):                           # 구름
        for dx, dy, rr in ((0, 0, 10), (12, -5, 9), (24, 0, 10), (10, 4, 9)):
            rr *= r; d.ellipse((cx + dx * r - rr, cy + dy * r - rr * .6, cx + dx * r + rr, cy + dy * r + rr * .6), fill=(255, 255, 255))
    for x0, h, c in ((-40, 34, (134, 196, 120)), (200, 44, (120, 186, 110)), (420, 30, (134, 196, 120))):   # 먼 언덕
        d.ellipse((x0, 104 - h, x0 + 300, 104 + h), fill=c)
    d.rectangle((0, 100, W, H), fill=(128, 196, 96))                                          # 풀밭
    for y in range(106, H, 6):
        for x in range((y * 7) % 13, W, 13): d.point((x, y), fill=(110, 178, 82))
    # 나무 (왼쪽, 지도 버튼 아래로)
    d.rectangle((40, 82, 46, 104), fill=(120, 78, 46), outline=INK)
    for bx in ((22, 60, 64, 90), (14, 68, 44, 92), (42, 66, 72, 94), (28, 56, 58, 76)):
        d.ellipse(bx, fill=(84, 160, 74), outline=INK)
    for x, y in ((32, 60), (50, 70), (22, 74)): d.ellipse((x, y, x + 8, y + 5), fill=(126, 196, 98))
    for x, y in ((34, 78), (56, 80), (26, 84)): d.ellipse((x, y, x + 4, y + 4), fill=(232, 70, 60), outline=INK)
    # 헛간 + 사일로 (가운데 뒤, 오른쪽 칸에 안 가려지는 자리)
    d.rectangle((394, 46, 422, 104), fill=(196, 206, 220), outline=INK)                                  # 사일로
    for y in range(52, 104, 8): d.line((395, y, 421, y), fill=(160, 172, 192))
    d.line((396, 47, 396, 103), fill=(232, 238, 246))
    d.pieslice((394, 34, 422, 60), 180, 360, fill=(170, 60, 56), outline=INK)
    d.polygon([(300, 64), (346, 36), (392, 64)], fill=(170, 52, 48), outline=INK)                         # 지붕
    d.line((304, 63, 346, 38), fill=(214, 96, 84))
    d.rectangle((306, 64, 386, 104), fill=(210, 78, 66), outline=INK)                                   # 벽
    for x in range(312, 386, 8): d.line((x, 65, x, 103), fill=(186, 62, 54))
    d.rectangle((330, 76, 362, 104), fill=(246, 236, 214), outline=INK)                                 # 큰 문
    d.rectangle((333, 79, 359, 104), fill=(196, 70, 60), outline=INK)
    d.line((333, 79, 359, 104), fill=(246, 236, 214)); d.line((359, 79, 333, 104), fill=(246, 236, 214))
    d.rectangle((338, 46, 354, 58), fill=(246, 236, 214), outline=INK); d.rectangle((341, 49, 351, 58), fill=(60, 40, 40))   # 다락 창
    for x in (288, 270):                                                                                 # 건초 더미
        d.rounded_rectangle((x, 90, x + 16, 104), 3, fill=(240, 204, 100), outline=INK)
        d.line((x + 2, 94, x + 14, 94), fill=(204, 160, 60)); d.line((x + 2, 99, x + 14, 99), fill=(204, 160, 60))
    # 울타리
    d.rectangle((0, 104, W, 106), fill=(214, 170, 110), outline=INK); d.rectangle((0, 112, W, 114), fill=(214, 170, 110), outline=INK)
    for x in range(6, W, 24):
        d.rectangle((x, 98, x + 4, 118), fill=(232, 192, 130), outline=INK); d.point((x + 1, 99), fill=(250, 226, 180))
    if dim: im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.6)).enhance(.75)
    return im


def soil(base, x, y, w, h):
    """나무 틀 텃밭 + 포슬포슬한 흙 (점 무늬, 줄무늬 아님)"""
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w - 1, y + h - 1), fill=K.WOOD[2], outline=INK)                 # 나무 틀
    d.line((x + 1, y + 1, x + w - 2, y + 1), fill=K.WOOD[4]); d.line((x + 1, y + h - 2, x + w - 2, y + h - 2), fill=K.WOOD[1])
    for xx in range(x + 24, x + w - 4, 32): d.point((xx, y + 2), fill=K.WOOD[1]); d.point((xx, y + h - 3), fill=K.WOOD[1])
    d.rectangle((x + 4, y + 4, x + w - 5, y + h - 5), fill=(132, 84, 50), outline=(84, 50, 28))
    d.line((x + 5, y + 5, x + w - 6, y + 5), fill=(92, 56, 32))                                # 틀 그림자
    for j, yy in enumerate(range(y + 8, y + h - 6, 3)):
        for i in range((j * 7) % 11, w - 10, 11):
            xx = x + 6 + i
            if xx < x + w - 6:
                d.point((xx, yy), fill=(168, 112, 70)); d.point((xx + 1, yy + 1), fill=(104, 64, 38))


def locked(base, x, y, w, h, cost, next_one):
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w - 1, y + h - 1), fill=(112, 176, 84) if next_one else (98, 150, 76), outline=(70, 120, 56))
    for i in range(0, w, 8): d.point((x + i + 3, y + 6 + (i * 5) % (h - 12)), fill=(150, 210, 110))
    # 팻말
    d.rectangle((x + w // 2 - 1, y + h // 2, x + w // 2 + 1, y + h - 10), fill=K.WOOD[1], outline=INK)
    sw = 76; sx = x + (w - sw) // 2; sy = y + h // 2 - 26
    d.rectangle((sx, sy, sx + sw, sy + 30), fill=K.WOOD[3] if next_one else K.WOOD[2], outline=INK)
    d.line((sx + 1, sy + 1, sx + sw - 1, sy + 1), fill=K.WOOD[4])
    if next_one:
        text_mid(base, sx + sw / 2, sy + 9, '밭 넓히기', K.F_SMALL(), (255, 250, 236), K.WOOD[0])
        paste(base, K.icon('coin'), (sx + 18, sy + 16)); text_mid(base, sx + 46, sy + 22, f'{cost:,}', K.F_TITLE(), (255, 236, 150), K.WOOD[0])
    else:
        text_mid(base, sx + sw / 2, sy + 15, '잠김', K.F_BODY(), (236, 220, 200), K.WOOD[0])


def mmss(sec): return f'{sec // 60}:{sec % 60:02d}'


def fill_plants(base, x, y, w, im):
    """밭 한 칸을 6포기로 꽉 채움 (뒷줄 → 앞줄, 번갈아 좌우 뒤집기)"""
    ox = x + (w - 132) // 2
    for i, (dx, dy) in enumerate([(6, 14), (42, 12), (78, 14), (2, 46), (38, 48), (74, 46)]):
        g = im.transpose(Image.FLIP_LEFT_RIGHT) if i % 2 else im
        paste(base, g, (ox + dx, y + dy))


def plot_tile(base, x, y, w, h, crop, st, rem, sel=False, hover_seed=None):
    soil(base, x, y, w, h)
    if crop:
        fill_plants(base, x, y, w, plant(crop, st))
        if st == 'ripe':
            d = ImageDraw.Draw(base)
            for sx, sy in ((x + 18, y + 16), (x + w - 20, y + 22), (x + w - 30, y + 10)):
                d.line((sx - 3, sy, sx + 3, sy), fill=(255, 240, 140)); d.line((sx, sy - 3, sx, sy + 3), fill=(255, 240, 140)); d.point((sx, sy), fill=(255, 255, 255))
            cw = chip(base, x + 4, y + 4, '수확!', 'green')
        else:
            cw = chip(base, x + 4, y + 4, mmss(rem), 'brown')
            gauge(base, x + 6, y + h - 12, w - 12, 8, 600 - rem, 600, 'green')
    else:
        if hover_seed:                                                                        # 심을 자리 미리보기
            g = plant(hover_seed, 'sprout'); g.putalpha(g.getchannel('A').point(lambda v: v * 0.5))
            fill_plants(base, x, y, w, g)
        text_mid(base, x + w / 2, y + 16, '빈 밭', K.F_SMALL(), (236, 210, 180), (90, 56, 30))
    if sel: B.corners(base, x - 2, y - 2, x + w + 1, y + h + 1)


def field_grid(base, x0, y0, cw, ch, gap, sel=3, hover_seed=None):
    for i in range(6):
        x = x0 + (i % 3) * (cw + gap); y = y0 + (i // 3) * (ch + gap)
        if i < len(PLOTS):
            c, st, rem = PLOTS[i]; plot_tile(base, x, y, cw, ch, c, st, rem, i == sel, hover_seed if i == sel else None)
        else:
            locked(base, x, y, cw, ch, NEXT_COST, i == len(PLOTS))


def top(base, title='밭'):
    B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, title, 'red')


# ---------------- A: 밭 + 오른쪽 칸 ----------------
def farm_A(out):
    base = farm_bg(); top(base)
    B.card(base, 154, 32, 150, 22); paste(base, K.icon('sun'), (160, 37))
    text_mid(base, 233, 43, '심고 10분 · 수확 3개', K.F_BODY(), K.TEXT)
    field_grid(base, 14, 124, 132, 108, 12, sel=3, hover_seed='potato')
    B.panel(base, 444, 58, 188, 298)
    K.draw_text(base, (456, 76), '4번 밭 · 빈 밭', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (456, 92), '심을 씨앗 선택', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, (k, n, own) in enumerate(CROPS):
        x = 456 + (i % 2) * 86; y = 102 + (i // 2) * 52
        B.card(base, x, y, 82, 48, i == 0)
        ic = FI.seed_bag(k).resize((32, 32), Image.NEAREST)
        if not own: ic.putalpha(ic.getchannel('A').point(lambda v: v * 0.45))
        paste(base, ic, (x + 4, y + 8))
        K.draw_text(base, (x + 40, y + 16), n, K.F_BODY(), K.TEXT if own else K.TEXT_SOFT, 'lm')
        K.draw_text(base, (x + 40, y + 32), f'보유 {own}', K.F_SMALL(), K.TEXT_SOFT if own else RED, 'lm')
    K.draw_text(base, (456, 270), '씨앗 1개 → 감자 3개', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (456, 284), '씨앗은 상점에서 10코인', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 456, 300, 164, 40, '감자 심기', 'green', icon='heart', sub='10분 뒤 수확')
    save(base, out)


def farm_A_ready(out):
    """A안: 다 자란 밭을 고른 모습"""
    base = farm_bg(); top(base)
    B.card(base, 154, 32, 150, 22); paste(base, K.icon('sun'), (160, 37))
    text_mid(base, 233, 43, '심고 10분 · 수확 3개', K.F_BODY(), K.TEXT)
    field_grid(base, 14, 124, 132, 108, 12, sel=0)
    B.panel(base, 444, 58, 188, 298)
    K.draw_text(base, (456, 76), '1번 밭 · 토마토', K.F_TITLE(), K.TEXT, 'lm')
    chip(base, 456, 86, '수확 가능', 'green')
    d = ImageDraw.Draw(base); d.rectangle((456, 110, 620, 196), fill=(150, 98, 60), outline=INK)
    paste(base, FI.RIPE['tomato']().resize((72, 72), Image.NEAREST), (502, 118))
    K.draw_text(base, (456, 214), '받는 것', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    paste(base, crop_icon('tomato').resize((32, 32), Image.NEAREST), (456, 222))
    K.draw_text(base, (494, 238), '토마토 ×3', K.F_BIG(), K.TEXT, 'lm')
    K.draw_text(base, (456, 270), '가방 보유 2 → 5', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (456, 284), '수확하면 빈 밭이 됨', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 456, 300, 164, 40, '수확하기', 'orange', icon='heart', sub='토마토 3개')
    save(base, out)


# ---------------- B: 밭 크게 + 아래 씨앗 줄 ----------------
def farm_B(out):
    base = farm_bg(); top(base)
    button(base, 516, 32, 116, 22, '모두 수확', 'orange', icon='heart', f=K.F_BODY())
    field_grid(base, 26, 122, 186, 82, 10, sel=3, hover_seed='potato')
    # 아래 씨앗 줄 (도구 칸처럼)
    B.panel(base, 8, 302, 624, 54)
    K.draw_text(base, (20, 320), '씨앗', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (20, 336), '골라서 밭 클릭', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, (k, n, own) in enumerate(CROPS):
        x = 104 + i * 76; y = 308
        B.card(base, x, y, 72, 42, i == 0)
        ic = FI.seed_bag(k).resize((32, 32), Image.NEAREST)
        if not own: ic.putalpha(ic.getchannel('A').point(lambda v: v * 0.45))
        paste(base, ic, (x + 4, y + 5))
        K.draw_text(base, (x + 40, y + 14), n, K.F_SMALL(), K.TEXT if own else K.TEXT_SOFT, 'lm')
        K.draw_text(base, (x + 40, y + 29), f'×{own}', K.F_TITLE(), K.TEXT if own else RED, 'lm')
    B.corners(base, 104, 308, 175, 349)
    save(base, out)


# ---------------- C: 목록 ----------------
def farm_C(out):
    base = farm_bg(dim=True); top(base)
    B.panel(base, 8, 58, 624, 298)
    K.draw_text(base, (22, 76), '내 밭 4 / 6', K.F_TITLE(), K.TEXT, 'lm')
    rows = PLOTS + [None, None]
    for i, p in enumerate(rows):
        y = 88 + i * 44
        B.card(base, 18, y, 604, 40, i == 3)
        d = ImageDraw.Draw(base); d.rectangle((24, y + 4, 64, y + 35), fill=(150, 98, 60), outline=INK)
        K.draw_text(base, (74, y + 20), f'{i + 1}번', K.F_BODY(), K.TEXT_SOFT, 'lm')
        if p is None:
            text_mid(base, 44, y + 20, '잠김', K.F_SMALL(), (236, 210, 180))
            if i == 4:
                K.draw_text(base, (110, y + 20), '밭 넓히기', K.F_TITLE(), K.TEXT, 'lm')
                button(base, 520, y + 9, 94, 22, '900', 'orange', icon='coin', f=K.F_BODY())
            else: K.draw_text(base, (110, y + 20), '앞 밭을 먼저 넓혀야 함', K.F_SMALL(), K.TEXT_SOFT, 'lm')
            continue
        c, st, rem = p
        if c: paste(base, (FI.RIPE[c]() if st == 'ripe' else FI.STAGES[st]()), (32, y + 6))
        if c is None:
            K.draw_text(base, (110, y + 20), '빈 밭', K.F_TITLE(), K.TEXT_SOFT, 'lm')
            button(base, 520, y + 9, 94, 22, '심기', 'green', icon='heart', f=K.F_BODY())
        else:
            K.draw_text(base, (110, y + 20), NAME[c], K.F_TITLE(), K.TEXT, 'lm')
            if st == 'ripe':
                chip(base, 170, y + 12, '수확 가능', 'green')
                button(base, 520, y + 9, 94, 22, '수확', 'orange', icon='heart', f=K.F_BODY())
            else:
                gauge(base, 170, y + 15, 250, 10, 600 - rem, 600, 'green')
                K.draw_text(base, (430, y + 20), f'남은 시간 {mmss(rem)}', K.F_SMALL(), K.TEXT, 'lm')
    save(base, out)


# ---------------- 수확 결과 (알림 대신 짧은 연출) ----------------
def harvest_pop(out):
    base = farm_bg(); top(base)
    field_grid(base, 14, 124, 132, 108, 12, sel=0)
    d = ImageDraw.Draw(base)
    soil(base, 14, 124, 132, 108)                                    # 수확 뒤 빈 밭
    for i, (dx, dy) in enumerate(((-18, -30), (2, -42), (22, -28))):  # 튀어 오르는 토마토 3개
        paste(base, crop_icon('tomato').resize((32, 32), Image.NEAREST), (64 + dx, 168 + dy))
    B.card(base, 40, 92, 82, 22); text_mid(base, 81, 103, '토마토 +3', K.F_TITLE(), GREEN)
    B.panel(base, 444, 58, 188, 298)
    K.draw_text(base, (456, 76), '1번 밭 · 빈 밭', K.F_TITLE(), K.TEXT, 'lm')
    save(base, out)


def farm_all(out):
    """6칸 모두 다 자란 모습 (작물 6종 확인용)"""
    global PLOTS
    keep = PLOTS
    PLOTS = [(k, 'ripe', 0) for k in ('tomato', 'cabbage', 'wheat', 'potato', 'rice', 'onion')]
    base = farm_bg(); top(base)
    button(base, 154, 32, 116, 22, '모두 수확', 'orange', icon='heart', f=K.F_BODY())
    field_grid(base, 14, 124, 132, 108, 12, sel=1)
    B.panel(base, 444, 58, 188, 298)
    K.draw_text(base, (456, 76), '2번 밭 · 양배추', K.F_TITLE(), K.TEXT, 'lm')
    chip(base, 456, 86, '수확 가능', 'green')
    d = ImageDraw.Draw(base); d.rectangle((456, 110, 620, 196), fill=(132, 84, 50), outline=INK)
    paste(base, FI.RIPE['cabbage']().resize((72, 72), Image.NEAREST), (502, 118))
    K.draw_text(base, (456, 214), '받는 것', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    paste(base, crop_icon('cabbage').resize((32, 32), Image.NEAREST), (456, 222))
    K.draw_text(base, (494, 238), '양배추 ×3', K.F_BIG(), K.TEXT, 'lm')
    K.draw_text(base, (456, 270), '가방 보유 0 → 3', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (456, 284), '수확하면 빈 밭이 됨', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 456, 300, 164, 40, '수확하기', 'orange', icon='heart', sub='양배추 3개')
    save(base, out); PLOTS = keep


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    farm_A(out / 'farm_A_field.png'); farm_A_ready(out / 'farm_A2_ready.png'); farm_B(out / 'farm_B_hotbar.png'); farm_C(out / 'farm_C_list.png'); farm_all(out / 'farm_A3_all_ripe.png')
    print('ok')
