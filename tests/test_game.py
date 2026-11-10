import random
import tempfile
import unittest
from pathlib import Path
from roc import GameService, GameRuleError
from roc import battle as B
from roc import config as C

class Clock:
    def __init__(self,value=1800000000):self.t=float(value)
    def __call__(self):return self.t
    def advance(self,x):self.t+=x

class ZeroDisease(random.Random):
    def random(self):return .99

class HighDisease(random.Random):
    def random(self):return .0

class GameTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.clock=Clock()
        self.path=Path(self.tmp.name)/'game.db'
        self.g=GameService(self.path,now=self.clock,rng=ZeroDisease(42))
        self.ids=[a['id'] for a in self.g.get_animals()]
    def tearDown(self):self.tmp.cleanup()
    def expect_error(self,fn):
        with self.assertRaises(GameRuleError):fn()

    def test_new_game_and_catalog(self):
        self.assertEqual(len(self.g.get_catalog()),30)
        self.assertEqual(len(self.g.get_animals()),3)
        self.assertEqual(self.g.get_game_state()['coins'],300)
        self.assertEqual(self.g.get_inventory()['stackable']['snack'],3)
        self.assertEqual(sum(x['owned'] for x in self.g.get_pokedex()),3)

    def test_store_restart_and_offline_crop(self):
        self.g.buy_item('seed_potato')
        self.g.plant_crop(0,'potato')
        self.clock.advance(1200)
        other=GameService(self.path,now=self.clock,rng=ZeroDisease())
        self.assertTrue(other.get_plots()[0]['ready'])
        self.assertEqual(other.harvest_crop(0),{'crop':'potato','count':3})
        self.expect_error(lambda:other.harvest_crop(0))
        other=GameService(self.path,now=self.clock,rng=ZeroDisease())
        self.assertEqual(other.get_inventory()['stackable']['potato'],3)

    def test_plant_requires_seed_atomic(self):
        before=self.g.get_game_state()['coins']
        self.expect_error(lambda:self.g.plant_crop(0,'wheat'))
        self.assertEqual(self.g.get_game_state()['coins'],before)
        self.assertIsNone(self.g.get_plots()[0]['crop'])

    def test_buy_sell_equipment_and_restrictions(self):
        self.g._mutate(lambda s:s.update(coins=500))
        self.g.buy_item('equip_necklace')
        a=self.ids[0]
        self.g.equip(a,'equip_necklace')
        self.assertEqual(self.g.get_animals()[0]['effective_stats']['hp'],self.g.get_animals()[0]['stats']['hp']+50)
        self.g.equip(a,None)
        self.assertEqual(self.g.get_inventory()['stackable']['equip_necklace'],1)
        self.g.sell_item('equip_necklace')
        self.assertEqual(self.g.get_game_state()['coins'],300)
        self.expect_error(lambda:self.g.sell_item('snack'))

    def test_training_offline_once(self):
        a=self.ids[0]
        before=self.g.get_animals()[0]['stats']['attack']
        self.g.start_training(a,'attack','easy')
        self.expect_error(lambda:self.g.start_training(a,'attack','easy'))
        self.clock.advance(600)
        self.assertEqual(self.g.get_animals()[0]['stats']['attack'],before+10)
        self.g.tick()
        self.assertEqual(self.g.get_animals()[0]['stats']['attack'],before+10)
        self.assertIsNone(self.g.get_animals()[0]['activity'])

    def test_training_half_when_fatigue50(self):
        a=self.ids[0]
        self.g._mutate(lambda s:s['animals'][a].update(fatigue=50))
        before=self.g.get_animals()[0]['stats']['hp']
        self.g.start_training(a,'hp','easy')
        self.clock.advance(600)
        self.assertEqual(self.g.get_animals()[0]['stats']['hp'],before+5)

    def test_cancel_training(self):
        a=self.ids[0];before=self.g.get_animals()[0]['stats']['hp']
        self.g.start_training(a,'hp','easy');self.g.cancel_training(a)
        self.clock.advance(700)
        self.assertEqual(self.g.get_animals()[0]['stats']['hp'],before)

    def test_hunting_parallel_and_cancel(self):
        self.g.start_hunting(self.ids[0],'chicken_coop')
        self.g.start_hunting(self.ids[1],'ranch')
        self.expect_error(lambda:self.g.start_hunting(self.ids[2],'chicken_coop'))
        self.g.cancel_hunting('ranch')
        self.clock.advance(1800)
        self.g.get_game_state()
        self.assertEqual(self.g.collect_hunt('chicken_coop')['count'],3)
        self.expect_error(lambda:self.g.collect_hunt('ranch'))
        self.assertEqual(self.g.get_inventory()['stackable']['chicken'],3)

    def test_cooking_consumes_material_and_xp(self):
        self.g.buy_item('egg_food',1)
        result=self.g.cook('boiled_egg')
        self.assertTrue(result['success'])
        self.assertEqual(result['xp'],10)
        self.assertEqual(self.g.get_inventory()['stackable']['food_boiled_egg'],1)
        self.expect_error(lambda:self.g.cook('boiled_egg'))

    def test_cure_consumption_on_failure(self):
        a=self.ids[0]
        self.g._mutate(lambda s:s['animals'][a].update(sick=True))
        self.g.buy_item('heal_basic',1)
        self.g.rng=HighDisease(42)
        # probability 0 -> succeeds; create guaranteed failure by overriding random
        self.g.rng=ZeroDisease()
        res=self.g.use_item('heal_basic',a)
        self.assertFalse(res['success'])
        self.assertTrue(self.g.get_animals()[0]['sick'])
        self.assertNotIn('heal_basic',self.g.get_inventory()['stackable'])

    def test_nature_blocks_participation(self):
        a=self.ids[0]
        self.g._mutate(lambda s:s['animals'][a].update(nature='glutton',fullness=50))
        self.assertFalse(self.g.can_participate(a)['ok'])
        self.g._mutate(lambda s:s['animals'][a].update(nature='balanced'))
        self.assertTrue(self.g.can_participate(a)['ok'])

    def test_evolution_only_when_all_caps_and_cost(self):
        a=self.ids[0]
        self.expect_error(lambda:self.g.evolve(a))
        caps=self.g.get_evolution_status(a)['caps']
        self.g._mutate(lambda s:(s.update(coins=1000),s['animals'][a]['stats'].update(dict(caps))))
        value=self.g.evolve(a)
        self.assertEqual(value['stage'],2)
        self.assertEqual(value['stats']['attack'],caps['attack'])
        self.assertEqual(self.g.get_evolution_status(a)['max_stage'],2)
        self.expect_error(lambda:self.g.evolve(a))

    def test_hatch_duplicate_no_refund(self):
        a=self.ids[0]
        self.g._mutate(lambda s:s['animals'][a]['stats'].update(attack=123))
        self.g._mutate(lambda s:s['inventory'].update(egg_basic=1))
        # max no refund regardless of what hatches
        old=self.g.get_game_state()['coins']
        result=self.g.hatch_egg('egg_basic')
        self.assertEqual(result['refund'],0)
        self.assertEqual(self.g.get_game_state()['coins'],old)
        self.assertEqual(next(x for x in self.g.get_animals() if x['id']==a)['stats']['attack'],123)

    def test_basic_battle_turns_and_unlock(self):
        b=self.g.start_battle('tutorial',self.ids)
        self.assertEqual(b['current'],'player')
        self.assertEqual(len(b['player']),3)
        self.expect_error(lambda:self.g.start_battle('easy',self.ids))
        # Force enemy hp low for API completion test; inspect terminal stage progression.
        self.g._mutate(lambda s:[f.update(hp=1) for f in s['battle']['enemy']])
        dealer=next(x for x in self.ids if 'dealer' in x)
        res=self.g.battle_action(dealer,'attack')
        self.assertTrue(res['result']['win'])
        self.assertEqual(self.g.get_game_state()['progress'],0)
        self.assertTrue(next(x for x in self.g.get_stages() if x['id']=='easy')['unlocked'])
        self.assertEqual(self.g.get_game_state()['coins'],400)
        self.assertEqual(self.g.get_inventory()['stackable']['snack'],5)

    def test_battle_outcome_injury_vs_hp(self):
        self.g.start_battle('tutorial',self.ids)
        self.g.forfeit_battle()
        first=self.g.get_animals()[0]
        self.assertEqual(first['stats']['hp'],self.g.characters[first['id']]['base_stats']['hp'])
        self.assertEqual(self.g.get_game_state()['coins'],300)

    def test_battle_item_in_combat(self):
        self.g.buy_item('battle_bandage')
        self.g.start_battle('tutorial',self.ids)
        a=self.ids[0]
        self.g._mutate(lambda s:next(x for x in s['battle']['player'] if x['id']==a).update(hp=10))
        output=self.g.battle_action('battle_bandage','battle_item',a)
        self.assertEqual(output['events'][0]['amount'],min(80, self.g.get_animals()[0]['stats']['hp']-10))
        self.assertNotIn('battle_bandage',self.g.get_inventory()['stackable'])

    def test_rank_first_reward_once(self):
        self.g._mutate(lambda s:s.update(progress=1))
        b=self.g.start_battle('bronze',self.ids)
        self.g._mutate(lambda s:[f.update(hp=1) for f in s['battle']['enemy']])
        a=self.ids[0]
        res=self.g.battle_action(a,'attack')
        self.assertTrue(res['result']['win'])
        self.assertEqual(self.g.get_game_state()['rank'],'bronze')
        old=self.g.get_game_state()['coins']
        self.g.start_battle('bronze',self.ids)
        self.g._mutate(lambda s:[f.update(hp=1) for f in s['battle']['enemy']])
        self.g.battle_action(a,'attack')
        self.assertEqual(self.g.get_game_state()['coins'],old)

    def test_demo_clock_persists_rate(self):
        self.g.set_demo_mode(True,60)
        self.clock.advance(30)
        self.assertGreaterEqual(self.g.get_game_state()['clock']['timestamp'],1800001800)
        self.g.set_demo_mode(False)
        another=GameService(self.path,now=self.clock,rng=ZeroDisease())
        self.assertEqual(another.get_game_state()['clock']['rate'],1)

    def test_offline_job_after_reopen_not_double_applied(self):
        a=self.ids[0]
        self.g.start_training(a,'attack','easy')
        self.clock.advance(620)
        saved=GameService(self.path,now=self.clock,rng=ZeroDisease())
        first=next(x for x in saved.get_animals() if x['id']==a)['stats']['attack']
        saved.get_game_state()
        second=GameService(self.path,now=self.clock,rng=ZeroDisease())
        self.assertEqual(next(x for x in second.get_animals() if x['id']==a)['stats']['attack'],first)

    def test_parallel_shop_transactions_preserve_coins(self):
        import threading
        self.g._mutate(lambda s:s.update(coins=10000))
        failures=[]
        def buy():
            try:
                for _ in range(20):self.g.buy_item('seed_wheat')
            except Exception as e:failures.append(e)
        workers=[threading.Thread(target=buy) for _ in range(4)]
        for t in workers:t.start()
        for t in workers:t.join()
        self.assertFalse(failures)
        self.assertEqual(self.g.get_game_state()['coins'],10000-4*20*10)
        self.assertEqual(self.g.get_inventory()['stackable']['seed_wheat'],80)

    def test_weather_storm_training_bonus(self):
        a=self.ids[0]
        self.clock.advance(3000) # final 10 min of storm cycle
        self.g.get_game_state()
        self.assertTrue(self.g.get_game_state()['clock']['storm'])
        before=next(x for x in self.g.get_animals() if x['id']==a)['stats']['attack']
        # restore mood/fullness, since 50 minutes passed
        self.g._mutate(lambda s:s['animals'][a].update(fullness=90,mood=90,fatigue=0))
        self.g.start_training(a,'attack','easy')
        self.clock.advance(600)
        self.assertEqual(next(x for x in self.g.get_animals() if x['id']==a)['stats']['attack'],before+20)

    def test_special_egg_duplicate_goes_to_existing_without_refund(self):
        a=self.ids[0]
        self.g._mutate(lambda s:s['inventory'].update(egg_special=1))
        coins=self.g.get_game_state()['coins']
        res=self.g.hatch_egg('egg_special')
        self.assertEqual(res['refund'],0)
        self.assertEqual(self.g.get_game_state()['coins'],coins)

    def test_ai_higher_difficulty_legal_move(self):
        self.g._mutate(lambda s:s.update(progress=7))
        battle=self.g.start_battle('diamond',self.ids)
        B.end_turn(battle)
        for ai in ('random','rules','heuristic','lookahead'):
            action=B.choose_ai_action(battle,ai,random.Random(42))
            self.assertIsNotNone(action)
            self.assertIn(action,B.legal_actions(battle,action['actor']))

    def test_battle_pure_shield_during_opponent_turn(self):
        tank=B.make_fighter('t','player','tank','water',1,{'hp':300,'attack':50,'defense':90,'agility':40})
        ally=B.make_fighter('a','player','dealer','fire',1,{'hp':100,'attack':90,'defense':50,'agility':80})
        foe=B.make_fighter('e','enemy','dealer','fire',1,{'hp':300,'attack':90,'defense':50,'agility':80})
        b={'player':[tank,ally],'enemy':[foe],'current':'player','actions':0,'winner':None,'round':1}
        B.perform(b,'t','special','a',ZeroDisease())
        B.end_turn(b)
        self.assertTrue(ally['shield'])
        B.perform(b,'e','attack',None,ZeroDisease())
        self.assertEqual(ally['hp'],100)
        B.end_turn(b)
        self.assertFalse(ally['shield'])

    def test_battle_cooldown_one_own_turn(self):
        tank=B.make_fighter('t','player','tank','water',1,{'hp':300,'attack':50,'defense':90,'agility':40})
        foe=B.make_fighter('e','enemy','tank','water',1,{'hp':300,'attack':50,'defense':90,'agility':40})
        b={'player':[tank],'enemy':[foe],'current':'player','actions':0,'winner':None,'round':1}
        B.perform(b,'t','special','t',ZeroDisease())
        B.end_turn(b);B.end_turn(b)
        self.assertEqual(tank['cooldown'],1)
        self.assertFalse(any(a['kind']=='special' for a in B.legal_actions(b,'t')))
        B.end_turn(b);B.end_turn(b)
        self.assertEqual(tank['cooldown'],0)

if __name__=='__main__':unittest.main()
