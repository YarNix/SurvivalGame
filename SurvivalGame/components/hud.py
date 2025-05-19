from SurvivalGame.components.entity import EntityBase, Player
from SurvivalGame.components.state import StateComponent
from SurvivalGame.components.text import TextComponent
import pygame as pg

class HUD(EntityBase):
    def __init__(self, player: Player, font: pg.Font) -> None:
        super().__init__()
        self.player = player
        self.add_component(TextComponent, font, text="100", topleft=(0, 0))
    def update(self, **kwargs):
        self.get_component(TextComponent).text = str(self.player.get_component(StateComponent).health)
        return super().update(**kwargs)