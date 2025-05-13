import pygame as pg
from SurvivalGame.const import ORD_DEFAULT
from SurvivalGame.typing import Point, Rect
from typing import Protocol, Type, TypeVar, ParamSpec, Generator, Callable, Any, overload, runtime_checkable

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

    def get_components(self, comp_type: Type[T]) -> list[T]: ...
    def update(self, *args, **kwargs): ...

@runtime_checkable
class UpdateComponent(Protocol):
    needs_update = True
    def update(self, *args, entity: AbstractEntity, **kwargs): ...

@runtime_checkable
class AttachComponent(Protocol):
    def on_attach(self, entity: AbstractEntity): ...

class PhysicComponent:
    direction: pg.Vector2
    bound: Point
    speed: float

class SpriteComponent:
    image: pg.Surface
    rect: Rect

class EntityBase:
    _sentinel = object()
    """
    An abstract class that represent entities in a world
    """
    def __init__(self):
        self.components: dict[Type, Any] = {}

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

    def update(self, *args, **kwargs):
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
                component.update(entity=self, order=order, *args, **kwargs)

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