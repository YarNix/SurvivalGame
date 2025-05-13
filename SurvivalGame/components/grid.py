from SurvivalGame.typing import *
from SurvivalGame.const import CELL_SIZE
from collections.abc import Iterable, Generator
from typing import Any
import math
import pygame as pg

def to_cell(*args) -> Generator[int]:
    for arg in args:
        if isinstance(arg, Iterable):
            yield from to_cell(*arg)
        else:
            yield int(arg // CELL_SIZE)

def obj_get_rect(obj) -> Rect:
    if isinstance(obj, pg.Rect | pg.FRect):
        return obj
    if hasattr(obj, 'get_rect') and callable(obj.get_rect):
        rect = obj.get_rect()
        if isinstance(rect, pg.Rect | pg.FRect):
            return rect
    raise ValueError(f"Object {obj} can't be converted to a Rect object")
    

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

class SpatialHashGrid:
    def __init__(self):
        self.map: dict[Point, list] = dict()

    def add(self, obj, /):
        rect = obj_get_rect(obj)
        if rect.w < CELL_SIZE and rect.h < CELL_SIZE:
            x, y = to_cell(rect.center)
            self.map.setdefault((x, y), []).append(obj)
        else:
            xmin, xmax, ymin, ymax = to_cell(rect.left, math.ceil(rect.right) - 1, rect.top, math.ceil(rect.bottom) - 1)
            for gx in range(xmin, xmax + 1):
                for gy in range(ymin, ymax + 1):
                    self.map.setdefault((gx, gy), []).append(obj)

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

    def get_neighbours(self, rect: Rect, /) -> Generator[list[Rect, Any]]:
        x, y = to_cell(rect.center)
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                for obj in self.map.get((i, j), []):
                    obj_rect = obj_get_rect(obj)
                    if obj_rect is rect:
                        continue
                    if obj_rect is obj:
                        yield obj_rect, None
                    else:
                        yield obj_rect, obj
