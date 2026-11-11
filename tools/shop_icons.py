"""상점·병원 아이템 아이콘 16x16 (음식 아이콘과 같은 윤기 명암)."""
from PIL import Image, ImageDraw
import mon2 as M
from mon2 import Spr, E, R, P, L, U, pal
from food_icons import _s, BONE, LEAFG, POT

GLASS = pal('#ffffff', '#eef6ff', '#cfe0f4', '#9cb4d4', '#6a82a8')
CORK = pal('#f0c890', '#c8925a', '#9a6438', '#6e4224', '#4a2a18')
LIQ = {'pink': pal('#ffe0ee', '#ff9ac4', '#f0609c', '#c03c78', '#80244e'),
       'gold': pal('#fff6c0', '#ffd860', '#f4b030', '#c47e18', '#86500e'),
       'red': pal('#ffd0c8', '#ff7a6a', '#e8463a', '#b0282e', '#741c24'),
       'blue': pal('#d8ecff', '#7ab8ff', '#4a88e8', '#2e5cb0', '#1e3c7a'),
       'orange': pal('#ffe6c0', '#ffb860', '#f28a2e', '#c45e1c', '#843a12'),
       'green': pal('#e6ffd0', '#9ae070', '#5cbc4c', '#3a8a3e', '#24602a')}
WHITE = pal('#ffffff', '#fbfbff', '#e8eaf2', '#c4c8d6', '#8a90a6')
LEATHER = pal('#e8b880', '#c08050', '#9a5c34', '#6e3e22', '#4a2814')
METAL = pal('#ffffff', '#e2e8f2', '#b8c2d4', '#8692aa', '#5a6480')
SHELLG = pal('#e6f0a0', '#b8cc66', '#8aa648', '#5e7a32', '#3e5222')
EGG1 = pal('#fffef6', '#fff4dc', '#f2ddb8', '#d4b88a', '#9c8058')
EGG2 = pal('#f4e8ff', '#d8c0ff', '#b08ef0', '#8264c8', '#56408e')
CANDY = pal('#fff0f6', '#ffc0dc', '#ff8ab8', '#e05a92', '#a03466')
TEDDY = pal('#f6dcb0', '#dca878', '#b8804e', '#8a5832', '#5e3a1e')
SACK = pal('#fff2d0', '#ecd4a0', '#ccac72', '#a0804c', '#6e5430')


def _bottle(liq, big=False):
    s = _s()
    if big:
        s.part(U(E((2, 5, 14, 15)), R((6, 2, 10, 6))), GLASS)
        s.part(E((3, 8, 13, 15)), liq)
    else:
        s.part(U(E((3, 6, 13, 15)), R((6, 3, 10, 7))), GLASS)
        s.part(E((4, 9, 12, 15)), liq)
    s.part(R((6, 0, 10, 3)), CORK, spec=False)
    return s


def heal_basic():
    return _bottle(LIQ['pink']).done()


def heal_advanced():
    s = _bottle(LIQ['gold'], big=True)
    s.dot([(1, 1), (0, 2), (2, 2), (1, 3), (14, 4), (15, 5), (13, 5), (14, 6)], (255, 236, 120)); return s.done()


def _stat_potion(col):
    s = _s(); s.part(U(R((5, 4, 11, 15)), E((4, 8, 12, 15))), GLASS); s.part(U(R((5, 8, 11, 15)), E((4, 10, 12, 15))), LIQ[col])
    s.part(R((6, 1, 10, 4)), CORK, spec=False); s.part(R((6, 10, 10, 12)), WHITE, spec=False, rim=False); return s.done()


def potion_attack(): return _stat_potion('orange')
def potion_defense(): return _stat_potion('blue')
def potion_hp(): return _stat_potion('red')
def potion_agility(): return _stat_potion('green')


def battle_bandage():
    s = _s(); s.part(E((1, 4, 15, 14)), WHITE); s.part(E((5, 7, 11, 11)), WHITE, spec=False)
    s.flat(R((7, 5, 8, 12)), (230, 70, 70)); s.flat(R((4, 8, 11, 9)), (230, 70, 70)); return s.done()


def snack():
    s = _s(); s.part(P([(0, 5), (4, 8), (0, 11)]), CANDY, spec=False); s.part(P([(15, 5), (11, 8), (15, 11)]), CANDY, spec=False)
    s.part(E((3, 3, 13, 13)), CANDY); s.dot([(6, 6), (9, 9), (7, 10)], (255, 255, 255)); return s.done()


