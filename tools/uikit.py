"""EvoTail 도트 UI 키트. 모든 조각은 1배(논리 픽셀)로 그리고 화면에서 2배 확대한다."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = None
INK = (46, 32, 38)
WOOD = [(84, 52, 36), (122, 78, 48), (162, 108, 64), (198, 146, 92), (226, 182, 124)]
PAPER = [(214, 190, 150), (236, 216, 178), (250, 236, 206), (255, 246, 224)]
TEXT = (70, 46, 34)
TEXT_SOFT = (138, 108, 82)
BTN = {
    'green':  [(40, 92, 52), (70, 140, 76), (98, 176, 98), (140, 206, 120)],
    'orange': [(120, 56, 28), (196, 104, 52), (236, 146, 72), (255, 190, 112)],
    'purple': [(60, 40, 104), (104, 76, 168), (140, 108, 208), (184, 156, 236)],
    'red':    [(110, 34, 36), (180, 64, 60), (220, 92, 80), (250, 140, 120)],
    'brown':  [(70, 44, 30), (120, 80, 50), (162, 112, 70), (204, 154, 100)],
    'gray':   [(96, 90, 86), (150, 142, 134), (184, 176, 166), (214, 208, 198)],
    'blue':   [(30, 60, 110), (60, 110, 180), (90, 150, 220), (150, 196, 245)],
    'gold':   [(120, 78, 16), (184, 128, 28), (226, 172, 40), (255, 218, 104)],   # 특급·알 확률
}
ROLE = {'dealer': 'orange', 'tank': 'blue', 'healer': 'green'}


def font(name, size):
    return ImageFont.truetype(str(FONT_DIR / name), size)

F_TITLE = lambda: font('Galmuri11-Bold.ttf', 12)
F_BODY = lambda: font('Galmuri11.ttf', 12)
F_SMALL = lambda: font('Galmuri9.ttf', 10)
F_BIG = lambda: font('Galmuri14.ttf', 15)


def draw_text(im, xy, s, f, fill=TEXT, anchor='la', shadow=None):
    d = ImageDraw.Draw(im); d.fontmode = '1'
    if shadow:
        d.text((xy[0] + 1, xy[1] + 1), s, font=f, fill=shadow, anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)
    return d.textlength(s, font=f)


# ---------- 9-slice 조각 ----------
def piece_panel():
    """양피지 + 나무 테두리 창. 32x32, 가장자리 8."""
    im = Image.new('RGBA', (32, 32)); p = im.load()
    for y in range(32):
        for x in range(32):
            e = min(x, y, 31 - x, 31 - y)
            if e == 0:
                c = INK
            elif e <= 3:
                c = WOOD[4] if (x < 4 or y < 4) and e == 1 else WOOD[3] if (x < 16 and y < 16) else WOOD[2]
                if e == 3:
                    c = WOOD[1]
                if (x > 27 or y > 27) and e in (1, 2):
                    c = WOOD[1] if e == 1 else WOOD[2]
            elif e == 4:
                c = INK
            elif e == 5:
                c = PAPER[1]
            else:
                c = PAPER[3] if y < 9 else PAPER[2]
            p[x, y] = c + (255,) if len(c) == 3 else c
    for cx, cy in ((2, 2), (29, 2), (2, 29), (29, 29)):            # 못
        p[cx, cy] = (236, 210, 150, 255)
    for x, y in ((0, 0), (31, 0), (0, 31), (31, 31)):
        p[x, y] = (0, 0, 0, 0)
    return im, 8


def piece_card(selected=False):
    """목록 칸. 24x24, 가장자리 6."""
    im = Image.new('RGBA', (24, 24)); p = im.load()
    edge = (236, 150, 60) if selected else (196, 160, 116)
    fill = (255, 228, 176) if selected else (252, 240, 214)
    for y in range(24):
        for x in range(24):
            e = min(x, y, 23 - x, 23 - y)
            if e == 0:
                c = (120, 80, 50) if not selected else (176, 90, 30)
            elif e == 1:
                c = edge
            elif e == 2 and selected:
                c = (255, 206, 120)
            else:
                c = fill if y < 20 else tuple(v - 10 for v in fill)
            p[x, y] = c + (255,)
    for x, y in ((0, 0), (23, 0), (0, 23), (23, 23)):
        p[x, y] = (0, 0, 0, 0)
    return im, 6


def piece_button(color, state='normal'):
    """24x16 버튼, 가장자리 5. 아래 2줄이 그림자(입체)."""
    pal = BTN['gray'] if state == 'disabled' else BTN[color]
    if state == 'hover':
        pal = [tuple(min(255, v + 18) for v in c) for c in pal]
    im = Image.new('RGBA', (24, 16)); p = im.load()
    press = state == 'pressed'
    top = 1 if press else 0
    for y in range(16):
        for x in range(24):
            if y < top:
                continue
            e = min(x, 23 - x)
            body_bottom = 15 if press else 13
            if y > body_bottom:
                c = pal[0] if 0 < x < 23 else None
            elif y == top or y == body_bottom or e == 0:
                c = INK
            elif y == top + 1:
                c = pal[3]
            elif e == 1:
                c = pal[3] if x < 12 else pal[1]
            elif y >= body_bottom - 2:
                c = pal[1]
            else:
                c = pal[2]
            if c:
                p[x, y] = c + (255,)
    for x, y in ((0, top), (23, top), (0, 15), (23, 15)):
        p[x, y] = (0, 0, 0, 0)
    return im, 5


def piece_gauge():
    """게이지 틀 16x8, 가장자리 3. 채움은 코드로 그린다."""
    im = Image.new('RGBA', (16, 8)); p = im.load()
    for y in range(8):
        for x in range(16):
            e = min(x, y, 15 - x, 7 - y)
            c = INK if e == 0 else (WOOD[3] if e == 1 and y < 4 else WOOD[2] if e == 1 else (70, 52, 46))
            p[x, y] = c + (255,)
    for x, y in ((0, 0), (15, 0), (0, 7), (15, 7)):
        p[x, y] = (0, 0, 0, 0)
    return im, 3


def piece_ribbon(color='red'):
    """제목 리본 40x16, 가장자리 9 (양 끝이 V자로 잘림)."""
    pal = BTN[color]
    im = Image.new('RGBA', (40, 16)); p = im.load()
    for y in range(16):
        for x in range(40):
            notch = abs(y - 7.5) // 2
            if x < notch or x > 39 - notch:
                continue
            if y in (0, 15) or x == int(notch) or x == 39 - int(notch):
                c = INK
            elif y == 1:
                c = pal[3]
            elif y >= 13:
                c = pal[1]
            else:
                c = pal[2]
            p[x, y] = c + (255,)
    for y in range(2, 14):
        p[5, y] = pal[1] + (255,); p[34, y] = pal[1] + (255,)
    return im, 9


def nine(piece, margin, w, h):
    src, m = piece, margin
    sw, sh = src.size
    out = Image.new('RGBA', (w, h))
    cols = [(0, m, 0, m), (m, sw - m, m, w - m), (sw - m, sw, w - m, w)]
    rows = [(0, m, 0, m), (m, sh - m, m, h - m), (sh - m, sh, h - m, h)]
    for sx0, sx1, dx0, dx1 in cols:
        for sy0, sy1, dy0, dy1 in rows:
            if dx1 <= dx0 or dy1 <= dy0:
                continue
            part = src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.paste(part, (dx0, dy0))
    return out


# ---------- 아이콘 12x12 ----------
ICON_ROWS = {
 'heart': ("............", ".OO....OO...", "ORRO..ORRO..", "ORWRRORRRRO.", "ORRRRRRRRRO.", "ORRRRRRRRRO.", ".ORRRRRRRO..", "..ORRRRRO...", "...ORRRO....", "....ORO.....", ".....O......", "............"),
 'sword': ("..........OO", ".........OWO", "........OWO.", ".......OWO..", "......OWO...", ".O...OWO....", ".OO.OWO.....", "..OOWO......", "..OBOO......", ".OBOOO......", "OBO..OO.....", "OO..........."),
 'shield': ("............", ".OOOOOOOOO..", ".OWWBBBBBO..", ".OWBBBBBBO..", ".OWBBYBBBO..", ".OWBYYYBBO..", ".OBBBYBBBO..", "..OBBBBBO...", "..OBBBBBO...", "...OBBBO....", "....OOO.....", "............"),
 'wing': ("............", "........OO..", "......OOWWO.", "....OOWWWWO.", "..OOWWWWGWO.", ".OWWWWWGGWO.", "OWWWWWGGGO..", "OWWWGGGGO...", ".OWGGGOO....", "..OOOO......", "............", "............"),
 'meat': ("............", "......OOOO..", ".....ORRRRO.", "....ORRWRRRO", "....ORRRRRRO", "....ORRRRRRO", "...OORRRRRO.", "..OWWOOOOO..", ".OWWO.......", ".OWO........", "..O.........", "............"),
 'smile': ("............", "...OOOOOO...", "..OYYYYYYO..", ".OYYYYYYYYO.", ".OYOYYYOYYO.", ".OYYYYYYYYO.", ".OYOYYYYOYO.", ".OYYOOOOYYO.", "..OYYYYYYO..", "...OOOOOO...", "............", "............"),
 'frown': ("............", "...OOOOOO...", "..OSSSSSSO..", ".OSSSSSSSSO.", ".OSOSSSOSSO.", ".OSSSSSSSSO.", ".OSSOOOOSSO.", ".OSOSSSSOSO.", "..OSSSSSSO..", "...OOOOOO...", "............", "............"),  # 기분 나쁨 (회색 찡그린 얼굴)
 'lock': ("............", "....OOOO....", "...O....O...", "...O....O...", "..OOOOOOOO..", "..OYYYYYYO..", "..OYYOOYYO..", "..OYYOOYYO..", "..OYYYYYYO..", "..OOOOOOOO..", "............", "............"),  # 잠김
 'check': ("............", "...OOOOOO...", "..OKKKKKKO..", ".OKKKKKKWKO.", ".OKKKKKWWKO.", ".OKWKKWWKKO.", ".OKWWWWKKKO.", ".OKKWWKKKKO.", "..OKKKKKKO..", "...OOOOOO...", "............", "............"),  # 깬 단계
 'zzz': ("............", "......OOOOO.", "......OBBO..", ".......OO...", "......OBBOO.", "..OOOO.OOOO.", "..OBBO......", "...OO.......", "..OBBOO.....", "..OOOOO.....", "............", "............"),
 'coin': ("............", "...OOOOO....", "..OYYYYYO...", ".OYWYYYYYO..", ".OYWYOOYYO..", ".OYYYOYYYO..", ".OYYYOYYYO..", ".OYYOOOYYO..", "..OYYYYYO...", "...OOOOO....", "............", "............"),
 'sun': ("....Y..Y....", ".Y........Y.", "...OOOOO....", "..OYYYYYO...", "Y.OYWYYYO..Y", "..OYYYYYO...", "..OYYYYYO...", "Y.OYYYYYO..Y", "...OOOOO....", ".Y........Y.", "....Y..Y....", "............"),
 'snack': ("............", "..OOOOOOO...", ".OPPPPPPPO..", ".OPWPPPPPO..", ".OPPPOPPPO..", ".OOOOOOOOO..", ".OYYYYYYYO..", ".OYYYYYYYO..", ".OYYYYYYYO..", "..OOOOOOO...", "............", "............"),
 'home': ("............", ".....OO.....", "....ORRO....", "...ORRRRO...", "..ORRRRRRO..", ".OOOOOOOOOO.", "..OWWWWWWO..", "..OWBBWBBO..", "..OWBBWWWO..", "..OWWWWDDO..", "..OOOOOOOO..", "............"),
 'back': ("............", "....O.......", "...OO.......", "..OWO.......", ".OWWOOOOOOO.", "OWWWWWWWWWO.", ".OWWOOOOOOO.", "..OWO.......", "...OO.......", "....O.......", "............", "............"),
}
ICON_COL = {'O': INK, 'R': (228, 76, 76), 'W': (255, 252, 240), 'B': (120, 160, 220), 'Y': (250, 204, 70),
            'G': (200, 210, 230), 'P': (240, 150, 170), 'D': (140, 90, 60), 'S': BTN['gray'][2], 'K': BTN['green'][2]}


def icon(name):
    im = Image.new('RGBA', (12, 12)); p = im.load()
    for y, row in enumerate(ICON_ROWS[name]):
        for x, ch in enumerate(row[:12]):
            if ch in ICON_COL:
                p[x, y] = ICON_COL[ch] + (255,)
    return im


def export_kit(out):
    out.mkdir(parents=True, exist_ok=True)
    meta = {'scale_note': '1배 픽셀 조각. 화면에서는 2배로 키워 쓴다 (nearest).', 'nine_slice': {}}
    def save(name, pair):
        im, m = pair; im.save(out / f'{name}.png'); meta['nine_slice'][name] = {'size': list(im.size), 'margin': m}
    save('panel', piece_panel())
    save('card', piece_card()); save('card_selected', piece_card(True))
    for c in BTN:
        for st in ('normal', 'hover', 'pressed', 'disabled'):
            if c == 'gray' and st != 'normal':
                continue
            save(f'button_{c}_{st}', piece_button(c, st))
    save('gauge_frame', piece_gauge())
    for c in ('red', 'brown', 'green', 'gray'):      # gray = 전투 결과 "도망쳤다"
        save(f'ribbon_{c}', piece_ribbon(c))
    (out / 'icons').mkdir(exist_ok=True)
    for n in ICON_ROWS:
        icon(n).save(out / 'icons' / f'{n}.png')
    meta['icons'] = sorted(ICON_ROWS)
    meta['colors'] = {'text': TEXT, 'text_soft': TEXT_SOFT, 'ink': INK,
                      'gauge_fill': {k: v for k, v in BTN.items()}}
    (out / 'ui_kit.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
