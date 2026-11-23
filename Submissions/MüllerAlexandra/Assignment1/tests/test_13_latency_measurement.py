"""Latency instrumentation preserves raw samples and documented breakdowns."""

from __future__ import annotations

from collections.abc import Iterator
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from limit_order_book.measurement import (
    latency_breakdown_ns,
    measure_event_latencies,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_SCRIPT = PROJECT_ROOT / "scripts" / "04_benchmark.py"


class FakeBook:
    def __init__(self) -> None:
        self.sequences: list[int] = []

    def process_event(self, event: dict[str, object]) -> dict[str, object]:
        sequence = event["seq"]
        assert isinstance(sequence, int)
        self.sequences.append(sequence)
        return {"status": "accepted"}


def test_event_latencies_use_one_fresh_book_and_keep_raw_samples() -> None:
    books: list[FakeBook] = []
    clock_values: Iterator[int] = iter([100, 110, 200, 225])

    def factory() -> FakeBook:
        book = FakeBook()
        books.append(book)
        return book

    records = measure_event_latencies(
        factory,
        [
            {"seq": 1, "type": "LIMIT"},
            {"seq": 2, "type": "CANCEL"},
        ],
        clock_ns=lambda: next(clock_values),
    )

    assert len(books) == 1
    assert books[0].sequences == [1, 2]
    assert records == [
        {
            "event_index": 1,
            "event_type": "LIMIT",
            "latency_ns": 10,
        },
        {
            "event_index": 2,
            "event_type": "CANCEL",
            "latency_ns": 25,
        },
    ]


def test_latency_measurement_rejects_empty_input_or_negative_clock() -> None:
    with pytest.raises(ValueError):
        measure_event_latencies(FakeBook, [])

    clock_values: Iterator[int] = iter([10, 9])
    with pytest.raises(ValueError):
        measure_event_latencies(
            FakeBook,
            [{"seq": 1, "type": "LIMIT"}],
            clock_ns=lambda: next(clock_values),
        )


def test_latency_breakdown_reports_overall_type_and_ten_percent_windows() -> None:
    records = [
        {
            "event_index": index,
            "event_type": "LIMIT" if index % 2 else "CANCEL",
            "latency_ns": index,
        }
        for index in range(1, 11)
    ]

    assert latency_breakdown_ns(records) == {
        "overall": {
            "sample_count": 10,
            "median_ns": 5.5,
            "p95_ns": 10,
            "p99_ns": 10,
        },
        "by_event_type": {
            "CANCEL": {
                "sample_count": 5,
                "median_ns": 6,
                "p95_ns": 10,
                "p99_ns": 10,
            },
            "LIMIT": {
                "sample_count": 5,
                "median_ns": 5,
                "p95_ns": 9,
                "p99_ns": 9,
            },
        },
        "early_10_percent": {
            "sample_count": 1,
            "median_ns": 1,
            "p95_ns": 1,
            "p99_ns": 1,
        },
        "late_10_percent": {
            "sample_count": 1,
            "median_ns": 10,
            "p95_ns": 10,
            "p99_ns": 10,
        },
        "window_size": 1,
    }


def test_latency_breakdown_rejects_empty_records() -> None:
    with pytest.raises(ValueError):
        latency_breakdown_ns([])


def benchmark_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def test_latency_cli_writes_distinct_raw_and_summary_output(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    source.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "seq": 1,
                        "event_id": "e1",
                        "type": "CANCEL",
                        "target_order_id": "x",
                    }
                ),
                json.dumps(
                    {
                        "seq": 2,
                        "event_id": "e2",
                        "type": "CANCEL",
                        "target_order_id": "y",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "latency.json"

    completed = subprocess.run(
        [
            sys.executable,
            str(BENCHMARK_SCRIPT),
            "--phase",
            "latency",
            "--version",
            "baseline",
            "--input",
            str(source),
            "--max-events",
            "2",
            "--out",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        env=benchmark_environment(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["phase"] == "latency"
    assert document["settings"] == {
        "clock": "time.perf_counter_ns",
        "window_fraction": 0.1,
    }
    assert len(document["records"]) == 2
    assert all(record["latency_ns"] >= 0 for record in document["records"])
    assert document["summary"]["overall"]["sample_count"] == 2
    assert document["summary"]["by_event_type"]["CANCEL"]["sample_count"] == 2
