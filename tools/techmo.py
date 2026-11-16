"""안내원 '테크모': 학사모 쓴 회색 까마귀 (32×32 손 도트). 프레임: idle / blink / wave(날개 펄럭) / talk(부리 벌림)."""
from PIL import Image

PAL = {
    'k': (44, 40, 52),      # 테두리
    'G': (150, 152, 166),   # 깃털 중간
    'g': (184, 186, 198),   # 깃털 밝음
    'h': (214, 216, 226),   # 하이라이트
    'd': (112, 114, 130),   # 깃털 어두움
    'w': (255, 255, 255),   # 흰자
    'p': (36, 32, 44),      # 검은자
    'b': (92, 88, 100),     # 부리
    'B': (140, 136, 148),   # 부리 윗면
    'c': (255, 168, 182),   # 볼
    'm': (48, 48, 62),      # 학사모
    'M': (88, 88, 108),     # 학사모 윗면
    'y': (250, 200, 60),    # 술
    'Y': (196, 140, 30),
    'r': (60, 56, 76),      # 가운
    'R': (92, 88, 112),     # 가운 밝음
    'l': (250, 246, 236),   # 흰 깃
    'f': (120, 116, 126),   # 발
}

IDLE = [
    '................................',
    '........kkkkkkkkkkkkkkkk........',
    '......kkMMMMMMMMMMMMMMMMkk......',
    '.....kmmmmmmmmmmmmmmmmmmmmk.....',
    '......kkmmmmmmmmmmmmmmmmkkyk....',
    '........kkmmmmmmmmmmmkkk..yk....',
    '.........kmmmmmmmmmmmk...kyk....',
    '........kGGGGGGGGGGGGGk..kYk....',
    '.......kGGhhGGGGGGGGGGGk..k.....',
    '......kGGhwwwwGGGGwwwwGGk.......',
    '......kGgwwwwwwGGwwwwwwgGk......',
    '.....kGGgwwwppwGGwwppwwgGGk.....',
    '.....kGgwwwpwpwGGwwpwpwwgGk.....',
    '.....kGgwwwppppggwwppppwgGk.....',
    '.....kGgwwwppppggwwppppwgGk.....',
    '.....kGggwwwppkBBkwppwwggGk.....',
    '.....kGcggwwwkBBBBkwwwggcGk.....',
    '......kGcggggkbbbbkggggcGk......',
    '......kdGggggkkbbkkggggGdk......',
    '.......kdGGgggkbbkgggGGdk.......',
    '........kkdGGGGkkGGGGdkk........',
    '...kkk....kkrrRlllRrrkk....kkk..',
    '..krrrkk.krrrrRlllRrrrrk.kkrrrk.',
    '..krRrrrkkrrrrrRlRrrrrrkkrrrRrk.',
    '...krRRrrrrrrrrrRrrrrrrrrrRRrk..',
    '....kkrRRrrrrrrrrrrrrrrrRRrkk...',
    '......kkkrrrrrrrrrrrrrrrkkk.....',
    '.........krrrrrrrrrrrrrk........',
    '..........krrrrrrrrrrrk.........',
    '...........kkkkkkkkkkk..........',
    '............kfk...kfk...........',
    '...........kffk...kffk..........',
]


def _fix(rows):
    return [r.ljust(32, '.')[:32] for r in rows]


EYE_WHITE = {9: (10, 13), 10: (9, 14), 11: (9, 14), 12: (9, 14), 13: (9, 14), 14: (9, 14), 15: (10, 13)}
PUPIL = {10: '.pp.', 11: 'pwpp', 12: 'pppp', 13: 'pppp', 14: '.pp.'}      # 왼쪽 위 흰 점 = 반짝


def _eyes(rows):
    rows = [list(r) for r in rows]
    for y in range(8, 17):                       # 예전 눈 지우기
        for x in list(range(8, 15)) + list(range(17, 25)):
            if rows[y][x] in 'wp': rows[y][x] = 'G'
    for off in (0, 9):
        for y, (a, b) in EYE_WHITE.items():
            for x in range(a + off, b + off + 1): rows[y][x] = 'w'
        rows[16][10 + off] = rows[16][13 + off] = 'G'
        for x in range(10 + off, 14 + off): rows[16][x] = 'd' if rows[16][x] in 'Gg' else rows[16][x]
        for y, pat in PUPIL.items():
            for i, ch in enumerate(pat):
                if ch != '.': rows[y][10 + off + i] = ch
    return [''.join(r) for r in rows]


def _render(rows, eyes=False):
    rows = _fix(rows)
    if eyes: rows = _eyes(rows)
    im = Image.new('RGBA', (32, 32)); px = im.load()
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in PAL: px[x, y] = PAL[ch] + (255,)
    return im


