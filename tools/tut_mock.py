"""새 게임 흐름 목업: 테크모 인사 → 첫 동료 고르기(일반 15 중 3) → 한 마리씩 맞이 → 지도 안내(간식·훈련·첫 전투) → 마무리."""
import json, math, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance
import uikit as K
import battle_mock as B
from ui_mock import paste, button, chip, ribbon, text_mid, gauge
import title5 as T5
import techmo

W, H = 640, 360
INK = K.INK
GAME = T5.GAME
CH = json.load(open(GAME / 'data' / 'characters.json', encoding='utf-8'))
NORMAL = [k for k, v in CH.items() if v['rarity'] == 'normal']
ROLE = {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}
ROLE_C = {'dealer': 'orange', 'tank': 'blue', 'healer': 'green'}
ELEM = {'fire': '불', 'water': '물', 'wind': '바람'}
ELEM_C = {'fire': 'red', 'water': 'blue', 'wind': 'green'}
ROLE_LINE = {'dealer': ('딜러는 적 전체를 한 번에 공격해.', '공격력이 높을수록 아프게 때린다!'),
             'tank': ('탱커는 튼튼해서 오래 버텨.', '아군 하나를 절대방어로 지켜 줄 수도 있어.'),
             'healer': ('힐러는 다친 아군을 회복시켜.', '힐러가 있으면 오래 싸울 수 있지!')}
SHOTS = GAME / 'saves' / 'screenshots' / 'fresh'   # 새 게임 실제 화면(map.png, animals.png)을 먼저 찍어 둘 것
PICK = ['dealer_normal_01', 'tank_normal_03', 'healer_normal_05']


def tl(t, f): return f.getlength(t)


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def shot(name):
    return Image.open(SHOTS / name).convert('RGBA').resize((W, H), Image.NEAREST)


def garden(dim=0):
    """표지 정원 (로고·메뉴 없이)"""
    L = T5.static_layers()
    base = L['back'].copy()
    for (x, y, w) in ((24, 40, 70), (470, 34, 96), (300, 26, 50), (150, 128, 44)):
        T5.puff_cloud(base, x, y, w)
    T5.float_island(base, 84, 62, 0, .8); T5.float_island(base, 566, 56, .4, .75, flip=True)
    base.alpha_composite(L['mid']); base.alpha_composite(L['front'])
    if dim: base.alpha_composite(Image.new('RGBA', (W, H), (20, 14, 30, dim)))
    return base


# ---------------- 대화 상자 ----------------
def progress(base, label, n, total):
    """왼쪽 위 진행 칸: 글씨 + 점 (글씨 폭에 맞춤)"""
    f = K.F_BODY(); tw = int(tl(label, f))
    w = 8 + tw + 8 + total * 9 + 6
    B.card(base, 8, 32, w, 22)
    K.draw_text(base, (16, 43), label, f, K.TEXT, 'lm')
    d = ImageDraw.Draw(base)
    for i in range(total):
        x = 16 + tw + 8 + i * 9
        d.rectangle((x, 40, x + 5, 45), fill=(250, 196, 60) if i < n else (150, 128, 104), outline=INK)


def dialog(base, lines, kind='talk', step=None, skip=True, name='테크모', top=False):
    y0 = 58 if top else 282                                        # top = 아래 화면을 가리키면 위쪽에
    B.panel(base, 8, y0, 624, 74)
    d = ImageDraw.Draw(base)
    d.rectangle((16, y0 + 8, 76, y0 + 66), fill=(206, 226, 240), outline=K.WOOD[2])
    face = techmo.frame(kind, 2).crop((0, 0, 64, 52))
    paste(base, face, (14, y0 + 12))
    chip(base, 84, y0 + 8, name, 'brown')
    for i, ln in enumerate(lines[:2]):
        K.draw_text(base, (86, y0 + 36 + i * 18), ln, K.F_TITLE(), K.TEXT, 'lm')
    text_mid(base, 606, y0 + 62, '▼ 클릭', K.F_SMALL(), K.TEXT_SOFT)
    if step:
        progress(base, '처음 안내', step[0], step[1])
    if skip:
        button(base, 556, 32, 76, 20, '건너뛰기', 'brown', f=K.F_BODY())


