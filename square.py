from turtle import color
from typing import Any, override
from color import BLACK, GRAY


class Square:
    _color: tuple[int, int, int]
    _locked: bool
    _reserved: bool

    def __init__(
        self,
        color: tuple[int, int, int] = GRAY,
        locked: bool = False,
        reserved: bool = False,
    ):
        self._color = color
        self._locked = locked
        self._reserved = reserved

    def set_color(self, color: tuple[int, int, int]) -> "Square":
        # TODO: Before done, make locking actually work.
        # Currently disabled to indicate possible error

        # if self._locked: return
        self._color = color
        return self

    def get_color(self) -> tuple[int, int, int]:
        # if self.is_locked() or self.is_reserved():
        #    return (0, 256, 0)
        return self._color

    def is_reserved(self) -> bool:
        return self._reserved

    def reserve(self) -> None:
        self._reserved = True

    def is_locked(self) -> bool:
        return self._locked

    def lock(self) -> None:
        self._locked = True
        self._reserved = True

    @override
    def __repr__(self) -> str:
        return "1" if self._color == BLACK else "0"

    @override
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Square):
            return self._color == other.get_color()
        elif isinstance(other, tuple):
            return self.get_color() == other
        else:
            return False
