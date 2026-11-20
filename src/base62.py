"""Base62 conversion using the alphabet 0-9, a-z, A-Z."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)


def encode(n: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("number must be an integer")
    if n < 0:
        raise ValueError("number must be non-negative")
    if n == 0:
        return ALPHABET[0]

    encoded = []
    while n:
        n, remainder = divmod(n, BASE)
        encoded.append(ALPHABET[remainder])
    return "".join(reversed(encoded))


def decode(s: str) -> int:
    """Decode a base62 string to a non-negative integer."""
    if not isinstance(s, str):
        raise TypeError("code must be a string")
    if not s:
        raise ValueError("code must not be empty")

    number = 0
    for character in s:
        digit = ALPHABET.find(character)
        if digit < 0:
            raise ValueError(f"invalid base62 character: {character!r}")
        number = number * BASE + digit
    return number


encode_base62 = encode
decode_base62 = decode
