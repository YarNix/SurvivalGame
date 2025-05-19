from SurvivalGame.components.abstract import EntityBase, PhysicComponent, SpriteComponent
from SurvivalGame.typing import *
from SurvivalGame.const import *
from collections.abc import Generator, Iterable
import pygame as pg
import bisect
import math

def to_cell(*args) -> Generator[int]:
    for arg in args:
        if isinstance(arg, Iterable):
            yield from to_cell(*arg)
        else:
            yield int(arg // CELL_SIZE)


def obj_get_rect(obj) -> Rect:
    if isinstance(obj, pg.Rect | pg.FRect):
        return obj
    if isinstance(obj, EntityBase):
        physic = obj.get_component(PhysicComponent, None)
        sprite = obj.get_component(SpriteComponent, None)
        if sprite:
            if physic:
                return pg.FRect(sprite.rect.center - pg.Vector2(physic.bound) / 2, physic.bound)
            return sprite.rect
    raise ValueError(f"Object {obj} can't be converted to a Rect object")


def get_rank(obj) -> int:
    if isinstance(obj, EntityBase):
        return 0
    if isinstance(obj, pg.Rect | pg.FRect):
        return 1
    return 2


def remove_by_identity(lst, obj):
    """
    Remove an object using the is keyword rather than equality
    """
    for i, o in enumerate(lst):
        if o is obj:
            del lst[i]
            return
    raise ValueError(
        'remove_by_identity(lst, obj):',
        'obj does not exist in lst'
    )


class SpatialGrid:
    def __init__(self):
        self.map: dict[Point, list] = dict()

    def add(self, obj, /):
        rect = obj_get_rect(obj)
        if rect.w < CELL_SIZE and rect.h < CELL_SIZE:
            x, y = to_cell(rect.center)
            bisect.insort_right(self.map.setdefault((x, y), []), obj, key=get_rank)
        else:
            xmin, xmax, ymin, ymax = to_cell(rect.left, math.ceil(rect.right) - 1, rect.top, math.ceil(rect.bottom) - 1)
            for gx in range(xmin, xmax + 1):
                for gy in range(ymin, ymax + 1):
                    bisect.insort_right(self.map.setdefault((gx, gy), []), obj, key=get_rank)

    def remove(self, obj, /):
        rect = obj_get_rect(obj)
        if rect.w < CELL_SIZE and rect.h < CELL_SIZE:
            x, y = to_cell(rect.center)
            remove_by_identity(self.map[(x, y)], obj)
        else:
            xmin, xmax, ymin, ymax = to_cell(rect.left, math.ceil(rect.right) - 1, rect.top, math.ceil(rect.bottom) - 1)
            for gx in range(xmin, xmax + 1):
                for gy in range(ymin, ymax + 1):
                    remove_by_identity(self.map[(gx, gy)], obj)

    def get_collidables(self, point: Point, /):
        obj_set = set()
        x, y = to_cell(point)
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                for obj in self.map.get((i, j), []):
                    obj_rect = obj_get_rect(obj)
                    if id(obj) in obj_set:
                        continue
                    obj_set.add(id(obj))
                    if obj_rect is obj:
                        yield obj_rect, None
                    else:
                        yield obj_rect, obj