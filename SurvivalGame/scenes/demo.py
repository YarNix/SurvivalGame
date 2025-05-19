import pygame as pg
from SurvivalGame.components.abstract import AbstractEntity, PhysicComponent, SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.debug import Debugger, Switches
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.hud import HUD
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.spawner import EnemySpawnPool
from SurvivalGame.components.sprites import BasicSprite
from SurvivalGame.const import *
from SurvivalGame.components.entity import Player

class Demo:
    def __init__(self, game):
        self.pause = False
        self.gametime = 0.0
        self.default_font = pg.font.Font(None, 28)
        self.rendering = LayeredRender(scale=2)
        self.entities: list[AbstractEntity] = []
        self.collide_grid = SpatialGrid()

        self.map = TmxMap(path=join(PT_MAP, "map.tmx"), )
        self.rendering.extend(self.map.map_sprites)
        self.entities.extend(self.map.entities)
        for rect in self.map.collisions:
            self.collide_grid.add(rect)

        player_spawn = next(iter(self.map.markers.get('Player', [])), (X_SCREEN_CENTER, Y_SCREEN_CENTER))
        self.player = Player(spawn=player_spawn, skin='Farmer 2')
        self.player.add_component(CameraComponent, self.rendering)
        self.add_entity(self.player)

        hud = HUD(player=self.player, font=self.default_font)
        self.add_entity(hud)

        self.debug_switch = Switches(active=True)
        self.debugger = Debugger(self.debug_switch, self.rendering)
        self.add_entity(self.debugger)

        self.enemy_spawn = EnemySpawnPool(self.player, self.map, self)
        #self.enemy_spawn.enable = False

    def update(self, dt, *args, **kwargs):
        # event: pg.Event
        # for event in kwargs.get('events', []):
        #     pass
        if self.pause:
            dt = 0.0
        else:
            self.gametime += dt
            self.enemy_spawn.update(self.gametime, dt)
        for entity in self.entities.copy(): # copy in case the update add/remove entity
            entity.update(scene=self, collide_grid=self.collide_grid, dt=dt, *args, **kwargs)

    def draw(self, surf: pg.Surface) -> list[pg.FRect | pg.Rect]:
        self.rendering.render(surf)
        return []
    
    def add_entity(self, entity: AbstractEntity, **kwargs):
        self.rendering.extend(entity.get_components(SpriteComponent))
        if entity.get_component(PhysicComponent, None):
            self.collide_grid.add(entity)
        self.entities.append(entity)

    def rem_entity(self, entity: AbstractEntity, **kwargs):
        for spr in entity.get_components(SpriteComponent):
            self.rendering.remove(spr)
        if entity.get_component(PhysicComponent, None):
            self.collide_grid.remove(entity)
        self.entities.remove(entity)