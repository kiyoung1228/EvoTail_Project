"""Standalone non-GUI interactive-flow demonstration with fake clock. No save modified.
Run: python demo_scenario.py
"""
import random
import tempfile
from pathlib import Path
from roc import GameService
from roc import battle as B

class FakeClock:
    def __init__(self):self.value=1800000000.0
    def __call__(self):return self.value
    def advance(self,seconds):self.value+=seconds


def main():
    clock=FakeClock()
    with tempfile.TemporaryDirectory() as directory:
        game=GameService(Path(directory)/'demo.db',now=clock,rng=random.Random(11))
        ids=[a['id'] for a in game.get_animals()]
        print('1. 새 게임:',game.get_game_state())
        game.buy_item('seed_potato')
        print('2. 밭 재배:',game.plant_crop(0,'potato'))
        game.buy_item('egg_food')
        print('3. 요리:',game.cook('boiled_egg'))
        print('4. 튜토리얼 적 팀 공개:',game.preview_stage('tutorial')['enemy'])
        game.start_battle('tutorial',ids)
        for _ in range(30):
            b=game.get_battle()
            if b is None:break
            candidates=[action for fighter in b['player'] for action in B.legal_actions(b,fighter['id'])]
            if not candidates:
                game.end_player_turn();continue
            action=next((a for a in candidates if a['kind']=='attack' and 'dealer' in a['actor']), candidates[0])
            game.battle_action(action['actor'],action['kind'],action['target'])
        print('5. 전투 결과:',game.get_last_battle_result()['winner'])
        clock.advance(601)
        print('6. 오프라인 시간 경과/수확:',game.harvest_crop(0))
        print('7. 인벤토리:',game.get_inventory())
        print('8. 저장:',game.save_game())
        print('9. 재실행 후 상태:',GameService(Path(directory)/'demo.db',now=clock,rng=random.Random(11)).get_game_state())

if __name__=='__main__':main()
