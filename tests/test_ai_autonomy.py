"""Focused tests that demonstrate implemented AI difficulty and autonomous behaviors."""
import copy
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roc import GameService
from roc import autonomy as AUTO
from roc import battle as B
from roc import config as C


class FakeClock:
    def __init__(self, start=1800000000):
        self.value = float(start)
    def __call__(self):
        return self.value
    def jump(self, seconds):
        self.value += seconds


def stats(hp=300, attack=70, defense=80, agility=50):
    return {'hp':hp, 'attack':attack, 'defense':defense, 'agility':agility}


def make_battle():
    own=[B.make_fighter('E_t', 'enemy', 'tank', 'water', 1, stats(300,70,120)),
         B.make_fighter('E_h', 'enemy', 'healer', 'wind', 1, stats(300,50,60)),
         B.make_fighter('E_d', 'enemy', 'dealer', 'fire', 1, stats(250,95,55))]
    foe=[B.make_fighter('P_t', 'player', 'tank', 'water', 1, stats(300,70,120)),
         B.make_fighter('P_h', 'player', 'healer', 'wind', 1, stats(300,50,60)),
         B.make_fighter('P_d', 'player', 'dealer', 'fire', 1, stats(250,95,55))]
    return {'player':foe,'enemy':own,'current':'enemy','actions':0,
            'round':1,'winner':None}


class AutonomousDecisionTests(unittest.TestCase):
    def test_mild_needs_and_personality_produce_different_actions(self):
        animal={'fullness':60,'fatigue':20,'mood':60,'nature':'balanced'}
        self.assertEqual(AUTO.evaluate(animal).action,'idle')
        animal['nature']='glutton'
        self.assertEqual(AUTO.evaluate(animal).action,'eat')
        animal['nature']='playful'
        self.assertEqual(AUTO.evaluate(animal).action,'play')
        animal.update(nature='sleepy', fatigue=40)
        self.assertEqual(AUTO.evaluate(animal).action,'rest')

    def test_emergency_need_overrides_personality(self):
        a={'fullness':90,'fatigue':90,'mood':90,'nature':'glutton'}
        decision=AUTO.evaluate(a)
        self.assertEqual(decision.action,'rest')
        self.assertIn('나쁨',decision.reason)

    def test_picky_animal_refuses_unhealthy_state(self):
        a={'fullness':20,'fatigue':5,'mood':90,'nature':'picky'}
        self.assertEqual(AUTO.evaluate(a).action,'refuse')


class AutonomousIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.clock=FakeClock()
        self.path=Path(self.temp.name)/'save.db'
        self.game=GameService(self.path, now=self.clock, rng=random.Random(8))
        self.id=self.game.get_animals()[0]['id']
    def tearDown(self):
        self.temp.cleanup()
    def _set(self, **values):
        self.game._mutate(lambda state:state['animals'][self.id].update(values))
    def _animal(self):
        return next(x for x in self.game.get_animals() if x['id']==self.id)

    def test_glutton_search_is_visible_and_does_not_mint_food(self):
        self._set(nature='glutton',fullness=60,mood=80,fatigue=0)
        before=copy.deepcopy(self.game.get_inventory())
        coins=self.game.get_game_state()['coins']
        self.clock.jump(61)
        view=self.game.get_autonomous_state(self.id)
        self.assertEqual(view['action'],'eat')
        self.assertEqual(view['nature'],'glutton')
        self.assertEqual(self.game.get_inventory(),before)
        self.assertEqual(self.game.get_game_state()['coins'],coins)
        self.assertTrue(any(ev['type']=='autonomous_action' and ev['action']=='eat'
                            for ev in self.game.recent_events()))

    def test_play_mood_bonus_respects_cap_and_no_unlimited_resources(self):
        self._set(nature='playful',fullness=100,mood=35,fatigue=0)
        self.clock.jump(61)
        self.assertEqual(self.game.get_autonomous_state(self.id)['action'],'play')
        self.clock.jump(600)
        self.assertGreaterEqual(self._animal()['mood'],37)  # -1 passive +3 autonomous
        self.clock.jump(7200)
        self.assertLessEqual(self._animal()['mood'],55)

    def test_idle_day_night_rest_and_busy_stop_autonomy(self):
        self._set(nature='sleepy',fullness=90,mood=90,fatigue=60)
        self.clock.jump(61)
        self.assertEqual(self.game.get_autonomous_state(self.id)['action'],'rest')
        self.assertLess(self._animal()['fatigue'],60)
        # Start training after replenishing readiness; while busy no play or rest.
        self._set(nature='balanced',fullness=90,mood=90,fatigue=0)
        self.game.start_training(self.id,'attack','easy')
        self.clock.jump(120)
        self.assertEqual(self.game.get_autonomous_state(self.id)['action'],'training')
        self.assertEqual(self._animal()['fatigue'],0)

    def test_offline_autonomy_is_reproducible_and_does_not_pay_rewards_twice(self):
        self._set(nature='playful',mood=40,fullness=95)
        self.clock.jump(3*3600)
        first=self._animal()
        self.assertIn(first['auto_action'],('eat','play','idle','rest','refuse'))
        again=GameService(self.path,now=self.clock,rng=random.Random(10))
        same=next(x for x in again.get_animals() if x['id']==self.id)
        for key in ('mood','fullness','fatigue','auto_action','last_tick'):
            self.assertEqual(first[key],same[key])

    def test_month_offline_advances_and_state_remains_bounded(self):
        self.clock.jump(32*24*3600)
        now=self._animal()
        self.assertEqual(now['fullness'],0)
        self.assertTrue(0<=now['mood']<=100)
        self.assertTrue(0<=now['fatigue']<=100)

    def test_sick_animal_still_idle_but_cannot_train(self):
        self._set(sick=True, nature='sleepy',fatigue=65)
        self.clock.jump(61)
        self.assertIn(self.game.get_autonomous_state(self.id)['action'],('rest','idle'))
        self.assertFalse(self.game.can_participate(self.id)['ok'])


