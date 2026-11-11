"""사냥터 후보 A(구역 지도 + 오른쪽 칸) / B(구역 카드 4장)."""
import sys, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
import food_icons as F
import hunt_art as HA
from ui_mock import paste, button, gauge, chip, ribbon, text_mid

W, H = 640, 360
INK = K.INK
RED = K.BTN['red'][1]; GREEN = K.BTN['green'][1]
AREAS = [('chicken_coop', '닭장', 30, 'chicken', '닭고기'), ('pig_pen', '돼지우리', 30, 'pork', '돼지고기'),
         ('ranch', '목장', 30, 'beef', '소고기'), ('rabbit_hill', '달토끼 언덕', 60, 'lucky_rabbit', '행운의 토끼고기')]
# 지금 상태: 닭장 = 불씨여우 12:40 남음, 돼지우리 = 물방울수달 다 옴, 목장·언덕 비어 있음
STATE = {'chicken_coop': ('dealer_normal_01', 760, 1800), 'pig_pen': ('tank_normal_01', 0, 1800)}


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


import meat_icons as MI
import hunt_zone2 as Z2


def meat(k):
    if k in MI.MEATS: return MI.MEATS[k]()
    return Image.open(f'/home/claude/evotail_project/assets/food/{k}.png').convert('RGBA').resize((16, 16), Image.NEAREST)


def mmss(s): return f'{s // 60}:{s % 60:02d}'


def critter(k, n=1, flip=False):
    im = HA.CRITTERS[k]().resize((28 * n, 28 * n), Image.NEAREST)
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


# ---------------- 구역 그림 (코드 도트) ----------------
def fence(d, x0, y0, x1, c=(232, 196, 136)):
    for y in (y0 + 3, y0 + 8):
        d.rectangle((x0, y, x1, y + 2), fill=c, outline=INK)
    for x in range(x0, x1, 14):
        d.rectangle((x, y0, x + 3, y0 + 14), fill=c, outline=INK); d.point((x + 1, y0 + 1), fill=(255, 240, 200))


def zone(key, w, h, t=0):
    im = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(im)
    if key == 'rabbit_hill':                                    # 밤 언덕 + 큰 달
        for i, c in enumerate([(44, 40, 96), (60, 52, 120), (80, 68, 146)]):
            d.rectangle((0, i * h // 6, w, h), fill=c)
        for x, y in ((20, 14), (60, 30), (150, 10), (190, 40), (110, 22), (30, 60)):
            d.point((x % w, y), fill=(255, 250, 220)); d.point((x % w + 1, y), fill=(200, 200, 255))
        d.ellipse((w - 70, 10, w - 22, 58), fill=(255, 246, 200), outline=(220, 200, 140))
        d.ellipse((w - 58, 22, w - 50, 30), fill=(240, 226, 170)); d.ellipse((w - 40, 36, w - 34, 42), fill=(240, 226, 170))
        d.ellipse((-40, h * .45, w * .7, h * 1.5), fill=(120, 150, 200)); d.ellipse((w * .3, h * .55, w + 40, h * 1.6), fill=(106, 136, 188))
        for x, y in ((40, 90), (100, 110), (160, 96)): d.ellipse((x, y, x + 6, y + 4), fill=(255, 240, 160))   # 빛 꽃
    else:
        sky = {'chicken_coop': (190, 232, 250), 'pig_pen': (200, 230, 248), 'ranch': (180, 226, 252)}[key]
        d.rectangle((0, 0, w, h), fill=sky)
        ground = {'chicken_coop': (150, 206, 106), 'pig_pen': (150, 200, 100), 'ranch': (132, 200, 100)}[key]
        d.rectangle((0, 34, w, h), fill=ground)
        for y in range(40, h, 6):
            for x in range((y * 7) % 11, w, 11): d.point((x, y), fill=tuple(int(c * .88) for c in ground))
        if key == 'chicken_coop':                                # 닭장 오두막 + 경사 사다리
            d.polygon([(12, 28), (36, 12), (60, 28)], fill=(200, 70, 60), outline=INK)
            d.rectangle((16, 28, 56, 58), fill=(236, 210, 160), outline=INK)
            d.rectangle((30, 40, 42, 58), fill=(110, 70, 44), outline=INK)
            d.polygon([(42, 58), (60, 70), (64, 68), (46, 56)], fill=(200, 160, 110), outline=INK)
            for x in range(80, w, 26): d.ellipse((x, 70 + (x % 3) * 6, x + 4, 73 + (x % 3) * 6), fill=(250, 220, 120))   # 모이
        elif key == 'pig_pen':                                   # 진흙탕
            d.ellipse((30, 54, w - 30, h - 8), fill=(150, 108, 72), outline=(110, 76, 48))
            d.ellipse((50, 62, w - 60, h - 20), fill=(132, 92, 60))
            d.ellipse((70, 66, 100, 72), fill=(176, 136, 96))
            d.rectangle((w - 50, 14, w - 10, 34), fill=(214, 170, 110), outline=INK); d.line((w - 46, 24, w - 14, 24), fill=(170, 120, 70))  # 여물통
        else:                                                    # 목장: 언덕 + 건초 + 나무
            d.ellipse((-30, 20, w * .6, 70), fill=(150, 214, 116)); d.rectangle((0, 46, w, h), fill=ground)
            for x in (w - 54, w - 34):
                d.rounded_rectangle((x, 30, x + 18, 46), 3, fill=(240, 204, 100), outline=INK)
                d.line((x + 2, 35, x + 16, 35), fill=(204, 160, 60)); d.line((x + 2, 40, x + 16, 40), fill=(204, 160, 60))
        fence(d, 0, h - 18, w)
    return im


# ---------------- A: 4구역 지도 + 오른쪽 칸 ----------------
def top(base):
    B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 80, '사냥터', 'red')


def hunt_bg():
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 26, W, H), fill=(86, 128, 70))
    for y in range(30, H, 5):
        for x in range((y * 5) % 9, W, 9): d.point((x, y), fill=(76, 116, 62))
    return im


