import math
from heapq import heappush, heappop
import sys
from typing import TypeVar, Generic, Generator, Literal, Iterable
from itertools import combinations
from SurvivalGame.typing import *
import pygame as pg

type RectEdge = Literal['topleft', 'topright', 'bottomleft', 'bottomright']
T = TypeVar('T')

def ray_intersect(pointA: Point, pointB: Point, collisions: Iterable[Rect]):
    for obj in collisions:
        clip = obj.clipline(pointA, pointB)
        if clip and clip[0] != clip[1]:
            return True
    return False

def rect_scan_intersect(rect: Rect, scanLine: pg.Vector2, collisions: Iterable[Rect]):
    for obj in collisions:
        infobj = obj.inflate(rect.w, rect.h)
        clip = infobj.clipline(rect.center, rect.center + scanLine)
        if clip and clip[0] != clip[1]:
            return True
    return False
    
def get_edge(rect: Rect, attrib: RectEdge) -> Point:
    return getattr(rect, attrib)

class BoundedPoint:
    def __init__(self, point: Point, key: RectEdge):
        self.point = point
        self.key = key
    def __hash__(self):
        return hash(self.point)
    def __eq__(self, value):
        if isinstance(value, BoundedPoint):
            return self.point.__eq__(value.point)
        else:
            return self.point.__eq__(value)
    def __repr__(self):
        return (int(self.point[0]), int(self.point[1])).__repr__()

class NodePath(Generic[T]):
    def __init__(self, data: T, cost: float, parent: 'NodePath | None' = None):
        self.data = data
        self.cost = cost
        self.parent = parent
    def __lt__(self, other: 'NodePath') -> bool:
        return self.cost < other.cost
    def __repr__(self):
        return (self.data, self.cost).__repr__()
    
def path_trace(end: NodePath[T]):
    prev = end
    while prev.parent is not None:
        yield prev.data
        prev = prev.parent

def rect_move_bound(rect: Rect, bp: BoundedPoint):
    return rect.move_to(**{bp.key: bp.point})

def get_distance(x: BoundedPoint, y: BoundedPoint):
    return pg.Vector2(x.point).distance_to(y.point)

class PathFinder:
    def __init__(self, *, collisions: list[Rect]):
        self.collisions = collisions
        self.neighbour_map: dict[BoundedPoint, list[BoundedPoint]] = {}
        self.map()

    def map(self):
        self.neighbour_map.clear()
        # Building the map
        for edgeStart, edgeEnd in combinations(self.all_edges(), 2):
            if not ray_intersect(edgeStart.point, edgeEnd.point, self.collisions):
                self.neighbour_map.setdefault(edgeStart, []).append(edgeEnd)
                self.neighbour_map.setdefault(edgeEnd, []).append(edgeStart)
                

    def add_point(self, adding: BoundedPoint, collisions = None):
        """
        Add a point to the map and find its neighbours
        """
        neighbours = self.neighbour_map.setdefault(adding, [])
        neighbours.clear()
        for other in self.neighbour_map:
            if math.isclose(adding.point[0], other.point[0], rel_tol=1e-4) and math.isclose(adding.point[1], other.point[1], rel_tol=1e-4):
                continue
            if not ray_intersect(adding.point, other.point, collisions or self.collisions):
                self.neighbour_map[adding].append(other)
                self.neighbour_map[other].append(adding)

    def rem_point(self, point: BoundedPoint):
        """
        Remove a point from the map and its neighbours' reference to itself
        """
        for other in self.neighbour_map.pop(point):
            self.neighbour_map[other].remove(point)
    
    def all_edges(self) -> Generator[BoundedPoint, None, None]:
        for obj in self.collisions:
            # for FRect.clipline detection this is nessesary to prevent the edges from clipping with itself
            inf = obj.inflate(0.5, 0.5)
            yield BoundedPoint(inf.topleft, 'bottomright')
            yield BoundedPoint(inf.topright, 'bottomleft')
            yield BoundedPoint(inf.bottomleft, 'topright')
            yield BoundedPoint(inf.bottomright, 'topleft')

    def get_path(self, start: Rect, end: Rect):
        path = None
        start_point = BoundedPoint(start.center, 'center')
        end_point = BoundedPoint(end.center, 'center')

        no_start_point = start_point not in self.neighbour_map
        no_end_point = end_point not in self.neighbour_map
        colliable = [collision for collision in self.collisions if not collision.colliderect(start)]

        if no_start_point:
            self.add_point(start_point, colliable)
        if no_end_point:
            self.add_point(end_point, colliable)
        
        queue = [NodePath(start_point, 0)]
        g_score = {start_point.point: 0.0}

        greedy = False
        if start.move_to(center=end.center).collidelist(self.collisions) >= 0:
            # Be greedy if the start can't reach end
            greedy = True
        
        while len(queue) > 0:
            node = heappop(queue)
            curr_g = g_score[node.data.point]
            if node.data == end_point:
                path = [rect_move_bound(start, p).center for p in path_trace(node)]
                break
            old_rect = rect_move_bound(start, node.data)
            for new_point in self.neighbour_map[node.data]:
                # Check if the entity can walk to the point
                if not greedy or new_point != end_point: 
                    new_rect = rect_move_bound(start, new_point)
                    if rect_scan_intersect(old_rect, pg.Vector2(new_rect.center) - old_rect.center, colliable):
                        continue
                new_g = curr_g + get_distance(node.data, new_point)
                if new_g < g_score.get(new_point, sys.float_info.max):
                    new_node = NodePath(new_point, new_g + get_distance(new_point, end_point), node)
                    g_score[new_point.point] = new_g
                    heappush(queue, new_node)
        
        if no_start_point:
            self.rem_point(start_point)
        if no_end_point:
            self.rem_point(end_point)
        return path, greedy
        
    def get_next(self, start: Rect, end: Rect) -> tuple[Point | None, bool]:
        path, greedy = self.get_path(start, end)
        if path is None or len(path) < 2:
            return None, greedy
        else:
            return rect_move_bound(start, path[-1]).center, greedy