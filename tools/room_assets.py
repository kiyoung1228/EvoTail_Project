"""마이룸 그림 내보내기: assets/my_room/ (배경 낮·밤, 트로피 16종 달성·아직, room.json 위치값).
글씨·트로피·동물은 게임 코드가 그 위에 그린다. 숫자는 room.json에서 읽을 것."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import battle_mock as B
import room_mock as R

W, H = 640, 360
INK = K.INK
SHELF = dict(x=12, y=70, cols=4, rows=4, cell=40, rowh=42, n=2)
BOARD = (196, 132, 206, 96)
DIARY = (412, 70, 218, 128)
PLATE = (37, 248, 120, 18)
RUG = (320, 312, 140, 32)
CUSHION = (520, 300)


def background(night):
    base = R.room(floor_y=246, window=None)
    R.window2(base, 248, 40, 102, 60, night)
    d = ImageDraw.Draw(base)
    keep = R.ACH; R.ACH = []                                  # 빈 진열장 (트로피는 게임이 그림)
    R.shelf(base, SHELF['x'], SHELF['y'], SHELF['cols'], SHELF['rows'], cell=SHELF['cell'], n=SHELF['n'], rowh=SHELF['rowh'])
    R.ACH = keep
    x, y, w, h = BOARD                                         # 칠판 (글씨 없이)
    d.rectangle((x, y, x + w, y + h), fill=K.WOOD[1], outline=INK)
    d.rectangle((x + 5, y + 5, x + w - 5, y + h - 5), fill=(52, 92, 72), outline=INK)
    d.rectangle((x + 10, y + h - 4, x + w - 10, y + h + 2), fill=K.WOOD[2], outline=INK)
    d.rectangle((x + w - 30, y + h - 6, x + w - 22, y + h - 3), fill=(250, 250, 250))
    d.line((x + 20, y + 25, x + w - 20, y + 25), fill=(110, 150, 126))
    R.desk(base, 412, 204, 218)
    x, y, w, h = DIARY                                         # 일기장 (글씨 없이, 줄만)
    d.rectangle((x + 3, y + 3, x + w + 3, y + h + 3), fill=(120, 70, 140))
    d.rectangle((x, y, x + w, y + h), fill=(252, 244, 226), outline=INK)
    d.rectangle((x, y, x + w, y + 22), fill=(170, 110, 190), outline=INK)
    for rx in range(x + 10, x + w - 6, 14): d.ellipse((rx, y - 4, rx + 5, y + 4), fill=(200, 200, 210), outline=INK)
    for k in range(6): d.line((x + 6, y + 42 + k * 17, x + w - 6, y + 42 + k * 17), fill=(226, 210, 196))
    d.rectangle((x + w - 16, y + h - 2, x + w - 10, y + h + 10), fill=(220, 70, 70))
    R.rug(base, *RUG); R.cushion(base, *CUSHION); R.plant(base, 186, 230)
    ImageDraw.Draw(base).rectangle((0, 0, W, 25), fill=(0, 0, 0, 0))     # 상단 바 자리 투명
    return base


def layout():
    s = SHELF; slots = []
    for i, (code, name, _) in enumerate(R.ACH):
        r, c = divmod(i, s['cols'])
        sy = s['y'] + 8 + r * s['rowh']
        slots.append({'id': code, 'x': s['x'] + 6 + c * s['cell'] + (s['cell'] - 16 * s['n']) // 2, 'y': sy + s['rowh'] - 6 - 16 * s['n']})
    bx, by, bw, bh = BOARD; dx, dy, dw, dh = DIARY
    cells = []
    # 칸 = 칠판 초록 면(bx+5 ~ bx+bw-5) 안쪽 8px 여백 안을 같은 폭 두 칸으로: 아이콘 12 + 3px + 이름(두 글자) + 숫자.
    # 숫자 오른쪽 끝 = 칸 끝 - 4 (오른쪽 칸은 초록 면 테두리에서 12px, 9999까지 들어감)
    face0, face1 = bx + 5 + 8, bx + bw - 5 - 8
    col_w = (face1 - face0) // 2
    for k in range(6):
        ix = face0 + (k % 2) * col_w; cy = by + 38 + (k // 2) * 20
        cells.append({'icon': [ix, cy - 6], 'label_left': [ix + 12 + 3, cy], 'value_right': [ix + col_w - 4, cy]})
    return {
        '_note': '논리 좌표(640×360). 배경 png는 2배 → ½로 그대로. 트로피 png는 원본 16의 4배(64) → ½ = 32로 그림',
        'floor_y': 246,
        'window': [238, 26, 362, 132],
        'shelf': {'rect': [s['x'], s['y'], s['x'] + s['cols'] * s['cell'] + 12, s['y'] + s['rows'] * s['rowh'] + 14],
                  'trophy_size': 32, 'slots': slots,
                  'shadow': {'dx0': 2, 'dy0': 28, 'dx1': 30, 'dy1': 33, 'color': [90, 56, 42]}},
        'plate': {'rect': list(PLATE), 'text': '트로피 {got} / {total}'},
        'board': {'rect': list(BOARD), 'title_center': [bx + bw // 2, by + 16], 'title': '나의 기록',
                  'title_color': [250, 230, 140], 'text_color': [236, 240, 226], 'value_color': [255, 255, 255], 'cells': cells},
        'diary': {'rect': list(DIARY), 'title_left': [dx + 8, dy + 13], 'title': '일기장', 'title_color': [255, 246, 230], 'title_shadow': [110, 60, 130],
                  'sub_right': [dx + dw - 8, dy + 13], 'sub': '최근 일', 'sub_color': [240, 220, 246],
                  'lines': [{'icon': [dx + 7, dy + 28 + k * 17], 'text_left': [dx + 22, dy + 34 + k * 17]} for k in range(6)],
                  'text_max_w': dw - 30},
        'rug': {'center': [RUG[0], RUG[1]], 'rx': RUG[2], 'ry': RUG[3]},
        'cushion': {'center': list(CUSHION)},
    }


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else R.GAME / 'assets' / 'my_room'
    K.FONT_DIR = R.GAME / 'assets' / 'fonts'; B.SPR = R.GAME / 'assets' / 'sprites'
    (out / 'trophies').mkdir(parents=True, exist_ok=True)
    for nt, nm in ((False, 'day'), (True, 'night')):
        background(nt).resize((W * 2, H * 2), Image.NEAREST).save(out / f'room_{nm}.png')
    for code, name, _ in R.ACH:
        R.trophy(code, True, 4).save(out / 'trophies' / f'{code}.png')
        R.trophy(code, False, 4).save(out / 'trophies' / f'{code}_locked.png')
    (out / 'room.json').write_text(json.dumps(layout(), ensure_ascii=False, indent=1), encoding='utf-8')
