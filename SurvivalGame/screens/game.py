import random
import itertools
from SurvivalGame.components.pathfinder import PathFinder
from SurvivalGame.const import *
from SurvivalGame.components.sprites import Player, MouseTracking, Enemy
from SurvivalGame.components.camera import Camera
import pygame as pg
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer, TiledObjectGroup

class GameScreen:
    TILED_LAYER = 0
    OBJECT_LAYER = 2
    OVERLAY_LAYER = 4
    
    def __init__(self, game):
        # Loading the map with the player
        map = load_pygame(join(PT_MAP, "default_map.tmx"))
        self.map_collisions = []
        self.stage_width = map.width * map.tilewidth
        self.stage_height = map.height * map.tileheight

        self.all_sprites: dict[int, list[pg.sprite.Sprite]] = {self.TILED_LAYER: [], self.OBJECT_LAYER: [], self.OVERLAY_LAYER: []}

        self.tile_map = pg.sprite.Sprite()
        self.tile_map.image = pg.Surface((self.stage_width, self.stage_height))
        self.tile_map.rect = self.tile_map.image.get_frect()
        
        self.player = Player(collisions=self.map_collisions)
        # Setting the player to the center because the camera assume the player in centered
        self.player.set_pos(X_SCREEN_CENTER, Y_SCREEN_CENTER)
        camera = Camera(subject=self.player, background=self.tile_map)
        self.player.set_camera(camera)

        self.all_sprites[self.TILED_LAYER].append(self.tile_map)
        self.all_sprites[self.OBJECT_LAYER].append(self.player)

        crosshair_surf = pg.image.load(join(PT_SPRITE, 'Crosshair', 'Crosshair47.png'))
        crosshair_surf = pg.transform.scale(crosshair_surf, (25, 25))
        self.crosshair = MouseTracking(crosshair_surf)
        self.all_sprites[self.OVERLAY_LAYER].append(self.crosshair)
        pg.mouse.set_visible(False)

        self.enemy_spawn_event = pg.event.custom_type()
        pg.time.set_timer(self.enemy_spawn_event, 3000)
        self.enemy_spawns: list[tuple[int, int] | tuple[float, float]] = []

        for layer in map.layers:
            if layer.visible:
                if isinstance(layer, TiledTileLayer):
                    for x, y, s in layer.tiles():
                        self.tile_map.image.blit(s, (x * map.tilewidth, y * map.tileheight))
                elif isinstance(layer, TiledObjectGroup):
                    for obj in layer:
                        objspr = pg.sprite.Sprite()
                        objspr.image = obj.image
                        objspr.rect = objspr.image.get_frect(topleft=(obj.x, obj.y))
                        camera.add(objspr)
                        self.all_sprites[self.OBJECT_LAYER].append(objspr)
            else:
                cl = getattr(layer, 'class') if hasattr(layer, 'class') else ""
                if cl == 'Marking':
                    for obj in layer:
                        if obj.name == 'PlayerSpawn':
                            self.player.set_pos(obj.x, obj.y)
                        elif obj.name == 'EnemySpawn':
                            self.enemy_spawns.append((obj.x, obj.y))
                elif cl == 'Collision':
                    for obj in layer:
                        self.map_collisions.append(pg.rect.FRect(obj.x, obj.y, obj.width, obj.height))
                else:
                    print(f'Unknown {cl} layer found:', layer)

        self.map_finder = PathFinder(collisions=self.map_collisions)

        self.stage_music = pg.mixer.Sound(join(PT_AUDIO, "ost.mp3"))
        self.stage_music.set_volume(0.25)
        self.stage_music.play(-1, fade_ms=1500)

    def update(self, *args, **kwargs):
        for event in kwargs.get('events', []):
            if event.type == pg.WINDOWFOCUSLOST:
                self.stage_music.set_volume(0)
            elif event.type == pg.WINDOWFOCUSGAINED:
                self.stage_music.set_volume(0.2)
            elif event.type == self.enemy_spawn_event:
                enemy = Enemy(collisions=self.map_collisions, player=self.player, pathfind=self.map_finder, onkill=lambda spr: self.all_sprites[self.OBJECT_LAYER].remove(spr))
                spawn = (self.tile_map.rect.w / 2, self.tile_map.rect.h / 2)
                enemy.set_pos(spawn)
                self.player.camera.add(enemy)
                self.all_sprites[self.OBJECT_LAYER].append(enemy)

        for sprite in itertools.chain.from_iterable(self.all_sprites.values()):
            sprite.update(**kwargs)

        player_pos = self.player.rect.centery
        self.all_sprites[self.OBJECT_LAYER].sort(key=lambda spr: -1 if spr.rect.centery < player_pos else 0 if spr.rect.centery == player_pos else 1)
    
    def draw(self, surface: pg.Surface, _sub: list = []):
        for _, sprites in self.all_sprites.items():
            surface.blits((spr.image, spr.rect) for spr in sprites)
        surface.blit(MASK_BG)
        return _sub

