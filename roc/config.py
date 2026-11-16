"""게임 규칙 설정. 문서에서 임시로 정한 수치도 이곳에서 관리한다."""
from __future__ import annotations

STATS = ('hp', 'attack', 'defense', 'agility')
ROLES = ('dealer', 'tank', 'healer')
ROLE_ELEMENTS = {'dealer': 'fire', 'tank': 'water', 'healer': 'wind'}
NATURES = ('glutton', 'sleepy', 'playful', 'balanced', 'picky')

# 역할·능력치·진화 단계별 실제 상한은 data/role_caps.json에 있다.
# 진화와 훈련의 상한은 GameService.caps를 기준으로만 판단한다.
YARD_MAX_ANIMALS = 5
EVOLUTION_COST = {2: 800, 3: 3000}
TRAINING = {'easy': (600, 10, 10), 'medium': (1800, 30, 30), 'hard': (3600, 65, 65)} # 소요 시간(초), 능력치 증가량, 피로도 증가량 / 기분·포만감 감소량
# 상태값이 범위를 벗어나거나 100을 넘지 않도록 제한한다. 난이도별 최소 조건은 임시 수치다.
TRAINING_MIN = {'easy': 10, 'medium': 30, 'hard': 65}
FATIGUE_TRAINING_HALF_THRESHOLD = 50
DISEASE_CHANCE = 0.30

# 밭 한 칸은 기본 제공하고, 나머지 다섯 칸은 구매로 확장한다.
PLOT_COSTS = [0, 150, 350, 600, 900, 1200]
CROPS = ('wheat', 'potato', 'tomato', 'rice', 'onion', 'cabbage')
SEED_COST = 10
CROP_DURATION = 600
CROP_YIELD = 3
CROP_SELL = 15

# 처음 등급을 뽑을 때 사용하는 확률이다. 특수 알은 선택한 등급을 모두 보유했다면
# 다른 등급의 미보유 동물을 우선 선택할 수 있다.
HATCHING = {
    'egg_basic': {'special_probability':0.10},
    'egg_special': {'special_probability':0.60, 'duplicate_probability_cap':0.20},
}

HUNTS = {
    'chicken_coop': {'duration':1800, 'item':'chicken', 'count':3, 'label':'닭장',
                     'completion_effects':{'fullness':-10, 'mood':-5, 'fatigue':20}},
    'pig_pen': {'duration':1800, 'item':'pork', 'count':3, 'label':'돼지우리',
                'completion_effects':{'fullness':-10, 'mood':-5, 'fatigue':20}},
    'ranch': {'duration':1800, 'item':'beef', 'count':3, 'label':'목장',
              'completion_effects':{'fullness':-10, 'mood':-5, 'fatigue':20}},
    'rabbit_hill': {'duration':3600, 'item':'lucky_rabbit', 'count':3, 'label':'달토끼 언덕',
                    'completion_effects':{'fullness':-20, 'mood':-10, 'fatigue':35}},
}
# 화면 표시용 한글 이름과 구분하여 item을 고유 식별자로 사용한다.
ITEMS = {
    'snack': {'label':'기본 간식', 'buy':50, 'sell':None, 'kind':'snack', 'fullness':35},
    'toy_ball': {'label':'장난감 공', 'buy':100, 'sell':50, 'kind':'toy', 'charges':5, 'mood':20},
    'toy_doll': {'label':'인형', 'buy':150, 'sell':75, 'kind':'toy', 'charges':3, 'mood':35},
    'heal_basic': {'label':'기본 회복 포션', 'buy':40, 'sell':20, 'kind':'cure', 'chance':0.5, 'fatigue':-10},
    'heal_advanced': {'label':'고급 회복 포션', 'buy':80, 'sell':40, 'kind':'cure', 'chance':0.9, 'fatigue':-30},
    'potion_attack': {'label':'공격력 포션', 'buy':150, 'sell':75, 'kind':'prebattle', 'stat':'attack', 'amount':100},
    'potion_defense': {'label':'방어력 포션', 'buy':130, 'sell':65, 'kind':'prebattle', 'stat':'defense', 'amount':100},
    'potion_hp': {'label':'체력 포션', 'buy':120, 'sell':60, 'kind':'prebattle', 'stat':'hp', 'amount':100},
    'potion_agility': {'label':'민첩성 포션', 'buy':100, 'sell':50, 'kind':'prebattle', 'stat':'agility', 'amount':100},
    'equip_necklace': {'label':'가죽 목걸이', 'buy':400, 'sell':200, 'kind':'equip', 'stat':'hp', 'amount':50},
    'equip_claw': {'label':'날카로운 발톱', 'buy':500, 'sell':250, 'kind':'equip', 'stat':'attack', 'amount':50},
    'equip_shell': {'label':'등껍질 보호대', 'buy':450, 'sell':225, 'kind':'equip', 'stat':'defense', 'amount':50},
    'equip_feather': {'label':'가벼운 깃털', 'buy':400, 'sell':200, 'kind':'equip', 'stat':'agility', 'amount':30},
    'egg_basic': {'label':'기본 부화 알', 'buy':500, 'sell':None, 'kind':'egg'},
    'egg_special': {'label':'특수 부화 알', 'buy':2200, 'sell':None, 'kind':'egg'},
    'milk': {'label':'우유', 'buy':20, 'sell':None, 'kind':'ingredient'},
    'egg_food': {'label':'달걀', 'buy':15, 'sell':None, 'kind':'ingredient'},
    'salt': {'label':'소금', 'buy':5, 'sell':None, 'kind':'ingredient'},
    'butter': {'label':'버터', 'buy':10, 'sell':None, 'kind':'ingredient'},
    'chicken': {'label':'닭고기', 'buy':None, 'sell':40, 'kind':'ingredient'},
    'pork': {'label':'돼지고기', 'buy':None, 'sell':50, 'kind':'ingredient'},
    'beef': {'label':'소고기', 'buy':None, 'sell':60, 'kind':'ingredient'},
    'lucky_rabbit': {'label':'행운의 토끼고기', 'buy':None, 'sell':170, 'kind':'ingredient'},
}
for crop in CROPS:
    ITEMS[crop] = {'label':{'wheat':'밀', 'potato':'감자','tomato':'토마토','rice':'쌀','onion':'양파','cabbage':'양배추'}[crop], 'buy':None, 'sell':CROP_SELL, 'kind':'crop'}
    ITEMS['seed_'+crop] = {'label':ITEMS[crop]['label']+' 씨앗', 'buy':SEED_COST, 'sell':None, 'kind':'seed', 'crop':crop}

