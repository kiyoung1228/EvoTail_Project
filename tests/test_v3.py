"""Regression suite for the v3 integration, save safety, catalog swap and GUI bridge."""
import json
import random
import tempfile
import threading
import unittest
from pathlib import Path

from roc import GameService, GameRuleError, GameBridge
from roc import battle as B, config as C
from roc.store import SQLiteStore


class FakeClock:
    def __init__(self, value=1800000000):
        self.value=float(value)
    def __call__(self):
        return self.value
    def add(self,seconds):
        self.value+=seconds


class ReliableRNG(random.Random):
    def random(self):
        return .99


class AlwaysHitRNG(random.Random):
    def random(self):
        return .99


class V3Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'world.db'
        self.clock=FakeClock()
        self.game=GameService(self.path,now=self.clock,rng=ReliableRNG(123))
        self.ids=[a['id'] for a in self.game.get_animals()]

    def test_gui_bridge_returns_json_friendly_one_snapshot(self):
        bridge=GameBridge(self.game)
        response=bridge.call('get_snapshot')
        self.assertTrue(response['ok'])
        state=response['data']
        self.assertEqual(state['coins'],300)
        self.assertEqual(len(state['animals']),3)
        self.assertIn('effective_stats',state['animals'][0])
        self.assertIn('remaining_seconds',state['plots'][0])
        self.assertEqual(len(state['stages']),9)
        self.assertIn('battle',state)
        json.dumps(response,ensure_ascii=False,allow_nan=False)
        state['animals'][0]['stats']['attack']=99999
        self.assertNotEqual(self.game.get_animals()[0]['stats']['attack'],99999)

    def test_bridge_unknown_and_validation_error_never_crashes_ui(self):
        bridge=GameBridge(self.game)
        self.assertEqual(bridge.call('unexpected')['error']['code'],'UNKNOWN_COMMAND')
        self.assertEqual(bridge.call('buy_item',item='equip_claw',quantity=999)['error']['code'],
                         'RULE_REJECTED')
        self.assertEqual(bridge.call('start_training',key=self.ids[0])['error']['code'],
                         'INVALID_ARGUMENTS')
        self.assertTrue(bridge.call('buy_item',item='seed_wheat')['ok'])
        self.assertEqual(self.game.get_inventory()['stackable']['seed_wheat'],1)

    def test_event_history_persists_across_restart_and_doesnt_double_log(self):
        self.game.buy_item('seed_wheat')
        self.game.plant_crop(0,'wheat')
        self.clock.add(610)
        self.game.get_snapshot()
        hist=self.game.get_event_history(100)
        self.assertTrue(any(ev['type']=='crop_ready' for ev in hist))
        before=sum(ev['type']=='crop_ready' for ev in hist)
        again=GameService(self.path,now=self.clock,rng=ReliableRNG())
        again.get_game_state()
        self.assertEqual(sum(ev['type']=='crop_ready' for ev in again.get_event_history(100)),before)
        self.assertEqual(before,1)

    def test_event_log_not_truncated_to_eighty_with_many_events_one_transaction(self):
        self.game._mutate(lambda s:[self.game._emit(s,'debug_test',index=i) for i in range(100)])
        history=self.game.get_event_history(200)
        self.assertEqual(sum(ev['type']=='debug_test' for ev in history),100)
        self.assertLessEqual(len(self.game.recent_events()),80)

    def test_save_conflict_detected_and_keeps_newer_changes(self):
        other=GameService(self.path,now=self.clock,rng=ReliableRNG())
        self.game.buy_item('seed_wheat')
        with self.assertRaisesRegex(GameRuleError,'저장 파일'):
            other.buy_item('seed_potato')
        other.load_game()
        self.assertTrue(other.buy_item('seed_potato'))
        inv=self.game.store.load()['inventory']
        self.assertIn('seed_potato',inv)
        self.assertIn('seed_wheat',inv)

    def test_role_stat_caps_loaded_from_json(self):
        data=json.loads((Path(__file__).resolve().parent.parent/'data/role_caps.json').read_text())
        data['dealer']['1']['hp']=180
        data['dealer']['1']['attack']=320
        caps=Path(self.tmp.name)/'caps.json'
        caps.write_text(json.dumps(data))
        new=GameService(Path(self.tmp.name)/'other.db',now=self.clock,
                        rng=ReliableRNG(),cap_path=caps)
        dealer=next(a for a in new.get_animals() if a['role']=='dealer')
        tank=next(a for a in new.get_animals() if a['role']=='tank')
        self.assertEqual(dealer['caps']['hp'],180)
        self.assertEqual(dealer['caps']['attack'],320)
        self.assertEqual(tank['caps']['attack'],data['tank']['1']['attack'])
        self.assertEqual(new.get_evolution_status(dealer['id'])['caps']['attack'],320)
        self.assertEqual(new.get_rules()['caps']['dealer'][1]['hp'],180)

    def test_invalid_caps_rejected_early(self):
        data=json.loads((Path(__file__).resolve().parent.parent/'data/role_caps.json').read_text())
        data['tank']['2']['hp']=1
        path=Path(self.tmp.name)/'wrong_caps.json';path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'cannot decrease'):
            GameService(Path(self.tmp.name)/'wrong.db',cap_path=path)

    def test_all_base_species_fit_first_stage_cap(self):
        for key,animal in self.game.get_catalog().items():
            caps=self.game.caps[animal['role']][1]
            self.assertTrue(all(animal['base_stats'][k]<=caps[k] for k in C.STATS))

    def test_all_crops_are_finite_and_use_seed(self):
        self.game._mutate(lambda s:s.update(coins=10000))
        for crop in C.CROPS:
            with self.subTest(crop=crop):
                self.game.buy_item('seed_'+crop)
                self.game.plant_crop(0,crop)
                self.clock.add(610)
                self.assertTrue(self.game.get_plots()[0]['ready'])
                res=self.game.harvest_crop(0)
                self.assertEqual(res['count'],3)
                with self.assertRaises(GameRuleError):
                    self.game.harvest_crop(0)
                self.assertGreaterEqual(self.game.get_inventory()['stackable'][crop],3)

    def test_all_recipes_have_catalog_items_and_ingredients(self):
        for key,spec in C.RECIPES.items():
            with self.subTest(recipe=key):
                self.assertIn('food_'+key,C.ITEMS)
                self.assertGreaterEqual(spec['sell'],0)
                for ingredient,n in spec['ingredients'].items():
                    self.assertIn(ingredient,C.ITEMS)
                    self.assertGreater(n,0)

    def test_no_free_item_use_while_in_training(self):
        self.game.start_training(self.ids[0],'attack','easy')
        with self.assertRaisesRegex(GameRuleError,'활동 중'):
            self.game.use_item('snack',self.ids[0])
        self.assertEqual(self.game.get_inventory()['stackable']['snack'],3)

    def test_hunt_ready_cannot_be_discarded_using_cancel(self):
        self.game.start_hunting(self.ids[0],'chicken_coop')
        self.clock.add(1801)
        with self.assertRaises(GameRuleError):
            self.game.cancel_hunting('chicken_coop')
        self.assertEqual(self.game.collect_hunt('chicken_coop')['count'],3)

    def test_achievement_updates_and_survives_restart(self):
        self.game.buy_item('seed_potato')
        self.game.plant_crop(0,'potato')
        self.clock.add(610)
        self.game.harvest_crop(0)
        flags=self.game.get_achievements()
        self.assertTrue(flags['first_crop'])
        self.assertFalse(flags['champion'])
        self.assertEqual(self.game.get_statistics()['crops_harvested'],3)
        again=GameService(self.path,now=self.clock,rng=ReliableRNG())
        self.assertTrue(again.get_achievements()['first_crop'])
        self.assertTrue(any(x['id']=='first_crop' and x['achieved']
                            for x in again.get_achievement_details()))

    def test_tank_healer_skill_and_defend_legal(self):
        team=self.game.get_animals()
        ids=[row['id'] for row in team]
        self.game.start_battle('tutorial',ids)
        for key in ids:
            actions=self.game.get_battle_actions(key)
            self.assertTrue(any(a['kind']=='attack' for a in actions))
            self.assertTrue(any(a['kind']=='defend' for a in actions))
        dealer=next(x for x in ids if 'dealer' in x)
        res=self.game.battle_action(dealer,'defend',dealer)
        battle=res['battle']
        guarded=next(x for x in battle['player'] if x['id']==dealer)
        self.assertTrue(guarded['guard'])
        with self.assertRaises(GameRuleError):
            self.game.battle_action(dealer,'defend',dealer)

    def test_guard_reduces_damage_but_absolute_shield_blocks_all(self):
        tank=B.make_fighter('tank','player','tank','water',1,{'hp':300,'attack':80,'defense':90,'agility':40})
        foe=B.make_fighter('enemy','enemy','tank','water',1,{'hp':300,'attack':100,'defense':90,'agility':40})
        base={'player':[tank],'enemy':[foe],'current':'player','actions':0,'winner':None,'round':1}
        B.perform(base,'tank','defend','tank',AlwaysHitRNG())
        B.end_turn(base)
        start_hp=tank['hp']
        hit=B.perform(base,'enemy','attack','tank',AlwaysHitRNG())
        self.assertTrue(hit[0]['guarded'])
        self.assertLess(hit[0]['damage'],B.calc_damage(foe,tank))
        self.assertEqual(tank['hp'],start_hp-hit[0]['damage'])
        B.end_turn(base)
        self.assertFalse(tank['guard'])
        B.perform(base,'tank','special','tank',AlwaysHitRNG())
        B.end_turn(base)
        blocked=B.perform(base,'enemy','attack','tank',AlwaysHitRNG())
        self.assertEqual(blocked[0]['type'],'blocked')

    def test_zero_or_negative_cost_and_stats_no_custom_catalog_mutations(self):
        before=self.game.get_game_state()['coins']
        for qty in (0,-1,1.5,True):
            with self.subTest(qty=qty):
                with self.assertRaises(GameRuleError):
                    self.game.buy_item('seed_wheat',quantity=qty)
        self.assertEqual(self.game.get_game_state()['coins'],before)

    def test_snapshot_changes_after_real_time_and_is_json(self):
        snap1=self.game.get_snapshot()
        self.clock.add(620)
        snap2=self.game.get_snapshot()
        self.assertGreater(snap2['clock']['timestamp'],snap1['clock']['timestamp'])
        self.assertLess(snap2['animals'][0]['fullness'],snap1['animals'][0]['fullness'])
        self.assertTrue(json.dumps(snap2,allow_nan=False))

    def test_store_contains_revision_and_event_history(self):
        store=SQLiteStore(self.path)
        data,rev1=store.load_with_revision()
        self.assertIsNotNone(data)
        self.game.buy_item('seed_wheat')
        _,rev2=store.load_with_revision()
        self.assertGreater(rev2,rev1)

    def test_gui_bridge_rejects_private_mutator_access(self):
        bridge=GameBridge(self.game)
        self.assertFalse(bridge.call('_mutate')['ok'])
        self.assertEqual(self.game.get_game_state()['coins'],300)

    def test_progress_initially_only_tutorial_unlocked(self):
        stages=self.game.get_stages()
        self.assertEqual([x['id'] for x in stages if x['unlocked']], ['tutorial'])
        self.game.start_battle('tutorial',self.ids)
        self.game._mutate(lambda s:[x.update(hp=1) for x in s['battle']['enemy']])
        dealer=next(x for x in self.ids if 'dealer' in x)
        result=self.game.battle_action(dealer,'attack',None)
        self.assertTrue(result['result']['win'])
        self.assertIn('easy',[x['id'] for x in self.game.get_stages() if x['unlocked']])

    def test_all_four_hunts_have_three_items_each(self):
        self.assertEqual(len(C.HUNTS),4)
        self.assertTrue(all(x['count']==3 for x in C.HUNTS.values()))

    def test_all_skills_rig_cooldown(self):
        # Confirm 2-team-turn limit doesn't allow repeated actions by same creature.
        ids=self.ids
        self.game.start_battle('tutorial',ids)
        a=next(x for x in ids if 'tank' in x)
        r=self.game.battle_action(a,'special',a)
        self.assertTrue(any(x['type']=='shield' for x in r['events']))
        with self.assertRaises(GameRuleError):
            self.game.battle_action(a,'attack','enemy_0')

    def test_multithreaded_gamebridge_shop_transactions(self):
        self.game._mutate(lambda s:s.update(coins=20000))
        bridge=GameBridge(self.game)
        outcomes=[]
        def task():
            for _ in range(20):
                outcomes.append(bridge.call('buy_item',item='seed_wheat')['ok'])
        threads=[threading.Thread(target=task) for _ in range(6)]
        for th in threads:th.start()
        for th in threads:th.join()
        self.assertTrue(all(outcomes))
        self.assertEqual(self.game.get_inventory()['stackable']['seed_wheat'],120)
        self.assertEqual(self.game.get_game_state()['coins'],18800)


