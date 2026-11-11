"""재료·요리 아이콘 16x16 (mon2 툴킷 사용). 저장은 4배."""
from PIL import Image
import mon2 as M
from mon2 import Spr, E, R, P, L, U, pal, hx

EGG = pal('#ffffff', '#fffaf0', '#f4e6cc', '#d8c0a0', '#a88a6c')
YOLK = pal('#fff6b0', '#ffd84a', '#f2b030', '#c88020', '#8c5a14')
POT = pal('#f6dca0', '#d8a868', '#b8844a', '#8c5e32', '#5e3c20')
TOM = pal('#ffd0c0', '#ff7a62', '#e8463a', '#b0282e', '#741c24')
LEAFG = pal('#d8f59a', '#8fd86a', '#5cb24e', '#3a8a40', '#24602e')
ONI = pal('#fff0e0', '#f0d0b0', '#d8a888', '#b07a64', '#7a4e44')
MILKB = pal('#ffffff', '#f4f8ff', '#dce6f4', '#aebcd6', '#7a88a8')
BLUE = pal('#d0e8ff', '#7ab8ff', '#4a88e8', '#2e5cb0', '#1e3c7a')
GRAY = pal('#f0f0f4', '#c8c8d2', '#9a9aa8', '#6e6e7c', '#4a4a56')
BUT = pal('#fffbd0', '#fff07a', '#ffd84a', '#e0aa2a', '#a0741a')
WHEAT = pal('#fff4c0', '#f6d878', '#e0b44a', '#b8862c', '#7c5a1c')
MEAT = pal('#ffd0b8', '#e8946c', '#c8643e', '#9a4028', '#66281a')
BEEF = pal('#ffc0c0', '#e85a5a', '#c43a40', '#8e2430', '#5e1820')
BONE = pal('#ffffff', '#fffaf0', '#ece0cc', '#c8b49a', '#8c7a64')
RABBIT = pal('#ffe0ec', '#ffaacc', '#f080b0', '#c05088', '#80305c')
RICE = pal('#ffffff', '#f8f4ec', '#e8dcc8', '#c4b49c', '#8a7a64')
PLATE = pal('#ffffff', '#f4f6fa', '#dfe4ec', '#b4bccc', '#7a8496')
BOWL = pal('#fff0e0', '#e8b890', '#c88a5c', '#9a603c', '#663c24')
SOUP = pal('#ffd0b8', '#ff8a5c', '#e8583a', '#b03a28', '#742418')
BUN = pal('#ffe6b0', '#f2b866', '#d88a3c', '#a8602a', '#6e3c1c')
CREAM = pal('#fffef4', '#fff6d8', '#f4e2b0', '#d8c088', '#a08a5c')
KETCH = (220, 50, 50)


def _s():
    M.OFF[0] = 0; M.SC[:] = [1.0, 0.0, 0.0]; return Spr(16)


# ---------- 재료 ----------
def egg():
    s = _s(); s.part(E((4, 2, 12, 14)), EGG); return s.done()
def potato():
    s = _s(); s.part(E((2, 4, 14, 13)), POT); s.dot([(5, 7), (9, 9), (11, 6)], POT[3]); return s.done()
def tomato():
    s = _s(); s.part(E((2, 4, 14, 15)), TOM); s.part(P([(5, 4), (8, 1), (11, 4), (8, 6)]), LEAFG, spec=False); return s.done()
def onion():
    s = _s(); s.part(U(E((3, 5, 13, 15)), P([(6, 6), (8, 1), (10, 6)])), ONI)
    s.dot([(8, 7), (8, 9), (8, 11)], ONI[3]); return s.done()
def milk():
    s = _s(); s.part(U(R((4, 5, 11, 15)), P([(4, 5), (6, 2), (9, 2), (11, 5)])), MILKB)
    s.part(R((4, 8, 11, 11)), BLUE, spec=False); s.part(R((6, 0, 9, 2)), BLUE, spec=False); return s.done()
def salt():
    s = _s(); s.part(R((4, 6, 11, 15)), MILKB); s.part(E((4, 1, 11, 7)), GRAY, spec=False)
    s.dot([(6, 3), (8, 2), (9, 4)], GRAY[3]); return s.done()
def butter():
    s = _s(); s.part(P([(1, 9), (9, 5), (15, 8), (7, 13)]), BUT); s.part(P([(1, 9), (7, 13), (7, 15), (1, 11)]), BUT, spec=False)
    s.part(P([(7, 13), (15, 8), (15, 10), (7, 15)]), BUT, spec=False); return s.done()
def wheat():
    s = _s(); s.part(L([(8, 15), (8, 4)], 1), WHEAT, spec=False)
    for y in (3, 6, 9):
        s.part(E((4, y, 8, y + 3)), WHEAT, spec=False); s.part(E((8, y, 12, y + 3)), WHEAT, spec=False)
    s.part(E((6, 0, 10, 4)), WHEAT, spec=False); return s.done()
