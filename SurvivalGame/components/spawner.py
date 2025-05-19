import os
import pickle
import pandas as pd
import pygame as pg
from random import choice
from SurvivalGame.components.abstract import AbstractEntity, SpriteComponent, SupportsEntityOperation
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.entity import Enemy, EnemyType
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.pathfind import UninformedPathFind, InformedPathFind, LocalPathFind, AOSearching, BackTrackCSP, QLearningPathFind
from SurvivalGame.components.render import LayerId
from SurvivalGame.components.state import StateComponent
from SurvivalGame.components.text import AttachedText
from SurvivalGame.typing import *

ENEMY_TYPE_TO_SKIN = {
    EnemyType.WEAK_ZOMBIE: "Enemy 0",
    EnemyType.STRONG_ZOMBIE: "Enemy 1",
    EnemyType.WEAK_SKELETON: "Enemy 2",
    EnemyType.STRONG_SKELETON: "Enemy 3",
    EnemyType.GHOUL: "Enemy 4"
} 

ENEMY_TYPE_TO_PATHFIND: dict[EnemyType, list[type]] = {
    EnemyType.WEAK_ZOMBIE: [UninformedPathFind, QLearningPathFind],
    EnemyType.STRONG_ZOMBIE: [LocalPathFind],
    EnemyType.WEAK_SKELETON: [BackTrackCSP],
    EnemyType.STRONG_SKELETON: [AOSearching],
    EnemyType.GHOUL: [InformedPathFind]
}

ENEMY_TYPE_TO_STATS: dict[EnemyType, float] = {
    EnemyType.UNKNOWN: 1.0,
    EnemyType.WEAK_ZOMBIE: 0.2,
    EnemyType.STRONG_ZOMBIE: 0.5,
    EnemyType.WEAK_SKELETON: 0.5,
    EnemyType.STRONG_SKELETON: 0.75,
    EnemyType.GHOUL: 1
}

ENEMY_TYPE_TO_NAME: dict[type, str] = {
    UninformedPathFind: 'BFS',
    InformedPathFind: 'A*',
    LocalPathFind: 'BEAM',
    AOSearching: 'AND_OR',
    BackTrackCSP: 'Backtrack',
    QLearningPathFind: 'QLearning'    
}

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
    entity.add_component(AttachedText, pg.Font(size=14), ENEMY_TYPE_TO_NAME[pathfind_type], offset=(0, -14))

class EnemySpawnPool:
    def __init__(self, player: AbstractEntity, tmx_map: TmxMap, context: SupportsEntityOperation, max_spawn = 80) -> None:
        self.enable = True
        self.max_gametime = 5 * 60
        self.max_spawn = max_spawn
        self.last_spawn_time = 0
        
        self.active: list[Enemy] = []
        self.inactive: list[Enemy] = []
        self.spawn_points = tmx_map.markers.get('Enemy', [])
        self.player = player
        self.tmx_map = tmx_map
        self.context = context

        if os.path.exists('qtable.pkl'):
            with open('qtable.pkl', "rb") as f:
                self.qtable: pd.DataFrame | None = pickle.load(f)
        else:
            self.qtable = None
            print('Warning: Missing qtable.pkl for QLearningPathFind')

    def spawn(self, etype: EnemyType):
        camera = self.player.get_component(CameraComponent).get_rect(self.player)
        spawn = choice([spawn for spawn in self.spawn_points if not camera.collidepoint(spawn)] or self.spawn_points)
        for deactive in self.inactive:
            if deactive.type_name == etype:
                enemy = deactive
                enemy.get_component(SpriteComponent).rect.center = spawn
                break
        else:
            enemy = Enemy(type_name=etype, skin=ENEMY_TYPE_TO_SKIN[etype], spawn=spawn)
            pathfind_resolution(enemy, choice(ENEMY_TYPE_TO_PATHFIND[etype]), nav_map=self.tmx_map.template_nav, target=self.player, qtable=self.qtable, map=self.tmx_map)
        self.activate_enemy(enemy)
        return enemy
    
    def activate_enemy(self, enemy: Enemy):
        if enemy in self.inactive:
            self.inactive.remove(enemy)
        if enemy not in self.active:
            self.active.append(enemy)
        state = enemy.get_component(StateComponent)
        state.health = 100 * ENEMY_TYPE_TO_STATS[enemy.type_name]
        state.dead = False
        state.damage = False
        self.context.add_entity(enemy)

    def deactive_enemy(self, enemy: Enemy):
        if enemy in self.active:
            self.active.remove(enemy)
        if enemy not in self.inactive:
            self.inactive.append(enemy)
        self.context.rem_entity(enemy)

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
    
    def update(self, gametime: float, dt: float):
        if not self.enable or dt <= 0:
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
        
        