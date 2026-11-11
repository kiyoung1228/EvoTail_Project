"""적 몬스터 표시 정보 (data/enemies.json). 게임 규칙은 없다.

- 스테이지 지도처럼 백엔드가 아직 적을 주지 않는 곳(스테이지별 보스 얼굴)에서만 이 파일을 읽는다
- 전투·미리보기의 적은 백엔드가 주는 name / sprite / boss를 그대로 쓴다 (enemy_look)
  기영님이 백엔드에서 적을 enemies.json 기준으로 바꿔 주기 전에는 sprite가 동물 그림이고 boss가 없다 →
  보스 여부는 SpriteCache.is_boss가 그림 크기(원본 46)로 판단
"""
import json
import os

from . import theme as T

_data = None


def data():
    global _data
    if _data is None:
        path = os.path.join(T.ROOT, 'data', 'enemies.json')
        try:
            with open(path, encoding='utf-8') as f:
                _data = json.load(f)
        except OSError:
            _data = {'minions': [], 'bosses': []}
    return _data


def boss_for_stage(stage_id):
    """스테이지의 보스 {'id','name','stage','role','element','boss','sprite'} 또는 None."""
    return next((b for b in data().get('bosses', []) if b.get('stage') == stage_id), None)


def enemy_look(sprites, enemy):
    """백엔드 적 dict → (이름, 그림 경로, 보스 여부). 보스 값이 없으면 그림 크기로."""
    sprite = enemy.get('sprite')
    return enemy.get('name', ''), sprite, sprites.is_boss(sprite, enemy.get('boss'))