def chicken():
    s = _s(); s.part(L([(4, 12), (8, 8)], 2), BONE, spec=False); s.part(E((1, 11, 5, 15)), BONE, spec=False)
    s.part(E((6, 1, 15, 11)), MEAT); return s.done()
def beef():
    s = _s(); s.part(E((1, 3, 15, 13)), BEEF); s.part(E((3, 5, 9, 10)), BONE, spec=False, rim=False)
    s.part(E((4, 6, 8, 9)), BEEF, spec=False, rim=False); return s.done()
def rice():
    s = _s(); s.part(U(R((3, 5, 12, 15)), E((3, 3, 12, 8))), RICE); s.part(R((6, 1, 9, 4)), WHEAT, spec=False)
    s.dot([(7, 9), (8, 10), (7, 11)], WHEAT[2]); return s.done()
def rabbit_meat():
    s = _s(); s.part(L([(4, 12), (8, 8)], 2), BONE, spec=False); s.part(E((1, 11, 5, 15)), BONE, spec=False)
    s.part(E((6, 1, 15, 11)), RABBIT); s.dot([(13, 0), (14, 1), (15, 0)], (255, 236, 120)); return s.done()


# ---------- 요리 (접시·그릇) ----------
def _plate(s): s.part(E((0, 8, 15, 15)), PLATE, spec=False)
def _bowl(s, soup=SOUP):
    s.part(U(E((1, 6, 14, 15)), R((1, 6, 14, 10))), BOWL, spec=False); s.part(E((2, 5, 13, 9)), soup, spec=False)


def d_boiled_egg():
    s = _s(); _plate(s); s.part(E((3, 4, 9, 12)), EGG); s.part(E((7, 6, 13, 12)), EGG); s.part(E((9, 8, 11, 10)), YOLK, spec=False); return s.done()
def d_steamed_potato():
    s = _s(); _plate(s); s.part(E((2, 5, 9, 12)), POT); s.part(E((7, 4, 14, 11)), POT); s.dot([(4, 2), (5, 1), (10, 1), (11, 0)], (230, 236, 246)); return s.done()
def d_egg_roll():
    s = _s(); _plate(s)
    for x in (2, 6, 10): s.part(R((x, 5, x + 3, 11)), YOLK)
    return s.done()
def d_tomato_soup():
    s = _s(); _bowl(s); s.dot([(5, 6), (9, 7)], LEAFG[1]); return s.done()
def d_butter_potato():
    s = _s(); _plate(s); s.part(E((2, 4, 14, 12)), POT); s.part(R((6, 4, 10, 7)), BUT, spec=False); return s.done()
def _burger(meat):
    s = _s(); s.part(U(E((2, 1, 14, 8)), R((2, 5, 14, 7))), BUN); s.part(R((1, 8, 15, 9)), LEAFG, spec=False)
    s.part(R((2, 10, 14, 11)), meat, spec=False); s.part(R((2, 12, 14, 14)), BUN, spec=False)
    s.dot([(5, 3), (8, 2), (11, 4)], (255, 246, 220)); return s.done()
def d_chicken_burger(): return _burger(MEAT)
def d_beef_burger(): return _burger(BEEF)
def d_fried_chicken():
    s = _s(); _plate(s); s.part(E((1, 3, 9, 11)), BUN); s.part(E((7, 2, 15, 10)), BUN); s.part(L([(12, 9), (14, 13)], 2), BONE, spec=False); return s.done()
def d_carbonara():
    s = _s(); _plate(s); s.part(E((2, 3, 14, 12)), CREAM)
    for pts in ([(4, 6), (8, 8), (12, 5)], [(3, 9), (7, 7), (11, 10)]): s.flat(L(pts), CREAM[3])
    s.dot([(6, 5), (10, 9)], (200, 120, 90)); return s.done()
def d_omelette_rice():
    s = _s(); _plate(s); s.part(U(E((1, 3, 15, 13)), R((1, 8, 15, 11))), YOLK); s.flat(L([(4, 6), (7, 8), (10, 6), (12, 8)]), KETCH); return s.done()
def d_rabbit_stew():
    s = _s(); _bowl(s, BUN); s.dot([(5, 6), (9, 7), (7, 8)], POT[1]); s.dot([(13, 0), (14, 1), (15, 0), (1, 1)], (255, 236, 120)); return s.done()
def d_burned():
    s = _s(); _plate(s); s.part(E((3, 4, 13, 12)), pal('#6a5a52', '#4a3c38', '#2e2426', '#1e1618', '#120c0e'))
    s.dot([(5, 1), (6, 0), (10, 2), (11, 1)], (150, 150, 160)); return s.done()


