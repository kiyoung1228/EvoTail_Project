"""Healing previews must equal the HP actually restored by battle actions.

Run from the project root:
    python -m unittest discover -s tests -p "test_battle_healing.py" -v

Only temporary save files are used; saves/game.db is never opened.
"""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roc import GameBridge, GameService
from roc import battle as B
from roc import config as C


def fighter(key, role, stage=1, hp=1000):
    element=C.ROLE_ELEMENTS[role]
    return B.make_fighter(key,'player',role,element,stage,
                          {'hp':hp,'attack':60,'defense':60,'agility':60})


def battle_fixture(stage=1):
    return {'player':[fighter('healer','healer',stage),
                      fighter('tank','tank'),fighter('dealer','dealer')],
            'enemy':[fighter('enemy','dealer')],
            'current':'player','actions':0,'round':1,'winner':None,'log':[]}


class HealingActionTests(unittest.TestCase):
    def test_every_healer_stage_reports_actual_capped_healing(self):
        for stage,maximum in ((1,100),(2,300),(3,500)):
            for missing in (1,80,maximum,800):
                with self.subTest(stage=stage,missing=missing):
                    battle=battle_fixture(stage)
                    target=battle['player'][1]
                    target['hp']-=missing
                    action=next(a for a in B.legal_actions(battle,'healer')
                                if a['kind']=='special' and a['target']=='tank')
                    before=target['hp']
                    events=B.perform(battle,'healer','special','tank',random.Random(7))
                    self.assertEqual(action['amount'],min(maximum,missing))
                    self.assertEqual(events[0]['amount'],action['amount'])
                    self.assertEqual(target['hp']-before,action['amount'])
                    self.assertEqual(battle['player'][0]['cooldown'],2)

    def test_healing_only_targets_living_injured_allies(self):
        battle=battle_fixture()
        battle['player'][0]['hp']=995
        battle['player'][1]['hp']=0
        options=[a for a in B.legal_actions(battle,'healer') if a['kind']=='special']
        self.assertEqual(options,[{'kind':'special','actor':'healer',
                                   'target':'healer','amount':5}])
        events=B.perform(battle,'healer','special','healer',random.Random(7))
        self.assertEqual(events[0]['amount'],5)
        self.assertEqual(battle['player'][0]['hp'],1000)

    def test_healer_cooldown_actor_and_action_limits_are_preserved(self):
        for change in ('cooldown','acted','dead','budget','wrong_turn'):
            with self.subTest(change=change):
                battle=battle_fixture()
                battle['player'][1]['hp']=500
                healer=battle['player'][0]
                if change=='cooldown':healer['cooldown']=1
                elif change=='acted':healer['acted']=True
                elif change=='dead':healer['hp']=0
                elif change=='budget':battle['actions']=2
                else:battle['current']='enemy'
                self.assertFalse(any(a['kind']=='special'
                                     for a in B.legal_actions(battle,'healer')))
                with self.assertRaises(ValueError):
                    B.perform(battle,'healer','special','tank',random.Random(7))

    def test_nonhealing_actions_do_not_gain_amount(self):
        battle=battle_fixture()
        for actor in ('tank','dealer'):
            self.assertTrue(B.legal_actions(battle,actor))
            self.assertTrue(all('amount' not in a for a in B.legal_actions(battle,actor)))

    def test_bandage_amount_uses_item_rule_and_matches_actual_event(self):
        for capacity in (80,37):
            for missing in (1,capacity,200):
                with self.subTest(capacity=capacity,missing=missing):
                    battle=battle_fixture()
                    target=battle['player'][1]
                    target['hp']-=missing
                    with patch.dict(C.ITEMS['battle_bandage'],{'heal':capacity}):
                        amount=B.battle_item_heal_amount('battle_bandage',target)
                        before=target['hp']
                        events=B.use_battle_item(battle,'battle_bandage','tank')
                    self.assertEqual(amount,min(capacity,missing))
                    self.assertEqual(events[0]['amount'],amount)
                    self.assertEqual(target['hp']-before,amount)
                    self.assertEqual(battle['actions'],1)

    def test_bandage_invalid_actions_still_raise_without_mutating_battle(self):
        for invalid in ('full','dead','budget','wrong_turn','unknown_item','unknown_target'):
            with self.subTest(invalid=invalid):
                battle=battle_fixture()
                battle['player'][1]['hp']=500
                item,target='battle_bandage','tank'
                if invalid=='full':battle['player'][1]['hp']=1000
                elif invalid=='dead':battle['player'][1]['hp']=0
                elif invalid=='budget':battle['actions']=2
                elif invalid=='wrong_turn':battle['current']='enemy'
                elif invalid=='unknown_item':item='snack'
                else:target='missing'
                before=copy.deepcopy(battle)
                with self.assertRaises(ValueError):B.use_battle_item(battle,item,target)
                self.assertEqual(battle,before)


class HealingServiceTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.game=GameService(Path(temp.name)/'healing.db',now=lambda:1_800_000_000.0,
                              rng=random.Random(7))
        self.team=[a['id'] for a in self.game.get_animals()]
        self.game.start_battle('tutorial',self.team)
        self.healer=next(key for key in self.team
                         if self.game.characters[key]['role']=='healer')
        self.target=next(key for key in self.team if key!=self.healer)

    def hurt(self,missing=20):
        def update(s):
            target=next(f for f in s['battle']['player'] if f['id']==self.target)
            target['hp']=target['stats']['hp']-missing
        self.game._mutate(update)

    def test_bridge_healer_action_amount_matches_execution(self):
        self.hurt()
        response=GameBridge(self.game).call('get_battle_actions',actor=self.healer)
        self.assertTrue(response['ok'])
        options=json.loads(json.dumps(response['data']))
        action=next(a for a in options if a['kind']=='special' and a['target']==self.target)
        result=self.game.battle_action(self.healer,'special',self.target)
        self.assertEqual(action['amount'],20)
        self.assertEqual(result['events'][0]['amount'],action['amount'])

    def test_service_bandage_preview_matches_execution_and_consumes_inventory(self):
        self.game.buy_item('battle_bandage')
        self.hurt()
        options=self.game.get_battle_actions('battle_bandage')
        action=next(a for a in options if a['target']==self.target)
        self.assertEqual(action['amount'],20)
        result=self.game.battle_action('battle_bandage','battle_item',self.target)
        self.assertEqual(result['events'][0]['amount'],action['amount'])
        self.assertEqual(self.game.get_inventory()['stackable'].get('battle_bandage',0),0)

    def test_service_bandage_requires_inventory_injury_turn_and_budget(self):
        self.hurt()
        self.assertEqual(self.game.get_battle_actions('battle_bandage'),[])
        self.game.buy_item('battle_bandage')
        self.assertTrue(self.game.get_battle_actions('battle_bandage'))
        for change in ('full','dead','budget','wrong_turn'):
            with self.subTest(change=change):
                before=copy.deepcopy(self.game.state)
                def update(s):
                    battle=s['battle']
                    target=next(f for f in battle['player'] if f['id']==self.target)
                    if change=='full':target['hp']=target['stats']['hp']
                    elif change=='dead':target['hp']=0
                    elif change=='budget':battle['actions']=2
                    else:battle['current']='enemy'
                self.game._mutate(update)
                self.assertEqual(self.game.get_battle_actions('battle_bandage'),[])
                self.game._mutate(lambda s:s.update(copy.deepcopy(before)))


if __name__=='__main__':
    unittest.main()
