from random import choice
import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.debug import Debugger, Switches
from SurvivalGame.components.map import TmxMap
from SurvivalGame.components.pathfind import AOSearching, BackTrackCSP, InformedPathFind, LocalPathFind, UninformedPathFind
from SurvivalGame.components.pathfinder import PathFinder
from SurvivalGame.components.physic import RigidBoundingBox
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
from SurvivalGame.const import *
from SurvivalGame.components.entity import Enemy, Player

class Demo:
    def __init__(self, game):
        self.pause = False
        self.rendering = LayeredRender(scale=2.5)
        self.map = TmxMap(join(PT_MAP, "map.tmx"))
        for spr, layer in self.map.map_renders:
            self.rendering.add(spr, layer)
        self.entities = [*self.map.entities]

        player_spawn = next(iter(self.map.markers.get('Player', [])), (X_SCREEN_CENTER, Y_SCREEN_CENTER))
        self.player = Player(spawn=player_spawn, skin='Farmer 1')
        self.player.add_component(CameraComponent, self.rendering)
        self.entities.append(self.player)
        self.rendering.add(self.player.get_component(BasicSprite), LayerId.OBJECT)
        self.map.collide_grid.add(self.player)
        
        self.debug_switch = Switches(active=True)
        debugger = Debugger(self.debug_switch, self.rendering)
        self.entities.append(debugger)

        self.enemy_spawn_event = pg.event.custom_type()
        #pg.time.set_timer(self.enemy_spawn_event, 1500)

    def spawn_enemy(self):
        camera = self.player.get_component(CameraComponent).get_rect(self.player)
        spawns = self.map.markers.get('Enemy', [])
        spawn = choice([spawn for spawn in spawns if not camera.collidepoint(spawn)] or spawns)
        enemy = Enemy(spawn=spawn, skin='Enemy 1')
        enemy.add_component(AOSearching, self.map.template_nav, self.player)
        self.entities.append(enemy)
        self.rendering.add(enemy.get_component(SpriteComponent), LayerId.OBJECT)
        self.map.collide_grid.add(enemy)
        return enemy

    def update(self, *args, **kwargs):
        event: pg.Event
        for event in kwargs.get('events', []):
            if event.type == self.enemy_spawn_event and not self.pause:
                self.spawn_enemy()

        for entity in self.entities:
            entity.update(scene = self, collide_grid = self.map.collide_grid, *args, **kwargs)

    def draw(self, surf: pg.Surface) -> list[pg.FRect | pg.Rect]:
        self.rendering.render(surf)
        return []