"""Run reproducible order-book timing and diagnostic experiments."""

import argparse
import cProfile
import ctypes
import hashlib
import json
import math
import multiprocessing
import os
import platform
import pstats
import random
import statistics
import subprocess
import sys
import time
import traceback
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.metrics import (  # noqa: E402
    book_state_counts,
    ceil_percent,
    counter_replay,
    load_events,
    percentile_nearest_rank,
    phase_row,
    replay_without_history,
    stopped_phase_row,
    summarize_seconds,
    validate_event_stream,
)


SCENARIOS = ("buildup", "crowded", "mixed", "sweep", "cancel_churn")
VERSIONS = ("baseline", "revised")
RUNS_DIR = ROOT / "results" / "benchmarks"
TIMING_REPEATS = 5
MEMORY_POLL_SECONDS = 0.05


def _json_write_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path):
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(Path(path).resolve())


def _write_custom_jsonl(path, events, settings):
    path = Path(path)
    metadata_path = Path(str(path) + ".metadata.json")
    if path.exists() or metadata_path.exists():
        if not path.is_file() or not metadata_path.is_file():
            raise FileExistsError(f"incomplete existing input: {path}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        actual_hash = _sha256_file(path)
        if metadata.get("settings") != settings:
            raise ValueError(f"existing input settings differ: {path}")
        if metadata.get("sha256") != actual_hash:
            raise ValueError(f"existing input checksum differs: {path}")
        return metadata

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for event in events:
            stream.write(json.dumps(event, separators=(",", ":")))
            stream.write("\n")

    metadata = {
        "generator": "benchmarks.run_benchmarks custom deterministic workload",
        "settings": settings,
        "event_count": len(events),
        "sha256": _sha256_file(path),
    }
    _json_write_exclusive(metadata_path, metadata)
    return metadata


def _generated_events_path(run_dir, scenario, event_count, seed, levels):
    supplied = ROOT / "data" / f"{scenario}_10000.jsonl.gz"
    if event_count == 10000 and seed == 42 and levels == 1000 and supplied.is_file():
        return supplied

    inputs_dir = Path(run_dir) / "inputs"
    output = inputs_dir / (
        f"{scenario}_M{event_count}_seed{seed}_levels{levels}.jsonl.gz"
    )
    metadata_path = Path(str(output) + ".metadata.json")
    expected = {
        "scenario": scenario,
        "events": event_count,
        "seed": seed,
        "levels": levels,
    }
    if output.exists() or metadata_path.exists():
        if not output.is_file() or not metadata_path.is_file():
            raise FileExistsError(f"incomplete generated input: {output}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if any(metadata.get(key) != value for key, value in expected.items()):
            raise ValueError(f"existing generated input settings differ: {output}")
        if metadata.get("sha256") != _sha256_file(output):
            raise ValueError(f"existing generated input checksum differs: {output}")
        return output

    command = [
        sys.executable,
        str(ROOT / "generate_orders.py"),
        "--scenario",
        scenario,
        "--events",
        str(event_count),
        "--levels",
        str(levels),
        "--seed",
        str(seed),
        "--out",
        str(output),
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(completed.stdout.strip().splitlines()[-1])
    if any(metadata.get(key) != value for key, value in expected.items()):
        raise ValueError(f"generator returned unexpected settings for {output}")
    return output


def _make_fixed_book_events(order_count, seed):
    rng = random.Random(seed)
    price_levels = min(100, order_count)
    events = []
    for index in range(order_count):
        seq = index + 1
        order_id = f"fixed-bid-{index:08d}"
        events.append(
            {
                "seq": seq,
                "event_id": f"fixed-event-{seq:08d}",
                "type": "LIMIT",
                "order_id": order_id,
                "side": "BUY",
                "price_ticks": 6000000 - (index % price_levels),
                "qty_units": rng.randint(1, 7) * 1000000,
            }
        )
    return events


def _make_queue_events(order_count, price_count, seed):
    rng = random.Random(seed)
    events = []
    for index in range(order_count):
        seq = index + 1
        events.append(
            {
                "seq": seq,
                "event_id": f"queue-event-{seq:08d}",
                "type": "LIMIT",
                "order_id": f"queue-order-{index:08d}",
                "side": "BUY",
                "price_ticks": 5500000 + ((index + seed) % price_count),
                "qty_units": rng.randint(1, 9) * 100000,
            }
        )
    return events


def _make_anchored_churn_events(cycles):
    events = [
        {
            "seq": 1,
            "event_id": "anchor-event",
            "type": "LIMIT",
            "order_id": "anchor-bid",
            "side": "BUY",
            "price_ticks": 6000000,
            "qty_units": 1000000,
        }
    ]
    for index in range(cycles):
        add_seq = 2 + index * 2
        order_id = f"churn-order-{index:08d}"
        events.append(
            {
                "seq": add_seq,
                "event_id": f"churn-add-{index:08d}",
                "type": "LIMIT",
                "order_id": order_id,
                "side": "BUY",
                "price_ticks": 1000000 + index,
                "qty_units": 1000000,
            }
        )
        events.append(
            {
                "seq": add_seq + 1,
                "event_id": f"churn-cancel-{index:08d}",
                "type": "CANCEL",
                "target_order_id": order_id,
            }
        )
    return events


def _custom_case(run_dir, case_id, experiment, scenario, seed, events, settings):
    input_path = Path(run_dir) / "inputs" / f"{case_id}.jsonl"
    _write_custom_jsonl(input_path, events, settings)
    validate_event_stream(events, expected_count=len(events))
    return {
        "case_id": case_id,
        "experiment": experiment,
        "scenario": scenario,
        "seed": seed,
        "event_count": len(events),
        "input_path": str(input_path.resolve()),
        "input_paths": [str(input_path.resolve())],
        "input_checksums": {input_path.name: _sha256_file(input_path)},
        "generator_settings": settings,
    }


def build_cases(settings, run_dir):
    cases = []
    for scenario in settings["scenarios"]:
        for event_count in settings["event_sizes"]:
            for seed in settings["seeds"]:
                input_path = _generated_events_path(
                    run_dir,
                    scenario,
                    event_count,
                    seed,
                    settings["levels"],
                )
                events = load_events(input_path)
                validate_event_stream(events, expected_count=event_count)
                sidecar = Path(str(input_path) + ".metadata.json")
                sidecar_data = json.loads(sidecar.read_text(encoding="utf-8"))
                expected_settings = {
                    "scenario": scenario,
                    "events": event_count,
                    "seed": seed,
                    "levels": settings["levels"],
                }
                if any(
                    sidecar_data.get(key) != value
                    for key, value in expected_settings.items()
                ):
                    raise ValueError(f"input metadata mismatch: {input_path}")
                if sidecar_data.get("sha256") != _sha256_file(input_path):
                    raise ValueError(f"input checksum mismatch: {input_path}")
                cases.append(
                    {
                        "case_id": (
                            f"workload_{scenario}_M{event_count}_seed{seed}"
                        ),
                        "experiment": "workload_replay",
                        "scenario": scenario,
                        "seed": seed,
                        "event_count": event_count,
                        "input_path": str(input_path.resolve()),
                        "input_paths": [str(input_path.resolve())],
                        "input_checksums": {
                            input_path.name: _sha256_file(input_path)
                        },
                        "generator_settings": {
                            "generator": "generate_orders.py",
                            "scenario": scenario,
                            "events": event_count,
                            "seed": seed,
                            "levels": settings["levels"],
                            "source": (
                                "supplied" if input_path.parent == ROOT / "data"
                                else "generated"
                            ),
                        },
                        "profile": (
                            scenario == "mixed"
                            and event_count == min(settings["event_sizes"])
                            and seed == settings["seeds"][0]
                        ),
                    }
                )

    fixed_events = _make_fixed_book_events(
        settings["fixed_book_orders"], settings["seeds"][0]
    )
    fixed_total = sum(event["qty_units"] for event in fixed_events)
    fixed_input = _custom_case(
        run_dir,
        f"fixed_bid_book_M{len(fixed_events)}_seed{settings['seeds'][0]}",
        "fixed_liquidation",
        "fixed_bid_book",
        settings["seeds"][0],
        fixed_events,
        {
            "generator": "fixed bid-book builder",
            "orders": len(fixed_events),
            "seed": settings["seeds"][0],
            "price_levels": min(100, len(fixed_events)),
            "quantity_rule": "seeded integer multiples of 1,000,000 units",
        },
    )
    fixed_input.update(
        {
            "event_count": len(fixed_events) + 1,
            "initial_book_event_count": len(fixed_events),
            "available_bid_qty_units": fixed_total,
            "sell_quantities": [
                {"percent": percent, "qty_units": ceil_percent(fixed_total, percent)}
                for percent in (10, 100, 200)
            ],
        }
    )
    cases.append(fixed_input)

    for price_count in (4, 1000):
        queue_events = _make_queue_events(
            settings["queue_orders"], price_count, settings["seeds"][0]
        )
        queue_case = _custom_case(
            run_dir,
            f"queue_concentration_prices{price_count}_M{len(queue_events)}",
            "queue_concentration",
            f"queue_{price_count}_prices",
            settings["seeds"][0],
            queue_events,
            {
                "generator": "queue concentration builder",
                "orders": len(queue_events),
                "available_prices": price_count,
                "seed": settings["seeds"][0],
                "quantity_rule": (
                    "same seeded quantity sequence across price concentrations"
                ),
            },
        )
        queue_case["available_price_count"] = price_count
        cases.append(queue_case)

    churn_events = _make_anchored_churn_events(settings["churn_cycles"])
    churn_case = _custom_case(
        run_dir,
        f"churn_with_anchor_cycles{settings['churn_cycles']}",
        "cancellation_churn",
        "churn_with_anchor",
        settings["seeds"][0],
        churn_events,
        {
            "generator": "anchored cancellation churn builder",
            "cycles": settings["churn_cycles"],
            "events": len(churn_events),
            "anchor_order_remains_active": True,
            "transient_prices": "unique prices below the anchor",
        },
    )
    cases.append(churn_case)
    return cases


def _case_manifest(case):
    result = {}
    for name in (
        "case_id",
        "experiment",
        "scenario",
        "seed",
        "event_count",
        "input_checksums",
        "generator_settings",
        "initial_book_event_count",
        "available_bid_qty_units",
        "sell_quantities",
        "available_price_count",
        "profile",
    ):
        if name in case:
            result[name] = case[name]
    result["input_paths"] = [_relative_path(path) for path in case["input_paths"]]
    return result


def _get_engine_class(version):
    if version == "baseline":
        from orderbook.baseline import OrderBook
    elif version == "revised":
        from orderbook.revised import OrderBook
    else:
        raise ValueError(f"unknown engine version: {version}")
    return OrderBook


def _validate_pair(events, event_limit):
    compared_events = events[:event_limit]
    baseline = _get_engine_class("baseline")()
    revised = _get_engine_class("revised")()
    for position, event in enumerate(compared_events, start=1):
        baseline_result = baseline.process_event(event)
        revised_result = revised.process_event(event)
        if revised_result != baseline_result:
            raise AssertionError(
                f"result parity failed at event {position}: {event!r}"
            )
        if revised.last_accepted_seq != baseline.last_accepted_seq:
            raise AssertionError(
                f"accepted-sequence parity failed at event {position}"
            )
        if revised.inspect_book() != baseline.inspect_book():
            raise AssertionError(f"book parity failed at event {position}")
    return len(compared_events)


def validate_case(case, event_limit):
    events = load_events(case["input_path"])
    validate_event_stream(events, expected_count=case["event_count"]
                          if case["experiment"] != "fixed_liquidation"
                          else case["initial_book_event_count"])
    if case["experiment"] != "fixed_liquidation":
        return {
            "status": "passed",
            "events_compared": _validate_pair(events, event_limit),
            "sale_cases_compared": 0,
        }

    initial_events = events[:event_limit]
    events_compared = _validate_pair(initial_events, event_limit)
    available_qty = sum(event["qty_units"] for event in initial_events)
    sale_cases_compared = 0
    for percent in (10, 100, 200):
        qty_units = ceil_percent(available_qty, percent)
        sale_event = {
            "seq": len(initial_events) + 1,
            "event_id": f"parity-sale-{percent}",
            "type": "MARKET_SELL",
            "order_id": f"parity-taker-{percent}",
            "qty_units": qty_units,
        }
        event_stream = initial_events + [sale_event]
        if _validate_pair(event_stream, len(event_stream)) != len(event_stream):
            raise AssertionError("fixed-book sale parity length mismatch")
        sale_cases_compared += 1
    return {
        "status": "passed",
        "events_compared": events_compared,
        "sale_cases_compared": sale_cases_compared,
    }


def _environment_snapshot():
    requirement_path = ROOT / "requirements.txt"
    dependencies = [
        line.strip()
        for line in requirement_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        git_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(ROOT),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        git_dirty = bool(git_status.strip())
    except (OSError, subprocess.CalledProcessError) as error:
        head = None
        branch = None
        git_dirty = None
        git_error = str(error)
    else:
        git_error = None
    return {
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "dependencies": dependencies,
        "machine": platform.machine(),
        "processor": platform.processor(),
        "platform": platform.platform(),
        "os": os.name,
        "git_head": head,
        "git_branch": branch,
        "git_dirty": git_dirty,
        "git_error": git_error,
    }


def _code_hashes():
    paths = {
        "baseline.py": ROOT / "orderbook" / "baseline.py",
        "revised.py": ROOT / "orderbook" / "revised.py",
        "generate_orders.py": ROOT / "generate_orders.py",
        "run_benchmarks.py": Path(__file__),
        "metrics.py": Path(__file__).with_name("metrics.py"),
        "test_specification.py": ROOT / "tests" / "test_specification.py",
        "test_generated_streams.py": ROOT / "tests" / "test_generated_streams.py",
        "test_benchmark_tools.py": ROOT / "tests" / "test_benchmark_tools.py",
    }
    return {
        name: _sha256_file(path)
        for name, path in paths.items()
        if path.is_file()
    }


def _sale_event(case, percent, qty_units):
    seq = case["initial_book_event_count"] + 1
    return {
        "seq": seq,
        "event_id": f"liquidation-event-{percent}",
        "type": "MARKET_SELL",
        "order_id": f"liquidation-taker-{percent}",
        "qty_units": qty_units,
    }


def _emit(connection, row):
    connection.send({"kind": "row", "row": row})


def _timing_phase(connection, phase, repeats, warmup, measure, event_count):
    warmup()
    values = []
    for repeat in range(1, repeats + 1):
        elapsed, details = measure()
        values.append(elapsed)
        row = phase_row(phase, repeat=repeat, elapsed_seconds=elapsed)
        row.update(details)
        if event_count is not None and phase in (
            "engine_replay",
            "total_application",
        ):
            row["throughput_events_per_second"] = (
                event_count / elapsed if elapsed > 0 else None
            )
        _emit(connection, row)

    summary = summarize_seconds(values, event_count or 0)
    row = phase_row(
        f"{phase}_summary",
        status="completed",
        elapsed_seconds=summary["median_seconds"],
    )
    row["raw_repeats_seconds"] = values
    row["median_seconds"] = summary["median_seconds"]
    row["throughput_events_per_second"] = summary[
        "throughput_events_per_second"
    ] if event_count else None
    _emit(connection, row)


def _measure_input_parse(path):
    started = time.perf_counter()
    events = load_events(path)
    elapsed = time.perf_counter() - started
    return elapsed, {"parsed_event_count": len(events)}


def _measure_engine_replay(book_type, events):
    book = book_type()
    started = time.perf_counter()
    replay_without_history(book, events)
    return time.perf_counter() - started, {}


def _measure_total_application(path, book_type):
    started = time.perf_counter()
    events = load_events(path)
    book = book_type()
    replay_without_history(book, events)
    return time.perf_counter() - started, {"parsed_event_count": len(events)}


def _build_book(book_type, events):
    book = book_type()
    replay_without_history(book, events)
    return book


def _measure_initial_book(book_type, initial_events):
    started = time.perf_counter()
    _build_book(book_type, initial_events)
    return time.perf_counter() - started, {}


def _measure_sell_operation(book_type, initial_events, sale_event):
    book = _build_book(book_type, initial_events)
    started = time.perf_counter()
    result = book.process_event(sale_event)
    elapsed = time.perf_counter() - started
    return elapsed, {"returned_fill_count": len(result.get("fills", []))}


def _measure_total_sell(path, book_type, sale_event):
    started = time.perf_counter()
    initial_events = load_events(path)
    book = _build_book(book_type, initial_events)
    result = book.process_event(sale_event)
    elapsed = time.perf_counter() - started
    return elapsed, {
        "parsed_event_count": len(initial_events),
        "returned_fill_count": len(result.get("fills", [])),
    }


def _state_checkpoint(book, event_position, label, last_result):
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    row = phase_row("memory", repeat=1)
    row.update(book_state_counts(book))
    row.update(
        {
            "checkpoint": label,
            "event_position": event_position,
            "traced_current_bytes": current_bytes,
            "traced_peak_bytes": peak_bytes,
            "current_result_retained": last_result is not None,
        }
    )
    return row


def _memory_replay(book_type, events, case):
    if not events:
        raise ValueError("memory replay requires events")
    tracemalloc.start()
    rows = []
    try:
        book = book_type()
        last_result = None
        positions = {
            max(1, math.ceil(len(events) * fraction))
            for fraction in (0.25, 0.5, 0.75, 1.0)
        }
        if case["experiment"] == "fixed_liquidation":
            positions.add(len(events) - 1)
        for position, event in enumerate(events, start=1):
            last_result = book.process_event(event)
            if position in positions:
                label = (
                    "final"
                    if position == len(events)
                    else f"after_event_{position}"
                )
                rows.append(_state_checkpoint(book, position, label, last_result))
    finally:
        tracemalloc.stop()
    return rows


def _counter_event_replay(book_type, events):
    return counter_replay(book_type, events)


def _latency_replay(book_type, events, raw_path):
    replay_without_history(book_type(), events)
    book = book_type()
    raw_latencies = []
    raw_path = Path(raw_path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("x", encoding="utf-8", newline="\n", buffering=1) as stream:
        for position, event in enumerate(events, start=1):
            started = time.perf_counter()
            book.process_event(event)
            elapsed = time.perf_counter() - started
            raw_latencies.append(elapsed)
            stream.write(
                json.dumps(
                    {
                        "event_position": position,
                        "event_seq": event["seq"],
                        "event_type": event["type"],
                        "latency_seconds": elapsed,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
            stream.flush()
    if not raw_latencies:
        raise ValueError("latency replay requires events")
    window_size = max(1, math.ceil(len(raw_latencies) / 10))
    early_window = raw_latencies[:window_size]
    late_window = raw_latencies[-window_size:]
    return {
        "latency_median_seconds": statistics.median(raw_latencies),
        "latency_p95_seconds": percentile_nearest_rank(raw_latencies, 95),
        "latency_p99_seconds": percentile_nearest_rank(raw_latencies, 99),
        "latency_percentile_convention": "nearest rank; median uses statistics.median",
        "latency_raw_count": len(raw_latencies),
        "latency_raw_path": str(raw_path),
        "latency_process_throughput_events_per_second": (
            len(raw_latencies) / sum(raw_latencies)
            if sum(raw_latencies) > 0
            else None
        ),
        "early_window_event_count": len(early_window),
        "early_window_median_seconds": statistics.median(early_window),
        "early_window_p95_seconds": percentile_nearest_rank(early_window, 95),
        "early_window_p99_seconds": percentile_nearest_rank(early_window, 99),
        "early_window_process_throughput_events_per_second": (
            len(early_window) / sum(early_window)
            if sum(early_window) > 0
            else None
        ),
        "late_window_event_count": len(late_window),
        "late_window_median_seconds": statistics.median(late_window),
        "late_window_p95_seconds": percentile_nearest_rank(late_window, 95),
        "late_window_p99_seconds": percentile_nearest_rank(late_window, 99),
        "late_window_process_throughput_events_per_second": (
            len(late_window) / sum(late_window)
            if sum(late_window) > 0
            else None
        ),
    }


def _profile_replay(book_type, events, artifact_dir, max_events):
    profiled_events = events[:max_events]
    book = book_type()
    profiler = cProfile.Profile()
    profiler.enable()
    replay_without_history(book, profiled_events)
    profiler.disable()

    artifact_dir = Path(artifact_dir)
    binary_path = artifact_dir / "profile.prof"
    text_path = artifact_dir / "profile.txt"
    profiler.dump_stats(str(binary_path))
    with text_path.open("x", encoding="utf-8", newline="\n") as stream:
        stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
        stats.print_stats(40)
    return {
        "profiled_event_count": len(profiled_events),
        "profile_data_path": str(binary_path),
        "profile_text_path": str(text_path),
        "profiler": "cProfile",
    }


def _generic_worker(connection, case, version, repeats, artifact_dir,
                    profile_event_limit):
    book_type = _get_engine_class(version)
    events = load_events(case["input_path"])
    event_count = len(events)
    path = case["input_path"]

    def warm_parse():
        load_events(path)

    def warm_empty():
        book_type()

    def warm_replay():
        replay_without_history(book_type(), events)

    _timing_phase(
        connection,
        "input_read_parse",
        repeats,
        warm_parse,
        lambda: _measure_input_parse(path),
        event_count,
    )
    _timing_phase(
        connection,
        "empty_engine_construction",
        repeats,
        warm_empty,
        lambda: _measure_constructor(book_type),
        None,
    )
    _timing_phase(
        connection,
        "engine_replay",
        repeats,
        warm_replay,
        lambda: _measure_engine_replay(book_type, events),
        event_count,
    )

    def warm_total():
        _measure_total_application(path, book_type)

    _timing_phase(
        connection,
        "total_application",
        repeats,
        warm_total,
        lambda: _measure_total_application(path, book_type),
        event_count,
    )

    counter = _counter_event_replay(book_type, events)
    counter_row = phase_row("counters", repeat=1)
    counter_row.update(counter)
    if "available_price_count" in case:
        counter_row["available_price_count"] = case["available_price_count"]
        counter_row["realized_price_count"] = counter["final_state"][
            "occupied_price_levels"
        ]
    _emit(connection, counter_row)

    latency_path = Path(artifact_dir) / "latencies.jsonl"
    latency_summary = _latency_replay(book_type, events, latency_path)
    latency_row = phase_row("latency_summary", repeat=1)
    latency_row.update(latency_summary)
    _emit(connection, latency_row)

    for memory_row in _memory_replay(book_type, events, case):
        _emit(connection, memory_row)

    if case.get("profile"):
        profile_summary = _profile_replay(
            book_type, events, artifact_dir, profile_event_limit
        )
        profile_row = phase_row("profile", repeat=1)
        profile_row.update(profile_summary)
        _emit(connection, profile_row)


def _measure_constructor(book_type):
    started = time.perf_counter()
    book_type()
    return time.perf_counter() - started, {}


def _fixed_worker(connection, case, version, repeats, artifact_dir):
    book_type = _get_engine_class(version)
    initial_events = load_events(case["input_path"])
    event_count = len(initial_events)
    path = case["input_path"]

    def warm_parse():
        load_events(path)

    _timing_phase(
        connection,
        "input_read_parse",
        repeats,
        warm_parse,
        lambda: _measure_input_parse(path),
        event_count,
    )
    _timing_phase(
        connection,
        "empty_engine_construction",
        repeats,
        lambda: book_type(),
        lambda: _measure_constructor(book_type),
        None,
    )
    _timing_phase(
        connection,
        "initial_book_construction",
        repeats,
        lambda: _build_book(book_type, initial_events),
        lambda: _measure_initial_book(book_type, initial_events),
        event_count,
    )

    for sale_case in case["sell_quantities"]:
        percent = sale_case["percent"]
        sale_event = _sale_event(case, percent, sale_case["qty_units"])
        phase = f"sell_operation_{percent}pct"

        def warm_sell(book_type=book_type, initial_events=initial_events,
                      sale_event=sale_event):
            _measure_sell_operation(book_type, initial_events, sale_event)

        def warm_total_sell(path=path, book_type=book_type,
                            sale_event=sale_event):
            _measure_total_sell(path, book_type, sale_event)

        _timing_phase(
            connection,
            phase,
            repeats,
            warm_sell,
            lambda book_type=book_type, initial_events=initial_events,
            sale_event=sale_event: _measure_sell_operation(
                book_type, initial_events, sale_event
            ),
            1,
        )
        _timing_phase(
            connection,
            f"total_application_sell_{percent}pct",
            repeats,
            warm_total_sell,
            lambda path=path, book_type=book_type,
            sale_event=sale_event: _measure_total_sell(
                path, book_type, sale_event
            ),
            len(initial_events) + 1,
        )

        combined_events = initial_events + [sale_event]
        counter = _counter_event_replay(book_type, combined_events)
        counter_row = phase_row("counters", repeat=1)
        counter_row.update(counter)
        counter_row["requested_sell_qty_units"] = sale_event["qty_units"]
        counter_row["sell_percent"] = percent
        _emit(connection, counter_row)

        memory_rows = _memory_replay(book_type, combined_events, case)
        for row in memory_rows:
            row["requested_sell_qty_units"] = sale_event["qty_units"]
            row["sell_percent"] = percent
            _emit(connection, row)

    representative_sale = case["sell_quantities"][1]
    sale_event = _sale_event(
        case, representative_sale["percent"], representative_sale["qty_units"]
    )
    combined_events = initial_events + [sale_event]
    latency_path = Path(artifact_dir) / "latencies.jsonl"
    latency_summary = _latency_replay(book_type, combined_events, latency_path)
    latency_row = phase_row("latency_summary", repeat=1)
    latency_row.update(latency_summary)
    latency_row["requested_sell_qty_units"] = sale_event["qty_units"]
    _emit(connection, latency_row)


def _measure_worker(connection, case, version, repeats, artifact_dir,
                    profile_event_limit):
    try:
        if case["experiment"] == "fixed_liquidation":
            _fixed_worker(connection, case, version, repeats, artifact_dir)
        else:
            _generic_worker(
                connection,
                case,
                version,
                repeats,
                artifact_dir,
                profile_event_limit,
            )
        connection.send({"kind": "done"})
    except Exception as error:
        connection.send(
            {
                "kind": "error",
                "error_type": type(error).__name__,
                "error": str(error),
                "traceback": traceback.format_exc(),
            }
        )
    finally:
        connection.close()


_WINDOWS_MEMORY_API = None
_WINDOWS_MEMORY_COUNTERS = None


def _peak_working_set_bytes(pid):
    if os.name == "nt":
        global _WINDOWS_MEMORY_API
        global _WINDOWS_MEMORY_COUNTERS
        if _WINDOWS_MEMORY_API is None:
            from ctypes import wintypes

            class ProcessMemoryCountersEx(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                    ("PrivateUsage", ctypes.c_size_t),
                ]

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("Psapi", use_last_error=True)
            kernel32.OpenProcess.argtypes = [
                wintypes.DWORD,
                wintypes.BOOL,
                wintypes.DWORD,
            ]
            kernel32.OpenProcess.restype = wintypes.HANDLE
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.CloseHandle.restype = wintypes.BOOL
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(ProcessMemoryCountersEx),
                wintypes.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
            _WINDOWS_MEMORY_API = (kernel32, psapi)
            _WINDOWS_MEMORY_COUNTERS = ProcessMemoryCountersEx

        kernel32, psapi = _WINDOWS_MEMORY_API
        counters_type = _WINDOWS_MEMORY_COUNTERS
        handle = kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:
                return None
            raise OSError(error, "OpenProcess failed for memory monitoring")
        try:
            counters = counters_type()
            counters.cb = ctypes.sizeof(counters)
            if not psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                raise OSError(
                    ctypes.get_last_error(),
                    "GetProcessMemoryInfo failed",
                )
            return int(counters.PeakWorkingSetSize)
        finally:
            kernel32.CloseHandle(handle)

    if sys.platform.startswith("linux"):
        status_path = Path(f"/proc/{pid}/status")
        try:
            for line in status_path.read_text(encoding="ascii").splitlines():
                if line.startswith("VmHWM:"):
                    return int(line.split()[1]) * 1024
        except FileNotFoundError:
            return None
        raise RuntimeError(f"VmHWM not found in {status_path}")
    raise RuntimeError(
        "sampled memory-limit enforcement is supported on Windows and Linux"
    )


def _terminate_worker(process):
    if process.is_alive():
        process.terminate()
        process.join(timeout=3)
    if process.is_alive():
        process.kill()
        process.join(timeout=3)


def _write_jsonl_line(stream, value):
    stream.write(json.dumps(value, separators=(",", ":"), sort_keys=True))
    stream.write("\n")
    stream.flush()


def _receive_worker_message(connection, timeout=0):
    try:
        if not connection.poll(timeout):
            return None
        return connection.recv()
    except (EOFError, OSError) as error:
        return {
            "kind": "ipc_error",
            "error": f"{type(error).__name__}: {error}",
        }


def _config_id(case, version):
    case_id = case["case_id"].replace(
        "queue_concentration_prices", "queue_prices", 1
    )
    return f"{case_id}__{version}".replace("/", "_").replace("\\", "_")


def _next_attempt(records_dir, config_id):
    records_dir = Path(records_dir)
    attempt = 1
    while (
        records_dir / f"{config_id}__attempt_{attempt:03d}.json"
    ).exists() or (
        records_dir / f"{config_id}__attempt_{attempt:03d}.progress.jsonl"
    ).exists():
        attempt += 1
    return attempt


def _completed_config_exists(records_dir, config_id):
    prefix = f"{config_id}__attempt_"
    for path in Path(records_dir).glob(f"{prefix}*.json"):
        if path.name.endswith(".progress.jsonl"):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if record.get("status") == "completed":
            return True
    return False


def _row_common(case, version, environment, code_hashes, limits):
    return {
        "version": version,
        "experiment": case["experiment"],
        "scenario": case["scenario"],
        "seed": case.get("seed"),
        "event_count": case["event_count"],
        "generator_settings": case["generator_settings"],
        "input_checksums": case["input_checksums"],
        "active_order_peak": None,
        "occupied_price_level_peak": None,
        "requested_sell_qty_units": None,
        "fill_count": None,
        "phase": None,
        "repeat": None,
        "elapsed_seconds": None,
        "traced_current_bytes": None,
        "traced_peak_bytes": None,
        "status": None,
        "environment": environment,
        "code_hashes": code_hashes,
        "time_limit_seconds": limits["time_limit_seconds"],
        "memory_limit_mib": limits["memory_limit_mib"],
    }


def _decorate_row(row, common, run_dir):
    decorated = dict(common)
    decorated.update(row)
    for path_field in ("latency_raw_path", "profile_data_path", "profile_text_path"):
        if decorated.get(path_field):
            try:
                decorated[path_field] = str(
                    Path(decorated[path_field]).resolve().relative_to(run_dir)
                )
            except ValueError:
                pass
    return decorated


def _run_one_configuration(run_dir, case, version, limits, settings):
    records_dir = Path(run_dir) / "records"
    artifacts_root = Path(run_dir) / "artifacts"
    records_dir.mkdir(parents=True, exist_ok=True)
    artifacts_root.mkdir(parents=True, exist_ok=True)
    config_id = _config_id(case, version)
    attempt = _next_attempt(records_dir, config_id)
    attempt_name = f"{config_id}__attempt_{attempt:03d}"
    progress_path = records_dir / f"{attempt_name}.progress.jsonl"
    result_path = records_dir / f"{attempt_name}.json"
    artifact_dir = artifacts_root / attempt_name
    artifact_dir.mkdir(parents=True, exist_ok=False)

    environment = _environment_snapshot()
    code_hashes = _code_hashes()
    common = _row_common(case, version, environment, code_hashes, limits)
    context = multiprocessing.get_context("spawn")
    parent_connection, child_connection = context.Pipe(duplex=False)
    process = context.Process(
        target=_measure_worker,
        args=(
            child_connection,
            case,
            version,
            TIMING_REPEATS,
            str(artifact_dir),
            settings["profile_event_limit"],
        ),
        name=f"benchmark-{config_id}",
    )

    rows = []
    worker_message = None
    stop_status = None
    stop_error = None
    started = time.monotonic()
    peak_working_set = None
    with progress_path.open("x", encoding="utf-8", newline="\n") as progress:
        process.start()
        child_connection.close()
        try:
            try:
                sampled_memory = _peak_working_set_bytes(process.pid)
                if sampled_memory is not None:
                    peak_working_set = sampled_memory
                    if sampled_memory > limits["memory_limit_bytes"]:
                        stop_status = "stopped_memory_limit"
            except (OSError, RuntimeError) as error:
                stop_status = "error"
                stop_error = (
                    f"memory monitor failed: {type(error).__name__}: {error}"
                )
            while process.is_alive():
                if stop_status is not None:
                    break
                elapsed = time.monotonic() - started
                remaining = limits["time_limit_seconds"] - elapsed
                if remaining <= 0:
                    stop_status = "stopped_timeout"
                    break
                message = _receive_worker_message(
                    parent_connection, min(MEMORY_POLL_SECONDS, remaining)
                )
                if message is not None:
                    if message["kind"] == "row":
                        row = _decorate_row(message["row"], common, Path(run_dir))
                        rows.append(row)
                        _write_jsonl_line(progress, {"kind": "row", "row": row})
                    elif message["kind"] == "error":
                        worker_message = message
                        stop_status = "error"
                        break
                    elif message["kind"] == "done":
                        if (
                            time.monotonic() - started
                            >= limits["time_limit_seconds"]
                        ):
                            stop_status = "stopped_timeout"
                        else:
                            worker_message = message
                        break
                    elif message["kind"] == "ipc_error":
                        worker_message = message
                        stop_status = "error"
                        stop_error = message["error"]
                        break

                elapsed = time.monotonic() - started
                if elapsed >= limits["time_limit_seconds"]:
                    stop_status = "stopped_timeout"
                    break

                try:
                    sampled_memory = _peak_working_set_bytes(process.pid)
                except (OSError, RuntimeError) as error:
                    stop_status = "error"
                    stop_error = (
                        f"memory monitor failed: {type(error).__name__}: {error}"
                    )
                    break
                if sampled_memory is not None:
                    peak_working_set = max(
                        peak_working_set or 0, sampled_memory
                    )
                    if sampled_memory > limits["memory_limit_bytes"]:
                        stop_status = "stopped_memory_limit"
                        break
            if stop_status is not None and process.is_alive():
                _terminate_worker(process)
            else:
                process.join(timeout=1)
                if process.is_alive():
                    stop_status = "error"
                    stop_error = "worker did not exit after sending completion"
                    _terminate_worker(process)

            while True:
                message = _receive_worker_message(parent_connection)
                if message is None or message["kind"] == "ipc_error":
                    if (
                        message is not None
                        and worker_message is None
                        and stop_status is None
                    ):
                        worker_message = message
                        stop_status = "error"
                        stop_error = message["error"]
                    break
                if message["kind"] == "row":
                    row = _decorate_row(message["row"], common, Path(run_dir))
                    rows.append(row)
                    _write_jsonl_line(progress, {"kind": "row", "row": row})
                elif message["kind"] == "error":
                    worker_message = message
                    stop_status = "error"
                elif message["kind"] == "done":
                    worker_message = message
        finally:
            parent_connection.close()
            if process.is_alive():
                _terminate_worker(process)

    duration_until_stop = time.monotonic() - started
    if stop_status is None:
        if worker_message and worker_message.get("kind") == "done":
            status = "completed"
        elif worker_message and worker_message.get("kind") == "error":
            status = "error"
        elif process.exitcode == 0:
            status = "completed"
        else:
            status = "error"
    else:
        status = stop_status

    failure = None
    if worker_message and worker_message.get("kind") == "error":
        failure = {
            "error_type": worker_message.get("error_type"),
            "error": worker_message.get("error"),
            "traceback": worker_message.get("traceback"),
        }
    elif stop_error:
        failure = {"error": stop_error}
    elif status != "completed":
        failure = {
            "message": (
                "worker stopped at its enforced wall-time limit"
                if status == "stopped_timeout"
                else "worker exceeded sampled process memory limit"
                if status == "stopped_memory_limit"
                else "worker exited without a completion message"
            ),
            "duration_until_stop_seconds": duration_until_stop,
            "peak_working_set_bytes_observed": peak_working_set,
        }
    if status != "completed":
        stop_row = stopped_phase_row(
            status, duration_until_stop, peak_working_set
        )
        decorated_stop_row = _decorate_row(stop_row, common, Path(run_dir))
        rows.append(decorated_stop_row)
        with progress_path.open("a", encoding="utf-8", newline="\n") as progress:
            _write_jsonl_line(
                progress, {"kind": "worker_stop", "row": decorated_stop_row}
            )

    record = {
        "config_id": config_id,
        "attempt": attempt,
        "status": status,
        "case": _case_manifest(case),
        "version": version,
        "time_limit_seconds": limits["time_limit_seconds"],
        "memory_limit_mib": limits["memory_limit_mib"],
        "duration_until_stop_seconds": duration_until_stop,
        "peak_working_set_bytes_observed": peak_working_set,
        "failure": failure,
        "rows": rows,
        "progress_file": _relative_path(progress_path),
        "artifact_directory": _relative_path(artifact_dir),
    }
    _json_write_exclusive(result_path, record)
    return record


def _parse_int_list(value, option):
    try:
        numbers = [int(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as error:
        raise ValueError(f"{option} must be comma-separated integers") from error
    if not numbers or any(number <= 0 for number in numbers):
        raise ValueError(f"{option} values must be positive integers")
    return numbers


def _settings_from_args(args):
    smoke = args.smoke
    settings = {
        "profile": "smoke" if smoke else "full",
        "event_sizes": [25] if smoke else [1000, 10000, 100000],
        "seeds": [42] if smoke else [42, 43, 44],
        "scenarios": list(SCENARIOS),
        "levels": 1000,
        "fixed_book_orders": 40 if smoke else 1000,
        "queue_orders": 1000 if smoke else 10000,
        "churn_cycles": 20 if smoke else 5000,
        "parity_event_limit": 1000,
        "profile_event_limit": 2000,
        "time_limit_seconds": 60 if smoke else 300,
        "memory_limit_mib": 2048 if smoke else 4096,
        "timing_repeats": TIMING_REPEATS,
        "memory_monitor_poll_seconds": MEMORY_POLL_SECONDS,
    }
    if args.events:
        settings["event_sizes"] = _parse_int_list(args.events, "--events")
    if args.seeds:
        settings["seeds"] = _parse_int_list(args.seeds, "--seeds")
    if args.scenarios:
        scenarios = [item.strip() for item in args.scenarios.split(",")]
        if not scenarios or any(item not in SCENARIOS for item in scenarios):
            raise ValueError(f"--scenarios values must be chosen from {SCENARIOS}")
        settings["scenarios"] = scenarios
    for option, setting in (
        ("levels", "levels"),
        ("fixed_book_orders", "fixed_book_orders"),
        ("queue_orders", "queue_orders"),
        ("churn_cycles", "churn_cycles"),
        ("parity_event_limit", "parity_event_limit"),
        ("profile_event_limit", "profile_event_limit"),
    ):
        value = getattr(args, option)
        if value is not None:
            settings[setting] = value
    if args.time_limit_seconds is not None:
        settings["time_limit_seconds"] = args.time_limit_seconds
    if args.memory_limit_mib is not None:
        settings["memory_limit_mib"] = args.memory_limit_mib
    positive = (
        "levels",
        "fixed_book_orders",
        "queue_orders",
        "churn_cycles",
        "parity_event_limit",
        "profile_event_limit",
        "time_limit_seconds",
        "memory_limit_mib",
    )
    if any(settings[key] <= 0 for key in positive):
        raise ValueError("sizes and resource limits must be positive")
    if settings["levels"] >= 6000000:
        raise ValueError("--levels must be less than 6,000,000")
    if not math.isfinite(settings["time_limit_seconds"]):
        raise ValueError("--time-limit-seconds must be finite")
    if not math.isfinite(settings["memory_limit_mib"]):
        raise ValueError("--memory-limit-mib must be finite")
    if len(set(settings["event_sizes"])) != len(settings["event_sizes"]):
        raise ValueError("--events must not contain duplicate sizes")
    if len(set(settings["seeds"])) != len(settings["seeds"]):
        raise ValueError("--seeds must not contain duplicates")
    if len(set(settings["scenarios"])) != len(settings["scenarios"]):
        raise ValueError("--scenarios must not contain duplicates")
    return settings


def _argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run-id")
    parser.add_argument("--resume")
    parser.add_argument("--events", help="comma-separated event sizes")
    parser.add_argument("--seeds", help="comma-separated seeds")
    parser.add_argument("--scenarios", help="comma-separated scenario names")
    parser.add_argument("--levels", type=int)
    parser.add_argument("--fixed-book-orders", type=int)
    parser.add_argument("--queue-orders", type=int)
    parser.add_argument("--churn-cycles", type=int)
    parser.add_argument("--parity-event-limit", type=int)
    parser.add_argument("--profile-event-limit", type=int)
    parser.add_argument("--time-limit-seconds", type=float)
    parser.add_argument("--memory-limit-mib", type=float)
    return parser


def _resolve_run_path(run_id_or_path):
    candidate = Path(run_id_or_path)
    if not candidate.is_absolute():
        candidate = RUNS_DIR / candidate
    return candidate.resolve()


def _create_run_directory(run_id):
    if not run_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in run_id):
        raise ValueError("run-id may contain only letters, digits, dot, underscore, and hyphen")
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "inputs").mkdir()
    (run_dir / "records").mkdir()
    (run_dir / "artifacts").mkdir()
    return run_dir


def _run(args):
    if args.resume and (args.run_id or args.smoke or args.events or args.seeds
                        or args.scenarios or args.levels
                        or args.fixed_book_orders or args.queue_orders
                        or args.churn_cycles):
        raise ValueError(
            "resume uses the saved workload configuration; specify only new limits"
        )

    if args.resume:
        run_dir = _resolve_run_path(args.resume)
        metadata_path = run_dir / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        settings = metadata["settings"]
        if args.time_limit_seconds is not None:
            settings["time_limit_seconds"] = args.time_limit_seconds
        if args.memory_limit_mib is not None:
            settings["memory_limit_mib"] = args.memory_limit_mib
        cases = build_cases(settings, run_dir)
        current_cases = [_case_manifest(case) for case in cases]
        if current_cases != metadata["cases"]:
            raise ValueError("resume inputs/settings differ from saved run metadata")
    else:
        settings = _settings_from_args(args)
        run_id = args.run_id or (
            f"{settings['profile']}_"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        )
        run_dir = _create_run_directory(run_id)
        try:
            cases = build_cases(settings, run_dir)
            parity = [
                {
                    "case_id": case["case_id"],
                    **validate_case(case, settings["parity_event_limit"]),
                }
                for case in cases
            ]
            metadata = {
                "schema_version": 1,
                "run_id": run_id,
                "created_at_utc": datetime.now(timezone.utc).isoformat(),
                "settings": settings,
                "cases": [_case_manifest(case) for case in cases],
                "parity_validation": parity,
                "environment": _environment_snapshot(),
                "code_hashes": _code_hashes(),
            }
            _json_write_exclusive(run_dir / "metadata.json", metadata)
        except Exception as error:
            _json_write_exclusive(
                run_dir / "generation_or_validation_error.json",
                {
                    "status": "error",
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                },
            )
            raise

    limits = {
        "time_limit_seconds": settings["time_limit_seconds"],
        "memory_limit_mib": settings["memory_limit_mib"],
        "memory_limit_bytes": int(settings["memory_limit_mib"] * 1024 * 1024),
    }
    run_statuses = {}
    for case in cases:
        parity = validate_case(case, settings["parity_event_limit"])
        if parity["status"] != "passed":
            raise AssertionError(f"benchmark input parity failed for {case['case_id']}")
        for version in VERSIONS:
            config_id = _config_id(case, version)
            records_dir = run_dir / "records"
            if args.resume and _completed_config_exists(records_dir, config_id):
                run_statuses[config_id] = "skipped_completed"
                print(f"{config_id}: skipped (completed record exists)")
                continue
            record = _run_one_configuration(
                run_dir, case, version, limits, settings
            )
            run_statuses[config_id] = record["status"]
            print(
                f"{config_id}: {record['status']} "
                f"({len(record['rows'])} measurement rows)"
            )

    status_counts = {}
    for status in run_statuses.values():
        status_counts[status] = status_counts.get(status, 0) + 1
    summary = {
        "run_id": run_dir.name,
        "run_directory": str(run_dir),
        "profile": settings["profile"],
        "config_status_counts": status_counts,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(
        status in ("completed", "skipped_completed")
        for status in run_statuses.values()
    ) else 2


def main(argv=None):
    parser = _argument_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except Exception as error:
        parser.exit(
            2,
            f"benchmark run failed: {type(error).__name__}: {error}\n",
        )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
