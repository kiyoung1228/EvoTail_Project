"""화면 출력이나 파일 입출력 없이 전투 상태를 계산한다.

모든 무작위 판정은 전달받은 rng로 수행하여 같은 조건에서 결과를 재현할 수 있다.
전투 상태를 저장하면 재실행 후 이어갈 수 있다. 한 팀 턴에는 살아 있는 서로 다른
동물이 최대 두 마리까지 행동한다.
"""
from __future__ import annotations
import math
import copy
import random
from . import config as C


def clamp(value, low, high):
    return max(low, min(high, value))


def round_half_up(value):
    return math.floor(value + .5)


def stats_for(info, equipped=None, potion=None):
    result=dict(info['stats'])
    for code in (equipped,potion):
        if code and code in C.ITEMS and 'stat' in C.ITEMS[code]:
            spec=C.ITEMS[code]
            result[spec['stat']]+=spec['amount']
    return result


def make_fighter(key, team, role, element, stage, stats):
    return {'id':key, 'team':team, 'role':role,'element':element,'stage':stage,
            'stats':stats,'hp':stats['hp'],'cooldown':0,'shield':False,'guard':False,'acted':False}


def alive(fighter):
    return fighter['hp']>0


def healing_amount(healer, target):
    """현재 대상에게 힐러의 특수 기술로 실제 회복할 수 있는 체력량을 계산한다."""
    maximum={1:100,2:300,3:500}[healer['stage']]
    return min(maximum,max(0,target['stats']['hp']-target['hp']))


def battle_item_heal_amount(item_id, target):
    """전투용 회복 아이템으로 실제 회복할 수 있는 체력량을 계산한다."""
    if item_id!='battle_bandage':raise ValueError('전투용 아이템 아님')
    return min(C.ITEMS[item_id]['heal'],max(0,target['stats']['hp']-target['hp']))


def multiplier(attacker, defender):
    a,b=attacker['element'],defender['element']
    if C.ELEMENT_BEATS.get(a)==b: return C.ELEMENT_ADVANTAGE
    if C.ELEMENT_BEATS.get(b)==a: return C.ELEMENT_DISADVANTAGE
    return 1.0


def calc_damage(attacker, defender, critical=False):
    atk=attacker['stats']['attack']; defense=defender['stats']['defense']
    dmg=atk*200/(200+defense)
    dmg*=multiplier(attacker,defender)
    if critical: dmg*=1.5
    return max(1,round_half_up(dmg))


def crit_chance(attacker):
    return min(.30,(5+attacker['stats']['attack']*.02)/100)


def dodge_chance(defender):
    return min(.25,(2+defender['stats']['agility']*.02)/100)


def start_team_turn(battle, side):
    battle['current']=side
    battle['actions']=0
    for fighter in battle[side]:
        fighter['acted']=False
        # 재사용 대기시간은 해당 동물의 팀 턴이 시작될 때만 줄인다.
        if fighter['cooldown']>0:
            fighter['cooldown']-=1
    return battle


def get_team(battle, side):
    return battle[side]


def max_actions(battle):
    return min(2,sum(alive(f) for f in get_team(battle,battle['current'])))


def legal_actions(battle, actor_id):
    side=battle['current']
    matches=[f for f in battle[side] if f['id']==actor_id]
    if not matches: return []
    actor=matches[0]
    if not alive(actor) or actor['acted'] or battle['actions']>=max_actions(battle): return []
    opponents=[x for x in battle['enemy' if side=='player' else 'player'] if alive(x)]
    teammates=[x for x in battle[side] if alive(x)]
    actions=[]
    # 기본 방어는 탱커의 절대방어와 다른 일반 전투 행동이다.
    # 다음 상대 팀 턴에 행동자 자신이 받는 공격 피해를 50% 줄인다.
    if C.ENABLE_BASIC_GUARD and not actor.get('guard',False):
        actions.append({'kind':'defend','actor':actor_id,'target':actor_id})
    if actor['role']=='dealer':
        if opponents: actions.append({'kind':'attack', 'actor':actor_id,'target':None})
    else:
        for target in opponents:
            actions.append({'kind':'attack','actor':actor_id,'target':target['id']})
    if actor['cooldown']==0:
        if actor['role']=='tank':
            actions.extend({'kind':'special','actor':actor_id,'target':x['id']} for x in teammates)
        elif actor['role']=='healer':
            actions.extend({'kind':'special','actor':actor_id,'target':x['id'],
                            'amount':healing_amount(actor,x)}
                           for x in teammates if x['hp']<x['stats']['hp'])
    return actions


def _find(team, key):
    return next((f for f in team if f['id']==key),None)


