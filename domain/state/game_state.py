from enum import Enum


class GameState(Enum):
    INTRO = 1
    MENU_SCREEN = 2
    MENU = 3
    PLAYING = 4
    GAME_OVER = 5