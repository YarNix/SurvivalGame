import math
import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent
from SurvivalGame.components.render import LayerId
from SurvivalGame.const import *
from SurvivalGame.typing import *
from pathlib import Path
import yaml
from pytmx.pytmx import AnimationFrame, TiledMap


class SpriteSlice(yaml.YAMLObject):
    yaml_tag = '!SpriteSlice'
    def __init__(self, name: str, rect: BaseRect):
        self.name = name
        self.rect = rect

class SpriteSheet(yaml.YAMLObject):
    yaml_tag = '!SpriteSheet'
    def __init__(self, sprites: list[SpriteSlice], states: dict[str, AnimationData]):
        self.sprites = sprites
        self.states = states

def generate_missing_surface(size: tuple[int, int] = (16, 16), cell_size = 8) -> pg.Surface:
    surf = pg.Surface(size)
    surf.fill(CL_BLACK)
    cols = math.ceil(size[0] / cell_size)
    rows = math.ceil(size[1] / cell_size)
    for row in range(rows):
        for col in range(cols):
            if (row + col) % 2:
                x = col * cell_size
                y = row * cell_size
                w = min(cell_size, size[0] - x)
                h = min(cell_size, size[1] - y)
                pg.draw.rect(surf, (255, 0, 220), pg.Rect(x, y, w, h))
    return surf

class SpriteSheetImage:
    LOADED: dict[str, 'SpriteSheetImage'] = {}
    def __init__(self, sprites: dict[str, pg.Surface] = {}, states: dict[str, AnimationData] = {}):
        self.sprites = sprites
        self.states = states

    @staticmethod
    def from_yaml(source):
        if source not in SpriteSheetImage.LOADED:
            src_path = Path(source)
            sheet: SpriteSheet = yaml.load(src_path.with_name(src_path.name + '.spdt').open(), yaml.Loader)
            image = pg.image.load(src_path)
            sprites = {
                spr.name: image.subsurface(spr.rect[0], image.height - spr.rect[1] - spr.rect[3], spr.rect[2], spr.rect[3])
                for spr in sheet.sprites
            }
            SpriteSheetImage.LOADED[source] = SpriteSheetImage(sprites, sheet.states)
        return SpriteSheetImage.LOADED[source]
    
    @staticmethod
    def from_tile_animation(animation: list[AnimationFrame], map: TiledMap):
        sprites = {}
        frames = []
        for idx, frame in enumerate(animation):
            surface: pg.Surface = map.get_tile_image_by_gid(frame.gid) or generate_missing_surface()
            sprites[str(idx)] = surface
            frames.append((str(idx), frame.duration))
        return SpriteSheetImage(sprites, {'default': frames})

class BasicSprite(SpriteComponent):
    LAYER = LayerId.DEFAULT
    def __init__(self, image: pg.Surface = generate_missing_surface(), *, layer=LAYER, **kwargs):
        super().__init__()
        self.image = image
        self.rect = self.image.get_frect(**kwargs)
        if layer != BasicSprite.LAYER:
            self.__dict__.setdefault('LAYER', layer)


def dir_from_polar(len_angle: tuple[float, float]):
    angle = (len_angle[1] + 45)
    return ['right', 'down', 'left', 'up'][int(angle // 90)]

def mousedir_relative_to(point: tuple[int, int]):
    return dir_from_polar((pg.Vector2(pg.mouse.get_pos()) - point).as_polar())

def point_isclose(a: tuple[int, int], b: tuple[int, int], *, rel_tol = 1e-4):
    import math
    return math.isclose(a[0], b[0], rel_tol=rel_tol) and math.isclose(a[1], b[1], rel_tol=rel_tol)

# class MouseTracking(pg.sprite.Sprite):
#     def __init__(self, surf: pg.Surface, *groups):
#         super().__init__(*groups)
#         self.image = surf
#         self.rect = surf.get_frect(center=pg.mouse.get_pos())
#         self.active = True

#     def update(self, events, **kwargs):
#         if not self.active:
#             return
#         for event in events:
#             if event.type == pg.MOUSEMOTION:
#                 self.rect.center = event.pos


