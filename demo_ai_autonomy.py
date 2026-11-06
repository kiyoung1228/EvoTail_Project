"""No Pygame required. Run: python demo_ai_autonomy.py"""
from __future__ import annotations
import random
import tempfile
from pathlib import Path
from roc import GameService
from roc import battle as B
from roc.autonomy import evaluate


def fighter(key,team,role,element,hp=300,attack=70,defense=80,agility=50):
    return B.make_fighter(key,team,role,element,1,
                          {'hp':hp,'attack':attack,'defense':defense,'agility':agility})


class Clock:
    def __init__(self):self.now=1800000000.0
    def __call__(self):return self.now
    def jump(self,seconds):self.now+=seconds


def main():
    print('=== 전투 AI: 난이도별 실제 의사결정 ===')
    for ai in B.AI_PROFILES:
        battle={'player':[fighter('P1','player','dealer','fire'),
                          fighter('P2','player','tank','water'),
                          fighter('P3','player','healer','wind')],
                'enemy':[fighter('E1','enemy','tank','water'),
                         fighter('E2','enemy','healer','wind'),
                         fighter('E3','enemy','dealer','fire')],
                'current':'enemy','actions':0,'round':1,'winner':None}
        battle['enemy'][0]['hp']=80
        decision=B.choose_ai_decision(battle,ai,random.Random(9))
        print(f"{B.AI_PROFILES[ai]['label']:>4}: {decision['action']} | {decision['reason']}")
    print('\n=== 자율행동 AI: 동일한 상태에서 성격별 차이 ===')
    for nature in ('balanced','glutton','sleepy','playful','picky'):
        state={'nature':nature,'fullness':60,'mood':60,'fatigue':40}
        decision=evaluate(state)
        print(f"{nature:>8}: {decision.action:<6} / {decision.reason}")

    print('\n=== 실제 GameService API: 시간 경과 및 적 AI 행동 로그 ===')
    clock=Clock()
    with tempfile.TemporaryDirectory() as temp:
        game=GameService(Path(temp)/'demo.db',now=clock,rng=random.Random(7))
        ids=[row['id'] for row in game.get_animals()]
        clock.jump(65)
        print('자율행동 상태:',[(x['id'],x['action']) for x in game.get_autonomous_state()])
        print('AI 프로필:',[v['strategy'] for v in game.get_ai_profiles().values()])
        game.start_battle('tutorial',ids)
        result=game.end_player_turn()  # 0 actions chosen: enemy AI performs its legal turn
        log=result['battle']['log'] if result['battle'] else result['result']['log']
        print('적 AI 실제 사용 행동:',[ev['action'] for ev in log if ev['type']=='ai_decision'])
        print('전투 이벤트 수:',len(log))
    print('Demo complete.')


if __name__=='__main__':
    main()