def zone_tile(base, key, x, y, w, h, sel):
    name = dict((a[0], a[1]) for a in AREAS)[key]
    mins = dict((a[0], a[2]) for a in AREAS)[key]
    z = Z2.zone(key, w - 4, h - 4)
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w - 1, y + h - 1), fill=K.WOOD[2], outline=INK)
    paste(base, z, (x + 2, y + 2))
    d.rectangle((x + 2, y + 2, x + w - 3, y + h - 3), outline=K.WOOD[0])
    # 사냥감 2마리 + 보낸 동물: 자리는 Z2.SPOTS (보낸 동물 자리는 배경에 소품 없음)
    for i, (cx, cy) in enumerate(Z2.SPOTS['critters'][key]):
        paste(base, critter(key, 2, i % 2 == 1), (x + 2 + cx - 28, y + 2 + cy - 28))
    # 간판
    sw = int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(f'{name} · {mins}분', font=K.F_BODY())) + 14
    d.rectangle((x + 6, y + 6, x + 6 + sw, y + 24), fill=K.WOOD[3], outline=INK); d.line((x + 7, y + 7, x + 5 + sw, y + 7), fill=K.WOOD[4])
    text_mid(base, x + 6 + sw / 2 + .5, y + 15, f'{name} · {mins}분', K.F_BODY(), (255, 250, 236), K.WOOD[0])
    st = STATE.get(key)
    if st:
        aid, rem, dur = st
        ax, ay = x + 2 + Z2.SPOTS['animal'][0], y + 2 + Z2.SPOTS['animal'][1] - 28
        paste(base, B.spr(aid, 1, 2), (ax, ay))
        if rem:
            chip(base, x + 2 + Z2.SPOTS['chip'][0], y + 2 + Z2.SPOTS['chip'][1], f'남은 {mmss(rem)}', 'brown')
            gauge(base, x + 8, y + h - 24, w - 16, 8, dur - rem, dur, 'green')
        else:
            chip(base, x + 2 + Z2.SPOTS['chip'][0], y + 2 + Z2.SPOTS['chip'][1], '사냥 완료!', 'green')
            item = dict((a_[0], a_[3]) for a_ in AREAS)[key]                      # 말풍선: 고기 ×3
            bx, by = ax + 6, ay - 22
            B.card(base, bx, by, 46, 22); dd = ImageDraw.Draw(base)
            dd.polygon([(bx + 18, by + 21), (bx + 26, by + 21), (bx + 22, by + 26)], fill=(250, 240, 220), outline=INK)
            paste(base, meat(item), (bx + 4, by + 3)); text_mid(base, bx + 33, by + 11, '×3', K.F_TITLE(), K.TEXT)
    if sel: B.corners(base, x - 2, y - 2, x + w + 1, y + h + 1)


