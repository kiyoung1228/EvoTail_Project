"""설정 창 (목업 docs/mockups/settings.png, 키트 docs/UI_KIT.md). 지도 위에 뜨는 창.

- 시간 속도 보통 / 빠르게(5배), 시연 모드(60배) 토글: F5·F12와 같은 App.toggle_speed
- 저장하기(save_game), 불러오기(load_game, 확인 창 먼저), 도움말, 게임 종료
- 마지막 저장 시각. 백엔드는 모든 변경을 바로 SQLite에 저장하므로(자동 저장) "자동 저장 켜짐"도 표시
- 배경음·효과음은 팀 결정 전이라 없음
- ESC나 창 밖 클릭으로 닫기 (App.Overlay)
"""
import os
import time
import pygame

from .. import theme as T
from ..app import Overlay
from ..widgets import text, text_width, panel, card, chip, nine, Button, mouse_pos


def clock_text(ts):
    """실제 시각 → '오후 2:18'."""
    t = time.localtime(ts)
    h = t.tm_hour % 12 or 12
    return f"{'오전' if t.tm_hour < 12 else '오후'} {h}:{t.tm_min:02d}"


def _title(surface, rect, label, icon_img=None):
    """창 제목 줄: (아이콘) 큰 글씨 + 아래 구분선."""
    x = rect.x + 12
    if icon_img:
        surface.blit(icon_img, (x, rect.y + 8))
        x += 28
    text(surface, label, (x, rect.y + 20), 'big', T.TEXT, 'midleft')
    pygame.draw.line(surface, T.WOOD[3], (rect.x + 9, rect.y + 34), (rect.right - 10, rect.y + 34))


class SettingsOverlay(Overlay):
    def __init__(self, app):
        super().__init__(app, (196, 66, 248, 218))
        P = self.rect
        path = os.path.join(T.ROOT, 'assets', 'ui', 'icon_settings.png')
        self.icon = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (24, 24)) \
            if os.path.exists(path) else None
        self.close_btn = Button((P.right - 32, P.y + 10, 20, 19), 'X', self.close, 'red')
        fast_w = text_width(f'빠르게 ({T.SPEED_FAST}배)') + 14
        self.speed_normal = pygame.Rect(P.x + 92, P.y + 46, P.w - 12 - 92 - 6 - fast_w, 20)
        self.speed_fast = pygame.Rect(self.speed_normal.right + 6, P.y + 46, fast_w, 20)
        self.demo_toggle = pygame.Rect(P.x + 92, P.y + 78, 26, 14)
        self.demo_row = pygame.Rect(P.x + 12, P.y + 74, P.w - 24, 22)
        bw = (P.w - 40) // 2
        self.buttons = [
            Button((P.x + 16, P.y + 116, bw, 24), '저장하기', self.save, 'blue'),
            Button((P.x + 24 + bw, P.y + 116, bw, 24), '불러오기', self.ask_load, 'purple'),
            Button((P.x + 16, P.y + 148, bw, 24), '도움말', lambda: app.open_overlay(HelpOverlay(app)), 'orange'),
            Button((P.x + 24 + bw, P.y + 148, bw, 24), '게임 종료', self.quit, 'red'),
        ]

    # ---------- 동작 ----------
    def _rate(self):
        return self.app.state.get('clock', {}).get('rate', 1) or 1

    def set_normal(self):
        rate = self._rate()
        if rate != 1:
            self.app.toggle_speed(rate)          # 지금 배속과 같은 값 → 보통으로

    def set_fast(self):
        if self._rate() != T.SPEED_FAST:
            self.app.toggle_speed(T.SPEED_FAST)

    def toggle_demo(self):
        self.app.toggle_speed(T.SPEED_DEMO)      # F12와 같은 함수

    def save(self):
        if self.app.act('save_game', '저장했어요', icon='home') is not None:
            self.app.last_saved = time.time()

    def ask_load(self):
        self.app.open_overlay(ConfirmOverlay(
            self.app, '불러올까요?', '저장 안 한 내용은 사라져요', '불러오기', 'purple', self.load))

    def load(self):
        if self.app.call('load_game') is not None:
            self.app.refresh()
            events = self.app.call('recent_events') or []
            self.app.last_seq = max([e.get('seq', 0) for e in events], default=0)
            self.app.toast('저장된 게임을 불러왔어요', 'ok', 'home')

    def quit(self):
        """게임 종료. App.run이 끝나면서 save_game을 한 번 더 부른다 (자동 저장)."""
        self.app.running = False

    # ---------- 입력 ----------
    def handle(self, event):
        if self.close_btn.handle(event):
            return True
        for b in self.buttons:
            if b.handle(event):
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.speed_normal.collidepoint(event.pos):
                self.set_normal()
            elif self.speed_fast.collidepoint(event.pos):
                self.set_fast()
            elif self.demo_row.collidepoint(event.pos):
                self.toggle_demo()
            else:
                return False
            return True
        return False

    # ---------- 그리기 ----------
    def _option(self, surface, rect, label, selected):
        """선택지 버튼: 고른 것 = 초록 키트 버튼, 아닌 것 = card 칸 (마우스 올리면 강조)."""
        if selected:
            nine(surface, 'button_green_normal', rect)
            text(surface, label, (rect.centerx, rect.centery - 1), 'title', T.WHITE, 'center',
                 shadow=T.shade('green', 0))
        else:
            card(surface, rect, rect.collidepoint(mouse_pos()))
            text(surface, label, rect.center, 'body', T.TEXT, 'center')

    def _toggle(self, surface, rect, on):
        """켜기/끄기 스위치: 게이지 틀 + 켜지면 초록 채움, 손잡이는 card 칸."""
        nine(surface, 'gauge_frame', rect)
        inner = rect.inflate(-4, -4)
        if on:
            pygame.draw.rect(surface, T.shade('green', 2), inner)
            pygame.draw.line(surface, T.shade('green', 3), inner.topleft, (inner.right - 1, inner.top))
        knob = pygame.Rect(0, 0, 12, 12)
        if on:
            knob.midright = (rect.right, rect.centery)
        else:
            knob.midleft = (rect.x, rect.centery)
        card(surface, knob)

    def draw(self, surface):
        P = self.rect
        panel(surface, P)
        _title(surface, P, '설정', self.icon)
        self.close_btn.draw(surface)
        rate = self._rate()
        demo = rate >= T.SPEED_DEMO
        # 시간 속도
        text(surface, '시간 속도', (P.x + 16, self.speed_normal.centery), 'title', T.TEXT, 'midleft')
        self._option(surface, self.speed_normal, '보통', rate == 1)
        self._option(surface, self.speed_fast, f'빠르게 ({T.SPEED_FAST}배)', rate == T.SPEED_FAST)
        # 시연 모드
        text(surface, '시연 모드', (P.x + 16, self.demo_toggle.centery), 'title', T.TEXT, 'midleft')
        self._toggle(surface, self.demo_toggle, demo)
        text(surface, f'{T.SPEED_DEMO}배 · 영상 촬영용 (F12)', (self.demo_toggle.right + 6, self.demo_toggle.centery),
             'small', T.shade('red', 1) if demo else T.TEXT_SOFT, 'midleft')
        pygame.draw.line(surface, T.WOOD[3], (P.x + 12, P.y + 106), (P.right - 13, P.y + 106))
        for b in self.buttons:
            b.draw(surface)
        # 마지막 저장
        if self.app.last_saved:
            saved = f"마지막 저장: {clock_text(self.app.last_saved)} (자동 저장 켜짐)"
        else:
            saved = '자동 저장 켜짐 · 바뀐 내용은 바로 저장돼요'
        text(surface, saved, (P.centerx, P.bottom - 26), 'small', T.TEXT_SOFT, 'center')
        text(surface, 'ESC · 창 밖을 누르면 닫혀요', (P.centerx, P.bottom - 14), 'small', T.TEXT_SOFT, 'center')


