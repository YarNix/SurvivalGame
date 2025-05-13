from SurvivalGame.components.abstract import EntityBase, PhysicComponent
from SurvivalGame.components.camera import CameraComponent
from SurvivalGame.components.map import SpatialGrid
from SurvivalGame.components.pathfind import PathFindComponent, UninformedPathFind
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.sprites import BasicSprite
from SurvivalGame.const import *
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
        self.add_component(BasicSprite, pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA))
        overlay = self.get_component(BasicSprite)
        overlay.image.fill(CL_TRANS)
        render.add(overlay, LayerId.OVERLAY)
    def update(self, *args, **kwargs):
        if not self.switch.active:
            return
        super().update(*args, **kwargs)
        for event in kwargs.get('events', []):
            if event.type == pg.KEYDOWN and event.mod == pg.KMOD_RCTRL:
                if event.key == pg.K_c:
                    self.switch.draw_collision = not self.switch.draw_collision
                elif event.key == pg.K_e:
                    scene = kwargs.get('scene', None)
                    if scene is not None:
                        enemy: EntityBase = scene.spawn_enemy()
                        # player: EntityBase = scene.player
                        # camera = player.get_component(CameraComponent)
                        # camera.__dict__["needs_update"] = False
                        # enemy.add_component(CameraComponent, self._render)
                elif event.key == pg.K_p:
                    self.switch.draw_pathfind = not self.switch.draw_pathfind

        surf = self.get_component(BasicSprite).image
        surf.fill(CL_TRANS)
        scene = kwargs.get('scene', None)
        if scene is None:
            return
        if self.switch.draw_collision:
            collide_grid = kwargs.get('collide_grid', None)
            
            if not isinstance(collide_grid, SpatialGrid):
                return    
            player: EntityBase = scene.player
            scale = self._render.scale
            prect = player.get_component(BasicSprite).rect
            x, y = prect.center
            scr_offset = self._render.offset * scale
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
                    # bound = entity.get_component(PhysicComponent).bound
                    if pathfind.path:
                        path = pathfind.path + [pos]
                        for pA, pB in zip(path, path[1:]):
                            pg.draw.aaline(surf, CL_WHITE, self._render.to_screen(pA), self._render.to_screen(pB), 3)
                        
    