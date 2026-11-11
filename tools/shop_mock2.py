"""상점 A(확정) 게임 말투 + 알 부화 연출 + 병원 후보 3개."""
import sys, math, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
import shop_icons as S
from ui_mock import paste, button, gauge, chip, ribbon, text_mid
import hosp_room as HR
from shop_mock import shop_bg, ic, price, save, W, H, INK

K.BTN.setdefault('gold', [(104, 62, 10), (184, 120, 24), (232, 170, 36), (255, 220, 110)])
RED = K.BTN['red'][1]; GREEN = K.BTN['green'][1]
STATS = [('hp', '체력', 'heart', 'red'), ('attack', '공격력', 'sword', 'orange'),
         ('defense', '방어력', 'shield', 'blue'), ('agility', '민첩성', 'wing', 'green')]
CATS = [('먹이·장난감', 'snack'), ('회복·포션', 'heal_basic'), ('장비', 'equip_claw'), ('알', 'egg_special'), ('재료·씨앗', 'seed'), ('팔기', 'toy_ball')]


def tl(t, f): return ImageDraw.Draw(Image.new('L', (1, 1))).textlength(t, font=f)


# ================= 상점 A =================
def shop_frame(tab):
    base = shop_bg(dim=True); B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '상점', 'red')
    B.panel(base, 8, 58, 112, 298)
    for i, (t, k) in enumerate(CATS):
        y = 68 + i * 46; on = i == tab
        B.card(base, 16, y, 96, 40, on)
        paste(base, ic(k, 1), (22, y + 12))
        K.draw_text(base, (42, y + 20), t, K.F_TITLE() if on else K.F_BODY(), K.TEXT if i < 5 else RED, 'lm')
    B.panel(base, 124, 58, 304, 298); B.panel(base, 432, 58, 200, 298)
    return base


