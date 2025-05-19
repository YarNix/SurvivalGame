from SurvivalGame.components.abstract import AbstractEntity, CollideTriggerComponent, EntityBase
from SurvivalGame.components.state import StateComponent
from SurvivalGame.const import ORD_PREPROCESS


class PlayerTrigger(CollideTriggerComponent):
    needs_update = True
    update_order = ORD_PREPROCESS
    def __init__(self) -> None:
        self.ignore_hits = {}
    def on_attach(self, entity: AbstractEntity):
        self.owner = entity
    def on_any_collided(self, obj):
        if isinstance(obj, EntityBase) and 'enemy' in obj.tags:
            ignore_time = self.ignore_hits.get(obj, 0)
            if ignore_time > 0:
                return
            state = self.owner.get_component(StateComponent)
            state.health -= 5
            if state.health <= 0:
                state.dead = True
            self.ignore_hits[obj] = 0.5

    def update(self, dt: float, **_):
        for ent in list(self.ignore_hits):
            remaining = self.ignore_hits[ent] - dt
            if remaining < 0:
                del self.ignore_hits[ent]
            else:
                self.ignore_hits[ent] = remaining


class BulletTrigger(CollideTriggerComponent):
    def on_attach(self, entity: EntityBase):
        self.owner = entity
    def on_any_collided(self, obj):
        if isinstance(obj, EntityBase):
            if 'enemy' in obj.tags:
                enemy_state = obj.get_component(StateComponent)
                if enemy_state.health <= 0:
                    return
                enemy_state.health -= 10
                enemy_state.damage = True
                self.owner.add_tag('killing')
        else:
            self.owner.add_tag('killing')