from pygame import Rect as _Rect, FRect as _FRect
type Point = tuple[float, float] | tuple[int, int]
type BaseRect = tuple[float, float, float, float] | tuple[int, int, int, int]
type Rect = _Rect | _FRect
KeyFrame = tuple[str, float]
AnimationData = str | list[KeyFrame]
del _Rect, _FRect