def _blink(rows):
    rows = [list(r) for r in _fix(rows)]
    for y in range(9, 16):
        for x in range(32):
            if rows[y][x] in 'wp': rows[y][x] = 'G' if y != 13 else 'k'
    for x in (10, 11, 12, 13, 19, 20, 21, 22):
        rows[13][x] = 'k'
    rows[12][9] = rows[12][14] = rows[12][18] = rows[12][23] = 'k'
    return [''.join(r) for r in rows]


def _talk(rows):
    rows = [list(r) for r in _fix(rows)]
    rows[17][14:18] = list('kppk'); rows[18][14:18] = list('kbbk')
    return [''.join(r) for r in rows]


WAVE_L = [
    (15, '.kk.......'),
    (16, 'kRrk......'),
    (17, 'krRrk.....'),
    (18, '.krRrk....'),
    (19, '..krrrk...'),
    (20, '...krrrk..'),
    (21, '....krrrkk'),
    (22, '.....kkrrr'),
]


def _wave(rows):
    """가운 소매(날개)를 위로 들어 반갑게 흔들기"""
    rows = [list(r) for r in _fix(rows)]
    for y in range(21, 27):
        for x in list(range(0, 10)) + list(range(22, 32)):
            if rows[y][x] in 'krR': rows[y][x] = '.'
    for y, seg in WAVE_L:
        for i, ch in enumerate(seg):
            if ch == '.': continue
            if rows[y][i] in '.': rows[y][i] = ch
            if rows[y][31 - i] in '.': rows[y][31 - i] = ch
    for y in (21, 22, 23):                       # 몸통 옆선 다시
        for x in (9, 22):
            if rows[y][x] == '.': rows[y][x] = 'k'
    return [''.join(r) for r in rows]


def frame(kind='idle', n=1):
    rows = IDLE
    if kind == 'blink': rows = _blink(IDLE)
    elif kind == 'talk': rows = _talk(IDLE)
    elif kind == 'wave': rows = _wave(IDLE)
    elif kind == 'wave_talk': rows = _talk(_wave(IDLE))
    im = _render(rows)
    if kind.startswith('flap'):
        im = flap(im, {'flap1': 3, 'flap2': 6, 'flap3': -2}[kind.split('_')[0]])
        if kind.endswith('_talk'): im = _render_talk_over(im)
    return _scale(im, n)


def _render_talk_over(im):
    t = _render(_talk(IDLE)); im.paste(t.crop((13, 16, 19, 20)), (13, 16)); return im


def flap(im, dy):
    """날개(가운 소매)만 dy픽셀 위로 올림 (음수 = 아래로). 몸통과 이음새는 가운 색으로 메움"""
    out = im.copy(); src = im.load(); po = out.load()
    wing = lambda x: x <= 9 or x >= 22
    for y in range(19, 28):
        for x in range(32):
            if wing(x): po[x, y] = (0, 0, 0, 0)
    moved = {}
    for y in range(19, 28):
        for x in range(32):
            if wing(x) and src[x, y][3]:
                dist = (9 - x) if x <= 9 else (x - 22)              # 몸에서 멀수록 더 많이 (날개 끝이 퍼덕)
                ny = y - round(dy * (dist + 1) / 8)
                if 0 <= ny < 32: po[x, ny] = src[x, y]; moved.setdefault(x, []).append(ny)
    r, R, k = PAL['r'] + (255,), PAL['R'] + (255,), PAL['k'] + (255,)
    for x in range(32):                                          # 날개 칸 틈 메우기
        ys = moved.get(x)
        if ys:
            for y in range(min(ys), max(ys) + 1):
                if not po[x, y][3]: po[x, y] = r
    for x in (8, 9, 22, 23):                                     # 어깨 이음새
        ys = [y for y in range(16, 30) if po[x, y][3] and po[x, y][:3] in (PAL['r'], PAL['R'])]
        for y in range(19, 25):
            if not po[x, y][3] or po[x, y][:3] == PAL['k']:
                if any(abs(y - yy) <= 3 for yy in ys): po[x, y] = r
    # 바깥 테두리 다시
    a = out.copy().load()
    for y in range(32):
        for x in range(32):
            if not a[x, y][3] and any(0 <= x + ex < 32 and 0 <= y + ey < 32 and a[x + ex, y + ey][3] and a[x + ex, y + ey][:3] != PAL['k']
                                      for ex, ey in ((1, 0), (-1, 0), (0, 1), (0, -1))) and 16 <= y <= 29:
                po[x, y] = k
    return out


def _scale(im, n):
    return im.resize((32 * n, 32 * n), Image.NEAREST) if n != 1 else im


if __name__ == '__main__':
    import sys
    kinds = ['idle', 'blink', 'talk', 'flap3', 'flap1', 'flap2']
    sheet = Image.new('RGBA', (len(kinds) * 272 + 16, 288), (196, 226, 190, 255))
    for i, k in enumerate(kinds):
        sheet.alpha_composite(frame(k, 8), (16 + i * 272, 16))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else 'techmo_sheet.png')
