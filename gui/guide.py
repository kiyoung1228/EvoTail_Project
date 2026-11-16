"""안내원 테크모 (학사모를 쓴 회색 까마귀, 오리지널 도트)와 대화 상자 · 대사 표.

- 그림 assets/guide/techmo_<표정>.png: 원본 32×32, 파일 4배(128). TechmoArt.get(kind, n) = 원본 × n (정수배만)
- 표정 순서는 assets/guide/techmo.json (flap_cycle = 날개 파닥 한 바퀴)
- Dialog: 아래(또는 위) 판 + 왼쪽 테크모 얼굴(말할 때 talk ↔ idle) + 이름 칩 + 2줄 + "▼ 클릭".
  글자는 한 글자씩, 클릭하면 바로 다 보이고 한 번 더 클릭하면 다음. 글씨 줄은 넘침 점검 기록(tag guide)
- 대사는 이 파일의 표 한 곳 (WELCOME, ROLE_LINES, TUTORIAL, DONE). 숫자(훈련 동시 수 등)는 백엔드 값으로 채움
"""
import json
import math
import os
import pygame

from . import theme as T
from .widgets import text, text_in, panel, card, chip, record, fit_width

GUIDE_DIR = os.path.join(T.ROOT, 'assets', 'guide')
with open(os.path.join(GUIDE_DIR, 'techmo.json'), encoding='utf-8') as _f:
    TECHMO = json.load(_f)
NAME = '테크모'

# ---------- 대사 표 (한 곳) ----------
WELCOME = ('어서 와! 나는 이 섬의 안내원 테크모야.', '먼저 같이 지낼 동료 3마리를 골라 볼까?')
PICK_HINT = '일반 동물 중 마음에 드는 3마리를 골라!'
ROLE_LINES = {      # 맞이: 첫 줄 앞에 "○○와 함께!"
    'dealer': ('적 전체를 한 번에 공격해.', '공격력이 높을수록 아프게 때린다!'),
    'tank': ('튼튼해서 오래 버텨.', '아군 하나를 절대방어로 지켜 줄 수도 있어.'),
    'healer': ('다친 아군을 회복시켜.', '힐러가 있으면 오래 싸울 수 있지!'),
}
TUTORIAL = (        # (대사 2줄). {n} = 스냅샷 training_max_concurrent
    ('배고픈 친구에겐 간식을 주자.', '오른쪽 메뉴의 가방을 눌러 봐!'),
    ('내 동물에서는 능력치를 훈련할 수 있어.', '네 능력치가 모두 MAX가 되면 진화!'),
    ('훈련할 능력치를 고르고 난이도를 눌러.', '훈련은 동시에 {n}마리까지 할 수 있어.'),
    ('준비가 됐으면 전투장으로!', '첫 상대는 뉴비 스테이지. 져도 걱정 마.'),
    ('이제 자유롭게 섬을 돌아다녀 봐!', '궁금하면 설정의 도움말을 열어 줘. 그럼 안녕~'),
)

# ---------- 대화 상자 자리 (목업 docs/mockups/title, tools/tut_mock.py dialog()) ----------
BOX_BOTTOM, BOX_TOP = 282, 58
BOX = (8, 624, 74)                 # x, 폭, 높이
SKIP_RECT = pygame.Rect(556, 32, 76, 20)
TYPE_SPEED = 40                    # 한 글자씩 (글자/초)
TALK_SWAP = 0.15                   # talk ↔ idle 바꾸는 간격 (techmo.json talk)


