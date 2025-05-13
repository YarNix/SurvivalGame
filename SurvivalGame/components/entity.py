from SurvivalGame.components.abstract import EntityBase
from SurvivalGame.components.animator import BasicAnimator, PlayerAnimator
from SurvivalGame.components.controller import PlayerController
from SurvivalGame.components.physic import NonRigidBoundingBox, RigidBoundingBox
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
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

class Enemy(EntityBase):
    def __init__(self, spawn: Point, skin: str, speed: float = 90.0):
        super().__init__()
        self.add_component(BasicSprite, center=spawn)
        self.add_component(BasicAnimator, SpriteSheetImage.from_yaml(join(PT_SPRITE, f'{skin}.png')), 'Run')
        self.add_component(RigidBoundingBox, (10, 11), speed = speed)