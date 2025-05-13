from SurvivalGame.components.abstract import AbstractPixelMap, PhysicComponent, SpriteComponent, EntityBase
from SurvivalGame.components.animator import BasicAnimator
from SurvivalGame.components.render import LayerId, LayeredRender
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
from SurvivalGame.typing import *
from SurvivalGame.const import *
from collections.abc import Iterable, Generator
from typing import Literal, NamedTuple
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer, TiledObjectGroup, TiledObject
import math
from itertools import combinations
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
    if isinstance(obj, EntityBase):
        physic = obj.get_component(PhysicComponent, None)
        sprite = obj.get_component(SpriteComponent, None)
        if sprite:
            if physic:
                return pg.FRect(sprite.rect.center - pg.Vector2(physic.bound) / 2, physic.bound)
            return sprite.rect
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

class SpatialGrid:
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

    def get_collidables(self, point: Point, /):
        x, y = to_cell(point)
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                for obj in self.map.get((i, j), []):
                    obj_rect = obj_get_rect(obj)
                    if obj_rect is obj:
                        yield obj_rect, None
                    else:
                        yield obj_rect, obj

def ray_intersect(pointA: Point, pointB: Point, collisions: Iterable[Rect]):
    for obj in collisions:
        clip = obj.clipline(pointA, pointB)
        if clip and clip[0] != clip[1]:
            return True
    return False

type RectEdge = Literal['topleft', 'topright', 'bottomleft', 'bottomright', 'center']
class Edge(NamedTuple):
    point: Point
    name: RectEdge

def rect_at_edge(rect: Rect, edge: Edge):
    return rect.move_to(**{edge.name: edge.point})

def rect_scan_intersect(rect: Rect, rect_end: Rect, collisions: Iterable[Rect]):
    for obj in collisions:
        infobj = obj.inflate(rect.w, rect.h)
        clip = infobj.clipline(rect.center, rect_end.center)
        if clip and clip[0] != clip[1]:
            return True
    return False

NavigationMap = dict[Point, list[Point]]
class NavigationTemplateMap:
    def __init__(self, collisions: list[Rect]) -> None:
        self.collisions = collisions
        self.nav_map: dict[Edge, list[Edge]] = {}
        self.cached_map: dict[Point, NavigationMap] = {}
        # Building the map
        for edgeStart, edgeEnd in combinations(self.get_collision_edges(), 2):
            if not ray_intersect(edgeStart.point, edgeEnd.point, self.collisions):
                self.nav_map.setdefault(edgeStart, []).append(edgeEnd)
                self.nav_map.setdefault(edgeEnd, []).append(edgeStart)

    def get_collision_edges(self) -> Generator[Edge, None, None]:
        for obj in self.collisions:
            # for FRect.clipline detection this is nessesary to prevent the edges from clipping with itself
            inf = obj.inflate(0.5, 0.5)
            yield Edge(inf.topleft, 'bottomright')
            yield Edge(inf.topright, 'bottomleft')
            yield Edge(inf.bottomleft, 'topright')
            yield Edge(inf.bottomright, 'topleft')

    def get_nav_for(self, bound: Point, start: Point, end: Point):
        """
        Build a navigation map for a entity with the bounding box
        """
        rect_bound = pg.FRect((0, 0), bound)
        colliable = [collision for collision in self.collisions if not collision.colliderect(rect_bound)]
        if bound not in self.cached_map:
            bounded_nav_map = {}
            for edge, neigh_edges in self.nav_map.items():
                start_rect = rect_at_edge(rect_bound, edge)
                if start_rect.collidelist(colliable) >= 0:
                    bounded_nav_map.setdefault(start_rect.center, [])
                    continue
                neigh_points: list = bounded_nav_map.setdefault(start_rect.center, [])
                for neigh in neigh_edges:
                    end_rect = rect_at_edge(rect_bound, neigh)
                    if rect_scan_intersect(start_rect, end_rect, colliable):
                        continue
                    neigh_points.append(end_rect.center)
            self.cached_map[bound] = bounded_nav_map
        # Inserting start point and end point to the map
        nav_map = self.cached_map[bound].copy()
        if start not in nav_map:
            neighbours = []
            rect_bound.center = start
            # for edge in self.get_collision_edges():
            for edge in self.nav_map:
                end_rect = rect_at_edge(rect_bound, edge)
                if not rect_scan_intersect(rect_bound, end_rect, colliable):
                    neighbours.append(end_rect.center)
                    # don't need to return to start
                    # nav_map[end_rect.center].append(start) 
                    # only add for default
                    # nav_map.setdefault(end_rect.center, [])
            nav_map[start] = neighbours
        if end not in nav_map:
            nav_map.setdefault(end, [])
            rect_bound.center = end
            # for edge in self.get_collision_edges():
            for edge in self.nav_map:
                start_rect = rect_at_edge(rect_bound, edge)
                if not rect_scan_intersect(rect_bound, start_rect, colliable):
                    # don't need to return to other point when ended
                    # neighbours.append(end_rect.center)
                    # making a copy as to not affect the cached map
                    neighbours = [end]
                    neighbours.extend(nav_map.get(start_rect.center, []))
                    nav_map[start_rect.center] = neighbours
        if not rect_scan_intersect(rect_bound.move_to(center=start), rect_bound.move_to(center=end), colliable):
            nav_map[start].append(end)
            #nav_map[end].append(start)
        
        return nav_map