class TechmoArt:
    """테크모 그림 캐시. get(kind, n) = 원본 32 × n (파일 128 → ¼ → ×n, 정수배만)."""

    def __init__(self):
        self._cache = {}

    def get(self, kind, n=2):
        key = (kind, n)
        if key not in self._cache:
            path = os.path.join(GUIDE_DIR, f'techmo_{kind}.png')
            if not os.path.exists(path):
                path = os.path.join(GUIDE_DIR, 'techmo_idle.png')
            img = pygame.image.load(path).convert_alpha()
            base = pygame.transform.scale(img, (img.get_width() // 4, img.get_height() // 4))
            self._cache[key] = base if n == 1 else pygame.transform.scale(base, (base.get_width() * n,
                                                                                 base.get_height() * n))
        return self._cache[key]

    def flap(self, t, fps=10, talk=False):
        """날개 파닥 한 바퀴(flap_cycle) 중 지금 표정. talk면 입 벌린 그림(_talk)."""
        cycle = TECHMO['flap_cycle']
        kind = cycle[int(t * fps) % len(cycle)]
        return kind + ('_talk' if talk and kind != 'idle' else '')

    @staticmethod
    def idle_kind(t):
        """가만히: 가끔 깜빡 (약 3초마다 0.1초)."""
        return 'blink' if (t % 3.2) < 0.1 else 'idle'


ART = None


def art():
    global ART
    if ART is None:
        ART = TechmoArt()
    return ART


def sparkle(surface, x, y, color=(255, 250, 200)):
    pygame.draw.line(surface, color, (x - 3, y), (x + 3, y))
    pygame.draw.line(surface, color, (x, y - 3), (x, y + 3))


def progress_width(label, total):
    return 8 + (fit_width(label, 'body') - 4) + 8 + total * 9 + 6


def progress(surface, label, n, total, topleft=(8, 32)):
    """진행 칸: 글씨 + 점 (글씨 폭에 맞춤). 예) "처음 안내 ■■□□□". 기본 자리 = 왼쪽 위 (맞이 화면),
    튜토리얼은 대화 상자 안 오른쪽 위 (TutorialOverlay.layout)."""
    x0, y0 = topleft
    tw = fit_width(label, 'body') - 4                      # 글자 폭
    box = pygame.Rect(x0, y0, progress_width(label, total), 22)
    card(surface, box)
    text_in(surface, label, (x0 + 6, y0 + 1, tw + 4, 20), 'body', align='left', tag='guide')   # 글자는 x0 + 8부터
    for i in range(total):
        x = x0 + 8 + tw + 8 + i * 9
        r = pygame.Rect(x, y0 + 8, 6, 6)
        pygame.draw.rect(surface, (250, 196, 60) if i < n else (150, 128, 104), r)
        pygame.draw.rect(surface, T.INK, r, 1)
    return box


class Dialog:
    """테크모 대화 상자. say(줄들) → 한 글자씩. click() = 다 보이게 / 다 보였으면 True(다음)."""

    def __init__(self):
        self.lines = ('', '')
        self.t = 0.0
        self.shown = 0

    def say(self, lines):
        self.lines = tuple(lines)[:2]
        self.t = 0.0
        self.shown = 0

    @property
    def total(self):
        return sum(len(s) for s in self.lines)

    @property
    def done(self):
        return self.shown >= self.total

    def update(self, dt):
        self.t += dt
        if not self.done:
            self.shown = min(self.total, int(self.t * TYPE_SPEED))

    def click(self):
        """글자가 나오는 중이면 다 보이게 하고 False, 다 보였으면 True (다음으로)."""
        if not self.done:
            self.shown = self.total
            return False
        return True

    def rect(self, top=False):
        x, w, h = BOX
        return pygame.Rect(x, BOX_TOP if top else BOX_BOTTOM, w, h)

    def draw(self, surface, top=False, name=NAME):
        r = self.rect(top)
        y0 = r.y
        panel(surface, r)
        face_box = pygame.Rect(16, y0 + 8, 61, 59)
        pygame.draw.rect(surface, (206, 226, 240), face_box)
        talking = not self.done and int(self.t / TALK_SWAP) % 2 == 0
        kind = 'talk' if talking else TechmoArt.idle_kind(self.t)
        face = art().get(kind, 2)
        surface.blit(face, (14, y0 + 12), pygame.Rect(0, 0, face.get_width(), 52))
        pygame.draw.rect(surface, T.WOOD[2], face_box, 1)
        chip(surface, (84, y0 + 8), name, 'brown')
        left = self.shown
        right = r.right - 12
        for i, line in enumerate(self.lines):
            part = line[:max(0, left)]
            left -= len(line)
            g = text(surface, part, (86, y0 + 36 + i * 18), 'title', T.TEXT, 'midleft')
            if part:
                record(part, g, pygame.Rect(84, g.y - 2, right - 84, g.h + 4), 'guide')
        if self.done and int(self.t * 2) % 2 == 0:
            text(surface, '▼ 클릭', (606, y0 + 62), 'small', T.TEXT_SOFT, 'center')
        return r


def team_counts(roles):
    """역할 개수만 셈 (막지 않음). roles = 고른 동물들의 역할 목록 → [(역할, 개수)] 딜러·탱커·힐러 순."""
    return [(r, roles.count(r)) for r in ('dealer', 'tank', 'healer') if roles.count(r)]


def bob(t, amp=2, period=0.6):
    return round(amp * math.sin(t * math.pi * 2 / period))
