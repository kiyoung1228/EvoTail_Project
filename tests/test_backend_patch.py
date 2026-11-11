"""Regression tests for yard persistence, timing-grade cooking and role caps.

Run: python -m unittest discover -s tests -v
"""
import json
import random
import tempfile
import unittest
from pathlib import Path

from roc import GameService, GameRuleError
from roc import battle as B
from roc import config as C
from roc.bridge import GameBridge


class Clock:
    def __init__(self):
        self.t=1800000000.0
    def __call__(self):
        return self.t
    def add(self,sec):
        self.t+=sec


class FixedRng(random.Random):
    def __init__(self, chance):
        super().__init__(123)
        self.chance=chance
    def random(self):
        return self.chance


class BackendPatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'save.db'
        self.clock=Clock()
        self.g=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        self.ids=list(self.g.state['animals'])

    def test_yard_defaults_to_empty_gui_fills_slots(self):
        snap=self.g.get_snapshot()
        self.assertEqual(snap['yard'],[])
        self.assertEqual(snap['yard_max'],5)
        self.assertEqual(self.g.get_rules()['yard_max'],5)

    def test_yard_reorder_and_empty_are_allowed(self):
        self.assertEqual(self.g.set_yard_animals([self.ids[2],self.ids[0]])['yard'],
                         [self.ids[2],self.ids[0]])
        self.assertEqual(self.g.get_yard_animals()['keys'],[self.ids[2],self.ids[0]])
        self.assertEqual(self.g.get_snapshot()['yard'],[self.ids[2],self.ids[0]])
        self.assertEqual(self.g.set_yard_animals([])['yard'],[])
        self.assertEqual(len(self.g.get_animals()),3)  # hiding != releasing

    def test_yard_rejects_duplicates_unowned_bad_type_without_changing_save(self):
        prev=self.g.get_snapshot()['yard']
        for keys in ([self.ids[0],self.ids[0]],['not_owned'], 'bad', [4], (self.ids[0],)):
            with self.subTest(keys=keys), self.assertRaises(GameRuleError):
                self.g.set_yard_animals(keys)
            self.assertEqual(self.g.get_snapshot()['yard'],prev)

    def test_yard_allows_five_but_not_six(self):
        additional=[k for k in self.g.characters if k not in self.ids][:4]
        self.g._mutate(lambda s:s['animals'].update({k:self.g._new_animal(k,s['clock']['virtual'])
                                                   for k in additional}))
        self.g.set_yard_animals(self.ids+additional[:2])
        self.assertEqual(len(self.g.get_snapshot()['yard']),5)
        with self.assertRaises(GameRuleError):
            self.g.set_yard_animals(self.ids+additional[:3])
        self.assertEqual(len(self.g.get_snapshot()['yard']),5)

    def test_yard_survives_restart(self):
        new_selection=[self.ids[1]]
        self.g.set_yard_animals(new_selection)
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        self.assertEqual(again.get_snapshot()['yard'],new_selection)

    def test_pre_patch_saves_without_yard_get_migrated(self):
        self.g._mutate(lambda s:s.pop('yard'))
        self.assertNotIn('yard',self.g.store.load())
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        self.assertEqual(again.get_snapshot()['yard'],[])
        self.assertEqual(again.store.load()['yard'],[])

    def test_legacy_six_selection_migrates_to_five_without_losing_animals(self):
        extra=[k for k in self.g.characters if k not in self.ids][:3]
        selected=self.ids+extra
        def legacy(s):
            s['animals'].update({k:self.g._new_animal(k,s['clock']['virtual']) for k in extra})
            s['yard']=selected
        self.g._mutate(legacy)
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        self.assertEqual(again.get_snapshot()['yard'],selected[:5])
        self.assertEqual(again.store.load()['yard'],selected[:5])
        self.assertEqual(len(again.get_animals()),6)

    def test_bridge_accepts_yard_command_and_preserves_json(self):
        bridge=GameBridge(self.g)
        answer=bridge.call('set_yard_animals',keys=self.ids[:2])
        self.assertTrue(answer['ok'])
        self.assertEqual(answer['data']['count'],2)
        self.assertEqual(bridge.call('get_snapshot')['data']['yard'],self.ids[:2])
        self.assertFalse(bridge.call('set_yard_animals',keys=['other'])['ok'])
        json.dumps(bridge.call('get_snapshot'),ensure_ascii=False)

    def test_undisplayed_animals_still_have_status_updates(self):
        self.g.set_yard_animals([self.ids[0]])
        before=self.g.state['animals'][self.ids[1]]['fullness']
        self.clock.add(C.PASSIVE_FULLNESS_EVERY)
        self.g.get_snapshot()
        self.assertLess(self.g.state['animals'][self.ids[1]]['fullness'],before)

    def test_cooking_legacy_call_defaults_to_good(self):
        self.g.buy_item('egg_food')
        self.g.rng=FixedRng(.99)
        result=self.g.cook('boiled_egg')
        self.assertTrue(result['success'])
        self.assertEqual(result['xp_gained'],10)
        self.assertEqual(result['xp'],10)
        self.assertEqual(self.g.get_inventory()['stackable']['food_boiled_egg'],1)
        self.assertEqual(result['grade'],'Good')
        self.assertEqual(result['result'],'success')

    def test_failed_cooking_gives_burned_food_not_xp(self):
        self.g.buy_item('egg_food')
        self.g.rng=FixedRng(0.0)
        res=self.g.cook('boiled_egg','Miss')
        self.assertFalse(res['success'])
        self.assertEqual(res['xp_gained'],0)
        self.assertEqual(res['xp'],0)
        self.assertEqual(self.g.get_inventory()['stackable']['burned_food'],1)

    def test_cooking_xp_and_levels_follow_star_times_ten(self):
        self.assertEqual(C.COOK_XP,{1:10,2:20,3:30,4:40,5:50})
        for xp, level in [(0,1),(99,1),(100,2),(299,2),(300,3),
                          (599,3),(600,4),(999,4),(1000,5)]:
            with self.subTest(xp=xp):
                self.g._mutate(lambda s:s.update(cook_xp=xp))
                self.assertEqual(self.g.get_recipes()['level'],level)
        self.assertEqual(self.g.get_rules()['cooking']['xp_per_star'][5],50)
        self.assertIn('rabbit_stew',self.g.get_recipes()['recipes'])  # no recipe locking added

    def test_cooking_rescue_metadata_by_star_and_level(self):
        rules=self.g.get_rules()['cooking']
        self.assertNotIn('base_failure',rules)
        self.assertNotIn('failure_reduction',rules)
        self.assertEqual(rules['miss_rescue_by_level'],[0,.1,.2,.3,.4])
        self.assertEqual(rules['miss_rescue_max_star'],3)
        for xp,chance in zip(C.COOK_LEVEL_XP,(0,.1,.2,.3,.4)):
            self.g._mutate(lambda s:s.update(cook_xp=xp))
            for recipe, r in self.g.get_recipes()['recipes'].items():
                with self.subTest(recipe=recipe,xp=xp):
                    expected=chance if r['stars']<=3 else 0.0
                    self.assertEqual(r['miss_rescue_chance'],expected)
                    self.assertAlmostEqual(r['miss_failure_chance'],1-expected)
                    self.assertNotIn('failure_chance',r)

    def _give_recipe_ingredients(self,recipe):
        self.g._mutate(lambda s: [self.g._add(s,item,n)
                                 for item,n in C.RECIPES[recipe]['ingredients'].items()])

    def test_perfect_cooking_via_bridge_awards_distinct_food_and_xp(self):
        self.g.buy_item('egg_food')
        response=GameBridge(self.g).call('cook',recipe='boiled_egg',judgment='perfect')
        self.assertTrue(response['ok'])
        res=response['data']
        self.assertTrue(res['success'])
        self.assertEqual(res['grade'],'Perfect')
        self.assertEqual(res['result'],'great_success')
        self.assertEqual(res['judgment'],'perfect')
        self.assertEqual(res['outcome'],'great')
        self.assertEqual(res['xp'],10)
        self.assertEqual(res['effect_multiplier'],1.5)
        self.assertEqual(res['effects']['fullness'],15)
        self.assertEqual(res['xp_gained'],10)
        self.assertEqual(res['item'],'food_perfect_boiled_egg')
        self.assertEqual(self.g.get_inventory()['stackable'][res['item']],1)
        self.assertNotIn('egg_food',self.g.get_inventory()['stackable'])
        json.dumps(response)

    def test_good_and_perfect_always_succeed_at_every_star_and_level(self):
        for recipe,r in C.RECIPES.items():
            stars=r['stars']
            for xp in C.COOK_LEVEL_XP:
                for grade in ('Perfect','Good'):
                    for roll in (0.0,.999):
                        with self.subTest(recipe=recipe,xp=xp,grade=grade,roll=roll):
                            self.g._mutate(lambda s:s.update(cook_xp=xp))
                            self._give_recipe_ingredients(recipe)
                            self.g.rng=FixedRng(roll)
                            result=self.g.cook(recipe,grade)
                            self.assertEqual(result['failure_chance'],0.0)
                            self.assertTrue(result['success'])
                            self.assertFalse(result['rescued'])
                            self.assertEqual(result['xp_gained'],stars*10)
                            self.assertEqual(result['xp'],stars*10)
                            self.assertEqual(result['total_xp'],xp+stars*10)
                            expected_item=('food_perfect_' if grade=='Perfect' else 'food_')+recipe
                            self.assertEqual(result['item'],expected_item)
                            self.assertEqual(result['result'],
                                             'great_success' if grade=='Perfect' else 'success')
                            self.assertEqual(result['outcome'],'great' if grade=='Perfect' else 'success')
                            self.assertEqual(result['effect_multiplier'],1.5 if grade=='Perfect' else 1.0)
                            inv=self.g.get_inventory()['stackable']
                            self.assertTrue(all(item not in inv for item in r['ingredients']))

    def test_miss_rescue_probability_and_no_xp_at_all_levels_and_stars(self):
        for recipe in ('boiled_egg','egg_roll','chicken_burger','fried_chicken','carbonara'):
            stars=C.RECIPES[recipe]['stars']
            for xp,chance in zip(C.COOK_LEVEL_XP,(0,.1,.2,.3,.4)):
                chance=chance if stars<=3 else 0.0
                for roll in (0.0,max(0.0,chance-.001),chance,.999):
                    expected=chance>0 and roll<chance
                    with self.subTest(recipe=recipe,xp=xp,roll=roll):
                        self.g._mutate(lambda s:s.update(cook_xp=xp))
                        self._give_recipe_ingredients(recipe)
                        before=self.g.get_inventory()['stackable']
                        self.g.rng=FixedRng(roll)
                        response=GameBridge(self.g).call('cook',recipe=recipe,judgment='miss')
                        self.assertTrue(response['ok'])
                        result=response['data']
                        self.assertEqual(result['grade'],'Miss')
                        self.assertEqual(result['rescued'],expected)
                        self.assertEqual(result['success'],expected)
                        self.assertEqual(result['result'],'success' if expected else 'failure')
                        self.assertEqual(result['outcome'],'rescued' if expected else 'burnt')
                        self.assertEqual(result['judgment'],'miss')
                        self.assertEqual(result['miss_rescue_chance'],chance)
                        self.assertAlmostEqual(result['failure_chance'],1-chance)
                        self.assertEqual(result['xp_gained'],0)
                        self.assertEqual(result['xp'],0)
                        self.assertEqual(result['total_xp'],xp)
                        self.assertEqual(result['level'],self.g.get_recipes()['level'])
                        item='food_'+recipe if expected else 'burned_food'
                        self.assertEqual(result['item'],item)
                        self.assertEqual(result['effect_multiplier'],1.0)
                        inv=self.g.get_inventory()['stackable']
                        self.assertEqual(inv[item],before.get(item,0)+1)
                        self.assertTrue(all(key not in inv for key in C.RECIPES[recipe]['ingredients']))

    def test_rescued_food_persists_as_normal_food_and_grants_no_xp(self):
        self.g._mutate(lambda s:s.update(cook_xp=1000))
        self._give_recipe_ingredients('chicken_burger')
        self.g.rng=FixedRng(0.0)
        result=self.g.cook('chicken_burger','Miss')
        self.assertTrue(result['rescued'])
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        self.assertEqual(again.get_recipes()['xp'],1000)
        self.assertEqual(again.get_inventory()['stackable']['food_chicken_burger'],1)
        self.assertNotIn('food_perfect_chicken_burger',again.get_inventory()['stackable'])
        key=self.ids[0]
        again._mutate(lambda s:s['animals'][key].update(fullness=0,mood=20,fatigue=50))
        fed=again.use_item('food_chicken_burger',key)
        self.assertEqual((fed['fullness'],fed['mood'],fed['fatigue']),(50,40,50))

    def test_miss_always_burns_even_with_best_rng_and_max_level(self):
        self.g._mutate(lambda s:s.update(cook_xp=1000))
        self._give_recipe_ingredients('carbonara')
        self.g.rng=FixedRng(.999)
        result=self.g.cook('carbonara','Miss')
        self.assertEqual(result['grade'],'Miss')
        self.assertEqual(result['result'],'failure')
        self.assertFalse(result['success'])
        self.assertEqual(result['failure_chance'],1.0)
        self.assertEqual(result['miss_rescue_chance'],0.0)
        self.assertFalse(result['rescued'])
        self.assertEqual(result['xp_gained'],0)
        self.assertEqual(result['xp'],0)
        self.assertEqual(result['total_xp'],1000)
        self.assertEqual(result['item'],'burned_food')
        self.assertEqual(self.g.get_inventory()['stackable']['burned_food'],1)
        self.assertNotIn('wheat',self.g.get_inventory()['stackable'])

    def test_invalid_grade_and_missing_ingredients_do_not_consume_inventory(self):
        self.g.buy_item('egg_food')
        before=self.g.get_inventory()
        bridge=GameBridge(self.g)
        for grade in ('Great','',None,[],3):
            with self.subTest(grade=grade):
                res=bridge.call('cook',recipe='boiled_egg',grade=grade)
                self.assertFalse(res['ok'])
                self.assertEqual(res['error']['code'],'RULE_REJECTED')
                self.assertEqual(self.g.get_inventory(),before)
        for recipe in ('carbonara','not_recipe'):
            self.assertFalse(bridge.call('cook',recipe=recipe,grade='Perfect')['ok'])
            self.assertEqual(self.g.get_inventory(),before)
        self.assertEqual(self.g.get_recipes()['xp'],0)

    def test_canonical_judgment_returns_attempt_xp_and_total_xp(self):
        self.g._mutate(lambda s:s.update(cook_xp=90))
        self._give_recipe_ingredients('boiled_egg')
        bridge=GameBridge(self.g)
        result=bridge.call('cook',recipe='boiled_egg',judgment='good')['data']
        self.assertEqual((result['outcome'],result['judgment'],result['xp'],
                          result['total_xp'],result['level']),('success','good',10,100,2))
        self.assertEqual(self.g.get_recipes()['xp'],100)
        self._give_recipe_ingredients('boiled_egg')
        before=self.g.get_inventory()
        for params in ({'judgment':None},{'judgment':'great'},
                       {'judgment':'good','grade':'Miss'}):
            result=bridge.call('cook',recipe='boiled_egg',**params)
            self.assertFalse(result['ok'])
            self.assertEqual(result['error']['code'],'RULE_REJECTED')
            self.assertEqual(self.g.get_inventory(),before)
        result=bridge.call('cook',recipe='boiled_egg',judgment='perfect')['data']
        self.assertEqual((result['outcome'],result['xp'],result['total_xp']),('great',10,110))

    def test_perfect_food_is_separate_and_saved_then_feeds_at_1_5x(self):
        self._give_recipe_ingredients('fried_chicken')
        self._give_recipe_ingredients('fried_chicken')
        self.g.cook('fried_chicken','Good')
        perfect=self.g.cook('fried_chicken','Perfect')
        self.assertEqual(perfect['effects'],{'fullness':105,'mood':45,'fatigue':-30})
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        inv=again.get_inventory()['stackable']
        self.assertEqual(inv['food_fried_chicken'],1)
        self.assertEqual(inv['food_perfect_fried_chicken'],1)
        key=self.ids[0]
        again._mutate(lambda s:s['animals'][key].update(fullness=0,mood=20,fatigue=50))
        regular=again.use_item('food_fried_chicken',key)
        self.assertEqual((regular['fullness'],regular['mood'],regular['fatigue']),(70,50,30))
        again._mutate(lambda s:s['animals'][key].update(fullness=0,mood=20,fatigue=50))
        great=again.use_item('food_perfect_fried_chicken',key)
        self.assertEqual((great['fullness'],great['mood'],great['fatigue']),(100,65,20))
        self.assertNotIn('food_perfect_fried_chicken',again.get_inventory()['stackable'])

    def test_perfect_food_clamps_and_can_sell_without_changing_base_price(self):
        self._give_recipe_ingredients('carbonara')
        self._give_recipe_ingredients('carbonara')
        first=self.g.cook('carbonara','Perfect')
        self.g.cook('carbonara','Perfect')
        key=self.ids[0]
        self.g._mutate(lambda s:s['animals'][key].update(fullness=90,mood=95,fatigue=10))
        result=self.g.use_item(first['item'],key)
        self.assertEqual((result['fullness'],result['mood'],result['fatigue']),(100,100,0))
        self.assertEqual(self.g.sell_item(first['item'])['earned'],C.RECIPES['carbonara']['sell'])
        self.assertNotIn(first['item'],self.g.get_inventory()['stackable'])

    def test_burned_food_effects_and_refusal_unchanged(self):
        self._give_recipe_ingredients('boiled_egg')
        self._give_recipe_ingredients('boiled_egg')
        self.g.cook('boiled_egg','Miss')
        self.g.cook('boiled_egg','Miss')
        key=self.ids[0]
        self.g._mutate(lambda s:s['animals'][key].update(fullness=30,mood=50,fatigue=20))
        result=self.g.use_item('burned_food',key)
        self.assertFalse(result['refused'])
        self.assertEqual((result['fullness'],result['mood'],result['fatigue']),(35,40,20))
        self.g.rng=FixedRng(0.0)
        result=self.g.use_item('burned_food',key)
        self.assertTrue(result['refused'])
        self.assertEqual((result['fullness'],result['mood'],result['fatigue']),(35,40,20))

    def test_cooking_catalog_and_timing_metadata(self):
        rules=self.g.get_rules()['cooking']
        self.assertEqual(rules['grades'],['Perfect','Good','Miss'])
        self.assertEqual(rules['judgments'],['perfect','good','miss'])
        timing=rules['timing']
        self.assertEqual(timing['timeout_seconds'],5)
        self.assertEqual(timing['perfect_half_width'],5)
        self.assertEqual(timing['good_half_width'],15)
        catalog=self.g.get_shop_catalog()
        for key,r in self.g.get_recipes()['recipes'].items():
            with self.subTest(recipe=key):
                self.assertEqual(r['travel_seconds'],timing['travel_seconds_by_star'][r['stars']])
                normal=catalog[r['regular_item']]
                perfect=catalog[r['perfect_item']]
                self.assertEqual(normal['effect_multiplier'],1.0)
                self.assertEqual(perfect['effect_multiplier'],1.5)
                self.assertIsNone(perfect['buy'])
                self.assertEqual(perfect['sell'],normal['sell'])
                self.assertEqual(perfect['effects'],{k:int(v*1.5) for k,v in normal['effects'].items()})

    def test_restarting_during_demo_uses_normal_offline_clock(self):
        self.g.set_demo_mode(True,rate=60)
        self.clock.add(10)
        earlier=self.g.get_game_state()['clock']['timestamp']
        self.assertEqual(earlier,1800000600)
        self.clock.add(25) # game closed without explicitly disabling demo
        again=GameService(self.path,now=self.clock,rng=FixedRng(.99))
        later=again.get_game_state()['clock']
        self.assertEqual(later['rate'],1.0)
        self.assertEqual(later['timestamp']-earlier,25)

    def test_evolution_caps_differ_by_role_and_are_used_as_conditions(self):
        ids={self.g.characters[k]['role']:k for k in self.ids}
        d=self.g.get_evolution_status(ids['dealer'])
        t=self.g.get_evolution_status(ids['tank'])
        h=self.g.get_evolution_status(ids['healer'])
        self.assertEqual(d['caps']['attack'],420)
        self.assertEqual(t['caps']['attack'],180)
        self.assertEqual(h['caps']['attack'],240)
        self.assertEqual(d['caps']['agility'],360)
        self.assertEqual(t['caps']['hp'],420)
        self.assertFalse(d['ready'])
        self.g._mutate(lambda s:(s.update(coins=2000),s['animals'][ids['dealer']]['stats'].update(d['caps'])))
        status=self.g.get_evolution_status(ids['dealer'])
        self.assertTrue(status['ready'])
        self.assertEqual(status['remaining'],{'hp':0,'attack':0,'defense':0,'agility':0})
        self.assertEqual(status['next_caps']['attack'],700)
        evo=self.g.evolve(ids['dealer'])
        self.assertEqual(evo['stats']['attack'],420)  # no resetting on evolution
        self.assertEqual(evo['stage'],2)
        self.assertFalse(self.g.get_evolution_status(ids['dealer'])['ready'])  # normal reaches max stage 2

    def test_special_three_stages_have_separate_caps(self):
        key='dealer_special_01'
        self.g._mutate(lambda s:(s['animals'].update({key:self.g._new_animal(key,s['clock']['virtual'])}),
                                 s.update(coins=10000)))
        first=self.g.get_evolution_status(key)
        self.assertEqual(first['max_stage'],3)
        self.g._mutate(lambda s:s['animals'][key]['stats'].update(first['caps']))
        self.g.evolve(key)
        second=self.g.get_evolution_status(key)
        self.assertEqual(second['caps']['attack'],700)
        self.assertEqual(second['next_caps']['attack'],1400)
        self.g._mutate(lambda s:s['animals'][key]['stats'].update(second['caps']))
        self.assertEqual(self.g.evolve(key)['stage'],3)
        third=self.g.get_evolution_status(key)
        self.assertIsNone(third['next_caps'])
        self.assertFalse(third['ready'])

    def test_one_living_fighter_does_not_lose(self):
        p=[B.make_fighter(str(i),'player','dealer','fire',1,{'hp':100,'attack':10,'defense':10,'agility':10}) for i in range(3)]
        e=[B.make_fighter(str(i+3),'enemy','dealer','fire',1,{'hp':100,'attack':10,'defense':10,'agility':10}) for i in range(3)]
        state={'player':p,'enemy':e,'winner':None}
        p[0]['hp']=0;p[1]['hp']=0
        B.update_winner(state)
        self.assertIsNone(state['winner'])
        p[2]['hp']=0
        B.update_winner(state)
        self.assertEqual(state['winner'],'enemy')


if __name__=='__main__':
    unittest.main()
