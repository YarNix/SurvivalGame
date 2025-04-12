from SurvivalGame.typing import *
from SurvivalGame.const import CELL_SIZE
from collections.abc import Iterable, Generator
import math

def to_cell(*args) -> Generator[int]:
    for arg in args:
        if isinstance(arg, Iterable):
            yield from to_cell(*arg)
        else:
            yield int(arg // CELL_SIZE)

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
        self.map: dict[Point, list[Rect]] = dict()

    def add(self, obj: Rect, /):
        if obj.w < CELL_SIZE and obj.h < CELL_SIZE:
            x, y = to_cell(obj.center)
            self.map.setdefault((x, y), []).append(obj)
        else:
            xmin, xmax, ymin, ymax = to_cell(obj.left, math.ceil(obj.right) - 1, obj.top, math.ceil(obj.bottom) - 1)
            for gx in range(xmin, xmax + 1):
                for gy in range(ymin, ymax + 1):
                    self.map.setdefault((gx, gy), []).append(obj)

    def remove(self, obj: Rect, /):
        if obj.w < CELL_SIZE and obj.h < CELL_SIZE:
            x, y = to_cell(obj.center)
            remove_by_identity(self.map[(x, y)], obj)
        else:
            xmin, xmax, ymin, ymax = to_cell(obj.left, math.ceil(obj.right) - 1, obj.top, math.ceil(obj.bottom) - 1)
            for gx in range(xmin, xmax + 1):
                for gy in range(ymin, ymax + 1):
                    remove_by_identity(self.map[(gx, gy)], obj)

    def get_neighbours(self, obj: Rect, /) -> Generator[Rect]:
        x, y = to_cell(obj.center)
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                for o in self.map.get((i, j), []):
                    if o is not obj:
                        yield o
