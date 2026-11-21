"""Timing, latency, diagnostics, memory, environment, and report validation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
import gc
import gzip
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
from time import perf_counter, perf_counter_ns, get_clock_info
import tracemalloc
from typing import Any, Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MeasurementTimeout(TimeoutError):
    """Raised when a declared per-phase wall-time limit is reached."""


@contextmanager
def time_limit(seconds: float | None) -> Iterator[None]:
    """Apply a POSIX real-time limit without hiding an interrupted run."""

    if seconds is None:
        yield
        return
    if seconds <= 0:
        raise ValueError("time limit must be positive")
    if not hasattr(signal, "setitimer"):
        raise RuntimeError("time limits require signal.setitimer on this platform")

    def handle_timeout(signum: int, frame: object) -> None:
        del signum, frame
        raise MeasurementTimeout(f"phase exceeded {seconds} seconds")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, handle_timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer != (0.0, 0.0):
            signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def nearest_rank(samples: Sequence[int], percentile: float) -> int:
    """Return the nearest-rank percentile (ceil(p*n), clamped at rank one)."""

    if not samples:
        raise ValueError("percentile requires at least one sample")
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(samples)
    rank = max(1, math.ceil(percentile / 100 * len(ordered)))
    return ordered[rank - 1]


def latency_summary(samples: Sequence[int]) -> dict[str, int]:
    """Summarize a nonempty latency sample with the declared convention."""

    if not samples:
        raise ValueError("latency summary requires at least one sample")
    return {
        "count": len(samples),
        "p50_ns": nearest_rank(samples, 50),
        "p95_ns": nearest_rank(samples, 95),
        "p99_ns": nearest_rank(samples, 99),
    }


def book_counts(book: Any) -> tuple[int, int]:
    # Diagnostics are intentionally separate from primary timing. Use the
    # concrete structures when available so 100,000-event peak tracking does
    # not sort the full public inspection view after every event.
    if hasattr(book, "_active") and hasattr(book, "_levels"):
        active = len(book._active)
        levels = len(book._levels["BUY"]) + len(book._levels["SELL"])
        return active, levels
    if hasattr(book, "_orders"):
        orders = book._orders
        levels = {(order.side, order.price_ticks) for order in orders}
        return len(orders), len(levels)
    orders = book.InspectBook()
    levels = {(order["side"], order["price_ticks"]) for order in orders}
    return len(orders), len(levels)


def replay_diagnostics(
    book_class: type[Any], events: Sequence[Mapping[str, object]]
) -> dict[str, object]:
    """Collect correctness/operation counts in a separate instrumented run."""

    book = book_class()
    event_types: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    active_peak = 0
    level_peak = 0
    fill_count = 0
    filled_qty = 0
    levels_visited = 0
    market_unfilled_qty = 0

    for event in events:
        event_types[str(event.get("type"))] += 1
        result = book.ProcessEvent(event)
        statuses[str(result["status"])] += 1
        fills = result.get("fills", [])
        fill_count += len(fills)
        filled_qty += sum(item["qty_units"] for item in fills)
        levels_visited += len({item["price_ticks"] for item in fills})
        if event.get("type") == "MARKET_SELL":
            market_unfilled_qty += result["unfilled_qty_units"]
        active, occupied = book_counts(book)
        active_peak = max(active_peak, active)
        level_peak = max(level_peak, occupied)

    final_active, final_levels = book_counts(book)
    return {
        "events_processed": len(events),
        "event_type_counts": dict(sorted(event_types.items())),
        "status_counts": dict(sorted(statuses.items())),
        "active_order_peak": active_peak,
        "occupied_price_level_peak": level_peak,
        "final_active_order_count": final_active,
        "final_occupied_price_levels": final_levels,
        "fill_count": fill_count,
        "filled_qty_units": filled_qty,
        "maker_price_levels_visited": levels_visited,
        "market_unfilled_qty_units": market_unfilled_qty,
    }


def timed_replay(
    book_class: type[Any],
    events: Sequence[Mapping[str, object]],
    time_limit_seconds: float | None,
) -> dict[str, object]:
    """Time empty-book construction plus a complete event batch."""

    processed = 0
    last_output: dict[str, object] | None = None
    started = perf_counter()
    try:
        with time_limit(time_limit_seconds):
            book = book_class()
            for event in events:
                last_output = book.ProcessEvent(event)
                processed += 1
    except MeasurementTimeout as error:
        elapsed = perf_counter() - started
        return {
            "elapsed_seconds": elapsed,
            "events_processed": processed,
            "stopped": True,
            "stop_reason": str(error),
        }
    elapsed = perf_counter() - started
    # Keep the final output live until after the clock read.
    assert last_output is not None or not events
    return {
        "elapsed_seconds": elapsed,
        "events_processed": processed,
        "stopped": False,
    }


def latency_replay(
    book_class: type[Any],
    events: Sequence[Mapping[str, object]],
    time_limit_seconds: float | None,
) -> dict[str, object]:
    """Record every per-event processing duration in a separate run."""

    book = book_class()
    samples: list[int] = []
    try:
        with time_limit(time_limit_seconds):
            for event in events:
                started = perf_counter_ns()
                book.ProcessEvent(event)
                samples.append(perf_counter_ns() - started)
    except MeasurementTimeout as error:
        result: dict[str, object] = {
            "samples_ns": samples,
            "sample_count": len(samples),
            "stopped": True,
            "stop_reason": str(error),
        }
        if samples:
            result.update(_latency_breakdowns(events[: len(samples)], samples))
        return result
    return {
        "samples_ns": samples,
        "sample_count": len(samples),
        **latency_summary(samples),
        **_latency_breakdowns(events, samples),
        "stopped": False,
    }


def _latency_breakdowns(
    events: Sequence[Mapping[str, object]], samples: Sequence[int]
) -> dict[str, object]:
    grouped: dict[str, list[int]] = {}
    for event, sample in zip(events, samples, strict=True):
        grouped.setdefault(str(event.get("type")), []).append(sample)
    by_event_type = {
        event_type: latency_summary(values)
        for event_type, values in sorted(grouped.items())
    }
    window_size = max(1, min(1_000, math.ceil(len(samples) * 0.10)))
    return {
        "by_event_type": by_event_type,
        "early_late_window_size": window_size,
        "early_window": latency_summary(samples[:window_size]),
        "late_window": latency_summary(samples[-window_size:]),
    }


def traced_memory_replay(
    book_class: type[Any],
    events: Sequence[Mapping[str, object]],
    time_limit_seconds: float | None = None,
) -> dict[str, object]:
    """Measure Python allocations with input prepared before fresh tracing."""

    if tracemalloc.is_tracing():
        raise RuntimeError("tracemalloc must not already be running")
    gc.collect()
    processed = 0
    stopped = False
    stop_reason: str | None = None
    event_count = len(events)
    checkpoint_specs = []
    for fraction in (0.10, 0.50, 1.00):
        target = max(1, math.ceil(event_count * fraction)) if event_count else 0
        if target not in {item["events_processed"] for item in checkpoint_specs}:
            checkpoint_specs.append(
                {
                    "fraction": fraction,
                    "events_processed": target,
                    "current_traced_bytes": None,
                    "peak_traced_bytes": None,
                }
            )
    checkpoint_by_target = {
        item["events_processed"]: item for item in checkpoint_specs if item["events_processed"]
    }
    tracemalloc.start()
    try:
        book = book_class()
        final_output: dict[str, object] | None = None
        try:
            with time_limit(time_limit_seconds):
                for event in events:
                    final_output = book.ProcessEvent(event)
                    processed += 1
                    checkpoint = checkpoint_by_target.get(processed)
                    if checkpoint is not None:
                        checkpoint_current, checkpoint_peak = tracemalloc.get_traced_memory()
                        checkpoint["current_traced_bytes"] = checkpoint_current
                        checkpoint["peak_traced_bytes"] = checkpoint_peak
        except MeasurementTimeout as error:
            stopped = True
            stop_reason = str(error)
        current, peak = tracemalloc.get_traced_memory()
        # The book and final output remain live at this read.
        assert book is not None
        assert final_output is not None or stopped or not events
    finally:
        tracemalloc.stop()
    result: dict[str, object] = {
        "current_traced_bytes": current,
        "peak_traced_bytes": peak,
        "events_processed": processed,
        "allocation_checkpoints": [
            item
            for item in checkpoint_specs
            if item["current_traced_bytes"] is not None
        ],
        "checkpoint_bookkeeping_note": (
            "checkpoint containers are allocated before tracing; retained integer readings "
            "add negligible traced bookkeeping"
        ),
        "input_included": False,
        "book_included": True,
        "final_output_included": True,
        "prior_outputs_retained": False,
        "tracing_scope": "fresh_per_version",
        "allocator_scope": "Python allocations traced by tracemalloc; native allocations excluded",
        "stopped": stopped,
    }
    if stop_reason is not None:
        result["stop_reason"] = stop_reason
    return result


def environment_metadata() -> dict[str, object]:
    def git(*args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    dirty_lines = git("status", "--porcelain", "--", ".").splitlines()
    clock = get_clock_info("perf_counter")
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "git_commit": git("rev-parse", "HEAD"),
        "git_dirty": bool(dirty_lines),
        "git_dirty_paths": dirty_lines,
        "perf_counter_resolution_seconds": clock.resolution,
        "perf_counter_monotonic": clock.monotonic,
        "timer": "time.perf_counter",
        "latency_timer": "time.perf_counter_ns",
        "memory_tool": "tracemalloc",
        "third_party_dependencies": [],
    }


def _require(record: Mapping[str, object], fields: Sequence[str]) -> None:
    missing = [field for field in fields if field not in record]
    if missing:
        raise ValueError(f"record missing required fields: {missing}")


def validate_report(report: Mapping[str, object]) -> None:
    """Reject incomplete, non-finite, or silently stopped measurement data."""

    _require(
        report,
        ("schema_version", "run_label", "environment", "settings", "datasets", "records"),
    )
    records = report["records"]
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("every record must be an object")
        _require(record, ("measurement_kind", "phase", "version", "stopped"))
        if record["measurement_kind"] == "timing":
            _require(record, ("repeat", "elapsed_seconds"))
            elapsed = record["elapsed_seconds"]
            if not isinstance(elapsed, (int, float)) or not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError("timing elapsed_seconds must be finite and nonnegative")
        if record["stopped"]:
            _require(record, ("stop_reason",))
        if record["measurement_kind"] == "memory":
            _require(record, ("current_traced_bytes", "peak_traced_bytes"))
        if record["measurement_kind"] == "latency" and not record["stopped"]:
            _require(record, ("samples_ns", "p50_ns", "p95_ns", "p99_ns"))


def write_report(path: Path, report: Mapping[str, object]) -> None:
    validate_report(report)
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if path.suffix == ".gz":
        with path.open("wb") as raw:
            with gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as stream:
                stream.write(serialized)
    else:
        path.write_bytes(serialized)


def load_report(path: Path) -> dict[str, object]:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            report = json.load(stream)
    else:
        report = json.loads(path.read_text(encoding="utf-8"))
    validate_report(report)
    return report
