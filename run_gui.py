"""EvoTail 게임 실행 (Pygame 화면). 프로젝트 폴더에서: python run_gui.py

F5: 시간 빠르게(5배) 켜기/끄기
F12: 시연 모드(60배) 켜기/끄기 - 영상 촬영용
"""
from gui.app import App
from gui.scenes.map_scene import MapScene
from gui.scenes.animals_scene import AnimalsScene
from gui.scenes.placeholder import PlaceholderScene


def main(save_path='saves/game.db'):
    app = App(save_path)
    app.register('map', MapScene(app))
    app.register('animals', AnimalsScene(app))
    for name, title in (('farm', '밭'), ('shop', '상점'), ('hospital', '병원'), ('kitchen', '주방'),
                        ('hunting', '사냥터'), ('battle', '전투장'), ('pokedex', '도감')):
        app.register(name, PlaceholderScene(app, title))
    app.go('map')
    app.run()


if __name__ == '__main__':
    main()