def perform(battle, actor_id, kind, target, rng):
    """행동을 검증하고 적용한다. 허용되지 않은 행동이면 ValueError를 발생시킨다."""
    if battle.get('winner') is not None: raise ValueError('이미 끝난 전투')
    side=battle['current']
    actor=_find(battle[side],actor_id)
    if actor is None: raise ValueError('없는 전투 동물')
    legal=legal_actions(battle,actor_id)
    if not any(a['kind']==kind and a['target']==target for a in legal):
        raise ValueError('지금 사용할 수 없는 행동·대상')
    actor['acted']=True
    battle['actions']+=1
    events=[]
    if kind=='attack':
        enemies=battle['enemy' if side=='player' else 'player']
        # 딜러의 전체 공격은 치명타를 한 번만 판정하고, 대상별 회피는 각각 판정한다.
        critical=(rng.random()<crit_chance(actor))
        victims=[f for f in enemies if alive(f)] if actor['role']=='dealer' else [_find(enemies,target)]
        for victim in victims:
            if victim['shield']:
                events.append({'type':'blocked','actor':actor_id,'target':victim['id']})
            elif rng.random()<dodge_chance(victim):
                events.append({'type':'dodged','actor':actor_id,'target':victim['id']})
            else:
                raw_damage=calc_damage(actor,victim,critical)
                if victim.get('guard',False):
                    raw_damage=round_half_up(raw_damage*C.GUARD_DAMAGE_MULTIPLIER)
                dealt=min(victim['hp'],max(1,raw_damage))
                victim['hp']-=dealt
                events.append({'type':'hit','actor':actor_id,'target':victim['id'],
                               'damage':dealt,'critical':critical,
                               'guarded':bool(victim.get('guard',False))})
    elif kind=='defend':
        actor['guard']=True
        events.append({'type':'guard','actor':actor_id,'target':actor_id,
                       'damage_multiplier':C.GUARD_DAMAGE_MULTIPLIER})
    elif kind=='special':
        teammate=_find(battle[side],target)
        if actor['role']=='tank':
            teammate['shield']=True
            events.append({'type':'shield','actor':actor_id,'target':target})
        elif actor['role']=='healer':
            gain=healing_amount(actor,teammate)
            teammate['hp']+=gain
            events.append({'type':'heal','actor':actor_id,'target':target,'amount':gain})
        # 다음 아군 팀 턴 한 번은 특수 기술을 쓸 수 없다. 다음 턴 시작에 2→1, 그다음에 1→0이 된다.
        actor['cooldown']=2
    update_winner(battle)
    return events


def use_battle_item(battle, item_id, target_id):
    """붕대를 사용하고 팀 행동 횟수를 한 번 소모한다.
    아이템 보유 수량의 확인과 차감은 이 함수가 아니라 서비스에서 처리한다.
    """
    if item_id!='battle_bandage': raise ValueError('전투용 아이템 아님')
    if battle['current']!='player' or battle.get('winner') is not None: raise ValueError('아직 내 차례 아님')
    if battle['actions']>=max_actions(battle): raise ValueError('이번 턴 행동 소진')
    target=_find(battle['player'],target_id)
    if target is None or not alive(target) or target['hp']>=target['stats']['hp']:
        raise ValueError('회복할 수 없는 대상')
    healed=battle_item_heal_amount(item_id,target)
    target['hp']+=healed
    battle['actions']+=1
    return [{'type':'battle_item','item':item_id,'target':target_id,'amount':healed}]


def update_winner(battle):
    if not any(alive(f) for f in battle['enemy']): battle['winner']='player'
    elif not any(alive(f) for f in battle['player']): battle['winner']='enemy'


def end_turn(battle):
    if battle.get('winner') is not None: return
    if battle['current']=='enemy':
        # 탱커의 절대방어는 다음 상대 팀 턴이 끝나면 해제한다.
        for f in battle['player']:
            f['shield']=False
            f['guard']=False
        battle['round']+=1
        start_team_turn(battle,'player')
    else:
        for f in battle['enemy']:
            f['shield']=False
            f['guard']=False
        start_team_turn(battle,'enemy')


def _evaluate(battle, side):
    own=battle[side]; foe=battle['player' if side=='enemy' else 'enemy']
    hp=lambda team:sum(f['hp']/max(1,f['stats']['hp']) for f in team)
    alive_count=lambda team:sum(alive(f) for f in team)
    return 160*(hp(own)-hp(foe))+100*(alive_count(own)-alive_count(foe))


