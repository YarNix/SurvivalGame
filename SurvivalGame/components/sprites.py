import math
import pygame as pg
from SurvivalGame.components.abstract import SpriteComponent
from SurvivalGame.const import *
from pytmx.util_pygame import load_pygame
from .camera import Camera
from .pathfinder import PathFinder
from .grid import SpatialHashGrid
from typing import Callable
from random import random
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

def generate_missing_surface(size: tuple[int, int] = (16, 16)) -> pg.Surface:
    surf = pg.Surface(size)
    surf.fill(CL_BLACK)
    _CELL_SIZE = 8
    cols = math.ceil(size[0] / _CELL_SIZE)
    rows = math.ceil(size[1] / _CELL_SIZE)
    for row in range(rows):
        for col in range(cols):
            if (row + col) % 2:
                x = col * _CELL_SIZE
                y = row * _CELL_SIZE
                w = min(_CELL_SIZE, size[0] - x)
                h = min(_CELL_SIZE, size[1] - y)
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
    def __init__(self, image: pg.Surface = generate_missing_surface(), **kwargs):
        super().__init__()
        self.image = image
        self.rect = self.image.get_frect(**kwargs)


def dir_from_polar(len_angle: tuple[float, float]):
    angle = (len_angle[1] + 45)
    return ['right', 'down', 'left', 'up'][int(angle // 90)]

def mousedir_relative_to(point: tuple[int, int]):
    return dir_from_polar((pg.Vector2(pg.mouse.get_pos()) - point).as_polar())

def point_isclose(a: tuple[int, int], b: tuple[int, int], *, rel_tol = 1e-4):
    import math
    return math.isclose(a[0], b[0], rel_tol=rel_tol) and math.isclose(a[1], b[1], rel_tol=rel_tol)

KeyFrame = tuple[pg.Surface, int]
class AnimatedSprite(pg.sprite.Sprite):
    def __init__(self, frames: list[KeyFrame], *groups):
        super().__init__(*groups)
        self.keyframes = frames
        self.frame_index = 0
        self.image, self._duration = self.keyframes[self.frame_index]
        self.rect = self.image.get_frect()
        self.elapsed_time = 0
        self.looped = 0

    def update(self, dt, **kwargs):
        self.elapsed_time += dt * 1000
        while self.elapsed_time >= self._duration:
            self.elapsed_time -= self._duration
            self.frame_index = (self.frame_index + 1)
            if self.frame_index >= len(self.keyframes):
                self.frame_index = 0
                self.looped += 1
            self.image, self._duration = self.keyframes[self.frame_index]

    def restart(self, from_index=0):
        self.frame_index = from_index
        self.image, self._duration = self.keyframes[self.frame_index]
        self.looped = 0

class _TmxSprite:
    
    type SpriteTemplate = tuple[list[KeyFrame], pg.Rect]
    type TileDataDict = dict[str, list[SpriteTemplate]]
    LOADED: dict[str, tuple[int, int, int, int, list[str], list[str], TileDataDict]] = {}
    def __init__(self, file: str):
        self.tile_states: dict[str, list[AnimatedSprite]] = {}
        self.atlas_width, self.atlas_height, self.sub_width, self.sub_height, self.row_states, self.col_states, self.tileDict = self.load_sprites(file)
        self.image_atlas = pg.Surface((self.atlas_width, self.atlas_height), pg.SRCALPHA)
        self.atlas_rect = pg.FRect(0, 0, self.sub_width, self.sub_height)
        for state, templates in self.tileDict.items():
            sprites = self.tile_states.setdefault(state, [])
            for frames, rect in templates:
                sprite = AnimatedSprite(frames)
                sprite.rect = rect
                sprites.append(sprite)
    def load_sprites(self, file: str) -> tuple[int, int, int, int, list[str], list[str], TileDataDict]:
        if file in self.LOADED:
            return self.LOADED[file]
        data = load_pygame(file)
        atlas_width, atlas_height = data.width * data.tilewidth, data.height * data.tileheight
        sub_width, sub_height = int(data.properties.get('GroupWidth', 0)) * data.tilewidth, int(data.properties.get('GroupHeight', 0)) * data.tileheight
        row_states: list[str] = str(data.properties.get('RowStates')).split(', ')
        col_states: list[str] = str(data.properties.get('ColumnStates')).split(', ')
        tile_data: _TmxSprite.TileDataDict = self.LOADED.setdefault(file, (atlas_width, atlas_height, sub_width, sub_height, row_states, col_states, dict()))[6]
        for idx, layer in enumerate(data.layers):
            if not layer.visible:
                continue
            props: dict
            for gid, props in data.get_tile_properties_by_layer(idx):
                _, width, height, frames = props.values()
                tileset = data.get_tileset_from_gid(gid)
                if tileset.name not in row_states and tileset.name not in col_states:
                    continue
                spr_templates = tile_data.setdefault(tileset.name, [])
                keyframes = [(data.get_tile_image_by_gid(frame.gid), frame.duration) for frame in frames]
                for x, y, _ in data.get_tile_locations_by_gid(gid):
                    spr_templates.append((keyframes, pg.rect.Rect(data.tilewidth * x, data.tileheight * y, width, height)))
        return (atlas_width, atlas_height, sub_width, sub_height, row_states, col_states, tile_data)
        
class AbstractEntity:
    """
    An abstract class that represent entities in a world
    The entity can move and collide with things in the world
    """
    def __init__(self, width = 10, height = 10, x = 0, y = 0, speed = 200, collision_grid: SpatialHashGrid | None = None):
        self.state_rect = pg.FRect(0, 0, width, height)
        self.state_rect.center = (x, y)
        self.direction = pg.Vector2(0, 0)
        self.speed = speed
        self.collision_grid = collision_grid
        if collision_grid:
            collision_grid.add(self)

    def update_movement(self, dt: float) -> pg.Vector2:
        """
        Process the entity movement within the time delta
        
        returns the vector of displacement applied to the entity
        """
        # Checking for collision
        if self.collision_grid:
            k_x = 1
            k_y = 1
            offset = self.direction * self.speed * dt
            new_rect = self.state_rect.copy()
            new_rect.center += offset
            DIST_TOL = 1e-4
            for obj, owner in self.collision_grid.get_neighbours(self.state_rect):
                if not new_rect.colliderect(obj):
                    continue
                if obj.colliderect(self.state_rect):
                    if owner is None:
                        # Edge case where the entity is already
                        # inside the collision rect for more than a tick
                        continue
                    elif isinstance(owner, AbstractEntity):
                        # Entity is inside another entity
                        # apply a force to seperate them
                        sep_dir = self.get_rect().center - pg.Vector2(owner.get_rect().center)
                        SEP_FORCE = 5
                        if sep_dir.xy == (0, 0):
                            sep_dir.update(SEP_FORCE, 0)
                            sep_dir.rotate_ip(random() * 360)
                        else:
                            sep_dir.scale_to_length(SEP_FORCE)
                        print(f'Detected {obj} inside, applying {sep_dir}')
                        self.direction += sep_dir
                        offset = self.direction * self.speed * dt
                        
                if self.direction.x != 0:
                    dist = (obj.left - self.state_rect.right) if self.direction.x > 0 else (self.state_rect.left - obj.right)
                    if abs(dist) > DIST_TOL:
                        k_x = min(k_x, abs(dist / offset.x))
                    else:
                        k_x = 0
                if self.direction.y != 0:
                    dist = (obj.top - self.state_rect.bottom) if self.direction.y > 0 else (self.state_rect.top - obj.bottom)
                    if abs(dist) > DIST_TOL:
                        k_y = min(k_y, abs(dist / offset.y))
                    else:
                        k_y = 0

        # Updating movement
        offset.x *= k_x
        offset.y *= k_y
        self.move_pos(offset)
        return offset
    
    def set_pos(self, x: float | int | tuple[float | int], y: float | int | None = None):
        # Updating postion
        self.collision_grid.remove(self)
        if isinstance(x, tuple):
            offset = pg.Vector2(x) - self.state_rect.center
            self.state_rect.center = x
        else:
            offset = pg.Vector2(x, y or 0) - self.state_rect.center
            self.state_rect.center = (x, y or 0)
        self.collision_grid.add(self)
        # Updating other position attached properties
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.update(offset)
        elif hasattr(self, 'rect') and self.rect is not None:
            self.rect.center += offset

    def move_pos(self, x: float | int | tuple[float | int], y: float | int | None = None):
        if isinstance(x, tuple):
            offset = pg.Vector2(x)
        else:
            offset = pg.Vector2(x, y or 0)
        # Updating postion
        self.collision_grid.remove(self)
        self.state_rect.center += offset
        self.collision_grid.add(self)
        # Updating other position attached properties
        if hasattr(self, 'camera') and self.camera is not None:
            self.camera.update(offset)
        elif hasattr(self, 'rect') and self.rect is not None:
            self.rect.center += offset

    def get_pos(self) -> tuple[float | int, float | int]:
        return self.state_rect.center
    
    def get_rect(self) -> pg.FRect:
        """Get the rect representing the entity"""
        return self.state_rect


class Player(pg.sprite.Sprite, _TmxSprite, AbstractEntity):
    def __init__(self, *groups, collisions: list[pg.rect.FRect]):
        super().__init__(groups)
        # Loading player images
        _TmxSprite.__init__(self, join(PT_SPRITE, "Player", "Base_boy.tmx"))
        self.state_row, self.state_col = 0, 0
        self.scaled = 2
        
        self.image = pg.Surface(pg.Vector2(self.sub_width, self.sub_height) * self.scaled, pg.SRCALPHA)
        self.rect = self.image.get_frect(center=(0, 0)) # Align the image with the default position
        self.camera: Camera | None = None

        # Initialize player state
        AbstractEntity.__init__(self, 11 * self.scaled, 13 * self.scaled, -0.5, 4.5, collision_grid = collisions)
        self.desire_direction = pg.Vector2()
        self.attacking, self.damaged = False, False
        self.attack_mask: None | pg.mask.Mask = None
        self.locked_state = -1

        # Initialize player timer
        self.attack_event = pg.event.custom_type()
        pg.time.set_timer(self.attack_event, 1500)
    
    def set_camera(self, cam: Camera):
        self.camera = cam

    def update(self, *, dt: float, events: list[pg.Event], global_var: dict, **kwargs):
        # Handling key events
        event_attacking = False
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_w:
                    self.desire_direction.y += -1
                elif event.key == pg.K_s:
                    self.desire_direction.y += 1
                elif event.key == pg.K_a:
                    self.desire_direction.x += -1
                elif event.key == pg.K_d:
                    self.desire_direction.x += 1
            elif event.type == pg.KEYUP:
                if event.key == pg.K_w:
                    self.desire_direction.y += 1
                elif event.key == pg.K_s:
                    self.desire_direction.y += -1
                elif event.key == pg.K_a:
                    self.desire_direction.x += 1
                elif event.key == pg.K_d:
                    self.desire_direction.x += -1
            elif event.type == self.attack_event:
                event_attacking = True

        self.direction = self.desire_direction.normalize() if self.desire_direction.length_squared() != 0 else self.desire_direction

        if global_var['debug'] and not global_var['update_step']:
            # Stop updating
            return
        offset = self.update_movement(dt)

        # Updating animations
        for spr in self.tile_states[self.col_states[self.state_col]]:
            spr.update(dt=dt)
            
        # Check if animation need to reset to a new state
        if self.attacking and self.tile_states[self.col_states[self.col_states.index('Sword_Walk_Attack')]][0].looped != 0:
            self.attacking = False
        elif event_attacking:
            self.attacking = True
            self.locked_state = self.row_states.index(mousedir_relative_to(self.rect.center))
        
        if self.attacking:
            row = self.locked_state
            col = self.col_states.index('Sword_Walk_Attack')
        elif self.direction.x == 0:
            if self.direction.y == 0:
                row = self.row_states.index(mousedir_relative_to(self.rect.center))
                col = self.col_states.index('Sword_Idle')
            else:
                row = self.row_states.index('down' if self.direction.y > 0 else 'up')
                col = self.col_states.index('Sword_Walk')
        else:
            row = self.row_states.index('right' if self.direction.x > 0 else 'left')
            col = self.col_states.index('Sword_Walk')

        if self.state_row != row or self.state_col != col:
            self.state_row, self.state_col = row, col
            for spr in self.tile_states[self.col_states[col]]:
                spr.restart()
        
        # Drawing new animations
        self.image_atlas.fill(CL_TRANS)
        for spr in self.tile_states[self.col_states[self.state_col]]:
            self.image_atlas.blit(spr.image, spr.rect)
        pg.transform.scale_by(self.image_atlas.subsurface(self.state_col * self.sub_width, self.state_row * self.sub_height, self.sub_width, self.sub_height), self.scaled, self.image)
        
        if self.attacking and self.tile_states[self.col_states[self.state_col]][0].frame_index == 2:
            self.attack_mask = pg.mask.from_surface(self.image)
        else:
            self.attack_mask = None
    

class Enemy(pg.sprite.Sprite, _TmxSprite, AbstractEntity):
    def __init__(self, *groups, collisions: list[pg.rect.FRect] = [], player: Player | None = None, pathfind: PathFinder | None = None, onkill: Callable[['Enemy'], None] | None = None):
        super().__init__(*groups)
        _TmxSprite.__init__(self, join(PT_SPRITE, "Orcs", "Orc1.tmx"))
        self.state_row, self.state_col = 0, 0
        self.scaled = 1.75
         
        for state in self.tile_states.keys():
            if state.endswith('idle_full'):
                self.IDLE_STATE = state
            elif state.endswith('walk_full'):
                self.WALK_STATE = state
            elif state.endswith('hurt_full'):
                self.HURT_STATE = state
            elif state.endswith('death_full'):
                self.DEAD_STATE = state
        
        self.image = pg.Surface(pg.Vector2(self.sub_width, self.sub_height) * self.scaled, pg.SRCALPHA)
        # Align the image with the default position
        self.rect = self.image.get_frect(center = (0, 0) if player.camera is None else player.camera.background.rect.topleft)

        # Initialize enemy state
        AbstractEntity.__init__(self, 16 * self.scaled, 20 * self.scaled, -0.5, -1, speed=100, collision_grid = collisions)
        self.health = 100
        self.damaged, self.missed = False, False
        self.player = player
        self.pathfind = pathfind
        self.onkill = onkill
        self.update_path = False
        self.cached_path = None
        self.groups()

    def update(self, *, dt: float, global_var: dict, **kwargs):
        if global_var['draw_path']:
            surf = global_var['debug_surf']
            if self.cached_path:
                path = self.cached_path + [self.get_pos()]
                camoffset = pg.Vector2(self.player.camera.background.rect.topleft)
                for pA, pB in zip(path, path[1:]):
                    pg.draw.aaline(surf, CL_WHITE, pA + camoffset, pB + camoffset, 3)
        if global_var['debug'] and not global_var['update_step']:
            # Stop updating
            return
        if self.health > 0: # Skip movement if dying
            state_vec = pg.Vector2(self.get_pos())
            # Check if path needs updating
            if not self.update_path and self.cached_path:
                to_player_angle = (state_vec - self.player.get_pos()).as_polar()[1]
                to_target_angle = (state_vec - self.cached_path[0]).as_polar()[1]
                angle = abs(to_player_angle - to_target_angle) % 180
                if angle > 45:
                    # print('Changed mind; {:.2f} diff {:.2f}'.format(to_player_angle, to_target_angle), end=' ')
                    self.update_path = True
                pass

            next_target = None
            if self.update_path or not self.cached_path:
                global_var['path_calls'] = global_var.get('path_calls', 0) + 1
                self.cached_path, self.update_path = self.pathfind.get_path(self.state_rect, self.player.state_rect)
                if self.cached_path:
                    next_target = self.cached_path[-1]
                #print('Walking to', next_target or 'None')
                # if next_target is None:
                #     global_var['debug'] = True
            elif self.cached_path:
                next_target = self.cached_path[-1]
            
            if next_target is not None:
                to_target_vec = next_target - state_vec
                to_target_len = to_target_vec.length()
            elif self.player:
                to_target_vec = self.player.get_pos() - state_vec
                to_target_len = to_target_vec.length()
                self.direction.update(to_target_vec)
            else:
                to_target_len = INF
                self.direction.update(0, 0)
            if self.direction != (0, 0):
                self.direction.normalize_ip()
            offset = self.update_movement(dt)
            if offset.length() >= to_target_len:
                self.cached_path.pop()
                #print('Path walked.', end=' ')

        # Updating animations
        for spr in self.tile_states[self.row_states[self.state_row]]:
            spr.update(dt=dt)

        # Check if animation need to reset to a new state
        if self.direction.x == 0:
            if self.direction.y == 0:
                col = self.state_col
                row = self.state_row
            else:
                col = self.col_states.index(dir_from_polar(self.direction.as_polar()))
                row = self.row_states.index(self.WALK_STATE)
        else:
            col = self.col_states.index(dir_from_polar(self.direction.as_polar()))
            row = self.row_states.index(self.WALK_STATE)

        if self.health <= 0:
            if self.collision_grid:
                self.collision_grid.remove(self)
                self.collision_grid = None
            if self.tile_states[self.DEAD_STATE][0].looped != 0 and self.onkill:
                self.onkill(self)
                return

        if self.damaged and self.tile_states[self.HURT_STATE][0].looped != 0:
            self.damaged = False

        if self.player.attacking:
            if self.player.attack_mask is not None and not (self.missed or self.damaged):
                hitbox = pg.Mask(self.state_rect.size, True)
                offset = self.state_rect.center - (self.player.state_rect.center - pg.Vector2(self.player.rect.size) / 2)
                if self.player.rect.colliderect(self.rect) and self.player.attack_mask.overlap(hitbox, offset):
                    self.damaged = True
                    self.health -= 50
                else:
                    self.missed = True
        else:
            self.missed = False
                    
        if self.health <= 0:
            row = self.row_states.index(self.DEAD_STATE)
        elif self.damaged:
            row = self.row_states.index(self.HURT_STATE)

        if self.state_row != row or self.state_col != col:
            self.state_row, self.state_col = row, col
            for spr in self.tile_states[self.row_states[self.state_row]]:
                spr.restart()

        # Drawing new animations
        self.image_atlas.fill(CL_TRANS)
        for spr in self.tile_states[self.row_states[self.state_row]]:
            self.image_atlas.blit(spr.image, spr.rect)
        pg.transform.scale_by(self.image_atlas.subsurface(self.state_col * self.sub_width, self.state_row * self.sub_height, self.sub_width, self.sub_height), self.scaled, self.image)



class MouseTracking(pg.sprite.Sprite):
    def __init__(self, surf: pg.Surface, *groups):
        super().__init__(*groups)
        self.image = surf
        self.rect = surf.get_frect(center=pg.mouse.get_pos())
        self.active = True

    def update(self, events, **kwargs):
        if not self.active:
            return
        for event in events:
            if event.type == pg.MOUSEMOTION:
                self.rect.center = event.pos


