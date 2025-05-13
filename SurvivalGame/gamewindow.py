import pygame as pg

from SurvivalGame.statemgr import *
from .const import *

class SurvivalGame:
    def __init__(self, *, title=None):
        # init pygame
        pg.init()
        self.screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = False
        if title is None:
            title = "SPKT"
        pg.display.set_caption(title)

        self.text_font = pg.font.Font(join(PT_FONT, "pixel_font.otf"), 42)

        self.pause = False

        self.statemgr = StateManager(self, game=GameScene, menu=MenuScene, demo=Demo)
        self.statemgr.setactive("demo")

    def run(self):
        self.running = True
        while self.running:
            if len(pg.event.get(pg.QUIT)):
                self.running = False
                break
            events = pg.event.get()
            dt = min(self.clock.tick(TICK_RATE) / 1000, 1.0)
            
            self.screen.fill(CL_BLACK)
            if self.statemgr.current:
                self.statemgr.current.update(dt=dt, events=events)
                self.statemgr.current.draw(self.screen)
            pg.display.update()
        pg.quit()
        pass