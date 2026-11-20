"""URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import encode_base62
from src.hash_table import HashTable


class URLShortener:
    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 0

    def shorten(self, url):
        self._validate_url(url)
        existing_code = self._url_to_code.get(url)
        if existing_code is not None:
            return existing_code

        code = encode_base62(self._next_id)
        self._next_id += 1
        self._url_to_code[url] = code
        self._code_to_url[code] = url
        return code

    def expand(self, code):
        if not isinstance(code, str):
            raise KeyError(code)
        return self._code_to_url[code]

    @staticmethod
    def _validate_url(url):
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        if (
            not url
            or url != url.strip()
            or any(character.isspace() or ord(character) < 32 or ord(character) == 127
                   for character in url)
            or "\\" in url
        ):
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            parsed.port
        except ValueError as error:
            raise ValueError("url must be a valid absolute HTTP or HTTPS URL") from error
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc or not hostname:
            raise ValueError("url must be an absolute HTTP or HTTPS URL")
