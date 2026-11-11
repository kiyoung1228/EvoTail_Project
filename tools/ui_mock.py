"""도트 UI 키트로 다시 그린 '내 동물' 화면 목업 (640x360 → 1280x720)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import uikit as K

W, H = 640, 360


def sprite(spr_dir, key, stage, scale):
    im = Image.open(spr_dir / f'{key}_s{stage}.png').convert('RGBA').resize((28, 28), Image.NEAREST)
    return im.resize((28 * scale, 28 * scale), Image.NEAREST)


def paste(base, im, xy):
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


def button(base, x, y, w, h, label, color='green', state='normal', icon=None, f=None, sub=None):
    im, m = K.piece_button(color, state)
    paste(base, K.nine(im, m, w, h), (x, y))
    off = 1 if state == 'pressed' else 0
    f = f or K.F_TITLE()
    fill = (255, 255, 255) if state != 'disabled' else (238, 232, 224)
    shadow = K.BTN['gray' if state == 'disabled' else color][0]
    body_h = h - 2
    cy = y + body_h // 2 + off
    if sub:
        cy -= 6
    tw = ImageDraw.Draw(base).textlength(label, font=f)
    total = tw + (14 if icon else 0)
    tx = x + (w - total) / 2
    if icon:
        paste(base, K.icon(icon), (tx, cy - 6)); tx += 14
    K.draw_text(base, (tx, cy), label, f, fill, 'lm', shadow)
    if sub:
        K.draw_text(base, (x + w / 2, cy + 13), sub, K.F_SMALL(), (255, 246, 220), 'mm', shadow)


def gauge(base, x, y, w, h, value, maximum, color, cap_line=None):
    im, m = K.piece_gauge()
    paste(base, K.nine(im, m, w, h), (x, y))
    pal = K.BTN[color]
    inner_w = w - 4
    fw = int(inner_w * max(0, min(value, maximum)) / maximum) if maximum else 0
    d = ImageDraw.Draw(base)
    if fw > 0:
        d.rectangle((x + 2, y + 2, x + 1 + fw, y + h - 3), fill=pal[2])
        d.line((x + 2, y + 2, x + 1 + fw, y + 2), fill=pal[3])
        d.line((x + 2, y + h - 3, x + 1 + fw, y + h - 3), fill=pal[1])
    for i in range(1, 10):
        tx = x + 2 + inner_w * i // 10
        d.point((tx, y + h - 3), fill=(40, 28, 26) if tx > x + 1 + fw else pal[0])


CHIP_H = 16


def text_mid(base, cx, cy, text, f, fill, shadow=None):
    """실제 글자 모양(bbox) 기준 가운데 정렬 = GUI widgets.text_in과 같은 방식"""
    l, t, r, b = f.getbbox(text)
    K.draw_text(base, (round(cx - (l + r) / 2), round(cy - (t + b) / 2)), text, f, fill, 'la', shadow)


def chip(base, x, y, text, color, f=None):
    f = f or K.F_SMALL()
    pal = K.BTN[color]
    l, t, r, b = f.getbbox(text)
    w = (r - l) + 10
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + CHIP_H - 1), fill=pal[2], outline=K.INK)
    d.line((x + 1, y + 1, x + w - 1, y + 1), fill=pal[3])
    d.point([(x, y), (x + w, y), (x, y + CHIP_H - 1), (x + w, y + CHIP_H - 1)], fill=(0, 0, 0, 0))
    text_mid(base, x + w / 2 + .5, y + CHIP_H / 2, text, f, (255, 255, 255), pal[0])
    return w


def ribbon(base, x, y, w, text, color='red'):
    im, m = K.piece_ribbon(color)
    paste(base, K.nine(im, m, w, 18), (x, y))
    K.draw_text(base, (x + w / 2, y + 8), text, K.F_TITLE(), (255, 250, 236), 'mm', K.BTN[color][0])


def header(base, map_dir):
    d = ImageDraw.Draw(base)
    d.rectangle((0, 0, W, 25), fill=K.WOOD[2])
    for x in range(0, W, 40):                                                     # 나무 판자 이음새
        d.line((x, 2, x, 23), fill=K.WOOD[1])
    d.line((0, 1, W, 1), fill=K.WOOD[4]); d.line((0, 24, W, 24), fill=K.WOOD[1]); d.line((0, 25, W, 25), fill=K.INK)
    K.draw_text(base, (12, 13), 'EvoTail', K.F_TITLE(), (255, 236, 190), 'lm', K.WOOD[0])
    for (x0, x1, ic, txt) in ((240, 400, 'sun', '1일차 · 낮 14:20 · 맑음'), (540, 630, 'coin', '4,200')):
        pnl, m = K.piece_card()
        paste(base, K.nine(pnl, m, x1 - x0, 18), (x0, 4))
        paste(base, K.icon(ic), (x0 + 5, 7))
        if ic == 'coin':
            K.draw_text(base, (x1 - 7, 13), txt, K.F_TITLE(), K.TEXT, 'rm')
        else:
            K.draw_text(base, (x0 + 21, 13), txt, K.F_BODY(), K.TEXT, 'lm')


def main(out, map_dir, spr_dir):
    base = Image.open(map_dir / 'map_day.png').convert('RGBA').resize((W, H), Image.NEAREST)
    base = ImageEnhance.Brightness(base).enhance(.55)
    base = ImageEnhance.Color(base).enhance(.7)
    header(base, map_dir)

    # 뒤로 + 제목 리본
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 92, '내 동물', 'red')

    # 왼쪽 목록
    pnl, m = K.piece_panel()
    paste(base, K.nine(pnl, m, 176, 300), (8, 56))
    animals = [('dealer_normal_01', 1, '불씨여우', 'dealer', False, 'ok'), ('tank_normal_01', 1, '물방울수달', 'tank', True, 'warn'),
               ('healer_normal_01', 1, '산들오리', 'healer', True, 'ok'), ('tank_normal_02', 1, '물방울거북', 'tank', False, 'warn'),
               ('healer_special_01', 1, '산들학', 'healer', False, 'ok'), ('dealer_special_02', 2, '불꽃매', 'dealer', True, 'ok'),
               ('tank_special_03', 1, '물방울가재', 'tank', False, 'ok'), ('healer_normal_03', 1, '산들햄스터', 'healer', False, 'sick')]
    roles = {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}
    for i, (key, st, name, role, yard, state) in enumerate(animals):
        y = 66 + i * 35
        sel = key == 'dealer_special_02'
        c, cm = K.piece_card(sel)
        paste(base, K.nine(c, cm, 156, 32), (18, y))
        d = ImageDraw.Draw(base)
        d.rectangle((22, y + 3, 47, y + 28), fill=(232, 220, 190), outline=(176, 140, 100))
        paste(base, sprite(spr_dir, key, st, 1), (21, y + 2))
        K.draw_text(base, (52, y + 10), name, K.F_TITLE(), K.TEXT, 'lm')
        K.draw_text(base, (52, y + 23), f'{roles[role]} · {st}단계', K.F_SMALL(), K.BTN[K.ROLE[role]][1], 'lm')
        if yard:
            chip(base, 120, y + 4, '마당', 'green')
        ic = {'ok': 'heart', 'warn': 'meat', 'sick': 'zzz'}[state]
        paste(base, K.icon(ic), (157, y + 17))
    d = ImageDraw.Draw(base)
    d.rectangle((168, 70, 171, 340), fill=K.PAPER[1]); d.rectangle((168, 70, 171, 160), fill=K.WOOD[2])   # 스크롤 막대

    # 오른쪽 상세
    paste(base, K.nine(pnl, m, 444, 300), (190, 56))
    # 초상 + 받침
    d.rectangle((204, 70, 296, 162), fill=(204, 232, 170), outline=K.INK)
    d.rectangle((205, 71, 295, 82), fill=(222, 242, 190))
    d.ellipse((218, 140, 282, 156), fill=(130, 186, 100), outline=(80, 130, 70))
    paste(base, sprite(spr_dir, 'dealer_special_02', 2, 3), (208, 72))
    # 이름 + 태그
    K.draw_text(base, (308, 80), '불꽃매', K.F_BIG(), K.TEXT, 'lm')
    x = 308
    for t, c in (('딜러', 'orange'), ('불', 'red'), ('특급', 'purple'), ('2/3단계', 'brown'), ('장난꾸러기', 'blue')):
        x += chip(base, x, 92, t, c) + 3
    button(base, 520, 66, 104, 20, '마당에서 들이기', 'brown', f=K.F_SMALL(), icon='home')
    K.draw_text(base, (308, 116), '지금: 자유 행동 — 모든 상태가 양호해요', K.F_BODY(), K.TEXT_SOFT, 'lm')
    paste(base, K.icon('heart'), (308, 124)); K.draw_text(base, (322, 130), '훈련 · 전투 가능', K.F_TITLE(), K.BTN['green'][1], 'lm')
    for i, (ic, label, v, lv, col) in enumerate((('meat', '포만감', 80, '좋음', 'green'), ('smile', '기분', 80, '좋음', 'green'), ('zzz', '피로도', 10, '좋음', 'green'))):
        y = 140 + i * 11
        paste(base, K.icon(ic), (308, y - 2))
        K.draw_text(base, (324, y + 4), label, K.F_SMALL(), K.TEXT, 'lm')
        gauge(base, 364, y, 190, 8, v, 100, col)
        K.draw_text(base, (560, y + 4), f'{v} {lv}', K.F_SMALL(), K.BTN[col][1], 'lm')

    # 능력치
    ribbon(base, 204, 176, 70, '능력치', 'brown')
    K.draw_text(base, (282, 185), '줄을 눌러 훈련할 능력치를 골라요 · 막대 끝 = 이번 단계 MAX', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    stats = (('heart', '체력', 81, 400, 'red'), ('sword', '공격력', 125, 700, 'orange'), ('shield', '방어력', 66, 300, 'blue'), ('wing', '민첩성', 121, 600, 'green'))
    for i, (ic, label, v, cap, col) in enumerate(stats):
        y = 200 + i * 20
        if label == '공격력':
            c, cm = K.piece_card(True)
            paste(base, K.nine(c, cm, 412, 20), (206, y - 3))
        paste(base, K.icon(ic), (214, y + 1))
        K.draw_text(base, (230, y + 7), label, K.F_TITLE(), K.TEXT, 'lm')
        gauge(base, 282, y + 2, 252, 10, v, cap, col)
        K.draw_text(base, (544, y + 7), f'{v} / {cap}', K.F_BODY(), K.TEXT, 'lm')

    # 훈련 버튼
    K.draw_text(base, (206, 288), '공격력 훈련', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (206, 301), '피로도↑ 포만감↓', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    for i, (lbl, sub, state) in enumerate((('쉬움', '10분 · +10', 'hover'), ('중간', '30분 · +30', 'normal'), ('어려움', '60분 · +65', 'normal'))):
        button(base, 300 + i * 108, 280, 102, 30, lbl, 'green', state, sub=sub)
    # 아래 버튼
    button(base, 204, 322, 130, 24, '간식 주기 ×3', 'orange', icon='snack')
    button(base, 486, 322, 134, 24, '진화 3,000', 'purple', 'disabled', icon='coin')
    K.draw_text(base, (480, 334), '능력치를 모두 MAX로!', K.F_SMALL(), K.TEXT_SOFT, 'rm')

    # 알림
    c, cm = K.piece_card()
    paste(base, K.nine(c, cm, 200, 22), (300, 31))
    d.rectangle((302, 33, 305, 50), fill=K.BTN['green'][2])
    paste(base, K.icon('home'), (310, 36))
    K.draw_text(base, (326, 42), '불꽃매를 마당에 내보냈어요', K.F_BODY(), K.TEXT, 'lm')

    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1])
    main(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    print('ok')
