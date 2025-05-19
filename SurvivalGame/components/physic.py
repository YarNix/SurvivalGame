from random import random
from SurvivalGame.components.abstract import AbstractEntity, CollideTriggerComponent, PhysicComponent, SpriteComponent, EntityBase
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.state import StateComponent
from SurvivalGame.const import *
from SurvivalGame.typing import *
import pygame as pg

class BoundingBoxCollider(PhysicComponent):
    needs_update = True
    update_order = ORD_PHYSIC
    def __init__(self, bound: Point = (1, 1), direction: Point = (0, 0), speed: float = PhysicComponent.DEFAULT_SPEED, is_solid = True):
        self.solid = is_solid
        self.clip = True # Allow clipping when inside another collider
        self.bound = bound
        self.direction = pg.Vector2(direction)
        self.speed = speed
    def should_obj_collide(self, obj):
        """
        Check if object can collide with one another
        """
        if isinstance(obj, EntityBase):
            if not self.solid:
                return False
            other_state = obj.get_component(StateComponent, None)
            if other_state and other_state.health <= 0:
                return False
            other_collider = obj.get_component(BoundingBoxCollider, None)
            return other_collider is not None and other_collider.solid
        return True
    def should_ent_inside(self, ent: EntityBase):
        """
        Check if entity can be inside this entity
        """
        if not self.solid:
            return self.clip
        other_state = ent.get_component(StateComponent, None)
        if other_state and other_state.health <= 0:
            return True
        other_collider = ent.get_component(BoundingBoxCollider, None)
        return other_collider is None or not other_collider.solid
    def update(self, entity: AbstractEntity, dt: float, collide_grid = None, **_): 
        state = entity.get_component(StateComponent, None)
        if state and state.health <= 0:
            return
        sprite = entity.get_component(SpriteComponent, None)
        if sprite is None:
            return
        if not isinstance(collide_grid, SpatialGrid):
            sprite.rect.center += self.direction * self.speed * dt
            return
        TOLERANCE = 1e-4
        offset = self.direction * self.speed * dt
        kx = 1.0
        ky = 1.0
        box = pg.FRect(sprite.rect.center - pg.Vector2(self.bound) / 2, self.bound)
        offset_box = box.move(offset)
        for other_box, owner in collide_grid.get_collidables(sprite.rect.center):
            if owner is entity or not offset_box.colliderect(other_box):
                continue
            if box.colliderect(other_box):
                trigger = entity.get_component(CollideTriggerComponent, None)
                if trigger:
                    trigger.on_any_collided(owner)
                if isinstance(owner, EntityBase):
                    if self.should_ent_inside(owner):
                        continue
                    # Entity should not be inside another entity
                    # apply a force to seperate them
                    other_sprite = owner.get_component(SpriteComponent, None)
                    if other_sprite:
                        sep_dir = pg.Vector2(sprite.rect.center) - other_sprite.rect.center
                    else:
                        sep_dir = pg.Vector2()
                    SEP_FORCE = 3
                    if sep_dir == (0, 0):
                        sep_dir.update(SEP_FORCE, 0)
                        sep_dir.rotate_ip(random() * 360)
                    else:
                        sep_dir.scale_to_length(SEP_FORCE)
                    self.direction += sep_dir
                    offset.update(self.direction * self.speed * dt)
                    offset_box.update(box.move(offset)) 
                elif self.clip:
                    continue
            # Collision happened. Check if it should happen
            if not self.should_obj_collide(owner):
                continue
            if self.direction.x != 0:
                dist = (other_box.left - box.right) if self.direction.x > 0 else (box.left - other_box.right)
                if abs(dist) > TOLERANCE:
                    kx = min(kx, abs(dist / offset.x))
                else:
                    kx = 0.0
            if self.direction.y != 0:
                dist = (other_box.top - box.bottom) if self.direction.y > 0 else (box.top - other_box.bottom)
                if abs(dist) > TOLERANCE:
                    ky = min(ky, abs(dist / offset.y))
                else:
                    ky = 0

        # Updating movement
        offset.x *= kx
        offset.y *= ky

        collide_grid.remove(entity)
        sprite.rect.center += offset
        collide_grid.add(entity)

class BulletCollider(BoundingBoxCollider):
    def should_obj_collide(self, obj):
        return False