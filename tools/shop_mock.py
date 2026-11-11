"""상점 후보 A(카운터)·B(진열대) + 알 부화 + 병원 목업."""
import sys, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
import shop_icons as S
import food_icons as F
import home_mock as Hm
from ui_mock import paste, button, gauge, chip, ribbon

W, H = 640, 360
INK = K.INK


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def ic(key, sc=1):
    if key in S.ICONS or key.startswith('seed_'): return S.icon(key, sc)
    return F.icon(key, sc)


# ---------------- 배경: 상점 안 ----------------
def shop_bg(dim=False, clean=False):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 26, W, 280), fill=(236, 206, 160))
    for x in range(0, W, 20): d.line((x, 40, x, 280), fill=(222, 190, 144))
    for x in range(0, W, 16):                                               # 줄무늬 차양
        d.rectangle((x, 26, x + 7, 40), fill=(220, 80, 70)); d.rectangle((x + 8, 26, x + 15, 40), fill=(255, 246, 230))
    for x in range(0, W, 16): d.pieslice((x, 34, x + 16, 48), 0, 180, fill=(220, 80, 70) if (x // 16) % 2 == 0 else (255, 246, 230))
    d.line((0, 40, W, 40), fill=INK)
    for y in (() if clean else (96, 160, 224)):                             # 벽 선반
        d.rectangle((8, y, 632, y + 6), fill=K.WOOD[2], outline=INK)
        for x in range(20, 620, 30):
            c = [(230, 120, 90), (140, 200, 230), (250, 204, 70), (180, 140, 220), (140, 200, 120), (240, 160, 190)][(x // 30 + y) % 6]
            h = 14 + (x * 7 + y) % 10
            d.rectangle((x, y - h, x + 18, y - 1), fill=c, outline=INK); d.line((x + 2, y - h + 2, x + 2, y - 3), fill=(255, 255, 255))
    d.rectangle((0, 280, W, H), fill=K.WOOD[2])
    d.rectangle((0, 280, W, 292), fill=K.WOOD[4], outline=INK)
    for x in range(0, W, 48): d.rectangle((x + 4, 296, x + 44, H), outline=K.WOOD[1])
    if dim:
        im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.55)).enhance(.7)
    return im


def hospital_bg(dim=False):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 26, W, 260), fill=(250, 236, 240))
    for y in range(26, 260, 18): d.line((0, y, W, y), fill=(244, 222, 230))
    d.rectangle((0, 200, W, 260), fill=(246, 200, 214)); d.line((0, 200, W, 200), fill=(220, 150, 170))
    d.rectangle((280, 50, 360, 130), fill=(255, 255, 255), outline=INK)       # 십자 간판
    d.rectangle((310, 60, 330, 120), fill=(230, 70, 80)); d.rectangle((290, 80, 350, 100), fill=(230, 70, 80))
    for x in (40, 500):                                                      # 침대
        d.rectangle((x, 170, x + 100, 230), fill=(255, 255, 255), outline=INK)
        d.rectangle((x, 160, x + 30, 182), fill=(200, 230, 250), outline=INK)
        d.rectangle((x + 30, 176, x + 100, 230), fill=(160, 210, 240), outline=INK)
        d.rectangle((x - 4, 150, x + 4, 240), fill=(170, 176, 190), outline=INK)
    d.rectangle((0, 260, W, H), fill=(200, 220, 236))
    for x in range(0, W, 32):
        for y in range(260, H, 32):
            if (x // 32 + y // 32) % 2 == 0: d.rectangle((x, y, x + 31, y + 31), fill=(220, 234, 246))
    if dim:
        im = ImageEnhance.Color(ImageEnhance.Brightness(im).enhance(.55)).enhance(.7)
    return im


def coins(base, n='4,200'):
    pass


CATS = [('먹이·장난감', 'snack'), ('회복·포션', 'heal_basic'), ('장비', 'equip_claw'), ('알', 'egg_basic'), ('재료·씨앗', 'seed'), ('팔기', 'toy_ball')]
POTIONS = [('heal_basic', '기본 회복 포션', 40, '질병 치료 50% · 피로도 -10', 2), ('heal_advanced', '고급 회복 포션', 80, '질병 치료 90% · 피로도 -30', 0),
           ('potion_attack', '공격력 포션', 150, '전투 1번 공격 +100', 1), ('potion_defense', '방어력 포션', 130, '전투 1번 방어 +100', 0),
           ('potion_hp', '체력 포션', 120, '전투 1번 체력 +100', 0), ('potion_agility', '민첩성 포션', 100, '전투 1번 민첩 +100', 0),
           ('battle_bandage', '전투 응급 붕대', 80, '전투 중 체력 +80', 2)]


def price(base, x, y, n, anchor='lm', col=K.TEXT):
    paste(base, K.icon('coin'), (x, y - 6) if anchor == 'lm' else (x - 14 - ImageDraw.Draw(base).textlength(f'{n:,}', font=K.F_TITLE()), y - 6))
    if anchor == 'lm': K.draw_text(base, (x + 14, y), f'{n:,}', K.F_TITLE(), col, 'lm')
    else: K.draw_text(base, (x, y), f'{n:,}', K.F_TITLE(), col, 'rm')


# ---------------- A: 카운터 (탭 + 격자 + 상세) ----------------
def shop_counter(out):
    base = shop_bg(dim=True); B.header(base)
    button(base, 12, 46, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 47, 70, '상점', 'red')
    # 왼쪽 탭
    B.panel(base, 8, 72, 112, 284)
    for i, (t, k) in enumerate(CATS):
        y = 82 + i * 44
        on = i == 1
        B.card(base, 16, y, 96, 40, on)
        paste(base, ic(k, 1), (22, y + 12))
        K.draw_text(base, (42, y + 20), t, K.F_TITLE() if on else K.F_BODY(), K.TEXT if i < 5 else K.BTN['red'][1], 'lm')
    # 가운데 격자
    B.panel(base, 124, 72, 304, 284)
    for i, (k, name, p, desc, own) in enumerate(POTIONS):
        col, row = i % 3, i // 3
        x = 134 + col * 96; y = 82 + row * 90
        B.card(base, x, y, 92, 86, k == 'heal_advanced')
        paste(base, ic(k, 2), (x + 30, y + 6))
        K.draw_text(base, (x + 46, y + 48), name if len(name) <= 6 else name[:6], K.F_SMALL(), K.TEXT, 'mm')
        if len(name) > 6: K.draw_text(base, (x + 46, y + 59), name[6:], K.F_SMALL(), K.TEXT, 'mm')
        price(base, x + 30, y + 74, p)
        if own: chip(base, x + 60, y + 4, f'{own}개', 'gray')
    # 오른쪽 상세
    B.panel(base, 432, 72, 200, 284)
    d = ImageDraw.Draw(base)
    d.rectangle((446, 86, 618, 150), fill=(250, 236, 206), outline=K.WOOD[2])
    paste(base, ic('heal_advanced', 3), (508, 94))
    K.draw_text(base, (446, 166), '고급 회복 포션', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 446, 178, '회복', 'green')
    K.draw_text(base, (446, 204), '아픈 동물을 90% 확률로 치료', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (446, 218), '피로도도 30 줄여요', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (446, 232), '가진 개수: 0개', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 수량
    button(base, 446, 250, 26, 22, '－', 'brown', f=K.F_TITLE())
    B.card(base, 476, 250, 46, 22); K.draw_text(base, (499, 261), '2', K.F_TITLE(), K.TEXT, 'mm')
    button(base, 526, 250, 26, 22, '＋', 'brown', f=K.F_TITLE())
    K.draw_text(base, (618, 261), '160', K.F_TITLE(), K.TEXT, 'rm'); paste(base, K.icon('coin'), (576, 255))
    button(base, 446, 300, 172, 40, '사기', 'orange', icon='coin')
    save(base, out)


# ---------------- B: 진열대 (선반 위 물건 + 아래 서랍) ----------------
def shop_shelf(out):
    base = shop_bg(clean=True); B.header(base)
    d = ImageDraw.Draw(base)
    button(base, 12, 46, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 47, 70, '상점', 'red')
    for i, (t, k) in enumerate(CATS):
        x = 160 + i * 79; on = i == 1
        button(base, x, 46, 75, 20, t, 'orange' if on else ('red' if i == 5 else 'brown'), 'normal', f=K.F_SMALL())
    for y in (150, 250):
        d.rectangle((14, y, 400, y + 8), fill=K.WOOD[2], outline=INK); d.line((15, y + 1, 399, y + 1), fill=K.WOOD[4])
        d.rectangle((24, y + 9, 30, y + 22), fill=K.WOOD[1], outline=INK); d.rectangle((384, y + 9, 390, y + 22), fill=K.WOOD[1], outline=INK)
    pos = [(36, 150), (128, 150), (220, 150), (312, 150), (36, 250), (128, 250), (220, 250)]
    for (k, name, p, desc, own), (x, y) in zip(POTIONS, pos):
        paste(base, ic(k, 3), (x, y - 48))
        d.line((x + 24, y + 8, x + 24, y + 14), fill=INK)
        B.card(base, x + 2, y + 14, 46, 18, k == 'heal_advanced')
        K.draw_text(base, (x + 25, y + 23), f'{p}', K.F_TITLE(), K.TEXT, 'mm')
    B.corners(base, 124, 96, 180, 150)
    # 오른쪽 말풍선 상세
    B.card(base, 410, 70, 220, 196)
    K.draw_text(base, (424, 86), '고급 회복 포션', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 424, 98, '회복', 'green')
    K.draw_text(base, (424, 126), '아픈 동물을 90% 확률로 치료', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (424, 140), '피로도도 30 줄여요', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (424, 154), '가진 개수: 0개', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 424, 176, 26, 22, '－', 'brown', f=K.F_TITLE())
    B.card(base, 454, 176, 46, 22); K.draw_text(base, (477, 187), '2', K.F_TITLE(), K.TEXT, 'mm')
    button(base, 504, 176, 26, 22, '＋', 'brown', f=K.F_TITLE())
    paste(base, K.icon('coin'), (568, 181)); K.draw_text(base, (616, 187), '160', K.F_TITLE(), K.TEXT, 'rm')
    button(base, 424, 214, 192, 38, '사기', 'orange', icon='coin')
    # 계산대
    K.draw_text(base, (24, 318), '진열대에서 물건을 누르면 오른쪽에 설명이 나와요', K.F_SMALL(), K.TEXT, 'lm', K.WOOD[4])
    save(base, out)


# ---------------- 알 부화 ----------------
def hatch(out):
    base = shop_bg(dim=True); B.header(base)
    d = ImageDraw.Draw(base)
    B.panel(base, 170, 60, 300, 290)
    ribbon(base, 270, 52, 100, '알 부화!', 'green')
    d.rectangle((262, 82, 378, 196), fill=(255, 246, 214), outline=K.WOOD[2])
    for i in range(16):
        a = i * math.pi / 8; d.line((320, 140, 320 + 56 * math.cos(a), 140 + 50 * math.sin(a)), fill=(255, 236, 170))
    # 깨진 알 껍질
    sh = S.egg_special().resize((64, 64), Image.NEAREST)
    paste(base, sh.crop((0, 36, 64, 64)), (288, 158))
    paste(base, B.spr('dealer_special_02', 1, 2), (292, 96))
    for x, y in ((276, 92), (362, 96), (366, 176), (272, 170)):
        d.line((x - 3, y, x + 3, y), fill=(250, 204, 70)); d.line((x, y - 3, x, y + 3), fill=(250, 204, 70))
    K.draw_text(base, (320, 212), '불씨매', K.F_BIG(), K.TEXT, 'mm')
    x = 254
    for t, c in (('특급', 'purple'), ('딜러', 'orange'), ('불', 'red'), ('도감 새 등록!', 'green')):
        x += chip(base, x, 224, t, c) + 3
    K.draw_text(base, (320, 256), '공 125 · 방 70 · 민 110 · 체 85', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 190, 300, 124, 34, '내 동물 보기', 'green', icon='heart', f=K.F_SMALL())
    button(base, 326, 300, 124, 34, '상점으로', 'brown', icon='back', f=K.F_SMALL())
    save(base, out)


# ---------------- 병원 ----------------
def hospital(out):
    base = hospital_bg(dim=True); B.header(base)
    d = ImageDraw.Draw(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 70, '병원', 'red')
    # 왼쪽: 아픈 동물
    B.panel(base, 8, 58, 300, 298)
    K.draw_text(base, (24, 74), '아픈 동물', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (292, 74), '2마리', K.F_SMALL(), K.BTN['red'][1], 'rm')
    sick = [('healer_normal_03', '산들햄스터', 72, True), ('tank_normal_02', '물방울거북', 60, False)]
    for i, (k, n, fat, sel) in enumerate(sick):
        y = 86 + i * 64
        B.card(base, 18, y, 280, 58, sel)
        d.rectangle((26, y + 6, 70, y + 50), fill=(250, 226, 232), outline=(220, 150, 170))
        paste(base, B.spr(k, 1, 1), (34, y + 14))
        K.draw_text(base, (80, y + 14), n, K.F_TITLE(), K.TEXT, 'lm')
        chip(base, 80, y + 22, '아픔', 'red')
        K.draw_text(base, (82, y + 46), '출전·훈련 못 해요', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        paste(base, K.icon('zzz'), (200, y + 20)); gauge(base, 214, y + 22, 76, 8, fat, 100, 'red' if fat >= 56 else 'orange')
    K.draw_text(base, (24, 230), '건강한 동물', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, k in enumerate(('dealer_normal_01', 'tank_normal_01', 'healer_normal_01', 'dealer_special_02')):
        x = 22 + i * 46; B.card(base, x, 240, 42, 40)
        paste(base, B.spr(k, 2 if k.endswith('02') else 1, 1), (x + 7, 246))
    K.draw_text(base, (24, 300), '아프면 마을 지도에서 병원 앞에 보여요', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 오른쪽: 치료
    B.panel(base, 314, 58, 318, 298)
    d.rectangle((330, 74, 420, 164), fill=(250, 226, 232), outline=(220, 150, 170))
    paste(base, B.spr('healer_normal_03', 1, 3), (334, 78))
    K.draw_text(base, (432, 90), '산들햄스터', K.F_BIG(), K.TEXT, 'lm')
    chip(base, 432, 102, '아픔', 'red')
    K.draw_text(base, (432, 134), '포션을 골라 치료해요', K.F_BODY(), K.TEXT, 'lm')
    K.draw_text(base, (432, 150), '실패하면 포션만 없어져요', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, (k, n, ch, f_, own, sel) in enumerate((('heal_basic', '기본 회복 포션', 50, 10, 2, False), ('heal_advanced', '고급 회복 포션', 90, 30, 0, True))):
        y = 176 + i * 52
        B.card(base, 330, y, 286, 46, sel)
        paste(base, ic(k, 2), (338, y + 7))
        K.draw_text(base, (376, y + 14), n, K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (376, y + 30), f'치료 {ch}% · 피로도 -{f_}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        # 성공 확률 막대
        gauge(base, 500, y + 26, 70, 8, ch, 100, 'green')
        K.draw_text(base, (606, y + 14), f'{own}개', K.F_TITLE(), K.TEXT if own else K.BTN['red'][1], 'rm')
    K.draw_text(base, (330, 290), '고급 포션이 없어요 · 80코인으로 바로 사서 쓸 수 있어요', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 330, 302, 140, 38, '사서 치료 (80)', 'orange', icon='coin', f=K.F_SMALL())
    button(base, 478, 302, 138, 38, '치료하기', 'green', 'disabled', icon='heart')
    save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    shop_counter(out / 'shop_A_counter.png'); shop_shelf(out / 'shop_B_shelf.png'); hatch(out / 'shop_hatch.png'); hospital(out / 'hospital.png')
    print('ok')
