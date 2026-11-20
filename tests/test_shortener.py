import unittest

from src.shortener import URLShortener


class URLShortenerTests(unittest.TestCase):
    def test_shorten_and_expand_url(self):
        shortener = URLShortener()
        code = shortener.shorten("https://example.com/path?q=1")

        self.assertEqual(code, "0")
        self.assertEqual(shortener.expand(code), "https://example.com/path?q=1")

    def test_same_url_gets_same_code(self):
        shortener = URLShortener()
        first = shortener.shorten("https://example.com")

        self.assertEqual(shortener.shorten("https://example.com"), first)

    def test_distinct_urls_get_sequential_codes(self):
        shortener = URLShortener()

        self.assertEqual(shortener.shorten("https://one.example"), "0")
        self.assertEqual(shortener.shorten("https://two.example"), "1")

    def test_invalid_urls_are_rejected(self):
        shortener = URLShortener()
        invalid_urls = (
            "",
            "   ",
            "example.com",
            "ftp://example.com",
            "https://",
            "https://example.com:bad",
            "https://example.com/a b",
            "https:// example.com",
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_non_string_url_is_rejected(self):
        shortener = URLShortener()
        for url in (None, 1, True):
            with self.subTest(url=url):
                with self.assertRaises(TypeError):
                    shortener.shorten(url)

    def test_query_fragment_and_http_url_are_preserved(self):
        shortener = URLShortener()
        url = "http://example.com/path?q=1#section"

        code = shortener.shorten(url)

        self.assertEqual(shortener.expand(code), url)

    def test_unknown_code_is_rejected(self):
        with self.assertRaises(KeyError):
            URLShortener().expand("missing")


if __name__ == "__main__":
    unittest.main()
