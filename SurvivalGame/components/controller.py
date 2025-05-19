from SurvivalGame.components.abstract import PhysicComponent, AbstractEntity
from SurvivalGame.const import *
import pygame as pg

class PlayerController:
    needs_update = True
    update_order = ORD_INPUT
    def __init__(self):
        self.input_dir = pg.Vector2()
    def update(self, entity: AbstractEntity, events: list[pg.Event], **_):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    self.input_dir.y += -1
                elif event.key == pg.K_s:
                    self.input_dir.y += 1
                elif event.key == pg.K_a:
                    self.input_dir.x += -1
                elif event.key == pg.K_d:
                    self.input_dir.x += 1
            elif event.type == pg.KEYUP:
                if event.key == pg.K_w:
                    self.input_dir.y += 1
                elif event.key == pg.K_s:
                    self.input_dir.y += -1
                elif event.key == pg.K_a:
                    self.input_dir.x += 1
                elif event.key == pg.K_d:
                    self.input_dir.x += -1
        
        physic = entity.get_component(PhysicComponent, None)
        if physic:
            physic.direction.update(self.input_dir.normalize() if self.input_dir.length_squared() != 0 else self.input_dir)
        