FOOD_EFFECTS = {
    0: {'fullness':5, 'mood':-10, 'fatigue':0}, # 탄 요리(반 개의 별)
    1: {'fullness':10, 'mood':0, 'fatigue':0},
    2: {'fullness':30, 'mood':10, 'fatigue':0},
    3: {'fullness':50, 'mood':20, 'fatigue':0},
    4: {'fullness':70, 'mood':30, 'fatigue':-20},
    5: {'fullness':100, 'mood':50, 'fatigue':-40},
}
COOK_XP = {stars: stars * 10 for stars in range(1, 6)}
COOK_LEVEL_XP = (0,100,300,600,1000)
COOK_LEVELS = COOK_LEVEL_XP  # 요리 레벨 1~5의 누적 경험치 기준
COOK_MISS_RESCUE_BY_LEVEL = (0.0, .10, .20, .30, .40)
COOK_MISS_RESCUE_MAX_STAR = 3
COOK_JUDGMENTS = ('perfect', 'good', 'miss')
COOK_GRADES = ('Perfect', 'Good', 'Miss')  # 이전 화면 구현과의 호환을 위한 판정 이름
COOK_PERFECT_MULTIPLIER = 1.5
# 커서 좌표는 0~100 범위로 맞추고, 화면에서 타이밍 판정을 측정한다.
# 실패 구제 확률, 아이템 수량, 경험치, 음식 효과는 백엔드가 처리한다.
COOK_TIMING = {
    'min_position': 0, 'max_position': 100,
    'target_center_min': 20, 'target_center_max': 80,
    'perfect_half_width': 5, 'good_half_width': 15,
    'timeout_seconds': 5,
    'travel_seconds_by_star': {1:1.8, 2:1.6, 3:1.4, 4:1.2, 5:1.0},
}
RECIPES = {
    'boiled_egg': {'label':'삶은 달걀', 'stars':1, 'ingredients':{'egg_food':1}, 'sell':12},
    'steamed_potato': {'label':'찐 감자', 'stars':1, 'ingredients':{'potato':1,'salt':1}, 'sell':35},
    'egg_roll': {'label':'계란말이', 'stars':2, 'ingredients':{'egg_food':2,'onion':1,'salt':1}, 'sell':80},
    'tomato_soup': {'label':'토마토수프', 'stars':2, 'ingredients':{'tomato':2,'onion':1,'milk':1}, 'sell':100},
    'butter_potato': {'label':'감자버터구이', 'stars':2, 'ingredients':{'potato':1,'butter':1}, 'sell':45},
    'chicken_burger': {'label':'닭고기 햄버거', 'stars':3, 'ingredients':{'chicken':1,'wheat':1,'tomato':1,'onion':1}, 'sell':140},
    'beef_burger': {'label':'소고기 햄버거', 'stars':3, 'ingredients':{'beef':1,'wheat':1,'tomato':1,'onion':1}, 'sell':170},
    'fried_chicken': {'label':'치킨', 'stars':4, 'ingredients':{'chicken':2,'salt':1,'wheat':2}, 'sell':210},
    'carbonara': {'label':'까르보나라', 'stars':5, 'ingredients':{'wheat':2,'onion':1,'milk':2,'egg_food':1,'butter':1}, 'sell':205},
    'omelette_rice': {'label':'오므라이스', 'stars':5, 'ingredients':{'rice':2,'onion':1,'chicken':1,'egg_food':2,'butter':1}, 'sell':235},
    'rabbit_stew': {'label':'행운의 토끼고기 스튜', 'stars':5, 'ingredients':{'lucky_rabbit':1,'potato':1,'onion':1,'tomato':1,'butter':1}, 'sell':400},
}
ITEMS['burned_food'] = {'label':'탄 요리','buy':None,'sell':3,'kind':'food','stars':0,
                        'quality':'burned','effect_multiplier':1.0,'effects':dict(FOOD_EFFECTS[0])}
