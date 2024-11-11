import unittest

from polynomials import GFValue, GFPolynomial


class TestEncodingMethods(unittest.TestCase):
    def test_GFPolynomial_creation(self):
        _ = GFPolynomial()
        _ = GFPolynomial(GFValue(0, 0))
        _ = GFPolynomial(GFValue(0, 0), GFValue(0, 2), GFValue(3, 0))

    def test_GFPolynomial_stringify(self):
        GFValue.view_as_int = False
        a = GFPolynomial(GFValue(0, 0))
        b = GFPolynomial(GFValue(0, 1), GFValue(0, 2), GFValue(3, 0))
        self.assertEqual("a^(0)*x^(0)", str(a))
        self.assertEqual("a^(0)*x^(2) + a^(0)*x^(1) + a^(3)*x^(0)", str(b))

    def test_GFPolynomial_combine_like_terms(self):
        a = GFPolynomial(
            GFValue(2, 2),
            GFValue(27, 1),
            GFValue(1, 1),
            GFValue(3, 0),
            GFValue(0, 3),
            GFValue(25, 2),
        )
        self.assertEqual(
            a,
            GFPolynomial(
                GFValue(0, 3), GFValue(198, 2), GFValue(199, 1), GFValue(3, 0)
            ),
        )

    def test_GFPolynomial_add(self):
        a = GFPolynomial(GFValue(0, 2), GFValue(0, 1))
        b = GFPolynomial(GFValue(1, 1), GFValue(1, 0))
        self.assertEqual(
            GFPolynomial(GFValue(0, 2), GFValue(25, 1), GFValue(1, 0)), a + b
        )

    def test_GFPolynomial_mul(self):
        a = GFPolynomial(GFValue(0, 2), GFValue(25, 1), GFValue(1, 0))
        b = GFPolynomial(GFValue(0, 1), GFValue(2, 0))
        c = GFPolynomial(GFValue(0, 1), GFValue(3, 0))
        d = GFPolynomial(GFValue(0, 1), GFValue(4, 0))
        e = GFPolynomial(GFValue(0, 1), GFValue(5, 0))
        f = GFPolynomial(GFValue(0, 1), GFValue(6, 0))
        g = GFPolynomial(GFValue(0, 1), GFValue(7, 0))
        self.assertEqual(
            GFPolynomial(
                GFValue(0, 3), GFValue(198, 2), GFValue(199, 1), GFValue(3, 0)
            ),
            a * b,
        )
        self.assertEqual(
            GFPolynomial(
                GFValue(0, 8),
                GFValue(175, 7),
                GFValue(238, 6),
                GFValue(208, 5),
                GFValue(249, 4),
                GFValue(215, 3),
                GFValue(252, 2),
                GFValue(196, 1),
                GFValue(28, 0),
            ),
            a * b * c * d * e * f * g,
        )

    def test_GFPolynomial_mul_gfvalue(self):
        gf = GFPolynomial(
            GFValue(0, 25),
            GFValue(251, 24),
            GFValue(67, 23),
            GFValue(46, 22),
            GFValue(61, 21),
            GFValue(118, 20),
            GFValue(70, 19),
            GFValue(64, 18),
            GFValue(94, 17),
            GFValue(32, 16),
            GFValue(45, 15),
        )
        self.assertEqual(
            GFPolynomial(
                GFValue(5, 26),
                GFValue(1, 25),
                GFValue(72, 24),
                GFValue(51, 23),
                GFValue(66, 22),
                GFValue(123, 21),
                GFValue(75, 20),
                GFValue(69, 19),
                GFValue(99, 18),
                GFValue(37, 17),
                GFValue(50, 16),
            ),
            gf * GFValue(5, 1),
        )

    def test_GFPolynomial_iter(self):
        a = GFPolynomial(
            GFValue(2, 2),
            GFValue(27, 1),
            GFValue(1, 1),
            GFValue(3, 0),
            GFValue(0, 3),
            GFValue(25, 2),
        )
        self.assertEqual(
            list(a), [GFValue(0, 3), GFValue(198, 2), GFValue(199, 1), GFValue(3, 0)]
        )

    def test_GFPolynomial_getitem(self):
        gf = GFPolynomial(
            GFValue(8, 12),
            GFValue(17, 0),
            GFValue(12, 18),
            GFValue(0, 12),
            GFValue(9, 8),
        )

        self.assertEqual(GFValue(12, 18), gf[0])
        self.assertEqual(GFValue(9, 8), gf[2])
        self.assertEqual(GFValue(17, 0), gf[-1])

    def test_GFPolynomial_len(self):
        gf = GFPolynomial(
            GFValue(8, 12),
            GFValue(17, 0),
            GFValue(12, 18),
            GFValue(0, 12),
            GFValue(9, 8),
        )

        self.assertEqual(18, len(gf))

    def test_GFPolynomial_as_integers(self):
        gf = GFPolynomial(
            GFValue(5, 25),
            GFValue(1, 24),
            GFValue(72, 23),
            GFValue(51, 22),
            GFValue(66, 21),
            GFValue(123, 20),
            GFValue(75, 19),
            GFValue(69, 18),
            GFValue(99, 17),
            GFValue(37, 16),
            GFValue(50, 15),
        )
        self.assertSequenceEqual(
            [
                32,
                2,
                101,
                10,
                97,
                197,
                15,
                47,
                134,
                74,
                5,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
            ],
            gf.as_integers(),
        )

    def test_GFPolynomial_xor(self):
        gen = GFPolynomial(
            GFValue(5, 25),
            GFValue(1, 24),
            GFValue(72, 23),
            GFValue(51, 22),
            GFValue(66, 21),
            GFValue(123, 20),
            GFValue(75, 19),
            GFValue(69, 18),
            GFValue(99, 17),
            GFValue(37, 16),
            GFValue(50, 15),
        )

        mes = GFPolynomial(
            GFValue.from_a_value(32, 25),
            GFValue.from_a_value(91, 24),
            GFValue.from_a_value(11, 23),
            GFValue.from_a_value(120, 22),
            GFValue.from_a_value(209, 21),
            GFValue.from_a_value(114, 20),
            GFValue.from_a_value(220, 19),
            GFValue.from_a_value(77, 18),
            GFValue.from_a_value(67, 17),
            GFValue.from_a_value(64, 16),
            GFValue.from_a_value(236, 15),
            GFValue.from_a_value(17, 14),
            GFValue.from_a_value(236, 13),
            GFValue.from_a_value(17, 12),
            GFValue.from_a_value(236, 11),
            GFValue.from_a_value(17, 10),
        )

        o = GFPolynomial(
            GFValue.from_a_value(89, 24),
            GFValue.from_a_value(110, 23),
            GFValue.from_a_value(114, 22),
            GFValue.from_a_value(176, 21),
            GFValue.from_a_value(183, 20),
            GFValue.from_a_value(211, 19),
            GFValue.from_a_value(98, 18),
            GFValue.from_a_value(197, 17),
            GFValue.from_a_value(10, 16),
            GFValue.from_a_value(233, 15),
            GFValue.from_a_value(17, 14),
            GFValue.from_a_value(236, 13),
            GFValue.from_a_value(17, 12),
            GFValue.from_a_value(236, 11),
            GFValue.from_a_value(17, 10),
        )

        self.assertEqual(o, mes ^ gen)
        self.assertEqual(o, gen ^ mes)

    # def test_GFPolynomial_from_a_value(self):
    #    self.assertEqual(GFPolynomial(25, 1), GFPolynomial.from_a_value(3, 1))
    #    self.assertEqual(GFPolynomial(198, 1), GFPolynomial.from_a_value(7, 1))
