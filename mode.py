from enum import IntEnum


class Mode(IntEnum):
    NUMERIC = 0b0001
    ALPHANUMERIC = 0b0010
    BINARY = 0b0100
    KANJI = 0b1000
    ANY = -1
