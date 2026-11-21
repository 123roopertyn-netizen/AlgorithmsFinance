"""Integrity and schema checks for the copied course teaching data."""

from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FixtureTests(unittest.TestCase):
    def test_every_copied_file_matches_recorded_size_and_sha256(self) -> None:
        manifest = json.loads(
            (PROJECT_ROOT / "fixtures" / "CHECKSUMS.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(manifest["copied_byte_for_byte"])
        for relative_path, expected in manifest["files"].items():
            with self.subTest(path=relative_path):
                path = PROJECT_ROOT / relative_path
                content = path.read_bytes()
                self.assertEqual(len(content), expected["bytes"])
                self.assertEqual(hashlib.sha256(content).hexdigest(), expected["sha256"])

    def test_supplied_streams_have_exact_counts_shapes_and_sequence(self) -> None:
        expected_types = {
            "buildup": {"LIMIT": 10_000},
            "cancel_churn": {"LIMIT": 5_000, "CANCEL": 5_000},
            "crowded": {"LIMIT": 10_000},
            "mixed": {"LIMIT": 6_075, "CANCEL": 2_438, "MARKET_SELL": 1_487},
            "sweep": {"LIMIT": 8_000, "MARKET_SELL": 2_000},
        }
        supplied = PROJECT_ROOT / "fixtures" / "supplied"

        for scenario, type_counts in expected_types.items():
            with self.subTest(scenario=scenario):
                data_path = supplied / f"{scenario}_10000.jsonl.gz"
                metadata = json.loads(
                    (supplied / f"{scenario}_10000.jsonl.gz.metadata.json").read_text(
                        encoding="utf-8"
                    )
                )
                counts: Counter[str] = Counter()
                sequences = []
                event_ids = set()
                with gzip.open(data_path, "rt", encoding="utf-8") as stream:
                    for line in stream:
                        event = json.loads(line)
                        counts[event["type"]] += 1
                        sequences.append(event["seq"])
                        event_ids.add(event["event_id"])
                self.assertEqual(dict(counts), type_counts)
                self.assertEqual(sequences, list(range(1, 10_001)))
                self.assertEqual(len(event_ids), 10_000)
                self.assertEqual(metadata["scenario"], scenario)
                self.assertEqual(metadata["events"], 10_000)
                self.assertEqual(metadata["seed"], 42)
                self.assertEqual(metadata["sha256"], hashlib.sha256(data_path.read_bytes()).hexdigest())

    def test_generator_is_local_seeded_and_reproducible(self) -> None:
        path = PROJECT_ROOT / "tools" / "generate_orders.py"
        spec = importlib.util.spec_from_file_location("assignment1_generator", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        first = tuple(module.events("mixed", 100, 42, 20))
        second = tuple(module.events("mixed", 100, 42, 20))
        different = tuple(module.events("mixed", 100, 43, 20))
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertEqual([event["seq"] for event in first], list(range(1, 101)))

    def test_worked_fixture_contains_independent_expected_values(self) -> None:
        expected = json.loads(
            (PROJECT_ROOT / "fixtures" / "worked_expected.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [fill["maker_id"] for fill in expected["market_sell_result"]["fills"]],
            ["b1", "b2", "b3", "b4"],
        )
        self.assertEqual(
            [fill["qty_units"] for fill in expected["market_sell_result"]["fills"]],
            [100_000_000, 100_000_000, 300_000_000, 100_000_000],
        )
        self.assertEqual(expected["gross_proceeds_tick_units"], 3_594_000_000_000_000)
        self.assertEqual(expected["gross_proceeds_usd"], "359400.00")


if __name__ == "__main__":
    unittest.main()
