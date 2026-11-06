"""No-GUI smoke demonstration. Run from project root: python main.py"""
from roc import GameService, GameRuleError

if __name__=='__main__':
    game=GameService()
    print('Rise of Champions | backend smoke demonstration')
    print('게임 상태:',game.get_game_state())
    print('동물 목록:')
    for row in game.get_animals():
        print(' ',row['id'],row['name'],row['nature'],row['stats'])
    print('도감 수집:',len([x for x in game.get_pokedex() if x['owned']]),'/30')
    print('스테이지:')
    for st in game.get_stages():print(' ',st['id'],st['power'],'unlocked:',st['unlocked'])
    print('샘플 실행 성공. GUI 연결은 docs/API_V3.md를 참고하세요.')
