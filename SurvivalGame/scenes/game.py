import random
import itertools
from SurvivalGame.components.pathfinder import PathFinder
from SurvivalGame.const import *
from SurvivalGame.components.sprites import Player, MouseTracking, Enemy
from SurvivalGame.components.camera import Camera
from SurvivalGame.components.ui import Button
from SurvivalGame.components.grid import SpatialHashGrid
import pygame as pg
from pytmx.util_pygame import load_pygame
from pytmx.pytmx import TiledTileLayer, TiledObjectGroup

class GameScene:
    TILED_LAYER = 0
    OBJECT_LAYER = 2
    OVERLAY_LAYER = 4
    
    def __init__(self, game):
        # Loading the map with the player
        map = load_pygame(join(PT_MAP, "default_map.tmx"))
        map_collisions = []
        self.grid_collisions = SpatialHashGrid()
        self.stage_width = map.width * map.tilewidth
        self.stage_height = map.height * map.tileheight

        self.all_sprites: dict[int, list[pg.sprite.Sprite]] = {self.TILED_LAYER: [], self.OBJECT_LAYER: [], self.OVERLAY_LAYER: []}

        self.tile_map = pg.sprite.Sprite()
        self.tile_map.image = pg.Surface((self.stage_width, self.stage_height))
        self.tile_map.rect = self.tile_map.image.get_frect()
        
        self.player = Player(collisions=self.grid_collisions)
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
        #pg.time.set_timer(self.enemy_spawn_event, 1500)
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
                        rect = pg.rect.FRect(obj.x, obj.y, obj.width, obj.height)
                        map_collisions.append(rect)
                        self.grid_collisions.add(rect)
                else:
                    print(f'Unknown {cl} layer found:', layer)

        self.map_finder = PathFinder(collisions=map_collisions)

        self.stage_music = pg.mixer.Sound(join(PT_AUDIO, "ost.mp3"))
        self.stage_music.set_volume(0.25)
        self.stage_music.play(-1, fade_ms=1500)

        self.global_var = {'debug': False, 'draw_path': False, 'draw_coll': False, 'update_step': False, 'debug_surf': pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)}
        
        debug_overlay = pg.sprite.Sprite()
        debug_overlay.image = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)
        debug_overlay.rect = debug_overlay.image.get_frect()
        self.global_var['debug_surf'] = debug_overlay.image
        self.all_sprites[self.OVERLAY_LAYER].insert(0, debug_overlay)
        self.debug_menu = pg.sprite.Group()
        Button(self.debug_menu, text='Spawn Enemy', pos=(X_SCREEN_CENTER, Y_SCREEN_CENTER - 50), click=self.do_spawn_enemy)
        Button(self.debug_menu, text='Step', pos=(X_SCREEN_CENTER, Y_SCREEN_CENTER), click=lambda: self.global_var.update([('update_step', not self.global_var.get('update_step'))]))
        Button(self.debug_menu, text='Toggle Path', pos=(X_SCREEN_CENTER, Y_SCREEN_CENTER + 50), click=lambda: self.global_var.update([('draw_path', not self.global_var.get('draw_path'))]))
        Button(self.debug_menu, text='Toggle Collision', pos=(X_SCREEN_CENTER, Y_SCREEN_CENTER + 100), click=lambda: self.global_var.update([('draw_coll', not self.global_var.get('draw_coll'))]))

    def do_spawn_enemy(self):
        enemy = Enemy(collisions=self.grid_collisions, player=self.player, pathfind=self.map_finder, onkill=lambda spr: self.all_sprites[self.OBJECT_LAYER].remove(spr))
        map = self.player.camera.background.rect
        visible = pg.FRect(-map.left, -map.top, SCREEN_WIDTH, SCREEN_HEIGHT)
        spawns = [s for s in self.enemy_spawns if not visible.collidepoint(s)] or self.enemy_spawns
        enemy.set_pos((200, 300))
        self.player.camera.add(enemy)
        self.all_sprites[self.OBJECT_LAYER].append(enemy)

    def update(self, *args, **kwargs):
        for event in kwargs.get('events', []):
            if event.type == pg.WINDOWFOCUSLOST:
                self.stage_music.set_volume(0)
            elif event.type == pg.WINDOWFOCUSGAINED:
                self.stage_music.set_volume(0.2)
            elif event.type == self.enemy_spawn_event and not self.global_var['debug']:
                self.do_spawn_enemy()
            elif event.type == pg.KEYDOWN and event.key == pg.K_p and event.mod == pg.KMOD_LCTRL:
                # Debugging
                self.global_var['debug'] = not self.global_var['debug']

        kwargs.setdefault('global_var', self.global_var)
        self.global_var['path_calls'] = 0

        if self.global_var['debug']:
            self.global_var['debug_surf'].fill((80, 80, 80, 100))
        else:
            self.global_var['debug_surf'].fill(CL_TRANS)
        
        for sprite in itertools.chain.from_iterable(self.all_sprites.values()):
            sprite.update(**kwargs)
        self.global_var['update_step'] = False
        if self.global_var['debug']:
            self.debug_menu.update(**kwargs)

        player_pos = self.player.rect.centery
        self.all_sprites[self.OBJECT_LAYER].sort(key=lambda spr: spr.rect.centery)
    
    def draw(self, surface: pg.Surface, _sub: list = []):
        if self.global_var['draw_path']:
            surf = self.global_var['debug_surf']
            f = pg.Font(size=30)
            t = "Calls: " + str(self.global_var['path_calls'])
            lineheight = float(max((m[3] for m in f.metrics(t))))
            surf.blit(f.render(t, True, (255, 10, 10)))
            self.global_var['max_calls'] = max(self.global_var.setdefault('max_calls', 0), self.global_var['path_calls'])
            surf.blit(f.render("Max Calls: " + str(self.global_var['max_calls']), True, (255, 10, 10)), (0, lineheight + 5))

        if self.global_var['draw_coll']:
            surf = self.global_var['debug_surf']
            x, y = self.player.get_pos()
            scr_offset = pg.Vector2(self.player.camera.background.rect.topleft)
            xstart = int(x // CELL_SIZE - 1)
            ystart = int(y // CELL_SIZE - 1)
            for i in range(xstart, xstart + 4):
                start = (i * CELL_SIZE, ystart * CELL_SIZE) + scr_offset
                end = (i * CELL_SIZE, (ystart + 3) * CELL_SIZE) + scr_offset
                pg.draw.line(surf, CL_WHITE, start, end)
            for i in range(ystart, ystart + 4):
                start = (xstart * CELL_SIZE, i * CELL_SIZE) + scr_offset
                end = ((xstart + 3) * CELL_SIZE, i * CELL_SIZE) + scr_offset
                pg.draw.line(surf, CL_WHITE, start, end)
            for o, _ in self.grid_collisions.get_neighbours(self.player.state_rect):
                pg.draw.rect(surf, CL_LGRAY, o.move(scr_offset))

        for _, sprites in self.all_sprites.items():
            surface.blits((spr.image, spr.rect) for spr in sprites)
        
        if self.global_var['debug']:
            self.debug_menu.draw(surface)
        
        return _sub

