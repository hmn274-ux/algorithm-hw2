import unittest

from src.base62 import decode_base62, encode_base62


class Base62Tests(unittest.TestCase):
    def test_zero_and_alphabet_boundaries(self):
        self.assertEqual(encode_base62(0), "0")
        self.assertEqual(encode_base62(61), "Z")
        self.assertEqual(encode_base62(62), "10")

    def test_round_trip_large_integer(self):
        number = 2**128
        self.assertEqual(decode_base62(encode_base62(number)), number)

    def test_decode_rejects_empty_or_invalid_codes(self):
        for code in ("", "a-"):
            with self.subTest(code=code):
                with self.assertRaises(ValueError):
                    decode_base62(code)

    def test_encode_rejects_invalid_numbers(self):
        for number, error in ((-1, ValueError), (1.5, TypeError), (True, TypeError)):
            with self.subTest(number=number):
                with self.assertRaises(error):
                    encode_base62(number)


if __name__ == "__main__":
    unittest.main()