def _score_action(battle, action):
    actor=_find(battle['enemy'],action['actor']); kind=action['kind']
    if kind=='defend':
        # 살아 있는 플레이어 동물의 공격에 노출된 저체력 동물일수록 방어의 가치가 크다.
        # 기본 방어는 다음에 받는 공격 피해를 절반으로 줄인다.
        defender=actor
        if defender.get('guard',False):return 0
        expected=sum(calc_damage(foe,defender)*(1-dodge_chance(defender))
                     for foe in battle['player'] if alive(foe))
        return min(defender['hp'],expected*C.GUARD_DAMAGE_MULTIPLIER)*.5
    if kind=='attack':
        targets=[f for f in battle['player'] if alive(f)] if actor['role']=='dealer' else [_find(battle['player'],action['target'])]
        return sum((1-dodge_chance(t)) * (0 if t['shield'] else min(t['hp'],calc_damage(actor,t)*(1+.5*crit_chance(actor))*(C.GUARD_DAMAGE_MULTIPLIER if t.get('guard',False) else 1))) for t in targets)
    target=_find(battle['enemy'],action['target'])
    if actor['role']=='healer':
        return min({1:100,2:300,3:500}[actor['stage']],target['stats']['hp']-target['hp'])*1.0
    if actor['role']=='tank':
        danger=sum(calc_damage(foe,target) for foe in battle['player'] if alive(foe))/max(1,sum(alive(f) for f in battle['enemy']))
        return danger*.7 if not target['shield'] else 0
    return 0


AI_PROFILES = {
    'tutorial': {
        'label':'뉴비', 'strategy':'공격 우선 무작위',
        'summary':'일반 공격만 사용해요',
        'description':'합법적인 일반 공격만 골라 튜토리얼 난이도를 낮춥니다.'},
    'random': {
        'label':'쉬움', 'strategy':'균등 무작위',
        'summary':'행동을 무작위로 골라요',
        'description':'공격/기본 방어/회복/절대방어 등 합법적인 행동을 무작위 선택합니다.'},
    'rules': {
        'label':'보통', 'strategy':'조건문 우선순위',
        'summary':'회복·보호를 우선해요',
        'description':'위급한 아군 회복 → 위급한 아군 보호 → 우선 공격 순서로 결정합니다.'},
    'heuristic': {
        'label':'어려움', 'strategy':'행동 기대효용 점수',
        'summary':'행동의 이득을 계산해요',
        'description':'광역 기대피해/명중/치명타, 회복 낭비, 보호 효용을 비교해 행동합니다.'},
    'lookahead': {
        'label':'극악', 'strategy':'전술 선행탐색',
        'summary':'다음 반격까지 내다봐요',
        'description':'자기 팀 남은 행동과 플레이어 반격, 다음 AI 행동까지 가상 전투로 비교합니다.'},
}


def _legal_enemy_actions(battle):
    if battle.get('winner') is not None or battle.get('current')!='enemy':
        return []
    return [a for f in battle['enemy'] for a in legal_actions(battle,f['id'])]


def _rule_based_choice(battle, legal):
    """상태별 긴급도와 조건문을 기준으로 설명 가능한 행동을 선택한다."""
    danger=[a for a in legal if a['kind']=='special'
            and _find(battle['enemy'],a['actor'])['role']=='healer'
            and (_find(battle['enemy'],a['target'])['hp']
                 / max(1,_find(battle['enemy'],a['target'])['stats']['hp']))<.55]
    if danger:
        return max(danger,key=lambda a:_score_action(battle,a)), '위급 아군 체력 55% 미만: 회복 우선'
    threatened=[a for a in legal if a['kind']=='special'
                and _find(battle['enemy'],a['actor'])['role']=='tank'
                and _find(battle['enemy'],a['target'])['hp']
                / max(1,_find(battle['enemy'],a['target'])['stats']['hp'])<.45
                and not _find(battle['enemy'],a['target'])['shield']]
    if threatened:
        return max(threatened,key=lambda a:_score_action(battle,a)), '위급 아군 체력 45% 미만: 보호 우선'
    attacks=[a for a in legal if a['kind']=='attack']
    if attacks:
        return max(attacks,key=lambda a:_score_action(battle,a)), '공격 효율이 가장 높은 대상 선택'
    return max(legal,key=lambda a:_score_action(battle,a)), '사용 가능한 유효 행동 선택'


