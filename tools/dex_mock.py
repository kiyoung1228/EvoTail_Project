"""도감 후보: A(펼친 도감 책, 일반/특급 책갈피) / B(30칸 수집 보드 + 아래 정보 줄)."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import battle_mock as B
import bag_mock as BM
from ui_mock import paste, button, gauge, chip, ribbon, text_mid

W, H = 640, 360; INK = K.INK
REPO = Path('/home/claude/evotail_project')
CH = json.load(open(REPO / 'data' / 'characters.json'))
CAPS = json.load(open(REPO / 'data' / 'role_caps.json'))
ROLE = {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}
ROLE_C = {'dealer': 'orange', 'tank': 'blue', 'healer': 'green'}
ELEM = {'fire': '불', 'water': '물', 'wind': '바람'}
ELEM_C = {'fire': 'red', 'water': 'blue', 'wind': 'green'}
OWNED = {'dealer_normal_01': 2, 'dealer_normal_03': 1, 'tank_normal_01': 1, 'tank_normal_02': 2,
         'healer_normal_01': 1, 'healer_normal_04': 1, 'dealer_special_02': 2, 'tank_special_01': 1,
         'healer_special_02': 1}
ORDER = list(CH)                    # characters.json 순서 = 도감 번호
SIL = (54, 44, 60)


def no(key): return ORDER.index(key) + 1


def spr(key, stage, n, crop=False):
    im = Image.open(REPO / 'assets' / 'sprites' / f'{key}_s{stage}.png').convert('RGBA').resize((28, 28), Image.NEAREST)
    if crop: im = im.crop(im.getbbox())
    return im.resize((im.width * n, im.height * n), Image.NEAREST)


def silhouette(im, col=SIL):
    out = Image.new('RGBA', im.size, col + (0,)); a = im.getchannel('A')
    sil = Image.new('RGBA', im.size, col + (255,)); out.paste(sil, (0, 0), a)
    return out


def tl(t, f): return f.getlength(t)


def wrap(text, f, w):
    lines, cur = [], ''
    for word in text.split(' '):
        t = (cur + ' ' + word).strip()
        if tl(t, f) <= w: cur = t
        else: lines.append(cur); cur = word
    lines.append(cur); return lines


def center(base, im, cx, cy): paste(base, im, (cx - im.width // 2, cy - im.height // 2))


def qmark(base, cx, cy, f=None):
    f = f or K.F_BIG(); text_mid(base, cx, cy, '?', f, (150, 136, 160), INK)


def progress(base, x, y):
    n = len(OWNED)
    B.card(base, x, y, 150, 22)
    text_mid(base, x + 30, y + 11, f'등록 {n} / 30', K.F_SMALL(), K.TEXT)
    gauge(base, x + 60, y + 7, 82, 9, n, 30, 'green')


def stage_dots(base, x, y, cur, mx):
    d = ImageDraw.Draw(base)
    for i in range(mx):
        on = cur and i < cur
        d.rectangle((x + i * 6, y, x + i * 6 + 4, y + 4), fill=(255, 206, 60) if on else (110, 88, 74), outline=INK)
        if on: d.point((x + i * 6 + 1, y + 1), fill=(255, 246, 200))


def cell(base, x, y, w, h, key, sel=False, gold=False):
    """도감 한 칸: 가진 동물 = 지금 단계 그림 ×2, 없는 동물 = 실루엣 + ?"""
    d = ImageDraw.Draw(base); own = key in OWNED; info = CH[key]
    if own:
        d.rectangle((x, y, x + w - 1, y + h - 1), fill=(255, 246, 224), outline=INK)
        d.line((x + 1, y + 1, x + w - 2, y + 1), fill=(255, 255, 255))
        d.rectangle((x + 1, y + h - 14, x + w - 2, y + h - 2), fill=(236, 216, 178))
    else:
        d.rectangle((x, y, x + w - 1, y + h - 1), fill=(150, 128, 104), outline=INK)
        d.rectangle((x + 1, y + h - 14, x + w - 2, y + h - 2), fill=(132, 110, 88))
    if gold:
        d.rectangle((x + 1, y + 1, x + w - 2, y + h - 2), outline=(240, 188, 60))
    im = spr(key, OWNED.get(key, 1), 2, crop=True)
    if own: center(base, im, x + w // 2, y + (h - 14) // 2 + 1)
    else:
        center(base, silhouette(im), x + w // 2, y + (h - 14) // 2 + 1)
        qmark(base, x + w // 2, y + (h - 14) // 2 + 1)
    K.draw_text(base, (x + 4, y + h - 8), f'{no(key):02d}', K.F_SMALL(), K.TEXT if own else (226, 210, 190), 'lm')
    stage_dots(base, x + w - 5 - info['max_stage'] * 6 + 1, y + h - 10, OWNED.get(key), info['max_stage'])
    if sel: B.corners(base, x - 2, y - 2, x + w + 1, y + h + 1)


def stat_rows(base, x, y, key, cols=2, colw=136, gap=16, known=True):
    st = ['hp', 'attack', 'defense', 'agility']; lab = {'hp': '체력', 'attack': '공격', 'defense': '방어', 'agility': '민첩'}
    info = CH[key]; stage = OWNED.get(key, 1); caps = CAPS[info['role']][str(stage)]
    base_stats = info['base_stats']
    for i, s in enumerate(st):
        cx = x + (i % cols) * colw; cy = y + (i // cols) * gap
        K.draw_text(base, (cx, cy + 5), lab[s], K.F_SMALL(), K.TEXT_SOFT, 'lm')
        if known:
            v = int(base_stats[s] * (1.6 if stage == 2 else 1))
            gauge(base, cx + 24, cy, colw - 80, 10, v, caps[s], ROLE_C[info['role']])
            K.draw_text(base, (cx + colw - 6, cy + 5), f'{v}/{caps[s]}', K.F_SMALL(), K.TEXT, 'rm')
        else:
            gauge(base, cx + 24, cy, colw - 80, 10, 0, 1, 'gray')
            K.draw_text(base, (cx + colw - 6, cy + 5), '???', K.F_SMALL(), K.TEXT_SOFT, 'rm')


def chips(base, x, y, key, show_strength=True):
    info = CH[key]
    w = chip(base, x, y, '특급' if info['rarity'] == 'special' else '일반', 'gold' if info['rarity'] == 'special' else 'gray') + 3
    w += chip(base, x + w, y, ROLE[info['role']], ROLE_C[info['role']]) + 3
    w += chip(base, x + w, y, ELEM[info['element']], ELEM_C[info['element']]) + 3
    if show_strength:
        s = info['strength']; s = '균형' if s == '기준' else s
        w += chip(base, x + w, y, '강점 ' + s, 'brown') + 3
    return w


def evo_line(base, x, y, key, step=84, n=2, label=True):
    """진화 단계 그림: 지금까지 온 단계는 그림, 아직 못 간 단계는 실루엣"""
    info = CH[key]; cur = OWNED.get(key, 0); d = ImageDraw.Draw(base)
    for i in range(info['max_stage']):
        st = i + 1; cx = x + i * step + 28 * n // 2
        box = (cx - 30, y, cx + 29, y + 28 * n + 2) if n == 2 else (cx - 18, y, cx + 17, y + 32)
        d.rectangle(box, fill=(255, 248, 230) if st <= cur else (196, 176, 150), outline=K.WOOD[2])
        if st == cur: B.corners(base, box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1)
        im = spr(key, st, n, crop=True)
        bx = (box[0] + box[2]) // 2; by = (box[1] + box[3]) // 2
        if st <= cur: center(base, im, bx, by)
        else: center(base, silhouette(im, (90, 76, 92)), bx, by); qmark(base, bx, by, K.F_TITLE())
        if label:
            name = info['stage_names'][i] if st <= cur else '???'
            text_mid(base, bx, box[3] + 9, name, K.F_SMALL(), K.TEXT if st <= cur else K.TEXT_SOFT)
        if i < info['max_stage'] - 1:
            ax = box[2] + (step - (box[2] - box[0])) // 2
            text_mid(base, ax + 1, by, '▶', K.F_SMALL(), K.WOOD[2])


# ================= A: 펼친 도감 책 =================
def book(base, tab):
    d = ImageDraw.Draw(base)
    # 책갈피 탭 (책 위로 튀어나옴)
    for i, (t, c) in enumerate((('일반', 'brown'), ('특급', 'gold'))):
        x = 196 + i * 62; up = 8 if (t == tab) else 0
        pal = K.BTN[c]
        d.rectangle((x, 44 - up, x + 56, 64), fill=pal[2] if t == tab else pal[1], outline=INK)
        d.line((x + 1, 45 - up, x + 55, 45 - up), fill=pal[3])
        n = sum(1 for k in OWNED if CH[k]['rarity'] == ('special' if t == '특급' else 'normal'))
        text_mid(base, x + 28, 52 - up // 2, f'{t} {n}/15', K.F_SMALL(), (255, 255, 255), pal[0])
    # 표지 + 두 쪽
    d.rectangle((8, 58, 631, 355), fill=K.WOOD[1], outline=INK)
    d.rectangle((10, 60, 629, 353), outline=K.WOOD[3])
    for (x0, x1) in ((16, 318), (322, 623)):
        d.rectangle((x0, 64, x1, 348), fill=K.PAPER[2], outline=K.WOOD[0])
        d.line((x0 + 1, 65, x1 - 1, 65), fill=K.PAPER[3])
    for i in range(4):   # 가운데 접힌 그림자
        d.line((318 - i, 65, 318 - i, 347), fill=(214 - i * 8, 190 - i * 8, 150 - i * 8))
        d.line((322 + i, 65, 322 + i, 347), fill=(214 - i * 8, 190 - i * 8, 150 - i * 8))


def left_page(base, tab, sel):
    rar = 'special' if tab == '특급' else 'normal'
    for r, role in enumerate(('dealer', 'tank', 'healer')):
        y = 72 + r * 82
        keys = [k for k in ORDER if CH[k]['role'] == role and CH[k]['rarity'] == rar]
        # 줄 머리: 역할·속성
        chip(base, 24, y + 2, ROLE[role], ROLE_C[role]); chip(base, 24, y + 20, ELEM[CH[keys[0]]['element']], ELEM_C[CH[keys[0]]['element']])
        own = sum(1 for k in keys if k in OWNED)
        K.draw_text(base, (26, y + 46), f'{own}/5', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        for c, k in enumerate(keys):
            cell(base, 62 + c * 51, y, 48, 74, k, sel=(k == sel), gold=(rar == 'special'))
    K.draw_text(base, (167, 338), '칸을 누르면 오른쪽에 정보', K.F_SMALL(), K.TEXT_SOFT, 'mm')


def right_page_owned(base, key):
    info = CH[key]; st = OWNED[key]; x = 334
    K.draw_text(base, (x, 74), f'No.{no(key):02d}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x + 34, 76), info['stage_names'][st - 1], K.F_BIG(), K.TEXT, 'lm')
    chip(base, 556, 68, f'{st}단계', 'brown')
    chips(base, x, 90, key)
    d = ImageDraw.Draw(base)
    d.rectangle((x, 112, x + 90, 200), fill=(255, 250, 236), outline=K.WOOD[2])
    d.ellipse((x + 17, 178, x + 73, 190), fill=(236, 216, 178))
    center(base, spr(key, st, 3, crop=True), x + 45, 152)
    lines = wrap(info['description'], K.F_SMALL(), 186)
    for i, ln in enumerate(lines[:4]):
        K.draw_text(base, (x + 100, 120 + i * 14), ln, K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (x + 100, 190), f'{info["species"]} · {info["type"]}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x, 214), '진화', K.F_TITLE(), K.TEXT, 'lm')
    evo_line(base, x + 34, 208, key, step=84 if info['max_stage'] == 3 else 100)
    stat_rows(base, x, 290, key, colw=144)
    button(base, x, 326, 282, 20, '내 동물에서 보기', 'green', icon='heart', f=K.F_SMALL())


def right_page_missing(base, key):
    info = CH[key]; x = 334; d = ImageDraw.Draw(base)
    K.draw_text(base, (x, 74), f'No.{no(key):02d}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x + 34, 76), '???', K.F_BIG(), K.TEXT_SOFT, 'lm')
    chips(base, x, 90, key, show_strength=False)
    d.rectangle((x, 112, x + 90, 200), fill=(196, 176, 150), outline=K.WOOD[2])
    im = spr(key, 1, 3, crop=True); center(base, silhouette(im), x + 45, 152); qmark(base, x + 45, 152)
    K.draw_text(base, (x + 100, 122), '아직 만나지 못한 동물', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (x + 100, 140), '부화하면 그림·이름·설명이', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x + 100, 154), '도감에 등록된다', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    d.rectangle((x + 100, 168, 616, 198), fill=(255, 246, 224), outline=K.WOOD[2])
    paste(base, BM.icon('egg_special' if info['rarity'] == 'special' else 'egg_basic', 1), (x + 106, 175))
    K.draw_text(base, (x + 126, 178), '만나는 곳: 상점 알 부화', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (x + 126, 191), '특수 부화 알 특급 60%' if info['rarity'] == 'special' else '기본 부화 알 · 특수 부화 알', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (x, 214), '진화', K.F_TITLE(), K.TEXT, 'lm')
    evo_line(base, x + 34, 208, key, step=84 if info['max_stage'] == 3 else 100)
    stat_rows(base, x, 290, key, colw=144, known=False)
    button(base, x, 326, 282, 20, '상점에서 알 사기', 'orange', icon='coin', f=K.F_SMALL())


def dex_A(out, sel, tab):
    base = BM.bg(); ribbon_fix(base)
    progress(base, 478, 31)
    book(base, tab); left_page(base, tab, sel)
    (right_page_owned if sel in OWNED else right_page_missing)(base, sel)
    BM.save(base, out)


def ribbon_fix(base):
    ribbon(base, 78, 33, 70, '도감', 'red')   # bg()가 그린 '가방' 리본 위에 덮어 그림


# ================= B: 30칸 수집 보드 =================
def dex_B(out, sel):
    base = BM.bg(); ribbon(base, 78, 33, 70, '도감', 'red')
    progress(base, 158, 31)
    d = ImageDraw.Draw(base)
    B.panel(base, 6, 56, 628, 210)
    # 열 머리
    K.draw_text(base, (204, 68), '일반 · 2단계까지', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    K.draw_text(base, (490, 68), '특급 · 3단계까지', K.F_SMALL(), (196, 140, 30), 'mm')
    d.line((345, 64, 345, 258), fill=K.WOOD[3])
    for r, role in enumerate(('dealer', 'tank', 'healer')):
        y = 78 + r * 60
        el = {'dealer': 'fire', 'tank': 'water', 'healer': 'wind'}[role]
        B.card(base, 14, y, 54, 56)
        text_mid(base, 41, y + 12, ROLE[role], K.F_TITLE(), K.TEXT)
        chip(base, 41 - (tl(ELEM[el], K.F_SMALL()) + 10) // 2, y + 22, ELEM[el], ELEM_C[el])
        own = sum(1 for k in ORDER if CH[k]['role'] == role and k in OWNED)
        text_mid(base, 41, y + 47, f'{own}/10', K.F_SMALL(), K.TEXT_SOFT)
        for rar, x0 in (('normal', 74), ('special', 352)):
            keys = [k for k in ORDER if CH[k]['role'] == role and CH[k]['rarity'] == rar]
            for c, k in enumerate(keys):
                cell(base, x0 + c * 54, y, 50, 56, k, sel=(k == sel), gold=(rar == 'special'))
    # 아래 정보 줄
    B.panel(base, 6, 270, 628, 86)
    info = CH[sel]; own = sel in OWNED; st = OWNED.get(sel, 1)
    d.rectangle((16, 280, 92, 346), fill=(255, 250, 236) if own else (196, 176, 150), outline=K.WOOD[2])
    im = spr(sel, st, 2, crop=True)
    if own: center(base, im, 54, 313)
    else: center(base, silhouette(im), 54, 313); qmark(base, 54, 313)
    K.draw_text(base, (102, 285), f'No.{no(sel):02d}', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (136, 287), info['stage_names'][st - 1] if own else '???', K.F_BIG(), K.TEXT if own else K.TEXT_SOFT, 'lm')
    chips(base, 102, 298, sel, show_strength=own)
    if own:
        K.draw_text(base, (102, 328), wrap(info['description'], K.F_SMALL(), 210)[0], K.F_SMALL(), K.TEXT, 'lm')
        K.draw_text(base, (102, 342), (wrap(info['description'], K.F_SMALL(), 210) + [''])[1], K.F_SMALL(), K.TEXT, 'lm')
    else:
        K.draw_text(base, (102, 328), '아직 만나지 못한 동물', K.F_SMALL(), K.TEXT, 'lm')
        K.draw_text(base, (102, 342), '만나는 곳: 상점 알 부화', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 진화 줄 (×1) + 능력치
    K.draw_text(base, (330, 284), '진화', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    evo_line(base, 356, 278, sel, step=46, n=1, label=False)
    stat_rows(base, 328, 318, sel, colw=148, gap=14, known=own)
    if own: button(base, 500, 278, 124, 34, '내 동물에서 보기', 'green', f=K.F_SMALL())
    else: button(base, 500, 278, 124, 34, '상점에서 알 사기', 'orange', icon='coin', f=K.F_SMALL())
    BM.save(base, out)


if __name__ == '__main__':
    import sys
    K.FONT_DIR = REPO / 'assets' / 'fonts'; B.SPR = REPO / 'assets' / 'sprites'
    o = Path(sys.argv[1] if len(sys.argv) > 1 else '../dex'); o.mkdir(exist_ok=True)
    dex_A(o / 'dex_A1_owned.png', 'dealer_special_02', '특급')
    dex_A(o / 'dex_A2_missing.png', 'dealer_special_03', '특급')
    dex_B(o / 'dex_B1_owned.png', 'tank_normal_02')
    dex_B(o / 'dex_B2_missing.png', 'healer_special_04')
    print('ok')