class ConfirmOverlay(Overlay):
    """확인 창: 제목 + 설명 + [확인][취소]. 밖을 누르거나 ESC = 취소."""

    def __init__(self, app, title, message, ok_label, ok_color, on_ok):
        w = max(200, text_width(message) + 40)
        super().__init__(app, ((T.WIDTH - w) // 2, 132, w, 104))
        R = self.rect
        self.title, self.message = title, message
        bw = (R.w - 40) // 2

        def ok():
            self.close()
            on_ok()
        self.buttons = [Button((R.x + 16, R.bottom - 36, bw, 24), ok_label, ok, ok_color),
                        Button((R.x + 24 + bw, R.bottom - 36, bw, 24), '취소', self.close, 'brown')]

    def handle(self, event):
        return any(b.handle(event) for b in self.buttons)

    def draw(self, surface):
        R = self.rect
        panel(surface, R)
        _title(surface, R, self.title)
        text(surface, self.message, (R.centerx, R.y + 50), 'body', T.TEXT, 'center')
        for b in self.buttons:
            b.draw(surface)


class HelpOverlay(Overlay):
    """도움말: 조작법."""
    LINES = [
        ('F5', 'brown', '시간 빠르게(5배) 켜기 / 끄기'),
        ('F12', 'red', '시연 모드(60배) 켜기 / 끄기 · 영상용'),
        ('클릭', 'green', '건물 · 오른쪽 메뉴 · 마당 동물 누르기'),
        ('휠', 'blue', '내 동물 목록 넘기기'),
        ('ESC', 'gray', '열린 창 닫기'),
    ]

    def __init__(self, app):
        w = 60 + max(text_width(desc) for _, _, desc in self.LINES) + 16
        super().__init__(app, ((T.WIDTH - w) // 2, 82, w, 190))
        R = self.rect
        self.back = Button((R.centerx - 40, R.bottom - 34, 80, 22), '닫기', self.close, 'brown')

    def handle(self, event):
        return self.back.handle(event)

    def draw(self, surface):
        R = self.rect
        panel(surface, R)
        _title(surface, R, '도움말')
        for i, (key, color, desc) in enumerate(self.LINES):
            y = R.y + 48 + i * 19
            chip(surface, (R.x + 46, y), key, color, anchor='midright')
            text(surface, desc, (R.x + 54, y), 'body', T.TEXT, 'midleft')
        self.back.draw(surface)
