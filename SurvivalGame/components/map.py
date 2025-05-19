from SurvivalGame.components.abstract import AbstractPixelMap, SpriteComponent, EntityBase, SupportsEntityOperation
from SurvivalGame.components.animator import BasicAnimator
from SurvivalGame.components.grid import SpatialGrid
from SurvivalGame.components.render import LayerId
from SurvivalGame.components.sprites import BasicSprite, SpriteSheetImage
from SurvivalGame.typing import *
from SurvivalGame.const import *
from collections.abc import Iterable, Generator
from typing import Literal, NamedTuple
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer, TiledObjectGroup, TiledObject
from itertools import combinations
import pygame as pg

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
        self.__map_data = load_pygame(path)
        self.markers: dict[str, list[Point]] = {}
        self.collisions: list[Rect] = []
        self.entities: list[EntityBase] = []
        ground = BasicSprite(pg.Surface((self.width, self.height)), layer=LayerId.TILED)
        self.map_sprites = [ground]

        tilewidth, tileheight = self.tilewidth, self.tileheight
        for idx, layer in enumerate(self.__map_data.layers):
            if not getattr(layer, 'visible', False):
                continue
            if isinstance(layer, TiledTileLayer):
                if layer.name == 'Ground':
                    for x, y, s in layer.tiles():
                        ground.image.blit(s, (x * tilewidth, y * tileheight))
                elif layer.name == 'Object' or layer.name == 'Behind':
                    layer_id = LayerId.OBJECT if layer.name == 'Object' else LayerId.BEHIND
                    for x, y, s in layer.tiles():
                        gid = self.__map_data.get_tile_gid(x, y, idx)
                        prop = self.__map_data.get_tile_properties_by_gid(gid)
                        if prop is None or 'frames' not in prop:
                            self.map_sprites.append(BasicSprite(s, layer=layer_id, topleft=(x * tilewidth, y * tileheight)))
                        else:
                            ent = EntityBase()
                            ent.add_component(BasicSprite, s, layer=layer_id, topleft=(x * tilewidth, y * tileheight))
                            ent.add_component(BasicAnimator, SpriteSheetImage.from_tile_animation(prop['frames'], self.__map_data))
                            self.map_sprites.append(ent.get_component(BasicSprite))
                            self.entities.append(ent)
            elif isinstance(layer, TiledObjectGroup):
                obj: TiledObject
                if layer.name == 'Collision':
                    for obj in layer:
                        rect = pg.rect.FRect(obj.x, obj.y, obj.width, obj.height)
                        self.collisions.append(rect)
                        
                elif layer.name == 'Marker':
                    for obj in layer:
                        obj: TiledObject
                        self.markers.setdefault(str(obj.name), []).append((obj.x, obj.y))
        self.template_nav = NavigationTemplateMap(self.collisions)

    @property    
    def tilewidth(self):
        """Width of the tile in pixel"""
        return self.__map_data.tilewidth
    
    @property
    def tileheight(self):
        """Height of the tile in pixel"""
        return self.__map_data.tileheight
    
    @property
    def mapwidth(self):
        """Width of the map in tiles"""
        return self.__map_data.width
    
    @property
    def mapheight(self):
        """Height of the map in tiles"""
        return self.__map_data.height

    @property
    def width(self):
        """Width of the map in pixel"""
        return self.__map_data.width * self.__map_data.tilewidth
    
    @property
    def height(self):
        """Height of the map in pixel"""
        return self.__map_data.height * self.__map_data.tileheight