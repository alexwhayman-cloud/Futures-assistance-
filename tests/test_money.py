import unittest

from propdata.money import parse_money, parse_number


class TestParseNumber(unittest.TestCase):
    def test_indonesian_thousands(self):
        self.assertEqual(parse_number("1.500.000.000"), 1_500_000_000)

    def test_indonesian_decimal_comma(self):
        # The trap: stripping commas would make this 35.
        self.assertEqual(parse_number("3,5"), 3.5)

    def test_english_thousands(self):
        self.assertEqual(parse_number("250,000"), 250_000)

    def test_mixed_separators_rightmost_is_decimal(self):
        self.assertEqual(parse_number("1,234.56"), 1234.56)
        self.assertEqual(parse_number("1.234,56"), 1234.56)

    def test_ambiguous_grouped_thousand_resolves_english(self):
        # "1,500" is 1500 (EN) or 1.5 (ID). Documented resolution: 1500.
        self.assertEqual(parse_number("1,500"), 1500)


class TestParseMoney(unittest.TestCase):
    def test_m_means_miliar_in_idr(self):
        result = parse_money("Rp 3,5 M")
        self.assertEqual(result.amount, 3_500_000_000)
        self.assertEqual(result.currency, "IDR")

    def test_m_means_million_elsewhere(self):
        # Same letter, 1000x apart, decided by currency.
        self.assertEqual(parse_money("USD 3.5M").amount, 3_500_000)

    def test_indonesian_multiplier_words(self):
        self.assertEqual(parse_money("Rp 850 juta").amount, 850_000_000)
        self.assertEqual(parse_money("3,5 miliar rupiah").amount, 3_500_000_000)

    def test_rental_period_is_reported(self):
        result = parse_money("US$ 25,000 / year")
        self.assertEqual(result.amount, 25_000)
        self.assertEqual(result.period, "year")

    def test_price_anchors_to_the_currency_not_the_first_number(self):
        # The land area is the first number on the page; the price is not.
        text = "Ocean view land, luas tanah 10 are. Harga Rp 1.500.000.000"
        self.assertEqual(parse_money(text).amount, 1_500_000_000)

    def test_suffix_currency_convention(self):
        self.assertEqual(parse_money("250.000.000,- IDR").amount, 250_000_000)

    def test_no_currency_and_no_default_is_none(self):
        self.assertIsNone(parse_money("Land 10 are, no price given"))

    def test_no_number_is_none(self):
        self.assertIsNone(parse_money("Price on application", default_currency="IDR"))


if __name__ == "__main__":
    unittest.main()
