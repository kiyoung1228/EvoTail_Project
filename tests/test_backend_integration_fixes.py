"""백엔드 규칙, 전투 결과와 짧은 오류 문구를 검증한다.

프로젝트 최상위 폴더에서 실행:
    python -m unittest discover -s tests -p test_backend_integration_fixes.py -v

임시 저장 파일만 사용하며 플레이어의 saves/game.db는 열지 않는다.
"""
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from roc import GameBridge, GameRuleError, GameService
from roc import config as C


class Clock:
    def __init__(self):
        self.value = 1_800_000_000.0

    def __call__(self):
        return self.value


class ReliableRandom(random.Random):
    def random(self):
        return .99


class FirstChoiceRandom(ReliableRandom):
    def choice(self, values):
        return values[0]


class BackendIntegrationFixTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / 'game.db'
        self.clock = Clock()
        self.game = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.ids = [a['id'] for a in self.game.get_animals()]
        self.game._mutate(lambda s: [a.update(nature='balanced') for a in s['animals'].values()])

    def start_battle(self, stage='easy'):
        self.game._mutate(lambda s: s.update(progress=0))
        return self.game.start_battle(stage, self.ids)

    def prepare_victory(self):
        def change(s):
            for enemy in s['battle']['enemy']:
                enemy['hp'] = 1
        self.game._mutate(change)

    def prepare_defeat(self):
        def change(s):
            battle = s['battle']
            battle['ai'] = 'tutorial'
            for enemy in battle['enemy']:
                enemy['role'] = 'dealer'
                enemy['stats']['attack'] = 100_000
            for animal in s['animals'].values():
                animal['fatigue'] = 7
        self.game._mutate(change)

    def test_rules_expose_json_friendly_independent_copies(self):
        response = GameBridge(self.game).call('get_rules')
        self.assertTrue(response['ok'])
        rules = response['data']
        exposed = {key:rules[key] for key in ('crops', 'hatching', 'hunts', 'disease_probability')}
        self.assertEqual(json.loads(json.dumps(exposed)), exposed)
        self.assertEqual(rules['crops'], {'duration_seconds':600, 'yield':3})
        self.assertEqual(rules['hatching']['egg_basic']['special_probability'], .10)
        self.assertEqual(rules['hatching']['egg_special'],
                         {'special_probability':.60, 'duplicate_probability_cap':.20})
        self.assertEqual(rules['disease_probability'], .30)
        self.assertEqual(rules['hunts'], self.game.get_hunts()['areas'])
        rules['hatching']['egg_basic']['special_probability'] = 0
        rules['hunts']['ranch']['completion_effects']['fatigue'] = 999
        self.assertEqual(C.HATCHING['egg_basic']['special_probability'], .10)
        self.assertEqual(C.HUNTS['ranch']['completion_effects']['fatigue'], 20)

    def test_crop_rules_and_execution_share_configuration(self):
        with patch.object(C, 'CROP_DURATION', 7), patch.object(C, 'CROP_YIELD', 5):
            rules = self.game.get_rules()['crops']
            self.game.buy_item('seed_potato')
            planted = self.game.plant_crop(0, 'potato')
            self.assertEqual(planted['end'] - self.clock.value, rules['duration_seconds'])
            self.clock.value += rules['duration_seconds']
            self.assertEqual(self.game.harvest_crop(0), {'crop':'potato', 'count':rules['yield']})

    def test_hatching_uses_exposed_initial_rarity_probability(self):
        self.game.rng = FirstChoiceRandom()
        for probability, expected in ((0.0, 'normal'), (1.0, 'special')):
            with self.subTest(probability=probability):
                with patch.dict(C.HATCHING['egg_basic'], special_probability=probability):
                    self.game._mutate(lambda s: s['inventory'].update(egg_basic=1))
                    self.assertEqual(self.game.get_rules()['hatching']['egg_basic']['special_probability'],
                                     probability)
                    result = self.game.hatch_egg('egg_basic')
                    self.assertEqual(self.game.characters[result['id']]['rarity'], expected)

    def test_special_egg_duplicate_branch_uses_exposed_cap(self):
        self.game.rng = FirstChoiceRandom()
        for cap, duplicate in ((1.0, True), (0.0, False)):
            with self.subTest(cap=cap):
                with patch.dict(C.HATCHING['egg_special'],
                                special_probability=0.0, duplicate_probability_cap=cap):
                    self.game._mutate(lambda s: s['inventory'].update(egg_special=1))
                    result = self.game.hatch_egg('egg_special')
                    self.assertEqual(result['duplicate'], duplicate)

    def test_special_egg_retains_cross_rarity_unowned_fallback(self):
        def own_specials(s):
            for key, info in self.game.characters.items():
                if info['rarity'] == 'special':
                    s['animals'][key] = self.game._new_animal(key, self.clock.value)
            s['inventory']['egg_special'] = 1
        self.game.rng = FirstChoiceRandom()
        self.game._mutate(own_specials)
        with patch.dict(C.HATCHING['egg_special'],
                        special_probability=1.0, duplicate_probability_cap=0.0):
            result = self.game.hatch_egg('egg_special')
        self.assertFalse(result['duplicate'])
        self.assertEqual(self.game.characters[result['id']]['rarity'], 'normal')

    def test_hunt_completion_uses_exposed_effects_and_disease_probability(self):
        effects = {'fullness':-7, 'mood':-3, 'fatigue':11}
        with patch.dict(C.HUNTS['chicken_coop'], completion_effects=effects), \
                patch.object(C, 'DISEASE_CHANCE', 1.0):
            rules = self.game.get_rules()
            self.assertEqual(rules['hunts']['chicken_coop']['completion_effects'], effects)
            self.assertEqual(rules['disease_probability'], 1.0)
            self.game.start_hunting(self.ids[0], 'chicken_coop')
            self.clock.value += C.HUNTS['chicken_coop']['duration']
            animal = next(a for a in self.game.get_animals() if a['id'] == self.ids[0])
            # 30분 사냥 중에는 시간 경과에 따른 상태 감소도 별도로 적용된다.
            self.assertEqual((animal['fullness'], animal['mood'], animal['fatigue']), (61, 74, 11))
            self.assertTrue(animal['sick'])
            self.assertTrue(self.game.get_hunts()['active']['chicken_coop']['ready'])

    def test_default_hunt_effects_cover_short_and_long_areas(self):
        for area, spec in self.game.get_hunts()['areas'].items():
            with self.subTest(area=area):
                expected = ({'fullness':-20, 'mood':-10, 'fatigue':35}
                            if spec['duration'] == 3600 else
                            {'fullness':-10, 'mood':-5, 'fatigue':20})
                self.assertEqual(spec['completion_effects'], expected)

    def test_training_completion_reports_actual_capped_gain(self):
        key = self.ids[0]
        cap = self.game.caps[self.game.characters[key]['role']][1]['attack']
        self.game._mutate(lambda s: s['animals'][key]['stats'].update(attack=cap-1))
        self.game.start_training(key, 'attack', 'easy')
        self.clock.value += 600
        animal = next(a for a in self.game.get_animals() if a['id'] == key)
        event = next(e for e in self.game.recent_events() if e['type'] == 'training_complete')
        self.assertEqual(animal['stats']['attack'], cap)
        self.assertEqual(event['gain'], 1)

    def test_forfeit_reason_and_existing_penalties_survive_restart(self):
        self.start_battle()
        self.game._mutate(lambda s: [a.update(fatigue=7) for a in s['animals'].values()])
        result = self.game.forfeit_battle()
        self.assertEqual((result['end_reason'], result['winner'], result['win']),
                         ('forfeit', 'enemy', False))
        for animal in self.game.get_animals():
            self.assertEqual((animal['fullness'], animal['mood'], animal['fatigue']), (60, 65, 100))
            self.assertFalse(animal['sick'])
        event = next(e for e in self.game.recent_events() if e['type'] == 'battle_end')
        self.assertEqual(event['end_reason'], 'forfeit')
        restored = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        self.assertEqual(restored.get_last_battle_result(), result)
        persisted = [e for e in restored.get_event_history() if e['type'] == 'battle_end']
        self.assertEqual(persisted[-1]['end_reason'], 'forfeit')

    def test_natural_victory_reason_keeps_existing_reward_and_penalties(self):
        self.start_battle()
        self.prepare_victory()
        response = self.game.battle_action(self.ids[0])
        result = response['result']
        self.assertEqual((result['end_reason'], result['winner'], result['win']),
                         ('victory', 'player', True))
        self.assertEqual(result['reward'], C.STAGES['easy']['reward'])
        for animal in self.game.get_animals():
            self.assertEqual((animal['fullness'], animal['mood'], animal['fatigue']), (70, 75, 30))

    def test_natural_defeat_reason_keeps_existing_penalties(self):
        self.start_battle()
        self.prepare_defeat()
        response = self.game.end_player_turn()
        self.assertIsNone(response['battle'])
        self.assertEqual(response['result']['end_reason'], 'defeat')
        for animal in self.game.get_animals():
            self.assertEqual((animal['fullness'], animal['mood'], animal['fatigue']), (60, 65, 100))

    def test_tutorial_forfeit_keeps_state_immunity(self):
        self.start_battle('tutorial')
        before = {a['id']:(a['fullness'], a['mood'], a['fatigue'], a['sick'])
                  for a in self.game.get_animals()}
        with patch.object(C, 'DISEASE_CHANCE', 1.0):
            result = self.game.forfeit_battle()
        self.assertEqual(result['end_reason'], 'forfeit')
        after = {a['id']:(a['fullness'], a['mood'], a['fatigue'], a['sick'])
                 for a in self.game.get_animals()}
        self.assertEqual(after, before)

    def test_equipment_changes_remain_blocked_for_battle_participants(self):
        self.start_battle()
        with self.assertRaises(GameRuleError):
            self.game.equip(self.ids[0])

    def test_turn_events_include_ai_without_changing_player_events(self):
        self.start_battle('tutorial')
        first = self.game.battle_action(self.ids[0], 'defend', self.ids[0])
        self.assertEqual(first['turn_events'], first['events'])
        before = len(first['battle']['log'])
        second = self.game.battle_action(self.ids[1], 'defend', self.ids[1])
        self.assertEqual(second['events'], [{'type':'guard', 'actor':self.ids[1],
                                            'target':self.ids[1], 'damage_multiplier':.5}])
        self.assertEqual(second['turn_events'], second['battle']['log'][before:])
        self.assertTrue(any(e['type'] == 'ai_decision' for e in second['turn_events']))
        self.assertEqual(second['turn_events'][:len(second['events'])], second['events'])

    def test_ending_turn_returns_all_ai_events(self):
        self.start_battle('tutorial')
        response = self.game.end_player_turn()
        self.assertEqual(response['turn_events'], response['battle']['log'])
        self.assertTrue(any(e['type'] == 'ai_decision' for e in response['turn_events']))

    def test_winning_action_keeps_delta_after_terminal_log_truncation(self):
        self.start_battle()
        self.prepare_victory()
        old = [{'type':'old', 'index':i} for i in range(250)]
        self.game._mutate(lambda s: s['battle'].update(log=copy.deepcopy(old)))
        response = self.game.battle_action(self.ids[0])
        self.assertIsNone(response['battle'])
        self.assertEqual(len(response['result']['log']), 200)
        self.assertEqual(response['turn_events'], response['events'])
        self.assertEqual(len(response['turn_events']), 3)
        self.assertTrue(all(e['type'] == 'hit' for e in response['turn_events']))
        self.assertEqual(response['result']['log'][-3:], response['turn_events'])

    def test_defeating_ai_turn_keeps_delta_after_terminal_log_truncation(self):
        self.start_battle()
        self.prepare_defeat()
        self.game._mutate(lambda s: s['battle'].update(log=[{'type':'old'} for _ in range(250)]))
        response = self.game.end_player_turn()
        self.assertIsNone(response['battle'])
        self.assertEqual(len(response['result']['log']), 200)
        delta = response['turn_events']
        self.assertEqual(delta[0]['type'], 'ai_decision')
        self.assertEqual(len([e for e in delta if e['type'] == 'hit']), 3)
        self.assertFalse(any(e['type'] == 'old' for e in delta))
        self.assertEqual(response['result']['log'][-len(delta):], delta)

    def test_second_action_keeps_player_and_terminal_ai_delta(self):
        self.start_battle()
        self.game.battle_action(self.ids[0], 'defend', self.ids[0])
        self.prepare_defeat()
        self.game._mutate(lambda s: s['battle'].update(log=[{'type':'old'} for _ in range(250)]))
        response = self.game.battle_action(self.ids[1], 'defend', self.ids[1])
        self.assertIsNone(response['battle'])
        self.assertEqual(response['result']['end_reason'], 'defeat')
        self.assertEqual(len(response['result']['log']), 200)
        delta = response['turn_events']
        self.assertEqual(delta[:len(response['events'])], response['events'])
        self.assertEqual(response['events'][0]['type'], 'guard')
        self.assertEqual(delta[1]['type'], 'ai_decision')
        self.assertEqual(len([e for e in delta if e['type'] == 'hit']), 3)
        self.assertFalse(any(e['type'] == 'old' for e in delta))
        self.assertEqual(response['result']['log'][-len(delta):], delta)

    def assert_rejected(self, command, message, *, code='RULE_REJECTED', **params):
        before = copy.deepcopy(self.game.state)
        response = GameBridge(self.game).call(command, **params)
        self.assertFalse(response['ok'])
        self.assertIsNone(response['data'])
        self.assertEqual(response['error'], {'code':code, 'message':message})
        self.assertEqual(self.game.state, before)

    def test_short_purchase_and_inventory_errors_do_not_spend_resources(self):
        self.assert_rejected('buy_item', '코인 부족', item='equip_claw')
        self.assert_rejected('sell_item', '아이템 수량 부족', item='equip_claw')

    def test_short_harvest_and_cooking_errors_keep_crop_and_ingredients(self):
        self.game.buy_item('seed_potato')
        self.game.plant_crop(0, 'potato')
        self.assert_rejected('harvest_crop', '아직 수확 불가', index=0)
        self.assert_rejected('cook', '요리 재료 부족', recipe='boiled_egg', judgment='good')

    def test_short_participation_reasons_match_snapshot_and_action_rejections(self):
        key = self.ids[0]
        cases = [
            ({'sick':True}, '아파서 활동 불가'),
            ({'fullness':20}, '상태 나쁨'),
            ({'nature':'glutton', 'fullness':40}, '먹보: 좋은 포만감 필요'),
            ({'nature':'sleepy', 'fatigue':40}, '잠꾸러기: 더 휴식 필요'),
            ({'nature':'playful', 'mood':40}, '장난꾸러기: 좋은 기분 필요'),
            ({'nature':'picky', 'fullness':40, 'mood':40}, '까칠: 보통 상태 2개 이상'),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                def prepare(s):
                    s['animals'][key].update(nature='balanced', fullness=80, mood=80,
                                             fatigue=0, sick=False, activity=None)
                    s['animals'][key].update(changes)
                self.game._mutate(prepare)
                participation = self.game.can_participate(key)
                self.assertEqual(participation, {'ok':False, 'reason':message})
                animal = next(a for a in self.game.get_snapshot()['animals'] if a['id'] == key)
                self.assertFalse(animal['participation'])
                self.assertEqual(animal['participation_reason'], message)
                self.assert_rejected('start_training', message, key=key,
                                     stat='attack', difficulty='easy')

    def test_short_busy_message_keeps_training_and_inventory_unchanged(self):
        self.game.start_training(self.ids[0], 'attack', 'easy')
        self.assert_rejected('start_training', '다른 활동 중', key=self.ids[0],
                             stat='defense', difficulty='easy')
        self.assert_rejected('use_item', '활동 중 아이템 사용 불가',
                             key=self.ids[0], item='snack')

    def test_short_battle_action_errors_keep_existing_rule_error_code(self):
        self.start_battle('tutorial')
        self.assert_rejected('battle_action', '없는 전투 동물', actor='missing')
        actor = self.ids[0]
        self.game.battle_action(actor, 'defend', actor)
        self.assert_rejected('battle_action', '지금 사용할 수 없는 행동·대상', actor=actor)

    def test_short_battle_item_error_keeps_existing_argument_code_and_inventory(self):
        self.start_battle('tutorial')
        self.game._mutate(lambda s: s['inventory'].update(battle_bandage=1))
        self.assert_rejected('battle_action', '회복할 수 없는 대상', code='INVALID_ARGUMENTS',
                             actor='battle_bandage', kind='battle_item', target=self.ids[0])
        self.assertEqual(self.game.get_inventory()['stackable']['battle_bandage'], 1)

    def test_short_save_conflict_message_preserves_reload_guidance(self):
        other = GameService(self.path, now=self.clock, rng=ReliableRandom(7))
        other.buy_item('seed_wheat')
        self.assert_rejected('buy_item', '다른 게임에서 저장 파일 변경됨 · 먼저 불러오기',
                             item='seed_potato')

    def test_short_confirmation_and_speed_errors_preserve_state(self):
        self.assert_rejected('reset_game', '새 게임 시작 확인 필요')
        self.assert_rejected('set_demo_mode', '배속 켜기·끄기 값 오류', enabled='yes')
        self.assert_rejected('set_demo_mode', '배속은 1~3600배', enabled=True, rate=0)


if __name__ == '__main__':
    unittest.main()
