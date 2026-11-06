"""Editable game rules. Values marked provisional in docs are centralized here."""
from __future__ import annotations

STATS = ('hp', 'attack', 'defense', 'agility')
ROLES = ('dealer', 'tank', 'healer')
ROLE_ELEMENTS = {'dealer': 'fire', 'tank': 'water', 'healer': 'wind'}
NATURES = ('glutton', 'sleepy', 'playful', 'balanced', 'picky')

# PROVISIONAL: role-specific stage caps must be confirmed with teammate.
CAPS = {role: {stage: {stat: cap for stat in STATS} for stage, cap in ((1,300),(2,500),(3,1000))} for role in ROLES}
EVOLUTION_COST = {2: 800, 3: 3000}
TRAINING = {'easy': (600, 10, 10), 'medium': (1800, 30, 30), 'hard': (3600, 65, 65)} # sec, stat gain, fatigue+ / mood-fullness-
# Agreement: avoid taking impossible state values or exceeding 100; easy/medium and hard requirements are provisional.
TRAINING_MIN = {'easy': 10, 'medium': 30, 'hard': 65}
FATIGUE_TRAINING_HALF_THRESHOLD = 50
DISEASE_CHANCE = 0.30

# One base farm plot free, five buyable.
PLOT_COSTS = [0, 150, 350, 600, 900, 1200]
CROPS = ('wheat', 'potato', 'tomato', 'rice', 'onion', 'cabbage')
SEED_COST = 10
CROP_DURATION = 600
CROP_YIELD = 3
CROP_SELL = 15

HUNTS = {
    'chicken_coop': {'duration':1800, 'item':'chicken', 'count':3, 'label':'닭장'},
    'pig_pen': {'duration':1800, 'item':'pork', 'count':3, 'label':'돼지우리'},
    'ranch': {'duration':1800, 'item':'beef', 'count':3, 'label':'목장'},
    'rabbit_hill': {'duration':3600, 'item':'lucky_rabbit', 'count':3, 'label':'달토끼 언덕'},
}
# For UI: item is unique key, separate from Korean label.
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
    0: {'fullness':5, 'mood':-10, 'fatigue':0}, # burned (half-star)
    1: {'fullness':10, 'mood':0, 'fatigue':0},
    2: {'fullness':30, 'mood':10, 'fatigue':0},
    3: {'fullness':50, 'mood':20, 'fatigue':0},
    4: {'fullness':70, 'mood':30, 'fatigue':-20},
    5: {'fullness':100, 'mood':50, 'fatigue':-40},
}
BASE_FAIL = {1:.05, 2:.10, 3:.15, 4:.20, 5:.25}
COOK_XP = {1:10, 2:20, 3:35, 4:55, 5:80}
COOK_LEVEL_XP = (0,100,300,700,1300)
COOK_FAIL_REDUCTION = (0, .03, .06, .09, .12)
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
ITEMS['burned_food'] = {'label':'탄 요리','buy':None,'sell':3,'kind':'food','stars':0}
for recipe_id, recipe in RECIPES.items():
    ITEMS['food_'+recipe_id] = {'label':recipe['label'], 'buy':None, 'sell':recipe['sell'], 'kind':'food', 'stars':recipe['stars']}

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

# Provisional numbers based on design discussion.
PASSIVE_FULLNESS_EVERY = 300
PASSIVE_FULLNESS_DELTA = -2
PASSIVE_MOOD_EVERY = 600
PASSIVE_MOOD_DELTA = -1
REST_EVERY = 5
AUTONOMOUS_EVERY = 60
AUTONOMOUS_PLAY_EVERY = 600
AUTONOMOUS_PLAY_MOOD_GAIN = 3
AUTONOMOUS_PLAY_MOOD_CAP = 55
AUTONOMOUS_OFFLINE_DETAIL_WINDOW = 86400  # replay last day of idle behavior accurately
STORM_CYCLE = 3600
STORM_DURATION = 600
# Additional random bonus event required by assignment; evaluated on bounded clock slots.
BONUS_EVENT_EVERY = 1800
BONUS_EVENT_PROBABILITY = 0.15
BONUS_EVENT_COINS = 30

# Provisional elemental gameplay matchup (not just GUI), with minimal multiplier.
ELEMENT_BEATS = {'fire':'wind','wind':'water','water':'fire'}
ELEMENT_ADVANTAGE = 1.1
ELEMENT_DISADVANTAGE = .9

# Provisional tutorial and battle item to comply with assignment item-in-combat requirement.
ITEMS['battle_bandage'] = {'label':'전투 응급 붕대','buy':80,'sell':40,'kind':'battle_item','heal':80}


# v3: a basic guard action is distinct from the tank's absolute shield.
# It absorbs half the next enemy-team turn's incoming attack damage.
# This supplements the mandatory attack/defense/special/item battle controls.
ENABLE_BASIC_GUARD = True
GUARD_DAMAGE_MULTIPLIER = 0.5

# A finite limit prevents excessive simulated battle rounds from locking the GUI.
# At this threshold the team with more remaining effective HP is declared the winner.
MAX_BATTLE_ROUNDS = 120

# v3: cooking, statuses, money and stage rules live here. Role-specific
# stat limits are read separately from data/role_caps.json.
GAME_RULES_VERSION = '3.0'
