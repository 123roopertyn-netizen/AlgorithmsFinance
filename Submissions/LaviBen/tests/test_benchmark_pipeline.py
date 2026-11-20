"""Small, fast integration tests for benchmark and dashboard generation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmark import ALGORITHMS, run_benchmarks, write_results
from dashboard import build_dashboard


class BenchmarkPipelineTests(unittest.TestCase):
    def test_every_algorithm_is_measured_for_every_size(self) -> None:
        sizes = [0, 4]
        results = run_benchmarks(sizes, repeats=1, seed=12, hit_rate=0.5)

        self.assertEqual(len(results), len(sizes) * len(ALGORITHMS))
        self.assertEqual({result.array_size for result in results}, set(sizes))
        self.assertTrue(all(result.median_ms >= 0 for result in results))

    def test_results_and_dashboard_are_reproducible_artifacts(self) -> None:
        results = run_benchmarks([3], repeats=1, seed=7, hit_rate=0.5)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            json_path, csv_path = write_results(
                results,
                output_directory,
                seed=7,
                hit_rate=0.5,
            )
            dashboard_path = build_dashboard(
                json_path,
                output_directory / "runtime_dashboard.html",
            )

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            dashboard = dashboard_path.read_text(encoding="utf-8")

            self.assertEqual(len(payload["results"]), len(ALGORITHMS))
            self.assertIn("algorithm,array_size,query_count", csv_path.read_text())
            self.assertIn("Search runtime dashboard", dashboard)
            self.assertIn("Binary search iterative v2", dashboard)


if __name__ == "__main__":
    unittest.main()
