import unittest

from propdata import units


class TestClean(unittest.TestCase):
    def test_null_sentinels_become_none(self):
        for token in ("", "  ", "NO DATA!", "unknown", "N/A", "INVALID!", "-"):
            with self.subTest(token=token):
                self.assertIsNone(units.clean(token))

    def test_real_values_survive_stripped(self):
        self.assertEqual(units.clean("  Semi-Detached "), "Semi-Detached")

    def test_zero_is_not_null(self):
        self.assertEqual(units.clean("0"), "0")


class TestCoercion(unittest.TestCase):
    def test_thousands_separator(self):
        self.assertEqual(units.to_float("1,250.5"), 1250.5)

    def test_garbage_is_none_not_raise(self):
        self.assertIsNone(units.to_float("NO DATA!"))
        self.assertIsNone(units.to_int("abc"))
        self.assertIsNone(units.to_date("INVALID!"))

    def test_date_parses(self):
        self.assertEqual(units.to_date("2019-04-02").year, 2019)


class TestArea(unittest.TestCase):
    def test_sqm_passthrough(self):
        self.assertEqual(units.normalise_area("94.5", "sqm"), 94.5)

    def test_sqft_conversion(self):
        self.assertEqual(units.normalise_area(1000, "sqft"), 92.9)

    def test_non_positive_area_is_none(self):
        self.assertIsNone(units.normalise_area("0", "sqm"))
        self.assertIsNone(units.normalise_area("-5", "sqm"))

    def test_unknown_unit_raises(self):
        # Loud failure beats a silently wrong area.
        with self.assertRaises(ValueError):
            units.normalise_area(100, "acres")


if __name__ == "__main__":
    unittest.main()
