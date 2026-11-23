"""Primary timing runs (README: "Benchmark limits and run rules").

    .venv/bin/python -m bench.timing                    # everything, resumable
    .venv/bin/python -m bench.timing --versions B --max-events 10000

Per (version, stream): fresh child process; parse time measured separately; the first replay is
timed; <= 60 s -> it is the warm-up and 5 timed replays follow; > 60 s -> it is the single
measurement. Every replay: fresh empty book, `gc.collect()` before and gc disabled during the
replay (like `timeit`), results discarded, `time.perf_counter`. A replay over 600 s is stopped.
Writes results/timing_raw.csv (one row per replay) and results/timing_summary.csv (one row per run).
"""
from __future__ import annotations

import argparse
import gc
import statistics
import time

from bench import common
from bench.common import RESULTS, append_csv, read_csv, stream_path
from bench.harness import run_limited
from lob import VERSIONS
from lob.common import load_events

RAW = RESULTS / "timing_raw.csv"
SUMMARY = RESULTS / "timing_summary.csv"
RAW_FIELDS = ["version", "scenario", "seed", "events", "levels", "phase", "repeat", "status",
              "elapsed_seconds", "events_done", "limit_seconds"]
SUMMARY_FIELDS = ["version", "scenario", "seed", "events", "levels", "status", "reason", "repeats",
                  "median_seconds", "min_seconds", "max_seconds", "throughput_events_per_second",
                  "parse_seconds", "limit_seconds", "events_done_at_stop"]


def _replay(cls, events) -> float:
    """One timed replay of `events` through a fresh book (name starts with _replay: see harness)."""
    book = cls()
    process = book.process
    gc.collect()
    gc.disable()
    start = time.perf_counter()
    for e in events:
        process(e)
    elapsed = time.perf_counter() - start
    gc.enable()
    return elapsed


def timing_worker(conn, version: str, path: str, slow_first_s: float, repeats: int) -> None:
    start = time.perf_counter()
    events = load_events(path)
    conn.send(("parsed", time.perf_counter() - start, len(events)))
    cls = VERSIONS[version]
    conn.send(("unit_start", "first"))
    first = _replay(cls, events)
    conn.send(("unit_done", "first", first))
    if first > slow_first_s:
        conn.send(("mode", "single"))
        return
    conn.send(("mode", "warmup"))
    for r in range(repeats):
        conn.send(("unit_start", f"timed{r}"))
        conn.send(("unit_done", f"timed{r}", _replay(cls, events)))


def run_one(version: str, spec: dict, limit_s: float, slow_first_s: float, repeats: int) -> None:
    """Run one (version, stream) pair and append its raw rows and its summary row."""
    base = {"version": version, **{k: spec[k] for k in ("scenario", "seed", "events", "levels")}}
    result = run_limited(timing_worker, (version, str(stream_path(**spec)), slow_first_s, repeats),
                         limit_s)
    parse_s, mode, done = None, None, {}
    for msg in result["messages"]:
        if msg[0] == "parsed":
            parse_s = msg[1]
        elif msg[0] == "mode":
            mode = msg[1]
        elif msg[0] == "unit_done":
            done[msg[1]] = msg[2]
    raw_rows = []
    if "first" in done:
        raw_rows.append({"phase": "single" if mode == "single" else "warmup", "repeat": 0,
                         "status": "ok", "elapsed_seconds": done["first"]})
    for r in range(common.TIMED_REPEATS):
        if f"timed{r}" in done:
            raw_rows.append({"phase": "timed", "repeat": r, "status": "ok",
                             "elapsed_seconds": done[f"timed{r}"]})
    status, reason = "ok", ""
    if result["outcome"] == "stopped":
        status = "stopped"
        tag = result["stopped_tag"]
        raw_rows.append({"phase": "single" if tag == "first" else "timed",
                         "repeat": 0 if tag == "first" else int(tag[5:]), "status": "stopped",
                         "elapsed_seconds": result["stopped_after_s"],
                         "events_done": result["events_done"]})
        reason = f"a replay reached the {limit_s:g} s limit; remaining repeats skipped"
    elif result["outcome"] == "error":
        status, reason = "error", result["error"]
    for row in raw_rows:
        append_csv(RAW, RAW_FIELDS, {**base, "limit_seconds": limit_s, **row})
    timed = [r["elapsed_seconds"] for r in raw_rows if r["status"] == "ok"
             and r["phase"] in ("timed", "single")]
    summary = {**base, "status": status, "reason": reason, "repeats": len(timed),
               "parse_seconds": parse_s, "limit_seconds": limit_s}
    if timed:
        median = statistics.median(timed)
        summary.update(median_seconds=median, min_seconds=min(timed), max_seconds=max(timed),
                       throughput_events_per_second=spec["events"] / median)
    if status == "stopped":
        summary["events_done_at_stop"] = result["events_done"]
    append_csv(SUMMARY, SUMMARY_FIELDS, summary)
    print(f"{version} {spec['scenario']:12s} M={spec['events']:>8d} L={spec['levels']:>4d} "
          f"s{spec['seed']}: {status} " + (f"median {summary.get('median_seconds', 0):.4f} s "
          f"repeats={summary['repeats']}" if timed else reason), flush=True)