class TmxMap(AbstractPixelMap):
    def __init__(self, path: str):
        self._map_data = load_pygame(path)
        self._ground = BasicSprite(pg.Surface((self.width, self.height)))
        self.collide_grid = SpatialGrid()
        self.collisions: list[Rect] = []
        self.markers: dict[str, list[Point]] = {}
        self.entities: list[EntityBase] = []
        self.map_renders: list[tuple[SpriteComponent, LayerId]] = []

        tilewidth, tileheight = self.tilewidth, self.tileheight
        for idx, layer in enumerate(self._map_data.layers):
            if not getattr(layer, 'visible', False):
                continue
            if isinstance(layer, TiledTileLayer):
                if layer.name == 'Ground':
                    for x, y, s in layer.tiles():
                        self._ground.image.blit(s, (x * tilewidth, y * tileheight))
                elif layer.name == 'Object' or layer.name == 'Behind':
                    layer_id = LayerId.OBJECT if layer.name == 'Object' else LayerId.BEHIND
                    for x, y, s in layer.tiles():
                        gid = self._map_data.get_tile_gid(x, y, idx)
                        prop = self._map_data.get_tile_properties_by_gid(gid)
                        if prop is None or 'frames' not in prop:
                            spr = BasicSprite(s, topleft=(x * tilewidth, y * tileheight))
                            self.map_renders.append((spr, layer_id))
                        else:
                            ent = EntityBase()
                            ent.add_component(BasicSprite, s, topleft=(x * tilewidth, y * tileheight))
                            ent.add_component(BasicAnimator, SpriteSheetImage.from_tile_animation(prop['frames'], self._map_data))
                            self.map_renders.append((ent.get_component(BasicSprite), layer_id))
                            self.entities.append(ent)
            elif isinstance(layer, TiledObjectGroup):
                obj: TiledObject
                if layer.name == 'Collision':
                    for obj in layer:
                        rect = pg.rect.FRect(obj.x, obj.y, obj.width, obj.height)
                        self.collisions.append(rect)
                        self.collide_grid.add(rect)
                elif layer.name == 'Marker':
                    for obj in layer:
                        obj: TiledObject
                        self.markers.setdefault(str(obj.name), []).append((obj.x, obj.y))
        self.map_renders.append((self._ground, LayerId.TILED))
        self.template_nav = NavigationTemplateMap(self.collisions)


    @property    
    def tilewidth(self):
        """Width of the tile in pixel"""
        return self._map_data.tilewidth
    
    @property
    def tileheight(self):
        """Height of the tile in pixel"""
        return self._map_data.tileheight
    
    @property
    def mapwidth(self):
        """Width of the map in tiles"""
        return self._map_data.width
    
    @property
    def mapheight(self):
        """Height of the map in tiles"""
        return self._map_data.height

    @property
    def width(self):
        """Width of the map in pixel"""
        return self._map_data.width * self._map_data.tilewidth
    
    @property
    def height(self):
        """Height of the map in pixel"""
        return self._map_data.height * self._map_data.tileheight