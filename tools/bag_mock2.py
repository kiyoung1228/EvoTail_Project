"""가방 B 계열 후보: C(열린 가죽 가방 + 칸막이 주머니) / D(세워 둔 배낭 + 쪽지)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import battle_mock as B
from ui_mock import paste, button, gauge, chip, ribbon, text_mid
import bag_mock as BM

W, H = 640, 360; INK = K.INK
GREEN = K.BTN['green'][1]; RED = K.BTN['red'][1]
LE = [(92, 56, 32), (130, 82, 46), (164, 108, 62), (196, 140, 86), (226, 178, 118)]   # 가죽 어두움→밝음
LINING = (78, 50, 34)


def stitch(d, box, c=(236, 200, 140), step=7):
    x0, y0, x1, y1 = box
    for x in range(x0 + 4, x1 - 4, step): d.line((x, y0, x + 3, y0), fill=c); d.line((x, y1, x + 3, y1), fill=c)
    for y in range(y0 + 4, y1 - 4, step): d.line((x0, y, x0, y + 3), fill=c); d.line((x1, y, x1, y + 3), fill=c)


def slot(base, x, y, w, h, item=None, sel=False, tint=(250, 236, 206)):
    d = ImageDraw.Draw(base)
    if item:
        d.rectangle((x, y, x + w - 1, y + h - 1), fill=tint, outline=INK)
        d.line((x + 1, y + 1, x + w - 2, y + 1), fill=(255, 255, 255))
        k, n, cnt, cat, sub = item
        paste(base, BM.icon(k, 2), (x + (w - 32) // 2, y + (h - 32) // 2 - 1))
        if cnt > 1 or k.startswith('toy'):
            t = f'{cnt}' if not k.startswith('toy') else sub.split('남은 ')[1].split('/')[0] + '회'
            text_mid(base, x + w - 9, y + h - 7, t, K.F_SMALL(), (255, 255, 255), INK)
    else:
        d.rectangle((x, y, x + w - 1, y + h - 1), fill=(104, 70, 46), outline=(64, 40, 24))
        d.line((x + 1, y + h - 2, x + w - 2, y + h - 2), fill=(124, 86, 58))
    if sel: B.corners(base, x - 2, y - 2, x + w + 1, y + h + 1)


def info_strip(base, y=286):
    B.panel(base, 8, y, 624, 70)
    d = ImageDraw.Draw(base); d.rectangle((18, y + 10, 70, y + 62), fill=(255, 226, 214), outline=K.WOOD[2])
    paste(base, BM.icon('food_perfect_rabbit_stew', 3), (20, y + 12))
    K.draw_text(base, (80, y + 18), '대성공 토끼고기 스튜', K.F_BIG(), K.TEXT, 'lm')
    cw = chip(base, 80, y + 30, '요리', 'red'); chip(base, 80 + cw + 3, y + 30, '대성공 1.5배', 'gold')
    K.draw_text(base, (80, y + 58), '포만감 +150 · 기분 +75 · 피로도 -60', K.F_SMALL(), GREEN, 'lm')
    K.draw_text(base, (400, y + 18), '보유 1', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    button(base, 464, y + 10, 158, 26, '동물에게 주기', 'green', icon='heart', f=K.F_BODY())
    button(base, 464, y + 40, 158, 22, '상점에 팔기 · 판매가 N', 'red', icon='coin', f=K.F_SMALL())


TINT = {'feed': (255, 236, 200), 'food': (255, 226, 214), 'potion': (226, 236, 255), 'gear': (236, 226, 255), 'mat': (232, 244, 214)}


# ---------------- C: 열린 가죽 가방 + 칸막이 주머니 ----------------
def bag_C(out):
    base = BM.bg()
    B.card(base, 154, 32, 112, 22); paste(base, BM.bag_icon(), (160, 37)); text_mid(base, 216, 43, f'아이템 {len(BM.ITEMS)}종', K.F_BODY(), K.TEXT)
    d = ImageDraw.Draw(base)
    # 열린 덮개 (뒤) + 버클 끈
    d.polygon([(70, 74), (110, 56), (530, 56), (570, 74)], fill=LE[1], outline=INK)
    d.line((112, 58, 528, 58), fill=LE[3])
    for bx in (200, 420):
        d.rectangle((bx, 56, bx + 14, 80), fill=LE[0], outline=INK)
        d.rectangle((bx - 2, 72, bx + 16, 82), fill=(232, 196, 90), outline=INK); d.rectangle((bx + 2, 75, bx + 12, 79), fill=LE[0])
    # 몸통
    d.rounded_rectangle((24, 74, 616, 282), 14, fill=LE[2], outline=INK)
    d.rounded_rectangle((28, 78, 612, 278), 12, outline=LE[3])
    stitch(d, (34, 84, 606, 272))
    d.rounded_rectangle((40, 90, 600, 266), 8, fill=LINING, outline=(50, 30, 20))
    # 칸막이 3구역: 왼쪽 주머니(포션) / 가운데 큰 칸(먹이·요리·장비) / 오른쪽 주머니(재료)
    secs = [((46, 96, 168, 260), '포션', 'potion'), ((176, 96, 466, 260), '먹이·요리·장비', None), ((474, 96, 594, 260), '재료', 'mat')]
    for (x0, y0, x1, y1), name, cat in secs:
        d.rectangle((x0, y0, x1, y1), fill=(92, 60, 40), outline=(50, 30, 20))
        w = int(BM.tl(name, K.F_SMALL())) + 12
        d.rectangle((x0 + 4, y0 + 3, x0 + 4 + w, y0 + 17), fill=(244, 230, 200), outline=INK)       # 천 이름표
        d.line((x0 + 5, y0 + 4, x0 + 3 + w, y0 + 4), fill=(255, 250, 236))
        text_mid(base, x0 + 4 + w / 2 + .5, y0 + 10, name, K.F_SMALL(), K.TEXT)
    for x in (172, 470): d.rectangle((x - 2, 94, x + 2, 262), fill=LE[1], outline=INK)            # 가죽 칸막이
    pot = [it for it in BM.ITEMS if it[3] == 'potion']
    mid = [it for it in BM.ITEMS if it[3] in ('feed', 'food', 'gear')]
    mat = [it for it in BM.ITEMS if it[3] == 'mat']
    def grid(items, x0, y0, cols, rows, sel_key=None):
        for i in range(cols * rows):
            x = x0 + (i % cols) * 56; y = y0 + (i // cols) * 46
            it = items[i] if i < len(items) else None
            slot(base, x, y, 52, 42, it, it is not None and it[0] == sel_key, TINT.get(it[3]) if it else None)
    grid(pot, 52, 120, 2, 3); grid(mid, 182, 120, 5, 3, 'food_perfect_rabbit_stew'); grid(mat, 480, 120, 2, 3)
    text_mid(base, 534, 266, f'▼ {len(mat) - 6}개 더 (휠)', K.F_SMALL(), (236, 210, 170))
    info_strip(base)
    BM.save(base, out)


# ---------------- D: 세워 둔 배낭 + 쪽지 ----------------
def bag_D(out, mode='feed'):
    base = BM.bg()
    d = ImageDraw.Draw(base)
    # 배낭 (왼쪽, 세워 둠): 손잡이, 윗덮개 + 버클, 몸통
    d.rounded_rectangle((140, 54, 200, 72), 8, outline=INK, width=4); d.rounded_rectangle((141, 55, 199, 71), 8, outline=LE[1], width=2)
    d.rounded_rectangle((10, 66, 326, 354), 24, fill=LE[2], outline=INK)
    d.rounded_rectangle((14, 70, 322, 350), 22, outline=LE[3])
    d.rounded_rectangle((10, 66, 326, 112), 24, fill=LE[1], outline=INK)
    d.rectangle((11, 96, 325, 112), fill=LE[1]); d.line((11, 112, 325, 112), fill=INK)
    for bx in (80, 244):
        d.rectangle((bx, 80, bx + 12, 128), fill=LE[0], outline=INK)
        d.rectangle((bx - 2, 118, bx + 14, 128), fill=(232, 196, 90), outline=INK); d.rectangle((bx + 2, 121, bx + 10, 125), fill=LE[0])
    stitch(d, (20, 116, 316, 344))
    d.rounded_rectangle((24, 132, 312, 340), 10, fill=LINING, outline=(50, 30, 20))
    # 옆으로 삐져나온 천 탭(분류)
    tabs = [('전체', None, 'bag', (236, 220, 190)), ('먹이', 'feed', 'snack', TINT['feed']), ('요리', 'food', 'butter_potato', TINT['food']),
            ('포션', 'potion', 'heal_basic', TINT['potion']), ('장비·알', 'gear', 'equip_claw', TINT['gear']), ('재료', 'mat', 'potato', TINT['mat'])]
    for i, (t, cat, ic, col) in enumerate(tabs):
        y = 116 + i * 38; on = i == 0
        tw = int(BM.tl(t, K.F_SMALL())) + 10
        x1 = 324 + max(tw, 30) + (8 if on else 0)
        d.rectangle((324, y, x1, y + 34), fill=col, outline=INK); d.line((325, y + 1, x1 - 1, y + 1), fill=(255, 255, 255))
        paste(base, BM.bag_icon() if ic == 'bag' else BM.icon(ic), (int((324 + x1) / 2) - 8, y + 2))
        text_mid(base, (324 + x1) / 2 + .5, y + 26, t, K.F_SMALL(), K.TEXT)
    # 안쪽 칸 5 x 4
    for i in range(20):
        x = 32 + (i % 5) * 56; y = 140 + (i // 5) * 49
        it = BM.ITEMS[i] if i < len(BM.ITEMS) else None
        slot(base, x, y, 52, 45, it, it is not None and it[0] == {'feed': 'snack', 'mat': 'lucky_rabbit', 'battle': 'potion_attack', 'gear': 'equip_shell'}[mode], TINT.get(it[3]) if it else None)
    d = ImageDraw.Draw(base)
    # 오른쪽 쪽지 (핀으로 고정)
    note_paper(base)
    sel = {'feed': 'snack', 'mat': 'lucky_rabbit', 'battle': 'potion_attack', 'gear': 'equip_shell'}[mode]
    it = [x for x in BM.ITEMS if x[0] == sel][0]
    d = ImageDraw.Draw(base)
    d.rectangle((418, 80, 470, 132), fill=TINT[it[3]], outline=K.WOOD[2]); paste(base, BM.icon(sel, 3), (420, 82))
    nm = it[1]
    if BM.tl(nm, K.F_BIG()) > 140: K.draw_text(base, (478, 86), '행운의', K.F_BIG(), K.TEXT, 'lm'); K.draw_text(base, (478, 102), '토끼고기', K.F_BIG(), K.TEXT, 'lm'); cy = 112
    else: K.draw_text(base, (478, 92), nm, K.F_BIG(), K.TEXT, 'lm'); cy = 104
    chip(base, 478, cy, {'feed': '먹이', 'mat': '재료', 'battle': '전투 포션', 'gear': '장비'}[mode], {'feed': 'orange', 'mat': 'brown', 'battle': 'blue', 'gear': 'purple'}[mode])
    K.draw_text(base, (618, cy + 8), f'보유 {it[2]}', K.F_SMALL(), K.TEXT_SOFT, 'rm')
    if mode == 'feed':
        paste(base, K.icon('meat'), (418, 142)); K.draw_text(base, (436, 148), '포만감 +35', K.F_BODY(), GREEN, 'lm')
        K.draw_text(base, (418, 172), '누구에게 줄까?', K.F_TITLE(), K.TEXT, 'lm')
        rows = [('dealer_normal_01', '불씨여우', 80, False, None), ('tank_normal_01', '물방울수달', 10, True, None), ('healer_normal_01', '산들오리', 60, False, '사냥 중')]
        for i, (aid, n, f, sel_, busy) in enumerate(rows):
            y = 182 + i * 34
            B.card(base, 416, y, 204, 30, sel_)
            paste(base, B.spr(aid, 1, 1).crop((2, 4, 26, 28)), (418, y + 3))
            K.draw_text(base, (446, y + 10), n, K.F_BODY(), K.TEXT_SOFT if busy else K.TEXT, 'lm')
            gauge(base, 446, y + 19, 110, 6, min(100, f + 35) if sel_ else f, 100, 'green')
            if sel_: gauge(base, 446, y + 19, 110, 6, f, 100, 'red')
            K.draw_text(base, (614, y + 10), f'{f}→{f + 35}' if sel_ else (busy or str(f)), K.F_SMALL(), GREEN if sel_ else K.TEXT_SOFT, 'rm')
        button(base, 416, 294, 204, 40, '물방울수달에게 주기', 'green', icon='heart', sub='기본 간식 1개')
    elif mode == 'mat':
        K.draw_text(base, (418, 150), '쓰는 곳', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        B.card(base, 416, 158, 204, 36)
        paste(base, BM.icon('rabbit_stew'), (422, 168)); K.draw_text(base, (444, 170), '토끼고기 스튜', K.F_BODY(), K.TEXT, 'lm')
        K.draw_text(base, (444, 184), '주방 레시피 ★5', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        K.draw_text(base, (418, 208), '얻는 곳: 사냥터 · 달토끼 언덕', K.F_SMALL(), K.TEXT, 'lm')
        K.draw_text(base, (418, 224), '판매가 170코인', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        button(base, 416, 246, 204, 26, '주방으로', 'orange', icon='home', f=K.F_BODY())
        button(base, 416, 278, 204, 22, '상점에 팔기 · 170코인', 'red', icon='coin', f=K.F_SMALL())
        K.draw_text(base, (518, 320), '요리 재료 · 여기서는 못 씀', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    elif mode == 'battle':
        paste(base, K.icon('sword'), (418, 142)); K.draw_text(base, (436, 148), '공격력 +100 (전투 1번)', K.F_BODY(), GREEN, 'lm')
        K.draw_text(base, (418, 176), '쓰는 곳', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        B.card(base, 416, 184, 204, 36)
        paste(base, K.icon('sword'), (422, 194)); K.draw_text(base, (444, 196), '전투장 · 출전 준비', K.F_BODY(), K.TEXT, 'lm')
        K.draw_text(base, (444, 210), '팀원에게 미리 먹이기', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        button(base, 416, 246, 204, 26, '전투장으로', 'blue', icon='sword', f=K.F_BODY())
        button(base, 416, 278, 204, 22, '상점에 팔기 · 75코인', 'red', icon='coin', f=K.F_SMALL())
        K.draw_text(base, (518, 320), '전투 중이 아니면 못 씀', K.F_SMALL(), K.TEXT_SOFT, 'mm')
    BM.save(base, out)


def note_paper(base):
    d = ImageDraw.Draw(base)
    d.polygon([(404, 66), (628, 62), (632, 350), (400, 354)], fill=(250, 240, 214), outline=INK)
    for y in range(92, 346, 14): d.line((410, y, 624, y - 1), fill=(232, 216, 186))
    d.ellipse((508, 56, 520, 68), fill=(232, 72, 72), outline=INK); d.point((511, 59), fill=(255, 200, 200))


if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); B.SPR = Path(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(exist_ok=True)
    bag_C(out / 'bag_C_satchel.png'); bag_D(out / 'bag_D1_feed.png'); bag_D(out / 'bag_D2_material.png', 'mat'); bag_D(out / 'bag_D3_battle.png', 'battle')
    print('ok')
