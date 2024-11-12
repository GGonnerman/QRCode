import unittest

from error_correction import ErrorCorrection
from polynomials import (
    GFValue,
    GFPolynomial,
    generate_error_correction_polynomial,
    generate_message_polynomial,
    generate_error_correction_codewords,
)

from encoding import get_codeword_block_information


# TODO: Update names for all of the tests
class TestEncodingMethods(unittest.TestCase):
    def test_generate_error_correction_polynomial(self):
        self.assertEqual(
            GFPolynomial(
                GFValue(0, 2),
                GFValue(25, 1),
                GFValue(1, 0),
            ),
            generate_error_correction_polynomial(2),
        )
        self.assertEqual(
            GFPolynomial(
                GFValue(0, 15),
                GFValue(8, 14),
                GFValue(183, 13),
                GFValue(61, 12),
                GFValue(91, 11),
                GFValue(202, 10),
                GFValue(37, 9),
                GFValue(51, 8),
                GFValue(58, 7),
                GFValue(58, 6),
                GFValue(237, 5),
                GFValue(140, 4),
                GFValue(124, 3),
                GFValue(5, 2),
                GFValue(99, 1),
                GFValue(105, 0),
            ),
            generate_error_correction_polynomial(15),
        )

    def test_generate_message_polynomial(self):
        self.assertEqual(
            [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17],
            generate_message_polynomial(
                [
                    "00100000",
                    "01011011",
                    "00001011",
                    "01111000",
                    "11010001",
                    "01110010",
                    "11011100",
                    "01001101",
                    "01000011",
                    "01000000",
                    "11101100",
                    "00010001",
                    "11101100",
                    "00010001",
                    "11101100",
                    "00010001",
                ]
            ).as_integers(),
        )

    def test_generate_error_correction_codewords(self):
        # TODO: probably remove this after done solving this issue
        # import logging
        # loglevel = logging.DEBUG
        # logging.basicConfig(level=loglevel)

        mp = generate_message_polynomial(
            [
                "00100000",
                "01011011",
                "00001011",
                "01111000",
                "11010001",
                "01110010",
                "11011100",
                "01001101",
                "01000011",
                "01000000",
                "11101100",
                "00010001",
                "11101100",
                "00010001",
                "11101100",
                "00010001",
            ]
        )

        codeword_count = get_codeword_block_information(
            1, ErrorCorrection.MEDIUM
        ).ec_codewords_per_block

        self.assertEqual(
            [196, 35, 39, 119, 235, 215, 231, 226, 93, 23],
            generate_error_correction_codewords(mp, codeword_count).as_integers(),
        )
