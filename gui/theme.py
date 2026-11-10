"""Colors, fonts and labels shared by every screen."""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WIDTH, HEIGHT = 1280, 720
FPS = 30

# 시간 속도 (백엔드 set_demo_mode에 그대로 넘긴다)
SPEED_FAST = 5      # F5: 평소 플레이용 빠르게
SPEED_DEMO = 60     # F12: 영상 촬영용 시연 모드

# 색 (밝은 파스텔 농장 느낌)
BG = (246, 241, 230)
PANEL = (255, 252, 245)
PANEL_EDGE = (214, 200, 176)
INK = (52, 44, 38)
INK_SOFT = (128, 116, 104)
ACCENT = (232, 128, 64)
ACCENT_DARK = (186, 92, 40)
OK = (92, 168, 96)
WARN = (226, 168, 52)
BAD = (214, 84, 72)
DISABLED = (200, 194, 186)
GRASS = (168, 208, 132)
GRASS_DARK = (138, 182, 104)
NIGHT_TINT = (24, 30, 72, 110)

ROLE_LABEL = {'dealer': '딜러', 'tank': '탱커', 'healer': '힐러'}
ROLE_COLOR = {'dealer': (236, 104, 64), 'tank': (64, 140, 220), 'healer': (72, 186, 150)}
ELEMENT_LABEL = {'fire': '불', 'water': '물', 'wind': '바람'}
STAT_LABEL = {'hp': '체력', 'attack': '공격력', 'defense': '방어력', 'agility': '민첩성'}
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


LEVEL_COLOR = {'좋음': OK, '보통': WARN, '나쁨': BAD}

_FONT_CANDIDATES = ('malgungothic', 'applesdgothicneo', 'applegothic', 'nanumgothic',
                    'notosanscjkkr', 'notosanskr', 'notosanscjk', 'gulim')
_LINUX_FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
_font_cache = {}


def font(size, bold=False):
    """한글이 나오는 폰트. assets/fonts/ 안 ttf → 시스템 폰트 → 기본 폰트 순서."""
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    f = None
    bundled = os.path.join(ROOT, 'assets', 'fonts')
    if os.path.isdir(bundled):
        files = sorted(x for x in os.listdir(bundled) if x.lower().endswith(('.ttf', '.otf', '.ttc')))
        if files:
            f = pygame.font.Font(os.path.join(bundled, files[0]), size)
    if f is None:
        path = pygame.font.match_font(_FONT_CANDIDATES, bold=bold)
        if path:
            f = pygame.font.Font(path, size)
    if f is None and os.path.exists(_LINUX_FONT):
        f = pygame.font.Font(_LINUX_FONT, size)
    if f is None:
        f = pygame.font.Font(None, size)
    f.set_bold(bold and not f.get_bold())
    _font_cache[key] = f
    return f
