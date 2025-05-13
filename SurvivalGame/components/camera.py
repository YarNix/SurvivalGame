import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent, AbstractEntity
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.const import *

class CameraComponent:
    """
    A camera following the main subject's movement
    """
    needs_update = True
    update_order = ORD_RENDER
    def __init__(self, render: LayeredRender):
        self.render = render

    def get_rect(self, subject: AbstractEntity):
        subject_pos = subject.get_component(SpriteComponent).rect.center
        scale = self.render.scale
        screen_rect = pg.Rect(0, 0, SCREEN_WIDTH / scale, SCREEN_HEIGHT / self.render.scale)
        return screen_rect.move_to(center=subject_pos)
    
    def update(self, entity: AbstractEntity, *_, **__):
        # Moving the render to focus on the entity
        camera_rect = self.get_rect(entity)
        for ground in self.render.sprites[LayerId.TILED]:
            camera_rect.clamp_ip(ground.rect)
        self.render.offset.update(pg.Vector2(X_SCREEN_CENTER, Y_SCREEN_CENTER) / self.render.scale - camera_rect.center)