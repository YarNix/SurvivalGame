from enum import IntEnum
from typing import overload
from SurvivalGame.components.abstract import SpriteComponent
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg


class LayerId(IntEnum):
    DEFAULT = 0
    TILED = 1
    BEHIND = 2
    OBJECT = 3
    OVERLAY = 4

class LayeredRender:
    def __init__(self, scale = 1.0):
        self.sprites: dict[int, list[SpriteComponent]] = {}
        self.offset = pg.Vector2()
        self.scale = float(scale)
        self.screen = pg.Surface((SCREEN_WIDTH / self.scale, SCREEN_HEIGHT / self.scale))

    def add(self, spr: SpriteComponent, layer: LayerId = LayerId.DEFAULT):
        self.sprites.setdefault(layer, []).append(spr)
    
    def remove(self, spr: SpriteComponent, layer: LayerId = LayerId.DEFAULT):
        self.sprites[layer].remove(spr)

    def render(self, surface: pg.Surface):
        self.sprites.get(LayerId.OBJECT, []).sort(key=lambda spr: spr.rect.centery)

        for layer in sorted(self.sprites.keys()):
            if layer == LayerId.OVERLAY:
                continue
            sprites = self.sprites[layer]
            self.screen.blits((spr.image, spr.rect.move(self.offset)) for spr in sprites)
            # if layer == LayerId.OBJECT:
            #     for spr in sprites:
            #         dst = spr.rect.move(self.offset)
            #         pg.draw.line(self.screen, (255, 0, 0), (dst.left, dst.centery), (dst.right, dst.centery), 1)
        pg.transform.scale_by(self.screen, self.scale, surface)
        surface.blits((spr.image, spr.rect) for spr in self.sprites.get(LayerId.OVERLAY, []))

    @overload
    def to_screen(self, obj: Point) -> Point: ...
    @overload
    def to_screen(self, obj: Rect) -> Rect: ...

    def to_screen(self, obj: Point | Rect):
        """
        Translate the object in world coordinate to screen coordinate
        """
        if isinstance(obj, pg.Rect | pg.FRect):
            rect = obj.copy()
            rect.center = self.to_screen(obj.center)
            rect.scale_by_ip(self.scale)
            return rect
        else:
            point = (obj + self.offset)
            point *= self.scale
            return tuple(point)