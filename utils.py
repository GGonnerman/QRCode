# https://www.thonky.com/qr-code-tutorial/error-correction-coding
def calculate_ec_generator_polynomial():
    pass

# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=85
def golay(version: int) -> str:
    seq = 18
    data = 6
    polynomial: int =  0b1111100100101

    return calculate_crc(polynomial, version, seq, data)

# https://www.arscreatio.com/repositorio/images/n_23/SC031-N-1915-18004Text.pdf#page=83
def bose_chaudhuri_hocquenghem(format: int) -> str:
    seq = 15
    data = 5
    polynomial = 0b10100110111

    coeff: int = int(calculate_crc(polynomial, format, seq, data), 2)

    mask = 0b101010000010010

    result = bin(coeff ^ mask)

    return f"{str(result)[2:].zfill(seq - data)}"

def calculate_crc(polynomial, value, seq, data):

    current = value * 2**(seq - data)

    while len(bin(current)) >= len(bin(polynomial)):

        offset: int = len(bin(current)) - len(bin(polynomial))

        current = current ^ (polynomial << offset)

    return f"{bin(value)[2:].zfill(data)}{bin(current)[2:].zfill(seq - data)}"

from color import *
def to_color(i: any) -> tuple[int, int, int]:
    if i == '1': return BLACK
    if i == '0': return WHITE
    if i == 1: return BLACK
    if i == 0: return WHITE
    print(i)
    raise Exception("Unable to convert to color")

if __name__ == "__main__":
    print(bose_chaudhuri_hocquenghem(0b10011))
