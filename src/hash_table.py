"""A string-keyed hash table using separate chaining."""

import math


class _Entry:
    __slots__ = ("key", "value", "next")

    def __init__(self, key, value, next_entry=None):
        self.key = key
        self.value = value
        self.next = next_entry


class HashTable:
    """A small mapping from string keys to arbitrary values."""

    _HASH_BASE = 31
    _MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity=8, max_load=_MAX_LOAD_FACTOR):
        if (
            isinstance(initial_capacity, bool)
            or not isinstance(initial_capacity, int)
            or initial_capacity < 1
        ):
            raise ValueError("initial_capacity must be a positive integer")
        if max_load is not None and (
            isinstance(max_load, bool)
            or not isinstance(max_load, (int, float))
            or max_load <= 0
            or (isinstance(max_load, float) and not math.isfinite(max_load))
        ):
            raise ValueError("max_load must be a positive finite number or None")
        self._buckets = [None] * initial_capacity
        self._size = 0
        self._max_load = max_load

    @property
    def capacity(self):
        return len(self._buckets)

    @property
    def load_factor(self):
        return self._size / self.capacity

    def hash_index(self, key):
        """Return the bucket index produced by the Horner polynomial."""
        self._validate_key(key)
        value = 0
        for character in key:
            value = (value * self._HASH_BASE + ord(character)) % self.capacity
        return value

    def __setitem__(self, key, value):
        index = self.hash_index(key)
        entry = self._buckets[index]
        while entry is not None:
            if entry.key == key:
                entry.value = value
                return
            entry = entry.next

        if (
            self._max_load is not None
            and (self._size + 1) / self.capacity > self._max_load
        ):
            self._resize(self.capacity * 2)
            index = self.hash_index(key)
        self._buckets[index] = _Entry(key, value, self._buckets[index])
        self._size += 1

    def __getitem__(self, key):
        entry = self._find_entry(key)
        if entry is None:
            raise KeyError(key)
        return entry.value

    def get(self, key, default=None):
        entry = self._find_entry(key)
        return default if entry is None else entry.value

    def __contains__(self, key):
        return self._find_entry(key) is not None

    def __delitem__(self, key):
        index = self.hash_index(key)
        previous = None
        entry = self._buckets[index]
        while entry is not None:
            if entry.key == key:
                if previous is None:
                    self._buckets[index] = entry.next
                else:
                    previous.next = entry.next
                self._size -= 1
                return
            previous = entry
            entry = entry.next
        raise KeyError(key)

    def __len__(self):
        return self._size

    def items(self):
        for bucket in self._buckets:
            entry = bucket
            while entry is not None:
                yield entry.key, entry.value
                entry = entry.next

    def bucket_items(self):
        """Return the keys and values grouped by bucket for inspection."""
        buckets = []
        for bucket in self._buckets:
            entries = []
            entry = bucket
            while entry is not None:
                entries.append((entry.key, entry.value))
                entry = entry.next
            buckets.append(entries)
        return buckets

    def probe_count(self, key):
        """Count key comparisons needed to find a key in its chain."""
        index = self.hash_index(key)
        comparisons = 0
        entry = self._buckets[index]
        while entry is not None:
            comparisons += 1
            if entry.key == key:
                break
            entry = entry.next
        return comparisons

    def _find_entry(self, key):
        index = self.hash_index(key)
        entry = self._buckets[index]
        while entry is not None:
            if entry.key == key:
                return entry
            entry = entry.next
        return None

    def _resize(self, new_capacity):
        old_buckets = self._buckets
        self._buckets = [None] * new_capacity
        for bucket in old_buckets:
            entry = bucket
            while entry is not None:
                index = self.hash_index(entry.key)
                self._buckets[index] = _Entry(
                    entry.key, entry.value, self._buckets[index]
                )
                entry = entry.next

    @staticmethod
    def _validate_key(key):
        if not isinstance(key, str):
            raise TypeError("keys must be strings")
