from random import random
from SurvivalGame.components.abstract import AbstractEntity, PhysicComponent, SpriteComponent, EntityBase
from SurvivalGame.components.map import SpatialGrid
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg

class NonRigidBoundingBox(PhysicComponent):
    needs_update = True
    update_order = ORD_PHYSIC
    def __init__(self, bound: Point = (1, 1), direction: Point = (0, 0), speed: float = 200.0):
        self.bound = bound
        self.direction = pg.Vector2(direction)
        self.speed = speed
        self.collided_ents = []
    def update(self, entity: AbstractEntity, dt: float, *_, **kwargs): 
        self.collided_ents.clear()
        collide_grid = kwargs.get('collide_grid', None)
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            return
        if isinstance(collide_grid, SpatialGrid):
            TOLERANCE = 1e-4
            k_x = 1
            k_y = 1
            offset = self.direction * self.speed * dt
            spr_pos = sprite.rect.center
            box = pg.FRect(spr_pos - pg.Vector2(self.bound) / 2, self.bound)
            new_box = box.move(offset)
            for other_box, owner in collide_grid.get_collidables(spr_pos):
                if isinstance(owner, EntityBase):
                    if new_box.colliderect(other_box):
                        self.collided_ents.append(owner)
                    continue
                if not new_box.colliderect(other_box):
                    continue
                if box.colliderect(other_box):
                    # The entity is clipped into collidable.
                    # Skip it.
                    continue
                        
                if self.direction.x != 0:
                    dist = (other_box.left - box.right) if self.direction.x > 0 else (box.left - other_box.right)
                    if abs(dist) > TOLERANCE:
                        k_x = min(k_x, abs(dist / offset.x))
                    else:
                        k_x = 0
                if self.direction.y != 0:
                    dist = (other_box.top - box.bottom) if self.direction.y > 0 else (box.top - other_box.bottom)
                    if abs(dist) > TOLERANCE:
                        k_y = min(k_y, abs(dist / offset.y))
                    else:
                        k_y = 0

            # Updating movement
            offset.x *= k_x
            offset.y *= k_y

            collide_grid.remove(entity)
            sprite.rect.center += offset
            collide_grid.add(entity)
        else:
            sprite.rect.center += self.direction * self.speed * dt

class RigidBoundingBox(PhysicComponent):
    needs_update = True
    update_order = ORD_PHYSIC
    def __init__(self, bound: Point = (1, 1), direction: Point = (0, 0), speed: float = 200.0):
        self.bound = bound
        self.direction = pg.Vector2(direction)
        self.speed = speed
    def update(self, entity: AbstractEntity, dt: float, *_, **kwargs):
        collide_grid = kwargs.get('collide_grid', None)
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            return
        if isinstance(collide_grid, SpatialGrid):
            TOLERANCE = 1e-4
            k_x = 1
            k_y = 1
            offset = self.direction * self.speed * dt
            spr_pos = sprite.rect.center
            box = pg.FRect(spr_pos - pg.Vector2(self.bound) / 2, self.bound)
            new_box = box.move(offset)
            for other_box, owner in collide_grid.get_collidables(spr_pos):
                if owner is entity or (isinstance(owner, EntityBase) and NonRigidBoundingBox in owner.components):
                    continue
                if not new_box.colliderect(other_box):
                    continue
                # if box.colliderect(other_box):
                #     if owner is None:
                #         # The entity is clipped into collidable.
                #         # Skip it.
                #         continue
                #     elif isinstance(owner, EntityBase) and RigidBoundingBox in owner.components:
                #         # Entity is inside another entity
                #         # apply a force to seperate them
                #         other_sprite = owner.get_component(SpriteComponent, None)
                #         if other_sprite:
                #             sep_dir = pg.Vector2(spr_pos) - other_sprite.rect.center
                #         else:
                #             sep_dir = pg.Vector2()
                #         SEP_FORCE = 5
                #         if sep_dir == (0, 0):
                #             sep_dir.update(SEP_FORCE, 0)
                #             sep_dir.rotate_ip(random() * 360)
                #         else:
                #             sep_dir.scale_to_length(SEP_FORCE)
                #         #print(f'Detected {other_box} inside, applying {sep_dir}')
                #         self.direction += sep_dir
                #         offset = self.direction * self.speed * dt
                        
                if self.direction.x != 0:
                    dist = (other_box.left - box.right) if self.direction.x > 0 else (box.left - other_box.right)
                    if abs(dist) > TOLERANCE:
                        k_x = min(k_x, abs(dist / offset.x))
                    else:
                        k_x = 0
                if self.direction.y != 0:
                    dist = (other_box.top - box.bottom) if self.direction.y > 0 else (box.top - other_box.bottom)
                    if abs(dist) > TOLERANCE:
                        k_y = min(k_y, abs(dist / offset.y))
                    else:
                        k_y = 0

            # Updating movement
            offset.x *= k_x
            offset.y *= k_y

            collide_grid.remove(entity)
            sprite.rect.center += offset
            #print("moved", offset, end=" ")
            collide_grid.add(entity)
        else:
            sprite.rect.center += self.direction * self.speed * dt