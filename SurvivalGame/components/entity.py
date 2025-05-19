from enum import IntEnum
from SurvivalGame.components.abstract import EntityBase, SpriteComponent, SupportsEntityOperation
from SurvivalGame.components.animator import EnemyAnimator, PlayerAnimator
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.controller import PlayerController
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.physic import BoundingBoxCollider, BulletCollider
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
from SurvivalGame.components.state import StateComponent
from SurvivalGame.components.trigger import BulletTrigger, PlayerTrigger
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg
from random import random
import math

class Bullet(EntityBase):
    def __init__(self, position: Point, direction: Point = (0, 0)):
        super().__init__()
        sprite = SpriteSheetImage.from_yaml(join(PT_SPRITE, f'Props.png')).sprites['Bullet 0']
        rotation = math.atan2(direction[1], direction[0]) + math.pi / 2
        rotation = rotation * -180 / math.pi
        if rotation != 0:
            sprite = pg.transform.rotate(sprite, rotation)
        self.add_component(BasicSprite, sprite, layer=LayerId.OBJECT, center=position)
        self.add_component(BulletCollider, bound=(2, 2), direction=direction, speed=300, is_solid=False)
        self.add_component(BulletTrigger)
    def update(self, paused=False, scene: SupportsEntityOperation | None = None, **kwargs):
        if 'killing' in self.tags:
            if scene:
                scene.rem_entity(self, layer=LayerId.OBJECT)
            self._tags.remove('killing')
            return
        return super().update(paused, **kwargs)

class Player(EntityBase):
    def __init__(self, spawn: Point, skin: str = 'Farmer 0'):
        super().__init__()
        self.add_component(BasicSprite, layer=LayerId.OBJECT, center=spawn)
        self.add_component(BoundingBoxCollider, (10, 11), speed=150.0, is_solid=False)
        self.add_component(PlayerAnimator, SpriteSheetImage.from_yaml(join(PT_SPRITE, f'{skin}.png')))
        self.add_component(PlayerController)
        self.add_component(StateComponent)
        self.add_component(PlayerTrigger)

        self.attack_event = pg.event.custom_type()
        pg.time.set_timer(self.attack_event, 500)

    def update(self, paused = False, scene: SupportsEntityOperation | None = None, events: list[pg.Event] = [], collide_grid: SpatialGrid | None = None, **kwargs):
        super().update(paused = paused, scene = scene, events=events, collide_grid=collide_grid, **kwargs)
        if paused or scene is None or not events or collide_grid is None:
            return
        for event in events:
            if event.type == self.attack_event:
                scene.add_entity(self.spawn_bullet())

    def spawn_bullet(self):
        camera = self.get_component(CameraComponent, None)
        current_pos = self.get_component(BasicSprite).rect.center
        if camera is None:
            direction = pg.Vector2(1)
            direction.rotate_ip(random() * 360)
        else:
            render = camera.render
            direction = pg.Vector2(pg.mouse.get_pos()) - render.to_screen(current_pos)
            direction.normalize_ip()
        return Bullet(position=current_pos, direction=(direction.x, direction.y))
        
class EnemyType(IntEnum):
    UNKNOWN = 0
    WEAK_ZOMBIE = 1
    STRONG_ZOMBIE = 2
    WEAK_SKELETON = 3
    STRONG_SKELETON = 4
    GHOUL = 5

class Enemy(EntityBase):
    def __init__(self, type_name: EnemyType, skin: str, speed: float = BoundingBoxCollider.DEFAULT_SPEED, spawn: Point = (0, 0)):
        super().__init__()
        self.type_name = type_name
        self.add_component(BasicSprite, layer=LayerId.OBJECT, center=spawn)
        self.add_component(EnemyAnimator, SpriteSheetImage.from_yaml(join(PT_SPRITE, f'{skin}.png')))
        self.add_component(BoundingBoxCollider, (10, 11), speed = speed)
        self.add_component(StateComponent)
        self.add_tag('enemy')
    
    def update(self, paused=False, scene: SupportsEntityOperation | None = None, **kwargs):
        if 'killing' in self.tags:
            if scene:
                scene.rem_entity(self, layer=LayerId.OBJECT)
            self._tags.remove('killing')
            return
        return super().update(paused=paused, scene=scene, **kwargs)


