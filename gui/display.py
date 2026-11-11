"""창 크기와 Windows 화면 배율(DPI).

Windows 배율이 125%처럼 100%가 아니면, DPI 인식을 켜지 않은 프로그램의 창을 Windows가 강제로 늘린다
(1280×720 → 1600×900, 1.25배). 정수배가 아니라 도트 글씨가 뿌옇고 획 굵기가 들쭉날쭉해진다.
그래서 pygame 창을 만들기 전에 DPI 인식을 켜고, 창은 640×360의 정수배 중 화면 작업 영역에 들어가는
가장 큰 크기로 정한다. (640 → 창 확대는 App이 pygame.transform.scale로 정수배만)
"""
import sys

from . import theme as T

MAX_SCALE = 3


def enable_dpi_awareness():
    """Windows가 창을 늘리지 않게 한다. 성공하면 방법 이름, 아니면 None. 다른 OS는 아무것도 안 함."""
    if sys.platform != 'win32':
        return None
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)        # 시스템 DPI 인식 (Windows 8.1+)
        return 'SetProcessDpiAwareness(1)'
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()          # Windows Vista+
            return 'SetProcessDPIAware'
        except Exception:
            return None


def screen_info():
    """(배율 %, 작업 영역 (w, h), 창 테두리 (가로, 세로)) — 실제 픽셀. 모르면 None."""
    if sys.platform != 'win32':
        return None
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    hdc = user32.GetDC(0)
    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)          # LOGPIXELSX
    user32.ReleaseDC(0, hdc)
    work = wintypes.RECT()
    user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0)   # SPI_GETWORKAREA (작업 표시줄 제외)
    style = 0x00C00000 | 0x00080000 | 0x00020000                     # 제목 표시줄 + 닫기 + 최소화
    frame = wintypes.RECT(0, 0, 100, 100)
    user32.AdjustWindowRectEx(ctypes.byref(frame), style, False, 0)
    return (round(dpi * 100 / 96), (work.right - work.left, work.bottom - work.top),
            (frame.right - frame.left - 100, frame.bottom - frame.top - 100))


def pick_scale(info=None):
    """작업 영역에 테두리까지 들어가는 가장 큰 정수배 (1~MAX_SCALE). 정보가 없으면 2."""
    if not info:
        return 2
    _, (ww, wh), (fw, fh) = info
    best = 1
    for n in range(1, MAX_SCALE + 1):
        if T.WIDTH * n + fw <= ww and T.HEIGHT * n + fh <= wh:
            best = n
    return best


def setup_window_scale(verbose=True):
    """pygame 창을 만들기 전에 부른다: DPI 인식 → 배율 결정 → theme.SCALE/WINDOW 설정."""
    how = enable_dpi_awareness()
    info = screen_info()
    T.set_scale(pick_scale(info))
    if verbose:
        if info:
            pct, (ww, wh), _ = info
            print(f'[화면] Windows 배율 {pct}% · 작업 영역 {ww}×{wh} · DPI 인식 {how or "실패"} '
                  f'→ 창 {T.WINDOW[0]}×{T.WINDOW[1]} ({T.SCALE}배)')
        else:
            print(f'[화면] 창 {T.WINDOW[0]}×{T.WINDOW[1]} ({T.SCALE}배)')
    return T.SCALE
