"""Preserve original input fixtures while production controls use WASD/contextual E."""
from app import App as ProductionApp,ROOT,STEP,MODES,CONTROL_KEYS
from play_view import FIELD,PLAY_CLEAR
GAME_KEYS={k:k for k in ('left','right','up','down','space','e','f','g','x','q','z')}
GAME_KEYS.update(lshift='shift',rshift='shift')
class App(ProductionApp):
    game_keys=GAME_KEYS
    contextual_e=False
    directional_yaw=False
