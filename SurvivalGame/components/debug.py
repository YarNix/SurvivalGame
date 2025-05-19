from random import choice
from typing import Any
from SurvivalGame.components.abstract import EntityBase, PhysicComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.entity import EnemyType
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.pathfind import AOSearching, BackTrackCSP, InformedPathFind, LocalPathFind, PathFindComponent, QLearningPathFind, UninformedPathFind
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.sprites import BasicSprite
from SurvivalGame.const import *
from SurvivalGame.components.spawner import ENEMY_TYPE_TO_SKIN, ENEMY_TYPE_TO_PATHFIND
import pygame as pg


class Switches:
    def __init__(self, **kwargs: bool):
        self.__dict__.update(kwargs)

    def __getattr__(self, name: str):
        return bool(self.__dict__.get(name, False))

    def __setattr__(self, name, value):
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]

class Debugger(EntityBase):
    def __init__(self, switch: Switches, render: LayeredRender) -> None:
        super().__init__()
        self.switch = switch
        self._render = render
        overlay = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        overlay.fill(CL_TRANS)
        self.add_component(BasicSprite, overlay, layer=LayerId.OVERLAY)
        
    def update(self, scene: Any = None, events: list[pg.Event] = [], **kwargs):
        if not self.switch.active:
            return
        super().update(**kwargs)
        if scene is None:
            return
        for event in events:
            if event.type == pg.KEYDOWN and (event.mod & pg.KMOD_RCTRL) != 0:
                if event.key == pg.K_c:
                    self.switch.draw_collision = not self.switch.draw_collision
                elif event.key == pg.K_e:
                    enemy: EntityBase = scene.enemy_spawn.spawn(EnemyType.GHOUL)
                elif event.key == pg.K_p:
                    self.switch.draw_pathfind = not self.switch.draw_pathfind
                elif event.key == pg.K_q:
                    scene.pause = not scene.pause
                elif event.key == pg.K_0:
                    scene.enemy_spawn.enable = False
                elif event.key == pg.K_1 or event.key == pg.K_2 or event.key == pg.K_3 or event.key == pg.K_4 or event.key == pg.K_5 or event.key == pg.K_6:
                    algo = {
                        pg.K_1: UninformedPathFind,
                        pg.K_2: InformedPathFind,
                        pg.K_3: LocalPathFind,
                        pg.K_4: AOSearching,
                        pg.K_5: BackTrackCSP,
                        pg.K_6: QLearningPathFind
                    }
                    print('Spawning', algo[event.key])
                    #ENEMY_TYPE_TO_SKIN[EnemyType.UNKNOWN] = ENEMY_TYPE_TO_SKIN[choice([EnemyType.WEAK_ZOMBIE, EnemyType.STRONG_ZOMBIE, EnemyType.WEAK_SKELETON, EnemyType.STRONG_SKELETON, EnemyType.GHOUL])]
                    ENEMY_TYPE_TO_SKIN[EnemyType.UNKNOWN] = ENEMY_TYPE_TO_SKIN[EnemyType.WEAK_ZOMBIE]
                    ENEMY_TYPE_TO_PATHFIND[EnemyType.UNKNOWN] = [algo[event.key]]
                    scene.enemy_spawn.spawn(EnemyType.UNKNOWN)
                elif event.key == pg.K_9:
                    for enemy in scene.enemy_spawn.active.copy():
                        scene.enemy_spawn.deactive_enemy(enemy)
                elif event.key == pg.K_l:
                    scene.enemy_spawn.enable = not scene.enemy_spawn.enable 
                elif event.key == pg.K_SPACE:
                    scene.add_entity(scene.player.spawn_bullet())
                    

        surf = self.get_component(BasicSprite).image
        surf.fill(CL_TRANS)
        if self.switch.draw_collision:
            collide_grid = kwargs.get('collide_grid', None)
            
            if not isinstance(collide_grid, SpatialGrid):
                return    
            player: EntityBase = scene.player
            prect = player.get_component(BasicSprite).rect
            x, y = prect.center
            xstart = int(x // CELL_SIZE - 1)
            ystart = int(y // CELL_SIZE - 1)
            for i in range(xstart, xstart + 4):
                start = (i * CELL_SIZE, ystart * CELL_SIZE)
                end = (i * CELL_SIZE, (ystart + 3) * CELL_SIZE)
                pg.draw.line(surf, CL_WHITE, self._render.to_screen(start), self._render.to_screen(end))
            for i in range(ystart, ystart + 4):
                start = (xstart * CELL_SIZE, i * CELL_SIZE)
                end = ((xstart + 3) * CELL_SIZE, i * CELL_SIZE)
                pg.draw.line(surf, CL_WHITE, self._render.to_screen(start), self._render.to_screen(end))
            for collider, _ in collide_grid.get_collidables((x, y)):
                pg.draw.rect(surf, Color(180, 180, 180, 200), self._render.to_screen(collider))
            # pg.draw.rect(surf, (0, 200, 200, 250), prect.move_to(center=(prect.centerx * scale, prect.centery * scale) + scr_offset).scale_by(scale, scale))
        if self.switch.draw_pathfind:
            for entity in scene.entities:
                entity: EntityBase
                pathfind = entity.get_component(PathFindComponent, None)
                if pathfind is not None:
                    pos = entity.get_component(BasicSprite).rect.center
                    if pathfind.path:
                        path = pathfind.path + [pos]
                        pathlen = len(path) - 1
                        for idx, (pA, pB) in enumerate(zip(path, path[1:])):
                            pg.draw.aaline(surf, pg.Color.from_hsva(240 * (idx / pathlen), 100, 100, 100), self._render.to_screen(pA), self._render.to_screen(pB), 3)
                        
    