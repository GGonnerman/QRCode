from gfpolynomial import GFPolynomial
from gfvalue import GFValue


def generate_error_correction_polynomial(codeword_count: int) -> GFPolynomial:
    polynomial: GFPolynomial = GFPolynomial(GFValue(0, 1), GFValue(0, 0))
    for i in range(1, codeword_count):
        polynomial *= GFPolynomial(GFValue(0, 1), GFValue(i, 0))
    return polynomial


def generate_message_polynomial(message: list[str]) -> GFPolynomial:
    coeff: list[int] = [int(w, 2) for w in message]
    coeff.reverse()
    polynomial: GFPolynomial = GFPolynomial()
    for i, val in enumerate(coeff):
        if val == 0:
            continue
        polynomial += GFValue.from_a_value(val, i)
    return polynomial


def generate_error_correction_codewords(message_polynomial: GFPolynomial, codeword_count: int) -> GFPolynomial:
    generator_polynomial: GFPolynomial = generate_error_correction_polynomial(codeword_count)

    # Multiply message polynomial by n^x to make sure it doesn't get too small
    message_polynomial *= GFValue(0, codeword_count)

    return message_polynomial / generator_polynomial


if __name__ == "__main__":
    mp = generate_message_polynomial("00100000 01011011 00001011 01111000 11010001 01110010 11011100 01001101 01000011 01000000 11101100 00010001 11101100 00010001 11101100 00010001".split(" "))

    print(mp)

    r = generate_error_correction_codewords(mp, 10)
