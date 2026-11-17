"""태풍 시간(밤 02:00)으로 맞춘 실제 화면 찍기 (지도·내 동물·스테이지·마이룸). 글씨 UI는 그대로, 비는 목업에서 덧그림."""
import os, sys, tempfile
PROJ = '/home/claude/kiyoung1228/evotail_project'
sys.path.insert(0, PROJ); os.chdir(PROJ)
OUT = sys.argv[1]
import pygame, run_gui
from gui.app import App
from gui import theme as T

def run(self):
    self.call('reset_game', confirm=True, starters=['dealer_normal_01', 'tank_normal_03', 'healer_normal_05'])
    with self.game._lock if hasattr(self.game, '_lock') else open(os.devnull):
        self.game.state['created'] -= 3300 + 30      # 경과 3330초 = 02:12, 태풍
    self.refresh()
    print('clock', self.state.get('clock'))
    S = T.SCALE
    def frames(n=2):
        for _ in range(n): self.step(1 / T.FPS)
    def shot(name): pygame.image.save(self.window, os.path.join(OUT, name))
    def move(l):
        w = (l[0] * S + S // 2, l[1] * S + S // 2); pygame.mouse.set_pos(w)
        pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=w, rel=(0, 0), buttons=(0, 0, 0))); frames(2)
    move((300, 345))
    self.go('map'); frames(30); shot('map.png')
    self.go('animals'); frames(5); shot('animals.png')
    self.go('battle'); frames(5); shot('stage.png')
    self.go('my_room'); frames(10); shot('room.png')

App.run = run
run_gui.main(os.path.join(tempfile.mkdtemp(), 'storm.db'))
