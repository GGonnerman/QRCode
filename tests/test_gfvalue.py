import unittest

from polynomials import GFValue


class TestEncodingMethods(unittest.TestCase):
    def test_GFValue_creation(self):
        _ = GFValue(0, 0)
        _ = GFValue(0, 1)
        _ = GFValue(1, 0)
        _ = GFValue(1, 1)

    def test_GFValue_stringify(self):
        GFValue.view_as_int = False
        self.assertEqual("a^(0)*x^(0)", str(GFValue(0, 0)))
        self.assertEqual("a^(0)*x^(1)", str(GFValue(0, 1)))
        self.assertEqual("a^(1)*x^(0)", str(GFValue(1, 0)))
        self.assertEqual("a^(1)*x^(1)", str(GFValue(1, 1)))

    def test_GFValue_add(self):
        a = GFValue(0, 1)
        b = GFValue(1, 1)
        c = GFValue(1, 4)
        self.assertEqual(GFValue(25, 1), a + b)
        self.assertEqual(GFValue(198, 2), GFValue(25, 2) + GFValue(2, 2))
        self.assertRaises(Exception, lambda: a + c)

    def test_GFValue_mul(self):
        a = GFValue(0, 0)
        b = GFValue(0, 1)
        self.assertEqual(GFValue(0, 1), a * b)
        self.assertEqual(GFValue(45, 4), GFValue(50, 2) * GFValue(250, 2))

    def test_GFValue_from_a_value(self):
        self.assertEqual(GFValue(25, 1), GFValue.from_a_value(3, 1))
        self.assertEqual(GFValue(198, 1), GFValue.from_a_value(7, 1))
