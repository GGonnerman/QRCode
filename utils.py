from color import BLACK, WHITE
from typing import TypeVar
from itertools import zip_longest

T = TypeVar("T")


def split_into_segments(data: list[T], segment_size: int) -> list[list[T]]:
    values: list[list[T]] = []
    for i in range(0, len(data), segment_size):
        values.append(data[i : i + segment_size])
    return values


def interleave(g1: list[list[T]], g2: list[list[T]]) -> list[T]:
    interleaved_values: list[T] = []
    for values in zip_longest(*g1, *g2):
        for value in values:
            if value is None:
                continue
            interleaved_values.append(value)
    return interleaved_values


# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=85
def golay(version: int) -> str:
    seq: int = 18
    data: int = 6
    polynomial: int = 0b1111100100101

    return calculate_crc(polynomial, version, seq, data)


# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=83
def bose_chaudhuri_hocquenghem(format: int) -> str:
    seq: int = 15
    data: int = 5
    polynomial: int = 0b10100110111

    coeff: int = int(calculate_crc(polynomial, format, seq, data), 2)

    mask: int = 0b101010000010010

    result: str = bin(coeff ^ mask)

    # TODO: I think I can remove the addition str call in this line, but would like testing bebfore I do it
    return f"{str(result)[2:].zfill(seq - data)}"


def calculate_crc(polynomial: int, value: int, seq: int, data: int) -> str:
    current: int = value * 2 ** (seq - data)

    while len(bin(current)) >= len(bin(polynomial)):
        offset: int = len(bin(current)) - len(bin(polynomial))

        current = current ^ (polynomial << offset)

    return f"{bin(value)[2:].zfill(data)}{bin(current)[2:].zfill(seq - data)}"


def to_color(i: object) -> tuple[int, int, int]:
    if i == "1":
        return BLACK
    if i == "0":
        return WHITE
    if i == 1:
        return BLACK
    if i == 0:
        return WHITE
    raise Exception("Unable to convert to color")


if __name__ == "__main__":
    print(bose_chaudhuri_hocquenghem(0b10011))
