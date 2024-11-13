from gfvalue import GFValue
from itertools import zip_longest
from typing import override
from collections.abc import Iterator
from utils import from_power


class GFPolynomial:
    values: list[GFValue]

    def __init__(self, *gfValues: GFValue):
        self.values = [v for v in gfValues]
        # print([str(v) for v in self.values])
        self.combine_like_terms()
        self._sort_by_x_power()

    def _sort_by_x_power(self) -> None:
        self.values.sort(key=lambda x: -x.x_power)

    def __gt__(self, other: "GFPolynomial") -> bool:
        for a, b in zip_longest(self, other, fillvalue=None):
            if a is None:
                return False
            if b is None:
                return True
            if a.x_power > b.x_power:
                return True
            if a.x_power < b.x_power:
                return False
            if a.a_power > b.a_power:
                return True
            if a.a_power < b.a_power:
                return False
        return False

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GFPolynomial):
            raise Exception(f"Cannot compare equality of GFPolynomial and {other.__class__.__name__}")
        # TODO: I don't think this function is full-proof, not sure though
        if len(self) != len(other) or len(self.values) != len(other.values):
            return False
        for a, b in zip(self, other):
            if a != b:
                return False

        return True

    def __add__(self, other: "GFPolynomial | GFValue"):
        if isinstance(other, GFValue):
            return GFPolynomial(*self.values, other)
        else:
            return GFPolynomial(*self.values, *other.values)

    def __iter__(self) -> Iterator[GFValue]:
        return self.values.__iter__()

    def __getitem__(self, i: int) -> GFValue:
        return self.values[i]

    def __mul__(self, other: "GFPolynomial | GFValue") -> "GFPolynomial":
        if isinstance(other, GFValue):
            return GFPolynomial(*[v * other for v in self])
        else:
            new_values: list[GFValue] = []
            for a in self:
                for b in other:
                    new_values.append(a * b)
            return GFPolynomial(*new_values)

    # TODO: This should probably be able to take a GFValue
    def __truediv__(self, divisor: "GFPolynomial") -> "GFPolynomial":
        dividend = self
        while dividend > divisor:
            # Multiply the generator polynomial so the lead term has the same power as the lead term of message polynomial
            temp_divisor: GFPolynomial = divisor * GFValue(0, len(dividend) - len(divisor))

            # Multiply the generator polynomial so it has the same first term
            temp_divisor *= GFValue(dividend[0].a_power - divisor[0].a_power, 0)

            GFValue.view_as_int = True

            dividend ^= temp_divisor

        return dividend

    def combine_like_terms(self):
        self._sort_by_x_power()
        i: int = 0
        while i < len(self.values) - 1:
            a = self.values[i]
            b = self.values[i + 1]
            if a.x_power == b.x_power:
                self.values[i] = a + b
                del self.values[i + 1]
                continue
            i += 1

    @override
    def __str__(self):
        return " + ".join([str(x) for x in self])

    def __len__(self) -> int:
        return max([v.x_power for v in self])

    def get_x_power(self, x_power: int) -> GFValue | None:
        for v in self:
            if v.x_power == x_power:
                return v

    def __xor__(self, other: "GFPolynomial") -> "GFPolynomial":
        new_values: list[GFValue] = []
        all_x_powers = set([*[v.x_power for v in self], *[v.x_power for v in other]])
        for x_power in all_x_powers:
            a = self.get_x_power(x_power)
            b = other.get_x_power(x_power)
            # Ensure that a is the existing value
            if a is None:
                a = b
                b = None

            # This should never happen, but here to satisfy type-checker
            if a is None:
                raise Exception("Was checking x power that neither polynomial contains")

            if b is None:
                new_value = from_power(a.a_power) ^ 0
            else:
                new_value = from_power(a.a_power) ^ from_power(b.a_power)

            if new_value == 0:
                continue

            new_values.append(GFValue.from_a_value(new_value, a.x_power))
        return GFPolynomial(*new_values)

        # new_values: list[GFValue] = []
        # for a, b in zip_longest(self, other, fillvalue=None):
        #    # Ensure that a is the existing value
        #    if a is None:
        #        a = b
        #        b = None

        #    # This should never happen, but here to satisfy type-checker
        #    if a is None:
        #        break

        #    if b is None:
        #        new_value = from_power(a.a_power) ^ 0
        #    else:
        #        new_value = from_power(a.a_power) ^ from_power(b.a_power)

        #    if new_value == 0:
        #        continue

        #    new_values.append(GFValue.from_a_value(new_value, a.x_power))
        # return GFPolynomial(*new_values)

    def as_integers(self) -> list[int]:
        # Create an empty list of size = highest x power
        out = [0 for _ in range(len(self) + 1)]
        # Fill in all positive values
        for v in self:
            out[v.x_power] = from_power(v.a_power)
        # Make it go 3x^2 + 4x^1 + 1x^0 = [3, 4, 1] instead of [1, 4, 3]
        out.reverse()
        return out