INGREDIENTS = {'egg_food': ('달걀', egg), 'potato': ('감자', potato), 'tomato': ('토마토', tomato), 'onion': ('양파', onion),
               'milk': ('우유', milk), 'salt': ('소금', salt), 'butter': ('버터', butter), 'wheat': ('밀', wheat),
               'chicken': ('닭고기', chicken), 'beef': ('소고기', beef), 'rice': ('쌀', rice), 'lucky_rabbit': ('행운의 토끼고기', rabbit_meat)}
DISHES = {'boiled_egg': d_boiled_egg, 'steamed_potato': d_steamed_potato, 'egg_roll': d_egg_roll, 'tomato_soup': d_tomato_soup,
          'butter_potato': d_butter_potato, 'chicken_burger': d_chicken_burger, 'beef_burger': d_beef_burger,
          'fried_chicken': d_fried_chicken, 'carbonara': d_carbonara, 'omelette_rice': d_omelette_rice,
          'rabbit_stew': d_rabbit_stew, 'burned_food': d_burned}


def icon(key, scale=1):
    fn = INGREDIENTS[key][1] if key in INGREDIENTS else DISHES[key]
    im = fn(); return im.resize((16 * scale, 16 * scale), Image.NEAREST)


# ---------- 윤기 나는 명암 그대로, 모양만 구분 (닭고기·소고기·치킨·버거) ----------
RAW = pal('#fff4ee', '#ffd8c8', '#f4ac94', '#d47c68', '#9a5244')        # 생닭: 연분홍
FAT = pal('#ffffff', '#fff6e8', '#f2e2c8', '#d8c0a0', '#a08a6c')
STEAK = pal('#ffb0b0', '#e24a52', '#bc2c3a', '#86182a', '#58101e')       # 소고기: 진빨강
CRISP = pal('#fff0a0', '#ffc860', '#e89838', '#b86a20', '#7a4414')       # 튀김옷
PATTY_B = pal('#b07860', '#7a4630', '#5a3020', '#3e2016', '#28140c')     # 소고기 패티
PATTY_C = pal('#ffe0a0', '#f2b05a', '#d4883a', '#a86024', '#703c14')     # 닭 패티
CHEESE = pal('#fff8c0', '#ffe060', '#f4c030', '#c89020', '#8a6010')


def chicken():            # 생닭 다리: 연분홍 살 + 하얀 뼈
    s = _s(); s.part(L([(4, 12), (8, 8)], 2), BONE, spec=False); s.part(E((1, 11, 5, 15)), BONE, spec=False)
    s.part(E((5, 1, 15, 11)), RAW); s.dot([(8, 5), (11, 7)], RAW[3]); return s.done()


def beef():               # 소고기: 지방 테두리 + 마블링, 뼈 없음
    s = _s(); s.part(E((0, 3, 15, 14)), FAT, spec=False)
    s.part(E((2, 4, 14, 13)), STEAK)
    s.dot([(5, 7), (6, 7), (9, 9), (10, 6), (7, 11), (11, 10)], (250, 200, 200)); return s.done()


def d_fried_chicken():    # 치킨: 뼈가 위로 솟은 바삭한 닭다리 두 개
    s = _s(); _plate(s)
    for bx in (4, 11):
        s.part(L([(bx, 1), (bx, 6)], 2), BONE, spec=False); s.part(E((bx - 2, 0, bx + 1, 2)), BONE, spec=False)
    s.part(E((0, 4, 8, 13)), CRISP); s.part(E((7, 4, 15, 13)), CRISP)
    s.dot([(2, 7), (4, 10), (5, 6), (9, 8), (12, 6), (13, 10), (10, 11)], CRISP[3])
    s.dot([(3, 6), (10, 6)], CRISP[0]); return s.done()


def _burger_v(patty, cheese):
    s = _s(); s.part(U(E((2, 0, 14, 7)), R((2, 4, 14, 6))), BUN)
    s.part(R((1, 7, 15, 7)), LEAFG, spec=False)
    if cheese: s.part(P([(1, 8), (15, 8), (14, 9), (2, 9)]), CHEESE, spec=False)
    else: s.part(R((2, 8, 14, 8)), TOM, spec=False)
    s.part(R((2, 9, 14, 11)), patty, spec=False)
    if cheese: s.dot([(4, 10), (8, 9), (12, 10)], PATTY_B[0])
    else: s.dot([(4, 10), (7, 9), (11, 10)], PATTY_C[0])
    s.part(U(R((2, 12, 14, 13)), E((2, 11, 14, 15))), BUN, spec=False)
    s.dot([(5, 2), (8, 1), (11, 3)], (255, 246, 220)); return s.done()


def d_chicken_burger(): return _burger_v(PATTY_C, cheese=False)
def d_beef_burger(): return _burger_v(PATTY_B, cheese=True)


INGREDIENTS['chicken'] = ('닭고기', chicken)
INGREDIENTS['beef'] = ('소고기', beef)
DISHES.update({'fried_chicken': d_fried_chicken, 'chicken_burger': d_chicken_burger, 'beef_burger': d_beef_burger})
