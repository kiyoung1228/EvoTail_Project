"""마이룸 후보 목업: 업적 트로피 선반 · 기록 액자/칠판 · 일기장 · 돌아다니는 동물 (백엔드 get_achievement_details·get_statistics·get_event_history)."""
import math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw
import uikit as K
import title5 as T5
import battle_mock as B
from ui_mock import paste, button, chip, ribbon, text_mid, gauge

W, H = 640, 360
INK = K.INK
GAME = Path(__file__).resolve().parent.parent      # 저장소 루트 (tools/ 위)

# ---------------- 예시 데이터 (백엔드 모양 그대로) ----------------
ACH = [  # get_achievement_details 순서
    ('first_win', '첫 승리', True), ('first_training', '첫 훈련 완료', True), ('first_hunt', '첫 자동 사냥 완료', True),
    ('first_crop', '첫 수확', True), ('first_cooking', '첫 요리 성공', True), ('cooking_master', '요리 마스터', False),
    ('pokedex_10', '도감 10종 수집', True), ('pokedex_complete', '도감 완성', False), ('first_evolution', '첫 진화', True),
    ('fully_evolved', '최종 진화 동물 보유', False), ('max_stats', '모든 능력치 MAX 달성 동물 보유', False),
    ('champion', '다이아몬드 챔피언', False), ('rank_bronze', '브론즈 승급', True), ('rank_silver', '실버 승급', False),
    ('rank_gold', '골드 승급', False), ('rank_diamond', '다이아몬드 승급', False)]
HOWTO = {  # GUI 표시 문구 (어떻게 얻는지)
    'first_win': '전투에서 한 번 이기기', 'first_training': '훈련을 한 번 끝내기', 'first_hunt': '사냥터에서 한 번 돌아오기',
    'first_crop': '밭에서 한 번 수확하기', 'first_cooking': '요리를 한 번 성공하기', 'cooking_master': '요리 레벨 5 달성',
    'pokedex_10': '동물 10종 모으기', 'pokedex_complete': '동물 30종 모두 모으기', 'first_evolution': '동물 한 마리 진화시키기',
    'fully_evolved': '최종 단계까지 진화시키기', 'max_stats': '네 능력치를 모두 MAX로', 'champion': '다이아몬드 대회 우승',
    'rank_bronze': '브론즈 대회 우승', 'rank_silver': '실버 대회 우승', 'rank_gold': '골드 대회 우승', 'rank_diamond': '다이아몬드 대회 우승'}
STATS = [('battles_won', '전투 승리', 12, 'sword'), ('trainings_completed', '훈련 완료', 34, 'heart'),
         ('hunts_completed', '사냥 다녀옴', 9, 'meat'), ('crops_harvested', '작물 수확', 27, 'snack'),
         ('cooks_succeeded', '요리 성공', 15, 'home'), ('items_purchased', '물건 구매', 41, 'coin')]
DIARY = [('evolve', '불씨여우가 불꽃여우로 진화했다!'), ('battle_end', '브론즈 대회 우승!'),
         ('hatch', '알에서 산들나비가 태어났다!'), ('training_complete', '물방울개구리 훈련 완료! 방어력 +30'),
         ('random_bonus', '행운 이벤트! 코인 +120'), ('hunt_complete', '산들사슴 사냥 완료!'),
         ('disease', '물방울수달이 아프다'), ('crop_ready', '밭의 작물 수확 가능')]
DIARY_ICON = {'evolve': 'heart', 'battle_end': 'sword', 'hatch': 'heart', 'training_complete': 'sword',
              'random_bonus': 'coin', 'hunt_complete': 'meat', 'disease': 'frown', 'crop_ready': 'snack'}
ROOMIES = [('dealer_normal_01', 2), ('tank_normal_03', 1), ('healer_normal_05', 1), ('healer_normal_02', 1)]


def save(base, out): base.resize((W * 2, H * 2), Image.NEAREST).convert('RGB').save(out)


# ---------------- 트로피 도트 (16×16) ----------------
GOLD = [(176, 116, 30), (226, 166, 44), (252, 210, 80), (255, 240, 170)]
SILVER = [(110, 116, 132), (160, 168, 184), (212, 218, 230), (248, 250, 255)]
BRONZE = [(120, 70, 40), (170, 106, 58), (212, 146, 88), (240, 196, 150)]
DIAMOND = [(50, 110, 170), (90, 170, 226), (160, 222, 250), (236, 250, 255)]


def _cup(d, c, big=False):
    d.rectangle((3, 2, 12, 2), fill=INK)
    d.polygon([(3, 3), (12, 3), (11, 8), (9, 10), (6, 10), (4, 8)], fill=c[2], outline=INK)
    d.line((5, 4, 5, 7), fill=c[3]); d.line((10, 4, 10, 8), fill=c[1])
    d.line((1, 4, 2, 4), fill=INK); d.line((1, 4, 1, 6), fill=INK); d.line((1, 6, 3, 7), fill=INK)
    d.line((13, 4, 14, 4), fill=INK); d.line((14, 4, 14, 6), fill=INK); d.line((14, 6, 12, 7), fill=INK)
    d.rectangle((7, 10, 8, 12), fill=c[1], outline=INK)
    d.rectangle((4, 12, 11, 14), fill=K.WOOD[1], outline=INK); d.line((5, 13, 10, 13), fill=c[2])
    if big:
        d.point([(5, 0), (7, 0), (10, 0)], fill=c[3]); d.line((5, 1, 10, 1), fill=c[2])


def _medal(d, c, rib=(220, 70, 70)):
    d.polygon([(4, 1), (7, 1), (8, 6), (6, 7)], fill=rib, outline=INK)
    d.polygon([(11, 1), (8, 1), (7, 6), (9, 7)], fill=tuple(int(v * .8) for v in rib), outline=INK)
    d.ellipse((3, 6, 12, 15), fill=c[2], outline=INK)
    d.ellipse((5, 8, 10, 13), fill=c[1]); d.ellipse((5, 8, 9, 12), fill=c[2]); d.point((6, 9), fill=c[3])


def _dumbbell(d):
    d.line((4, 8, 11, 8), fill=INK, width=1); d.line((4, 7, 11, 7), fill=(170, 170, 186))
    for x in (1, 11):
        d.rectangle((x, 4, x + 3, 11), fill=(90, 96, 120), outline=INK); d.line((x + 1, 5, x + 1, 10), fill=(140, 146, 170))
    d.rectangle((3, 13, 12, 14), fill=K.WOOD[2], outline=INK)


