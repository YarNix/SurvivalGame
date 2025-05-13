from enum import IntEnum
from SurvivalGame.components.abstract import EntityBase
from SurvivalGame.components.animator import BasicAnimator, EnemyAnimator, PlayerAnimator
from SurvivalGame.components.controller import PlayerController
from SurvivalGame.components.physic import NonRigidBoundingBox, RigidBoundingBox
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
from SurvivalGame.components.state import PlayerStateComponent
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg

class Player(EntityBase):
    def __init__(self, spawn: Point, skin: str = 'Farmer 0'):
        super().__init__()
        self.add_component(BasicSprite, center=spawn)
        self.add_component(PlayerAnimator, SpriteSheetImage.from_yaml(join(PT_SPRITE, f'{skin}.png')))
        self.add_component(NonRigidBoundingBox, (10, 11), speed=100)
        self.add_component(PlayerController)
        self.add_component(PlayerStateComponent)

class Enemy(EntityBase):
    def __init__(self, skin: str, speed: float = 90.0, spawn: Point = (0, 0)):
        super().__init__()
        self.add_component(BasicSprite, center=spawn)
        self.add_component(EnemyAnimator, SpriteSheetImage.from_yaml(join(PT_SPRITE, f'{skin}.png')))
        self.add_component(RigidBoundingBox, (10, 11), speed = speed)