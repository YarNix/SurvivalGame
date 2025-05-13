
from SurvivalGame.components.abstract import AbstractEntity, PhysicComponent
from SurvivalGame.const import *


class StateComponent:
    def __init__(self, health = 100, damaged = False, dead = False) -> None:
        self.health = health
        self.damage = damaged
        self.dead = dead

class PlayerStateComponent(StateComponent):
    needs_update = True
    update_order = ORD_POSTPHYSIC
    def __init__(self) -> None:
        super().__init__(health=100, damaged=False, dead=False)
        self.ignore_hits = {}

    def update(self, entity: AbstractEntity, dt: float, *args, **kwargs):
        for ent in self.ignore_hits:
            self.ignore_hits[ent] -= dt

        collided: list[AbstractEntity] = getattr(entity.get_component(PhysicComponent), 'collided_ents', [])
        if collided:
            for ent in collided:
                if ent is entity:
                    continue
                ignore_time = self.ignore_hits.get(ent, 0)
                if ignore_time > 0:
                    continue
                else:
                    self.health -= 5
                    # self.damage = True
                    if self.health <= 0:
                        self.dead = True
                    self.ignore_hits[ent] = 0.5

