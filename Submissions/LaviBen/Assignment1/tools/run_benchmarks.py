#!/usr/bin/env python3
"""Run reproducible timing, latency, diagnostics, and memory experiments."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import gc
from pathlib import Path
import statistics
import sys
from time import perf_counter
import tracemalloc
from typing import Any, Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from measurement.datasets import (  # noqa: E402
    liquidation_request,
    load_dataset,
    read_events,
)
from measurement.metrics import (  # noqa: E402
    MeasurementTimeout,
    environment_metadata,
    latency_replay,
    replay_diagnostics,
    time_limit,
    timed_replay,
    traced_memory_replay,
    validate_report,
    write_report,
)
from orderbook.baseline import BaselineOrderBook  # noqa: E402
from orderbook.revised import RevisedOrderBook  # noqa: E402


IMPLEMENTATIONS = {
    "baseline": BaselineOrderBook,
    "revised": RevisedOrderBook,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "canonical"), default="smoke")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=PROJECT_ROOT / "generated" / "benchmark",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "benchmark_smoke.json.gz",
    )
    parser.add_argument("--versions", nargs="+", choices=tuple(IMPLEMENTATIONS))
    parser.add_argument("--repeats", type=int)
    parser.add_argument("--parse-repeats", type=int)
    parser.add_argument("--warmup-events", type=int)
    parser.add_argument("--diagnostic-events", type=int, default=1_000)
    parser.add_argument("--latency-events", type=int)
    parser.add_argument("--time-limit-seconds", type=float, default=120.0)
    parser.add_argument("--skip-memory", action="store_true")
    return parser.parse_args()


def common_fields(metadata: Mapping[str, object]) -> dict[str, object]:
    return {
        "dataset_id": metadata["dataset_id"],
        "experiment": metadata["experiment"],
        "scenario": metadata["scenario"],
        "seed": metadata["seed"],
        "event_count": metadata["event_count"],
        "levels": metadata["levels"],
        "event_sha256": metadata["event_sha256"],
    }


def append_timing_summary(
    records: list[dict[str, object]],
    raw_records: Sequence[Mapping[str, object]],
    base: Mapping[str, object],
    phase: str,
    version: str,
) -> None:
    completed = [
        float(record["elapsed_seconds"])
        for record in raw_records
        if not record["stopped"]
    ]
    stopped_count = len(raw_records) - len(completed)
    if completed:
        median_elapsed = statistics.median(completed)
        completed_throughputs = [
            float(record["throughput_events_per_second"])
            for record in raw_records
            if not record["stopped"] and "throughput_events_per_second" in record
        ]
        summary: dict[str, object] = {
            **base,
            "measurement_kind": "timing_summary",
            "phase": phase,
            "version": version,
            "repeat": None,
            "elapsed_seconds_median": median_elapsed,
            "time_unit": "seconds",
            "completed_repeat_count": len(completed),
            "stopped_repeat_count": stopped_count,
            "stopped": False,
        }
        if completed_throughputs:
            summary["throughput_events_per_second_median"] = statistics.median(
                completed_throughputs
            )
        records.append(
            summary
        )
    else:
        records.append(
            {
                **base,
                "measurement_kind": "timing_summary",
                "phase": phase,
                "version": version,
                "repeat": None,
                "completed_repeat_count": 0,
                "stopped_repeat_count": stopped_count,
                "stopped": True,
                "stop_reason": "all raw repeats stopped at the declared limit",
                "time_unit": "seconds",
            }
        )


def compare_versions(
    events: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    books = {name: cls() for name, cls in IMPLEMENTATIONS.items()}
    for index, event in enumerate(events, 1):
        before = deepcopy(event)
        results = {name: book.ProcessEvent(event) for name, book in books.items()}
        if event != before:
            raise AssertionError(f"input mutation at diagnostic event {index}")
        if results["baseline"] != results["revised"]:
            raise AssertionError(f"result disagreement at diagnostic event {index}")
    states = {name: book.InspectBook() for name, book in books.items()}
    if states["baseline"] != states["revised"]:
        raise AssertionError("final diagnostic books disagree")
    return {
        "events_compared": len(events),
        "ordered_results_equal": True,
        "final_books_equal": True,
        "input_unchanged": True,
    }


def warm_up(book_class: type[Any], events: Sequence[Mapping[str, object]]) -> None:
    book = book_class()
    for event in events:
        book.ProcessEvent(event)


def parse_measurements(
    path: Path,
    metadata: Mapping[str, object],
    repeats: int,
) -> list[dict[str, object]]:
    base = common_fields(metadata)
    records: list[dict[str, object]] = []
    raw: list[dict[str, object]] = []
    for repeat in range(repeats):
        started = perf_counter()
        parsed = read_events(path)
        elapsed = perf_counter() - started
        if len(parsed) != metadata["event_count"]:
            raise AssertionError("parse repeat changed event count")
        record = {
            **base,
            "measurement_kind": "timing",
            "phase": "input_read_parse",
            "version": "shared",
            "repeat": repeat,
            "elapsed_seconds": elapsed,
            "time_unit": "seconds",
            "events_processed": len(parsed),
            "throughput_events_per_second": len(parsed) / elapsed,
            "stopped": False,
        }
        raw.append(record)
        records.append(record)
    append_timing_summary(records, raw, base, "input_read_parse", "shared")
    return records


def append_application_totals(records: list[dict[str, object]]) -> None:
    """Add raw and median parsing-plus-engine totals from paired repeats."""

    parse_by_repeat = {
        (record["dataset_id"], record["repeat"]): record
        for record in records
        if record["measurement_kind"] == "timing"
        and record["phase"] == "input_read_parse"
    }
    sources = [
        record
        for record in records
        if record["measurement_kind"] == "timing"
        and record["phase"] in {"engine_replay", "build_plus_sale"}
    ]
    totals: list[dict[str, object]] = []
    for source in sources:
        parse_record = parse_by_repeat.get((source["dataset_id"], source["repeat"]))
        if parse_record is None:
            continue
        total_elapsed = float(parse_record["elapsed_seconds"]) + float(
            source["elapsed_seconds"]
        )
        total: dict[str, object] = {
            key: source[key]
            for key in (
                "dataset_id",
                "experiment",
                "scenario",
                "seed",
                "event_count",
                "levels",
                "event_sha256",
                "version",
                "repeat",
            )
        }
        for optional in ("liquidation_percent", "requested_qty_units"):
            if optional in source:
                total[optional] = source[optional]
        total.update(
            {
                "measurement_kind": "timing",
                "phase": "application_total",
                "elapsed_seconds": total_elapsed,
                "time_unit": "seconds",
                "input_read_parse_seconds": parse_record["elapsed_seconds"],
                "engine_seconds": source["elapsed_seconds"],
                "events_processed": source.get("events_processed"),
                "stopped": source["stopped"],
            }
        )
        if source["stopped"]:
            total["stop_reason"] = source["stop_reason"]
        elif source.get("events_processed") and total_elapsed > 0:
            total["throughput_events_per_second"] = (
                int(source["events_processed"]) / total_elapsed
            )
        totals.append(total)
    records.extend(totals)

    grouped: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for total in totals:
        key = (
            total["dataset_id"],
            total["version"],
            total.get("liquidation_percent"),
        )
        grouped.setdefault(key, []).append(total)
    for values in grouped.values():
        first = values[0]
        base = {
            key: first[key]
            for key in (
                "dataset_id",
                "experiment",
                "scenario",
                "seed",
                "event_count",
                "levels",
                "event_sha256",
            )
        }
        for optional in ("liquidation_percent", "requested_qty_units"):
            if optional in first:
                base[optional] = first[optional]
        append_timing_summary(
            records,
            values,
            base,
            "application_total",
            str(first["version"]),
        )


def stream_measurements(
    events: Sequence[Mapping[str, object]],
    metadata: Mapping[str, object],
    versions: Sequence[str],
    repeats: int,
    warmup_events: int,
    diagnostic_events: int,
    latency_events: int | None,
    time_limit_seconds: float | None,
    include_memory: bool,
) -> list[dict[str, object]]:
    base = common_fields(metadata)
    records: list[dict[str, object]] = []
    diagnostic_input = events[: min(len(events), diagnostic_events)]
    correctness = compare_versions(diagnostic_input)
    records.append(
        {
            **base,
            "measurement_kind": "correctness",
            "phase": "diagnostic_prefix",
            "version": "shared",
            **correctness,
            "stopped": False,
        }
    )

    # One full diagnostics run uses the revised representation for O(1) active
    # and level counts in later implementations; it is outside primary timing.
    diagnostics = replay_diagnostics(RevisedOrderBook, events)
    records.append(
        {
            **base,
            "measurement_kind": "operation_counts",
            "phase": "full_replay_instrumented",
            "version": "revised",
            **diagnostics,
            "stopped": False,
        }
    )

    for version in versions:
        book_class = IMPLEMENTATIONS[version]
        warm_up(book_class, events[: min(len(events), warmup_events)])
        raw: list[dict[str, object]] = []
        for repeat in range(repeats):
            outcome = timed_replay(book_class, events, time_limit_seconds)
            elapsed = float(outcome["elapsed_seconds"])
            record = {
                **base,
                "measurement_kind": "timing",
                "phase": "engine_replay",
                "version": version,
                "repeat": repeat,
                "time_unit": "seconds",
                **outcome,
            }
            if not record["stopped"] and elapsed > 0:
                record["throughput_events_per_second"] = len(events) / elapsed
            raw.append(record)
            records.append(record)
        append_timing_summary(records, raw, base, "engine_replay", version)

        latency_input = events if latency_events is None else events[:latency_events]
        latency = latency_replay(book_class, latency_input, time_limit_seconds)
        records.append(
            {
                **base,
                "measurement_kind": "latency",
                "phase": "per_event_instrumented",
                "version": version,
                "percentile_convention": "nearest-rank: ceil(p/100*n), minimum rank 1",
                "latency_unit": "nanoseconds",
                **latency,
            }
        )

        if include_memory:
            memory = traced_memory_replay(book_class, events, time_limit_seconds)
            records.append(
                {
                    **base,
                    "measurement_kind": "memory",
                    "phase": "engine_replay",
                    "version": version,
                    "memory_unit": "traced_bytes",
                    **memory,
                }
            )
    return records


def traced_liquidation(
    book_class: type[Any],
    setup_events: Sequence[Mapping[str, object]],
    sale_event: Mapping[str, object],
    time_limit_seconds: float | None,
) -> dict[str, object]:
    if tracemalloc.is_tracing():
        raise RuntimeError("tracemalloc must not already be running")
    gc.collect()
    processed = 0
    stopped = False
    stop_reason: str | None = None
    tracemalloc.start()
    try:
        book = book_class()
        final_output: dict[str, object] | None = None
        try:
            with time_limit(time_limit_seconds):
                for event in setup_events:
                    book.ProcessEvent(event)
                    processed += 1
                final_output = book.ProcessEvent(sale_event)
                processed += 1
        except MeasurementTimeout as error:
            stopped = True
            stop_reason = str(error)
        current, peak = tracemalloc.get_traced_memory()
        assert book is not None
        assert final_output is not None or stopped
    finally:
        tracemalloc.stop()
    result: dict[str, object] = {
        "current_traced_bytes": current,
        "peak_traced_bytes": peak,
        "events_processed": processed,
        "input_included": False,
        "book_included": True,
        "final_output_included": True,
        "prior_outputs_retained": False,
        "tracing_scope": "fresh_per_version_and_sale_size",
        "allocator_scope": "Python allocations traced by tracemalloc; native allocations excluded",
        "stopped": stopped,
    }
    if stop_reason is not None:
        result["stop_reason"] = stop_reason
    return result


def liquidation_measurements(
    setup_events: Sequence[Mapping[str, object]],
    metadata: Mapping[str, object],
    versions: Sequence[str],
    repeats: int,
    warmup_events: int,
    time_limit_seconds: float | None,
    include_memory: bool,
) -> list[dict[str, object]]:
    base = common_fields(metadata)
    records: list[dict[str, object]] = []
    total_bid_qty = sum(int(event["qty_units"]) for event in setup_events)

    build_diagnostics = replay_diagnostics(RevisedOrderBook, setup_events)
    records.append(
        {
            **base,
            "measurement_kind": "operation_counts",
            "phase": "liquidation_book_build_instrumented",
            "version": "revised",
            **build_diagnostics,
            "stopped": False,
        }
    )

    for percent in (10, 100, 200):
        requested = liquidation_request(total_bid_qty, percent)
        sale_event = {
            "seq": len(setup_events) + 1,
            "event_id": f"liquidation-{percent}",
            "type": "MARKET_SELL",
            "order_id": f"liquidation-{percent}",
            "qty_units": requested,
        }
        books = {name: cls() for name, cls in IMPLEMENTATIONS.items()}
        for book in books.values():
            for event in setup_events:
                book.ProcessEvent(event)
        results = {name: book.ProcessEvent(sale_event) for name, book in books.items()}
        states = {name: book.InspectBook() for name, book in books.items()}
        if results["baseline"] != results["revised"] or states["baseline"] != states["revised"]:
            raise AssertionError(f"liquidation versions disagree at {percent}%")
        fills = results["revised"]["fills"]
        records.append(
            {
                **base,
                "measurement_kind": "correctness",
                "phase": "individual_sale",
                "version": "shared",
                "liquidation_percent": percent,
                "requested_qty_units": requested,
                "ordered_results_equal": True,
                "final_books_equal": True,
                "fill_count": len(fills),
                "maker_price_levels_visited": len({fill["price_ticks"] for fill in fills}),
                "unfilled_qty_units": results["revised"]["unfilled_qty_units"],
                "stopped": False,
            }
        )

    for version in versions:
        book_class = IMPLEMENTATIONS[version]
        warm_up(book_class, setup_events[: min(len(setup_events), warmup_events)])
        for percent in (10, 100, 200):
            requested = liquidation_request(total_bid_qty, percent)
            sale_event = {
                "seq": len(setup_events) + 1,
                "event_id": f"liquidation-{percent}",
                "type": "MARKET_SELL",
                "order_id": f"liquidation-{percent}",
                "qty_units": requested,
            }
            phase_raw: dict[str, list[dict[str, object]]] = {
                "book_build": [],
                "individual_sale": [],
                "build_plus_sale": [],
            }
            for repeat in range(repeats):
                build_started = perf_counter()
                build_stopped = False
                try:
                    with time_limit(time_limit_seconds):
                        book = book_class()
                        for event in setup_events:
                            book.ProcessEvent(event)
                except MeasurementTimeout as error:
                    build_elapsed = perf_counter() - build_started
                    build_stopped = True
                    stop_reason = str(error)
                else:
                    build_elapsed = perf_counter() - build_started

                build_record: dict[str, object] = {
                    **base,
                    "measurement_kind": "timing",
                    "phase": "book_build",
                    "version": version,
                    "repeat": repeat,
                    "liquidation_percent": percent,
                    "requested_qty_units": requested,
                    "elapsed_seconds": build_elapsed,
                    "time_unit": "seconds",
                    "events_processed": len(setup_events) if not build_stopped else None,
                    "stopped": build_stopped,
                }
                if build_stopped:
                    build_record["stop_reason"] = stop_reason
                else:
                    build_record["throughput_events_per_second"] = len(setup_events) / build_elapsed
                records.append(build_record)
                phase_raw["book_build"].append(build_record)

                if build_stopped:
                    for phase in ("individual_sale", "build_plus_sale"):
                        stopped_record = {
                            **base,
                            "measurement_kind": "timing",
                            "phase": phase,
                            "version": version,
                            "repeat": repeat,
                            "liquidation_percent": percent,
                            "requested_qty_units": requested,
                            "elapsed_seconds": build_elapsed,
                            "time_unit": "seconds",
                            "events_processed": None,
                            "stopped": True,
                            "stop_reason": "book build stopped; sale not attempted",
                        }
                        records.append(stopped_record)
                        phase_raw[phase].append(stopped_record)
                    continue

                sale_started = perf_counter()
                try:
                    with time_limit(time_limit_seconds):
                        sale_result = book.ProcessEvent(sale_event)
                except MeasurementTimeout as error:
                    sale_elapsed = perf_counter() - sale_started
                    sale_stopped = True
                    sale_stop_reason = str(error)
                    fill_count = None
                    levels_visited = None
                    unfilled = None
                else:
                    sale_elapsed = perf_counter() - sale_started
                    sale_stopped = False
                    fills = sale_result["fills"]
                    fill_count = len(fills)
                    levels_visited = len({fill["price_ticks"] for fill in fills})
                    unfilled = sale_result["unfilled_qty_units"]

                sale_record: dict[str, object] = {
                    **base,
                    "measurement_kind": "timing",
                    "phase": "individual_sale",
                    "version": version,
                    "repeat": repeat,
                    "liquidation_percent": percent,
                    "requested_qty_units": requested,
                    "elapsed_seconds": sale_elapsed,
                    "time_unit": "seconds",
                    "fill_count": fill_count,
                    "maker_price_levels_visited": levels_visited,
                    "unfilled_qty_units": unfilled,
                    "events_processed": 0 if sale_stopped else 1,
                    "stopped": sale_stopped,
                }
                if sale_stopped:
                    sale_record["stop_reason"] = sale_stop_reason
                records.append(sale_record)
                phase_raw["individual_sale"].append(sale_record)

                combined_record = {
                    **base,
                    "measurement_kind": "timing",
                    "phase": "build_plus_sale",
                    "version": version,
                    "repeat": repeat,
                    "liquidation_percent": percent,
                    "requested_qty_units": requested,
                    "elapsed_seconds": build_elapsed + sale_elapsed,
                    "time_unit": "seconds",
                    "events_processed": len(setup_events) + (0 if sale_stopped else 1),
                    "stopped": sale_stopped,
                }
                if sale_stopped:
                    combined_record["stop_reason"] = sale_stop_reason
                records.append(combined_record)
                phase_raw["build_plus_sale"].append(combined_record)

            phase_base = {
                **base,
                "liquidation_percent": percent,
                "requested_qty_units": requested,
            }
            for phase, raw in phase_raw.items():
                append_timing_summary(records, raw, phase_base, phase, version)

            if include_memory:
                memory = traced_liquidation(
                    book_class,
                    setup_events,
                    sale_event,
                    time_limit_seconds,
                )
                records.append(
                    {
                        **phase_base,
                        "measurement_kind": "memory",
                        "phase": "build_plus_sale",
                        "version": version,
                        "memory_unit": "traced_bytes",
                        **memory,
                    }
                )
    return records


def main() -> int:
    args = parse_args()
    versions = args.versions or list(IMPLEMENTATIONS)
    repeats = args.repeats if args.repeats is not None else (2 if args.profile == "smoke" else 5)
    parse_repeats = (
        args.parse_repeats
        if args.parse_repeats is not None
        else (2 if args.profile == "smoke" else 5)
    )
    warmup_events = (
        args.warmup_events
        if args.warmup_events is not None
        else (100 if args.profile == "smoke" else 1_000)
    )
    latency_events = args.latency_events
    if latency_events is None and args.profile == "smoke":
        latency_events = 1_000
    for name, value in (
        ("repeats", repeats),
        ("parse_repeats", parse_repeats),
        ("warmup_events", warmup_events),
        ("diagnostic_events", args.diagnostic_events),
    ):
        if value < 1:
            raise SystemExit(f"{name} must be positive")

    environment = environment_metadata()
    if args.profile == "canonical" and environment["git_dirty"]:
        raise SystemExit(
            "canonical measurement refused: commit the measurement code and run "
            "from a clean Assignment1 tree first"
        )

    paths = sorted(args.data_dir.glob("*.jsonl.gz"))
    if not paths:
        raise SystemExit(
            f"no prepared datasets found in {args.data_dir}; run "
            "tools/prepare_benchmarks.py first"
        )

    datasets: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    for path in paths:
        events, metadata = load_dataset(path)
        datasets.append(metadata)
        records.extend(parse_measurements(path, metadata, parse_repeats))
        if metadata["experiment"] == "liquidation":
            records.extend(
                liquidation_measurements(
                    events,
                    metadata,
                    versions,
                    repeats,
                    warmup_events,
                    args.time_limit_seconds,
                    not args.skip_memory,
                )
            )
        else:
            records.extend(
                stream_measurements(
                    events,
                    metadata,
                    versions,
                    repeats,
                    warmup_events,
                    args.diagnostic_events,
                    latency_events,
                    args.time_limit_seconds,
                    not args.skip_memory,
                )
            )
        print(f"measured {metadata['dataset_id']}")

    append_application_totals(records)

    report: dict[str, object] = {
        "schema_version": 1,
        "run_label": "provisional_smoke" if args.profile == "smoke" else "canonical",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "settings": {
            "profile": args.profile,
            "versions": versions,
            "repeats": repeats,
            "parse_repeats": parse_repeats,
            "warmup_events": warmup_events,
            "diagnostic_events": args.diagnostic_events,
            "latency_events": latency_events,
            "time_limit_seconds_per_phase": args.time_limit_seconds,
            "memory_enabled": not args.skip_memory,
            "same_prepared_event_tuple_for_versions": True,
            "fresh_book_per_replay_and_liquidation_size": True,
            "primary_timing_excludes_input_read_parse": True,
            "latency_instrumentation_separate_from_primary_timing": True,
            "operation_counts_separate_from_primary_timing": True,
            "memory_tracing_separate_from_primary_timing": True,
            "command": [sys.executable, *sys.argv],
        },
        "datasets": datasets,
        "records": records,
    }
    validate_report(report)
    write_report(args.output, report)
    print(f"run_label={report['run_label']}")
    print(f"datasets={len(datasets)}")
    print(f"records={len(records)}")
    print(f"output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
