"""표지·안내원 그림 내보내기 → assets/title/, assets/guide/ (파일은 논리 크기의 2배 또는 4배).
    python tools/title_assets.py
"""
import json, sys
from pathlib import Path
from PIL import Image
import uikit as K
import title5 as T5
import techmo

ROOT = Path(__file__).resolve().parent.parent if (Path(__file__).resolve().parent.parent / 'assets').exists() else T5.GAME
W, H = 640, 360


def x2(im): return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def logo_parts(logo_bb, cx=320, cy=96, cell=7):
    """로고 글자별 가로 범위·꼬리 영역·반짝이 자리 (title5.big_logo와 같은 계산). 로고 그림 왼쪽 위 기준(논리 px).
    표지 이스터에그(글자 누르면 통 튐, 꼬리 5번)와 반짝이 깜빡에 쓴다."""
    word = 'EvoTail'
    widths = [len(T5.GLYPH[c][0]) for c in word]
    total = sum(widths) + len(word) - 1
    full_w, full_h = total * cell + 8 * cell, 9 * cell + cell
    x0, y0 = cx - full_w // 2 + 3 * cell, cy - full_h // 2
    lx, ly = logo_bb[0], logo_bb[1]
    starts, x = [], 0
    for w in widths:
        starts.append(x0 + x * cell); x += w + 1
    cuts = [max(0, s - 3 - lx) for s in starts] + [logo_bb[2] - lx]
    letters = [[cuts[i], cuts[i + 1]] for i in range(len(word))]
    tail_x = x0 + (total - 1) * cell
    tail = [tail_x + cell + 1 - lx, y0 + 4 * cell - ly, tail_x + 8 * cell - lx, y0 + 10 * cell + 3 - ly]
    sparkles = [[x0 - 12, y0 + 18], [x0 + full_w + 6, y0 + 22], [x0 + 110, y0 + 2], [x0 + 30, y0 + full_h + 6],
                [x0 + full_w - 60, y0 + 4]]
    return letters, tail, sparkles


def main(root=ROOT):
    K.FONT_DIR = T5.GAME / 'assets' / 'fonts'
    t = root / 'assets' / 'title'; g = root / 'assets' / 'guide'
    t.mkdir(parents=True, exist_ok=True); g.mkdir(parents=True, exist_ok=True)
    L = T5.static_layers()
    x2(L['back']).save(t / 'back.png'); x2(L['mid']).save(t / 'mid.png'); x2(L['front']).save(t / 'front.png')
    for i, (x, y, w) in enumerate(((24, 40, 70), (470, 34, 96), (300, 26, 50), (560, 136, 56), (150, 128, 44))):
        c = Image.new('RGBA', (W, H)); T5.puff_cloud(c, 20, 30, w); c = c.crop(c.getbbox()); x2(c).save(t / f'cloud_{i}.png')
    islands = {}
    for name, (tx, ty, s, flip) in {'island_left': (84, 62, .8, False), 'island_right': (566, 56, .75, True)}.items():
        c = Image.new('RGBA', (240, 170))
        T5.float_island(c, 120, 80, 0.25 if not flip else 0.25 + 1e-9, s, flip)     # 흔들림 0 위치
        bb2 = c.getbbox(); x2(c.crop(bb2)).save(t / f'{name}.png')
        islands[name] = [tx - 120 + bb2[0], ty - 80 + bb2[1]]
    logo = Image.new('RGBA', (W, H)); T5.big_logo(logo, 320, 96, 7, t=0.99); T5.subtitle(logo, 320, 142)
    bb = logo.getbbox(); x2(logo.crop(bb)).save(t / 'logo.png')
    kinds = ['idle', 'blink', 'talk', 'flap1', 'flap2', 'flap3', 'flap1_talk', 'flap2_talk', 'flap3_talk']
    for k in kinds: techmo.frame(k, 4).save(g / f'techmo_{k}.png')
    meta = {'note': '표지 그림. 파일은 논리 640×360의 2배(back/mid/front/logo/cloud/island). 화면에서는 ½로 그대로 그림',
            'logo_topleft': [bb[0], bb[1]],
            'clouds': [[24, 40, 6], [470, 34, 4], [300, 26, 8], [560, 136, 5], [150, 128, 7]],
            'clouds_note': '[x, y, 흐르는 속도 px/초 × 1] 화면 너비+120에서 감아 돌기',
            'islands': islands, 'islands_note': '섬 그림 왼쪽 위 (논리 좌표). 위아래 ±2px 천천히 (사인, 주기 4초)',
            'techmo_feet': [168, 222], 'techmo_note': '테크모(원본 32 ×2 = 64) 발 가운데 좌표, 옛 돌문 위',
            'parade_y': 298, 'parade_gap': 64, 'parade_speed': 2, 'parade_note': '일반 15종 도감 순서, 발 y, 프레임당 2px(30fps 기준)',
            'blossoms_sample': [list(map(int, p)) for p in L['blossoms'][::12]],
            'menu_y0': 182, 'menu_gap': 19}
    letters, tail, sparkles = logo_parts(bb)
    meta.update(logo_letters=letters, logo_letters_bottom=142 - bb[1], logo_tail=tail, logo_sparkles=sparkles,
                logo_note='logo_letters = 글자별 [x0, x1) (로고 그림 기준), logo_letters_bottom 위쪽만 글자 '
                          '(아래는 부제 띠), logo_tail = 여우 꼬리 [x0, y0, x1, y1], logo_sparkles = 반짝이 (논리 좌표)')
    json.dump(meta, open(t / 'title.json', 'w'), ensure_ascii=False, indent=1)
    json.dump({'note': '안내원 테크모 (회색 까마귀, 학사모). 원본 32×32, 파일 4배(128). 화면 ×2(64) 또는 ×4(128 = 파일 그대로)',
               'frames': kinds, 'flap_cycle': ['flap3', 'idle', 'flap1', 'flap2', 'flap1', 'idle'],
               'blink': 'idle 사이에 0.1초', 'talk': '말할 때 talk ↔ idle 번갈아 (0.15초)'},
              open(g / 'techmo.json', 'w'), ensure_ascii=False, indent=1)
    print('ok', t, g)


if __name__ == '__main__':
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT)
