import unittest

from error_correction import ErrorCorrection
from mode import Mode

from encoding import (
    encode,
    lookup_alphanumeric_value,
    get_character_count_indicator_length,
    get_data_codeword_capacity,
)


class TestEncodingMethods(unittest.TestCase):
    def test_lookup_alphanumeric_value(self):
        self.assertEqual(4, lookup_alphanumeric_value("4"))
        self.assertEqual(30, lookup_alphanumeric_value("U"))
        self.assertEqual(36, lookup_alphanumeric_value(" "))

    def test_get_character_count_indicator(self):
        self.assertEqual(9, get_character_count_indicator_length(Mode.ALPHANUMERIC, 5))
        self.assertEqual(16, get_character_count_indicator_length(Mode.BINARY, 11))
        self.assertEqual(12, get_character_count_indicator_length(Mode.KANJI, 33))
        self.assertEqual(14, get_character_count_indicator_length(Mode.NUMERIC, 40))

    def test_to_alphanumeric(self):
        self.assertEqual(
            "00100000010110110000101101111000110100010111001011011100010011010100001101",
            encode("HELLO WORLD", version=1, mode=Mode.ALPHANUMERIC),
        )
        self.assertEqual(
            "00100000001010011100111011100111001000010",
            encode("AC-42", version=1, mode=Mode.ALPHANUMERIC),
        )
        self.assertRaises(
            ValueError,
            lambda: encode("Hello", version=1, mode=Mode.ALPHANUMERIC),
        )

    def test_to_numeric(self):
        self.assertEqual(
            "00010000001000000000110001010110011000011",
            encode("01234567", version=1, mode=Mode.NUMERIC),
        )
        self.assertEqual(
            "00010000000111110110001110000100101001",
            encode("8675309", version=1, mode=Mode.NUMERIC),
        )
        self.assertRaises(
            ValueError,
            lambda: encode("1234 HI", version=1, mode=Mode.NUMERIC),
        )

    def test_to_binary(self):
        self.assertEqual(
            "01000000110101001000011001010110110001101100011011110010110000100000011101110110111101110010011011000110010000100001",
            encode("Hello, world!", version=1, mode=Mode.BINARY),
        )
        self.assertRaises(
            ValueError,
            lambda: encode("П́ҦП̧П̑ҀԚ̆Р́", version=1, mode=Mode.BINARY),
        )

    def test_to_kanji(self):
        self.assertEqual(
            "10000000001011010101010100011010010111",
            encode("茗荷", version=1, mode=Mode.KANJI),
        )
        self.assertRaises(
            ValueError,
            lambda: encode("Hello", version=1, mode=Mode.KANJI),
        )

    def test_lookup_data_codeword_capacity(self):
        self.assertEqual(1276, get_data_codeword_capacity(40, ErrorCorrection.HIGH))
        self.assertEqual(1812, get_data_codeword_capacity(35, ErrorCorrection.MEDIUM))
        self.assertEqual(861, get_data_codeword_capacity(20, ErrorCorrection.LOW))
        self.assertEqual(1276, get_data_codeword_capacity(40, ErrorCorrection.HIGH))
        self.assertEqual(13, get_data_codeword_capacity(1, ErrorCorrection.QUARTILE))
        self.assertEqual(46, get_data_codeword_capacity(5, ErrorCorrection.HIGH))
        self.assertEqual(721, get_data_codeword_capacity(18, ErrorCorrection.LOW))
