"""전투장 화면 후보 목업 (640x360 논리 → 1280x720). A/B/C 전투 화면 + 스테이지 선택."""
import random, sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
from ui_mock import paste, button, gauge, chip, ribbon

W, H = 640, 360
SPR = None
ENEMY_DIR = Path('battle/enemies')
INK = K.INK


# ---------------- 공통 ----------------
def spr(key, stage=1, scale=2, flip=False, dim=False):
    path = (SPR.parent.parent / 'enemies' / f'{key}.png') if key.startswith(('m_', 'boss_')) else SPR / f'{key}_s{stage}.png'
    if key.startswith(('m_', 'boss_')): path = ENEMY_DIR / f'{key}.png'
    im = Image.open(path).convert('RGBA'); nat = im.width // 4
    im = im.resize((nat, nat), Image.NEAREST)
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if dim:
        px = im.load()
        for y in range(nat):
            for x in range(nat):
                r, g, b, a = px[x, y]
                if a:
                    v = (r + g + b) // 3
                    px[x, y] = ((v + 60) // 2 + 40, (v + 60) // 2 + 36, (v + 60) // 2 + 40, a)
    return im.resize((nat * scale, nat * scale), Image.NEAREST)


def outline_text(base, xy, s, f, fill, anchor='mm'):
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
        K.draw_text(base, (xy[0] + dx, xy[1] + dy), s, f, INK, anchor)
    K.draw_text(base, xy, s, f, fill, anchor)


def header(base, txt='3일차 · 낮 14:20 · 맑음', coins='4,200'):
    d = ImageDraw.Draw(base)
    d.rectangle((0, 0, W, 25), fill=K.WOOD[2])
    for x in range(0, W, 40):
        d.line((x, 2, x, 23), fill=K.WOOD[1])
    d.line((0, 1, W, 1), fill=K.WOOD[4]); d.line((0, 24, W, 24), fill=K.WOOD[1]); d.line((0, 25, W, 25), fill=INK)
    K.draw_text(base, (12, 13), 'EvoTail', K.F_TITLE(), (255, 236, 190), 'lm', K.WOOD[0])
    for (x0, x1, ic, t) in ((232, 408, 'sun', txt), (540, 630, 'coin', coins)):
        c, m = K.piece_card()
        paste(base, K.nine(c, m, x1 - x0, 18), (x0, 4))
        paste(base, K.icon(ic), (x0 + 5, 7))
        if ic == 'coin':
            K.draw_text(base, (x1 - 7, 13), t, K.F_TITLE(), K.TEXT, 'rm')
        else:
            K.draw_text(base, (x0 + 21, 13), t, K.F_BODY(), K.TEXT, 'lm')


def card(base, x, y, w, h, sel=False):
    c, m = K.piece_card(sel)
    paste(base, K.nine(c, m, w, h), (x, y))


def panel(base, x, y, w, h):
    p, m = K.piece_panel()
    paste(base, K.nine(p, m, w, h), (x, y))


def hp_col(v, mx):
    r = v / mx
    return 'green' if r > .5 else 'orange' if r > .25 else 'red'


def corners(base, x0, y0, x1, y1, col=(255, 214, 90)):
    d = ImageDraw.Draw(base)
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        for t in (0, 1):
            d.line((cx, cy + sy * t, cx + sx * 6, cy + sy * t), fill=INK if t else col)
            d.line((cx + sx * t, cy, cx + sx * t, cy + sy * 6), fill=INK if t else col)
        d.line((cx, cy, cx + sx * 5, cy), fill=col); d.line((cx, cy, cx, cy + sy * 5), fill=col)


# ---------------- 경기장 배경 ----------------
def arena_bg(top=26, horizon=118, night=False):
    rnd = random.Random(7)
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    # 하늘
    sky = [(150, 206, 240), (168, 216, 244), (186, 226, 247), (204, 234, 249)]
    for y in range(top, 72):
        t = (y - top) / (72 - top) * 3
        i = int(t); f = t - i
        for x in range(W):
            c = sky[min(3, i + (1 if ((x + y) % 2 == 0 and f > .5) else 0))]
            im.putpixel((x, y), c + (255,))
    for cx, cy in ((80, 40), (300, 34), (520, 46)):
        for k, (ox, oy, r) in enumerate(((0, 0, 9), (10, -3, 11), (22, 0, 8), (-9, 2, 6))):
            d.ellipse((cx + ox - r, cy + oy - r // 2 - 2, cx + ox + r, cy + oy + r // 2 + 2), fill=(255, 255, 255))
        d.line((cx - 15, cy + 7, cx + 30, cy + 7), fill=(214, 230, 242))
    # 관중석 (계단식 돌)
    stone = [(92, 88, 104), (120, 116, 132), (148, 144, 158), (176, 172, 184)]
    d.rectangle((0, 60, W, horizon - 22), fill=stone[1])
    for row, y in enumerate(range(62, horizon - 24, 8)):
        d.line((0, y, W, y), fill=stone[3]); d.line((0, y + 7, W, y + 7), fill=stone[0])
        for x in range(-8 + (row % 2) * 6, W, 4):                                # 관중
            if rnd.random() < .78:
                col = rnd.choice([(232, 96, 86), (90, 150, 220), (250, 204, 70), (120, 190, 110), (240, 160, 190), (255, 246, 224), (180, 120, 80)])
                d.rectangle((x, y + 2, x + 2, y + 4), fill=col)
                d.point((x + 1, y + 1), fill=(236, 196, 160))
    # 앞 벽 (벽돌)
    wy0, wy1 = horizon - 22, horizon
    d.rectangle((0, wy0, W, wy1), fill=stone[2])
    for r, y in enumerate(range(wy0, wy1, 6)):
        d.line((0, y, W, y), fill=stone[0])
        for x in range((r % 2) * 10, W, 20):
            d.line((x, y, x, y + 5), fill=stone[0])
            d.line((x + 1, y + 1, x + 18, y + 1), fill=stone[3])
    d.line((0, wy0, W, wy0), fill=INK); d.line((0, wy1, W, wy1), fill=INK)
    # 깃발
    for i, x in enumerate(range(40, W, 112)):
        col = [(220, 92, 80), (90, 150, 220), (250, 204, 70)][i % 3]
        dk = tuple(max(0, c - 60) for c in col)
        d.rectangle((x, wy0 + 2, x + 13, wy0 + 15), fill=col, outline=INK)
        d.polygon([(x, wy0 + 15), (x + 13, wy0 + 15), (x + 6, wy0 + 20)], fill=col, outline=INK)
        d.line((x + 2, wy0 + 4, x + 2, wy0 + 13), fill=tuple(min(255, c + 40) for c in col))
        d.rectangle((x + 4, wy0 + 6, x + 9, wy0 + 11), fill=dk)
    # 횃불
    for x in (96, 320, 544):
        d.rectangle((x, wy0 + 4, x + 3, wy1 - 2), fill=K.WOOD[1], outline=INK)
        d.ellipse((x - 3, wy0 - 6, x + 6, wy0 + 4), fill=(250, 150, 60))
        d.ellipse((x - 1, wy0 - 3, x + 4, wy0 + 3), fill=(255, 226, 120))
    # 모래 바닥
    sand = [(196, 160, 106), (214, 180, 124), (228, 196, 140), (240, 214, 162)]
    d.rectangle((0, wy1 + 1, W, H), fill=sand[2])
    for y in range(wy1 + 1, H):
        band = (y - wy1) // 24
        for x in range(W):
            n = rnd.random()
            if n < .05:
                im.putpixel((x, y), sand[1] + (255,))
            elif n < .07:
                im.putpixel((x, y), sand[3] + (255,))
        if band % 2 == 0 and y % 3 == 0:
            pass
    d.line((0, wy1 + 1, W, wy1 + 1), fill=sand[0])
    d.line((0, wy1 + 2, W, wy1 + 2), fill=sand[1])
    # 가운데 원
    cy = (wy1 + H) // 2 + 10
    d.ellipse((120, cy - 52, 520, cy + 52), outline=sand[3])
    d.ellipse((121, cy - 51, 519, cy + 51), outline=sand[3])
    d.line((320, wy1 + 4, 320, H), fill=sand[3])
    for _ in range(40):
        x, y = rnd.randrange(W), rnd.randrange(wy1 + 6, H)
        d.rectangle((x, y, x + 1, y), fill=(170, 150, 130)); d.point((x, y - 1), fill=sand[3])
    if night:
        ov = Image.new('RGBA', (W, H), (30, 30, 80, 110)); im.alpha_composite(ov)
    return im


def shadow(base, cx, cy, w=36):
    ov = Image.new('RGBA', (W, H)); ImageDraw.Draw(ov).ellipse((cx - w // 2, cy - 5, cx + w // 2, cy + 5), fill=(120, 84, 50, 120))
    base.alpha_composite(ov)


def fighter(base, f, cx, foot, flip, sel=False, target=False, small_bar=True, scale=2, name=False):
    s = (46 if f.get('boss') else 28) * scale
    shadow(base, cx, foot, int(s * .55))
    dead = f['hp'] <= 0
    paste(base, spr(f['key'], f.get('stage', 1), scale, flip, dim=dead), (cx - s // 2, foot - s + 2))
    if sel:
        corners(base, cx - s // 2 - 3, foot - s - 2, cx + s // 2 + 3, foot + 6)
    if target:
        corners(base, cx - s // 2 - 3, foot - s - 2, cx + s // 2 + 3, foot + 6, (240, 90, 80))
    if small_bar:
        y = foot - s - 8
        if name:
            K.draw_text(base, (cx, y - 6), f['name'], K.F_SMALL(), (255, 250, 236), 'mm', INK)
        gauge(base, cx - 22, y, 44, 8, f['hp'], f['max'], hp_col(f['hp'], f['max']))
    tags = f.get('tags', [])
    tx = cx - 26
    for t, c in tags:
        tx += chip(base, tx, foot + 8, t, c) + 2


def dmg(base, x, y, s, col=(255, 236, 120), f=None):
    outline_text(base, (x, y), s, f or K.F_BIG(), col)


PLAYER = [
    {'key': 'dealer_special_02', 'stage': 2, 'name': '불꽃매', 'hp': 248, 'max': 310, 'role': 'dealer'},
    {'key': 'tank_normal_01', 'stage': 1, 'name': '물방울수달', 'hp': 300, 'max': 410, 'role': 'tank'},
    {'key': 'healer_normal_01', 'stage': 1, 'name': '산들오리', 'hp': 96, 'max': 230, 'role': 'healer'},
]
ENEMY = [
    {'key': 'm_water_clam', 'stage': 1, 'name': '조개 기사', 'hp': 352, 'max': 400, 'role': 'tank'},
    {'key': 'boss_silver', 'stage': 1, 'name': '은빛 기사', 'hp': 410, 'max': 620, 'role': 'dealer', 'boss': True},
    {'key': 'm_wind_puff', 'stage': 1, 'name': '민들레 솜털', 'hp': 120, 'max': 240, 'role': 'healer'},
]


def turn_ribbon(base, x, y, text='2라운드 · 내 차례', acts=1):
    ribbon(base, x, y, 128, text, 'red')
    K.draw_text(base, (x + 136, y + 9), '행동', K.F_SMALL(), (255, 250, 236), 'lm', INK)
    for i in range(2):
        cx = x + 162 + i * 12
        d = ImageDraw.Draw(base)
        d.rectangle((cx, y + 4, cx + 8, y + 12), fill=(250, 204, 70) if i < 2 - acts else (90, 70, 60), outline=INK)
        if i < 2 - acts:
            d.point((cx + 2, y + 6), fill=(255, 246, 200))
    K.draw_text(base, (x + 188, y + 9), f'{acts}/2 남음', K.F_SMALL(), (255, 250, 236), 'lm', INK)


def log_lines(base, x, y, lines, gap=13, w=None):
    for i, (t, c) in enumerate(lines):
        K.draw_text(base, (x, y + i * gap), t, K.F_SMALL(), c, 'lm')


LOG = [('2R · 불꽃매의 화염 폭풍! 적 전체에 피해', K.TEXT),
       ('  야생 불꽃고양이 쓰러짐', K.BTN['red'][1]),
       ('  야생 물방울소라게 -48 (상성 0.9배)', K.TEXT_SOFT),
       ('적 · 산들올빼미가 소라게를 회복 +60', K.BTN['green'][1])]


# ---------------- A: 옆에서 보기 + 아래 명령창 ----------------
def cand_a(out):
    base = arena_bg(); header(base)
    button(base, 8, 31, 70, 20, '도망가기', 'brown', icon='back', f=K.F_SMALL())
    turn_ribbon(base, 216, 32)
    K.draw_text(base, (628, 41), '실버 대회 · 전투력 500', K.F_SMALL(), (255, 250, 236), 'rm', INK)
    # 아군 (왼쪽) / 적 (오른쪽) 지그재그 대형
    pos_p = [(200, 214), (130, 236), (60, 214)]
    pos_e = [(440, 214), (510, 236), (580, 214)]
    PLAYER[0]['tags'] = []; PLAYER[1]['tags'] = [('절대방어', 'blue')]; PLAYER[2]['tags'] = [('쿨타임 1', 'gray')]
    ENEMY[0]['tags'] = [('방어', 'blue')]
    for i in (0, 2, 1):
        fighter(base, PLAYER[i], *pos_p[i], flip=False, sel=(i == 0))
    for i in (0, 2, 1):
        fighter(base, ENEMY[i], *pos_e[i], flip=True)
    dmg(base, 440, 136, '-48')
    outline_text(base, (510, 158), 'KO', K.F_BIG(), (240, 110, 100))
    dmg(base, 580, 136, '-71')
    # 아래 명령창
    panel(base, 6, 274, 628, 82)
    card(base, 16, 284, 150, 62, True)
    paste(base, spr('dealer_special_02', 2, 1), (22, 290))
    K.draw_text(base, (54, 296), '불꽃매', K.F_TITLE(), K.TEXT, 'lm')
    chip(base, 54, 304, '딜러', 'orange'); chip(base, 86, 304, '불', 'red')
    gauge(base, 24, 322, 106, 8, 248, 310, 'green')
    K.draw_text(base, (134, 326), '248', K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (24, 338), '공 182 · 방 70 · 민 140', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 176, 284, 96, 28, '공격', 'orange', icon='sword', sub=None)
    button(base, 276, 284, 116, 28, '화염 폭풍', 'purple', 'hover', sub=None)
    K.draw_text(base, (334, 320), '적 전체 · 쓰면 1턴 쉼', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 176, 318, 96, 26, '방어', 'blue', icon='shield')
    button(base, 396, 284, 82, 28, '턴 넘기기', 'brown', f=K.F_SMALL())
    # 기록
    card(base, 486, 284, 140, 62)
    K.draw_text(base, (494, 293), '전투 기록', K.F_TITLE(), K.TEXT, 'lm')
    for i, (t, c) in enumerate(LOG[:3]):
        K.draw_text(base, (494, 307 + i * 12), t[:13] + ('…' if len(t) > 13 else ''), K.F_SMALL(), c, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- B: 원근 + 아래 팀 카드 3장 ----------------
def cand_b(out):
    base = arena_bg(horizon=104); header(base)
    button(base, 8, 31, 70, 20, '도망가기', 'brown', icon='back', f=K.F_SMALL())
    turn_ribbon(base, 216, 32)
    K.draw_text(base, (628, 41), '실버 대회 · 전투력 500', K.F_SMALL(), (255, 250, 236), 'rm', INK)
    # 적: 뒤쪽(작게, 1배 반) → 2배, 아군: 앞쪽 3배
    for i, cx in enumerate((236, 320, 404)):
        e = dict(ENEMY[i]); e['tags'] = [('방어', 'blue')] if i == 0 else []
        fighter(base, e, cx, 172, flip=False, target=(i == 2))
    dmg(base, 236, 96, '-48')
    outline_text(base, (320, 118), 'KO', K.F_BIG(), (240, 110, 100))
    for i, cx in enumerate((200, 320, 440)):
        p = PLAYER[i]
        shadow(base, cx, 236, 44)
        paste(base, spr(p['key'], p['stage'], 3, flip=False), (cx - 42, 236 - 84 + 2))
        if i == 0:
            corners(base, cx - 45, 236 - 86, cx + 45, 242)
    # 기록 한 줄
    card(base, 120, 244, 400, 18)
    K.draw_text(base, (128, 253), '▶ 산들오리를 고르면 회복할 아군을 누를 수 있어요', K.F_SMALL(), K.TEXT, 'lm')
    # 팀 카드 3장
    for i, x in enumerate((8, 216, 424)):
        p = PLAYER[i]; done = i == 1
        card(base, x, 266, 208, 90, i == 0)
        paste(base, spr(p['key'], p['stage'], 1, dim=done), (x + 6, 272))
        K.draw_text(base, (x + 38, 280), p['name'], K.F_TITLE(), K.TEXT if not done else K.TEXT_SOFT, 'lm')
        chip(base, x + 38, 288, {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}[p['role']], K.ROLE[p['role']])
        gauge(base, x + 108, 278, 72, 8, p['hp'], p['max'], hp_col(p['hp'], p['max']))
        K.draw_text(base, (x + 200, 282), f"{p['hp']}", K.F_SMALL(), K.TEXT, 'rm')
        if done:
            chip(base, x + 108, 290, '행동 완료', 'gray')
            K.draw_text(base, (x + 104, 326), '이번 턴은 끝났어요', K.F_SMALL(), K.TEXT_SOFT, 'mm')
            continue
        sp = {'dealer': ('화염 폭풍', '적 전체'), 'tank': ('절대방어', '아군 1'), 'healer': ('회복 +100', '아군 1')}[p['role']]
        cool = i == 2
        button(base, x + 6, 306, 62, 22, '공격', 'orange', f=K.F_SMALL(), icon='sword')
        button(base, x + 72, 306, 76, 22, sp[0], 'purple', 'disabled' if cool else 'normal', f=K.F_SMALL())
        button(base, x + 152, 306, 50, 22, '방어', 'blue', f=K.F_SMALL())
        K.draw_text(base, (x + 110, 336), '쿨타임 · 다음 턴에 사용' if cool else sp[1] + ' · 쓰면 1턴 쉼', K.F_SMALL(), K.TEXT_SOFT, 'mm')
        K.draw_text(base, (x + 8, 346), '', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- C: 넓은 경기장 + 오른쪽 기록판 + 말풍선 메뉴 ----------------
def cand_c(out):
    base = arena_bg(); header(base)
    button(base, 8, 31, 70, 20, '도망가기', 'brown', icon='back', f=K.F_SMALL())
    turn_ribbon(base, 150, 32)
    pos_p = [(130, 196), (60, 246), (150, 300)]
    pos_e = [(350, 196), (420, 246), (330, 300)]
    PLAYER[0]['tags'] = []; PLAYER[1]['tags'] = []; PLAYER[2]['tags'] = []
    for i in (0, 1, 2):
        fighter(base, PLAYER[i], *pos_p[i], flip=False, sel=(i == 2))
    for i in (0, 1, 2):
        e = dict(ENEMY[i]); e['tags'] = [('방어', 'blue')] if i == 0 else []
        fighter(base, e, *pos_e[i], flip=True)
    # 고른 동물 옆 행동 메뉴
    mx, my = 186, 236
    card(base, mx, my, 104, 76)
    d = ImageDraw.Draw(base)
    d.polygon([(mx, my + 52), (mx - 6, my + 58), (mx + 1, my + 60)], fill=K.PAPER[2], outline=INK)
    K.draw_text(base, (mx + 8, my + 9), '산들오리', K.F_TITLE(), K.TEXT, 'lm')
    for j, (ic, t, sub, st) in enumerate((('sword', '공격', '적 1', 'normal'), ('heart', '회복', '+100', 'hover'), ('shield', '방어', '피해 50%', 'normal'))):
        y = my + 18 + j * 18
        if st == 'hover':
            d.rectangle((mx + 4, y - 1, mx + 99, y + 15), fill=(255, 226, 150))
        paste(base, K.icon(ic), (mx + 8, y + 1))
        K.draw_text(base, (mx + 24, y + 7), t, K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (mx + 98, y + 7), sub, K.F_SMALL(), K.TEXT_SOFT, 'rm')
    outline_text(base, (60, 160), '+100', K.F_BIG(), (140, 230, 140))
    K.draw_text(base, (60, 174), '누르면 회복', K.F_SMALL(), (255, 250, 236), 'mm', INK)
    corners(base, 60 - 31, 246 - 58, 60 + 31, 252, (120, 220, 120))
    # 오른쪽 기록판
    panel(base, 470, 30, 164, 326)
    ribbon(base, 482, 40, 64, '실버', 'brown')
    K.draw_text(base, (552, 49), '대회 · 500', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (484, 70), '적 행동 방식: 규칙형', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    d.line((482, 80, 622, 80), fill=K.PAPER[0])
    K.draw_text(base, (484, 90), '전투 기록', K.F_TITLE(), K.TEXT, 'lm')
    lines = [('1R', '불꽃매 → 소라게 -62', K.TEXT), ('1R', '수달 절대방어 (오리)', K.BTN['blue'][1]),
             ('적', '고양이 → 수달 -0 막음', K.TEXT_SOFT), ('적', '올빼미 회복 +60', K.BTN['green'][1]),
             ('2R', '불꽃매 화염 폭풍!', K.BTN['orange'][1]), ('', '소라게 -48 · 올빼미 -71', K.TEXT),
             ('', '불꽃고양이 쓰러짐', K.BTN['red'][1])]
    for i, (r, t, c) in enumerate(lines):
        y = 106 + i * 15
        if r:
            chip(base, 482, y - 6, r, 'gray' if r == '적' else 'brown')
        K.draw_text(base, (506, y), t, K.F_SMALL(), c, 'lm')
    d.line((482, 222, 622, 222), fill=K.PAPER[0])
    K.draw_text(base, (484, 232), '남은 동물', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (484, 248), '내 팀 3 / 3', K.F_SMALL(), K.BTN['green'][1], 'lm')
    K.draw_text(base, (556, 248), '적 2 / 3', K.F_SMALL(), K.BTN['red'][1], 'lm')
    button(base, 482, 296, 140, 26, '턴 넘기기', 'brown', icon='back')
    K.draw_text(base, (552, 334), '행동 1번 남았어요', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- 스테이지 선택 + 팀 고르기 ----------------
STAGES = [('뉴비', 40, 'normal', True), ('쉬움', 150, 'normal', True), ('브론즈', 250, 'rank', True),
          ('보통', 400, 'normal', True), ('실버', 500, 'rank', None), ('어려움', 800, 'normal', False),
          ('골드', 900, 'rank', False), ('극악', 1100, 'normal', False), ('다이아몬드', 1200, 'rank', False)]


def stage_select(out, mapdir):
    from PIL import ImageEnhance
    base = Image.open(mapdir / 'map_day.png').convert('RGBA').resize((W, H), Image.NEAREST)
    base = ImageEnhance.Color(ImageEnhance.Brightness(base).enhance(.55)).enhance(.7)
    header(base)
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 92, '전투장', 'red')
    # 왼쪽: 단계 사다리
    panel(base, 8, 56, 170, 300)
    d = ImageDraw.Draw(base)
    for i, (lb, pw, mode, st) in enumerate(STAGES):
        y = 64 + i * 32
        sel = st is None
        if i < 8:
            d.line((30, y + 26, 30, y + 34), fill=K.WOOD[2], width=2)
        card(base, 16, y, 154, 28, sel)
        dot = K.BTN['green'][2] if st else (K.BTN['orange'][2] if sel else K.BTN['gray'][1])
        d.ellipse((24, y + 8, 36, y + 20), fill=dot, outline=INK)
        if st:
            d.line((27, y + 14, 29, y + 16), fill=(255, 255, 255)); d.line((29, y + 16, 33, y + 11), fill=(255, 255, 255))
        col = K.TEXT if st is not False else K.TEXT_SOFT
        K.draw_text(base, (42, y + 14), lb, K.F_TITLE(), col, 'lm')
        if mode == 'rank':
            chip(base, 108, y + 8, '대회', 'purple' if st is not False else 'gray')
        K.draw_text(base, (164, y + 14), f'{pw}', K.F_SMALL(), col, 'rm')
        if st is False:
            K.draw_text(base, (132, y + 14), '잠김', K.F_SMALL(), K.TEXT_SOFT, 'rm') if mode != 'rank' else None
    # 오른쪽: 미리보기
    panel(base, 186, 56, 448, 300)
    K.draw_text(base, (202, 74), '실버 대회', K.F_BIG(), K.TEXT, 'lm')
    x = 282
    for t, c in (('대회', 'purple'), ('전투력 500', 'brown'), ('규칙형 AI', 'blue')):
        x += chip(base, x, 68, t, c) + 3
    paste(base, K.icon('coin'), (520, 68)); K.draw_text(base, (534, 74), '첫 우승 800', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (202, 92), '규칙형: 체력이 낮은 동물을 먼저 노리고, 위험하면 회복해요', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 적 3
    for i, e in enumerate(ENEMY):
        x = 202 + i * 142
        card(base, x, 102, 136, 70)
        d.rectangle((x + 6, y := 108, x + 47, 149), fill=(236, 210, 160), outline=K.WOOD[2])
        im = spr(e['key'], e['stage'], 1, flip=True)
        if e.get('boss'): paste(base, im.crop((3, 2, 43, 42)), (x + 7, 109))
        else: paste(base, im, (x + 13, 114))
        nm = e['name']
        if e.get('boss'): chip(base, x + 86, 120, '보스', 'red')
        K.draw_text(base, (x + 52, 113), nm, K.F_TITLE(), K.TEXT, 'lm')
        chip(base, x + 52, 120, {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}[e['role']], K.ROLE[e['role']])
        K.draw_text(base, (x + 52, 143), f"체 {e['max']}", K.F_SMALL(), K.TEXT_SOFT, 'lm')
        K.draw_text(base, (x + 8, 161), '공 120 · 방 150 · 민 90', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 내 팀
    ribbon(base, 202, 180, 70, '내 팀', 'brown')
    K.draw_text(base, (280, 189), '3마리 · 아래에서 눌러 넣기/빼기', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, p in enumerate(PLAYER):
        x = 202 + i * 142
        card(base, x, 200, 136, 46, True)
        paste(base, spr(p['key'], p['stage'], 1), (x + 6, 209))
        K.draw_text(base, (x + 40, 213), p['name'], K.F_TITLE(), K.TEXT, 'lm')
        gauge(base, x + 40, 224, 64, 8, p['hp'], p['max'], 'green')
        K.draw_text(base, (x + 40, 239), '출전 가능', K.F_SMALL(), K.BTN['green'][1], 'lm')
        paste(base, K.icon('heart'), (x + 118, 207))
    # 후보 줄
    K.draw_text(base, (202, 258), '다른 동물', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    bench = [('tank_normal_02', '물방울거북', 'ok'), ('healer_special_01', '산들학', 'ok'), ('dealer_normal_01', '불씨여우', 'tired'),
             ('tank_special_03', '물방울가재', 'ok'), ('healer_normal_03', '산들햄스터', 'sick')]
    for i, (k, n, s) in enumerate(bench):
        x = 202 + i * 50
        card(base, x, 266, 46, 40)
        paste(base, spr(k, 1, 1, dim=(s != 'ok')), (x + 9, 270))
        if s != 'ok':
            chip(base, x + 4, 292, '피곤' if s == 'tired' else '아픔', 'gray')
    # 포션
    K.draw_text(base, (466, 258), '전투 전 포션 (전투 1번)', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, (t, n) in enumerate((('공격+100', 2), ('방어+100', 0))):
        x = 466 + i * 82
        card(base, x, 266, 78, 40, i == 0)
        K.draw_text(base, (x + 39, 280), t, K.F_TITLE(), K.TEXT if n else K.TEXT_SOFT, 'mm')
        K.draw_text(base, (x + 39, 295), f'{n}개 · 불꽃매' if i == 0 else '없음', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 466, 316, 158, 32, '출전!', 'red', icon='sword')
    K.draw_text(base, (202, 330), '이기면 피로도 +30 · 지면 +100', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); mapdir = Path(sys.argv[4])
    out.mkdir(exist_ok=True)
    cand_a(out / 'battle_A.png'); cand_b(out / 'battle_B.png'); cand_c(out / 'battle_C.png')
    stage_select(out / 'stage_select.png', mapdir)
    print('ok')


# ---------------- A 수정안 ----------------
FULL_LOG = [('1R', '불꽃매 → 조개 기사 공격 -62', K.TEXT), ('1R', '수달 → 오리에게 절대방어', K.BTN['blue'][1]),
            ('적', '은빛 기사 → 오리 공격, 막힘', K.TEXT_SOFT), ('적', '조개 기사 방어 자세', K.TEXT_SOFT),
            ('2R', '불꽃매 화염 폭풍! (적 전체)', K.BTN['orange'][1]), ('', '조개 기사 -48 (상성 0.9배)', K.TEXT),
            ('', '민들레 솜털 -71', K.TEXT), ('', '은빛 기사 -86', K.TEXT),
            ('적', '민들레 → 은빛 기사 회복 +60', K.BTN['green'][1]), ('적', '은빛 기사 → 수달 공격 -24', K.TEXT)]


def a_base(sel_idx):
    base = arena_bg(); header(base)
    button(base, 8, 31, 70, 20, '도망가기', 'brown', icon='back', f=K.F_SMALL())
    turn_ribbon(base, 216, 32)
    K.draw_text(base, (628, 41), '실버 대회 · 전투력 500', K.F_SMALL(), (255, 250, 236), 'rm', INK)
    return base


def a_bottom(base, who, actions, hint, log_rows=3):
    panel(base, 6, 274, 628, 82)
    card(base, 16, 284, 150, 62, True)
    paste(base, spr(who['key'], who['stage'], 1), (22, 290))
    K.draw_text(base, (54, 296), who['name'], K.F_TITLE(), K.TEXT, 'lm')
    role = {'dealer': ('딜러', '불', 'red'), 'tank': ('탱커', '물', 'blue'), 'healer': ('힐러', '바람', 'green')}[who['role']]
    x = 54 + chip(base, 54, 304, role[0], K.ROLE[who['role']]) + 2; chip(base, x, 304, role[1], role[2])
    gauge(base, 24, 322, 106, 8, who['hp'], who['max'], hp_col(who['hp'], who['max']))
    K.draw_text(base, (134, 326), str(who['hp']), K.F_SMALL(), K.TEXT, 'lm')
    K.draw_text(base, (24, 338), who.get('line', ''), K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for (bx, by, bw, bh, label, col, st, ic) in actions:
        button(base, bx, by, bw, bh, label, col, st, icon=ic)
    K.draw_text(base, (334, 320), hint, K.F_SMALL(), K.TEXT_SOFT, 'mm')
    button(base, 396, 284, 82, 28, '턴 넘기기', 'brown', f=K.F_SMALL())
    card(base, 486, 284, 140, 62)
    K.draw_text(base, (494, 293), '전투 기록', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (618, 293), '자세히 ▲', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    for i, (r, t, c) in enumerate(FULL_LOG[-log_rows:]):
        K.draw_text(base, (494, 307 + i * 12), (r + ' ' if r else '  ') + t[:11] + ('…' if len(t) > 11 else ''), K.F_SMALL(), c, 'lm')


POS_P = [(200, 214), (130, 236), (60, 214)]
POS_E = [(414, 214), (510, 240), (602, 214)]


def cand_a2_heal(out):
    """힐러를 고르고 '회복'을 누른 뒤 → 회복할 아군 고르기."""
    base = a_base(2)
    for f in PLAYER: f['tags'] = []
    PLAYER[0]['tags'] = [('행동 완료', 'gray')]
    for i in (0, 2, 1):
        fighter(base, PLAYER[i], *POS_P[i], flip=False, sel=(i == 2))
    for i in (0, 2, 1):
        e = dict(ENEMY[i]); e['tags'] = [('방어', 'blue')] if i == 0 else []
        fighter(base, e, *POS_E[i], flip=True, dim=None) if False else fighter(base, e, *POS_E[i], flip=True)
    # 아군 전부 초록 표시, 마우스 올린 수달은 노란 강조 + 미리보기
    for i, (cx, foot) in enumerate(POS_P):
        corners(base, cx - 31, foot - 58, cx + 31, foot + 6, (120, 220, 120))
    cx, foot = POS_P[1]
    corners(base, cx - 33, foot - 60, cx + 33, foot + 8, (255, 214, 90))
    y = foot - 56 - 8
    d = ImageDraw.Draw(base)
    # 회복 뒤 체력을 연한 초록으로 미리 보여주기
    p = PLAYER[1]; inner = 40
    a0 = int(inner * p['hp'] / p['max']); a1 = int(inner * min(p['max'], p['hp'] + 100) / p['max'])
    d.rectangle((cx - 22 + 2 + a0, y + 2, cx - 22 + 1 + a1, y + 5), fill=(190, 240, 170))
    outline_text(base, (cx, y - 12), '+100', K.F_BIG(), (140, 230, 140))
    # 안내 띠
    card(base, 196, 56, 248, 20)
    paste(base, K.icon('heart'), (204, 60))
    K.draw_text(base, (220, 66), '회복할 아군을 누르세요 · 취소는 ESC', K.F_BODY(), K.TEXT, 'lm')
    healer = dict(PLAYER[2]); healer['line'] = '공 60 · 방 60 · 민 60'
    a_bottom(base, healer, [
        (176, 284, 96, 28, '공격', 'orange', 'normal', 'sword'),
        (276, 284, 116, 28, '회복 +100', 'green', 'pressed', 'heart'),
        (176, 318, 96, 26, '방어', 'blue', 'normal', 'shield')], '아군 1마리 · 쓰면 1턴 쉼')
    # 마우스 커서
    _cursor(base, cx + 10, foot - 20)
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def cand_a2_attack(out):
    """딜러 '공격' → 공격할 적 고르기 (적 1마리)."""
    base = a_base(0)
    for f in PLAYER: f['tags'] = []
    for i in (0, 2, 1):
        fighter(base, PLAYER[i], *POS_P[i], flip=False, sel=(i == 0))
    for i in (0, 2, 1):
        e = dict(ENEMY[i]); e['tags'] = [('방어', 'blue')] if i == 0 else []
        fighter(base, e, *POS_E[i], flip=True)
    for i, (cx, foot) in enumerate(POS_E):
        if ENEMY[i]['hp'] > 0:
            hs = 48 if ENEMY[i].get("boss") else 31
            corners(base, cx - hs, foot - hs * 2 + 4, cx + hs, foot + 6, (240, 110, 100))
    cx, foot = POS_E[2]
    corners(base, cx - 33, foot - 60, cx + 33, foot + 8, (255, 214, 90))
    # 이름 말풍선 (마우스 올린 적)
    d0 = ImageDraw.Draw(base)
    tw = int(max(d0.textlength('민들레 솜털', font=K.F_TITLE()), d0.textlength('힐러 · 체력 120 / 240', font=K.F_SMALL()))) + 18
    tx = min(cx - 20, W - 6 - tw) if False else W - 8 - tw
    card(base, tx, foot + 10, tw, 32)
    K.draw_text(base, (tx + 9, foot + 19), '민들레 솜털', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (tx + 9, foot + 33), '힐러 · 체력 120 / 240', K.F_SMALL(), K.BTN['green'][1], 'lm')
    card(base, 196, 56, 248, 20)
    paste(base, K.icon('sword'), (204, 60))
    K.draw_text(base, (220, 66), '공격할 적을 누르세요 · 취소는 ESC', K.F_BODY(), K.TEXT, 'lm')
    me = dict(PLAYER[0]); me['line'] = '공 182 · 방 70 · 민 140'
    a_bottom(base, me, [
        (176, 284, 96, 28, '공격', 'orange', 'pressed', 'sword'),
        (276, 284, 116, 28, '화염 폭풍', 'purple', 'normal', None),
        (176, 318, 96, 26, '방어', 'blue', 'normal', 'shield')], '적 전체 · 쓰면 1턴 쉼')
    _cursor(base, cx + 8, foot - 22)
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def cand_a2_log(out):
    """전투 기록에 마우스를 올리면 위로 크게 펼쳐짐."""
    base = a_base(0)
    PLAYER[0]['tags'] = []; PLAYER[1]['tags'] = [('절대방어', 'blue')]; PLAYER[2]['tags'] = [('쿨타임 1', 'gray')]
    for i in (0, 2, 1):
        fighter(base, PLAYER[i], *POS_P[i], flip=False, sel=(i == 0))
    for i in (0, 2, 1):
        e = dict(ENEMY[i]); e['tags'] = [('방어', 'blue')] if i == 0 else []
        fighter(base, e, *POS_E[i], flip=True)
    me = dict(PLAYER[0]); me['line'] = '공 182 · 방 70 · 민 140'
    a_bottom(base, me, [
        (176, 284, 96, 28, '공격', 'orange', 'normal', 'sword'),
        (276, 284, 116, 28, '화염 폭풍', 'purple', 'normal', None),
        (176, 318, 96, 26, '방어', 'blue', 'normal', 'shield')], '적 전체 · 쓰면 1턴 쉼')
    # 펼친 기록
    x0, y0, w, h = 396, 84, 230, 262
    panel(base, x0, y0, w, h)
    K.draw_text(base, (x0 + 14, y0 + 16), '전투 기록', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (x0 + w - 14, y0 + 16), '규칙형 AI', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    d = ImageDraw.Draw(base)
    d.line((x0 + 12, y0 + 26, x0 + w - 12, y0 + 26), fill=K.PAPER[0])
    for i, (r, t, c) in enumerate(FULL_LOG):
        y = y0 + 38 + i * 19
        if i % 2 == 0:
            d.rectangle((x0 + 10, y - 8, x0 + w - 10, y + 9), fill=K.PAPER[3])
        if r:
            chip(base, x0 + 14, y - 6, r, 'gray' if r == '적' else 'brown')
        K.draw_text(base, (x0 + 40, y + 1), t, K.F_SMALL(), c, 'lm')
    d.rectangle((x0 + w - 12, y0 + 32, x0 + w - 10, y0 + h - 12), fill=K.PAPER[0])
    d.rectangle((x0 + w - 12, y0 + 150, x0 + w - 10, y0 + h - 12), fill=K.WOOD[2])
    _cursor(base, 560, 318)
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


def _cursor(base, x, y):
    rows = ("O.......", "OO......", "OWO.....", "OWWO....", "OWWWO...", "OWWWWO..", "OWWWWWO.", "OWWWOOOO", "OWOWO...", "OO.OWO..", "O..OWO..", "....OO..")
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch == 'O': base.putpixel((x + i, y + j), INK + (255,))
            elif ch == 'W': base.putpixel((x + i, y + j), (255, 255, 255, 255))


def run_a2(out):
    cand_a2_attack(out / 'battle_A2_1_attack.png')
    cand_a2_heal(out / 'battle_A2_2_heal.png')
    cand_a2_log(out / 'battle_A2_3_log.png')
