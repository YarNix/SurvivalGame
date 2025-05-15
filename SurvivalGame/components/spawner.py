from enum import IntEnum
import os
import pickle
from random import choice
from typing import Sequence
from SurvivalGame.components.abstract import AbstractEntity, SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.entity import Enemy
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.pathfind import QTable, UninformedPathFind, InformedPathFind, LocalPathFind, AOSearching, BackTrackCSP, QLearningPathFind
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.state import StateComponent
from SurvivalGame.typing import *

class EnemyType(IntEnum):
    WEAK_ZOMBIE = 1
    STRONG_ZOMBIE = 2
    WEAK_SKELETON = 3
    STRONG_SKELETON = 4
    GHOUL = 5

ENEMY_TYPE_TO_SKIN = {
    EnemyType.WEAK_ZOMBIE: "Enemy 0",
    EnemyType.STRONG_ZOMBIE: "Enemy 1",
    EnemyType.WEAK_SKELETON: "Enemy 2",
    EnemyType.STRONG_SKELETON: "Enemy 3",
    EnemyType.GHOUL: "Enemy 4"
} 

ENEMY_TYPE_TO_PATHFIND: dict[EnemyType, list[type]] = {
    EnemyType.WEAK_ZOMBIE: [UninformedPathFind, InformedPathFind],
    EnemyType.STRONG_ZOMBIE: [LocalPathFind],
    EnemyType.WEAK_SKELETON: [BackTrackCSP],
    EnemyType.STRONG_SKELETON: [AOSearching],
    EnemyType.GHOUL: [QLearningPathFind]
}

#ENEMY_TYPE_TO_STATS: dict[EnemyType, list[tuple[]]]

def pathfind_resolution(entity: AbstractEntity , pathfind_type: type[UninformedPathFind | InformedPathFind | LocalPathFind | AOSearching | BackTrackCSP | QLearningPathFind], **kwargs):
    if not issubclass(pathfind_type, QLearningPathFind):
        nav_map = kwargs['nav_map']
        target = kwargs['target']
        entity.add_component(pathfind_type, nav_map=nav_map, target=target)
    else:
        map = kwargs['map']
        qtable = kwargs['qtable']
        target = kwargs['target']
        entity.add_component(pathfind_type, map=map, qtable=qtable, target=target)

class EnemySpawnPool:
    def __init__(self, player: AbstractEntity, map: TmxMap, update_entities: list[AbstractEntity], render: LayeredRender, max_spawn = 100) -> None:
        self.enable = True
        self.active: list[AbstractEntity] = []
        self.inactive: list[AbstractEntity] = []
        self.spawn_points = map.markers.get('Enemy', [])
        self.player = player
        self.upd_ents = update_entities
        self.map = map
        self.render = render
        self.max_gametime = 5 * 60
        self.max_spawn = max_spawn
        self.last_spawn_time = 0
        if os.path.exists('qtable.pkl'):
            with open('qtable.pkl', "rb") as f:
                self.qtable: QTable | None = pickle.load(f)
        else:
            self.qtable = None
            print('Warning: Missing qtable.pkl for QLearningPathFind')

    def spawn(self, etype: EnemyType):
        camera = self.player.get_component(CameraComponent).get_rect(self.player)
        spawn = choice([spawn for spawn in self.spawn_points if not camera.collidepoint(spawn)] or self.spawn_points)
        enemy = Enemy(skin=ENEMY_TYPE_TO_SKIN[etype], spawn=spawn)
        enemy.add_component(StateComponent)
        pathfind_resolution(enemy, choice(ENEMY_TYPE_TO_PATHFIND[etype]), nav_map=self.map.template_nav, target=self.player, qtable=self.qtable, map=self.map)
        # enemy.add_component(InformedPathFind, self.map.template_nav, self.player)
        self.activate_enemy(enemy)
        return enemy
    
    def activate_enemy(self, enemy: AbstractEntity):
        if enemy in self.inactive:
            self.inactive.remove(enemy)
        if enemy not in self.active:
            self.active.append(enemy)
        self.upd_ents.append(enemy)
        self.render.add(enemy.get_component(SpriteComponent), LayerId.OBJECT)
        self.map.collide_grid.add(enemy)

    def deactive_enemy(self, enemy: AbstractEntity):
        if enemy in self.active:
            self.active.remove(enemy)
        if enemy not in self.inactive:
            self.inactive.append(enemy)
        self.upd_ents.remove(enemy)
        self.render.remove(enemy.get_component(SpriteComponent), LayerId.OBJECT)
        self.map.collide_grid.remove(enemy)

    def select_enemy_type(self, gametime: float) -> EnemyType:
        # Time-based enemy selection logic
        progress = gametime / self.max_gametime
        if progress < 0.2:
            return EnemyType.WEAK_ZOMBIE
        elif progress < 0.4:
            return choice([EnemyType.WEAK_ZOMBIE, EnemyType.WEAK_SKELETON])
        elif progress < 0.6:
            return choice([EnemyType.STRONG_ZOMBIE, EnemyType.WEAK_SKELETON])
        elif progress < 0.8:
            return choice([EnemyType.STRONG_ZOMBIE, EnemyType.STRONG_SKELETON])
        else:
            return choice(list(EnemyType))
    
    def update(self, gametime: float, dt: float, *args, **kwargs):
        if not self.enable:
            return
        for enemy in self.active[:]:
            status = enemy.get_component(StateComponent, None)
            if status is not None and status.dead:
                self.deactive_enemy(enemy)

        # Gradually increase spawn rate over time
        min_spawn_interval = 0.45
        self.spawn_interval = max(min_spawn_interval, 1.0 - (gametime / self.max_gametime))

        self.last_spawn_time += dt
        if self.last_spawn_time >= self.spawn_interval:
            self.last_spawn_time = 0
            etype = self.select_enemy_type(gametime)
            if len(self.active) < self.max_spawn:
                self.spawn(etype)
        
        