def hunt_A(out, sel='ranch'):
    base = hunt_bg(); top(base)
    t = '사냥터마다 1마리씩'; tw = int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(t, font=K.F_BODY()))
    B.card(base, 168, 32, tw + 30, 22); paste(base, K.icon('heart'), (174, 37))
    text_mid(base, 190 + tw / 2, 43, t, K.F_BODY(), K.TEXT)
    pos = [(10, 60), (226, 60), (10, 210), (226, 210)]
    for (key, *_), (x, y) in zip(AREAS, pos): zone_tile(base, key, x, y, 212, 144, key == sel)
    B.panel(base, 444, 58, 188, 298)
    if sel == 'ranch': panel_empty(base)
    elif sel == 'pig_pen': panel_ready(base)
    else: panel_running(base)
    save(base, out)


def effects(base, x, y, long=False):
    K.draw_text(base, (x, y), '다녀오면', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    a = ('포만감 -20 · 기분 -10', '피로도 +35 · 질병 30%') if long else ('포만감 -10 · 기분 -5', '피로도 +20 · 질병 30%')
    K.draw_text(base, (x, y + 14), a[0], K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (x, y + 28), a[1], K.F_SMALL(), RED, 'lm')


def panel_empty(base):
    K.draw_text(base, (456, 76), '목장', K.F_BIG(), K.TEXT, 'lm'); chip(base, 492, 68, '30분', 'brown')
    K.draw_text(base, (456, 98), '받는 것', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    paste(base, meat('beef').resize((32, 32), Image.NEAREST), (456, 104))
    K.draw_text(base, (494, 120), '소고기 ×3', K.F_BIG(), K.TEXT, 'lm')
    effects(base, 456, 148)
    K.draw_text(base, (456, 192), '보낼 동물', K.F_TITLE(), K.TEXT, 'lm')
    rows = [('healer_normal_01', '산들오리', '보낼 수 있음', True, True), ('dealer_normal_01', '불씨여우', '사냥 중 · 닭장', False, False),
            ('tank_normal_01', '물방울수달', '사냥 중 · 돼지우리', False, False)]
    for i, (aid, n, sub, ok, sel) in enumerate(rows):
        y = 200 + i * 33
        B.card(base, 456, y, 164, 31, sel)
        sp = B.spr(aid, 1, 1)
        if not ok: sp = ImageEnhance.Brightness(ImageEnhance.Color(sp).enhance(0)).enhance(1.1)
        paste(base, sp, (458, y + 2))
        K.draw_text(base, (488, y + 10), n, K.F_BODY(), K.TEXT if ok else K.TEXT_SOFT, 'lm')
        K.draw_text(base, (488, y + 23), sub, K.F_SMALL(), GREEN if ok else K.TEXT_SOFT, 'lm')
    button(base, 456, 302, 164, 40, '산들오리 보내기', 'green', icon='heart', sub='30분 뒤 소고기 3개')


def panel_ready(base):
    K.draw_text(base, (456, 76), '돼지우리', K.F_BIG(), K.TEXT, 'lm'); chip(base, 516, 68, '사냥 완료', 'green')
    d = ImageDraw.Draw(base); d.rectangle((456, 92, 620, 170), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, B.spr('tank_normal_01', 1, 2), (470, 104))
    for i in range(3): paste(base, meat('pork').resize((32, 32), Image.NEAREST), (532 + i * 26 - (i == 1) * 0, 110 + (i == 1) * -10))
    K.draw_text(base, (456, 186), '물방울수달 귀환', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (456, 202), '돼지고기 ×3 · 가방 보유 1 → 4', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (456, 224), '지금 상태', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (456, 238), '피로도', K.F_SMALL(), K.TEXT, 'lm'); K.draw_text(base, (620, 238), '40 보통', K.F_SMALL(), K.BTN['orange'][1], 'rm')
    gauge(base, 456, 246, 164, 8, 40, 100, 'orange')
    K.draw_text(base, (456, 270), '포만감', K.F_SMALL(), K.TEXT, 'lm'); K.draw_text(base, (620, 270), '70 좋음', K.F_SMALL(), GREEN, 'rm')
    gauge(base, 456, 278, 164, 8, 70, 100, 'green')
    button(base, 456, 300, 164, 40, '보상 받기', 'orange', icon='heart', sub='돼지고기 3개')


def panel_running(base):
    K.draw_text(base, (456, 76), '닭장', K.F_BIG(), K.TEXT, 'lm'); chip(base, 492, 68, '사냥 중', 'brown')
    d = ImageDraw.Draw(base); d.rectangle((456, 92, 620, 170), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, B.spr('dealer_normal_01', 1, 2), (508, 100))
    K.draw_text(base, (456, 186), '불씨여우 사냥 중', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (456, 206), '남은 시간', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (456, 222), '12:40', K.F_BIG(), K.TEXT, 'lm')
    gauge(base, 456, 234, 164, 10, 1040, 1800, 'green')
    paste(base, meat('chicken'), (456, 254)); K.draw_text(base, (476, 262), '다녀오면 닭고기 ×3', K.F_SMALL(), K.TEXT, 'lm')
    button(base, 456, 300, 164, 40, '불러오기', 'brown', icon='back', sub='보상 없음')


# ---------------- B: 구역 카드 4장 + 아래 동물 줄 ----------------
def hunt_B(out):
    base = hunt_bg(); top(base)
    for i, (key, name, mins, item, iname) in enumerate(AREAS):
        x = 8 + i * 158; y = 58
        B.panel(base, x, y, 152, 220)
        z = Z2.zone(key, 208, 140).crop((0, 30, 136, 126)) if key != 'rabbit_hill' else Z2.zone(key, 208, 140).crop((72, 6, 208, 102)); d = ImageDraw.Draw(base)
        d.rectangle((x + 7, y + 9, x + 144, y + 106), outline=INK); paste(base, z, (x + 8, y + 10))
        paste(base, critter(key, 2), (x + 28, y + 40)); paste(base, critter(key, 2, True), (x + 74, y + 46))
        K.draw_text(base, (x + 10, y + 120), name, K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (x + 142, y + 120), f'{mins}분', K.F_SMALL(), K.TEXT_SOFT, 'rm')
        paste(base, meat(item), (x + 10, y + 130)); K.draw_text(base, (x + 30, y + 138), f'{iname} ×3', K.F_SMALL(), K.TEXT, 'lm')
        st = STATE.get(key)
        if st and st[1]:
            paste(base, B.spr(st[0], 1, 1), (x + 10, y + 150)); K.draw_text(base, (x + 42, y + 164), f'남은 {mmss(st[1])}', K.F_BODY(), K.TEXT, 'lm')
            gauge(base, x + 10, y + 182, 132, 8, st[2] - st[1], st[2], 'green')
            button(base, x + 10, y + 194, 132, 20, '불러오기', 'brown', f=K.F_BODY())
        elif st:
            paste(base, B.spr(st[0], 1, 1), (x + 10, y + 150)); chip(base, x + 42, y + 156, '사냥 완료!', 'green')
            button(base, x + 10, y + 194, 132, 20, '보상 받기', 'orange', icon='heart', f=K.F_BODY())
        else:
            K.draw_text(base, (x + 10, y + 166), '비어 있음', K.F_BODY(), K.TEXT_SOFT, 'lm')
            button(base, x + 10, y + 194, 132, 20, '여기로 보내기', 'green', icon='heart', f=K.F_BODY())
        if key == 'ranch': B.corners(base, x - 2, y - 2, x + 153, y + 221)
    B.panel(base, 8, 284, 624, 72)
    K.draw_text(base, (20, 300), '보낼 동물', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (20, 316), '고른 뒤 사냥터 선택', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    rows = [('healer_normal_01', '산들오리', '보낼 수 있음', True), ('dealer_normal_01', '불씨여우', '사냥 중', False),
            ('tank_normal_01', '물방울수달', '사냥 완료', False), ('dealer_normal_02', '불씨다람쥐', '아픔', False)]
    for i, (aid, n, sub, ok) in enumerate(rows):
        x = 140 + i * 122
        B.card(base, x, 292, 118, 56, i == 0)
        sp = B.spr(aid, 1, 1)
        if not ok: sp = ImageEnhance.Brightness(ImageEnhance.Color(sp).enhance(0)).enhance(1.1)
        paste(base, sp, (x + 4, 306))
        K.draw_text(base, (x + 36, 312), n, K.F_BODY(), K.TEXT if ok else K.TEXT_SOFT, 'lm')
        K.draw_text(base, (x + 36, 328), sub, K.F_SMALL(), GREEN if ok else RED, 'lm')
    save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    hunt_A(out / 'hunt_A1_send.png', 'ranch'); hunt_A(out / 'hunt_A2_ready.png', 'pig_pen'); hunt_A(out / 'hunt_A3_running.png', 'chicken_coop')
    hunt_B(out / 'hunt_B_cards.png')
    print('ok')


# ================= 사냥 중 / 귀환 칸 v2 (풍경 무대 + 연출) =================
def stage_box(base, key, x, y, w, h, dim=1.0):
    z = Z2.zone(key, 208, 140)
    cx = {'rabbit_hill': 40, 'chicken_coop': 30, 'pig_pen': 20, 'ranch': 30}[key]
    crop = z.crop((cx, 140 - h - 18, cx + w, 140 - 18))
    if dim != 1.0: crop = ImageEnhance.Brightness(crop).enhance(dim)
    d = ImageDraw.Draw(base); d.rectangle((x - 1, y - 1, x + w, y + h), outline=INK)
    paste(base, crop, (x, y))


def dust(d, x, y):
    for dx, dy, r in ((0, 0, 3), (-6, 2, 2), (-11, 1, 1)):
        d.ellipse((x + dx - r, y + dy - r, x + dx + r, y + dy + r), fill=(250, 244, 230), outline=(200, 186, 160))


def panel_running2(base, key='rabbit_hill', aid='healer_normal_01', name='산들오리', rem=2400, dur=3600, item='lucky_rabbit', iname='행운의 토끼고기'):
    label = dict((a[0], a[1]) for a in AREAS)[key]
    K.draw_text(base, (456, 76), label, K.F_BIG(), K.TEXT, 'lm')
    chip(base, 456 + int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(label, font=K.F_BIG())) + 6, 68, '사냥 중', 'brown')
    stage_box(base, key, 457, 92, 162, 84)
    d = ImageDraw.Draw(base)
    paste(base, critter(key, 2), (546, 118))                                         # 도망가는 사냥감
    for i in range(3): d.line((542 - i * 3, 132 + i * 5, 536 - i * 3, 132 + i * 5), fill=(255, 255, 255))
    paste(base, B.spr(aid, 1, 2).transpose(Image.FLIP_LEFT_RIGHT), (476, 118))       # 쫓아가는 내 동물
    dust(d, 482, 170)
    B.card(base, 498, 98, 22, 20); text_mid(base, 509, 108, '!', K.F_TITLE(), RED)    # 느낌표 말풍선
    # 진행 길: 출발 깃발 → 발자국 → 내 동물 → 도착(고기)
    K.draw_text(base, (456, 192), f'{name} 사냥 중', K.F_TITLE(), K.TEXT, 'lm')
    y = 214; x0, x1 = 462, 600
    d.line((x0, y, x1, y), fill=K.WOOD[1], width=3)
    p = (dur - rem) / dur; px = int(x0 + (x1 - x0) * p)
    for fx in range(x0 + 6, px - 8, 9): d.point([(fx, y - 4), (fx + 2, y - 5)], fill=K.WOOD[0])          # 발자국
    d.rectangle((x0 - 3, y - 10, x0 - 2, y + 1), fill=INK); d.polygon([(x0 - 2, y - 10), (x0 + 5, y - 8), (x0 - 2, y - 6)], fill=GREEN)
    paste(base, meat(item), (x1 - 2, y - 14))
    paste(base, B.spr(aid, 1, 1).transpose(Image.FLIP_LEFT_RIGHT).crop((2, 2, 26, 26)), (px - 12, y - 22))
    K.draw_text(base, (456, 236), '남은 시간', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (620, 236), mmss(rem), K.F_BIG(), K.TEXT, 'rm')
    paste(base, meat(item), (456, 252)); K.draw_text(base, (476, 260), f'다녀오면 {iname} ×3', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (456, 280), '다녀오면 피로도 +35 · 질병 30%', K.F_SMALL(), RED, 'lm')
    button(base, 456, 302, 164, 40, '불러오기', 'brown', icon='back', sub='보상 없음')


def panel_ready2(base, key='rabbit_hill', aid='healer_normal_01', name='산들오리', item='lucky_rabbit', iname='행운의 토끼고기', sick=False):
    label = dict((a[0], a[1]) for a in AREAS)[key]
    K.draw_text(base, (456, 76), label, K.F_BIG(), K.TEXT, 'lm')
    chip(base, 456 + int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(label, font=K.F_BIG())) + 6, 68, '사냥 완료', 'green')
    stage_box(base, key, 457, 92, 162, 84)
    st = Image.new('RGBA', (W, H)); rays_c = (255, 240, 170)
    sd = ImageDraw.Draw(st)
    for i in range(12):
        a = i * math.pi / 6
        sd.polygon([(538, 150), (538 + 120 * math.cos(a), 150 + 120 * math.sin(a)), (538 + 120 * math.cos(a + .2), 150 + 120 * math.sin(a + .2))], fill=rays_c + (70,))
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).rectangle((457, 92, 618, 175), fill=255)
    sc = Image.new('RGBA', (W, H)); sc.paste(st, (0, 0), m); base.alpha_composite(sc)
    d = ImageDraw.Draw(base)
    # 바구니 + 고기 3개
    for i, (dx, dy) in enumerate(((0, 0), (14, -6), (28, 0))):
        paste(base, meat(item).resize((32, 32), Image.NEAREST), (532 + dx, 128 + dy))
    d.rounded_rectangle((534, 152, 592, 170), 3, fill=(206, 152, 88), outline=INK)                  # 바구니
    for xx in range(540, 590, 6): d.line((xx, 153, xx, 169), fill=(170, 116, 60))
    d.line((535, 156, 591, 156), fill=(232, 186, 120))
    paste(base, B.spr(aid, 1, 2), (474, 118))
    for sx, sy in ((470, 112), (528, 104), (604, 110), (600, 140)):
        d.line((sx - 3, sy, sx + 3, sy), fill=(255, 236, 120)); d.line((sx, sy - 3, sx, sy + 3), fill=(255, 236, 120)); d.point((sx, sy), fill=(255, 255, 255))
    ribbon(base, 474, 86, 64, '귀환!', 'green')
    K.draw_text(base, (456, 192), f'{name} 귀환', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (456, 208), f'{iname} ×3', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (620, 208), '가방 1 → 4', K.F_SMALL(), GREEN, 'rm')
    K.draw_text(base, (456, 226), '다녀온 결과', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    cx = 456
    for t, c in (('피로도 +35', 'orange'), ('포만감 -20', 'orange')):
        cx += chip(base, cx, 234, t, c) + 3
    cx = 456 + chip(base, 456, 254, '기분 -10', 'orange') + 3
    if sick: chip(base, cx, 254, '아픔 · 병원 치료', 'red')
    else: chip(base, cx, 254, '건강함', 'green')
    K.draw_text(base, (456, 286), '지금 피로도 35 보통', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 456, 302, 164, 40, '보상 받기', 'orange', icon='heart', sub=f'{iname} 3개')


def hunt_v2(out_run, out_ready, out_sick):
    global STATE
    keep = STATE
    STATE = {'rabbit_hill': ('healer_normal_01', 2400, 3600)}
    base = hunt_bg(); top(base)
    t = '사냥터마다 1마리씩'; tw = int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength(t, font=K.F_BODY()))
    B.card(base, 168, 32, tw + 30, 22); paste(base, K.icon('heart'), (174, 37)); text_mid(base, 190 + tw / 2, 43, t, K.F_BODY(), K.TEXT)
    pos = [(10, 60), (226, 60), (10, 210), (226, 210)]
    for (key, *_), (x, y) in zip(AREAS, pos): zone_tile(base, key, x, y, 212, 144, key == 'rabbit_hill')
    B.panel(base, 444, 58, 188, 298); panel_running2(base); save(base, out_run)
    STATE = {'rabbit_hill': ('healer_normal_01', 0, 3600)}
    for out, sick in ((out_ready, False), (out_sick, True)):
        base = hunt_bg(); top(base)
        B.card(base, 168, 32, tw + 30, 22); paste(base, K.icon('heart'), (174, 37)); text_mid(base, 190 + tw / 2, 43, t, K.F_BODY(), K.TEXT)
        for (key, *_), (x, y) in zip(AREAS, pos): zone_tile(base, key, x, y, 212, 144, key == 'rabbit_hill')
        B.panel(base, 444, 58, 188, 298); panel_ready2(base, sick=sick); save(base, out)
    STATE = keep
