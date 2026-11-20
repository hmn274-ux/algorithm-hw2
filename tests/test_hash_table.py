import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_insert_update_lookup_and_membership(self):
        table = HashTable()
        table["url"] = "https://example.com"
        table["url"] = "https://example.org"

        self.assertEqual(table["url"], "https://example.org")
        self.assertEqual(table.get("missing"), None)
        self.assertEqual(table.get("missing", "fallback"), "fallback")
        self.assertIn("url", table)
        self.assertNotIn("missing", table)
        self.assertEqual(len(table), 1)

    def test_collisions_in_final_bucket_are_resolved(self):
        table = HashTable()
        # With the specified hash, "7" and "g" share the last bucket.
        final_bucket_keys = next(
            (left, right)
            for left in (str(number) for number in range(10))
            for right in ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j")
            if table.hash_index(left) == table.capacity - 1
            and table.hash_index(right) == table.capacity - 1
        )
        table[final_bucket_keys[0]] = "first"
        table[final_bucket_keys[1]] = "second"

        self.assertEqual(table[final_bucket_keys[0]], "first")
        self.assertEqual(table[final_bucket_keys[1]], "second")

    def test_delete_preserves_other_colliding_entries(self):
        table = HashTable()
        table["a"] = 1
        table["i"] = 2
        del table["a"]

        self.assertNotIn("a", table)
        self.assertEqual(table["i"], 2)
        self.assertEqual(len(table), 1)
        with self.assertRaises(KeyError):
            del table["missing"]

    def test_table_grows_after_load_threshold(self):
        table = HashTable()
        initial_capacity = table.capacity
        for key in ("a", "b", "c", "d", "e", "f", "g"):
            table[key] = key

        self.assertGreater(table.capacity, initial_capacity)
        for key in ("a", "b", "c", "d", "e", "f", "g"):
            self.assertEqual(table[key], key)

    def test_non_string_keys_are_rejected(self):
        table = HashTable()
        with self.assertRaises(TypeError):
            table[1] = "value"
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()
