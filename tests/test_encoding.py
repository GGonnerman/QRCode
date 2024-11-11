import unittest

from error_correction import ErrorCorrection
from mode import Mode

from encoding import (
    lookup_alphanumeric_value,
    to_alphanumeric,
    get_character_count_indicator,
    lookup_data_codeword_capacity,
)


class TestEncodingMethods(unittest.TestCase):
    def test_lookup_alphanumeric_value(self):
        self.assertEqual(4, lookup_alphanumeric_value("4"))
        self.assertEqual(30, lookup_alphanumeric_value("U"))
        self.assertEqual(36, lookup_alphanumeric_value(" "))

    def test_get_character_count_indicator(self):
        self.assertEqual(9, get_character_count_indicator(Mode.ALPHANUMERIC, 5))
        self.assertEqual(16, get_character_count_indicator(Mode.BINARY, 11))
        self.assertEqual(12, get_character_count_indicator(Mode.KANJI, 33))
        self.assertEqual(14, get_character_count_indicator(Mode.NUMERIC, 40))

    def test_to_alphanumeric(self):
        self.assertEqual(
            "00100000010110110000101101111000110100010111001011011100010011010100001101",
            to_alphanumeric("HELLO WORLD", version=1),
        )
        self.assertEqual(
            "00100000001010011100111011100111001000010",
            to_alphanumeric("AC-42", version=1),
        )

    def test_lookup_data_codeword_capacity(self):
        self.assertEqual(1276, lookup_data_codeword_capacity(40, ErrorCorrection.HIGH))
        self.assertEqual(
            1812, lookup_data_codeword_capacity(35, ErrorCorrection.MEDIUM)
        )
        self.assertEqual(861, lookup_data_codeword_capacity(20, ErrorCorrection.LOW))
        self.assertEqual(1276, lookup_data_codeword_capacity(40, ErrorCorrection.HIGH))
        self.assertEqual(13, lookup_data_codeword_capacity(1, ErrorCorrection.QUARTILE))
        self.assertEqual(46, lookup_data_codeword_capacity(5, ErrorCorrection.HIGH))
        self.assertEqual(721, lookup_data_codeword_capacity(18, ErrorCorrection.LOW))