def toy_ball():
    s = _s(); s.part(E((1, 1, 15, 15)), LIQ['red']); s.part(R((1, 7, 15, 9)), WHITE, spec=False, rim=False)
    s.part(E((6, 6, 10, 10)), WHITE, spec=False); return s.done()


def toy_doll():
    s = _s(); s.part(E((1, 0, 6, 5)), TEDDY, spec=False); s.part(E((10, 0, 15, 5)), TEDDY, spec=False)
    s.part(E((3, 9, 13, 16)), TEDDY); s.part(E((2, 1, 14, 11)), TEDDY)
    s.dot([(5, 5), (10, 5)], (40, 30, 30)); s.dot([(7, 7), (8, 7)], (90, 50, 40)); s.dot([(4, 7), (11, 7)], (250, 160, 170)); return s.done()


def equip_necklace():
    s = _s(); s.flat(L([(2, 2), (4, 8), (8, 10), (12, 8), (14, 2)], 1), LEATHER[3])
    s.part(P([(6, 9), (10, 9), (8, 15)]), BONE); s.part(E((7, 8, 9, 10)), LIQ['gold'], spec=False); return s.done()


def equip_claw():
    s = _s()
    for x in (2, 6, 10):
        s.part(P([(x, 14), (x + 3, 14), (x + 5, 3), (x + 2, 7)]), METAL)
    return s.done()


def equip_shell():
    s = _s(); s.part(U(E((1, 3, 15, 15)), R((1, 9, 15, 12))), SHELLG)
    s.flat(L([(8, 4), (8, 14)]), SHELLG[3]); s.flat(L([(2, 9), (14, 9)]), SHELLG[3])
    s.flat(L([(4, 5), (12, 13)]), SHELLG[3]); s.flat(L([(12, 5), (4, 13)]), SHELLG[3]); return s.done()


def equip_feather():
    s = _s(); s.part(P([(3, 15), (5, 8), (10, 2), (14, 0), (12, 6), (7, 12)]), WHITE)
    s.flat(L([(3, 15), (13, 1)]), WHITE[3]); s.dot([(9, 6), (7, 9)], LIQ['blue'][1]); return s.done()


def egg_basic():
    s = _s(); s.part(E((3, 1, 13, 15)), EGG1); s.dot([(6, 5), (10, 8), (7, 11), (5, 9)], (190, 140, 90)); return s.done()


def egg_special():
    s = _s(); s.part(E((3, 1, 13, 15)), EGG2)
    for x, y in ((6, 5), (10, 9)):
        s.dot([(x, y - 1), (x - 1, y), (x, y), (x + 1, y), (x, y + 1)], (255, 226, 90))
    s.dot([(8, 12)], (255, 255, 255)); return s.done()


def seed():
    s = _s(); s.part(U(E((2, 5, 14, 15)), R((4, 4, 12, 7))), SACK)
    s.flat(L([(4, 6), (12, 6)]), SACK[3]); s.part(P([(8, 4), (5, 0), (8, 2), (11, 0)]), LEAFG, spec=False); return s.done()


ICONS = {'heal_basic': heal_basic, 'heal_advanced': heal_advanced, 'potion_attack': potion_attack, 'potion_defense': potion_defense,
         'potion_hp': potion_hp, 'potion_agility': potion_agility, 'battle_bandage': battle_bandage, 'snack': snack,
         'toy_ball': toy_ball, 'toy_doll': toy_doll, 'equip_necklace': equip_necklace, 'equip_claw': equip_claw,
         'equip_shell': equip_shell, 'equip_feather': equip_feather, 'egg_basic': egg_basic, 'egg_special': egg_special, 'seed': seed}


def icon(key, scale=1):
    im = ICONS['seed' if key.startswith('seed_') else key]()
    return im.resize((16 * scale, 16 * scale), Image.NEAREST)


# ================= v2: 알·장비 다시 =================
def _sp(n):
    M.OFF[0] = 0; M.SC[:] = [1.0, 0.0, 0.0]; return Spr(n)


