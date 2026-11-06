"""Minimal integration pattern for UI developer: replace print with Pygame drawing.

Do not call this module automatically; main.py is the no-GUI smoke demo.
"""
from roc import GameService, GameRuleError
from roc.worker import GameWorker


def make_game():
    service=GameService('saves/game.db')
    worker=GameWorker(service)
    worker.start()
    return service,worker


def on_click_buy_seed(game):
    try:
        return {'ok':True,'data':game.buy_item('seed_potato',1)}
    except GameRuleError as error:
        return {'ok':False,'message':str(error)}


def on_click_training(game,selected_id):
    try:
        return {'ok':True,'data':game.start_training(selected_id,'attack','easy')}
    except GameRuleError as error:
        return {'ok':False,'message':str(error)}


def on_click_battle(game,selected_ids):
    try:
        return {'ok':True,'data':game.start_battle('tutorial',selected_ids)}
    except GameRuleError as error:
        return {'ok':False,'message':str(error)}