class CombatAITests(unittest.TestCase):
    def test_every_difficulty_has_real_profile_and_legal_action(self):
        for ai in B.AI_PROFILES:
            with self.subTest(ai=ai):
                combat=make_battle()
                decision=B.choose_ai_decision(combat,ai,random.Random(20))
                self.assertEqual(decision['ai'],ai)
                self.assertIn('strategy',decision)
                self.assertIn('reason',decision)
                self.assertGreater(decision['legal_count'],0)
                self.assertIn(decision['action'], B.legal_actions(combat,decision['action']['actor']))

    def test_tutorial_ai_always_attacks(self):
        combat=make_battle()
        for i in range(20):
            decision=B.choose_ai_decision(combat,'tutorial',random.Random(i))
            self.assertEqual(decision['action']['kind'],'attack')

    def test_rules_ai_heals_critical_ally(self):
        combat=make_battle()
        combat['enemy'][0]['hp']=25
        decision=B.choose_ai_decision(combat,'rules',random.Random(3))
        self.assertEqual(decision['action']['kind'],'special')
        self.assertEqual(decision['action']['actor'],'E_h')
        self.assertEqual(decision['action']['target'],'E_t')

    def test_rules_ai_chooses_shield_for_low_ally_without_healer(self):
        combat=make_battle()
        combat['enemy'][0]['hp']=30
        combat['enemy'][1]['hp']=combat['enemy'][1]['stats']['hp']
        combat['enemy'][1]['acted']=True  # healer has already acted
        decision=B.choose_ai_decision(combat,'rules',random.Random(4))
        self.assertEqual(decision['action']['kind'],'special')
        self.assertEqual(decision['action']['actor'],'E_t')

    def test_lookahead_expands_more_than_a_single_greedy_action(self):
        combat=make_battle()
        with patch.object(B,'_sample_tactical_value',wraps=B._sample_tactical_value) as explore:
            B.choose_ai_decision(combat,'lookahead',random.Random(2))
            self.assertGreater(explore.call_count,2)

    def test_ai_uses_two_different_actors_and_respects_cooldown(self):
        combat=make_battle()
        used=[]
        for _ in range(2):
            move=B.choose_ai_action(combat,'rules',random.Random(42))
            self.assertNotIn(move['actor'],used)
            used.append(move['actor'])
            B.perform(combat,move['actor'],move['kind'],move['target'],random.Random(42))
        self.assertEqual(len(used),2)
        self.assertEqual(combat['actions'],2)
        self.assertIsNone(B.choose_ai_action(combat,'rules',random.Random(42)))

    def test_enemy_turn_log_contains_ai_decision_traces(self):
        with tempfile.TemporaryDirectory() as d:
            clock=FakeClock()
            game=GameService(Path(d)/'test.db',now=clock,rng=random.Random(42))
            ids=[row['id'] for row in game.get_animals()]
            game.start_battle('tutorial',ids)
            result=game.end_player_turn()
            trace=(result['battle'] or {}).get('log') or result['result']['log']
            decisions=[ev for ev in trace if ev['type']=='ai_decision']
            self.assertGreaterEqual(len(decisions),1)
            self.assertEqual(decisions[0]['ai'],'tutorial')
            self.assertEqual(decisions[0]['action']['kind'],'attack')
            self.assertEqual(len({ev['action']['actor'] for ev in decisions}),len(decisions))


if __name__=='__main__':
    unittest.main()
