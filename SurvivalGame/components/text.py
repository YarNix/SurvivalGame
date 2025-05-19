from SurvivalGame.components.abstract import AbstractEntity, SpriteComponent
from SurvivalGame.components.render import LayerId
from SurvivalGame.components.sprites import BasicSprite, generate_missing_surface
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg



class TextComponent(SpriteComponent):
    LAYER = LayerId.OVERLAY
    def __init__(self, font: pg.Font, text = "__unset__", color: pg.typing.ColorLike = CL_WHITE, **kwargs) -> None:
        self.font = font
        self.__text = text
        self.image = font.render(text, True, color)
        self.rect = self.image.get_frect(**kwargs)
        self.color = color
    
    @property
    def text(self):
        return self.__text
    
    @text.setter
    def text(self, value):
        self.__text = value
        self.image = self.font.render(self.__text, True, self.color)
        self.rect.update(self.rect.topleft, self.image.get_frect().size)

class AttachedText(TextComponent):
    LAYER = LayerId.ABOVE
    needs_update = True
    def __init__(self, font: pg.Font, text="__unset__", color: pg.typing.ColorLike = CL_WHITE, offset: Point = (0, 0), **kwargs) -> None:
        super().__init__(font, text, color, **kwargs)
        self.offset = pg.Vector2(offset)

    def update(self, entity: AbstractEntity, **kwargs):
        sprite = entity.get_component(BasicSprite, None)
        if sprite is None:
            return
        self.rect.center = self.offset + sprite.rect.center
        