GOLDE = pal('#fffce0', '#ffe680', '#ffc83a', '#e0961e', '#9a5c10')
GEM = {'r': pal('#ffd0e0', '#ff7aa8', '#e8407a', '#a82458', '#6c1438'),
       'b': pal('#d8f6ff', '#7ad8ff', '#3aa6f0', '#2468c0', '#163e80'),
       'g': pal('#e0ffd8', '#8ef08a', '#44c860', '#2a8a44', '#185a2c'),
       'p': pal('#f0e0ff', '#c8a0ff', '#9a64f0', '#6a40c0', '#422680')}
CREAM = pal('#ffffff', '#fff8e8', '#f2e2c0', '#d6bc90', '#9c825c')
SPOT = pal('#f0d8b0', '#d4a868', '#b08040', '#80582a', '#56381a')
STEEL = pal('#ffffff', '#e8eef8', '#bcc8dc', '#8492ae', '#545e7c')
LEATH = pal('#f4c890', '#cc8a50', '#a0602e', '#723e1c', '#4a2610')
SHELL2 = pal('#e8f4a8', '#b8d470', '#86ac48', '#5a7e32', '#3a5420')
FEATH = pal('#ffffff', '#eaf6ff', '#c4e2fa', '#8ab8e6', '#5a86bc')


def egg_basic(n=16):
    k = n / 16; s = _sp(n)
    s.part(E((3 * k, 1 * k, 13 * k - 1, 15 * k - 1)), CREAM)
    for x, y, r in ((6, 6, 1.4), (10, 9, 1.0), (7, 11, 1.1), (10, 4, .8)):
        s.part(E((x * k - r * k, y * k - r * k, x * k + r * k, y * k + r * k)), SPOT, spec=False, rim=False)
    return s.done()


def egg_special(n=16):
    """특급 알: 금빛 껍질 + 보석 띠 + 반짝이"""
    k = n / 16; s = _sp(n)
    s.part(E((3 * k, 1 * k, 13 * k - 1, 15 * k - 1)), GOLDE)
    # 지그재그 보석 띠
    band = [(3 * k, 8 * k), (5 * k, 6.5 * k), (7 * k, 8 * k), (9 * k, 6.5 * k), (11 * k, 8 * k), (13 * k, 6.5 * k),
            (13 * k, 9 * k), (11 * k, 10.5 * k), (9 * k, 9 * k), (7 * k, 10.5 * k), (5 * k, 9 * k), (3 * k, 10.5 * k)]
    m = Image.new('L', (n, n)); ImageDraw.Draw(m).polygon(band, fill=255)
    egg = s.img.copy(); px = s.img.load(); mp = m.load()
    for y in range(n):
        for x in range(n):
            if mp[x, y] and egg.getpixel((x, y))[3]:
                px[x, y] = GEM['p'][2 if (x + y) % 3 else 1] + (255,)
    for i, (gx, col) in enumerate(((5, 'r'), (8, 'b'), (11, 'g'))):
        cx, cy = gx * k, (4.2 if i != 1 else 3.2) * k + (8 if n > 16 else 0) * 0
        r = 1.1 * k
        s.part(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), GEM[col], spec=True, rim=False)
    s.part(P([(8 * k, 11.5 * k), (9.2 * k, 12.7 * k), (8 * k, 13.9 * k), (6.8 * k, 12.7 * k)]), GEM['r'], rim=False)
    im = s.done()
    # 바깥 반짝이
    sp = [(1, 2), (14, 3), (0, 11), (15, 12)]
    p2 = im.load()
    for x, y in sp:
        X, Y = int(x * k), int(y * k)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= X + dx < n and 0 <= Y + dy < n and not p2[X + dx, Y + dy][3]:
                p2[X + dx, Y + dy] = (255, 236, 120, 255) if (dx, dy) != (0, 0) else (255, 255, 255, 255)
    return im


def equip_necklace():     # 가죽 목걸이: 끈 + 구슬 + 송곳니 펜던트
    s = _sp(16)
    s.part(U(L([(1, 1), (3, 6), (6, 9)], 1), L([(15, 1), (13, 6), (10, 9)], 1)), LEATH, spec=False)
    for x, y in ((3, 6), (13, 6)): s.part(E((x - 1, y - 1, x + 1, y + 1)), GEM['b'], spec=False, rim=False)
    s.part(E((6, 7, 10, 11)), GOLDE, spec=False)
    s.part(P([(6, 10), (10, 10), (9, 13), (8, 15), (7, 13)]), CREAM)
    return s.done()


