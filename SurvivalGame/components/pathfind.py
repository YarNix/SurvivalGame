from collections import deque
from enum import IntEnum
from time import localtime
from random import Random
from typing import Any, Callable, NamedTuple, TypeVar, Generic, Protocol, runtime_checkable, cast
from abc import ABC, abstractmethod
from SurvivalGame.const import *
from SurvivalGame.typing import *
from SurvivalGame.components.abstract import AbstractEntity, AbstractPixelMap, PhysicComponent, SpriteComponent
from SurvivalGame.components.map import NavigationTemplateMap, rect_at_edge, rect_scan_intersect
import pandas as pd
import pygame as pg
import heapq

Path = list[Point]

class PathFindComponent:
    path: Path

class MinimalPathFindBase(PathFindComponent, ABC):
    needs_update = True
    update_order = ORD_PATH
    """
    A path finder that minimize updating the path.

    This is a base class doesn't do any path find.
    It just checking whether a new path needs to be calculated then call the abstract method implement by the subclass
    """
    def __init__(self, target: AbstractEntity) -> None:
        self.path = []
        self.target = target
        self._last_pos = None
        self.update_angle = 45

    @abstractmethod
    def path_find(self, start: Point, end: Point, entity: AbstractEntity): ...

    def update(self, entity: AbstractEntity, **_):
        current_position = entity.get_component(SpriteComponent).rect.center
        current_vect = pg.Vector2(current_position)
        current_destination = self.target.get_component(SpriteComponent).rect.center
        if self._last_pos and self.path:
            # Check if entity has travel to the next point in the path
            current_target = self.path[-1]
            last_vec = (current_target[0] - self._last_pos[0], current_target[1] - self._last_pos[1])
            end_vec = current_target - current_vect
            dot = end_vec.dot(last_vec)
            if dot < 0 and end_vec.length_squared() > (last_vec[0]**2 + last_vec[1]**2):
                self.path.pop()
        self._last_pos = current_position
        should_update = (not self.path)
        if not should_update:
            # Check whether path needs update
            last_destination = self.path[0]
            angle_to_last = (current_vect - last_destination).as_polar()[1]
            angle_to_curr = (current_vect - current_destination).as_polar()[1]
            angle = abs(angle_to_last - angle_to_curr) % 180
            should_update = angle > self.update_angle
        if should_update:
            self.path_find(current_position, current_destination, entity)
            # scene = kwargs.get('scene', None)
            # if scene is not None:
            #     scene.pause = not scene.pause

        direction = entity.get_component(PhysicComponent).direction
        if not self.path:
            direction.update()
        else:
            direction.update(self.path[-1] - current_vect)
            if direction.xy != (0, 0):
                direction.normalize_ip()

class UninformedPathFind(MinimalPathFindBase):
    """
    A uniformed path find component using BFS
    """
    def __init__(self, nav_map: NavigationTemplateMap, target: AbstractEntity):
        super().__init__(target)
        self.map_template = nav_map
        self.update_angle = 60

    def path_find(self, start: Point, end: Point, entity: AbstractEntity): 
        bound = entity.get_component(PhysicComponent).bound
        nav_map = self.map_template.get_nav_for(bound, start, end)
        # -- BFS Search --
        frontier: deque[Point] = deque([start])
        came_from: dict[Point, Point | None] = {start: None}
        while len(frontier) != 0:
            point = frontier.popleft()
            if point == end:
                self.path.clear()
                node = end
                while node is not None:
                    self.path.append(node)
                    node = came_from[node]
                self.path.pop() # pop the start node
                break
            for neighbour in nav_map.get(point, []):
                if neighbour not in came_from:
                    frontier.append(neighbour)
                    came_from[neighbour] = point
        else:
            # Can't find a path
            self.path.clear()

