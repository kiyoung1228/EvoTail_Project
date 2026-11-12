"""잡히지 않은 오류 기록 (실행 파일은 콘솔이 없어서 화면·파일로 알린다).

- log(exc): saves/error.log에 시각 + traceback을 덧붙인다 (한 오류는 한 번만)
- notice(app): 게임 창이 떠 있으면 키트 창 "오류 발생 · saves/error.log 확인"을 띄우고, 키·클릭·창 닫기로 끝
- message_box(): 창이 뜨기 전 오류면 Windows 알림 상자 (실행 파일일 때만)
- install(): 백그라운드 스레드(GameWorker)의 오류도 기록
"""
import datetime
import sys
import threading
import traceback

from . import paths


def log(exc):
    """error.log에 남긴다. 이미 남긴 오류면 건너뛴다. 남긴 파일 경로(실패하면 None)."""
    if getattr(exc, '_evotail_logged', False):
        return paths.log_path()
    try:
        exc._evotail_logged = True
    except Exception:
        pass
    try:
        stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        body = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        with open(paths.log_path(), 'a', encoding='utf-8') as f:
            f.write(f"===== {stamp} =====\n{body}\n")
        return paths.log_path()
    except Exception:
        return None


def install():
    """스레드 안 오류도 error.log로 (기본 출력은 그대로)."""
    default = threading.excepthook

    def hook(args):
        if args.exc_value is not None:
            log(args.exc_value)
        default(args)
    threading.excepthook = hook


def notice(app):
    """게임 창 위에 짧은 오류 창. 아무 키·클릭·창 닫기로 끝난다. 그리기도 실패하면 조용히 넘어감."""
    try:
        import pygame
        from . import theme as T
        from . import widgets as W
        if not pygame.display.get_init() or pygame.display.get_surface() is None:
            return False
        screen = app.screen
        dim = pygame.Surface((T.WIDTH, T.HEIGHT), pygame.SRCALPHA)
        dim.fill((24, 16, 24, 170))
        screen.blit(dim, (0, 0))
        title, sub = '오류 발생 · saves/error.log 확인', '아무 키나 누르면 닫힌다'
        w = max(W.fit_width(title, 'title'), W.fit_width(sub, 'small')) + 40
        box = pygame.Rect(0, 0, w, 64)
        box.center = (T.WIDTH // 2, T.HEIGHT // 2)
        W.panel(screen, box)
        W.text_in(screen, title, (box.x, box.y + 14, box.w, 18), 'title', (190, 40, 50))
        W.text_in(screen, sub, (box.x, box.y + 36, box.w, 14), 'small', T.TEXT_SOFT)
        pygame.transform.scale(screen, app.window.get_size(), app.window)
        pygame.display.flip()
        clock = pygame.time.Clock()
        waited = 0
        while waited < 120000:                 # 2분 뒤에는 그냥 닫힘
            for e in pygame.event.get():
                if e.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    return True
            waited += clock.tick(30)
        return True
    except Exception:
        return False


def message_box(path):
    """창이 없을 때 (실행 파일만): Windows 알림 상자."""
    if not paths.frozen() or sys.platform != 'win32':
        return
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, f"오류 발생 · saves/error.log 확인\n\n{path or ''}", 'EvoTail', 0x10)
    except Exception:
        pass
