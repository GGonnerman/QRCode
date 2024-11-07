from color import GRAY


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
        # if self.is_locked() or self.is_reserved(): return (0, 256, 0)
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
