"""Tests-first contract for benchmark data and measurement helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
from time import sleep
import unittest
from unittest.mock import patch

from measurement.datasets import (
    DatasetSpec,
    event_checksum,
    generate_events,
    liquidation_request,
    load_dataset,
    write_dataset,
)
from measurement.metrics import (
    latency_replay,
    nearest_rank,
    replay_diagnostics,
    timed_replay,
    traced_memory_replay,
    validate_report,
)
from orderbook.baseline import BaselineOrderBook
from orderbook.revised import RevisedOrderBook
import tools.run_benchmarks as benchmark_runner


class MeasurementContractTests(unittest.TestCase):
    def test_dataset_generation_is_deterministic_and_identified(self) -> None:
        spec = DatasetSpec("stream", "mixed", 100, 42, 20)
        first = generate_events(spec)
        second = generate_events(spec)
        other = generate_events(DatasetSpec("stream", "mixed", 100, 43, 20))

        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(event_checksum(first), event_checksum(second))
        self.assertNotEqual(event_checksum(first), event_checksum(other))
        self.assertEqual([event["seq"] for event in first], list(range(1, 101)))
        self.assertIn("stream__mixed__m100__seed42__levels20", spec.dataset_id)

    def test_stable_gzip_round_trip_and_metadata(self) -> None:
        spec = DatasetSpec("stream", "buildup", 25, 7, 10)
        events = generate_events(spec)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{spec.dataset_id}.jsonl.gz"
            metadata = write_dataset(path, spec, events)
            loaded, loaded_metadata = load_dataset(path)

            self.assertEqual(loaded, events)
            self.assertEqual(loaded_metadata, metadata)
            self.assertEqual(metadata["event_sha256"], event_checksum(events))
            self.assertEqual(metadata["event_count"], 25)
            self.assertEqual(metadata["synthetic"], True)
            self.assertEqual(metadata["calibrated_to_exchange_data"], False)

    def test_liquidation_requests_use_fresh_book_percentages(self) -> None:
        spec = DatasetSpec("liquidation", "bid_book", 40, 42, 8)
        events = generate_events(spec)
        total = sum(event["qty_units"] for event in events)

        self.assertTrue(all(event["type"] == "LIMIT" for event in events))
        self.assertTrue(all(event["side"] == "BUY" for event in events))
        self.assertEqual(liquidation_request(total, 10), max(1, (total + 9) // 10))
        self.assertEqual(liquidation_request(total, 100), total)
        self.assertEqual(liquidation_request(total, 200), total * 2)

    def test_liquidation_correctness_work_respects_declared_limit(self) -> None:
        class SlowBaseline(BaselineOrderBook):
            def ProcessEvent(self, event):
                sleep(0.02)
                return super().ProcessEvent(event)

        spec = DatasetSpec("liquidation", "bid_book", 2, 42, 8)
        events = generate_events(spec)
        metadata = {
            "dataset_id": spec.dataset_id,
            "experiment": spec.experiment,
            "scenario": spec.scenario,
            "event_count": spec.event_count,
            "seed": spec.seed,
            "levels": spec.levels,
            "event_sha256": event_checksum(events),
        }
        with patch.dict(
            benchmark_runner.IMPLEMENTATIONS,
            {"baseline": SlowBaseline, "revised": RevisedOrderBook},
            clear=True,
        ):
            records = benchmark_runner.liquidation_measurements(
                events,
                metadata,
                versions=(),
                repeats=1,
                warmup_events=1,
                time_limit_seconds=0.01,
                include_memory=False,
            )

        correctness = [
            record
            for record in records
            if record["measurement_kind"] == "correctness"
        ]
        self.assertEqual(len(correctness), 3)
        self.assertTrue(all(record["stopped"] for record in correctness))
        self.assertTrue(
            all("baseline" in record["stop_reason"] for record in correctness)
        )

    def test_nearest_rank_percentile_convention(self) -> None:
        samples = [50, 10, 40, 20, 30]
        self.assertEqual(nearest_rank(samples, 0), 10)
        self.assertEqual(nearest_rank(samples, 50), 30)
        self.assertEqual(nearest_rank(samples, 95), 50)
        self.assertEqual(nearest_rank(samples, 100), 50)
        with self.assertRaises(ValueError):
            nearest_rank([], 50)

    def test_latency_separates_event_types_and_early_late_windows(self) -> None:
        events = generate_events(DatasetSpec("stream", "mixed", 100, 42, 20))
        latency = latency_replay(RevisedOrderBook, events, 2.0)

        self.assertEqual(latency["stopped"], False)
        self.assertEqual(latency["sample_count"], 100)
        self.assertEqual(sum(item["count"] for item in latency["by_event_type"].values()), 100)
        self.assertEqual(latency["early_window"]["count"], 10)
        self.assertEqual(latency["late_window"]["count"], 10)
        self.assertEqual(latency["early_late_window_size"], 10)
        for summary in (
            *latency["by_event_type"].values(),
            latency["early_window"],
            latency["late_window"],
        ):
            self.assertGreaterEqual(summary["p99_ns"], summary["p50_ns"])

    def test_diagnostics_are_version_independent(self) -> None:
        events = generate_events(DatasetSpec("stream", "mixed", 100, 42, 20))
        baseline = replay_diagnostics(BaselineOrderBook, events)
        revised = replay_diagnostics(RevisedOrderBook, events)

        self.assertEqual(baseline, revised)
        self.assertEqual(baseline["events_processed"], 100)
        self.assertGreaterEqual(baseline["active_order_peak"], 0)
        self.assertGreaterEqual(baseline["occupied_price_level_peak"], 0)
        self.assertGreaterEqual(baseline["fill_count"], 0)

    def test_traced_memory_has_explicit_boundary_and_fresh_runs(self) -> None:
        events = generate_events(DatasetSpec("stream", "cancel_churn", 100, 42, 20))
        first = traced_memory_replay(BaselineOrderBook, events)
        second = traced_memory_replay(RevisedOrderBook, events)

        for record in (first, second):
            self.assertGreaterEqual(record["peak_traced_bytes"], record["current_traced_bytes"])
            self.assertGreaterEqual(record["current_traced_bytes"], 0)
            self.assertEqual(record["input_included"], False)
            self.assertEqual(record["book_included"], True)
            self.assertEqual(record["final_output_included"], True)
            self.assertEqual(record["prior_outputs_retained"], False)
            self.assertEqual(record["tracing_scope"], "fresh_per_version")
            self.assertEqual(len(record["allocation_checkpoints"]), 3)
            self.assertEqual(
                record["allocation_checkpoints"][-1]["events_processed"],
                100,
            )

    def test_declared_time_limit_labels_stopped_timing_and_memory(self) -> None:
        class SlowBook:
            def ProcessEvent(self, event):
                del event
                while True:
                    pass

        timing = timed_replay(SlowBook, ({"seq": 1},), 0.01)
        memory = traced_memory_replay(SlowBook, ({"seq": 1},), 0.01)

        for record in (timing, memory):
            self.assertEqual(record["stopped"], True)
            self.assertIn("exceeded 0.01 seconds", record["stop_reason"])
            self.assertEqual(record["events_processed"], 0)
        self.assertGreaterEqual(memory["peak_traced_bytes"], 0)

    def test_report_schema_rejects_missing_or_invented_measurements(self) -> None:
        report = {
            "schema_version": 1,
            "run_label": "provisional_smoke",
            "environment": {"python_version": "test"},
            "settings": {"repeats": 1},
            "datasets": [],
            "records": [
                {
                    "measurement_kind": "timing",
                    "phase": "engine_replay",
                    "version": "baseline",
                    "repeat": 0,
                    "elapsed_seconds": 0.1,
                    "stopped": False,
                }
            ],
        }
        validate_report(report)

        missing_elapsed = dict(report)
        missing_elapsed["records"] = [dict(report["records"][0])]
        del missing_elapsed["records"][0]["elapsed_seconds"]
        with self.assertRaises(ValueError):
            validate_report(missing_elapsed)

        invented = dict(report)
        invented["records"] = [dict(report["records"][0], stopped=True)]
        with self.assertRaises(ValueError):
            validate_report(invented)


if __name__ == "__main__":
    unittest.main()