def grid(base, items, sel):
    """items: (key, 이름 줄 목록, 가격, 보유)"""
    for i, (k, lines, p, own) in enumerate(items):
        col, row = i % 3, i // 3
        x = 134 + col * 96; y = 68 + row * 92
        B.card(base, x, y, 92, 88, k == sel)
        paste(base, ic(k, 2), (x + 30, y + 6))
        for j, ln in enumerate(lines): K.draw_text(base, (x + 46, y + 47 + j * 12), ln, K.F_SMALL(), K.TEXT, 'mm')
        price(base, x + 46 - (14 + tl(f'{p:,}', K.F_TITLE())) / 2, y + 76, p)
        if own: chip(base, x + 58, y + 26, f'×{own}', 'gray')
    if sel: B.corners(base, *[(134 + (i % 3) * 96, 68 + (i // 3) * 92, 134 + (i % 3) * 96 + 91, 68 + (i // 3) * 92 + 87) for i, it in enumerate(items) if it[0] == sel][0])


def detail(base, key, name, tag, tagc, lines, own, qty, unit, buy='구매'):
    d = ImageDraw.Draw(base)
    d.rectangle((446, 72, 618, 136), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, ic(key, 3), (508, 80))
    K.draw_text(base, (446, 152), name, K.F_BIG(), K.TEXT, 'lm')
    chip(base, 446, 164, tag, tagc)
    y = 190
    for ln in lines:
        if isinstance(ln, tuple):           # (아이콘, 글, 색)
            paste(base, K.icon(ln[0]), (446, y - 6)); K.draw_text(base, (462, y), ln[1], K.F_BODY(), ln[2], 'lm')
        else: K.draw_text(base, (446, y), ln, K.F_SMALL(), K.TEXT, 'lm')
        y += 15
    K.draw_text(base, (446, 254), f'보유 {own}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 446, 268, 22, 20, '-', 'brown', f=K.F_TITLE())
    B.card(base, 470, 268, 36, 20); K.draw_text(base, (488, 278), str(qty), K.F_TITLE(), K.TEXT, 'mm')
    button(base, 508, 268, 22, 20, '+', 'brown', f=K.F_TITLE())
    price(base, 618, 278, qty * unit, 'rm')
    button(base, 446, 300, 172, 40, buy, 'orange', icon='coin', sub=f'{qty}개 · {qty * unit:,}코인')


def shop_potion(out):
    base = shop_frame(1)
    items = [('heal_basic', ['기본 회복', '포션'], 40, 2), ('heal_advanced', ['고급 회복', '포션'], 80, 0),
             ('potion_attack', ['공격력 포션'], 150, 1), ('potion_defense', ['방어력 포션'], 130, 0),
             ('potion_hp', ['체력 포션'], 120, 0), ('potion_agility', ['민첩성 포션'], 100, 0), ('battle_bandage', ['전투 응급', '붕대'], 80, 2)]
    grid(base, items, 'heal_advanced')
    detail(base, 'heal_advanced', '고급 회복 포션', '치료', 'green',
           [('heart', '질병 치료 확률 90%', K.TEXT), ('zzz', '피로도 -30', K.TEXT), '병원에서 사용'], 0, 2, 80)
    save(base, out)


def shop_equip(out):
    base = shop_frame(2)
    items = [('equip_claw', ['날카로운 발톱'], 500, 0), ('equip_shell', ['등껍질', '보호대'], 450, 1),
             ('equip_necklace', ['가죽 목걸이'], 400, 0), ('equip_feather', ['가벼운 깃털'], 400, 0)]
    grid(base, items, 'equip_claw')
    detail(base, 'equip_claw', '날카로운 발톱', '장비', 'brown',
           [('sword', '공격력 +50', K.BTN['orange'][1]), '내 동물 화면에서 장착', '전투 중 교체 불가'], 0, 1, 500)
    save(base, out)


def shop_egg(out):
    base = shop_frame(3)
    items = [('egg_basic', ['기본 부화 알'], 500, 0), ('egg_special', ['특수 부화 알'], 2200, 1)]
    grid(base, items, 'egg_special')
    d = ImageDraw.Draw(base)
    K.draw_text(base, (276, 268), '알은 사면 바로 부화 가능', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    # 상세: 특급 등장 확률 막대
    d.rectangle((446, 72, 618, 136), fill=(60, 40, 30), outline=K.WOOD[2])
    for i in range(12):
        a = i * math.pi / 6; d.line((532, 104, 532 + 70 * math.cos(a), 104 + 40 * math.sin(a)), fill=(130, 96, 40))
    paste(base, S.egg_special(16).resize((48, 48), Image.NEAREST), (508, 80))
    K.draw_text(base, (446, 152), '특수 부화 알', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 446, 164, '알', 'gold')
    K.draw_text(base, (446, 190), '특급 등장 확률', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (618, 190), '60%', K.F_TITLE(), K.BTN['gold'][1], 'rm')
    gauge(base, 446, 198, 172, 10, 60, 100, 'gold')
    K.draw_text(base, (446, 222), '기본 부화 알은 10%', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (446, 236), '못 가진 동물 우선', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (446, 254), '보유 1', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 446, 268, 172, 22, '지금 부화', 'green', icon='heart', f=K.F_BODY())
    button(base, 446, 300, 172, 40, '구매', 'orange', icon='coin', sub='1개 · 2,200코인')
    save(base, out)


# ================= 알 부화 연출 =================
def rays(base, cx, cy, r, n, c1, c2, a0=0, alpha=255):
    ov = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ov)
    for i in range(n):
        a = a0 + i * 2 * math.pi / n; b = a + math.pi / n
        d.polygon([(cx, cy), (cx + r * math.cos(a), cy + r * math.sin(a)), (cx + r * math.cos(b), cy + r * math.sin(b))],
                  fill=(c1 if i % 2 == 0 else c2) + (alpha,))
    base.alpha_composite(ov)


def glow(base, cx, cy, r, col, steps=6, alpha=200):
    ov = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(ov)
    for i in range(steps, 0, -1):                     # 바깥은 옅게 (계단식 = 도트 느낌)
        rr = r * i / steps
        d.ellipse((cx - rr, cy - rr * .8, cx + rr, cy + rr * .8), fill=col + (int(alpha * (1 - (i - 1) / steps) ** 1.4),))
    base.alpha_composite(ov)


def sparkle(base, x, y, s=3, c=(255, 236, 120)):
    d = ImageDraw.Draw(base)
    d.line((x - s, y, x + s, y), fill=c); d.line((x, y - s, x, y + s), fill=c); d.point((x, y), fill=(255, 255, 255))
    if s >= 3:
        d.line((x - s - 1, y, x - s, y), fill=INK); d.line((x + s, y, x + s + 1, y), fill=INK)


EGG_SC = 5                                          # 16 x5 = 80 논리 px


def egg_img(): return S.egg_special(16).resize((16 * EGG_SC, 16 * EGG_SC), Image.NEAREST)


def cracks(im, lvl):
    """알 위에 금: lvl 1 = 한 줄, 2 = 여러 줄 + 빛 새어 나옴"""
    d = ImageDraw.Draw(im); u = EGG_SC
    lines = [[(5, 5), (7, 7), (6, 9), (8, 10)]]
    if lvl >= 2: lines += [[(8, 10), (10, 8), (11, 10)], [(7, 7), (9, 6), (10, 4)], [(6, 9), (4, 11)]]
    for ln in lines:
        pts = [(x * u + u // 2, y * u + u // 2) for x, y in ln]
        if lvl >= 2: d.line(pts, fill=(255, 250, 200), width=u + 2)
        d.line(pts, fill=INK, width=max(2, u // 2))
    return im


def scene_base():
    base = shop_bg(dim=True); B.header(base)
    ov = Image.new('RGBA', (W, H), (20, 12, 30, 150)); base.alpha_composite(ov)
    return base


def hatch_frame(stage, t=0):
    """stage 0 흔들림 / 1 금 / 2 빛 폭발 / 3 등장"""
    base = scene_base(); cx, cy = 320, 176
    if stage == 0:
        glow(base, cx, cy, 90, (255, 210, 90), alpha=120)
        e = egg_img(); dx = (-4, 4)[t % 2]
        paste(base, e, (cx - 40 + dx, cy - 44))
        d = ImageDraw.Draw(base)
        for s in (-1, 1):                              # 흔들림 선
            x = cx + s * 54 + dx
            for k in range(3): d.line((x + s * k * 5, cy - 18 + k * 12, x + s * k * 5, cy - 8 + k * 12), fill=(255, 240, 200))
        K.draw_text(base, (cx, 300), '...!', K.F_BIG(), (255, 246, 220), 'mm', INK)
    elif stage == 1:
        rays(base, cx, cy, 200, 16, (255, 224, 120), (255, 190, 70), .2, 90)
        glow(base, cx, cy, 110, (255, 230, 140), alpha=170)
        paste(base, cracks(egg_img(), 2), (cx - 40, cy - 44))
        for x, y in ((cx - 70, cy - 50), (cx + 66, cy - 30), (cx - 58, cy + 40), (cx + 74, cy + 46)): sparkle(base, x, y)
        K.draw_text(base, (cx, 300), '알에 금이 간다!', K.F_BIG(), (255, 246, 220), 'mm', INK)
    elif stage == 2:
        rays(base, cx, cy, 420, 20, (255, 246, 200), (255, 214, 110), .1, 200)
        glow(base, cx, cy, 160, (255, 255, 230), steps=8, alpha=255)
        e = egg_img(); top = e.crop((0, 0, 80, 40)).rotate(18, Image.NEAREST, expand=True); bot = e.crop((0, 40, 80, 80))
        paste(base, top, (cx - 110, cy - 110)); paste(base, bot.rotate(-10, Image.NEAREST, expand=True), (cx + 44, cy + 34))
        for i in range(10):
            a = i * 2 * math.pi / 10 + .3; r = 90 + (i % 3) * 18
            sparkle(base, int(cx + r * math.cos(a)), int(cy + r * .7 * math.sin(a)), 4 if i % 2 else 3, (255, 250, 220))
    else:
        rays(base, cx, cy - 6, 380, 16, (255, 220, 110), (240, 170, 60), .15, 120)
        glow(base, cx, cy, 120, (255, 236, 170), alpha=150)
        bot = egg_img().crop((0, 46, 80, 80))
        paste(base, B.spr('dealer_special_02', 1, 4), (cx - 56, cy - 92))
        paste(base, bot, (cx - 40, cy + 12))
        for x, y in ((cx - 76, cy - 60), (cx + 70, cy - 70), (cx - 84, cy + 20), (cx + 86, cy + 10), (cx, cy - 92)): sparkle(base, x, y, 4)
    return base


def storyboard(out):
    fr = [hatch_frame(0, 1), hatch_frame(1), hatch_frame(2), hatch_frame(3)]
    caps = ['① 흔들흔들 (0.0~1.2초)', '② 금 + 빛 새어 나옴 (1.2~2.2초)', '③ 빛 폭발 + 껍질 튐 (2.2~2.6초)', '④ 등장 → 결과 창 (2.6초~)']
    sb = Image.new('RGBA', (W * 2 + 24, H * 2 + 60), (40, 30, 26, 255))
    for i, (f, c) in enumerate(zip(fr, caps)):
        x, y = 8 + (i % 2) * (W + 8), 8 + (i // 2) * (H + 22)
        sb.alpha_composite(f, (x, y)); K.draw_text(sb, (x + 4, y + H + 10), c, K.F_TITLE(), (255, 240, 210), 'lm')
    sb.resize((sb.width * 2, sb.height * 2), Image.NEAREST).convert('RGB').save(out)


def hatch_result(out, dup=False):
    base = scene_base(); d = ImageDraw.Draw(base)
    B.panel(base, 56, 50, 528, 300)
    ribbon(base, 250, 42, 140, '부화 성공!', 'green')
    # 왼쪽: 등장 무대
    st = Image.new('RGBA', (W, H)); rays(st, 172, 168, 140, 16, (255, 224, 120), (250, 196, 80), .15, 255)
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).rectangle((74, 74, 270, 268), fill=255)
    bgc = Image.new('RGBA', (W, H)); bgc.paste(st, (0, 0), m)
    d.rectangle((73, 73, 271, 269), fill=(255, 238, 190)); base.alpha_composite(bgc)
    glow(base, 172, 168, 70, (255, 255, 230), alpha=200)
    d = ImageDraw.Draw(base); d.rectangle((73, 73, 271, 269), outline=K.WOOD[1])
    d.ellipse((136, 208, 208, 220), fill=(214, 160, 80))
    paste(base, B.spr('dealer_special_02', 1, 4), (116, 116))
    paste(base, egg_img().crop((0, 50, 80, 80)).resize((60, 22), Image.NEAREST), (84, 236))
    paste(base, egg_img().crop((0, 0, 80, 34)).rotate(-15, Image.NEAREST, expand=True).resize((50, 30), Image.NEAREST), (208, 228))
    for x, y in ((92, 92), (252, 100), (96, 196), (250, 190), (172, 84)): sparkle(base, x, y, 4)
    if not dup:                                         # NEW 배지
        f = K.F_TITLE(); l, t, r, b = f.getbbox('NEW'); w, h = (r - l) + 12, (b - t) + 8
        d.rectangle((78, 78, 78 + w, 78 + h), fill=RED, outline=INK); d.line((79, 79, 77 + w, 79), fill=K.BTN['red'][3])
        d.polygon([(78 + w + 1, 78), (78 + w + 6, 78), (78 + w + 1, 78 + h // 2), (78 + w + 6, 78 + h), (78 + w + 1, 78 + h)], fill=RED, outline=INK)
        text_mid(base, 78 + w / 2 + .5, 78 + h / 2 + .5, 'NEW', f, (255, 255, 255), K.BTN['red'][0])
    # 오른쪽 정보
    x0 = 286
    K.draw_text(base, (x0, 88), '불씨매', K.F_BIG(), K.TEXT, 'lm')
    cx = x0
    for t, c in (('특급', 'gold'), ('딜러', 'orange'), ('불', 'red'), ('강점 민첩', 'green')):
        cx += chip(base, cx, 100, t, c) + 3
    K.draw_text(base, (x0, 130), '불타는 날개로 하늘에서 내리꽂는다.', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    if dup:
        B.card(base, x0, 138, 280, 22); K.draw_text(base, (x0 + 140, 149), '이미 보유한 동물 · 도감 변화 없음', K.F_SMALL(), RED, 'mm')
    else:
        B.card(base, x0, 138, 280, 22); paste(base, K.icon('heart'), (x0 + 8, 143))
        K.draw_text(base, (x0 + 24, 149), '도감 등록!  14 / 30', K.F_BODY(), GREEN, 'lm')
    base_stats = {'hp': 81, 'attack': 125, 'defense': 66, 'agility': 121}
    caps = {'hp': 240, 'attack': 420, 'defense': 180, 'agility': 360}
    for i, (k, n, icn, col) in enumerate(STATS):
        y = 176 + i * 24
        paste(base, K.icon(icn), (x0, y - 6))
        K.draw_text(base, (x0 + 16, y), n, K.F_BODY(), K.TEXT, 'lm')
        K.draw_text(base, (x0 + 88, y), str(base_stats[k]), K.F_TITLE(), K.TEXT, 'rm')
        gauge(base, x0 + 96, y - 5, 140, 10, base_stats[k], caps[k], col)
        K.draw_text(base, (x0 + 280, y), f'/ {caps[k]}', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    K.draw_text(base, (x0, 270), '1단계 MAX 기준 · 네 능력치 MAX면 진화', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 74, 290, 148, 40, '내 동물 보기', 'green', icon='heart')
    button(base, 230, 290, 172, 40, '한 번 더 부화', 'orange', icon='coin', sub='특수 부화 알 0개' if not dup else '특수 부화 알 1개',
           state='disabled' if not dup else 'normal')
    button(base, 410, 290, 158, 40, '상점으로', 'brown', icon='back')
    save(base, out)


# ================= 병원 후보 =================
def hospital_bg(dim=False): return HR.room(dim)


def hosp_clean_old():
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 26, W, 260), fill=(250, 236, 240))
    for y in range(26, 260, 18): d.line((0, y, W, y), fill=(244, 222, 230))
    d.rectangle((0, 200, W, 260), fill=(246, 200, 214)); d.line((0, 200, W, 200), fill=(220, 150, 170))
    d.rectangle((30, 70, 150, 190), fill=(255, 255, 255), outline=INK)               # 약장
    for r in range(3):
        d.line((30, 110 + r * 40, 150, 110 + r * 40), fill=INK)
        for c in range(4):
            col = [(240, 120, 160), (250, 196, 70), (120, 200, 240), (140, 210, 120)][(r + c) % 4]
            d.rectangle((40 + c * 28, 92 + r * 40, 54 + c * 28, 109 + r * 40), fill=col, outline=INK)
    d.rectangle((272, 58, 368, 104), fill=(255, 255, 255), outline=INK)               # 십자 간판
    d.rectangle((312, 62, 328, 100), fill=(230, 70, 80)); d.rectangle((300, 74, 340, 88), fill=(230, 70, 80))
    d.rectangle((0, 260, W, H), fill=(200, 220, 236))
    for x in range(0, W, 32):
        for y in range(260, H, 32):
            if (x // 32 + y // 32) % 2 == 0: d.rectangle((x, y, x + 31, y + 31), fill=(220, 234, 246))
    return im


SICK = [('healer_normal_03', '산들햄스터', 72), ('tank_normal_02', '물방울거북', 60), ('dealer_normal_04', '불씨너구리', 40)]


def potion_row(base, x, y, w, k, name, ch, fat, own, sel):
    B.card(base, x, y, w, 44, sel)
    paste(base, ic(k, 2), (x + 6, y + 6))
    K.draw_text(base, (x + 44, y + 13), name, K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (x + 44, y + 30), f'치료 {ch}% · 피로도 -{fat}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x + w - 8, y + 13), f'보유 {own}', K.F_SMALL(), K.TEXT if own else RED, 'rm')


def hospital_A(out):
    """A 진료실: 가운데 침대에 환자 + 아래 포션 쟁반"""
    base = HR.room(); B.header(base); d = ImageDraw.Draw(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '병원', 'red')
    x = 160
    for i, (k, n, f) in enumerate(SICK):
        w = int(tl(n, K.F_BODY())) + 36
        B.card(base, x, 32, w, 22, i == 0); paste(base, B.spr(k, 1, 1).crop((4, 4, 24, 20)), (x + 4, 35))
        K.draw_text(base, (x + 28, 43), n, K.F_BODY(), K.TEXT, 'lm'); x += w + 4
    HR.bed_back(base)
    paste(base, B.spr('healer_normal_03', 1, 3), (236, 92))
    d = ImageDraw.Draw(base); d.ellipse((300, 112, 306, 120), fill=(140, 200, 250), outline=INK); d.point((302, 114), fill=(255, 255, 255))
    HR.blanket(base)
    d = ImageDraw.Draw(base)                                                               # 아픔 말풍선
    B.card(base, 312, 92, 54, 22); d.polygon([(318, 113), (324, 113), (314, 120)], fill=(250, 240, 220), outline=INK)
    paste(base, K.icon('zzz'), (317, 97)); K.draw_text(base, (351, 103), '아픔', K.F_BODY(), RED, 'mm')
    # 정보 띠
    B.panel(base, 456, 66, 176, 150)
    K.draw_text(base, (468, 84), '산들햄스터', K.F_BIG(), K.TEXT, 'lm')
    cx = 468
    for t, c in (('아픔', 'red'), ('출전 불가', 'gray')): cx += chip(base, cx, 96, t, c) + 3
    K.draw_text(base, (468, 124), '피로도', K.F_SMALL(), K.TEXT, 'lm'); K.draw_text(base, (620, 124), '72 나쁨', K.F_SMALL(), RED, 'rm')
    gauge(base, 468, 132, 152, 10, 72, 100, 'red')
    K.draw_text(base, (468, 160), '포만감', K.F_SMALL(), K.TEXT, 'lm'); K.draw_text(base, (620, 160), '보통', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    gauge(base, 468, 168, 152, 10, 48, 100, 'orange')
    K.draw_text(base, (468, 196), '훈련·사냥·전투 불가', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 아래 쟁반
    B.panel(base, 8, 252, 624, 104)
    K.draw_text(base, (22, 268), '치료할 포션 선택', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (432, 268), '실패 시 포션만 소모', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    potion_row(base, 18, 280, 204, 'heal_basic', '기본 회복 포션', 50, 10, 2, False)
    potion_row(base, 228, 280, 204, 'heal_advanced', '고급 회복 포션', 90, 30, 1, True)
    button(base, 442, 278, 180, 48, '치료하기', 'green', icon='heart', sub='고급 회복 포션 1개 사용')
    K.draw_text(base, (532, 340), '포션 사러 가기 ▶ 상점', K.F_SMALL(), K.BTN['orange'][1], 'mm')
    save(base, out)


def hospital_B(out):
    """B 환자 카드: 아픈 동물마다 카드 + 카드 안 치료 버튼 2개"""
    base = hospital_bg(dim=True); B.header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '병원', 'red')
    # 위: 가진 포션
    B.card(base, 380, 30, 252, 26)
    paste(base, ic('heal_basic', 1), (388, 35)); K.draw_text(base, (408, 44), '기본 2', K.F_BODY(), K.TEXT, 'lm')
    paste(base, ic('heal_advanced', 1), (460, 35)); K.draw_text(base, (480, 44), '고급 1', K.F_BODY(), K.TEXT, 'lm')
    button(base, 540, 33, 86, 20, '상점', 'orange', icon='coin', f=K.F_BODY())
    for i, (k, n, fat) in enumerate(SICK):
        x = 8 + i * 210; y = 64
        B.panel(base, x, y, 204, 292)
        d = ImageDraw.Draw(base)
        d.rectangle((x + 14, y + 14, x + 190, y + 112), fill=(250, 226, 232), outline=(220, 150, 170))
        d.rectangle((x + 92, y + 22, x + 112, y + 30), fill=(230, 70, 80)); d.rectangle((x + 98, y + 16, x + 106, y + 36), fill=(230, 70, 80))
        paste(base, B.spr(k, 1, 3, dim=True), (x + 60, y + 30))
        K.draw_text(base, (x + 14, y + 128), n, K.F_BIG(), K.TEXT, 'lm')
        chip(base, x + 14, y + 140, '아픔', 'red')
        K.draw_text(base, (x + 14, y + 168), '피로도', K.F_SMALL(), K.TEXT, 'lm')
        K.draw_text(base, (x + 190, y + 168), f'{fat}', K.F_SMALL(), RED if fat >= 56 else K.TEXT, 'rm')
        gauge(base, x + 14, y + 176, 176, 10, fat, 100, 'red' if fat >= 56 else 'orange')
        button(base, x + 14, y + 198, 176, 38, '기본 포션 치료', 'green', icon='heart', sub='치료 50% · 피로도 -10')
        button(base, x + 14, y + 242, 176, 38, '고급 포션 치료', 'blue', icon='heart', sub='치료 90% · 피로도 -30',
               state='normal' if i == 0 else 'disabled')
    save(base, out)


def hospital_C(out):
    """C 대기실 + 진료 결과: 왼쪽 대기 줄, 오른쪽 치료 결과 연출"""
    base = hospital_bg(dim=True); B.header(base); d = ImageDraw.Draw(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '병원', 'red')
    B.panel(base, 8, 58, 196, 298)
    K.draw_text(base, (22, 76), '대기 중', K.F_TITLE(), K.TEXT, 'lm'); K.draw_text(base, (190, 76), '3마리', K.F_SMALL(), RED, 'rm')
    for i, (k, n, fat) in enumerate(SICK):
        y = 88 + i * 52
        B.card(base, 16, y, 180, 48, i == 0)
        paste(base, B.spr(k, 1, 1), (22, y + 10))
        K.draw_text(base, (56, y + 16), n, K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (56, y + 33), f'피로도 {fat}', K.F_SMALL(), RED if fat >= 56 else K.TEXT_SOFT, 'lm')
        if i == 0: chip(base, 150, y + 4, '진료', 'green')
    # 결과 연출
    B.panel(base, 210, 58, 422, 298)
    ribbon(base, 361, 50, 120, '치료 성공!', 'green')
    st = Image.new('RGBA', (W, H)); rays(st, 421, 150, 260, 16, (210, 246, 200), (236, 255, 228), .2, 255)
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).rectangle((227, 81, 615, 213), fill=255)
    ImageDraw.Draw(base).rectangle((227, 81, 615, 213), fill=(236, 250, 236)); sc = Image.new('RGBA', (W, H)); sc.paste(st, (0, 0), m); base.alpha_composite(sc)
    d = ImageDraw.Draw(base); d.rectangle((226, 80, 616, 214), outline=(140, 200, 150))
    glow(base, 421, 150, 70, (255, 255, 240), alpha=220)
    paste(base, B.spr('healer_normal_03', 1, 3), (379, 98))
    for x, y in ((330, 110), (512, 104), (346, 186), (500, 190)):
        d = ImageDraw.Draw(base); d.rectangle((x - 1, y - 4, x + 1, y + 4), fill=(80, 200, 110)); d.rectangle((x - 4, y - 1, x + 4, y + 1), fill=(80, 200, 110))
    K.draw_text(base, (421, 232), '산들햄스터 회복!', K.F_BIG(), K.TEXT, 'mm')
    cx = 312
    K.draw_text(base, (cx, 258), '피로도', K.F_BODY(), K.TEXT, 'lm')
    K.draw_text(base, (cx + 70, 258), '72', K.F_TITLE(), RED, 'rm'); K.draw_text(base, (cx + 84, 258), '→', K.F_TITLE(), K.TEXT, 'mm')
    K.draw_text(base, (cx + 98, 258), '42', K.F_TITLE(), GREEN, 'lm')
    chip(base, cx + 124, 252, '보통', 'orange'); chip(base, cx + 160, 252, '출전 가능', 'green')
    K.draw_text(base, (421, 280), '고급 회복 포션 1개 사용', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 226, 300, 190, 40, '다음 환자', 'green', icon='heart', sub='물방울거북')
    button(base, 426, 300, 190, 40, '지도로', 'brown', icon='back')
    save(base, out)


def hospital_fail(out):
    """치료 실패 (A안 진료실 기준 결과 창)"""
    base = hospital_bg(dim=True); B.header(base)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 90)); base.alpha_composite(ov)
    B.panel(base, 170, 80, 300, 220)
    ribbon(base, 260, 72, 120, '치료 실패...', 'brown')
    d = ImageDraw.Draw(base); d.rectangle((268, 100, 372, 180), fill=(236, 228, 236), outline=(190, 170, 190))
    paste(base, B.spr('tank_normal_02', 1, 3, dim=True), (278, 98))
    d.ellipse((350, 104, 366, 120), fill=(140, 180, 230), outline=INK)
    K.draw_text(base, (320, 198), '물방울거북 아직 아픔', K.F_BIG(), K.TEXT, 'mm')
    K.draw_text(base, (320, 218), '기본 회복 포션 1개 소모', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 186, 240, 130, 40, '다시 치료', 'green', icon='heart', sub='기본 1개 남음')
    button(base, 324, 240, 130, 40, '닫기', 'brown')
    save(base, out)


def hospital_success(out):
    """치료 성공 (A안 진료실 위 결과 창)"""
    base = hospital_bg(dim=True); B.header(base)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 90)); base.alpha_composite(ov)
    B.panel(base, 170, 72, 300, 236)
    ribbon(base, 260, 64, 120, '치료 성공!', 'green')
    st = Image.new('RGBA', (W, H)); rays(st, 320, 136, 120, 14, (210, 246, 200), (236, 255, 228), .2, 255)
    m = Image.new('L', (W, H)); ImageDraw.Draw(m).rectangle((269, 93, 371, 175), fill=255)
    d = ImageDraw.Draw(base); d.rectangle((268, 92, 372, 176), fill=(236, 250, 236))
    sc = Image.new('RGBA', (W, H)); sc.paste(st, (0, 0), m); base.alpha_composite(sc)
    d = ImageDraw.Draw(base); d.rectangle((268, 92, 372, 176), outline=(140, 200, 150))
    paste(base, B.spr('healer_normal_03', 1, 3), (278, 90))
    for x, y in ((282, 104), (358, 110), (288, 164), (356, 160)):
        d.rectangle((x - 1, y - 4, x + 1, y + 4), fill=(80, 200, 110)); d.rectangle((x - 4, y - 1, x + 4, y + 1), fill=(80, 200, 110))
    K.draw_text(base, (320, 194), '산들햄스터 회복!', K.F_BIG(), K.TEXT, 'mm')
    K.draw_text(base, (262, 216), '피로도', K.F_BODY(), K.TEXT, 'lm')
    K.draw_text(base, (322, 216), '72', K.F_TITLE(), RED, 'rm'); K.draw_text(base, (334, 216), '→', K.F_TITLE(), K.TEXT, 'mm')
    K.draw_text(base, (346, 216), '42', K.F_TITLE(), GREEN, 'lm')
    K.draw_text(base, (320, 234), '고급 회복 포션 1개 사용', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 186, 252, 130, 40, '다음 환자', 'green', icon='heart', sub='물방울거북')
    button(base, 324, 252, 130, 40, '닫기', 'brown')
    save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    shop_potion(out / 'shop_A1_potion.png'); shop_equip(out / 'shop_A2_equip.png'); shop_egg(out / 'shop_A3_egg.png')
    storyboard(out / 'hatch_1_storyboard.png'); hatch_result(out / 'hatch_2_result.png'); hatch_result(out / 'hatch_3_duplicate.png', dup=True)
    hospital_A(out / 'hospital_A_room.png'); hospital_B(out / 'hospital_B_cards.png'); hospital_C(out / 'hospital_C_queue.png')
    hospital_fail(out / 'hospital_fail.png'); hospital_success(out / 'hospital_success.png')
    print('ok')
