from SurvivalGame.const import *

class StateComponent:
    def __init__(self, health = 100.0, damaged = False, dead = False) -> None:
        self.health = health
        self.damage = damaged
        self.dead = dead

