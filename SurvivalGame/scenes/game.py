import pygame as pg

class GameScene:
    
    def __init__(self, game):
        # Loading the map with the player
        pass

    def update(self, *args, **kwargs):
        # for event in kwargs.get('events', []):
        #     if event.type == pg.WINDOWFOCUSLOST:
        #         self.stage_music.set_volume(0)
        #     elif event.type == pg.WINDOWFOCUSGAINED:
        #         self.stage_music.set_volume(0.2)
        #     elif event.type == self.enemy_spawn_event and not self.global_var['debug']:
        #         self.do_spawn_enemy()
        #     elif event.type == pg.KEYDOWN and event.key == pg.K_p and event.mod == pg.KMOD_LCTRL:
        #         # Debugging
        #         self.global_var['debug'] = not self.global_var['debug']
        pass
    
    def draw(self, surface: pg.Surface, _sub: list = []):
        pass

