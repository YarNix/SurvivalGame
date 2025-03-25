import pygame as pg
from SurvivalGame.const import *

class Button(pg.sprite.Sprite):
    def __init__(self, *groups, text="Button", font=None, pos=None, size=None, click=None, rect=None, border_radius = -1):
        super().__init__(groups)
        # Init button states
        self.click = click
        self.hover = False
        self.down = False
        self.primed = False
        # Init button text
        self.text = text
        self.font = font or pg.font.Font(None, 32)
        self.text_suface = self.font.render(text, True, CL_BTN_FOREGROUND)
        self.text_rect = self.text_suface.get_frect()
        # Init button
        self.border_radius = border_radius
        if (pos or size) and not rect:
            rectsize = {'x': size[0], 'y': size[1]} if size else (self.text_rect.size + pg.Vector2(NM_BTN_PADDING[0] + NM_BTN_PADDING[2], NM_BTN_PADDING[1] + NM_BTN_PADDING[3]))
            rectpos = pos - (rectsize.xy / 2) if pos else pg.Vector2(0, 0)
            self.rect = pg.rect.FRect((rectpos.x, rectpos.y, rectsize.x, rectsize.y))
        elif rect and not (pos or size):
            self.rect = pg.rect.FRect(rect)
        else:
            raise ValueError("Either rect is defined or pos and size is defined, but not both")
        self.image = pg.Surface(self.rect.size, pg.SRCALPHA)
        pg.draw.rect(self.image, CL_BTN_BACKGROUND, self.image.get_rect(), border_radius=self.border_radius)
        self.text_rect.center = self.image.get_frect().center
        self.image.blit(self.text_suface, self.text_rect)
        
        
    def update(self, events: list[pg.event.Event], **kwargs):
        hovering = self.hover
        downing = self.down
        for event in events:
            if event.type == pg.MOUSEMOTION:
                if self.rect.collidepoint(event.pos):
                    hovering = True
                else:
                    hovering = False
            elif event.type == pg.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
                self.primed = True
                downing = True
            elif event.type == pg.MOUSEBUTTONUP:
                downing = False
                if self.primed and self.rect.collidepoint(event.pos):
                    self.primed = False
                    if self.click:
                        self.click()

        if self.hover != hovering or self.down != downing:
            self.hover = hovering
            self.down = downing
            if self.down:
                pg.draw.rect(self.image, CL_BTN_CLICK, self.image.get_rect(), border_radius=self.border_radius)
            elif self.hover:
                pg.draw.rect(self.image, CL_BTN_HOVER, self.image.get_rect(), border_radius=self.border_radius)
            else:
                pg.draw.rect(self.image, CL_BTN_BACKGROUND, self.image.get_rect(), border_radius=self.border_radius)
            self.image.blit(self.text_suface, self.text_suface.get_rect(center=self.image.get_rect().center))