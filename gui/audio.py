"""배경음(BGM)·효과음악. 곡은 전부 이 저장소에서 새로 만든 오리지널 (tools/bgm/songs.py → assets/bgm/*.ogg).

- 배경음: pygame.mixer.music, 반복(-1). 곡이 바뀌면 0.6초 페이드(0.3초 작아짐 → 새 곡 0.3초 커짐), 같은 곡이면 이어서
- 효과음악(jingle_*): pygame.mixer.Sound 한 번. 나오는 동안 배경음은 30%로 줄였다가 끝나면 원래대로
- 오디오 장치가 없거나 파일이 없으면 조용히 무음 (게임은 그대로)
- 설정(배경음 크기·효과음악 켬/끔)은 세이브 폴더의 settings.json (게임 세이브 DB·roc와 별개)

장면마다 곡은 Scene.music 하나로 정한다 (곡 이름 = 아래 TRACKS 키):
  'map'  = 지도 (낮 map_day / 밤 map_night, 지도에 있는 동안 바뀌면 페이드)
  None   = 지금 곡 그대로 이어서 (내 동물·도감·가방·마이룸, 지도 위 설정 창)
"""
import json
import os
import pygame

from . import theme as T

BGM_DIR = os.path.join(T.ROOT, 'assets', 'bgm')

# 곡 이름표 (여기 한 곳). 키 = Scene.music 값 / 효과음악 이름, 값 = assets/bgm 파일
TRACKS = {
    'map_day': 'map_day.ogg',        # 지도 낮
    'map_night': 'map_night.ogg',    # 지도 밤
    'home': 'home.ogg',              # 집 · 주방
    'shop': 'shop.ogg',              # 상점 · 부화
    'hospital': 'hospital.ogg',      # 병원
    'farm': 'farm.ogg',              # 밭
    'hunt': 'hunt.ogg',              # 사냥터
    'arena': 'arena.ogg',            # 스테이지 고르기 · 출전 준비 · 결과
    'battle': 'battle.ogg',          # 전투
}
JINGLES = {
    'jingle_win': 'jingle_win.ogg',      # 전투 승리
    'jingle_lose': 'jingle_lose.ogg',    # 전투 패배 · 도망
    'jingle_hatch': 'jingle_hatch.ogg',  # 부화 성공 (결과 창)
}

# 배경음 크기 단계 (설정 창 버튼 순서)
LEVELS = (('off', '끔', 0.0), ('low', '작게', 0.3), ('mid', '보통', 0.6), ('high', '크게', 1.0))
DEFAULTS = {'bgm': 'mid', 'jingle': True}
FADE = 0.3              # 작아지는 데 0.3초 + 커지는 데 0.3초 = 0.6초
DUCK = 0.3              # 효과음악 동안 배경음 비율
JINGLE_VOLUME = 0.8


def map_track(night):
    return 'map_night' if night else 'map_day'


class Audio:
    def __init__(self, settings_path=None):
        self.settings_path = settings_path
        self.settings = dict(DEFAULTS)
        self._load_settings()
        self.ok = False
        try:
            self.ok = pygame.mixer.get_init() is not None
        except pygame.error:
            self.ok = False
        self.current = None      # 지금 나오는(또는 들어오는) 곡
        self.target = None       # 나와야 하는 곡
        self.fade = 0.0          # 0~1 (페이드 크기)
        self.channel = None      # 효과음악 채널
        self._sounds = {}

    # ---------- 설정 ----------
    def _load_settings(self):
        if not self.settings_path:
            return
        try:
            with open(self.settings_path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        if data.get('bgm') in {k for k, _, _ in LEVELS}:
            self.settings['bgm'] = data['bgm']
        if isinstance(data.get('jingle'), bool):
            self.settings['jingle'] = data['jingle']

    def _save_settings(self):
        if not self.settings_path:
            return
        try:
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=1)
        except OSError:
            pass

    def set_bgm_level(self, key):
        self.settings['bgm'] = key
        self._save_settings()
        self._apply_volume()

    def set_jingle(self, on):
        self.settings['jingle'] = bool(on)
        self._save_settings()
        if not on and self.channel is not None:
            try:
                self.channel.stop()
            except pygame.error:
                pass

    def bgm_volume(self):
        return next(v for k, _, v in LEVELS if k == self.settings['bgm'])

    # ---------- 배경음 ----------
    def want(self, track):
        """이 곡이 나와야 함 (같은 곡이면 아무것도 안 함). track None = 지금 곡 그대로."""
        if track is not None and track in TRACKS:
            self.target = track

    def _start(self, track):
        self.current = track
        if not self.ok:
            return
        path = os.path.join(BGM_DIR, TRACKS[track])
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0)
            pygame.mixer.music.play(-1)
        except (pygame.error, FileNotFoundError):
            pass                 # 파일이 없거나 못 읽으면 무음

    def _ducking(self):
        try:
            return self.channel is not None and self.channel.get_busy()
        except pygame.error:
            return False

    def _apply_volume(self):
        if not self.ok:
            return
        vol = self.bgm_volume() * self.fade * (DUCK if self._ducking() else 1.0)
        try:
            pygame.mixer.music.set_volume(vol)
        except pygame.error:
            pass

    def update(self, dt):
        """매 프레임 (App.step). 페이드·효과음악 동안 줄이기."""
        step = dt / FADE
        if self.target != self.current:
            if self.current is None or self.fade <= 0:
                self._start(self.target)
                self.fade = 0.0
            else:
                self.fade = max(0.0, self.fade - step)
        elif self.current is not None:
            self.fade = min(1.0, self.fade + step)
        self._apply_volume()

    # ---------- 효과음악 ----------
    def jingle(self, name):
        if not self.ok or not self.settings['jingle'] or name not in JINGLES:
            return
        try:
            if name not in self._sounds:
                self._sounds[name] = pygame.mixer.Sound(os.path.join(BGM_DIR, JINGLES[name]))
            snd = self._sounds[name]
            snd.set_volume(JINGLE_VOLUME)
            self.channel = snd.play()
        except (pygame.error, FileNotFoundError):
            self.channel = None
        self._apply_volume()

    def stop(self):
        if not self.ok:
            return
        try:
            pygame.mixer.music.stop()
            pygame.mixer.stop()
        except pygame.error:
            pass
