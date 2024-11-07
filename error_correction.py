from enum import IntEnum

# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=61
class ErrorCorrection(IntEnum):
    LOW = 0b01
    MEDIUM = 0b00
    QUARTILE = 0b11
    HIGH = 0b10
