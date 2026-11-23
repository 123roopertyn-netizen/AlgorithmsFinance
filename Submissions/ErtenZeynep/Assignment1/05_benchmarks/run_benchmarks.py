"""Resource-bounded benchmark controller. Only the pilot mode is implemented."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import queue
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).resolve().with_name("_benchmark_worker.py")
IMPLEMENTATION_ROOT = PROJECT_ROOT / "04_implementation"
MAX_GLOBAL_SECONDS = 1200.0

PILOT_CONFIGS = [
    {
        "scenario": scenario,
        "events": 10_000,
        "seed": 42,
        "workload_id": f"02_data/supplied/data/{scenario}_10000.jsonl.gz",
        "processing_timeout": 30.0,
        "preparation_timeout": 15.0,
    }
    for scenario in ("buildup", "crowded", "mixed", "sweep", "cancel_churn")
] + [
    {
        "scenario": scenario,
        "events": 100_000,
        "seed": 42,
        "workload_id": f"02_data/generated/{scenario}_100000_seed42.jsonl.gz",
        "processing_timeout": 120.0,
        "preparation_timeout": 45.0,
    }
    for scenario in ("buildup", "cancel_churn", "sweep")
]


def _total_ram_bytes() -> int | None:
    try:
        if os.name == "nt":
            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_physical", ctypes.c_ulonglong),
                    ("available_physical", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong),
                    ("available_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("available_virtual", ctypes.c_ulonglong),
                    ("available_extended_virtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.total_physical)
            return None
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(pages * page_size)
    except (AttributeError, OSError, ValueError):
        return None


def _environment() -> dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or None,
        "cpu_count": os.cpu_count(),
        "total_ram_bytes": _total_ram_bytes(),
    }


def _reader(stream: TextIO, output: queue.Queue[str | None]) -> None:
    try:
        for line in stream:
            output.put(line)
    finally:
        output.put(None)


def _stderr_reader(stream: TextIO, lines: list[str]) -> None:
    for line in stream:
        lines.append(line.rstrip())
        if len(lines) > 50:
            del lines[0]


def _receive(messages: queue.Queue[str | None], timeout: float) -> dict[str, Any]:
    if timeout <= 0:
        raise queue.Empty
    line = messages.get(timeout=timeout)
    if line is None:
        raise EOFError("worker stdout closed")
    payload = json.loads(line)
    if type(payload) is not dict:
        raise ValueError("worker message is not an object")
    return payload


def _stop_worker(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        process.wait()
        return
    process.terminate()
    try:
        process.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


def _write_record(stream: TextIO, record: dict[str, Any]) -> None:
    stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def _plan() -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    for config_index, config in enumerate(PILOT_CONFIGS):
        order = ("baseline", "optimized") if config_index % 2 == 0 else ("optimized", "baseline")
        for engine in order:
            planned.append({**config, "engine": engine})
    return planned


def _base_record(index: int, run: dict[str, Any], environment: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase": "pilot",
        "planned_index": index,
        "engine": run["engine"],
        "scenario": run["scenario"],
        "event_count": run["events"],
        "seed": run["seed"],
        "workload_id": run["workload_id"],
        "status": None,
        "engine_seconds": None,
        "controller_wall_seconds": None,
        "preparation_seconds": None,
        "processing_timeout_seconds": run["processing_timeout"],
        "preparation_timeout_seconds": run["preparation_timeout"],
        "stop_reason": None,
        "snapshot_digest": None,
        "event_stream_digest": None,
        "workload_sha256": None,
        "final_active_orders": None,
        "last_accepted_seq": None,
        "worker_pid": None,
        "gc_policy": "collect_once_then_enabled",
        "environment": environment,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _execute_run(
    index: int,
    run: dict[str, Any],
    environment: dict[str, Any],
    global_start: float,
    global_limit: float,
) -> dict[str, Any]:
    record = _base_record(index, run, environment)
    workload = PROJECT_ROOT / run["workload_id"]
    nonce = uuid.uuid4().hex
    command = [
        sys.executable,
        str(WORKER),
        "--engine", run["engine"],
        "--workload", str(workload),
        "--workload-id", run["workload_id"],
        "--expected-events", str(run["events"]),
        "--nonce", nonce,
    ]
    worker_start = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=PROJECT_ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    record["worker_pid"] = process.pid
    messages: queue.Queue[str | None] = queue.Queue()
    stderr_lines: list[str] = []
    assert process.stdout is not None and process.stderr is not None
    threading.Thread(target=_reader, args=(process.stdout, messages), daemon=True).start()
    threading.Thread(target=_stderr_reader, args=(process.stderr, stderr_lines), daemon=True).start()

    try:
        remaining_global = global_limit - (time.perf_counter() - global_start)
        preparation_window = min(run["preparation_timeout"], remaining_global)
        try:
            ready = _receive(messages, preparation_window)
        except queue.Empty:
            record["status"] = "preparation_timeout"
            record["stop_reason"] = (
                "global_wall_clock_ceiling_during_preparation"
                if remaining_global <= run["preparation_timeout"]
                else "preparation_timeout"
            )
            return record
        except (EOFError, json.JSONDecodeError, ValueError) as exc:
            record["status"] = "failed"
            record["stop_reason"] = f"preparation_protocol_error:{type(exc).__name__}:{exc}"
            return record
        if ready.get("type") == "ERROR":
            record["status"] = "failed"
            record["stop_reason"] = f"worker_{ready.get('stage')}:{ready.get('error_type')}:{ready.get('message')}"
            return record
        if ready.get("type") != "READY" or ready.get("nonce") != nonce:
            record["status"] = "handshake_failed"
            record["stop_reason"] = "invalid_READY_message"
            return record
        if ready.get("event_count") != run["events"] or ready.get("gc_enabled") is not True:
            record["status"] = "failed"
            record["stop_reason"] = "READY_invariant_failed"
            return record

        for field in ("preparation_seconds", "event_stream_digest", "workload_sha256"):
            record[field] = ready.get(field)
        assert process.stdin is not None
        process.stdin.write(json.dumps({"type": "START", "nonce": nonce}) + "\n")
        process.stdin.flush()

        remaining_global = global_limit - (time.perf_counter() - global_start)
        try:
            started = _receive(messages, min(5.0, remaining_global))
        except (queue.Empty, EOFError, json.JSONDecodeError, ValueError) as exc:
            record["status"] = "handshake_failed"
            record["stop_reason"] = f"STARTED_error:{type(exc).__name__}:{exc}"
            return record
        if started != {"type": "STARTED", "nonce": nonce}:
            record["status"] = "handshake_failed"
            record["stop_reason"] = "invalid_STARTED_message"
            return record

        processing_controller_start = time.perf_counter()
        remaining_global = global_limit - (processing_controller_start - global_start)
        processing_window = min(run["processing_timeout"], remaining_global)
        try:
            done = _receive(messages, processing_window)
        except queue.Empty:
            record["status"] = "timed_out"
            record["stop_reason"] = (
                "global_wall_clock_ceiling_during_processing"
                if remaining_global <= run["processing_timeout"]
                else "processing_timeout"
            )
            return record
        except (EOFError, json.JSONDecodeError, ValueError) as exc:
            record["status"] = "failed"
            record["stop_reason"] = f"processing_protocol_error:{type(exc).__name__}:{exc}"
            return record
        if done.get("type") == "ERROR":
            record["status"] = "failed"
            record["stop_reason"] = f"worker_{done.get('stage')}:{done.get('error_type')}:{done.get('message')}"
            return record
        if done.get("type") != "DONE" or done.get("nonce") != nonce:
            record["status"] = "failed"
            record["stop_reason"] = "invalid_DONE_message"
            return record
        record.update(
            status="completed",
            engine_seconds=done.get("engine_seconds"),
            snapshot_digest=done.get("snapshot_digest"),
            final_active_orders=done.get("final_active_orders"),
            last_accepted_seq=done.get("last_accepted_seq"),
            stop_reason=None,
        )
        return record
    except (BrokenPipeError, OSError, subprocess.SubprocessError) as exc:
        record["status"] = "failed"
        record["stop_reason"] = f"controller_worker_error:{type(exc).__name__}:{exc}"
        return record
    finally:
        _stop_worker(process)
        record["controller_wall_seconds"] = time.perf_counter() - worker_start
        if record["status"] != "completed" and stderr_lines:
            record["worker_stderr_tail"] = stderr_lines[-10:]


def run_pilot(output: Path, global_limit: float) -> int:
    if global_limit <= 0 or global_limit > MAX_GLOBAL_SECONDS:
        raise ValueError(f"global limit must be in (0, {MAX_GLOBAL_SECONDS}]")
    if output.exists():
        raise FileExistsError(f"refusing to overwrite existing pilot output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = _environment()
    plan = _plan()
    global_start = time.perf_counter()
    records: list[dict[str, Any]] = []
    active_processes: list[subprocess.Popen[str]] = []
    try:
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            for index, run in enumerate(plan, 1):
                if time.perf_counter() - global_start >= global_limit:
                    record = _base_record(index, run, environment)
                    record["status"] = "skipped_global_budget"
                    record["stop_reason"] = "global_wall_clock_ceiling_reached_before_start"
                else:
                    record = _execute_run(index, run, environment, global_start, global_limit)
                record["global_elapsed_seconds"] = time.perf_counter() - global_start
                records.append(record)
                _write_record(stream, record)
    finally:
        for process in active_processes:
            _stop_worker(process)

    total = time.perf_counter() - global_start
    summary = {
        "phase": "pilot",
        "planned_runs": len(plan),
        "written_records": len(records),
        "statuses": dict(Counter(record["status"] for record in records)),
        "total_wall_seconds": total,
        "output": output.relative_to(PROJECT_ROOT).as_posix(),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if len(records) == len(plan) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    pilot = subparsers.add_parser("pilot", help="run the approved 16-run pilot")
    pilot.add_argument("--output", type=Path, required=True)
    pilot.add_argument("--global-timeout-seconds", type=float, default=MAX_GLOBAL_SECONDS)
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    if args.mode == "pilot":
        return run_pilot(output.resolve(), args.global_timeout_seconds)
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
