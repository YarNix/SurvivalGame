from abc import ABC, abstractmethod
import pygame as pg
from SurvivalGame.const import ORD_DEFAULT
from SurvivalGame.typing import Point, Rect
from typing import Protocol, Sequence, Type, TypeVar, ParamSpec, Callable, Any, overload, runtime_checkable

T = TypeVar('T')
P = ParamSpec('P')

class AbstractEntity(Protocol):
    @overload
    def add_component(self, comp_type: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> None: ... # type: ignore
    def add_component(self, comp_type, *args, **kwargs): ...

    @overload
    def get_component(self, comp_type: Type[T]) -> T: ...
    @overload
    def get_component(self, comp_type: Type[T], default: T) -> T: ...
    @overload
    def get_component(self, comp_type: Type[T], default: None = None) -> T | None: ...
    def get_component(self, comp_type: Type[T], default: Any = None) -> T | None: ...

    def get_components(self, comp_type: Type[T]) -> Sequence[T]: ...
    def update(self, **kwargs): ...

    @property
    def tags(self) -> tuple[str, ...]: ...
    def add_tag(self, tag: str): ...

@runtime_checkable
class UpdateComponent(Protocol):
    needs_update = True
    def update(self, entity: AbstractEntity, **kwargs): ...

@runtime_checkable
class AttachComponent(Protocol):
    def on_attach(self, entity: AbstractEntity): ...

class SupportsEntityOperation(Protocol):
    def add_entity(self, entity: AbstractEntity, **kwargs): ...
    def rem_entity(self, entity: AbstractEntity, **kwargs): ...

class PhysicComponent:
    direction: pg.Vector2
    bound: Point
    speed: float
    DEFAULT_SPEED = 80.0

class SpriteComponent:
    LAYER: int
    image: pg.Surface
    rect: pg.Rect | pg.FRect

class EntityBase:
    _sentinel = object()
    _default_tags: set[str] = set()
    """
    An abstract class that represent entities in a world
    """
    def __init__(self):
        self.components: dict[Type, Any] = {}
        self._tags = EntityBase._default_tags

    def add_component(self, comp_type: Type[T] | Callable[P, T], *args, **kwargs):
        if not isinstance(comp_type, type):
            raise ValueError("Function can not be a subclass of a component")
        if comp_type in self.components:
            return
        comp = comp_type(*args, **kwargs)
        self.components[comp_type] = comp
        if isinstance(comp, AttachComponent):
            comp.on_attach(self)

    @overload
    def get_component(self, comp_type: Type[T]) -> T: ...
    @overload
    def get_component(self, comp_type: Type[T], default: T) -> T: ...
    @overload
    def get_component(self, comp_type: Type[T], default: None = None) -> T | None: ...
    def get_component(self, comp_type: Type[T], default: Any = _sentinel) -> T | None:
        if comp_type in self.components:
            return self.components[comp_type]
        for comp in self.components.values():
            if isinstance(comp, comp_type):
                return comp
        if default is EntityBase._sentinel:
            raise ValueError(f"The component {comp_type.__name__} doesn't exist in this entity")
        return default

    def get_components(self, comp_type: Type[T]) -> list[T]:
        return [comp for comp in self.components.values() if isinstance(comp, comp_type)]

    def del_component(self, comp_type: Type[T]):
        if comp_type in self.components:
            del self.components[comp_type]
        for sub_type, comp in self.components.items():
            if isinstance(comp, comp_type):
                del self.components[sub_type]
                break

    def update(self, paused = False, **kwargs):
        if paused:
            return
        components = []
        for comp in self.components.values():
            order = getattr(comp, "update_order", ORD_DEFAULT)
            if isinstance(order, list):
                components.extend((o, comp) for o in order)
            else:
                components.append((order, comp))
        components.sort(key=lambda c: -c[0])
        #print(type(self).__name__, *(type(comp[1]).__name__ for comp in components))
        for order, component in components:
            if isinstance(component, UpdateComponent) and component.needs_update:
                component.update(entity=self, order=order, **kwargs)
    
    @property
    def tags(self):
        return tuple(self._tags)

    def add_tag(self, tag: str):
        if self._tags is self._default_tags:
            self._tags = set([tag])
        else:
            self._tags.add(tag)

class FrameAnimation(Protocol):
    def step(self, dt: float) -> bool: ...
    def restart(self): ...
    @property
    def index(self) -> str: ...

class AbstractPixelMap:
    @property    
    def tilewidth(self) -> int: ...
    @property
    def tileheight(self) -> int: ...
    @property
    def mapwidth(self) -> int: ...
    @property
    def mapheight(self) -> int: ...
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...

class CollideTriggerComponent:
    def on_any_collided(self, obj): ...