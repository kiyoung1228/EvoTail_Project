import sys, json
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent))
import uikit as K, mon2 as M
from ui_mock import paste, chip

ROLES = {'dealer': ('딜러·불', 'orange'), 'tank': ('탱커·물', 'blue'), 'healer': ('힐러·바람', 'green')}
RANK = ('브론즈', '실버', '골드', '다이아몬드')

def sheet(out):
    W, H = 640, 530
    base = Image.new('RGBA', (W, H), K.PAPER[2] + (255,))
    p, m = K.piece_panel(); paste(base, K.nine(p, m, W, H), (0, 0))
    K.draw_text(base, (16, 18), '졸개 12종 (역할별 4)', K.F_TITLE(), K.TEXT, 'lm')
    for i, (key, name, role, fn) in enumerate(M.MINIONS):
        x = 14 + (i % 6) * 104; y = 28 + (i // 6) * 98
        c, cm = K.piece_card(); paste(base, K.nine(c, cm, 98, 94), (x, y))
        paste(base, fn().resize((56, 56), Image.NEAREST), (x + 21, y))
        K.draw_text(base, (x + 49, y + 66), name, K.F_TITLE(), K.TEXT, 'mm')
        r = ROLES[role]; w = ImageDraw.Draw(base).textlength(r[0], font=K.F_SMALL()) + 8
        chip(base, int(x + 49 - w / 2), y + 76, r[0], r[1])
    K.draw_text(base, (16, 234), '스테이지 보스 9종 (보라 테두리 = 대회)', K.F_TITLE(), K.TEXT, 'lm')
    for i, (key, name, stage, role, fn) in enumerate(M.BOSSES):
        col, row = i % 5, i // 5
        x = 14 + col * 124 + (62 if row else 0); y = 244 + row * 140
        c, cm = K.piece_card(stage in RANK); paste(base, K.nine(c, cm, 118, 134), (x, y))
        paste(base, fn().resize((92, 92), Image.NEAREST), (x + 13, y + 4))
        K.draw_text(base, (x + 59, y + 102), name, K.F_TITLE(), K.TEXT, 'mm')
        tw = chip(base, x + 8, y + 112, stage, 'purple' if stage in RANK else 'brown')
        r = ROLES[role]; chip(base, x + 12 + tw, y + 112, r[0], r[1])
    base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)

def export(out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('*.png'): f.unlink()
    for key, *r in M.MINIONS + M.BOSSES:
        im = r[-1](); im.resize((im.width * 4, im.height * 4), Image.NEAREST).save(out / f'{key}.png')
    el = {'dealer': 'fire', 'tank': 'water', 'healer': 'wind'}
    st = {'뉴비': 'tutorial', '쉬움': 'easy', '브론즈': 'bronze', '보통': 'normal', '실버': 'silver', '어려움': 'hard', '골드': 'gold', '극악': 'extreme', '다이아몬드': 'diamond'}
    return {'note': '졸개 28x28, 보스 46x46 원본을 4배로 저장. 화면에서는 원본 크기 x2 (졸개 56, 보스 92 논리 픽셀)',
            'minions': [{'id': k, 'name': n, 'role': r, 'element': el[r], 'sprite': f'assets/enemies/{k}.png'} for k, n, r, _ in M.MINIONS],
            'bosses': [{'id': k, 'name': n, 'stage': st[s], 'role': r, 'element': el[r], 'boss': True, 'sprite': f'assets/enemies/{k}.png'} for k, n, s, r, _ in M.BOSSES]}

if __name__ == '__main__':
    K.FONT_DIR = Path(sys.argv[1]); sheet(sys.argv[2])
    data = export(sys.argv[3]); Path(sys.argv[4]).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8'); print('ok')
