import unittest

from src.minimum_finder import MinimumFinder


class TestMinimumFinder(unittest.TestCase):
    def setUp(self) -> None:
        self.lowercase_chars = tuple(chr(i) for i in range(ord("a"), ord("z") + 1))

    def test_find_single_min(self):
        minimum_finder = MinimumFinder(lambda vals: "c" in vals)
        min = minimum_finder.find_smallest_permission_set(self.lowercase_chars)
        self.assertEqual(("c",), min)

    def test_find_two_min(self):
        minimum_finder = MinimumFinder(lambda vals: "c" in vals and "x" in vals)
        min = minimum_finder.find_smallest_permission_set(self.lowercase_chars)
        self.assertEqual(("c", "x"), min)

    def test_find_many_min(self):
        minimum_finder = MinimumFinder(
            lambda vals: "a" in vals and "c" in vals and "f" in vals and "x" in vals
        )
        min = minimum_finder.find_smallest_permission_set(self.lowercase_chars)
        self.assertEqual(("a", "c", "f", "x"), min)


if __name__ == "__main__":
    unittest.main()
