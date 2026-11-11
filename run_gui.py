"""EvoTail 게임 실행 (Pygame 화면). 프로젝트 폴더에서: python run_gui.py

F5: 시간 빠르게(5배) 켜기/끄기
F12: 시연 모드(60배) 켜기/끄기 - 영상 촬영용
"""
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


def main(save_path='saves/game.db'):
    app = App(save_path)
    app.register('map', MapScene(app))
    app.register('animals', AnimalsScene(app))
    # 아직 만들지 않은 화면 (지도 건물 + 오른쪽 메뉴). 설정은 지도 위 창 (gui/scenes/settings.py)
    app.register('home', KitchenScene(app))      # 집: 주방 (레시피 북·요리 미니게임·음식 주기)
    app.register('shop', ShopScene(app))         # 상점: 탭 6개·구매·판매·알 부화
    app.register('hospital', HospitalScene(app)) # 병원: 아픈 동물·회복 포션
    app.register('farm', FarmScene(app))         # 밭: 텃밭 6칸·씨앗 심기·수확·밭 넓히기
    for name, title in (('hunting', '사냥터'),
                        ('pokedex', '도감'), ('bag', '가방'), ('my_room', '마이룸')):
        app.register(name, PlaceholderScene(app, title))
    # 전투장: 스테이지 고르기 → 출전 준비 → 전투 → 결과
    app.register('battle', StagePickScene(app))
    app.register('battle_prep', TeamPrepScene(app))
    app.register('battle_fight', BattleScene(app))
    app.register('battle_result', BattleResultScene(app))
    app.go('map')
    app.run()


if __name__ == '__main__':
    main()