def _meat(d):
    d.ellipse((2, 3, 11, 12), fill=(200, 90, 70), outline=INK); d.ellipse((4, 5, 8, 8), fill=(236, 140, 110))
    d.line((9, 10, 13, 14), fill=INK, width=3); d.line((9, 10, 13, 14), fill=(250, 240, 220))
    d.point([(13, 12), (14, 13), (12, 14)], fill=(250, 240, 220))


def _sprout(d):
    d.polygon([(4, 9), (11, 9), (10, 14), (5, 14)], fill=(200, 110, 70), outline=INK); d.line((4, 9, 11, 9), fill=(230, 150, 100))
    d.line((7, 9, 7, 4), fill=(80, 150, 60))
    d.ellipse((2, 2, 7, 6), fill=(120, 200, 90), outline=INK); d.ellipse((7, 1, 13, 5), fill=(140, 214, 100), outline=INK)


def _pan(d):
    d.ellipse((1, 5, 11, 13), fill=(70, 70, 86), outline=INK); d.ellipse((3, 6, 9, 11), fill=(110, 110, 130))
    d.ellipse((4, 7, 8, 10), fill=(255, 250, 230)); d.point((6, 8), fill=(250, 200, 60))
    d.line((11, 9, 15, 9), fill=INK, width=2); d.line((11, 9, 14, 9), fill=K.WOOD[2])


def _hat(d):
    for e in ((2, 1, 8, 7), (6, 0, 12, 6), (8, 2, 14, 8), (3, 3, 13, 9)):
        d.ellipse(e, fill=(255, 255, 255), outline=INK)
    d.ellipse((4, 4, 12, 8), fill=(255, 255, 255))
    d.rectangle((4, 8, 12, 13), fill=(244, 240, 232), outline=INK); d.line((5, 10, 11, 10), fill=(250, 200, 60))


def _book(d, c=(200, 80, 80), gold=False):
    d.rectangle((2, 2, 13, 14), fill=c, outline=INK); d.rectangle((3, 13, 13, 14), fill=(250, 240, 220), outline=INK)
    d.line((4, 2, 4, 12), fill=tuple(int(v * .7) for v in c))
    d.rectangle((6, 5, 11, 8), fill=(255, 230, 120) if gold else (250, 240, 220), outline=INK)
    if gold: d.point([(1, 1), (14, 3), (13, 0)], fill=(255, 250, 200))