def _sample_tactical_value(battle, action):
    """세 가지 고정 난수 조건에서 다음 두 AI 팀 턴의 전술을 탐색한다.

    후보 행동과 다른 AI 동물의 후속 행동, 플레이어의 반격 두 번, 다음 AI 팀 턴을
    차례로 가상 실행한다. 명중과 치명타는 임의의 고정값으로 대체하지 않고 실제
    난수로 판정한다. 학습된 강화학습 모델이 아니라 가능한 수를 탐색하는 방식이다.
    """
    scores=[]
    for seed in (11,29,47):
        shadow=copy.deepcopy(battle)
        simulator=random.Random(seed + shadow['round']*31 + len(action['actor']))
        perform(shadow,action['actor'],action['kind'],action['target'],simulator)
        if shadow['winner'] is not None:
            scores.append(_evaluate(shadow,'enemy')*3)
            continue

        # 첫 AI 팀 턴에서 살아 있는 다른 동물이 두 번째로 행동할 수 있다.
        if shadow['actions']<max_actions(shadow):
            more=_legal_enemy_actions(shadow)
            if more:
                follow=max(more,key=lambda a:_score_action(shadow,a))
                perform(shadow,follow['actor'],follow['kind'],follow['target'],simulator)
        if shadow['winner'] is None:
            end_turn(shadow)

        # 플레이어는 서로 다른 두 동물로 당장 점수가 가장 높은 반격을 한다고 가정한다.
        for _ in range(2):
            if shadow['winner'] is not None or shadow['current']!='player':break
            responses=[a for f in shadow['player'] for a in legal_actions(shadow,f['id'])]
            if not responses:break
            response=max(responses,key=lambda a:_player_response_score(shadow,a))
            perform(shadow,response['actor'],response['kind'],response['target'],simulator)
        if shadow['winner'] is None:
            end_turn(shadow)

        # 다음 AI 팀 턴까지 실행하여 플레이어의 반격을 버티는 행동의 가치를 평가한다.
        for _ in range(2):
            if shadow['winner'] is not None or shadow['current']!='enemy':break
            moves=_legal_enemy_actions(shadow)
            if not moves:break
            next_move=max(moves,key=lambda a:_score_action(shadow,a))
            perform(shadow,next_move['actor'],next_move['kind'],next_move['target'],simulator)
        scores.append(_evaluate(shadow,'enemy'))
    return sum(scores)/len(scores)


def _player_response_score(snapshot, action):
    actor=_find(snapshot['player'],action['actor'])
    if action['kind']=='defend':
        return .5*sum(calc_damage(f,actor) for f in snapshot['enemy'] if alive(f))*.5
    if action['kind']=='attack':
        targets=[f for f in snapshot['enemy'] if alive(f)] if actor['role']=='dealer' else [
            _find(snapshot['enemy'],action['target'])]
        return sum(0 if t['shield'] else min(t['hp'],calc_damage(actor,t))*(1-dodge_chance(t))*(C.GUARD_DAMAGE_MULTIPLIER if t.get('guard',False) else 1)
                   for t in targets)
    target=_find(snapshot['player'],action['target'])
    if actor['role']=='healer':
        return min({1:100,2:300,3:500}[actor['stage']],target['stats']['hp']-target['hp'])
    if actor['role']=='tank':
        return sum(calc_damage(f,target) for f in snapshot['enemy'] if alive(f))*.4
    return 0


def choose_ai_decision(battle, ai, rng):
    """허용된 AI 행동과 함께 화면·테스트에서 확인할 판단 근거를 반환한다.

    한 팀 턴에는 서로 다른 두 동물이 행동한다. 쓰러졌거나 이미 행동한 동물은
    제외하고, 체력이 줄었을 때만 회복하며, 재사용 대기시간이 끝났을 때만
    절대방어를 사용한다.
    """
    if ai not in AI_PROFILES:raise ValueError('알 수 없는 전투 AI')
    legal=_legal_enemy_actions(battle)
    if not legal:return None
    profile=AI_PROFILES[ai]
    if ai=='tutorial':
        attacks=[a for a in legal if a['kind']=='attack']
        choice=rng.choice(attacks or legal)
        why='뉴비: 공격 행동만 무작위 선택'
        score=None
    elif ai=='random':
        choice=rng.choice(legal)
        why='쉬움: 모든 합법적 행동 중 균등 무작위'
        score=None
    elif ai=='rules':
        choice,why=_rule_based_choice(battle,legal)
        score=_score_action(battle,choice)
    elif ai=='heuristic':
        choice=max(legal,key=lambda a:_score_action(battle,a))
        score=_score_action(battle,choice)
        why='어려움: 예측 피해·회복·방어 행동 점수 최댓값'
    elif ai=='lookahead':
        options=[(move,_sample_tactical_value(battle,move)) for move in legal]
        choice,score=max(options,key=lambda pair:pair[1])
        why='극악: 아군 2행동→플레이어 대응→다음 AI 행동 가상 탐색'
    return {'action':dict(choice),'ai':ai, 'strategy':profile['strategy'],
            'reason':why,'score':score,'legal_count':len(legal)}


def choose_ai_action(battle, ai, rng):
    """이전 호출 방식과 호환되도록 허용된 행동 사전만 반환한다."""
    decision=choose_ai_decision(battle,ai,rng)
    return decision['action'] if decision else None