if __name__=='__main__':
    unittest.main()


class NewGameTests(unittest.TestCase):
    def test_reset_requires_consent_resets_event_history_and_data(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'save.db'
            clock=FakeClock()
            g=GameService(p,now=clock,rng=ReliableRNG())
            g.buy_item('seed_wheat')
            with self.assertRaises(GameRuleError):
                g.reset_game()
            self.assertEqual(g.get_game_state()['coins'],290)
            result=g.reset_game(confirm=True)
            self.assertTrue(result['reset'])
            self.assertEqual(g.get_game_state()['coins'],300)
            self.assertNotIn('seed_wheat',g.get_inventory()['stackable'])
            self.assertEqual(g.get_event_history(),[])
            again=GameService(p,now=clock,rng=ReliableRNG())
            self.assertEqual(again.get_game_state()['coins'],300)

class WorkerIntegrationTests(unittest.TestCase):
    def test_worker_updates_completed_world_job_without_calling_ui(self):
        import time
        from roc.worker import GameWorker
        with tempfile.TemporaryDirectory() as d:
            clock=FakeClock()
            g=GameService(Path(d)/'world.db',now=clock,rng=ReliableRNG())
            g.buy_item('seed_potato')
            g.plant_crop(0,'potato')
            worker=GameWorker(g,interval=0.02)
            try:
                worker.start()
                clock.add(610)
                deadline=time.monotonic()+2
                notices=[]
                while time.monotonic()<deadline and not notices:
                    time.sleep(.03)
                    notices.extend(worker.poll(10))
                self.assertTrue(any(e['type']=='world_updated' for e in notices))
                self.assertTrue(g.get_plots()[0]['ready'])
                self.assertFalse(any(e['type']=='worker_error' for e in notices))
            finally:
                worker.stop()
            self.assertFalse(worker.thread.is_alive())
