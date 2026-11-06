"""Rise of Champions v2 -- headless integrated verification.

Place in the folder containing main.py and run:
    python test_integrated_flow.py

This uses a temporary SQLite database and a controllable test clock. It never
modifies the player's saves/game.db. The tests are intentionally deterministic.
A small amount of temporary test-only state setup (via _mutate) accelerates
MAX evolution and makes enemy turns safe for cooldown checks.
"""
from __future__ import annotations

import random
import tempfile
from pathlib import Path

from roc import GameService, GameRuleError
from roc import config as C


class TestClock:
    def __init__(self, start=1_800_000_000.0):
        self.current = float(start)

    def __call__(self):
        return self.current

    def advance(self, seconds):
        self.current += seconds


class FixedRandom(random.Random):
    """Control independent 30% disease/50% or 90% cure rolls."""

    def __init__(self, value):
        super().__init__(123)
        self.value = value

    def random(self):
        return self.value


def test_case(title, fn):
    print(f"\n[TEST] {title}")
    fn()
    print(f"[PASS] {title}")


def fresh():
    work = tempfile.TemporaryDirectory(prefix="roc_integration_")
    clock = TestClock()
    path = Path(work.name) / "test.db"
    game = GameService(path, now=clock, rng=FixedRandom(.99))
    ids = {a['role']: a['id'] for a in game.get_animals()}
    return work, clock, path, game, ids


def get_animal(game, key):
    return next(a for a in game.get_animals() if a['id'] == key)


def expect_rule_error(fn, label):
    try:
        fn()
    except GameRuleError as exc:
        print(f"  Expected rejection: {label} -> {exc}")
        return
    raise AssertionError(f"Expected a GameRuleError: {label}")


def test_training_evolution_and_offline():
    work, clock, path, game, ids = fresh()
    try:
        key = ids['dealer']
        before = get_animal(game, key)['stats']['attack']
        game.start_training(key, 'attack', 'easy')
        expect_rule_error(lambda: game.start_training(key, 'hp', 'easy'), 'busy animal')
        # Re-open while offline: 10 minutes should complete exactly once.
        clock.advance(610)
        reopened = GameService(path, now=clock, rng=FixedRandom(.99))
        after = get_animal(reopened, key)
        assert after['stats']['attack'] == before + 10, (before, after['stats']['attack'])
        assert after['activity'] is None
        assert 0 <= after['fatigue'] <= 10  # 10 seconds idle after training -> some recovery
        again = GameService(path, now=clock, rng=FixedRandom(.99))
        assert get_animal(again, key)['stats']['attack'] == before + 10
        print(f"  Training: attack {before}->{after['stats']['attack']}; fatigue={after['fatigue']}; saved/reloaded")

        # Inject an end-of-stage test fixture to avoid hours of manual training.
        cap = C.CAPS['dealer'][1]
        def ready_for_evolution(s):
            s['coins'] = 1_200
            s['animals'][key]['stats'].update(cap)
        again._mutate(ready_for_evolution)
        assert again.get_evolution_status(key)['ready']
        result = again.evolve(key)
        assert result['stage'] == 2 and result['stats'] == cap
        assert result['coins'] == 1_200 - C.EVOLUTION_COST[2]
        print(f"  Evolution: stage=2, unchanged stats={result['stats']}, coins={result['coins']}")
        expect_rule_error(lambda: again.evolve(key), 'normal species cannot evolve past stage 2')
    finally:
        work.cleanup()


def test_sickness_and_treatments():
    work, clock, _, game, ids = fresh()
    try:
        key = ids['tank']
        game.rng = FixedRandom(0.0)  # guaranteed disease in this controlled test
        game.start_training(key, 'hp', 'easy')
        clock.advance(601)
        assert get_animal(game, key)['sick']
        assert not game.can_participate(key)['ok']
        print('  Forced disease: detected, blocks participation')

        game.buy_item('heal_basic')
        game.rng = FixedRandom(.99)  # guaranteed failed cure
        result = game.use_item('heal_basic', key)
        assert not result['success'] and result['sick']
        assert game.get_inventory()['stackable'].get('heal_basic', 0) == 0
        print('  Failed cure: potion consumed, disease persists')

        game.buy_item('heal_advanced')
        game.rng = FixedRandom(0.0)  # guaranteed successful cure
        result = game.use_item('heal_advanced', key)
        assert result['success'] and not result['sick']
        assert game.can_participate(key)['ok']
        print('  Successful cure: disease removed and participation restored')
    finally:
        work.cleanup()


