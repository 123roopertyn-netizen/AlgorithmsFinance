"""Per-event processing latency: a separate instrumentation run.

Called by run_benchmark.py (phase "latency"). One child per (dataset,
version): load the events, one uninstrumented warm-up replay, then one
instrumented replay on a fresh book that records perf_counter_ns() around
every process_event call into a preallocated array (GC disabled, same
policy as the timing run). Each replay is under the same time limit.

This is algorithm processing latency only: no queueing or network latency,
and it says nothing about real-time overload capacity. It is never derived
from 1/throughput. Percentiles: nearest-rank (bench_common).

Segments: all events, the first 1,000 and the last 1,000 (for buildup the
book grows from 0 to M orders, so first vs last shows the growth).

Writes <out>/latency_summary.csv and <out>/latency_quantiles.csv (all
percentiles 0..100 plus 99.9 per segment; units: nanoseconds).

Child mode (internal): bench_latency.py --child <file> <version>
"""

import argparse
import gc
import time
from array import array

from bench_common import (VERSIONS, append_rows, book_class, dataset_name, emit, load_timed,
                          nearest_rank, read_manifest, rel, rotated, run_child, stop_note,
                          write_rows)

SUMMARY_FIELDS = ["version", "scenario", "seed", "events", "segment", "n", "min_ns", "p50_ns",
                  "p95_ns", "p99_ns", "p999_ns", "max_ns", "mean_ns", "timer_overhead_ns",
                  "status", "note"]
QUANTILE_FIELDS = ["version", "scenario", "seed", "events", "segment", "percentile",
                   "latency_ns"]
PERCENTILES = [float(p) for p in range(101)] + [99.9]
EDGE = 1000                           # first / last 1,000 events
SEGMENTS = ["all", f"first_{EDGE}", f"last_{EDGE}"]


def timer_overhead_ns(n=20_000):
    clock = time.perf_counter_ns
    gaps = []
    for _ in range(n):
        t0 = clock()
        gaps.append(clock() - t0)
    gaps.sort()
    return gaps[n // 2]


def child(path, version):
    events, _ = load_timed(path)
    cls = book_class(version)
    overhead = timer_overhead_ns()

    emit(start=["warm-up"])
    book = cls()
    process = book.process_event
    gc.collect()
    gc.disable()
    for event in events:
        process(event)
    gc.enable()
    emit(stop=["warm-up"])
    del process, book

    n = len(events)
    lat = array("q", bytes(8 * n))
    emit(start=["latency"])
    book = cls()
    process = book.process_event
    clock = time.perf_counter_ns
    gc.collect()
    gc.disable()
    for i, event in enumerate(events):
        t0 = clock()
        process(event)
        lat[i] = clock() - t0
    gc.enable()
    emit(stop=["latency"])

    segments = {"all": lat, f"first_{EDGE}": lat[:EDGE], f"last_{EDGE}": lat[-EDGE:]}
    out = {}
    for name, values in segments.items():
        values = sorted(values)
        out[name] = {"n": len(values), "mean": sum(values) / len(values),
                     "quantiles": [nearest_rank(values, p) for p in PERCENTILES]}
    emit(result={"segments": out, "timer_overhead_ns": overhead})


def run(cfg):
    summary_csv = cfg.out / "latency_summary.csv"
    quantile_csv = cfg.out / "latency_quantiles.csv"
    write_rows(summary_csv, SUMMARY_FIELDS, [])
    write_rows(quantile_csv, QUANTILE_FIELDS, [])
    manifest = {d["dataset"]: d for d in read_manifest(cfg)}
    for i, (scenario, m) in enumerate(cfg.latency_cells):
        ds = manifest[dataset_name(scenario, m, cfg.diag_seed, 1000)]
        for version in rotated(VERSIONS, i):
            key = {"version": version, "scenario": scenario, "seed": ds["seed"], "events": m}
            got = {}
            stopped = run_child("bench_latency.py", [ds["file"], version], cfg.time_limit,
                                lambda msg: got.update(msg.get("result", {})) and False)
            summary, quantiles = [], []
            if stopped:
                note = stop_note(stopped, stopped["step"] or ["latency"], cfg.time_limit)
                for seg in SEGMENTS:
                    summary.append({**key, "segment": seg, "status": "stopped", "note": note})
            else:
                for seg, s in got["segments"].items():
                    q = dict(zip(PERCENTILES, s["quantiles"]))
                    summary.append({**key, "segment": seg, "n": s["n"], "min_ns": q[0.0],
                                    "p50_ns": q[50.0], "p95_ns": q[95.0], "p99_ns": q[99.0],
                                    "p999_ns": q[99.9], "max_ns": q[100.0],
                                    "mean_ns": f"{s['mean']:.1f}",
                                    "timer_overhead_ns": got["timer_overhead_ns"],
                                    "status": "ok", "note": ""})
                    quantiles += [{**key, "segment": seg, "percentile": p, "latency_ns": v}
                                  for p, v in zip(PERCENTILES, s["quantiles"])]
            append_rows(summary_csv, SUMMARY_FIELDS, summary)
            append_rows(quantile_csv, QUANTILE_FIELDS, quantiles)
            print(f"  latency {ds['dataset']:34s} {version:8s} "
                  f"{'STOPPED' if stopped else 'ok'}", flush=True)
    print(f"  wrote {rel(summary_csv)}, {rel(quantile_csv)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", nargs=2, required=True)
    args = parser.parse_args()
    child(*args.child)


if __name__ == "__main__":
    main()
