import pygame as pg
from SurvivalGame.components.pathfinder import PathFinder
from SurvivalGame.components.sprites import AnimatedSprite
from SurvivalGame.const import *
from SurvivalGame.components.sprites import KeyFrame
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer, AnimationFrame
from itertools import cycle

class Demo:
    def __init__(self, game, *sprites):
        map = load_pygame(join(PT_MAP, "demo_map.tmx"))
        self.map_collisions: list[pg.FRect] = []
        self.path_find = PathFinder(collisions=self.map_collisions)
        for layer in map.layers:
            cl = getattr(layer, 'class') if hasattr(layer, 'class') else ""
            if cl == 'Collision':
                for obj in layer:
                    self.map_collisions.append(pg.rect.FRect(obj.x, obj.y, obj.width, obj.height))
        self.path_find.create_map()
        self.map = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface_mock = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface_mock.fill(CL_WHITE)
        self.surface_offset = pg.Vector2(0, 0)
        self.direction = pg.Vector2(0, 0)

        self.map.fill(CL_BLACK)
        for obj in self.map_collisions:
            self.map.blit(self.surface_mock, obj.move(*self.surface_offset).topleft, obj.move_to(topleft=(0, 0)))

        self.startPos = pg.Vector2()
        self.endPos = pg.Vector2()

        self.mapMask = pg.Mask((SCREEN_WIDTH, SCREEN_HEIGHT))
        for obj in self.map_collisions:
            self.mapMask.draw(pg.Mask(obj.size, True), obj.topleft)
        

    def update(self, *args, **kwargs):
        event: pg.Event
        for event in kwargs.get('events', []):
            if event.type == pg.KEYDOWN or event.type == pg.KEYUP:
                if event.key == pg.K_LEFT:
                    self.direction.x += 1 if event.type == pg.KEYDOWN else -1
                elif event.key == pg.K_RIGHT:
                    self.direction.x += -1 if event.type == pg.KEYDOWN else 1
                elif event.key == pg.K_UP:
                    self.direction.y += 1 if event.type == pg.KEYDOWN else -1
                elif event.key == pg.K_DOWN:
                    self.direction.y += -1 if event.type == pg.KEYDOWN else 1
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.path_find.get_path(pg.FRect(self.startPos, (15, 20)), pg.FRect(self.endPos, (15, 20)))
                elif event.key == pg.K_s:
                    self.startPos.update(pg.mouse.get_pos() - self.surface_offset)
                elif event.key == pg.K_e:
                    self.endPos.update(pg.mouse.get_pos() - self.surface_offset)
            if event.type == pg.MOUSEMOTION and event.buttons[0]:
                self.surface_offset += event.rel
        self.surface_offset += self.direction

        if self.mapMask.overlap(pg.Mask((5, 5), True), pg.mouse.get_pos()):
            print('Overlap')


    def draw(self, surf: pg.Surface) -> list[pg.FRect | pg.Rect]:
        self.map.fill(CL_BLACK)
        # for obj in self.map_collisions:
        #     self.map.blit(self.surface_mock, obj.move(*self.surface_offset).topleft, obj.move_to(topleft=(0, 0)))
        self.map.blit(self.mapMask.to_surface())
        startRect = pg.FRect(self.startPos + self.surface_offset, (15, 20))
        endRect = pg.FRect(self.endPos + self.surface_offset, (15, 20))
        pg.draw.rect(self.map, (255, 0, 0), startRect)
        pg.draw.rect(self.map, (0, 0, 255), endRect)

        if hasattr(self.path_find, 'recent_path') and self.path_find.recent_path is not None:
            lastp = None
            for node in self.path_find.recent_path:
                p = node.data.point + (pg.Vector2(startRect.center) - getattr(startRect, node.data.key)) + self.surface_offset
                if lastp is None:
                    lastp = p
                    continue
                pg.draw.aaline(self.map, (255, 255, 0), lastp, p, 2)
                lastp = p
        surf.blit(self.map)
        return []