def _star(d, c, big=False):
    cx, cy, r1, r2 = 7.5, 8, 7 if big else 6, 3 if big else 2.6
    pts = [(cx + (r1 if i % 2 == 0 else r2) * math.sin(i * math.pi / 5), cy - (r1 if i % 2 == 0 else r2) * math.cos(i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=c[2], outline=INK); d.point([(6, 6), (6, 7)], fill=c[3])


def _plaque(d):
    d.rectangle((1, 3, 14, 13), fill=K.WOOD[2], outline=INK); d.rectangle((3, 5, 12, 11), fill=GOLD[2], outline=INK)
    K.draw_text  # noqa
    for x, col in ((4, (230, 80, 80)), (6, (250, 170, 50)), (8, (90, 170, 230)), (10, (100, 190, 90))):
        d.rectangle((x, 7, x + 1, 9), fill=col)


def _crown_cup(d):
    _cup(d, DIAMOND)
    d.polygon([(4, 0), (6, 2), (8, 0), (10, 2), (12, 0), (12, 3), (4, 3)], fill=GOLD[2], outline=INK)


ART = {'first_win': lambda d: _cup(d, GOLD), 'first_training': _dumbbell, 'first_hunt': _meat, 'first_crop': _sprout,
       'first_cooking': _pan, 'cooking_master': _hat, 'pokedex_10': _book, 'pokedex_complete': lambda d: _book(d, (120, 70, 170), True),
       'first_evolution': lambda d: _star(d, GOLD), 'fully_evolved': lambda d: _star(d, [(120, 60, 160), (170, 100, 220), (214, 160, 250), (250, 230, 255)], True),
       'max_stats': _plaque, 'champion': _crown_cup, 'rank_bronze': lambda d: _medal(d, BRONZE, (90, 140, 220)),
       'rank_silver': lambda d: _medal(d, SILVER, (90, 140, 220)), 'rank_gold': lambda d: _medal(d, GOLD, (220, 70, 70)),
       'rank_diamond': lambda d: _medal(d, DIAMOND, (150, 90, 210))}


def trophy(code, got=True, n=2):
    im = Image.new('RGBA', (16, 16)); ART[code](ImageDraw.Draw(im))
    if not got:                                       # 아직: 어두운 실루엣
        px = im.load()
        for y in range(16):
            for x in range(16):
                if px[x, y][3]: px[x, y] = (72, 56, 60, 200) if px[x, y][:3] != INK else (44, 32, 38, 220)
    return im.resize((16 * n, 16 * n), Image.NEAREST)


# ---------------- 방 ----------------
WALL = [(236, 212, 222), (246, 226, 232), (226, 196, 210)]
FLOOR = [(176, 120, 76), (196, 140, 92), (156, 102, 62)]


def room(floor_y=236, window=(250, 54, 360, 140)):
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 26, W, floor_y), fill=WALL[1])
    for y in range(34, floor_y - 40, 18):                    # 벽지: 작은 매화 무늬
        for x in range((y // 18) % 2 * 14, W, 28):
            d.point([(x, y), (x - 1, y + 1), (x + 1, y + 1), (x, y + 2)], fill=WALL[2]); d.point((x, y + 1), fill=(250, 214, 120))
    d.rectangle((0, floor_y - 40, W, floor_y), fill=(200, 160, 170))   # 아래 판자벽
    for x in range(0, W, 20): d.line((x, floor_y - 39, x, floor_y), fill=(184, 142, 154))
    d.line((0, floor_y - 41, W, floor_y - 41), fill=K.WOOD[1]); d.line((0, floor_y - 40, W, floor_y - 40), fill=K.WOOD[3])
    d.rectangle((0, floor_y, W, H), fill=FLOOR[1])                      # 마루
    for i, y in enumerate(range(floor_y, H, 12)):
        d.line((0, y, W, y), fill=FLOOR[2])
        for x in range((i * 37) % 80, W, 80): d.line((x, y, x, y + 11), fill=FLOOR[2])
        d.line((0, y + 1, W, y + 1), fill=FLOOR[0] if False else (206, 152, 102))
    d.rectangle((0, floor_y - 1, W, floor_y), fill=K.WOOD[0])
    if window is None: return im
    # 창문 (낮 하늘 + 매화 가지)
    x0, y0, x1, y1 = window
    d.rectangle((x0 - 4, y0 - 4, x1 + 4, y1 + 4), fill=K.WOOD[2], outline=INK)
    d.rectangle((x0, y0, x1, y1), fill=(176, 222, 248))
    d.rectangle((x0, y1 - 26, x1, y1), fill=(150, 210, 140)); d.ellipse((x0 - 10, y1 - 40, x0 + 60, y1 - 10), fill=(132, 196, 120))
    d.ellipse((x0 + 14, y0 + 12, x0 + 40, y0 + 24), fill=(255, 255, 255)); d.ellipse((x0 + 28, y0 + 8, x0 + 54, y0 + 22), fill=(255, 255, 255))
    d.polygon([(x1 - 40, y1 - 30), (x1 - 30, y1 - 44), (x1 - 20, y1 - 30)], fill=(150, 160, 200))  # 먼 하늘섬
    d.line((x1, y0 + 20, x1 - 30, y0 + 34), fill=(110, 70, 60), width=2)
    for bx, by in ((x1 - 8, y0 + 20), (x1 - 20, y0 + 28), (x1 - 28, y0 + 36), (x1 - 14, y0 + 30)):
        d.ellipse((bx - 3, by - 3, bx + 3, by + 3), fill=(250, 196, 214), outline=(220, 140, 170))
    cx = (x0 + x1) // 2
    d.line((cx, y0, cx, y1), fill=K.WOOD[2], width=3); d.line((x0, (y0 + y1) // 2, x1, (y0 + y1) // 2), fill=K.WOOD[2], width=3)
    for side in (x0 - 12, x1 + 2):                                    # 커튼
        d.rectangle((side, y0 - 8, side + 10, y1 + 10), fill=(250, 214, 150), outline=INK)
        d.line((side + 4, y0 - 6, side + 4, y1 + 8), fill=(236, 190, 120))
    d.rectangle((x0 - 16, y0 - 10, x1 + 16, y0 - 7), fill=K.WOOD[1], outline=INK)
    d.rectangle((x0 - 6, y1 + 4, x1 + 6, y1 + 9), fill=K.WOOD[3], outline=INK)            # 창틀 + 화분
    d.rectangle((x1 - 22, y1 - 6, x1 - 10, y1 + 4), fill=(200, 110, 70), outline=INK); d.ellipse((x1 - 26, y1 - 18, x1 - 6, y1 - 4), fill=(110, 180, 90), outline=INK)
    return im


# ---------------- 창문 v2: 섬 풍경 (표지와 같은 세계) ----------------
def window_view(w, h, night=False):
    """창밖 풍경 w×h (논리 1배, 창 크기에 맞춰 직접 그림): 하늘 · 구름 · 떠 있는 섬 · 먼 산과 탑 · 언덕 · 매화 가지"""
    v = Image.new('RGBA', (w, h)); d = ImageDraw.Draw(v)
    mix = T5.mix
    hz = int(h * .62)                                              # 지평선
    sky = [(112, 178, 236), (150, 204, 244), (196, 228, 248), (246, 234, 226)] if not night else \
          [(20, 24, 62), (34, 40, 88), (60, 58, 116), (96, 80, 140)]
    for y in range(hz + 4):
        k = y / (hz + 4) * (len(sky) - 1); i = min(int(k), len(sky) - 2); t = int((k - i) * 4) / 4
        d.line((0, y, w, y), fill=mix(sky[i], sky[i + 1], t))
    rnd = random.Random(7)
    if night:
        for _ in range(34):
            x, y = rnd.randrange(w), rnd.randrange(hz - 6)
            d.point((x, y), fill=(255, 250, 220) if rnd.random() < .7 else (170, 196, 255))
        for x, y in ((18, 8), (60, 20)):
            d.point([(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], fill=(190, 200, 255)); d.point((x, y), fill=(255, 255, 255))
        mo = Image.new('RGBA', (w, h)); mdd = ImageDraw.Draw(mo)                 # 초승달 (안쪽을 투명하게 파냄)
        mdd.ellipse((w - 38, 16, w - 23, 31), fill=(255, 246, 196)); mdd.point((w - 34, 25), fill=(255, 255, 230))
        mdd.ellipse((w - 30, 12, w - 19, 23), fill=(0, 0, 0, 0)); v.alpha_composite(mo)
    else:
        d.ellipse((w - 36, 18, w - 22, 32), fill=(255, 248, 210)); d.ellipse((w - 34, 20, w - 24, 30), fill=(255, 236, 150))   # 해
    cl_hi, cl_lo = ((255, 255, 255), (212, 226, 242)) if not night else ((120, 120, 170), (84, 84, 136))
    def cloud(x, y, cw):
        for k in range(cw // 6):
            r = 3 + (k % 3); cx = x + k * 6 + 3
            d.ellipse((cx - r, y - r + 1, cx + r, y + r + 1), fill=cl_lo)
        for k in range(cw // 6):
            r = 3 + (k % 3); cx = x + k * 6 + 3
            d.ellipse((cx - r, y - r, cx + r, y + r - 1), fill=cl_hi)
        d.rectangle((x + 1, y, x + cw - 2, y + 3), fill=cl_hi); d.line((x + 2, y + 4, x + cw - 3, y + 4), fill=cl_lo)
    cloud(4, 14, 30); cloud(56, 28, 24)
    # 먼 산 두 겹
    far = [(176, 204, 222), (150, 186, 190)] if not night else [(58, 60, 112), (48, 56, 96)]
    for li, (base_y, amp, f, ph) in enumerate(((hz - 4, 7, .09, .5), (hz + 1, 5, .14, 2.0))):
        pts = [(x, base_y - amp * abs(math.sin(x * f + ph)) - 2 * math.sin(x * .4)) for x in range(0, w + 2)]
        d.polygon(pts + [(w, h), (0, h)], fill=far[li]); d.line(pts, fill=mix(far[li], (255, 255, 255), .25 if not night else .12))
    # 먼 언덕 위 탑 (오른쪽)
    tx, ty = w - 22, hz + 1
    wall_c, roof_c = ((236, 238, 248), (110, 140, 214)) if not night else ((110, 112, 160), (60, 76, 140))
    for (ox, tw, th) in ((-5, 4, 9), (0, 5, 15), (5, 4, 11)):
        d.rectangle((tx + ox - tw // 2, ty - th, tx + ox + tw // 2, ty), fill=wall_c)
        d.polygon([(tx + ox - tw // 2 - 1, ty - th), (tx + ox + tw // 2 + 1, ty - th), (tx + ox, ty - th - tw - 2)], fill=roof_c)
    d.point((tx, ty - 17 - 4), fill=(240, 90, 90))
    if night: d.point([(tx, ty - 9), (tx - 5, ty - 5), (tx + 5, ty - 6)], fill=(255, 214, 110))
    # 떠 있는 섬 (작게)
    ix, iy = 30, 30
    rock = [(150, 112, 88), (124, 90, 72), (100, 72, 60)] if not night else [(72, 64, 92), (58, 52, 80), (46, 42, 66)]
    grass = [(118, 188, 98), (152, 210, 118)] if not night else [(56, 92, 86), (70, 110, 96)]
    d.polygon([(ix - 13, iy), (ix + 13, iy), (ix + 6, iy + 6), (ix + 1, iy + 12), (ix - 2, iy + 13), (ix - 7, iy + 6)], fill=rock[1], outline=INK)
    d.line((ix - 9, iy + 3, ix + 8, iy + 3), fill=rock[0]); d.line((ix - 4, iy + 7, ix + 4, iy + 7), fill=rock[2])
    d.ellipse((ix - 14, iy - 3, ix + 14, iy + 3), fill=grass[0], outline=INK); d.line((ix - 10, iy - 1, ix + 9, iy - 1), fill=grass[1])
    d.line((ix - 6, iy - 2, ix - 7, iy - 7), fill=(80, 56, 50)); d.point([(ix - 9, iy - 8), (ix - 6, iy - 9), (ix - 4, iy - 7)], fill=(250, 186, 206) if not night else (170, 120, 160))
    for cx_, hh, col in ((ix + 4, 7, (150, 210, 255)), (ix + 7, 4, (214, 170, 255))):
        col = col if not night else mix(col, (40, 40, 90), .3)
        d.polygon([(cx_ - 1, iy - 1), (cx_ - 1, iy - hh + 1), (cx_, iy - hh), (cx_ + 1, iy - hh + 1), (cx_ + 1, iy - 1)], fill=col)
        if night: d.point((cx_, iy - hh - 2), fill=(200, 220, 255))
    for k in range(5): d.point((ix + 9, iy + 2 + k * 2), fill=(236, 248, 255) if not night else (150, 160, 210))   # 작은 폭포
    cloud(ix - 15, iy + 11, 18) if False else None
    # 가까운 언덕 두 겹 + 길 + 나무 + 꽃
    hills = [(146, 204, 120), (124, 190, 100)] if not night else [(44, 70, 74), (36, 60, 64)]
    for li, (by, amp, f, ph) in enumerate(((hz + 8, 4, .06, .3), (hz + 16, 3, .08, 1.9))):
        pts = [(x, by - amp * math.sin(x * f + ph)) for x in range(0, w + 2)]
        d.polygon(pts + [(w, h), (0, h)], fill=hills[li]); d.line(pts, fill=mix(hills[li], (255, 255, 255), .2 if not night else .06))
    path = (232, 210, 160) if not night else (90, 92, 110)
    d.polygon([(w // 2 - 4, hz + 13), (w // 2 + 1, hz + 13), (w // 2 + 12, h), (w // 2 - 10, h)], fill=path)
    for x, y in ((12, hz + 8), (22, hz + 10), (82, hz + 9)):                      # 동그란 나무
        tc = (90, 160, 80) if not night else (30, 52, 56)
        d.ellipse((x - 4, y - 7, x + 4, y + 1), fill=tc, outline=mix(tc, (0, 0, 0), .3)); d.point((x - 1, y - 5), fill=mix(tc, (255, 255, 255), .3))
        d.line((x, y + 1, x, y + 3), fill=(110, 76, 56))
    for k in range(14):
        x, y = rnd.randrange(w), rnd.randrange(hz + 18, h)
        c = [(255, 200, 214), (255, 240, 140), (255, 255, 255)][k % 3] if not night else (200, 255, 150)
        if night and k % 2: continue
        d.point((x, y), fill=c)
    if not night:
        for bx, by in ((48, 10), (54, 8), (60, 11)):                                # 새
            d.point([(bx - 1, by - 1), (bx, by), (bx + 1, by - 1)], fill=(80, 80, 110))
    # 앞쪽 매화 가지 (오른쪽 위에서)
    BR = (58, 40, 40) if not night else (24, 20, 30)
    pts = [(w + 1, 3), (w - 8, 6), (w - 16, 11), (w - 24, 13), (w - 31, 18)]
    for a_, b_ in zip(pts, pts[1:]): d.line((a_, b_), fill=BR, width=2)
    d.line(((w - 16, 11), (w - 19, 4), (w - 24, 1)), fill=BR); d.line(((w - 8, 6), (w - 9, 16)), fill=BR)
    pk, pk2 = ((250, 170, 196), (255, 228, 238)) if not night else ((150, 106, 146), (196, 156, 190))
    for bx, by in ((w - 4, 3), (w - 12, 8), (w - 20, 4), (w - 25, 1), (w - 27, 15), (w - 33, 18), (w - 9, 16), (w - 18, 13)):
        d.point([(bx, by - 1), (bx - 1, by), (bx + 1, by), (bx, by + 1)], fill=pk); d.point((bx, by), fill=pk2)
    # 유리 반짝임 + 안쪽 그림자
    g = Image.new('RGBA', (w, h)); gd = ImageDraw.Draw(g)
    for off, ww in ((14, 5), (24, 2), (w // 2 + 18, 4)):
        gd.line(((off, 0), (off - h * .5, h)), fill=(255, 255, 255, 40 if not night else 18), width=ww)
    gd.line((0, 0, w, 0), fill=(40, 30, 40, 90)); gd.line((0, 0, 0, h), fill=(40, 30, 40, 60))
    v.alpha_composite(g)
    return v


def window2(base, x0, y0, w, h, night=False):
    """아치 창문: 나무 틀(밝은 면·그늘) + 십자 창살 + 창턱 화분 + 묶은 커튼 + 커튼봉"""
    d = ImageDraw.Draw(base)
    arch = 14
    v = window_view(w, h + arch, night)
    mask = Image.new('L', (w, h + arch)); md = ImageDraw.Draw(mask)
    md.rectangle((0, arch, w, h + arch), fill=255); md.ellipse((0, 0, w - 1, arch * 2), fill=255)
    WD = [(92, 56, 40), (128, 84, 52), (168, 116, 70), (206, 158, 102), (232, 196, 140)]
    # 바깥 틀
    d.rectangle((x0 - 6, y0 + arch - 2, x0 + w + 5, y0 + arch + h + 4), fill=WD[2], outline=INK)
    d.ellipse((x0 - 6, y0 - 6, x0 + w + 5, y0 + arch * 2 + 6), fill=WD[2], outline=INK)
    d.rectangle((x0 - 5, y0 + arch, x0 + w + 4, y0 + arch + h + 3), fill=WD[2])
    d.arc((x0 - 4, y0 - 4, x0 + w + 3, y0 + arch * 2 + 4), 180, 360, fill=WD[4])          # 위 밝은 면
    d.line((x0 - 4, y0 + arch, x0 - 4, y0 + arch + h + 2), fill=WD[3])
    d.line((x0 + w + 3, y0 + arch, x0 + w + 3, y0 + arch + h + 2), fill=WD[1])
    paste(base, Image.composite(v, Image.new('RGBA', v.size), mask), (x0, y0))
    d.arc((x0 - 1, y0 - 1, x0 + w, y0 + arch * 2 + 1), 180, 360, fill=INK)
    d.rectangle((x0 - 1, y0 + arch, x0 + w, y0 + arch + h), outline=INK)
    d.line((x0, y0 + arch, x0 + w - 1, y0 + arch), fill=(0, 0, 0, 0))
    paste(base, Image.composite(v, Image.new('RGBA', v.size), mask).crop((0, arch, w, arch + 1)), (x0, y0 + arch))
    # 창살 (가운데 세로 + 가로 2 + 아치 부채살)
    cx = x0 + w // 2
    for (a, b) in (((cx - 1, y0), (cx - 1, y0 + arch + h)), ((cx + 1, y0), (cx + 1, y0 + arch + h))):
        d.line((a, b), fill=INK)
    d.line((cx, y0, cx, y0 + arch + h), fill=WD[3])
    for yy in (y0 + arch, y0 + arch + h // 2):
        d.line((x0, yy - 1, x0 + w - 1, yy - 1), fill=INK); d.line((x0, yy + 1, x0 + w - 1, yy + 1), fill=INK)
        d.line((x0, yy, x0 + w - 1, yy), fill=WD[3])
    # 창턱 + 화분 2개
    sy = y0 + arch + h + 4
    d.rectangle((x0 - 12, sy, x0 + w + 11, sy + 5), fill=WD[3], outline=INK); d.line((x0 - 11, sy + 1, x0 + w + 10, sy + 1), fill=WD[4])
    d.rectangle((x0 - 8, sy + 6, x0 + w + 7, sy + 8), fill=WD[1], outline=INK)
    for px_, cols in ((x0 + 8, ((240, 110, 140), (255, 200, 210))), (x0 + w - 22, ((250, 200, 70), (255, 240, 170)))):
        d.polygon([(px_, sy - 9), (px_ + 14, sy - 9), (px_ + 12, sy), (px_ + 2, sy)], fill=(206, 120, 80), outline=INK)
        d.line((px_ + 1, sy - 8, px_ + 13, sy - 8), fill=(236, 160, 110))
        for fx, fy in ((px_ + 3, sy - 14), (px_ + 8, sy - 17), (px_ + 12, sy - 13)):
            d.line((fx, fy + 2, px_ + 7, sy - 9), fill=(80, 150, 70))
            d.point([(fx - 1, fy), (fx + 1, fy), (fx, fy - 1), (fx, fy + 1)], fill=cols[0]); d.point((fx, fy), fill=cols[1])
    # 커튼 (양옆, 아래를 끈으로 묶음)
    CT = [(196, 120, 140), (226, 156, 172), (246, 196, 206)]
    for side in (-1, 1):
        ox = x0 - 20 if side < 0 else x0 + w + 4
        top_ = y0 - 2; tie = y0 + arch + h // 2 + 14; bot = sy + 4
        poly = [(ox, top_), (ox + 16, top_), (ox + (12 if side < 0 else 8), tie), (ox + 14 if side < 0 else ox + 2, bot), (ox, bot)] if side < 0 else \
               [(ox, top_), (ox + 16, top_), (ox + 16, bot), (ox + 2, bot), (ox + 6, tie)]
        d.polygon(poly, fill=CT[1], outline=INK)
        for k in (4, 9):
            fx = ox + k if side < 0 else ox + 16 - k
            d.line((fx, top_ + 2, fx + (2 if side < 0 else -2), tie - 2), fill=CT[0])
        d.line((ox + (2 if side < 0 else 14), top_ + 2, ox + (2 if side < 0 else 14), bot - 2), fill=CT[2])
        tx = ox + (10 if side < 0 else 6)
        d.rectangle((tx - 4, tie - 1, tx + 4, tie + 2), fill=(250, 204, 70), outline=INK)
        d.point((tx, tie + 4), fill=(250, 204, 70)); d.line((tx, tie + 3, tx, tie + 6), fill=(214, 160, 40))
    # 커튼봉
    ry = y0 - 6
    d.rectangle((x0 - 26, ry, x0 + w + 25, ry + 3), fill=WD[1], outline=INK); d.line((x0 - 25, ry + 1, x0 + w + 24, ry + 1), fill=WD[3])
    for ex in (x0 - 30, x0 + w + 26):
        d.ellipse((ex - 1, ry - 2, ex + 5, ry + 5), fill=(250, 204, 70), outline=INK); d.point((ex + 1, ry), fill=(255, 240, 170))
    for rx in range(x0 - 18, x0 - 4, 5): d.ellipse((rx, ry - 1, rx + 3, ry + 4), outline=INK)
    for rx in range(x0 + w + 6, x0 + w + 22, 5): d.ellipse((rx, ry - 1, rx + 3, ry + 4), outline=INK)


def rug(base, cx, cy, rx, ry):
    d = ImageDraw.Draw(base)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(206, 96, 110), outline=INK)
    d.ellipse((cx - rx + 6, cy - ry + 4, cx + rx - 6, cy + ry - 4), outline=(250, 214, 150))
    d.ellipse((cx - rx + 14, cy - ry + 9, cx + rx - 14, cy + ry - 9), fill=(226, 126, 132))
    for i in range(10):
        a = i * math.pi / 5
        d.point((cx + int((rx - 3) * math.cos(a)), cy + int((ry - 2) * math.sin(a))), fill=(250, 214, 150))


def shelf(base, x, y, cols, rows, cell=36, n=2, rowh=None, label=True):
    """트로피 진열장: 나무 틀 + 칸마다 트로피"""
    rowh = rowh or cell + 6
    w = cols * cell + 12; h = rows * rowh + 14
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + h), fill=K.WOOD[1], outline=INK)
    d.rectangle((x + 4, y + 6, x + w - 4, y + h - 4), fill=(110, 70, 52))
    d.rectangle((x - 3, y - 4, x + w + 3, y + 2), fill=K.WOOD[2], outline=INK)
    spots = []
    for r in range(rows):
        sy = y + 8 + r * rowh
        for c in range(cols):
            i = r * cols + c
            if i >= len(ACH): break
            code, name, got = ACH[i]
            tx = x + 6 + c * cell + (cell - 16 * n) // 2
            ty = sy + rowh - 6 - 16 * n
            if got:
                d.ellipse((tx + 2, ty + 16 * n - 4, tx + 16 * n - 2, ty + 16 * n + 1), fill=(90, 56, 42))
            paste(base, trophy(code, got, n), (tx, ty))
            spots.append((i, tx, ty))
        d.rectangle((x + 4, sy + rowh - 6, x + w - 4, sy + rowh - 2), fill=K.WOOD[3], outline=INK)
    return spots, (x, y, x + w, y + h)


def sparkle(base, x, y, col=(255, 250, 210)):
    d = ImageDraw.Draw(base); d.point([(x, y - 2), (x, y + 2), (x - 2, y), (x + 2, y)], fill=col); d.point((x, y), fill=(255, 255, 255))


def animal(base, key, stage, cx, foot, flip=False, scale=2):
    s = B.spr(key, stage, scale, flip)
    sh = Image.new('RGBA', (40, 8)); ImageDraw.Draw(sh).ellipse((2, 1, 37, 6), fill=(60, 30, 20, 70)); base.alpha_composite(sh, (cx - 20, foot - 4))
    paste(base, s, (cx - s.width // 2, foot - s.height + 2))


def bubble(base, x, y, txt):
    f = K.F_SMALL(); w = int(f.getlength(txt)) + 10
    B.card(base, x - w // 2, y, w, 16); text_mid(base, x, y + 8, txt, f, K.TEXT)


def desk(base, x, y, w=96):
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + 7), fill=K.WOOD[3], outline=INK)
    for lx in (x + 4, x + w - 9): d.rectangle((lx, y + 7, lx + 5, y + 44), fill=K.WOOD[1], outline=INK)
    d.rectangle((x + 10, y + 7, x + w - 10, y + 18), fill=K.WOOD[2], outline=INK); d.rectangle((x + w // 2 - 4, y + 11, x + w // 2 + 4, y + 13), fill=GOLD[2])


def diary_closed(base, x, y):
    d = ImageDraw.Draw(base)
    d.polygon([(x, y + 8), (x + 30, y + 2), (x + 40, y + 8), (x + 10, y + 14)], fill=(150, 90, 170), outline=INK)
    d.line((x + 10, y + 14, x + 10, y + 16), fill=INK); d.polygon([(x, y + 8), (x + 10, y + 14), (x + 10, y + 16), (x, y + 10)], fill=(250, 240, 220), outline=INK)
    d.polygon([(x + 10, y + 14), (x + 40, y + 8), (x + 40, y + 10), (x + 10, y + 16)], fill=(250, 240, 220), outline=INK)
    d.line((x + 22, y + 5, x + 26, y + 11), fill=(250, 200, 60))
    d.rectangle((x + 46, y - 4, x + 52, y + 12), fill=(250, 250, 250), outline=INK); d.line((x + 47, y - 8, x + 51, y - 4), fill=(110, 170, 110), width=2)  # 깃펜 컵


def frame(base, x, y, w, h, inner=(250, 240, 220)):
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + h), fill=GOLD[1], outline=INK); d.rectangle((x + 3, y + 3, x + w - 3, y + h - 3), fill=inner, outline=GOLD[0])
    d.line((x + w // 2, y - 8, x + 6, y), fill=INK); d.line((x + w // 2, y - 8, x + w - 6, y), fill=INK); d.point((x + w // 2, y - 8), fill=GOLD[2])


def lamp(base, x, y):
    d = ImageDraw.Draw(base)
    d.rectangle((x + 6, y + 14, x + 8, y + 40), fill=K.WOOD[0]); d.rectangle((x + 1, y + 40, x + 13, y + 44), fill=K.WOOD[1], outline=INK)
    d.polygon([(x + 2, y + 14), (x + 12, y + 14), (x + 10, y), (x + 4, y)], fill=(250, 226, 160), outline=INK)
    d.ellipse((x - 10, y + 8, x + 24, y + 26), fill=(255, 240, 180, 40))


def cushion(base, cx, cy):
    d = ImageDraw.Draw(base)
    d.ellipse((cx - 26, cy - 9, cx + 26, cy + 9), fill=(120, 170, 220), outline=INK); d.ellipse((cx - 20, cy - 6, cx + 20, cy + 5), fill=(160, 200, 240))


def plant(base, x, y):
    d = ImageDraw.Draw(base)
    for a in (-0.9, -0.4, 0, 0.4, 0.9):
        ex, ey = x + 10 + int(16 * math.sin(a)), y - int(18 * math.cos(a))
        d.line((x + 10, y + 4, ex, ey), fill=(70, 140, 70), width=2); d.ellipse((ex - 4, ey - 3, ex + 4, ey + 3), fill=(110, 190, 90), outline=INK)
    d.polygon([(x, y), (x + 20, y), (x + 17, y + 16), (x + 3, y + 16)], fill=(220, 150, 100), outline=INK)


def top(base, title='마이룸'):
    B.header(base, '6일차 · 낮 14:20 · 맑음', '1,850')
    button(base, 12, 32, 56, 20, '지도', 'brown', icon='back', f=K.F_BODY())
    ribbon(base, 78, 33, 80, title, 'red')


def ach_count(): return sum(1 for a in ACH if a[2]), len(ACH)


def cursor(base, x, y):
    d = ImageDraw.Draw(base)
    pts = [(0, 0), (0, 11), (3, 8), (5, 12), (7, 11), (5, 7), (9, 7)]
    d.polygon([(x + a, y + b) for a, b in pts], fill=(255, 255, 255), outline=INK)


def tip(base, x, y, lines):
    f = K.F_SMALL(); w = max(int(f.getlength(t)) for t, _ in lines) + 12; h = 6 + 13 * len(lines)
    B.card(base, x, y, w, h)
    for i, (t, c) in enumerate(lines): K.draw_text(base, (x + 6, y + 5 + i * 13), t, f, c)


# ---------------- A: 방 + 오른쪽 쪽지 ----------------
def cand_a(out, sel=8):
    base = room(floor_y=236, window=(170, 56, 270, 134))
    d = ImageDraw.Draw(base)
    spots, sbox = shelf(base, 18, 64, 4, 4, cell=32, n=2, rowh=40)
    frame(base, 296, 62, 54, 40); K.draw_text(base, (323, 75), '전투 승리', K.F_SMALL(), K.TEXT, 'mm'); K.draw_text(base, (323, 89), '12', K.F_TITLE(), (200, 70, 60), 'mm')
    frame(base, 300, 120, 46, 36); K.draw_text(base, (323, 131), '수확', K.F_SMALL(), K.TEXT, 'mm'); K.draw_text(base, (323, 144), '27', K.F_TITLE(), (80, 150, 70), 'mm')
    desk(base, 290, 196, 104); diary_closed(base, 304, 182); lamp(base, 370, 152)
    plant(base, 160, 216)
    rug(base, 220, 300, 130, 34); cushion(base, 340, 290)
    animal(base, 'dealer_normal_01', 2, 160, 300); animal(base, 'tank_normal_03', 1, 236, 318, True)
    animal(base, 'healer_normal_05', 1, 300, 296); animal(base, 'healer_normal_02', 1, 344, 290, True)
    bubble(base, 160, 244, '♪')
    # 고른 트로피 꺾쇠
    i, tx, ty = spots[sel]
    B.corners(base, tx - 3, ty - 3, tx + 34, ty + 34)
    for (j, sx, sy) in spots:
        if ACH[j][2] and j % 3 == 0: sparkle(base, sx + 28, sy + 4)
    top(base)
    got, tot = ach_count()
    # 오른쪽 쪽지
    px, py, pw, ph = 414, 30, 218, 324
    B.panel(base, px, py, pw, ph)
    K.draw_text(base, (px + 12, py + 14), '업적', K.F_TITLE(), K.TEXT, 'lm')
    K.draw_text(base, (px + pw - 12, py + 14), f'{got} / {tot}', K.F_TITLE(), K.TEXT, 'rm')
    gauge(base, px + 12, py + 24, pw - 24, 10, got, tot, 'orange')
    # 고른 업적
    code, name, ok = ACH[sel]
    B.card(base, px + 10, py + 42, pw - 20, 88)
    d.rectangle((px + 18, py + 52, px + 69, py + 103), fill=(110, 70, 52), outline=INK)
    paste(base, trophy(code, ok, 3), (px + 20, py + 54))
    K.draw_text(base, (px + 78, py + 60), name, K.F_TITLE(), K.TEXT, 'lm')
    chip(base, px + 78, py + 72, '달성!' if ok else '아직', 'green' if ok else 'gray')
    K.draw_text(base, (px + 78, py + 100), HOWTO[code], K.F_SMALL(), K.TEXT_SOFT, 'lm')
    K.draw_text(base, (px + 18, py + 118), '선반의 트로피를 눌러 확인!', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    # 기록
    K.draw_text(base, (px + 12, py + 146), '나의 기록', K.F_TITLE(), K.TEXT, 'lm')
    for k, (key, lab, v, ic) in enumerate(STATS):
        cx = px + 10 + (k % 2) * 100; cy = py + 158 + (k // 2) * 26
        B.card(base, cx, cy, 98, 24)
        paste(base, K.icon(ic), (cx + 5, cy + 6))
        K.draw_text(base, (cx + 20, cy + 12), lab, K.F_SMALL(), K.TEXT, 'lm')
        K.draw_text(base, (cx + 92, cy + 12), str(v), K.F_TITLE(), K.TEXT, 'rm')
    K.draw_text(base, (px + 12, py + 248), '최근 일기', K.F_TITLE(), K.TEXT, 'lm')
    for k, (kind, t) in enumerate(DIARY[:4]):
        yy = py + 262 + k * 15
        paste(base, K.icon(DIARY_ICON[kind]), (px + 12, yy - 6))
        K.draw_text(base, (px + 28, yy), t, K.F_SMALL(), K.TEXT, 'lm')
    save(base, out)


# ---------------- B: 방 위 + 아래 서랍 탭 ----------------
def tray_tabs(base, x, y, tabs, sel):
    cx = x
    for i, t in enumerate(tabs):
        w = int(K.F_TITLE().getlength(t)) + 22
        button(base, cx, y - (2 if i == sel else 0), w, 20, t, 'orange' if i == sel else 'brown', f=K.F_TITLE())
        cx += w + 4


def cand_b(out, tab=0):
    base = room(floor_y=200, window=(268, 46, 372, 116))
    d = ImageDraw.Draw(base)
    spots, sbox = shelf(base, 20, 60, 8, 2, cell=24, n=1, rowh=24)   # 작은 선반: 트로피 원본 크기
    frame(base, 420, 56, 60, 44); K.draw_text(base, (450, 70), '우리 섬', K.F_SMALL(), K.TEXT, 'mm'); K.draw_text(base, (450, 86), '6일차', K.F_TITLE(), K.TEXT, 'mm')
    frame(base, 500, 64, 40, 34, (176, 222, 248)); d.ellipse((508, 80, 532, 92), fill=(130, 196, 110))
    desk(base, 540, 150, 86); diary_closed(base, 552, 136); lamp(base, 604, 106)
    plant(base, 236, 182); plant(base, 400, 180)
    rug(base, 320, 222, 150, 18); cushion(base, 470, 216)
    animal(base, 'dealer_normal_01', 2, 120, 226); animal(base, 'tank_normal_03', 1, 270, 232, True)
    animal(base, 'healer_normal_05', 1, 360, 222); animal(base, 'healer_normal_02', 1, 472, 214, True)
    bubble(base, 120, 172, '♪'); bubble(base, 472, 162, 'zZ')
    top(base)
    got, tot = ach_count()
    # 아래 서랍
    tx, ty, tw, th = 8, 242, 624, 112
    tray_tabs(base, tx + 10, ty - 14, [f'업적 {got}/{tot}', '나의 기록', '일기'], tab)
    B.panel(base, tx, ty + 4, tw, th)
    if tab == 0:
        for k, (code, name, ok) in enumerate(ACH):
            cx = tx + 10 + (k % 8) * 62; cy = ty + 14 + (k // 8) * 46
            B.card(base, cx, cy, 58, 42, sel=(k == 8))
            paste(base, trophy(code, ok, 2), (cx + 13, cy + 5))
        # 오른쪽 끝 설명
        B.card(base, tx + 510, ty + 14, 106, 88)
        code, name, ok = ACH[8]
        K.draw_text(base, (tx + 516, ty + 26), name, K.F_TITLE(), K.TEXT, 'lm')
        chip(base, tx + 516, ty + 36, '달성!', 'green')
        K.draw_text(base, (tx + 516, ty + 66), '동물 한 마리', K.F_SMALL(), K.TEXT_SOFT, 'lm')
        K.draw_text(base, (tx + 516, ty + 79), '진화시키기', K.F_SMALL(), K.TEXT_SOFT, 'lm')
    save(base, out)


# ---------------- C: 방 안에 전부 ----------------
def board(base, x, y, w, h):
    d = ImageDraw.Draw(base)
    d.rectangle((x, y, x + w, y + h), fill=K.WOOD[1], outline=INK)
    d.rectangle((x + 5, y + 5, x + w - 5, y + h - 5), fill=(52, 92, 72), outline=INK)
    d.rectangle((x + 10, y + h - 4, x + w - 10, y + h + 2), fill=K.WOOD[2], outline=INK)
    d.rectangle((x + w - 30, y + h - 6, x + w - 22, y + h - 3), fill=(250, 250, 250))
    chalk = (236, 240, 226)
    K.draw_text(base, (x + w // 2, y + 16), '나의 기록', K.F_TITLE(), (250, 230, 140), 'mm')
    d.line((x + 20, y + 25, x + w - 20, y + 25), fill=(110, 150, 126))
    for k, (key, lab, v, ic) in enumerate(STATS):
        cx = x + 14 + (k % 2) * ((w - 20) // 2); cy = y + 38 + (k // 2) * 20
        paste(base, K.icon(ic), (cx, cy - 6))
        K.draw_text(base, (cx + 15, cy), lab, K.F_SMALL(), chalk, 'lm')
        K.draw_text(base, (cx + (w - 20) // 2 - 12, cy), str(v), K.F_TITLE(), (255, 255, 255), 'rm')


def diary_open(base, x, y, w, h, n=6):
    """스프링 일기장: 최근 일 한 줄씩"""
    d = ImageDraw.Draw(base)
    d.rectangle((x + 3, y + 3, x + w + 3, y + h + 3), fill=(120, 70, 140))
    d.rectangle((x, y, x + w, y + h), fill=(252, 244, 226), outline=INK)
    d.rectangle((x, y, x + w, y + 22), fill=(170, 110, 190), outline=INK)
    for rx in range(x + 10, x + w - 6, 14):
        d.ellipse((rx, y - 4, rx + 5, y + 4), fill=(200, 200, 210), outline=INK)
    K.draw_text(base, (x + 8, y + 13), '일기장', K.F_TITLE(), (255, 246, 230), 'lm', (110, 60, 130))
    K.draw_text(base, (x + w - 8, y + 13), '최근 일', K.F_SMALL(), (240, 220, 246), 'rm')
    for k, (kind, t) in enumerate(DIARY[:n]):
        ly = y + 34 + k * 17
        d.line((x + 6, ly + 8, x + w - 6, ly + 8), fill=(226, 210, 196))
        paste(base, K.icon(DIARY_ICON[kind]), (x + 7, ly - 6))
        K.draw_text(base, (x + 22, ly), t, K.F_SMALL(), K.TEXT, 'lm')
    d.rectangle((x + w - 16, y + h - 2, x + w - 10, y + h + 10), fill=(220, 70, 70))


def cand_c(out, night=False, hover=8):
    base = room(floor_y=246, window=None)
    window2(base, 248, 40, 102, 60, night)
    d = ImageDraw.Draw(base)
    top(base)
    got, tot = ach_count()
    # 진열장 (크게)
    spots, sbox = shelf(base, 12, 70, 4, 4, cell=40, n=2, rowh=42)
    plate_w = 120; B.card(base, 12 + (172 - plate_w) // 2, 248, plate_w, 18)
    text_mid(base, 12 + 86, 257, f'트로피 {got} / {tot}', K.F_BODY(), K.TEXT)
    for (j, sx, sy) in spots:
        if ACH[j][2] and j in (0, 8, 12): sparkle(base, sx + 30, sy + 3)
    board(base, 196, 132, 206, 96)
    desk(base, 412, 204, 218)
    diary_open(base, 412, 70, 218, 128)
    rug(base, 320, 312, 140, 32); cushion(base, 520, 300)
    plant(base, 186, 230)
    animal(base, 'dealer_normal_01', 2, 250, 308); animal(base, 'tank_normal_03', 1, 330, 326, True)
    animal(base, 'healer_normal_05', 1, 400, 306); animal(base, 'healer_normal_02', 1, 520, 300, True)
    bubble(base, 250, 252, '♪'); bubble(base, 520, 244, 'zZ')
    # 마우스 올린 트로피 말풍선
    i, tx, ty = spots[hover]
    code, name, ok = ACH[hover]
    B.corners(base, tx - 3, ty - 3, tx + 34, ty + 34)
    lines = [(name, K.TEXT), ('달성!' if ok else '아직', (70, 150, 70) if ok else K.TEXT_SOFT), (HOWTO[code], K.TEXT_SOFT)]
    tw = max(int(K.F_SMALL().getlength(t)) for t, _ in lines) + 12
    tip(base, tx + 36 if tx + 36 + tw < W - 4 else tx - tw - 4, ty + 6, lines)
    cursor(base, tx + 22, ty + 22)
    save(base, out)


def cand_c_locked(out):
    """C에서 아직 못 딴 트로피에 마우스"""
    base = room(floor_y=246, window=(268, 40, 360, 96))
    top(base)
    spots, sbox = shelf(base, 12, 70, 4, 4, cell=40, n=2, rowh=42)
    i, tx, ty = spots[15]
    B.corners(base, tx - 3, ty - 3, tx + 34, ty + 34)
    tip(base, tx - 40, ty + 38, [('다이아몬드 승급', K.TEXT), ('아직', K.TEXT_SOFT), ('다이아몬드 대회 우승', K.TEXT_SOFT)])
    base.crop((0, 26, 320, 360)).save(out)


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else '.'); out.mkdir(parents=True, exist_ok=True)
    K.FONT_DIR = GAME / 'assets' / 'fonts'; B.SPR = GAME / 'assets' / 'sprites'
    cand_c(out / 'room_C.png'); cand_c(out / 'room_C_night.png', night=True); cand_c(out / 'room_C_locked.png', hover=15)
    for nt, nm in ((False, 'day'), (True, 'night')):
        b = room(floor_y=246, window=None); window2(b, 248, 40, 102, 60, nt)
        b.crop((214, 26, 384, 132)).resize((170 * 4, 106 * 4), Image.NEAREST).save(out / f'window_{nm}.png')
    sheet = Image.new('RGBA', (16 * 3 * 8 + 18, 16 * 3 * 4 + 18), (110, 70, 52, 255))
    for k, (code, name, ok) in enumerate(ACH):
        paste(sheet, trophy(code, True, 3), (9 + (k % 8) * 48, 9 + (k // 8) * 48))
        paste(sheet, trophy(code, False, 3), (9 + (k % 8) * 48, 9 + 96 + (k // 8) * 48))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(out / 'trophies.png')
