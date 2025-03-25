import math
from heapq import heappush, heappop
import sys
from typing import TypeVar, Generic, Generator, Literal
from itertools import combinations
import pygame as pg

type Point = tuple[float, float] | tuple[int, int]
type Rect = pg.Rect | pg.FRect
type RectEdge = Literal['topleft', 'topright', 'bottomleft', 'bottomright']
T = TypeVar('T')

def has_line_of_sight(pointA: Point, pointB: Point, collisions: list[Rect]):
    for obj in collisions:
        clip = obj.clipline(pointA, pointB)
        if clip and clip[0] != clip[1]:
            return False
    return True
    
def get_edge(rect: Rect, attrib: RectEdge) -> Point:
    return getattr(rect, attrib)

class SmartPoint:
    def __init__(self, point: Point, key: RectEdge):
        self.point = point
        self.key = key
    def __hash__(self):
        return hash(self.point)
    def __eq__(self, value):
        if isinstance(value, SmartPoint):
            return self.point.__eq__(value.point)
        else:
            return self.point.__eq__(value)
    def __repr__(self):
        return self.point


class NodePath(Generic[T]):
    def __init__(self, data: T, cost: float, parent: 'NodePath | None' = None):
        self.data = data
        self.cost = cost
        self.parent = parent
    def __lt__(self, other: 'NodePath') -> bool:
        return self.cost < other.cost
    

class PathFinder:
    def __init__(self, *, collisions: list[Rect]):
        self.collisions = collisions
        self.neighbour_map: dict[SmartPoint, list[SmartPoint]] = {}
        self.create_map()

    def create_map(self):
        self.neighbour_map.clear()
        # Building the map
        for edgeStart, edgeEnd in combinations(self.all_edges(), 2):
            if has_line_of_sight(edgeStart.point, edgeEnd.point, self.collisions):
                self.neighbour_map.setdefault(edgeStart, []).append(edgeEnd)
                self.neighbour_map.setdefault(edgeEnd, []).append(edgeStart)
                

    def add_point(self, adding: SmartPoint):
        """
        Add a point to the map and find its neighbours
        """
        neighbours = self.neighbour_map.setdefault(adding, [])
        neighbours.clear()
        for other in self.neighbour_map:
            if math.isclose(adding.point[0], other.point[0], rel_tol=1e-4) and math.isclose(adding.point[1], other.point[1], rel_tol=1e-4):
                continue
            if has_line_of_sight(adding.point, other.point, self.collisions):
                self.neighbour_map[adding].append(other)
                self.neighbour_map[other].append(adding)

    def rem_point(self, point: SmartPoint):
        """
        Remove a point from the map and its neighbours' reference to itself
        """
        if point not in self.neighbour_map:
            return
        for other in self.neighbour_map.pop(point):
            self.neighbour_map[other].remove(point)
    
    def all_edges(self) -> Generator[SmartPoint, None, None]:
        for obj in self.collisions:
            # for FRect.clipline detection this is nessesary to prevent the edges from clipping with itself
            inf = obj.inflate(0.01, 0.01)
            yield SmartPoint(inf.topleft, 'bottomright')
            yield SmartPoint(inf.topright, 'bottomleft')
            yield SmartPoint(inf.bottomleft, 'topright')
            yield SmartPoint(inf.bottomright, 'topleft')

    def get_path(self, start: Rect, end: Rect):
        def path_trace(end: NodePath[T]):
            path: list[NodePath[T]] = []
            prev = end
            while prev is not None:
                path.append(prev)
                prev = prev.parent
            path.reverse()
            return path
        def get_distance(x: SmartPoint, y: SmartPoint):
            return pg.Vector2(x.point).distance_to(y.point)
        path = None
        start_point = SmartPoint(start.topleft, 'topleft')
        end_point = SmartPoint(end.topleft, 'topleft')

        self.add_point(start_point)
        self.add_point(end_point)
        
        queue = [NodePath(start_point, 0)]
        g_score = {start_point.point: 0.0}

        pessimistic = False
        if start.move_to(center=end.center).collidelist(self.collisions) >= 0:
            pessimistic = True
        
        while len(queue) > 0:
            node = heappop(queue)
            curr_g = g_score[node.data.point]
            if node.data == end_point:
                path = path_trace(node)
                break
            for new_point in self.neighbour_map[node.data]:
                # Be greedy if the start can't reach end
                if pessimistic and new_point == end_point: 
                    pass
                # Check if the entity can walk to the point
                elif node.data.key != new_point.key:
                    old_rect = start.move_to(**{node.data.key: node.data.point})
                    new_rect = start.move_to(**{new_point.key: new_point.point})
                    if not has_line_of_sight(get_edge(old_rect, new_point.key), get_edge(new_rect, new_point.key), self.collisions):
                        continue
                    vec = (pg.Vector2(start.center) - get_edge(start, new_point.key)) * 2
                    if not has_line_of_sight(get_edge(old_rect, new_point.key) + vec, get_edge(new_rect, new_point.key) + vec, self.collisions):
                        continue
                else:
                    vec = (pg.Vector2(start.center) - get_edge(start, node.data.key)) * 2
                    old_edge = node.data.point + vec
                    new_edge = new_point.point + vec
                    if not has_line_of_sight(old_edge, new_edge, self.collisions):
                        continue
                new_g = curr_g + get_distance(node.data, new_point)
                if new_g < g_score.get(new_point, sys.float_info.max):
                    new_node = NodePath(new_point, new_g + get_distance(new_point, end_point), node)
                    g_score[new_point.point] = new_g
                    heappush(queue, new_node)
        
        self.rem_point(start_point)
        self.rem_point(end_point)

        
        return path
        
    def get_direction(self, start: Rect, end: Rect) -> pg.Vector2:
        path = self.get_path(start, end)
        if path is None or len(path) < 2:
            return pg.Vector2()
        else:
            next = path[1].data
            next_pos = start.move_to(**{next.key: next.point})
            return (pg.Vector2(next_pos.center) - start.center).normalize()
        
            
    