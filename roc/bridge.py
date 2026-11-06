"""Pygame-facing command bridge. No imports of Pygame or GUI code.

The frontend can use ``bridge.call('command', key=..., ...)`` for *all* actions,
which always returns a JSON-compatible ``{'ok', 'data', 'error'}`` envelope.
No manual argument parsing, DB access, or direct state mutation in the GUI.
"""
from __future__ import annotations
from .service import GameService, GameRuleError


ALLOWED_COMMANDS = frozenset('''
    get_snapshot get_game_state get_animals get_catalog get_pokedex
    get_shop_catalog get_rules get_inventory get_autonomous_state
    get_evolution_status get_recipes get_plots get_hunts get_stages
    get_active_jobs get_ai_profiles get_battle get_battle_actions
    get_last_battle_result get_event_history get_achievements
    get_achievement_details get_statistics
    can_participate preview_stage
    buy_item sell_item use_item equip hatch_egg evolve
    start_training cancel_training expand_plot plant_crop harvest_crop
    start_hunting cancel_hunting collect_hunt cook
    start_battle battle_action end_player_turn forfeit_battle
    set_demo_mode save_game load_game reset_game tick recent_events
'''.split())


class GameBridge:
    def __init__(self, game: GameService):
        if not isinstance(game, GameService):
            raise TypeError('GameBridge requires a GameService instance')
        self.game = game

    def call(self, command: str, **params):
        if command not in ALLOWED_COMMANDS:
            return {'ok':False,'data':None,'error':{
                'code':'UNKNOWN_COMMAND','message':'지원하지 않는 게임 명령입니다.'}}
        try:
            data=getattr(self.game,command)(**params)
        except GameRuleError as exc:
            return {'ok':False,'data':None,'error':{
                'code':'RULE_REJECTED','message':str(exc)}}
        except (TypeError,ValueError) as exc:
            return {'ok':False,'data':None,'error':{
                'code':'INVALID_ARGUMENTS','message':str(exc)}}
        return {'ok':True,'data':data,'error':None}
