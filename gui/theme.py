"""화면 크기, 색, 글꼴, 한글 라벨. 모든 화면은 docs/UI_KIT.md를 따른다.

"1배로 그리고 2배로 키운다": 모든 화면은 640×360 논리 화면에 그리고,
App이 매 프레임 창(1280×720)에 2배로 붙인다. 아래 좌표·크기는 전부 논리 픽셀.
"""
import json
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KIT_DIR = os.path.join(ROOT, 'assets', 'ui', 'kit')
FONT_DIR = os.path.join(ROOT, 'assets', 'fonts')

WIDTH, HEIGHT = 640, 360          # 논리 화면
SCALE = 2                         # 창 = 논리 × 2
WINDOW = (WIDTH * SCALE, HEIGHT * SCALE)
HEADER_H = 26                     # 상단 바 (창에서 52px)
FPS = 30

# 시간 속도 (백엔드 set_demo_mode에 그대로 넘긴다)
SPEED_FAST = 5      # F5: 평소 플레이용 빠르게
SPEED_DEMO = 60     # F12: 영상 촬영용 시연 모드

# ---- 색 (ui_kit.json) ----
with open(os.path.join(KIT_DIR, 'ui_kit.json'), encoding='utf-8') as _f:
    KIT = json.load(_f)
TEXT = tuple(KIT['colors']['text'])
TEXT_SOFT = tuple(KIT['colors']['text_soft'])
INK = tuple(KIT['colors']['ink'])
WHITE = (255, 252, 240)
# 색 이름 → 4단계 [가장 어두움, 어두움, 본색, 밝음]
PALETTE = {name: [tuple(c) for c in shades] for name, shades in KIT['colors']['gauge_fill'].items()}
WOOD = [(84, 52, 36), (122, 78, 48), (162, 108, 64), (198, 146, 92), (226, 182, 124)]   # tools/uikit.py와 같음


def shade(name, i=2):
    return PALETTE[name][i]


OK, WARN, BAD = shade('green', 1), shade('orange', 1), shade('red', 1)   # 글씨용 (밝은 배경 위)

# ---- 한글 라벨 ----
ROLE_LABEL = {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}
ROLE_KIT = {'dealer': 'orange', 'tank': 'blue', 'healer': 'green'}          # 역할 색
ELEMENT_LABEL = {'fire': '불', 'water': '물', 'wind': '바람'}
ELEMENT_KIT = {'fire': 'red', 'water': 'blue', 'wind': 'green'}
STAT_LABEL = {'hp': '체력', 'attack': '공격력', 'defense': '방어력', 'agility': '민첩성'}
STAT_KIT = {'hp': 'red', 'attack': 'orange', 'defense': 'blue', 'agility': 'green'}   # 게이지 색
STAT_ICON = {'hp': 'heart', 'attack': 'sword', 'defense': 'shield', 'agility': 'wing'}
STATS = ('hp', 'attack', 'defense', 'agility')
NATURE_LABEL = {'glutton': '먹보', 'sleepy': '잠꾸러기', 'playful': '장난꾸러기',
                'balanced': '평범한', 'picky': '까칠'}
DIFFICULTY_LABEL = {'easy': '쉬움', 'medium': '중간', 'hard': '어려움'}

# 상태 3단계 기준 (백엔드 GameService._status_label 과 같은 값)
STATUS_BAD, STATUS_NORMAL_MAX = 30, 55


def status_level(kind, value):
    """'좋음' / '보통' / '나쁨'. 피로도는 높을수록 나쁨."""
    if kind == 'fatigue':
        return '좋음' if value < STATUS_BAD else ('보통' if value <= STATUS_NORMAL_MAX else '나쁨')
    return '나쁨' if value < STATUS_BAD else ('보통' if value <= STATUS_NORMAL_MAX else '좋음')


LEVEL_KIT = {'좋음': 'green', '보통': 'orange', '나쁨': 'red'}

# ---- 한국어 조사 ----
_JOSA = {'을': ('을', '를'), '를': ('을', '를'), '이': ('이', '가'), '가': ('이', '가'),
         '은': ('은', '는'), '는': ('은', '는'), '과': ('과', '와'), '와': ('과', '와'),
         '으로': ('으로', '로'), '로': ('으로', '로'), '아': ('아', '야'), '야': ('아', '야')}


def josa(word, particle):
    """받침을 보고 조사를 붙인다. josa('불꽃매', '을') → '불꽃매를', josa('물방울수달', '이') → '물방울수달이'.

    '으로/로'는 ㄹ받침이면 '로'. 마지막 글자가 한글이 아니면 '을(를)'처럼 둘 다 적는다.
    """
    word = str(word)
    with_final, without = _JOSA[particle]
    last = word[-1:] if word else ''
    if not ('가' <= last <= '힣'):
        return f"{word}{with_final}({without})" if particle not in ('으로', '로') else f"{word}(으)로"
    final = (ord(last) - 0xAC00) % 28
    if with_final == '으로':
        return word + ('로' if final in (0, 8) else '으로')     # 받침 없음 또는 ㄹ받침 → 로
    return word + (with_final if final else without)


# ---- 글꼴 (갈무리, 정해진 크기로만) ----
FONTS = {
    'title': ('Galmuri11-Bold.ttf', 12),   # 제목·버튼·이름
    'body': ('Galmuri11.ttf', 12),         # 본문
    'small': ('Galmuri9.ttf', 10),         # 작은 글씨·칩·게이지 숫자
    'big': ('Galmuri14.ttf', 15),          # 상세 화면 동물 이름
}
_font_cache = {}


def font(kind='body'):
    if kind not in _font_cache:
        name, size = FONTS[kind]
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            _font_cache[kind] = pygame.font.Font(path, size)
        else:   # 글꼴 파일이 없을 때만: 시스템 한글 폰트
            sys_path = pygame.font.match_font(('malgungothic', 'applesdgothicneo', 'nanumgothic', 'notosanscjkkr'))
            _font_cache[kind] = pygame.font.Font(sys_path, size)
    return _font_cache[kind]