def a_million_decision(spec: dict, summary_rows: list[dict]) -> str | None:
    """Rule 3: reason string if A must NOT run this 1,000,000-event stream, else None."""
    ref = [r for r in summary_rows if r["version"] == "A" and r["scenario"] == spec["scenario"]
           and r["seed"] == "42" and r["events"] == "100000" and r["levels"] == "1000"]
    if not ref:
        return "A at 100,000 events has no recorded result (run the 100,000-event streams first)"
    row = ref[0]
    if row["status"] != "ok" or not row["median_seconds"]:
        return f"A at 100,000 events on {spec['scenario']} did not finish (status {row['status']})"
    median = float(row["median_seconds"])
    if median >= common.A_MILLION_THRESHOLD:
        return (f"A at 100,000 events on {spec['scenario']} took {median:.1f} s "
                f"(>= {common.A_MILLION_THRESHOLD} s)")
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--versions", nargs="+", default=["A", "B"], choices=sorted(VERSIONS))
    parser.add_argument("--max-events", type=int, default=10**9)
    parser.add_argument("--scenarios", nargs="+", default=list(common.SCENARIOS))
    parser.add_argument("--limit-seconds", type=float, default=common.LIMIT_SECONDS)
    parser.add_argument("--slow-first-seconds", type=float, default=common.SLOW_FIRST_SECONDS)
    parser.add_argument("--repeats", type=int, default=common.TIMED_REPEATS)
    args = parser.parse_args(argv)
    done = {(r["version"], r["scenario"], r["seed"], r["events"], r["levels"])
            for r in read_csv(SUMMARY)}
    for spec in common.all_streams():
        if spec["events"] > args.max_events or spec["scenario"] not in args.scenarios:
            continue
        for version in args.versions:
            key = (version, spec["scenario"], str(spec["seed"]), str(spec["events"]),
                   str(spec["levels"]))
            if key in done:
                print("keep", key, flush=True)
                continue
            if version == "A" and spec["events"] == 1_000_000:
                reason = a_million_decision(spec, read_csv(SUMMARY))
                if reason:
                    append_csv(SUMMARY, SUMMARY_FIELDS, {
                        "version": "A", **{k: spec[k] for k in ("scenario", "seed", "events",
                                                                   "levels")},
                        "status": "not_run", "reason": reason, "repeats": 0})
                    print(f"A {spec['scenario']} M=1000000: not_run ({reason})", flush=True)
                    continue
            run_one(version, spec, args.limit_seconds, args.slow_first_seconds, args.repeats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
