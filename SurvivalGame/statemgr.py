from typing import Type
from SurvivalGame.scenes.abstract import AbstractScene

class StateManager():
    def __init__(self, _instance, **kwargs):
        self.current: AbstractScene | None = None
        self.game = _instance
        self.registered: dict[str, Type[AbstractScene]] = {
            name: state for name, state in kwargs.items() if isinstance(state, type)
        }

    def register(self, name: str, state: Type[AbstractScene]):
        self.registered[name] = state

    def setactive(self, name: str):
        if name in self.registered:
            self.current = self.registered[name](game=self.game)

from SurvivalGame.scenes.game import GameScene
from SurvivalGame.scenes.menu import MenuScene
from SurvivalGame.scenes.demo import Demo