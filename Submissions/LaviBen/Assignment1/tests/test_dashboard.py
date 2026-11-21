"""Saved-result dashboard generation tests; no benchmark is run here."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from dashboard import render_dashboard, write_dashboard


REPORT = {
    "schema_version": 1,
    "run_label": "provisional_smoke",
    "created_at_utc": "2026-11-21T12:00:00+00:00",
    "environment": {
        "python_version": "3.test",
        "platform": "test-platform",
        "git_commit": "abc123",
        "git_dirty": True,
    },
    "settings": {"repeats": 2, "time_limit_seconds_per_phase": 1},
    "datasets": [
        {
            "dataset_id": "stream__mixed__m1000__seed42__levels1000",
            "experiment": "stream",
            "scenario": "mixed",
            "event_count": 1000,
            "seed": 42,
            "levels": 1000,
            "event_sha256": "deadbeef",
        }
    ],
    "records": [
        {
            "measurement_kind": "timing",
            "phase": "engine_replay",
            "version": "baseline",
            "dataset_id": "stream__mixed__m1000__seed42__levels1000",
            "experiment": "stream",
            "scenario": "mixed",
            "event_count": 1000,
            "seed": 42,
            "levels": 1000,
            "event_sha256": "deadbeef",
            "repeat": 0,
            "elapsed_seconds": 0.1,
            "time_unit": "seconds",
            "stopped": False,
        },
        {
            "measurement_kind": "memory",
            "phase": "engine_replay",
            "version": "revised",
            "dataset_id": "stream__mixed__m1000__seed42__levels1000",
            "experiment": "stream",
            "scenario": "mixed",
            "event_count": 1000,
            "seed": 42,
            "levels": 1000,
            "event_sha256": "deadbeef",
            "current_traced_bytes": 100,
            "peak_traced_bytes": 200,
            "stopped": False,
        },
        {
            "measurement_kind": "correctness",
            "phase": "diagnostic_prefix",
            "version": "shared",
            "dataset_id": "stream__mixed__m1000__seed42__levels1000",
            "experiment": "stream",
            "scenario": "mixed",
            "event_count": 1000,
            "seed": 42,
            "levels": 1000,
            "event_sha256": "deadbeef",
            "ordered_results_equal": True,
            "final_books_equal": True,
            "stopped": False,
        },
    ],
}


class DashboardTests(unittest.TestCase):
    def test_dashboard_contains_required_saved_result_views(self) -> None:
        html = render_dashboard(REPORT)

        for text in (
            "Saved-results dashboard",
            "Timing and throughput",
            "Processing latency",
            "Traced memory",
            "Liquidation",
            "Correctness",
            "Raw repeats",
            "Environment and settings",
            "provisional_smoke",
            "test-platform",
        ):
            self.assertIn(text, html)
        self.assertIn("setDefault('experiment','stream')", html)
        self.assertIn("seriesKey", html)
        self.assertNotIn("run_benchmarks.py", html)

    def test_dashboard_output_is_byte_stable_for_same_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.html"
            second = Path(directory) / "second.html"
            write_dashboard(REPORT, first)
            write_dashboard(REPORT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
