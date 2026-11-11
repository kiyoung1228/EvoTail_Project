"""적 몬스터 v2: 파트별 구면 명암 + 디더 + 색 맞춤 외곽선 + 몬스터별 다른 눈.
졸개 28x28, 보스 40x40 (원본). 저장은 4배(졸개 112, 보스 160)."""
from pathlib import Path
from PIL import Image, ImageDraw

BAYER = [[0, 2], [3, 1]]


def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def pal(*cs): return [hx(c) for c in cs]       # 밝음 → 어두움 (4~5색)


def mix(a, b, t): return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))
def darker(c, f=.55): return tuple(int(v * f) for v in c)


# 팔레트 (밝음 → 어두움)
EMBER = pal('#fff3b0', '#ffc845', '#ff8a2e', '#e2492a', '#9c2a24')
FLAME_Y = pal('#ffffe0', '#fff07a', '#ffc845', '#ff9a2e', '#d85a22')
LAVA = pal('#7a5a52', '#5e4440', '#46302f', '#322124', '#21161a')
AQUA = pal('#f0feff', '#b4f0ff', '#6cd0ff', '#3a98e8', '#2560b0')
JELLY = pal('#f4fffd', '#c6f6ef', '#8fe6dc', '#56c2c4', '#348c9e')
CORAL = pal('#ffe6ea', '#ffb8c6', '#ff8aa4', '#e05a7e', '#a8385e')
PEARL = pal('#fffaf0', '#f6e6d6', '#e4c8b4', '#c49c8c', '#8c6a64')
STONE = pal('#e6eaf0', '#bcc4d2', '#8e98ae', '#646e88', '#454c64')
MOSS = pal('#d8f59a', '#a6e070', '#6fbf52', '#469a44', '#2c6c36')
LEAF = pal('#e8ffd0', '#b6ef8a', '#78d067', '#45a352', '#2c7442')
MINT = pal('#ffffff', '#e2fbf2', '#b8eedd', '#7fd6bd', '#4ea891')
CLOUD = pal('#ffffff', '#f2f6ff', '#d8e2f6', '#b0bede', '#8590b8')
LILAC = pal('#f6f0ff', '#ddd0ff', '#b8a4f2', '#8e78d8', '#6550aa')
GOLD = pal('#fffbd0', '#ffe46a', '#ffc23a', '#d98a1e', '#9a5a14')
SILVER = pal('#ffffff', '#e6ecf6', '#bcc8dc', '#8a98b4', '#5c6886')
BRONZE = pal('#ffe2b0', '#f0b46a', '#cc8442', '#9a5a2c', '#683a1e')
NAVY = pal('#7a86c8', '#525ea4', '#3a4282', '#272c60', '#191c40')
DARK = pal('#6a5a7a', '#4c3e5e', '#362c46', '#241c32', '#161020')
CRYS = pal('#ffffff', '#d8f8ff', '#9ee2ff', '#6aa8f0', '#5a68d0')
SKIN = pal('#fff4ea', '#ffe0c8', '#f6c4a4', '#d89a80', '#a8705e')
WOOD = pal('#f0c890', '#c8925a', '#9a6438', '#6e4224', '#4a2a18')
RED = pal('#ffd0c8', '#ff8a7a', '#e84a4a', '#b02a36', '#741c2a')
PINK = (255, 150, 170)
INK = (34, 22, 40)
W = (255, 255, 255)