T = TypeVar('T')
@runtime_checkable
class SupportsLessThan(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...

TKey = TypeVar('TKey', bound=SupportsLessThan)
TVal = TypeVar('TVal')
class KeyValueType(NamedTuple, Generic[TKey, TVal]):
    key: TKey
    value: TVal
    def __lt__(self, other: 'KeyValueType[TKey, TVal]') -> bool:
        return self.key < other.key
del SupportsLessThan

class InformedPathFind(MinimalPathFindBase):
    """
    A informed path find component using A*
    """
    def __init__(self, nav_map: NavigationTemplateMap, target: AbstractEntity):
        super().__init__(target)
        self.map_template = nav_map
    
    def path_find(self, start, end, entity):
        bound = entity.get_component(PhysicComponent).bound
        nav_map = self.map_template.get_nav_for(bound, start, end)
        # -- A* search --
        frontier = [KeyValueType(0.0, start)]
        came_from: dict[Point, Point | None] = {start: None}
        g_score: dict[Point, float] = {start: 0.0}
        vect_end = pg.Vector2(end)

        while len(frontier) > 0:
            _, point, = heapq.heappop(frontier)
            if point == end:
                self.path.clear()
                node = end
                while node is not None:
                    self.path.append(node)
                    node = came_from[node]
                self.path.pop() # pop the start nod
                break
            curr_g = g_score[point]
            vect = pg.Vector2(point)
            for neighbour in nav_map.get(point, []):
                new_g = curr_g + vect.distance_to(neighbour)
                if new_g < g_score.get(neighbour, INF):
                    came_from[neighbour] = point
                    g_score[neighbour] = new_g
                    new_h = vect_end.distance_to(neighbour)
                    heapq.heappush(frontier, KeyValueType(new_g + new_h, neighbour))
        else:
            # print("No path found")
            self.path.clear()

class LocalPathFind(MinimalPathFindBase):
    """
    A local search path find component using BeamSearch
    """
    def __init__(self, nav_map: NavigationTemplateMap, target: AbstractEntity, beam_width = 6, max_depth = 10):
        super().__init__(target)
        self.map_template = nav_map
        self.update_angle = 80
        self.beam_width = beam_width
        self.max_depth = max_depth
    
    def path_find(self, start, end, entity):
        end_vec = pg.Vector2(end)
        bound = entity.get_component(PhysicComponent).bound
        nav_map = self.map_template.get_nav_for(bound, start, end)
        # -- Beam search --

        beam = [KeyValueType(0.0, start)]
        came_from: dict[Point, Point | None] = {start: None}
        for _ in range(self.max_depth):
            if not beam:
                continue
            candidates: list[KeyValueType[float, Point]] = []
            for _, point in beam:
                if point == end:
                    self.path.clear()
                    node = end
                    while node is not None:
                        self.path.append(node)
                        node = came_from[node]
                    self.path.pop() # pop the start node
                    return
                for neighbour in nav_map.get(point, []):
                    if neighbour not in came_from:
                        came_from[neighbour] = point
                        candidates.append(KeyValueType((end_vec - neighbour).length(), neighbour))
            # Keep only top-k from the heap
            beam = heapq.nsmallest(self.beam_width, candidates)
        else:
            self.path.pop()


class AND_Node(NamedTuple):
    #type = Literal["AND"]
    data: tuple['SearchNode']
class OR_Node(NamedTuple):
    #type = Literal["OR"]
    data: tuple['SearchNode']
SearchNode = AND_Node | OR_Node | Point

class AOSearching(MinimalPathFindBase):
    """
    A path search component using AND OR Tree
    """
    def __init__(self, nav_map: NavigationTemplateMap, target: AbstractEntity):
        super().__init__(target)
        self.map_template = nav_map
        self.update_angle = 90
    
    def path_find(self, start, end, entity):
        bound = entity.get_component(PhysicComponent).bound
        self.nav_map = self.map_template.get_nav_for(bound, start, end)
        # -- AND OR search --
        path = self.and_or_search(start, AND_Node((end, )), set())
        self.path.clear()
        if path:
            self.path.extend(p for p in reversed(path) if p != start)
            
    def and_or_search(self, point: Point, goal: SearchNode, visited: set[Point]) -> Path | None:
        if point in visited:
            return None

        if isinstance(goal, AND_Node):
            result: Path = []
            for subgoal in goal.data:
                path = self.and_or_search(point, subgoal, visited.copy())
                if path is None:
                    return None
                result.extend(path)
                point = path[-1]
            return result
        elif isinstance(goal, OR_Node):
            for subgoal in goal.data:
                path = self.and_or_search(point, subgoal, visited.copy())
                if path:
                    return path
            return None
        else:
            # Base case: goal_structure is a position
            visited.add(point)
            return self.get_path(point, goal)
        

    def get_path(self, start: Point, end: Point):
        path: Path = []
        queue = deque([start])
        came_from: dict[Point, Point | None] = {start: None}
        while queue:
            current = queue.popleft()
            if current == end:
                node = end
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path
            for succ in self.nav_map.get(current, []):
                if succ not in came_from:
                    came_from[succ] = current
                    queue.append(succ)
        return None

def backtrack_search(picked: list[T], remain: list[T], is_valid: Callable[[list[T]], bool], reached_goal: Callable[[list[T]], bool]) -> list[T] | None:
    if not remain:
        return picked
    for picking in remain:
        new_picked = picked.copy()
        new_picked.append(picking)
        if not is_valid(new_picked):
            continue
        if reached_goal(new_picked):
            return new_picked
        new_remain = [r for r in remain if r is not picking]
        result = backtrack_search(new_picked, new_remain, is_valid, reached_goal)
        if result:
            return result
    return None

class BackTrackCSP(MinimalPathFindBase):
    def __init__(self, nav_map: NavigationTemplateMap, target: AbstractEntity) -> None:
        super().__init__(target)
        self.map_template = nav_map
    
    def path_find(self, start, end, entity):
        bound = entity.get_component(PhysicComponent).bound
        rect_bound = pg.FRect((0, 0), bound)
        end_vec = pg.Vector2(end)
        colliable = [collision for collision in self.map_template.collisions if not collision.colliderect(rect_bound)]
        # -- Backtracking Search --
        edges: list[Rect] = [rect_bound.move_to(center=end), *(rect_at_edge(rect_bound, edge) for edge in self.map_template.get_collision_edges())]
        edges.sort(key=lambda r: end_vec.distance_to(r.center))

        def can_walk_to(picked: list[Rect]):
            prev_rect = rect_bound.move_to(center=start)
            for rect in picked:
                if rect_scan_intersect(prev_rect, rect, colliable):
                    return False
                prev_rect = rect
            return True
        
        def end_at_target(picked: list[Rect]):
            return picked[-1].center == end
        
        result = backtrack_search([], edges, can_walk_to, end_at_target)
        if result is None:
            self.path.clear()
        else:
            self.path.clear()
            self.path.extend(r.center for r in reversed(result))

class Action(IntEnum):
    N = 0
    S = 1
    W = 3
    E = 4
    NW = 5
    NE = 6
    SW = 7
    SE = 8

ACTION_TO_DIRECTION = {
    Action.N: (0, -1),
    Action.S: (0, 1),
    Action.W: (-1, 0),
    Action.E: (1, 0),
    Action.NW: (-1, -1),
    Action.NE: (1, -1),
    Action.SW: (-1, 1),
    Action.SE: (1, 1)
}

class QLearningPathFind(MinimalPathFindBase):
    needs_update = True
    update_order = ORD_PATH
    """
    A reforcement learning path find component using Q-learning
    """
    def __init__(self, map: AbstractPixelMap, qtable: pd.DataFrame, target: AbstractEntity):
        super().__init__(target)
        self.map = map
        self.Q = qtable
        self.rng = Random()

    def to_tile(self, point: Point):
        return (int(point[0] // self.map.tilewidth), int(point[1] // self.map.tileheight))
    
    def from_tile(self, tile: Point):
        return (int((tile[0] + 0.5) * self.map.tilewidth), int((tile[1] + 0.5) * self.map.tileheight))
    
    def get_action(self, tile: Point, goal: Point):
        try:
            return Action(self.Q.at[tile, goal])
        except:
            # Choose a random angle
            self.rng.seed(hash((tile, localtime().tm_sec)))
            return cast(Action, Action._member_map_[self.rng.choice(Action._member_names_)])

    def path_find(self, start: Point, end: Point, entity: AbstractEntity):
        self.path.clear()
        steps = iter(range(18))
        current_tile = self.to_tile(start)
        current_goal = self.to_tile(end)
        current_action: Action = self.get_action(current_tile, current_goal)
        visited = set([current_goal])
        
        while current_tile not in visited and next(steps, -1) != -1:
            visited.add(current_tile)
            # Get the next tile from the action
            dir = ACTION_TO_DIRECTION[current_action]
            current_tile = (current_tile[0] + dir[0], current_tile[1] + dir[1])
            current_action = self.get_action(current_tile, current_goal)
            self.path.append(self.from_tile(current_tile))
        self.path.reverse()
