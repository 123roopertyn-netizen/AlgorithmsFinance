"""One correctness contract, applied without changes to all three search methods.

The search_algorithms module is deliberately not implemented in this test-first
step. Full discovery will report an import error until that module is added.
"""

import json
import random
import unittest
from pathlib import Path

import search_algorithms


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


class SearchContract:
    """Mixin so every implementation inherits exactly the same tests."""

    def setUp(self):
        self.search = getattr(search_algorithms, self.method_name)

    def check_result(self, ids, queries, expected):
        original_ids = ids.copy()
        original_queries = queries.copy()

        actual = self.search(ids, queries)

        self.assertEqual(ids, original_ids, "The input ID array was modified.")
        self.assertEqual(queries, original_queries, "The input queries were modified.")
        self.assertIsInstance(actual, list, "Return a list of Boolean answers.")
        self.assertEqual(len(actual), len(original_queries))
        self.assertTrue(
            all(type(answer) is bool for answer in actual),
            "Answers must be actual Booleans; integer 0/1 answers are insufficient.",
        )
        self.assertEqual(actual, expected, "Incorrect answers or query order.")

    def test_empty_array(self):
        self.check_result([], [5, -3, 5], [False, False, False])

    def test_empty_queries(self):
        self.check_result([3, 1, 3], [], [])

    def test_both_empty(self):
        self.check_result([], [], [])

    def test_singleton_and_neighbors(self):
        self.check_result([7], [7, 6, 8, 7], [True, False, False, True])

    def test_duplicates_negatives_and_query_order(self):
        self.check_result(
            [4, -2, 4, 0, -2],
            [4, 3, -2, 4, 0, -9],
            [True, False, True, True, True, False],
        )

    def test_sorted_array_boundaries(self):
        self.check_result(
            [-5, 0, 3, 9, 12],
            [-6, -5, 12, 13, 0, 8, 3, 9],
            [False, True, True, False, True, False, True, True],
        )

    def test_reverse_sorted_array(self):
        self.check_result(
            [12, 9, 3, 0, -5],
            [12, -5, 1, 3, 0],
            [True, True, False, True, True],
        )

    def test_very_large_integer_ids(self):
        large_id = 10**100
        self.check_result(
            [-large_id, 0, large_id],
            [large_id - 1, large_id, -large_id, 0, -large_id - 1],
            [False, True, True, True, False],
        )

    def test_all_ids_identical(self):
        self.check_result([5] * 30, [4, 5, 6, 5], [False, True, False, True])

    def test_no_queries_match(self):
        self.check_result([3, 1, 3, 0, -2], [2, 4, -3, 1_000], [False] * 4)

    def test_all_queries_match(self):
        self.check_result([8, -3, 0, 8], [0, 8, -3, 8], [True] * 4)

    def test_same_list_can_be_ids_and_queries(self):
        ids = [3, -1, 3, 0]
        self.check_result(ids, ids, [True] * 4)

    def test_repeated_calls_use_the_current_array(self):
        queries = [5, 8, 5]
        self.check_result([5], queries, [True, False, True])
        self.check_result([8], queries, [False, True, False])
        self.check_result([5], queries, [True, False, True])

    def test_seeded_random_cases_against_reference(self):
        rng = random.Random(984)
        for n_ids in (0, 1, 2, 5, 10, 31, 100):
            for n_queries in (0, 1, 2, 7, 32):
                with self.subTest(n_ids=n_ids, n_queries=n_queries):
                    ids = [rng.randint(-20, 20) for _ in range(n_ids)]
                    queries = [rng.randint(-30, 30) for _ in range(n_queries)]
                    if ids and queries:
                        queries[0] = rng.choice(ids)
                    if len(queries) > 1:
                        queries[-1] = 1_000
                    reference_ids = set(ids)
                    expected = [query in reference_ids for query in queries]
                    self.check_result(ids, queries, expected)

    def test_all_saved_datasets(self):
        dataset_paths = sorted(DATA_DIR.glob("*.json"))
        self.assertTrue(dataset_paths, "Run python generate_data.py first.")
        for path in dataset_paths:
            with self.subTest(dataset=path.stem):
                case = json.loads(path.read_text(encoding="utf-8"))
                self.check_result(case["ids"], case["queries"], case["expected"])


class TestLinearSearch(SearchContract, unittest.TestCase):
    method_name = "linear_search"


class TestBinarySearch(SearchContract, unittest.TestCase):
    method_name = "binary_search"


class TestHashSetMembership(SearchContract, unittest.TestCase):
    method_name = "hash_set_membership"


if __name__ == "__main__":
    unittest.main()
