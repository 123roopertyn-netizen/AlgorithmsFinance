"""Check the synthetic datasets before using them as search test fixtures."""

import json
import random
import unittest
from pathlib import Path

from generate_data import BASE_SEED, generate_random_case


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SIZES = (100, 1_000, 10_000)
HIT_RATES = (0.0, 0.5, 1.0)
SMALL_CASE_NAMES = {
    "both_empty",
    "empty_ids",
    "empty_queries",
    "single_id",
    "duplicates_and_negatives",
    "large_integers",
}


class TestSyntheticData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(DATA_DIR.glob("*.json"))
        }

    def test_expected_dataset_inventory(self):
        expected_names = SMALL_CASE_NAMES | {
            f"n{size}_q1000_hit{int(rate * 100)}"
            for size in SIZES
            for rate in HIT_RATES
        }
        self.assertEqual(
            set(self.cases),
            expected_names,
            "Run python generate_data.py to create the 15 required datasets.",
        )

    def test_saved_answers_and_metadata_are_correct(self):
        self.assertTrue(self.cases, "No generated datasets were found.")
        for name, case in self.cases.items():
            with self.subTest(dataset=name):
                ids = case["ids"]
                queries = case["queries"]
                expected = case["expected"]
                metadata = case["metadata"]
                self.assertEqual(case["name"], name)
                self.assertIsInstance(ids, list)
                self.assertIsInstance(queries, list)
                self.assertIsInstance(expected, list)
                self.assertTrue(all(type(value) is int for value in ids))
                self.assertTrue(all(type(value) is int for value in queries))
                self.assertTrue(all(type(value) is bool for value in expected))
                self.assertEqual(len(expected), len(queries))
                self.assertEqual(metadata["n_ids"], len(ids))
                self.assertEqual(metadata["n_queries"], len(queries))
                category = "correctness" if name in SMALL_CASE_NAMES else "benchmark"
                self.assertEqual(metadata["category"], category)
                reference_ids = set(ids)
                self.assertEqual(expected, [query in reference_ids for query in queries])

    def test_generator_produces_requested_hit_rates(self):
        for hit_rate in HIT_RATES:
            with self.subTest(hit_rate=hit_rate):
                ids, queries, expected = generate_random_case(64, 20, hit_rate, 17)
                reference_ids = set(ids)
                self.assertEqual(len(ids), 64)
                self.assertEqual(len(queries), 20)
                self.assertTrue(all(type(value) is bool for value in expected))
                self.assertEqual(expected, [query in reference_ids for query in queries])
                self.assertEqual(sum(expected), round(20 * hit_rate))

    def test_saved_benchmarks_can_be_reproduced(self):
        for size in SIZES:
            for hit_rate in HIT_RATES:
                name = f"n{size}_q1000_hit{int(hit_rate * 100)}"
                with self.subTest(dataset=name):
                    case = self.cases[name]
                    metadata = case["metadata"]
                    self.assertEqual(metadata["seed"], BASE_SEED + size)
                    self.assertEqual(metadata["target_hit_rate"], hit_rate)
                    regenerated = generate_random_case(size, 1_000, hit_rate, metadata["seed"])
                    self.assertEqual(regenerated, (case["ids"], case["queries"], case["expected"]))
                    self.assertEqual(sum(case["expected"]), round(1_000 * hit_rate))

    def test_hit_rate_variants_use_the_same_id_array(self):
        for size in SIZES:
            with self.subTest(size=size):
                baseline_ids = self.cases[f"n{size}_q1000_hit0"]["ids"]
                for hit_rate in HIT_RATES:
                    name = f"n{size}_q1000_hit{int(hit_rate * 100)}"
                    self.assertEqual(self.cases[name]["ids"], baseline_ids)

    def test_same_seed_repeats_the_same_data(self):
        first = generate_random_case(128, 64, 0.5, 123)
        second = generate_random_case(128, 64, 0.5, 123)
        self.assertEqual(first, second)

    def test_generator_preserves_global_random_state(self):
        original_state = random.getstate()
        try:
            generate_random_case(128, 64, 0.5, 123)
            self.assertEqual(random.getstate(), original_state)
        finally:
            random.setstate(original_state)


if __name__ == "__main__":
    unittest.main()
