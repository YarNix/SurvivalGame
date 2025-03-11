import pygame as pg
from .colors import *
from random import random
import math

class SurvivalGame:
    def __init__(self, *, title=None):
        self.SCREEN_WIDTH = 1000
        self.SCREEN_HEIGHT = 600
        self.TICK_RATE = 60
        # init pygame
        pg.init()
        self.screen = pg.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = False
        if title is None:
            title = "SPKT"
        pg.display.set_caption(title)

        self.lpad = pg.Surface((20, 80))
        self.lpad_frect = self.lpad.get_frect(midleft=(0, self.SCREEN_HEIGHT / 2))
        self.lpad.fill(CL_WHITE)
        self.lpad_dir = pg.Vector2()
        
        self.rpad = pg.Surface((20, 80))
        self.rpad_frect = self.rpad.get_frect(midright=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT / 2))
        self.rpad.fill(CL_WHITE)
        self.rpad_dir = pg.Vector2()

        self.PAD_SPD = 240

        self.circle_rad = 10
        self.circle_suf = pg.Surface((self.circle_rad * 2, self.circle_rad * 2))
        pg.draw.circle(self.circle_suf, CL_WHITE, (self.circle_rad, self.circle_rad), self.circle_rad)
        self.circle_frect = self.circle_suf.get_frect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
        self.circle_dir = pg.Vector2(1 if random() > 0.5 else -1, random()).normalize()
        self.DEFAULT_SPD = 320
        self.circle_spd_min = 300
        self.circle_spd_max = 1500
        self.circle_spd = self.DEFAULT_SPD

        self.font = pg.Font(None, 80)
        self.lwin = 0
        self.rwin = 0
        self.score: pg.Surface = self.font.render("0   -   0", True, CL_WHITE)
        self.score_rect = self.score.get_frect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))

        self.pause = False
        pass
    
    def handle_events(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.lpad_dir.y += 1
                elif event.key == pg.K_w:
                    self.lpad_dir.y += -1
                elif event.key == pg.K_DOWN:
                    self.rpad_dir.y += 1
                elif event.key == pg.K_UP:
                    self.rpad_dir.y += -1
                elif event.key == pg.K_ESCAPE:
                    self.pause = not self.pause
            if event.type == pg.KEYUP:
                if event.key == pg.K_s:
                    self.lpad_dir.y -= 1
                elif event.key == pg.K_w:
                    self.lpad_dir.y -= -1
                elif event.key == pg.K_DOWN:
                    self.rpad_dir.y -= 1
                elif event.key == pg.K_UP:
                    self.rpad_dir.y -= -1
        pass

    def run(self):
        self.running = True
        while self.running:
            self.handle_events()
            dt = self.clock.tick(self.TICK_RATE) / 1000
            if self.pause:
                pg.display.update()
                continue
            self.lpad_frect.center += self.lpad_dir * self.PAD_SPD * dt
            self.rpad_frect.center += self.rpad_dir * self.PAD_SPD * dt
            self.circle_frect.center += self.circle_dir * self.circle_spd * dt
            if self.circle_frect.top < 0 or self.circle_frect.bottom > self.SCREEN_HEIGHT:
                if self.circle_frect.top < 0:
                    self.circle_frect.top = 0
                else:
                    self.circle_frect.bottom = self.SCREEN_HEIGHT
                self.circle_dir.y = -self.circle_dir.y
                if self.circle_spd > self.circle_spd_min:
                    self.circle_spd -= 5
            if self.circle_frect.right < 0 or self.circle_frect.left > self.SCREEN_WIDTH:
                if self.circle_frect.right < 0:
                    self.rwin += 1
                elif self.circle_frect.left > self.SCREEN_WIDTH:
                    self.lwin += 1
                self.score = self.font.render(f"{self.lwin}   -   {self.rwin}", True, CL_WHITE)
                self.score_rect = self.score.get_frect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
                self.lpad_frect = self.lpad.get_frect(midleft=(0, self.SCREEN_HEIGHT / 2))
                self.rpad_frect = self.rpad.get_frect(midright=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT / 2))
                self.circle_frect = self.circle_suf.get_frect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))
                self.circle_dir = pg.Vector2(1 if random() > 0.5 else -1, random()).normalize()
                self.circle_spd = self.DEFAULT_SPD
            if self.circle_frect.colliderect(self.lpad_frect):
                self.circle_dir.x = abs(self.circle_dir.x)
                if self.lpad_dir.y != 0:
                    self.circle_dir.y += self.lpad_dir.y * 0.2
                    self.circle_dir.normalize_ip()
                if self.circle_spd < self.circle_spd_max:
                    self.circle_spd += 15
            elif self.circle_frect.colliderect(self.rpad_frect):
                self.circle_dir.x = -abs(self.circle_dir.x)
                if self.rpad_dir.y != 0:
                    self.circle_dir.y += self.rpad_dir.y * 0.2
                    self.circle_dir.normalize_ip()
                if self.circle_spd < self.circle_spd_max:
                    self.circle_spd += 15
            

            self.screen.fill(CL_BLACK)
            self.screen.blits([(self.score, self.score_rect), (self.lpad, self.lpad_frect), (self.rpad, self.rpad_frect), (self.circle_suf, self.circle_frect)])

            
            
            
            pg.display.update()
            #print(self.circle_spd)
        pg.quit()
        pass