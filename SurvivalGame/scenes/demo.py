import pygame as pg
from SurvivalGame.components.abstract import AbstractEntity, SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.debug import Debugger, Switches
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.pathfind import AOSearching, BackTrackCSP, InformedPathFind, LocalPathFind, UninformedPathFind
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.spawner import EnemySpawnPool
from SurvivalGame.components.sprites import BasicSprite
from SurvivalGame.const import *
from SurvivalGame.components.entity import Enemy, Player
from random import choice

class Demo:
    def __init__(self, game):
        self.pause = False
        self.gametime = 0.0
        self.rendering = LayeredRender(scale=2.5)
        self.map = TmxMap(join(PT_MAP, "map.tmx"))
        for spr, layer in self.map.map_renders:
            self.rendering.add(spr, layer)
        self.entities: list[AbstractEntity] = [*self.map.entities]

        player_spawn = next(iter(self.map.markers.get('Player', [])), (X_SCREEN_CENTER, Y_SCREEN_CENTER))
        self.player = Player(spawn=player_spawn, skin='Farmer 1')
        self.player.add_component(CameraComponent, self.rendering)
        self.entities.append(self.player)
        self.rendering.add(self.player.get_component(BasicSprite), LayerId.OBJECT)
        self.map.collide_grid.add(self.player)

        self.enemy_spawn = EnemySpawnPool(self.player, self.map, self.entities, self.rendering)
        
        self.debug_switch = Switches(active=True)
        debugger = Debugger(self.debug_switch, self.rendering)
        self.entities.append(debugger)

    def update(self, dt, *args, **kwargs):
        event: pg.Event
        for event in kwargs.get('events', []):
            pass
        self.gametime += dt
        self.enemy_spawn.update(self.gametime, dt, **kwargs)
        for entity in self.entities:
            entity.update(scene = self, collide_grid = self.map.collide_grid, dt = dt, *args, **kwargs)

    def draw(self, surf: pg.Surface) -> list[pg.FRect | pg.Rect]:
        self.rendering.render(surf)
        return []