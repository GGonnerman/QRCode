from itertools import zip_longest
import logging
from functools import cache
from textwrap import fill
from typing import override
from collections.abc import Iterator
from error_correction import ErrorCorrection


def from_power(value: int) -> int:
    from_power_table, _ = generate_log_antilog_table()
    return from_power_table[value]


def to_power(value: int) -> int:
    _, to_power_table = generate_log_antilog_table()
    return to_power_table[value]


@cache
def generate_log_antilog_table() -> tuple[dict[int, int], dict[int, int]]:
    generator_polynomial: int = 0b100011101
    from_power: dict[int, int] = {}
    for i in range(255):
        if i < 8:
            from_power[i] = 2**i
        else:
            current: int = from_power[i - 1] * 2
            if current >= 256:
                current ^= generator_polynomial
            from_power[i] = current

    to_power: dict[int, int] = {}
    for k, v in from_power.items():
        to_power[v] = k

    return (from_power, to_power)


class GFValue:
    a_power: int
    x_power: int
    view_as_int: bool = True

    @classmethod
    def from_a_value(cls, a_value: int, x_power: int):
        return GFValue(to_power(a_value), x_power)

    def __init__(self, a_power: int, x_power: int):
        self.a_power = a_power
        self.x_power = x_power

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GFValue):
            raise ValueError(
                f"Cannot compare equality of GFValue and {other.__class__.__name__}"
            )
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
            raise Exception(
                f"Cannot compare equality of GFPolynomial and {other.__class__.__name__}"
            )
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
            temp_divisor: GFPolynomial = divisor * GFValue(
                0, len(dividend) - len(divisor)
            )

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


def generate_error_correction_polynomial(codeword_count: int) -> GFPolynomial:
    polynomial: GFPolynomial = GFPolynomial(GFValue(0, 1), GFValue(0, 0))
    for i in range(1, codeword_count):
        polynomial *= GFPolynomial(GFValue(0, 1), GFValue(i, 0))
    return polynomial


def generate_message_polynomial(message: list[str]) -> GFPolynomial:
    coeff: list[int] = [int(w, 2) for w in message]
    coeff.reverse()
    polynomial = GFPolynomial()
    for i, val in enumerate(coeff):
        if val == 0:
            continue
        polynomial += GFValue.from_a_value(val, i)
    return polynomial


def generate_error_correction_codewords(
    message_polynomial: GFPolynomial, codeword_count: int
) -> GFPolynomial:
    generator_polynomial: GFPolynomial = generate_error_correction_polynomial(
        codeword_count
    )
    # Multiply message polynomial by n^x to make sure it doesn't get too small
    message_polynomial *= GFValue(0, codeword_count)

    logging.debug(message_polynomial)
    logging.debug(generator_polynomial)

    return message_polynomial / generator_polynomial


def lookup_ec_codewords_and_block_info(
    version: int, error_correction_level: ErrorCorrection
) -> tuple[list[int], list[int]]:
    pass


if __name__ == "__main__":
    mp = generate_message_polynomial(
        "00100000 01011011 00001011 01111000 11010001 01110010 11011100 01001101 01000011 01000000 11101100 00010001 11101100 00010001 11101100 00010001".split(
            " "
        )
    )

    print(mp)

    r = generate_error_correction_codewords(mp, 10)
