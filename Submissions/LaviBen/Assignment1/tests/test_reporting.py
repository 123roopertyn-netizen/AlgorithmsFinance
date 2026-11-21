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
        self.assertIn("Partial timing summaries:", report)

    def test_report_output_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "one.md"
            second = Path(directory) / "two.md"
            write_report_markdown(REPORT, first)
            write_report_markdown(REPORT, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_report_discloses_expected_stopped_and_missing_repeats(self) -> None:
        summary = {
            **REPORT["records"][0],
            "measurement_kind": "timing_summary",
            "phase": "engine_replay",
            "version": "revised",
            "repeat": None,
            "elapsed_seconds_median": 0.2,
            "expected_repeat_count": 5,
            "completed_repeat_count": 2,
            "stopped_repeat_count": 1,
            "missing_repeat_count": 2,
            "completion_status": "partial",
            "stopped": False,
        }
        revision_three = {
            **REPORT,
            "settings": {
                **REPORT["settings"],
                "measurement_integrity_revision": 3,
            },
            "records": [*REPORT["records"], summary],
        }

        report = render_report(revision_three)

        self.assertIn("2/5 (1 stopped, 2 missing)", report)
        self.assertIn("Missing timing repeats: 2.", report)

    def test_report_labels_bounded_operation_count_coverage(self) -> None:
        operation_counts = {
            **REPORT["records"][0],
            "measurement_kind": "operation_counts",
            "phase": "diagnostic_prefix_instrumented",
            "version": "revised",
            "events_requested": 100,
            "events_processed": 100,
            "active_order_peak": 12,
            "occupied_price_level_peak": 4,
            "fill_count": 3,
            "maker_price_levels_visited": 2,
            "final_active_order_count": 9,
        }

        report = render_report({**REPORT, "records": [operation_counts]})

        self.assertIn("Requested / processed", report)
        self.assertIn("100 / 100", report)

    def test_legacy_clean_report_is_marked_superseded(self) -> None:
        legacy = {
            **REPORT,
            "run_label": "canonical",
            "environment": {**REPORT["environment"], "git_dirty": False},
        }

        report = render_report(legacy)

        self.assertIn("SUPERSEDED: legacy measurement evidence.", report)
        self.assertNotIn(
            "**Evidence status:** Canonical clean-tree evidence.",
            report,
        )

        revision_two = {
            **legacy,
            "settings": {
                **legacy["settings"],
                "measurement_integrity_revision": 2,
            },
        }
        revision_two_report = render_report(revision_two)
        self.assertIn("SUPERSEDED: legacy measurement evidence.", revision_two_report)
        self.assertNotIn(
            "**Evidence status:** Canonical clean-tree evidence.",
            revision_two_report,
        )

        corrected = {
            **legacy,
            "settings": {
                **legacy["settings"],
                "measurement_integrity_revision": 3,
            },
        }
        corrected_report = render_report(corrected)
        self.assertIn(
            "**Evidence status:** Canonical clean-tree evidence.",
            corrected_report,
        )
        self.assertNotIn(
            "SUPERSEDED: legacy measurement evidence.",
            corrected_report,
        )


if __name__ == "__main__":
    unittest.main()