def equip_claw():         # 날카로운 발톱: 가죽 손등 + 휘어진 강철 칼날 3개
    s = _sp(16)
    s.part(U(E((1, 9, 9, 15)), R((1, 11, 9, 15))), LEATH)
    for i, x in enumerate((4, 7, 10)):
        s.part(P([(x - 1, 11 - i), (x + 1, 10 - i), (x + 6, 2 - i // 2), (x + 3, 6 - i)]), STEEL)
    s.flat(L([(2, 12), (8, 12)]), GOLDE[2])
    return s.done()


def equip_shell():        # 등껍질 보호대: 방패 모양 등껍질 + 끈
    s = _sp(16)
    s.part(P([(2, 2), (14, 2), (14, 9), (8, 15), (2, 9)]), SHELL2)
    s.part(P([(6, 5), (10, 5), (11, 8), (8, 11), (5, 8)]), SHELL2, spec=True, rim=False)
    for a, b in (((6, 5), (3, 3)), ((10, 5), (13, 3)), ((11, 8), (14, 9)), ((5, 8), (2, 9)), ((8, 11), (8, 14))):
        s.flat(L([a, b]), SHELL2[4])
    s.flat(L([(0, 6), (2, 6)]), LEATH[2]); s.flat(L([(14, 6), (15, 6)]), LEATH[2])
    return s.done()


def equip_feather():      # 가벼운 깃털: 하늘색 깃털 + 리본 장식
    s = _sp(16)
    s.part(P([(2, 15), (4, 9), (8, 4), (13, 0), (15, 2), (12, 7), (7, 12)]), FEATH)
    s.flat(L([(2, 15), (14, 1)]), FEATH[4])
    for t in (6, 9, 12): s.flat(L([(t - 1, 15 - t + 2), (t + 2, 15 - t + 1)]), FEATH[3])
    s.part(U(P([(1, 12), (4, 13), (1, 15)]), P([(5, 15), (4, 12), (7, 15)])), GEM['r'], spec=False)
    return s.done()


ICONS.update({'egg_basic': egg_basic, 'egg_special': egg_special, 'equip_necklace': equip_necklace,
              'equip_claw': equip_claw, 'equip_shell': equip_shell, 'equip_feather': equip_feather})


# ================= v3: 손으로 찍은 16px 알·장비 (가는 선이 뭉개지지 않게) =================
PX = {'o': (52, 34, 30), '.': None,
      'w': (255, 255, 255), 'c': (246, 232, 204), 'C': (214, 188, 146), 'D': (164, 134, 96), 'p': (150, 104, 60),
      'Y': (255, 242, 150), 'y': (250, 200, 60), 'G': (214, 140, 30), 'Z': (150, 88, 20),
      'W': (236, 236, 248), 'b': (90, 180, 255), 'B': (40, 110, 210), 'r': (255, 140, 170), 'R': (226, 50, 90),
      'm': (140, 24, 60), 'g': (120, 220, 110), 'h': (70, 160, 80), 'H': (40, 108, 56), 'e': (50, 200, 120),
      'l': (226, 168, 110), 'L': (176, 110, 60), 'd': (120, 68, 34),
      's': (250, 252, 255), 'S': (188, 200, 220), 't': (120, 132, 160),
      'f': (220, 240, 255), 'F': (130, 190, 240), 'v': (70, 120, 200),
      '+': (255, 230, 110), '*': (255, 255, 255)}


def pixmap(rows):
    assert all(len(r) == 16 for r in rows), [len(r) for r in rows]
    im = Image.new('RGBA', (16, 16)); px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if PX[ch]: px[x, y] = PX[ch] + (255,)
    return im


EGG_BASIC = [
    '................',
    '......oooo......',
    '.....owwcco.....',
    '....owwcccCo....',
    '...owwccpccCo...',
    '...owccccccCo...',
    '..owcpcccccCCo..',
    '..occcccccpcCo..',
    '..occcccccccCo..',
    '..occpccccccCo..',
    '..occcccpcccCo..',
    '..oCccccccCCDo..',
    '...oCCcccCCDo...',
    '...oDCCCCCDDo...',
    '....ooDDDDoo....',
    '......oooo......']
EGG_SPECIAL = [
    '......oooo......',
    '.+...oYYyyo..+..',
    '+*+.oYYyyyyo+*+.',
    '.+.oYYyyyyyGo+..',
    '...oYyyyRyyGo...',
    '..oYyyyRrRyGGo..',
    '..oWsWsWRWsWso..',
    '..osbsWsrsWesWo.',
    '..oWsWsWsWsWWo..',
    '..oyyyyyyyyGGo..',
    '..oyYyyyyyGGGo..',
    '..oGyyyyyGGGZo..',
    '...oGGyyGGGZo...',
    '...oZGGGGGZZo.+.',
    '....ooZZZZoo.+*+',
    '......oooo....+.']
NECKLACE = [
    '................',
    '.oo..........oo.',
    '.oLo........oLo.',
    '..oLo......oLo..',
    '..obo......obo..',
    '..oBo......oBo..',
    '...oLo....oLo...',
    '....oLooooLo....',
    '.....oYYyGo.....',
    '....oYyrRyGo....',
    '....oyRrRmGo....',
    '....oyRmmmGo....',
    '.....oGyyGo.....',
    '......owco......',
    '......occo......',
    '.......oo.......']
SHELL = [
    '................',
    '.oooooooooooooo.',
    '.oYYYYYYYYYYYGo.',
    '.oYgghHHHHhhHGo.',
    '.oYghHggggHhHGo.',
    '.oYgHgwgggHhHGo.',
    '.oYHHggggghHHGo.',
    '.oYgHgggggHhHGo.',
    '.oYghHggghHhHGo.',
    '..oYghHHHHhhGo..',
    '..oYgghhhhhHGo..',
    '...oYghhhhHGo...',
    '....oYghhHGo....',
    '.....oYhHGo.....',
    '......oGGo......',
    '.......oo.......']
FEATHER = [
    '...........oooo.',
    '.........oofffwo',
    '........offfFwFo',
    '.......offFFwFFo',
    '......offFFwFFo.',
    '.....offFFwFFFo.',
    '....offFFwFFFo..',
    '....ofFFwFFFo...',
    '...ofFFwFFvo....',
    '...ofFwFFvo.....',
    '...ofwFvvo......',
    '...owvvoo.......',
    '..oYyo..........',
    '.oYyo...........',
    '.oyo............',
    '..o.............']


def _claw_rows():
    g = [['.'] * 16 for _ in range(16)]
    for bx, top in ((2, 2), (6, 0), (10, 2)):
        g[top][bx + 2] = 'o'
        g[top + 1][bx + 1:bx + 4] = list('oso')
        for y in range(top + 2, 9): g[y][bx:bx + 4] = list('osto')
    rows = [''.join(r) for r in g[:9]]
    rows += ['.oYYYYYYYYYYYGo.', '.oGGyGGGGyGGGZo.', '.olllLLLLLLLLdo.', '.olLLLLLLLLLLdo.',
             '.oLLdLLdLLdLLdo.', '.oddddddddddddo.', '..oooooooooooo..']
    return rows


ICONS.update({'egg_basic': lambda: pixmap(EGG_BASIC),
              'equip_necklace': lambda: pixmap(NECKLACE), 'equip_claw': lambda: pixmap(_claw_rows()),
              'equip_shell': lambda: pixmap(SHELL), 'equip_feather': lambda: pixmap(FEATHER)})
_egg_special_shaded = egg_special


def egg_special(n=16):
    """16 = 손으로 찍은 아이콘, 32 = 부화 화면용 큰 알 (금 껍질 + 진주 띠 + 보석)"""
    if n == 16: return pixmap(EGG_SPECIAL)
    k = n / 16; s = _sp(n)
    s.part(E((3 * k, 1 * k, 13 * k - 1, 15 * k - 1)), GOLDE)
    im = s.img; px = im.load()
    # 진주 띠 (위아래 금 테 + 흰 진주 무늬)
    y0, y1 = int(6.6 * k), int(9.2 * k)
    for y in range(y0, y1 + 1):
        for x in range(n):
            if not px[x, y][3]: continue
            if y in (y0, y1): px[x, y] = GOLDE[3] + (255,)
            else: px[x, y] = ((250, 250, 255) if (x + y) % 4 else (214, 220, 240)) + (255,)
    s.img = im
    for gx, col in ((5.3, 'b'), (8, 'r'), (10.7, 'g')):
        cx, cy, r = gx * k, 7.9 * k, (1.1 if col != 'r' else 1.4) * k
        s.part(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), GEM[col], rim=False)
    cx, cy, r = 8 * k, 3.9 * k, 1.0 * k
    s.part(P([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]), GEM['r'], rim=False)
    return s.done()


ICONS['egg_special'] = egg_special