# ---------------- 1. 인사 ----------------
def welcome(out):
    base = garden(dim=60)
    d = ImageDraw.Draw(base)
    glow = Image.new('RGBA', (W, H)); gd = ImageDraw.Draw(glow)
    gd.ellipse((240, 70, 400, 250), fill=(255, 250, 220, 70)); base.alpha_composite(glow)
    t = techmo.frame('flap1_talk' if False else 'flap1', 4)
    paste(base, t, (320 - 64, 96))
    d.ellipse((276, 222, 364, 234), fill=(60, 90, 60))
    for (x, y) in ((250, 110), (392, 128), (270, 200), (380, 196)):
        d.line((x - 3, y, x + 3, y), fill=(255, 250, 200)); d.line((x, y - 3, x, y + 3), fill=(255, 250, 200))
    dialog(base, ['어서 와! 나는 이 섬의 안내원 테크모야.', '먼저 같이 지낼 동료 3마리를 골라 볼까?'], 'talk', skip=True)
    save(base, out)


# ---------------- 2. 첫 동료 고르기 ----------------
def team_notes(picked):
    roles = [CH[k]['role'] for k in picked]
    n = {r: roles.count(r) for r in ROLE}
    out = []
    for r, col in (('dealer', 'orange'), ('tank', 'blue'), ('healer', 'green')):
        if n[r]: out.append((col, f'{ROLE[r]} {n[r]}'))
    warn = []
    if picked and not n['healer']: warn.append('힐러 없음 · 회복 못 함')
    if picked and not n['tank']: warn.append('탱커 없음 · 지켜 줄 동료 없음')
    return out, warn


