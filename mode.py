from enum import IntEnum


class Mode(IntEnum):
    NUMERIC = 0b0001
    ALPHANUMERIC = 0b0010
    BINARY = 0b0100
    KANJI = 0b1000
    # TODO: Either implement these or remove them from Mode
    STRUCTUED_APPEND = 0b0011
    ECI = 0b0111
    FNC1_FIRST_POSITION = 0b0101
    FNC1_SECOND_POSITION = 0b1001
    END_OF_MESSAGE = 0b0000
