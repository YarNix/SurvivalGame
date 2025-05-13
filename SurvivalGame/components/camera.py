import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent, AbstractEntity
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.const import *

class Camera:
    """
    A simple class that simulate a camera following the main subject's movement
    """
    def __init__(self, subject: pg.sprite.Sprite, *others: pg.sprite.Sprite, background: pg.sprite.Sprite | None = None):
        self.subject = subject
        self.background = background
        self.others = [*others]
        if self.background is not None:
            self.others.append(self.background)

    def add(self, *others: pg.sprite.Sprite):
        self.others.extend(others)
    

    def update(self, offset: pg.Vector2):
        """
        Shifting the background sprites' rect to ensure the subject is visible

        The subject is assume to be in the screen center
        """
        # Scrolling the world in the opposite direction to simulate the subject movement
        offset = -offset
        new_map = self.background.rect.copy()
        new_map.center += offset
        local_offset = self.subject.rect.center - pg.Vector2(X_SCREEN_CENTER, Y_SCREEN_CENTER)

        # Bound the map within the screen and shift the subject center instead
        # Bounding the left side
        if new_map.left > 0:
            offset.x -= new_map.left
            local_offset.x -= new_map.left
        elif offset.x < 0 and local_offset.x < 0:
            rebound = local_offset.x - new_map.left
            if rebound > 0:
                local_offset.x = 0
                offset.x = -rebound
            else:
                offset.x = 0
                local_offset.x = rebound 
        # Bound the right side
        if new_map.right < SCREEN_WIDTH:
            bound = new_map.right - SCREEN_WIDTH
            offset.x -= bound
            local_offset.x -= bound
        elif offset.x > 0 and local_offset.x > 0:
            rebound = local_offset.x - (new_map.right - SCREEN_WIDTH)
            if rebound < 0:
                local_offset.x = 0
                offset.x = -rebound
            else:
                offset.x = 0
                local_offset.x = rebound
        # Bound the top side
        if new_map.top > 0:
            offset.y -= new_map.top
            local_offset.y -= new_map.top
        elif offset.y < 0 and local_offset.y < 0:
            rebound = local_offset.y - new_map.top
            if rebound > 0:
                local_offset.y = 0
                offset.y = -rebound
            else:
                offset.y = 0
                local_offset.y = rebound
        # Bound the bottom side
        if new_map.bottom < SCREEN_HEIGHT:
            bound = new_map.bottom - SCREEN_HEIGHT
            offset.y -= bound
            local_offset.y -= bound
        elif offset.y > 0 and local_offset.y > 0:
            rebound = local_offset.y - (new_map.bottom - SCREEN_HEIGHT)
            if rebound < 0:
                local_offset.y = 0
                offset.y = -rebound
            else:
                offset.y = 0
                local_offset.y = rebound

        for spr in self.others:
            spr.rect.center += offset
        self.subject.rect.center = (X_SCREEN_CENTER, Y_SCREEN_CENTER) + local_offset

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