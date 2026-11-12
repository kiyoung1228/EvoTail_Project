"""전투 응급 붕대 아이콘 (assets/items/battle_bandage.png).
손으로 찍은 16x16: 둘둘 만 붕대 롤(나선 단면) + 빨간 십자 + 풀린 끝자락 + 반짝이.
파일은 4배(64x64). 실행: python tools/bandage_icon.py
"""
import os
from PIL import Image

P = {'o': (52, 34, 30), '.': None, 'W': (255, 255, 255), 'w': (238, 242, 250), 'k': (206, 214, 232),
     'K': (160, 172, 202), 'n': (110, 118, 150), 'R': (228, 54, 66), 'q': (255, 120, 120),
     'M': (150, 28, 44), '+': (255, 226, 100), '*': (255, 255, 255)}

BANDAGE = [
    '.............+..',
    '............+*+.',
    '...oooooooooo+..',
    '..oWWWWnWWWWWo..',
    '.oWWKKKwnWWRWWo.',
    'oWWKwwwKnWWRWwo.',
    'oWKwKKwKnwWRWwo.',
    'oWKwKnwKnRRRRMo.',
    'oWKwKKKwnkWRWko.',
    'owKwwwwKnkkRkko.',
    'owwKKKKwnkkMkko.',
    '.owwwwwwnKKKKKo.',
    '..okkkknKwwwKo..',
    '...ooooooWwkkKo.',
    '........owkkKKo.',
    '.........oooooo.']


def bandage():
    im = Image.new('RGBA', (16, 16))
    px = im.load()
    for y, row in enumerate(BANDAGE):
        for x, ch in enumerate(row):
            if P[ch]:
                px[x, y] = P[ch] + (255,)
    return im


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, 'assets', 'items', 'battle_bandage.png')
    bandage().resize((64, 64), Image.NEAREST).save(out)
    print('saved', out)