class Spr:
    def __init__(self, n=28):
        self.n = n
        self.img = Image.new('RGBA', (n, n))
        self.outl = {}       # 외곽선 색 기억 (파트별 가장 어두운 색)

    # ----- 파트: 마스크를 그리고 구면 명암으로 채움 -----
    def part(self, draw_fn, P, light=(-.55, -.8), flat=False, spec=True, rim=True, box=None):
        m = Image.new('L', (self.n, self.n)); d = ImageDraw.Draw(m)
        draw_fn(d)
        bb = box or m.getbbox()
        if not bb: return
        x0, y0, x1, y1 = bb; cx, cy = (x0 + x1 - 1) / 2, (y0 + y1 - 1) / 2
        hw, hh = max(1, (x1 - x0) / 2), max(1, (y1 - y0) / 2)
        mp = m.load(); px = self.img.load()
        SP = P[0]
        if len(P) >= 5: P = P[1:]
        lvl = len(P) - 1
        for y in range(self.n):
            for x in range(self.n):
                if not mp[x, y]: continue
                u, v = (x - cx) / hw, (y - cy) / hh
                t = .5 + .55 * (u * light[0] + v * light[1]) * -1 if not flat else .5
                t = 1 - t                                         # 0=밝음
                t = .5 + (t - .5) * 1.2
                edge = rim and any(not (0 <= x + dx < self.n and 0 <= y + dy < self.n and mp[x + dx, y + dy]) for dx, dy in ((1, 0), (0, 1)))
                if edge: t += .22
                # 동물 도트처럼 3단(밝음·본색·그림자), 디더 없음
                i = 0 if t < BANDS[0] else (1 if t < BANDS[1] else 2)
                if len(P) >= 4: i += 1 if i else 0          # 본색·그림자는 한 단 진하게
                i = max(0, min(lvl, i))
                px[x, y] = P[i] + (255,)
                self.outl[(x, y)] = P[-1]
        if spec:
            # 반짝이: 왼쪽 위 1~2px
            sx, sy = int(cx - hw * .45), int(cy - hh * .5)
            for (a, b) in ((sx, sy), (sx + 1, sy)):
                if 0 <= a < self.n and 0 <= b < self.n and mp[a, b]:
                    px[a, b] = SP + (255,)

    def flat(self, draw_fn, c):
        m = Image.new('L', (self.n, self.n)); d = ImageDraw.Draw(m); draw_fn(d)
        mp = m.load(); px = self.img.load()
        for y in range(self.n):
            for x in range(self.n):
                if mp[x, y]: px[x, y] = c + (255,); self.outl[(x, y)] = darker(c, .5)

    def dot(self, pts, c):
        px = self.img.load()
        if getattr(self, '_raw', 0):
            it = pts
        else:
            it = [TX(a, b) for a, b in pts]
        for x, y in it:
            if 0 <= x < self.n and 0 <= y < self.n: px[x, y] = c + (255,)

    # ----- 눈 -----
    def _eyes_cute(self, x, y, gap, h=3, blush=True):
        for ex in (x, x + gap):
            self.dot([(ex, yy) for yy in range(y, y + h)] + [(ex + 1, yy) for yy in range(y, y + h)], INK)
            self.dot([(ex, y)], W)
            if h >= 3: self.dot([(ex + 1, y + h - 1)], (90, 80, 120))
        if blush:
            self.dot([(x - 2, y + h), (x - 1, y + h), (x + gap + 2, y + h), (x + gap + 3, y + h)], PINK)

    def _eyes_happy(self, x, y, gap, blush=True):
        for ex in (x, x + gap):
            self.dot([(ex, y + 1), (ex + 1, y), (ex + 2, y + 1)], INK)
        if blush: self.dot([(x - 2, y + 2), (x - 1, y + 2), (x + gap + 3, y + 2), (x + gap + 4, y + 2)], PINK)

    def _eyes_sleepy(self, x, y, gap):
        for ex in (x, x + gap):
            self.dot([(ex, y), (ex + 1, y), (ex + 2, y)], INK); self.dot([(ex, y - 1)], darker(INK, 1))

    def _eyes_smug(self, x, y, gap):          # 반쯤 감은 눈 + 눈동자
        for ex in (x, x + gap):
            self.dot([(ex, y), (ex + 1, y), (ex + 2, y)], INK)
            self.dot([(ex, y + 1), (ex + 1, y + 1), (ex + 2, y + 1)], W)
            self.dot([(ex + 1, y + 1) if ex == x else (ex + 1, y + 1)], INK)

    def _eyes_dot(self, x, y, gap):
        self.dot([(x, y), (x, y + 1), (x + gap, y), (x + gap, y + 1)], INK)

    def _eyes_glow(self, x, y, gap, c, slant=1, length=3):
        """날카롭게 빛나는 눈: 안쪽이 내려간 사선."""
        for side, ex in ((-1, x), (1, x + gap)):
            for i in range(length):
                yy = y + (i if side == -1 else (length - 1 - i)) * slant // 2 if slant else y
                self.dot([(ex + i, yy)], c)
                self.dot([(ex + i, yy + 1)], darker(c, .7))
            self.dot([(ex + (length - 1 if side == -1 else 0), y + (length - 1) * slant // 2 if side == -1 else y + (length - 1) * slant // 2)], W)

    def _eyes_round(self, x, y, gap, iris=INK):
        for ex in (x, x + gap):
            self.dot([(ex, y), (ex + 1, y), (ex, y + 1), (ex + 1, y + 1)], W)
            self.dot([(ex + 1, y + 1)], iris)

    def __getattr__(self, name):
        if name.startswith('eyes_'):
            inner = object.__getattribute__(self, '_' + name)
            def call(x, y, gap, *a, **kw):
                X, Y = TX(x, y); g = max(3, int(round(gap * SC[0])))
                self._raw = 1
                try: inner(X, Y, g, *a, **kw)
                finally: self._raw = 0
            return call
        raise AttributeError(name)

    # ----- 마무리: 색 맞춤 외곽선 -----
    def done(self, base_ink=INK, ground_dark=True):
        src = self.img.copy().load(); px = self.img.load(); n = self.n
        for y in range(n):
            for x in range(n):
                if src[x, y][3]: continue
                nb = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                      if 0 <= x + dx < n and 0 <= y + dy < n and src[x + dx, y + dy][3]]
                if nb:
                    c = self.outl.get(nb[0], darker(src[nb[0][0], nb[0][1]][:3], .45))
                    c = mix(c, base_ink, .72)
                    px[x, y] = c + (255,)
        return self.img


OFF = [0]
BANDS = [.3, .66]          # 밝음/그림자 경계 (아이콘은 좁게)
SC = [1.0, 0.0, 0.0]          # 졸개 축소: (배율, x이동, y이동)
MINI = [0.72, 13.5 - 13.5 * 0.72, 25.6 - 26 * 0.72]   # 동물 도트 크기(약 16~18칸)에 맞춤
def TX(x, y):
    k, ox, oy = SC; o = OFF[0]
    return (int(round(ox + x * k)) + o, int(round(oy + y * k)) + o)
def _b(b):
    a = TX(b[0], b[1]); c = TX(b[2], b[3]); return (a[0], a[1], max(a[0], c[0]), max(a[1], c[1]))
def _p(ps): return [TX(x, y) for x, y in ps]
def E(box): return lambda d: d.ellipse(_b(box), fill=255)
def R(box): return lambda d: d.rectangle(_b(box), fill=255)
def P(pts): return lambda d: d.polygon(_p(pts), fill=255)
def L(pts, w=1): return lambda d: d.line(_p(pts), fill=255, width=max(1, int(round(w * SC[0]))))
def U(*fs):
    def f(d):
        for g in fs: g(d)
    return f


# ================= 졸개 12 (28x28) =================
def ember_pup():          # 불씨 몽이 (딜러·귀여움)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(P([(11, 9), (13, 3), (14, 7), (16, 2), (17, 9)]), FLAME_Y, spec=False)
    s.part(E((6, 8, 21, 25)), EMBER)
    s.part(E((10, 17, 17, 23)), FLAME_Y, spec=False, rim=False)
    s.eyes_cute(10, 13, 6)
    s.dot([(13, 18), (14, 18)], INK)
    s.part(E((7, 23, 11, 26)), EMBER, spec=False); s.part(E((16, 23, 20, 26)), EMBER, spec=False)
    return s.done()


def flame_slime():        # 불꽃 슬라임 (딜러·건방)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(P([(8, 15), (10, 7), (12, 11), (14, 2), (17, 10), (19, 6), (20, 15)]), FLAME_Y, spec=False)
    s.part(U(E((4, 11, 23, 27)), R((4, 19, 23, 25))), EMBER)
    s.eyes_smug(8, 17, 8)
    s.dot([(12, 22), (13, 22), (14, 22), (15, 23)], INK); s.dot([(14, 23)], RED[1])
    return s.done()


def will_wisp():          # 도깨비불 (딜러·장난)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(P([(7, 16), (20, 16), (23, 26), (19, 22), (16, 27), (13, 22), (10, 27), (7, 22), (4, 25)]), EMBER, spec=False)
    s.part(U(E((6, 5, 21, 21)), P([(9, 7), (12, 0), (15, 6)])), FLAME_Y)
    s.eyes_cute(9, 11, 7)
    s.dot([(12, 16), (13, 17), (14, 17), (15, 16)], INK); s.dot([(13, 16), (14, 16)], RED[2])
    return s.done()


def lava_shroom():        # 화산 버섯 (딜러·생글)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(U(R((10, 15, 17, 24)), E((9, 20, 18, 26))), SKIN)
    s.part(U(E((3, 4, 24, 19)), R((3, 11, 24, 14))), EMBER)
    for b in ((7, 7, 10, 10), (15, 6, 18, 9), (12, 11, 15, 13), (19, 11, 21, 13)):
        s.part(E(b), FLAME_Y, spec=False, rim=False)
    s.eyes_cute(10, 19, 5, h=2)
    s.dot([(12, 22), (13, 23), (14, 23), (15, 22)], INK)
    return s.done()


def bubble_jelly():       # 방울 젤리 (탱커·귀여움)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(U(R((5, 10, 22, 25)), E((5, 6, 22, 15))), JELLY)
    for b in ((7, 9, 9, 11), (18, 20, 20, 22), (17, 8, 18, 9)):
        s.part(E(b), pal('#ffffff', '#e6fffb', '#c6f6ef'), spec=False, rim=False)
    s.eyes_cute(9, 14, 8)
    s.dot([(12, 19), (13, 20), (14, 19), (15, 20), (16, 19)], INK)
    return s.done()


def clam_guard():         # 조개 기사 (탱커·씩씩)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(U(E((3, 6, 24, 25)), R((3, 15, 24, 19))), PEARL)
    for x in (7, 11, 16, 20):
        s.flat(L([(x, 8), (13 if x < 13 else 14, 22)]), PEARL[3])
    s.part(E((7, 13, 20, 24)), pal('#fff4f0', '#ffd8d0', '#f6b8b0', '#d88e88', '#a8605e'))
    s.eyes_cute(9, 16, 7)
    s.dot([(8, 14), (9, 15), (18, 15), (19, 14)], INK)
    s.dot([(12, 21), (13, 21), (14, 21), (15, 21)], INK)
    s.part(E((11, 2, 16, 7)), CORAL, spec=True)
    return s.done()


def moss_pebble():        # 이끼 돌멩이 (탱커·무덤덤)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(E((4, 9, 23, 26)), STONE)
    s.part(U(E((5, 7, 21, 15)), R((5, 11, 21, 13))), MOSS, spec=False)
    s.part(P([(14, 8), (16, 1), (17, 8)]), LEAF, spec=False)
    s.eyes_dot(10, 17, 6)
    s.dot([(12, 21), (13, 21), (14, 21)], STONE[4])
    s.dot([(7, 14), (20, 15)], MOSS[1])
    return s.done()


def coral_bud():          # 산호 꼬마 (탱커·수줍)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(L([(9, 12), (6, 4)], 3), CORAL, spec=False); s.part(L([(18, 12), (21, 3)], 3), CORAL, spec=False)
    s.part(L([(13, 10), (13, 2)], 3), CORAL, spec=False)
    s.part(U(E((6, 9, 21, 26)), R((6, 18, 21, 24))), CORAL)
    s.eyes_cute(9, 15, 7, h=2)
    s.dot([(13, 20), (14, 20)], INK)
    for p in ((5, 4), (22, 3), (13, 1)): s.dot([p], CORAL[0])
    return s.done()


def dandelion_puff():     # 민들레 솜털 (힐러·귀여움)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(L([(13, 17), (13, 24)], 2), LEAF, spec=False)
    s.part(P([(13, 21), (7, 18), (9, 23)]), LEAF, spec=False); s.part(P([(14, 22), (20, 19), (18, 24)]), LEAF, spec=False)
    s.part(E((4, 2, 23, 19)), MINT)
    for p in ((5, 6), (8, 2), (14, 1), (20, 3), (23, 9), (22, 15), (5, 14)): s.dot([p], W)
    s.eyes_happy(9, 10, 6)
    s.dot([(13, 13), (14, 13)], INK)
    s.part(E((10, 23, 17, 27)), LEAF, spec=False)
    return s.done()


def cloud_nap():          # 구름 꼬마 (힐러·졸림)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(U(E((2, 11, 12, 21)), E((7, 6, 20, 18)), E((15, 10, 25, 21)), E((4, 14, 23, 23))), CLOUD)
    s.eyes_sleepy(9, 15, 7)
    s.dot([(13, 18), (14, 18)], INK)
    s.dot([(7, 17), (8, 17), (20, 17), (21, 17)], PINK)
    for i, (x, y) in enumerate(((21, 2), (24, 0))):
        s.dot([(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 2), (x + 1, y + 2)], LILAC[3])
    return s.done()


def leaf_sprite():        # 잎사귀 요정 (힐러·장난)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(P([(12, 12), (2, 6), (5, 15)]), MINT, spec=False); s.part(P([(15, 12), (25, 6), (22, 15)]), MINT, spec=False)
    s.part(U(E((9, 17, 18, 26)), R((10, 16, 17, 20))), LEAF)
    HAIR = pal('#e8ffd0', '#8fd86a', '#5cb24e', '#3a8a40', '#24602e')
    s.part(U(E((5, 5, 22, 19)), R((5, 11, 8, 20)), R((19, 11, 22, 20))), HAIR, spec=False)
    s.part(E((8, 8, 19, 19)), SKIN, spec=False)
    s.part(P([(7, 11), (9, 6), (13, 5), (18, 6), (20, 11), (17, 9), (15, 11), (13, 9), (11, 11), (9, 9)]), HAIR, spec=False)
    s.part(P([(6, 7), (13, 0), (21, 7), (18, 6), (13, 3), (9, 6)]), LEAF, spec=False)
    s.eyes_cute(10, 12, 6, h=2)
    s.dot([(12, 16), (13, 17), (14, 17), (15, 16)], INK)
    return s.done()


def pinwheel():           # 바람개비 정령 (힐러·명랑)
    OFF[0] = 0; SC[:] = MINI; s = Spr()
    s.part(L([(13, 14), (13, 26)], 2), WOOD, spec=False)
    for pts, P_ in (([(13, 9), (13, 1), (20, 5)], RED), ([(14, 10), (22, 10), (18, 17)], GOLD),
                    ([(13, 11), (13, 19), (6, 15)], AQUA), ([(12, 10), (4, 10), (8, 3)], LEAF)):
        s.part(P(pts), P_, spec=False)
    s.part(E((9, 6, 18, 15)), MINT)
    s.eyes_happy(10, 9, 4, blush=False)
    s.dot([(13, 12), (14, 12)], INK)
    s.part(E((9, 23, 18, 27)), WOOD, spec=False)
    return s.done()


MINIONS = [
    ('m_fire_pup', '불씨 몽이', 'dealer', ember_pup), ('m_fire_slime', '불꽃 슬라임', 'dealer', flame_slime),
    ('m_fire_wisp', '도깨비불', 'dealer', will_wisp), ('m_fire_shroom', '화산 버섯', 'dealer', lava_shroom),
    ('m_water_jelly', '방울 젤리', 'tank', bubble_jelly), ('m_water_clam', '조개 기사', 'tank', clam_guard),
    ('m_water_pebble', '이끼 돌멩이', 'tank', moss_pebble), ('m_water_coral', '꼬마 산호', 'tank', coral_bud),
    ('m_wind_puff', '민들레 솜털', 'healer', dandelion_puff), ('m_wind_cloud', '구름 꼬마', 'healer', cloud_nap),
    ('m_wind_leaf', '잎사귀 요정', 'healer', leaf_sprite), ('m_wind_pinwheel', '바람개비', 'healer', pinwheel),
]


# ================= 보스 9 (40칸 좌표, 46x46 캔버스 · 여백 3) =================
def BSpr():
    OFF[0] = 3; SC[:] = [1.0, 0.0, 0.0]; return Spr(46)


def _fin(s):
    im = s.done(); OFF[0] = 0; return im

def crown(s, x, y, w=11, P_=GOLD, gem=(230, 60, 80)):
    s.part(U(R((x, y + 3, x + w, y + 6)), P([(x, y + 3), (x + 1, y), (x + 3, y + 3)]),
             P([(x + w // 2 - 1, y + 3), (x + w // 2, y - 1), (x + w // 2 + 2, y + 3)]),
             P([(x + w - 3, y + 3), (x + w - 1, y), (x + w, y + 3)])), P_, spec=False)
    s.dot([(x + w // 2, y + 4), (x + w // 2 + 1, y + 4)], gem); s.dot([(x + w // 2, y + 4)], (255, 200, 210))


def b_slime_king():       # 뉴비 · 말랑대장 (탱커)
    s = BSpr()
    s.part(P([(8, 16), (32, 16), (36, 36), (4, 36)]), RED, spec=False)
    s.part(U(E((3, 10, 36, 39)), R((3, 26, 36, 37))), AQUA)
    for b in ((9, 15, 12, 18), (28, 30, 30, 32)):
        s.part(E(b), pal('#ffffff', '#e8fcff', '#b4f0ff'), spec=False, rim=False)
    crown(s, 14, 4, 12)
    s.eyes_cute(12, 22, 13, h=4)
    s.dot([(17, 30), (18, 31), (19, 31), (20, 31), (21, 31), (22, 30)], INK); s.dot([(19, 32), (20, 32)], RED[2])
    return _fin(s)


def b_dokkaebi():         # 쉬움 · 도깨비 장군 (딜러)
    s = BSpr()
    s.part(L([(30, 38), (36, 10)], 4), WOOD, spec=False)
    s.part(U(E((31, 2, 39, 16))), WOOD)
    s.dot([(33, 5), (36, 8), (34, 11), (37, 13)], GOLD[1])
    s.part(U(R((10, 24, 29, 39)), E((8, 22, 31, 32))), NAVY)
    s.part(R((10, 30, 29, 33)), GOLD, spec=False)
    s.part(P([(8, 14), (11, 2), (14, 9), (19, 0), (23, 8), (28, 1), (31, 14)]), FLAME_Y, spec=False)
    s.part(E((9, 7, 30, 27)), RED)
    s.part(P([(10, 10), (7, 1), (14, 8)]), GOLD, spec=False); s.part(P([(29, 10), (32, 1), (25, 8)]), GOLD, spec=False)
    s.eyes_glow(12, 14, 11, (255, 236, 120), slant=2, length=4)
    s.flat(R((14, 21, 25, 23)), INK); s.dot([(15, 21), (24, 21), (16, 23), (23, 23)], W)
    return _fin(s)


def b_bronze_golem():     # 브론즈 · 청동 기사 골렘 (탱커)
    s = BSpr()
    s.part(U(R((12, 30, 17, 39)), R((22, 30, 27, 39))), BRONZE, spec=False)
    s.part(E((1, 13, 13, 26)), BRONZE); s.part(E((26, 13, 38, 26)), BRONZE)
    s.part(U(R((9, 15, 30, 33)), E((9, 12, 30, 22))), BRONZE)
    s.part(E((15, 18, 24, 27)), AQUA)
    s.part(U(R((12, 2, 27, 15)), E((12, 0, 27, 8))), BRONZE)
    s.flat(R((14, 7, 25, 9)), INK); s.flat(R((19, 4, 20, 13)), INK)
    s.dot([(15, 8), (16, 8), (23, 8), (24, 8)], AQUA[1])
    s.part(P([(18, 0), (20, -4), (22, 0)]), RED, spec=False)
    s.part(U(R((0, 22, 8, 34)), P([(0, 34), (8, 34), (4, 38)])), STONE)
    s.dot([(4, 26), (4, 27), (3, 27), (5, 27), (4, 28)], GOLD[1])
    for p in ((11, 17), (28, 17), (11, 31), (28, 31)): s.dot([p], BRONZE[0])
    return _fin(s)


def b_wind_queen():       # 보통 · 바람 요정 여왕 (힐러)
    s = BSpr()
    s.part(P([(19, 16), (1, 3), (2, 20), (10, 24)]), pal('#ffffff', '#eafff7', '#c8f2e4', '#9adcc8', '#6cb8a6'), spec=False)
    s.part(P([(21, 16), (39, 3), (38, 20), (30, 24)]), pal('#ffffff', '#eafff7', '#c8f2e4', '#9adcc8', '#6cb8a6'), spec=False)
    s.part(P([(13, 22), (27, 22), (33, 39), (7, 39)]), LEAF)
    s.part(P([(10, 6), (30, 6), (33, 30), (28, 22), (12, 22), (7, 30)]), MINT)
    s.part(E((13, 7, 27, 22)), SKIN)
    s.part(P([(12, 10), (20, 4), (28, 10), (25, 9), (20, 7), (15, 9)]), MINT, spec=False)
    crown(s, 15, 1, 10, LEAF, (255, 120, 170))
    s.eyes_happy(15, 14, 7, blush=True)
    s.dot([(19, 18), (20, 18)], RED[2])
    for p in ((4, 30), (36, 28), (2, 12), (37, 11), (20, 37)): s.dot([p], W)
    return _fin(s)


def b_silver_knight():    # 실버 · 은빛 기사 (딜러)
    s = BSpr()
    s.part(P([(10, 14), (30, 14), (35, 39), (5, 39)]), RED)
    s.part(L([(33, 38), (38, 4)], 3), SILVER, spec=False); s.dot([(38, 3), (39, 2)], W)
    s.part(R((29, 26, 36, 28)), GOLD, spec=False)
    s.part(U(R((12, 18, 28, 37)), E((12, 15, 28, 25))), SILVER)
    s.part(E((6, 15, 15, 23)), SILVER); s.part(E((25, 15, 34, 23)), SILVER)
    s.part(R((18, 20, 21, 34)), GOLD, spec=False)
    s.part(P([(17, 4), (21, -2), (26, 1), (22, 6)]), EMBER, spec=False)
    s.part(U(R((12, 4, 27, 17)), E((12, 1, 27, 10))), SILVER)
    s.flat(R((14, 9, 25, 11)), INK)
    s.dot([(15, 10), (16, 10), (17, 10), (22, 10), (23, 10), (24, 10)], (255, 170, 60)); s.dot([(16, 10), (23, 10)], (255, 240, 160))
    s.flat(R((19, 12, 20, 15)), SILVER[3])
    return _fin(s)


def b_magma_titan():      # 어려움 · 용암 거인 (딜러)
    s = BSpr()
    s.part(E((0, 18, 12, 32)), LAVA); s.part(E((28, 18, 40, 32)), LAVA)
    s.part(U(R((9, 16, 31, 39)), E((7, 8, 33, 28))), LAVA)
    for pts in ([(12, 12), (15, 18), (13, 26)], [(27, 11), (24, 19), (27, 27)], [(18, 30), (21, 38)], [(3, 24), (8, 26)], [(32, 23), (37, 26)]):
        s.flat(L(pts), EMBER[2])
    s.dot([(15, 18), (24, 19), (20, 34)], FLAME_Y[1])
    s.part(P([(11, 9), (14, 0), (17, 6), (20, -2), (23, 6), (26, 0), (29, 9)]), FLAME_Y, spec=False)
    s.eyes_glow(12, 14, 11, (255, 220, 90), slant=2, length=5)
    s.flat(R((15, 22, 25, 24)), EMBER[3]); s.dot([(16, 22), (18, 22), (20, 22), (22, 22), (24, 22)], FLAME_Y[1])
    return _fin(s)


def b_gold_jelly():       # 골드 · 황금 해파리 여왕 (탱커)
    s = BSpr()
    for i, x in enumerate((7, 12, 17, 22, 27, 32)):
        s.part(L([(x, 22), (x + (2 if i % 2 else -2), 30), (x, 39)], 2), LILAC, spec=False)
    s.part(U(E((2, 6, 37, 30)), R((2, 18, 37, 24))), CORAL)
    s.part(R((2, 23, 37, 25)), GOLD, spec=False)
    for x in range(5, 36, 5): s.dot([(x, 26), (x, 27)], GOLD[1])
    crown(s, 13, 0, 13)
    s.dot([(11, 17), (12, 16), (13, 16), (14, 17), (25, 17), (26, 16), (27, 16), (28, 17)], INK)
    s.dot([(10, 15), (29, 15)], INK)
    s.dot([(9, 19), (10, 19), (29, 19), (30, 19)], PINK)
    s.dot([(19, 20), (20, 20)], INK)
    return _fin(s)


def b_dark_lord():        # 극악 · 흑염 마왕 (딜러)
    s = BSpr()
    s.part(P([(6, 14), (34, 14), (40, 39), (0, 39)]), RED)
    s.part(P([(8, 18), (32, 18), (36, 39), (4, 39)]), DARK)
    s.part(U(R((11, 18, 29, 39)), E((11, 14, 29, 26))), DARK)
    s.part(E((5, 15, 15, 24)), DARK); s.part(E((25, 15, 35, 24)), DARK)
    s.part(P([(17, 22), (23, 22), (20, 28)]), EMBER, spec=False)
    s.part(P([(9, 7), (13, 0), (17, 4), (20, -1), (23, 4), (27, 0), (31, 7), (30, 16), (10, 16)]), EMBER, spec=False)
    s.part(E((12, 4, 28, 19)), pal('#f4ecfa', '#e2d4f0', '#c8b4dc', '#a088bc', '#6c5888'))
    s.flat(R((13, 9, 27, 13)), (60, 40, 80))
    s.part(P([(12, 8), (5, 2), (8, 0), (14, 5)]), GOLD, spec=False); s.part(P([(28, 8), (35, 2), (32, 0), (26, 5)]), GOLD, spec=False)
    s.eyes_glow(14, 10, 8, (255, 70, 70), slant=2, length=4)
    s.dot([(17, 16), (18, 16), (19, 16), (20, 15), (21, 15)], INK)
    return _fin(s)


def b_crystal_dragon():   # 다이아몬드 · 수정 용왕 (탱커)
    s = BSpr()
    s.part(P([(4, 20), (12, 14), (14, 30), (2, 34)]), CRYS); s.part(P([(36, 20), (28, 14), (26, 30), (38, 34)]), CRYS)
    s.part(P([(8, 22), (32, 22), (36, 39), (4, 39)]), CRYS)
    s.part(P([(16, 33), (20, 29), (24, 33), (20, 38)]), pal('#ffffff', '#ffd6f0', '#ff9ad8', '#e060b0', '#a03a8a'), spec=True)
    s.part(U(E((10, 6, 30, 24)), P([(13, 18), (27, 18), (24, 27), (16, 27)])), CRYS)
    s.part(P([(12, 10), (6, 0), (15, 7)]), LILAC, spec=False); s.part(P([(28, 10), (34, 0), (25, 7)]), LILAC, spec=False)
    s.part(P([(18, 6), (20, 0), (22, 6)]), LILAC, spec=False)
    s.flat(L([(12, 12), (18, 14)]), CRYS[4]); s.flat(L([(28, 12), (22, 14)]), CRYS[4])
    s.eyes_glow(12, 14, 11, (120, 240, 255), slant=2, length=5)
    s.dot([(18, 24), (22, 24)], CRYS[4]); s.flat(L([(16, 27), (24, 27)]), CRYS[4])
    for y in (12, 16, 20): s.dot([(9, y), (31, y)], LILAC[2])
    for p in ((1, 6), (38, 7), (3, 14), (37, 15), (20, 38)): s.dot([p], W)
    return _fin(s)


BOSSES = [
    ('boss_tutorial', '말랑대장', '뉴비', 'tank', b_slime_king), ('boss_easy', '도깨비 장군', '쉬움', 'dealer', b_dokkaebi),
    ('boss_bronze', '청동 기사 골렘', '브론즈', 'tank', b_bronze_golem), ('boss_normal', '바람 요정 여왕', '보통', 'healer', b_wind_queen),
    ('boss_silver', '은빛 기사', '실버', 'dealer', b_silver_knight), ('boss_hard', '용암 거인', '어려움', 'dealer', b_magma_titan),
    ('boss_gold', '황금 해파리 여왕', '골드', 'tank', b_gold_jelly), ('boss_extreme', '흑염 마왕', '극악', 'dealer', b_dark_lord),
    ('boss_diamond', '수정 용왕', '다이아몬드', 'tank', b_crystal_dragon),
]
