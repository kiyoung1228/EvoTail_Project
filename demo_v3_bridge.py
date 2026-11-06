"""One-command GUI-contract demo: uses temporary save, not the real game.db."""
import json
import random
import tempfile
from pathlib import Path
from roc import GameService, GameBridge


def show(label, value):
    print(f'[{label}]',json.dumps(value,ensure_ascii=False))


def run():
    with tempfile.TemporaryDirectory() as folder:
        game=GameService(Path(folder)/'test_game.db', rng=random.Random(7))
        ui=GameBridge(game)
        snapshot=ui.call('get_snapshot')
        assert snapshot['ok'],snapshot
        show('GUI 첫 화면',{'coins':snapshot['data']['coins'],
                            'animals':len(snapshot['data']['animals']),
                            'plots':len(snapshot['data']['plots']),
                            'stages':len(snapshot['data']['stages'])})
        show('씨앗 구매',ui.call('buy_item',item='seed_potato'))
        show('감자 심기',ui.call('plant_crop',index=0,crop='potato'))
        show('스테이지 미리보기',ui.call('preview_stage',stage='tutorial')['data']['enemy'])
        team=[a['id'] for a in ui.call('get_animals')['data']]
        b=ui.call('start_battle',stage='tutorial',team=team)
        assert b['ok'],b
        dealer=next(a for a in b['data']['player'] if a['role']=='dealer')
        show('일반 공격/방어 버튼 목록',ui.call('get_battle_actions',actor=dealer['id']))
        result=ui.call('battle_action',actor=dealer['id'],kind='attack',target=None)
        assert result['ok'],result
        show('공격 결과',{'events':result['data']['events'],'ended':result['data']['battle'] is None})
        show('도감 일부',ui.call('get_pokedex')['data'][:2])
        show('업적 일부',ui.call('get_achievement_details')['data'][:3])
        show('잘못된 구매 처리',ui.call('buy_item',item='egg_special',quantity=999))
        show('최종 저장',ui.call('save_game'))
    print('V3 bridge demo OK. No real game save modified.')


if __name__=='__main__':
    run()
