"""EvoTail 게임 실행 (Pygame 화면). python run_gui.py  (실행 파일은 build_exe.bat → dist/EvoTail/EvoTail.exe)

F5: 시간 빠르게(5배) 켜기/끄기
F12: 시연 모드(60배) 켜기/끄기 - 영상 촬영용
세이브: 소스 실행은 저장소 saves/game.db, exe는 EvoTail.exe 옆 saves/game.db (gui/paths.py)
잡히지 않은 오류: saves/error.log (gui/crash.py)
"""
import sys

from gui import paths, crash
from gui.app import App
from gui.scenes.map_scene import MapScene
from gui.scenes.animals_scene import AnimalsScene
from gui.scenes.placeholder import PlaceholderScene
from gui.scenes.battle_stage import StagePickScene, TeamPrepScene
from gui.scenes.battle_fight import BattleScene, BattleResultScene
from gui.scenes.home_kitchen import KitchenScene
from gui.scenes.shop import ShopScene
from gui.scenes.hospital import HospitalScene
from gui.scenes.farm import FarmScene
from gui.scenes.hunting import HuntScene
from gui.scenes.bag import BagScene
from gui.scenes.pokedex import PokedexScene


def main(save_path=None):
    app = App(save_path or paths.save_path())
    app.register('map', MapScene(app))
    app.register('animals', AnimalsScene(app))
    # 아직 만들지 않은 화면 (지도 건물 + 오른쪽 메뉴). 설정은 지도 위 창 (gui/scenes/settings.py)
    app.register('home', KitchenScene(app))      # 집: 주방 (레시피 북·요리 미니게임·음식 주기)
    app.register('shop', ShopScene(app))         # 상점: 탭 6개·구매·판매·알 부화
    app.register('hospital', HospitalScene(app)) # 병원: 아픈 동물·회복 포션
    app.register('farm', FarmScene(app))         # 밭: 텃밭 6칸·씨앗 심기·수확·밭 넓히기
    app.register('hunting', HuntScene(app))      # 사냥터: 4곳·보내기·불러오기·보상 받기
    app.register('bag', BagScene(app))            # 가방: 배낭 5×4 칸·탭 6개·쪽지
    app.register('pokedex', PokedexScene(app))    # 도감(D안): 펼친 책 + 일반·특급 태그
    for name, title in (('my_room', '마이룸'),):
        app.register(name, PlaceholderScene(app, title))
    # 전투장: 스테이지 고르기 → 출전 준비 → 전투 → 결과
    app.register('battle', StagePickScene(app))
    app.register('battle_prep', TeamPrepScene(app))
    app.register('battle_fight', BattleScene(app))
    app.register('battle_result', BattleResultScene(app))
    app.go('map')
    app.run()


def run():
    """실행 파일·python run_gui.py 입구. 오류는 error.log에 남기고, 화면 알림이 못 떴으면 알림 상자."""
    for stream in (sys.stdout, sys.stderr):      # 한글을 못 찍는 콘솔(cp1252 등)에서도 안내 출력 때문에 멈추지 않게
        if stream is not None and hasattr(stream, 'reconfigure'):
            stream.reconfigure(errors='replace')
    crash.install()
    try:
        main()
    except Exception as exc:
        path = crash.log(exc)
        if not getattr(exc, '_evotail_shown', False):
            crash.message_box(path)
        if paths.frozen():          # 창 모드 exe: PyInstaller 기본 오류 창을 또 띄우지 않게
            sys.exit(1)
        raise


if __name__ == '__main__':
    run()
