"""세이브·오류 기록 위치.

- 소스로 실행(python run_gui.py): 저장소의 saves/ (예전과 같음, 지금 폴더(cwd)와 상관없이 저장소 기준)
- 실행 파일(EvoTail.exe, sys.frozen): EvoTail.exe가 있는 폴더의 saves/
  그 폴더에 쓸 수 없으면(예: Program Files) %LOCALAPPDATA%\\EvoTail\\saves
saves 폴더가 없으면 만든다. 그림·글꼴·데이터 위치는 theme.ROOT(exe면 _internal 안)라 여기와 상관없다.
"""
import os
import sys

from . import theme as T

_dir = None


def frozen():
    return bool(getattr(sys, 'frozen', False))


def _writable(folder):
    """폴더를 만들고 실제로 파일을 써 본다 (권한·읽기 전용 드라이브 확인)."""
    try:
        os.makedirs(folder, exist_ok=True)
        probe = os.path.join(folder, '.write_test')
        with open(probe, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(probe)
        return True
    except OSError:
        return False


def save_dir():
    global _dir
    if _dir is None:
        if frozen():
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates = [os.path.join(exe_dir, 'saves')]
            local = os.environ.get('LOCALAPPDATA') or os.path.join(os.path.expanduser('~'), 'AppData', 'Local')
            candidates.append(os.path.join(local, 'EvoTail', 'saves'))
        else:
            candidates = [os.path.join(T.ROOT, 'saves')]
        _dir = next((c for c in candidates if _writable(c)), candidates[-1])
    return _dir


def save_path():
    return os.path.join(save_dir(), 'game.db')


def log_path():
    return os.path.join(save_dir(), 'error.log')
