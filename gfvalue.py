from typing import override
from utils import from_power, to_power


class GFValue:
    a_power: int
    x_power: int
    view_as_int: bool = True

    @classmethod
    def from_a_value(cls, a_value: int, x_power: int) -> "GFValue":
        return GFValue(to_power(a_value), x_power)

    def __init__(self, a_power: int, x_power: int):
        self.a_power = a_power
        self.x_power = x_power

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GFValue):
            raise ValueError(f"Cannot compare equality of GFValue and {other.__class__.__name__}")

        return self.a_power == other.a_power and self.x_power == other.x_power

    def __mul__(self, other: "GFValue"):
        a_power = (self.a_power + other.a_power) % 255
        x_power = self.x_power + other.x_power

        return GFValue(a_power, x_power)

    def __add__(self, other: "GFValue"):
        if self.x_power != other.x_power:
            raise Exception("Cannot add GFValues with different x exponents")

        # WARN: I think technically the power could go over 255 here and might need a modulo, but not 100% sure
        new_value = from_power(self.a_power) ^ from_power(other.a_power)
        return GFValue.from_a_value(new_value, self.x_power)

    @override
    def __str__(self):
        # TODO: This is bad practice to use a class variable like this. Fix later
        if GFValue.view_as_int:
            return f"{from_power(self.a_power)}x^({self.x_power})"
        else:
            return f"a^({self.a_power})*x^({self.x_power})"

    @override
    def __repr__(self):
        if GFValue.view_as_int:
            return f"<GFValue a_int={from_power(self.a_power)} x_power={self.x_power}"
        else:
            return f"<GFValue a_power={self.a_power} x_power={self.x_power}"
