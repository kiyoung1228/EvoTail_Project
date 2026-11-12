"""EvoTail 아이콘: 불씨여우 1단계 도트 (assets/sprites/dealer_normal_01_s1.png).

원본 28×28(파일은 4배)에서 투명 여백을 잘라 낸 몸(16×15)을 크기마다 정수배 NEAREST로만 키워 가운데에 놓는다.
  16 = ×1, 32 = ×2, 48 = ×3, 256 = ×16   (줄이거나 부드럽게 늘리지 않음)
만드는 것:
  assets/icon/evotail.ico  exe 아이콘 (16·32·48·256 네 장, EvoTail.spec)
  assets/icon/evotail.png  pygame 창 아이콘 32×32 (gui/app.py set_window_icon)
실행: python tools/make_icon.py
"""
import os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'sprites', 'dealer_normal_01_s1.png')
OUT = os.path.join(ROOT, 'assets', 'icon')
SIZES = (16, 32, 48, 256)


def body():
    """4배 파일 → 원본 28 → 투명 여백을 잘라 낸 몸."""
    im = Image.open(SRC).convert('RGBA')
    base = im.resize((im.width // 4, im.height // 4), Image.NEAREST)
    assert base.resize(im.size, Image.NEAREST).tobytes() == im.tobytes(), '원본이 정확한 4배 그림이 아님'
    return base.crop(base.getbbox())


def icon(size, art=None):
    art = art or body()
    n = size // max(art.size)
    assert n >= 1, f'{size}px에 원본이 안 들어감'
    big = art.resize((art.width * n, art.height * n), Image.NEAREST)
    canvas = Image.new('RGBA', (size, size))
    canvas.paste(big, ((size - big.width) // 2, (size - big.height) // 2))
    return canvas


def main():
    os.makedirs(OUT, exist_ok=True)
    art = body()
    imgs = [icon(s, art) for s in SIZES]
    ico = os.path.join(OUT, 'evotail.ico')
    # 크기마다 직접 만든 그림을 그대로 넣는다 (Pillow가 다시 줄이지 않게 append_images)
    imgs[-1].save(ico, format='ICO', sizes=[(s, s) for s in SIZES], append_images=imgs[:-1])
    imgs[1].save(os.path.join(OUT, 'evotail.png'))
    # 확인: ico 안의 각 크기가 만든 그림과 같은지
    with Image.open(ico) as f:
        for s, want in zip(SIZES, imgs):
            f.size = (s, s)
            got = f.copy().convert('RGBA')
            assert got.tobytes() == want.tobytes(), f'{s}px 그림이 다름'
    print('saved', ico, 'sizes', SIZES, '+ evotail.png 32')


if __name__ == '__main__':
    main()
