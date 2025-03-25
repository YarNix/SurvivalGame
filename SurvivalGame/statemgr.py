import pygame as pg
from typing import Union
from SurvivalGame.screens.abstract import AbstractScreen

class StateManager():
    def __init__(self, _instance, **kwargs):
        self.current: AbstractScreen | None = None
        self.__game = _instance
        self.__registered: dict[str, AbstractScreen] = {
            name: state for name, state in kwargs.items() if isinstance(state, type)
        }

    def register(self, name: str, state: AbstractScreen):
        self.__registered[name] = state

    def setactive(self, name: str):
        if name in self.__registered:
            self.current = self.__registered[name](game=self.__game)

from SurvivalGame.screens.game import GameScreen
from SurvivalGame.screens.menu import MenuScreen
from SurvivalGame.screens.demo import Demo