def test_battle_turns_and_cooldowns():
    work, _, _, game, ids = fresh()
    try:
        team = list(ids.values())
        battle = game.start_battle('tutorial', team)
        assert len(battle['player']) == 3 and len(battle['enemy']) == 3
        assert battle['current'] == 'player'
        # Controlled fixture: enemy attacks are weak and enemy HP high, to ensure
        # the test observes multiple team turns instead of ending early.
        game._mutate(lambda s: [(f['stats'].update(attack=1, hp=999), f.update(hp=999))
                                for f in s['battle']['enemy']])
        tank, dealer = ids['tank'], ids['dealer']
        out = game.battle_action(tank, 'special', tank)
        assert any(e['type'] == 'shield' for e in out['events'])
        expect_rule_error(lambda: game.battle_action(tank, 'attack', game.get_battle()['enemy'][0]['id']),
                          'same fighter cannot act twice')
        game.battle_action(dealer, 'attack')  # uses second action, AI takes its turn
        battle = game.get_battle()
        assert battle is not None and battle['current'] == 'player'
        assert not any(a['kind'] == 'special' for a in game.get_battle_actions(tank)), \
            'Tank special should be unavailable on the very next own-team turn'
        print('  Two distinct actors per turn; repeat action rejected; special cooldown enforced')
        game.end_player_turn()
        assert any(a['kind'] == 'special' for a in game.get_battle_actions(tank)), \
            'Tank special should return after one own-team turn of cooldown'
        print('  Special becomes available after one skipped own-team turn')
    finally:
        work.cleanup()


def test_farm_hunt_and_inventory():
    work, clock, path, game, ids = fresh()
    try:
        game.buy_item('seed_potato')
        game.plant_crop(0, 'potato')
        game.start_hunting(ids['dealer'], 'chicken_coop')
        game.start_hunting(ids['tank'], 'ranch')
        expect_rule_error(lambda: game.start_hunting(ids['healer'], 'chicken_coop'),
                          'one animal per hunting area')
        clock.advance(1_800)
        reloaded = GameService(path, now=clock, rng=FixedRandom(.99))
        crop = reloaded.harvest_crop(0)
        chicken = reloaded.collect_hunt('chicken_coop')
        beef = reloaded.collect_hunt('ranch')
        assert crop['count'] == chicken['count'] == beef['count'] == 3
        expect_rule_error(lambda: reloaded.collect_hunt('chicken_coop'), 'no duplicate claim')
        inv = reloaded.get_inventory()['stackable']
        assert inv.get('potato') == 3 and inv.get('chicken') == 3 and inv.get('beef') == 3
        print('  After offline catch-up: potato=3, chicken=3, beef=3, no duplicate payout')
    finally:
        work.cleanup()


def test_autonomous_and_inventory_safety():
    work, clock, _, game, ids = fresh()
    try:
        key = ids['healer']
        old_inv = game.get_inventory()
        game._mutate(lambda s: s['animals'][key].update(nature='glutton', fullness=50,
                                                        mood=80, fatigue=0))
        clock.advance(61)
        status = game.get_autonomous_state(key)
        assert status['action'] == 'eat', status
        assert game.get_inventory() == old_inv, 'Foraging must not create free food or money'
        print(f"  Nature=glutton, fullness=50 -> {status['action']} ({status['reason']})")
    finally:
        work.cleanup()


def main():
    cases = [
        ('Training / evolution / save & offline', test_training_evolution_and_offline),
        ('Disease / potion loss on failure / cure', test_sickness_and_treatments),
        ('3vs3 turn limit / cooldown', test_battle_turns_and_cooldowns),
        ('Concurrent hunting / farming / one-time rewards', test_farm_hunt_and_inventory),
        ('Autonomous decision / no free resources', test_autonomous_and_inventory_safety),
    ]
    passed = 0
    for title, func in cases:
        try:
            test_case(title, func)
            passed += 1
        except Exception as exc:
            import traceback
            print(f'[FAIL] {title}: {exc}')
            traceback.print_exc()
    print(f'\nINTEGRATED TEST RESULT: {passed}/{len(cases)} passed')
    if passed != len(cases):
        raise SystemExit(1)
    print('All scenarios passed. Your normal saved game was not modified.')


if __name__ == '__main__':
    main()
