import unittest

from trip_Functions import convert_price_to_usd


class ConvertPriceToUsdTests(unittest.TestCase):
    def test_eur_converts_to_usd(self):
        result = convert_price_to_usd(
            {
                "currencyCode": "EUR",
                "amount": "16.00",
            }
        )

        self.assertEqual(
            result,
            {
                "currencyCode": "USD",
                "amount": "17.44",
            },
        )

    def test_usd_is_returned_as_usd(self):
        result = convert_price_to_usd(
            {
                "currencyCode": "USD",
                "amount": "16.00",
            }
        )

        self.assertEqual(
            result,
            {
                "currencyCode": "USD",
                "amount": "16.00",
            },
        )

    def test_lowercase_currency_code_is_supported(self):
        result = convert_price_to_usd(
            {
                "currencyCode": "aud",
                "amount": "85.00",
            }
        )

        self.assertEqual(
            result,
            {
                "currencyCode": "USD",
                "amount": "56.10",
            },
        )

    def test_unsupported_currency_returns_none(self):
        result = convert_price_to_usd(
            {
                "currencyCode": "ZAR",
                "amount": "25.00",
            }
        )

        self.assertIsNone(result)

    def test_invalid_amount_returns_none(self):
        result = convert_price_to_usd(
            {
                "currencyCode": "EUR",
                "amount": "not-a-number",
            }
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