def pick(out, picked, focus):
    base = garden(dim=150)
    B.header(base, '1일차 · 낮 06:00 · 맑음', '300')
    ribbon(base, 12, 33, 110, '첫 동료 고르기', 'red')
    button(base, 556, 32, 76, 20, '건너뛰기', 'brown', f=K.F_BODY())
    # 테크모 한 줄 안내
    paste(base, techmo.frame('idle', 1), (132, 26))
    B.card(base, 166, 32, 290, 22)
    K.draw_text(base, (174, 43), '일반 동물 중 마음에 드는 3마리를 골라!', K.F_BODY(), K.TEXT, 'lm')
    d = ImageDraw.Draw(base)
    # 왼쪽: 일반 15마리 (역할 3줄 × 5)
    B.panel(base, 8, 58, 352, 298)
    for r, role in enumerate(('dealer', 'tank', 'healer')):
        y = 66 + r * 95
        keys = [k for k in NORMAL if CH[k]['role'] == role]
        el = CH[keys[0]]['element']
        cw = chip(base, 16, y, ROLE[role], ROLE_C[role]); chip(base, 16 + cw + 3, y, ELEM[el], ELEM_C[el])
        for c, k in enumerate(keys):
            x = 16 + c * 68; cy = y + 19
            on = k in picked
            d.rectangle((x, cy, x + 62, cy + 70), fill=(255, 246, 224) if on else K.PAPER[2], outline=INK)
            d.line((x + 1, cy + 1, x + 61, cy + 1), fill=(255, 255, 255))
            im = B.spr(k, 1, 2); bb = im.getbbox(); im = im.crop(bb)
            paste(base, im, (x + 31 - im.width // 2, cy + 31 - im.height // 2))
            text_mid(base, x + 31, cy + 61, CH[k]['name'], K.F_SMALL(), K.TEXT)
            if on:
                i = picked.index(k) + 1
                d.ellipse((x + 46, cy + 3, x + 59, cy + 16), fill=(250, 196, 60), outline=INK)
                text_mid(base, x + 53, cy + 10, str(i), K.F_SMALL(), INK)
            if k == focus: B.corners(base, x - 2, cy - 2, x + 64, cy + 72)
    # 오른쪽: 내 팀 + 고른 동물 정보 + 조합
    B.panel(base, 364, 58, 268, 298)
    K.draw_text(base, (376, 72), f'나의 첫 동료 {len(picked)} / 3', K.F_TITLE(), K.TEXT, 'lm')
    for i in range(3):
        x = 376 + i * 82; y = 82
        if i < len(picked):
            k = picked[i]
            d.rectangle((x, y, x + 76, y + 62), fill=(214, 236, 196), outline=K.WOOD[2])
            im = B.spr(k, 1, 2); im = im.crop(im.getbbox()); paste(base, im, (x + 38 - im.width // 2, y + 25 - im.height // 2))
            lab = ROLE[CH[k]['role']]
            chip(base, x + 38 - (int(tl(lab, K.F_SMALL())) + 10) // 2, y + 44, lab, ROLE_C[CH[k]['role']])
            button(base, x + 62, y - 4, 16, 14, '', 'red')
            d = ImageDraw.Draw(base)
            d.line((x + 66, y, x + 73, y + 6), fill=(255, 255, 255)); d.line((x + 73, y, x + 66, y + 6), fill=(255, 255, 255))
        else:
            for xx in range(x, x + 76, 4): d.point((xx, y), fill=K.WOOD[2]); d.point((xx, y + 62), fill=K.WOOD[2])
            for yy in range(y, y + 62, 4): d.point((x, yy), fill=K.WOOD[2]); d.point((x + 76, yy), fill=K.WOOD[2])
            text_mid(base, x + 38, y + 31, '빈 자리', K.F_SMALL(), K.TEXT_SOFT)
    info = CH[focus]
    d.line((374, 154, 622, 154), fill=K.PAPER[0])
    K.draw_text(base, (376, 166), info['name'], K.F_TITLE(), K.TEXT, 'lm')
    x2 = 376 + int(tl(info['name'], K.F_TITLE())) + 6
    x2 += chip(base, x2, 158, ROLE[info['role']], ROLE_C[info['role']]) + 3
    chip(base, x2, 158, info.get('strength', '') if info.get('strength') not in (None, '', '기준') else '균형', 'brown')
    st = info['base_stats']
    for i, (s, l) in enumerate((('hp', '체력'), ('attack', '공격'), ('defense', '방어'), ('agility', '민첩'))):
        x = 376 + (i % 2) * 124; y = 180 + (i // 2) * 14
        K.draw_text(base, (x, y + 5), l, K.F_SMALL(), K.TEXT_SOFT, 'lm')
        gauge(base, x + 24, y, 62, 9, st[s], 120, ROLE_C[info['role']])
        K.draw_text(base, (x + 116, y + 5), str(st[s]), K.F_SMALL(), K.TEXT, 'rm')
    d.line((374, 214, 622, 214), fill=K.PAPER[0])
    K.draw_text(base, (376, 225), '팀 조합', K.F_TITLE(), K.TEXT, 'lm')
    good, warn = team_notes(picked)
    x = 376
    for col, t in good: x += chip(base, x, 234, t, col) + 3
    y = 254
    for t in warn: chip(base, 376, y, t, 'red'); y += 18
    if not warn and len(picked) == 3: chip(base, 376, y, '균형 잡힌 팀!', 'gold'); y += 18
    K.draw_text(base, (376, 302), '조합은 나중에 알을 부화해서 바꿀 수 있어', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    if len(picked) == 3: button(base, 376, 318, 244, 30, '이 동료들과 시작', 'green', icon='heart', f=K.F_TITLE())
    else: button(base, 376, 318, 244, 30, f'{3 - len(picked)}마리 더 고르기', 'gray', f=K.F_TITLE())
    save(base, out)


# ---------------- 3. 한 마리씩 맞이 ----------------
def meet(out, idx):
    k = PICK[idx]; info = CH[k]; role = info['role']
    base = garden(dim=110)
    d = ImageDraw.Draw(base)
    lay = Image.new('RGBA', (W, H)); ld = ImageDraw.Draw(lay)                 # 스포트라이트
    ld.polygon([(290, 26), (350, 26), (420, 250), (220, 250)], fill=(255, 250, 220, 50)); base.alpha_composite(lay)
    d = ImageDraw.Draw(base)
    d.ellipse((248, 226, 392, 248), fill=(255, 246, 200), outline=(220, 196, 140))
    im = B.spr(k, 1, 4); paste(base, im, (320 - im.width // 2, 236 - im.height + 8))
    for (x, y) in ((248, 120), (398, 138), (262, 196), (386, 206)):
        d.line((x - 3, y, x + 3, y), fill=(255, 250, 200)); d.line((x, y - 3, x, y + 3), fill=(255, 250, 200))
    # 이름 카드 (오른쪽)
    B.panel(base, 436, 96, 188, 118)
    K.draw_text(base, (448, 114), info['name'], K.F_BIG(), K.TEXT, 'lm')
    x = 448; x += chip(base, x, 126, ROLE[role], ROLE_C[role]) + 3; chip(base, x, 126, ELEM[info['element']], ELEM_C[info['element']])
    for i, (s, l, ic) in enumerate((('hp', '체력', 'heart'), ('attack', '공격', 'sword'), ('defense', '방어', 'shield'), ('agility', '민첩', 'wing'))):
        y = 150 + i * 14
        K.draw_text(base, (448, y + 5), l, K.F_SMALL(), K.TEXT_SOFT, 'lm')
        gauge(base, 476, y, 100, 9, info['base_stats'][s], 120, ROLE_C[role])
        K.draw_text(base, (612, y + 5), str(info['base_stats'][s]), K.F_SMALL(), K.TEXT, 'rm')
    # 테크모 (왼쪽, 작게 소개하는 몸짓)
    paste(base, techmo.frame('flap2', 2), (120, 172))
    # 왼쪽 위 "첫 동료 1/3"
    progress(base, '첫 동료', idx + 1, 3)
    button(base, 556, 32, 76, 20, '건너뛰기', 'brown', f=K.F_BODY())
    a, b = ROLE_LINE[role]
    dialog(base, [f'{info["name"]}{"과" if (ord(info["name"][-1]) - 0xAC00) % 28 else "와"} 함께! {a}', b], 'talk', skip=False)
    save(base, out)


# ---------------- 4. 지도·화면 안내 ----------------
def spotlight(base, rect, arrow='down', step=(1, 5), lines=('', ''), top=False):
    x0, y0, x1, y1 = rect
    shade = Image.new('RGBA', (W, H), (10, 8, 20, 150)); sd = ImageDraw.Draw(shade)
    sd.rounded_rectangle(rect, 6, fill=(0, 0, 0, 0)); base.alpha_composite(shade)
    d = ImageDraw.Draw(base)
    for i in range(2): d.rounded_rectangle((x0 - 2 - i, y0 - 2 - i, x1 + 2 + i, y1 + 2 + i), 7, outline=(255, 214, 80))
    Y = (255, 214, 80)
    if arrow == 'left':                                                    # 왼쪽에서 오른쪽을 가리킴
        cy = (y0 + y1) // 2
        d.polygon([(x0 - 6, cy), (x0 - 18, cy - 9), (x0 - 18, cy + 9)], fill=Y, outline=INK)
        d.rectangle((x0 - 34, cy - 4, x0 - 18, cy + 4), fill=Y, outline=INK)
    else:                                                                   # 위에서 아래로
        cx = (x0 + x1) // 2
        d.polygon([(cx, y0 - 6), (cx - 9, y0 - 18), (cx + 9, y0 - 18)], fill=Y, outline=INK)
        d.rectangle((cx - 4, y0 - 32, cx + 4, y0 - 18), fill=Y, outline=INK)
    dialog(base, list(lines), 'talk', step=step, top=top)


def tut(out, rect, arrow, step, lines, shot_name='map.png', top=False):
    base = shot(shot_name)
    spotlight(base, rect, arrow, step, lines, top)
    save(base, out)


def done(out):
    base = shot('map.png')
    base.alpha_composite(Image.new('RGBA', (W, H), (10, 8, 20, 80)))
    d = ImageDraw.Draw(base)
    paste(base, techmo.frame('flap1', 3), (320 - 48, 120))
    for (x, y) in ((280, 120), (370, 130), (290, 190), (360, 196)):
        d.line((x - 3, y, x + 3, y), fill=(255, 250, 200)); d.line((x, y - 3, x, y + 3), fill=(255, 250, 200))
    dialog(base, ['이제 자유롭게 섬을 돌아다녀 봐!', '궁금하면 설정의 도움말을 열어 줘. 그럼 안녕~'], 'talk', step=(5, 5), skip=False)
    save(base, out)


if __name__ == '__main__':
    K.FONT_DIR = GAME / 'assets' / 'fonts'; B.SPR = GAME / 'assets' / 'sprites'
    o = Path(sys.argv[1]); o.mkdir(exist_ok=True)
    welcome(o / 'n1_welcome.png')
    pick(o / 'n2_pick.png', ['dealer_normal_01', 'tank_normal_03'], 'tank_normal_03')
    pick(o / 'n3_pick_done.png', PICK, 'healer_normal_05')
    pick(o / 'n3b_pick_no_healer.png', ['dealer_normal_01', 'dealer_normal_04', 'tank_normal_03'], 'dealer_normal_04')
    for i in range(3): meet(o / f'n4_meet_{i + 1}.png', i)
    tut(o / 'n5_tut_bag.png', (586, 145, 632, 196), 'left', (1, 5), ('배고픈 친구에겐 간식을 주자.', '오른쪽 메뉴의 가방을 눌러 봐!'))
    tut(o / 'n6_tut_animals.png', (586, 44, 632, 96), 'left', (2, 5), ('내 동물에서는 능력치를 훈련할 수 있어.', '네 능력치가 모두 MAX가 되면 진화!'))
    tut(o / 'n6b_tut_train.png', (298, 282, 622, 310), 'down', (3, 5), ('훈련할 능력치를 고르고 난이도를 눌러.', '훈련은 동시에 3마리까지 할 수 있어.'), 'animals.png', top=True)
    tut(o / 'n7_tut_battle.png', (470, 190, 576, 268), 'down', (4, 5), ('준비가 됐으면 전투장으로!', '첫 상대는 뉴비 스테이지. 져도 걱정 마.'))
    done(o / 'n8_done.png')
    print('ok')