for recipe_id, recipe in RECIPES.items():
    base = {'label':recipe['label'], 'buy':None, 'sell':recipe['sell'], 'kind':'food', 'stars':recipe['stars']}
    ITEMS['food_'+recipe_id] = {**base, 'quality':'normal', 'effect_multiplier':1.0,
                               'effects':dict(FOOD_EFFECTS[recipe['stars']])}
    # 별도 아이템 키로 저장하여 보관하거나 나중에 먹여도 대성공 효과를 유지한다.
    # 판매가는 같고, 먹였을 때의 효과만 1.5배로 적용한다.
    ITEMS['food_perfect_'+recipe_id] = {**base, 'label':recipe['label']+' (대성공)',
                                       'quality':'perfect','effect_multiplier':COOK_PERFECT_MULTIPLIER,
                                       'effects':{stat:int(value*COOK_PERFECT_MULTIPLIER)
                                                  for stat,value in FOOD_EFFECTS[recipe['stars']].items()}}

STAGES = {
    'tutorial': {'label':'뉴비', 'mode':'tutorial','power':40, 'reward':100,'ai':'tutorial','order':0},
    'easy': {'label':'쉬움', 'mode':'normal','power':150, 'reward':200,'ai':'random','order':1},
    'bronze': {'label':'브론즈', 'mode':'rank','power':250,'reward':300,'ai':'random','order':2},
    'normal': {'label':'보통', 'mode':'normal','power':400,'reward':500,'ai':'rules','order':3},
    'silver': {'label':'실버', 'mode':'rank','power':500,'reward':800,'ai':'rules','order':4},
    'hard': {'label':'어려움', 'mode':'normal','power':800,'reward':1100,'ai':'heuristic','order':5},
    'gold': {'label':'골드', 'mode':'rank','power':900,'reward':1800,'ai':'heuristic','order':6},
    'extreme': {'label':'극악', 'mode':'normal','power':1100,'reward':1800,'ai':'lookahead','order':7},
    'diamond': {'label':'다이아몬드', 'mode':'rank','power':1200,'reward':3000,'ai':'lookahead','order':8},
}
STAGE_ORDER = tuple(sorted(STAGES, key=lambda key:STAGES[key]['order']))
RANKS = ('none','bronze','silver','gold','diamond')

# 게임 설계에 사용하는 임시 수치다.
PASSIVE_FULLNESS_EVERY = 300
PASSIVE_FULLNESS_DELTA = -2
PASSIVE_MOOD_EVERY = 600
PASSIVE_MOOD_DELTA = -1
REST_EVERY = 5
AUTONOMOUS_EVERY = 60
AUTONOMOUS_PLAY_EVERY = 600
AUTONOMOUS_PLAY_MOOD_GAIN = 3
AUTONOMOUS_PLAY_MOOD_CAP = 55
AUTONOMOUS_OFFLINE_DETAIL_WINDOW = 86400  # 최근 하루 동안의 자율행동은 상세히 재현한다.
STORM_CYCLE = 3600
STORM_DURATION = 600
# 과제의 확률 기반 보너스 이벤트. 정해진 시간 구간마다 발생 여부를 판단한다.
BONUS_EVENT_EVERY = 1800
BONUS_EVENT_PROBABILITY = 0.15
BONUS_EVENT_COINS = 30

# 실제 전투 계산에 적용하는 임시 속성 상성과 배율이다.
ELEMENT_BEATS = {'fire':'wind','wind':'water','water':'fire'}
ELEMENT_ADVANTAGE = 1.1
ELEMENT_DISADVANTAGE = .9

# 전투 중 아이템 사용 요구사항에 맞춘 임시 회복 아이템이다.
ITEMS['battle_bandage'] = {'label':'전투 응급 붕대','buy':80,'sell':40,'kind':'battle_item','heal':80}


# 기본 방어는 탱커의 절대방어 기술과 별개다.
# 다음 상대 팀 턴에 받는 공격 피해를 절반으로 줄인다.
# 공격·방어·특수 기술·아이템을 사용하는 전투 조작을 지원한다.
ENABLE_BASIC_GUARD = True
GUARD_DAMAGE_MULTIPLIER = 0.5

# 과도한 전투 시뮬레이션으로 화면이 멈추지 않도록 라운드 상한을 둔다.
# 상한에 도달하면 남은 유효 체력이 더 많은 팀을 승자로 판정하는 기준값이다.
MAX_BATTLE_ROUNDS = 120

# 요리·상태·재화·스테이지 규칙은 이 파일에서 관리한다.
# 역할별 능력치 상한은 data/role_caps.json에서 별도로 읽는다.
GAME_RULES_VERSION = '3.0'
