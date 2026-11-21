"""Tests for the short report generated only from saved results."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from build_report import render_report, write_report_markdown
from test_dashboard import REPORT


class ReportingTests(unittest.TestCase):
    def test_report_contains_required_assignment_sections(self) -> None:
        timing_summary = {
            **REPORT["records"][0],
            "measurement_kind": "timing_summary",
            "phase": "application_total",
            "version": "revised",
            "liquidation_percent": 100,
            "elapsed_seconds_median": 0.2,
            "throughput_events_per_second_median": 5_000,
        }
        report = render_report(
            {**REPORT, "records": [*REPORT["records"], timing_summary]}
        )
        for heading in (
            "# Limit order book report",
            "## Specification and boundaries",
            "## Correctness evidence",
            "## Implementation and revision",
            "## Runtime and throughput",
            "## Processing latency",
            "## Memory",
            "## Bottleneck and operation counts",
            "## Limitations",
            "## Reproducibility",
        ):
            self.assertIn(heading, report)
        self.assertIn("provisional_smoke", report)
        self.assertIn("abc123", report)
        self.assertIn(
            "| Experiment | Scenario | M | Levels | Version | Phase | Sale % |",
            report,
        )
        self.assertIn("Completed correctness rows passing", report)
        self.assertIn("stopped by the declared limit", report)

    def test_report_output_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "one.md"
            second = Path(directory) / "two.md"
            write_report_markdown(REPORT, first)
            write_report_markdown(REPORT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
