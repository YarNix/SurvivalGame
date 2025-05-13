import pygame as pg
from SurvivalGame.const import *
from SurvivalGame.components.ui import Button

class MenuScene(pg.sprite.Group):
    def __init__(self, game):
        super().__init__()
        background = pg.sprite.Sprite(self)
        background.image = pg.transform.scale(pg.image.load(join(PT_IMAGE, "background.jpg")), (SCREEN_WIDTH, SCREEN_HEIGHT))
        background.rect = background.image.get_rect()
        Button(
            self,
            text="Play",
            font=game.text_font,
            pos=(X_SCREEN_CENTER, Y_SCREEN_CENTER),
            click=lambda: game.statemgr.setactive("game"),
            border_radius=5
            )
        