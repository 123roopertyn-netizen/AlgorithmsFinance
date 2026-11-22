"""Planning extrapolations from M=1000 smoke only; never executes an engine."""
import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path

from bench.catalog import load
from bench.core import VERSIONS
from bench.run_all import MODES, PARTS, cases_for, rows_from


def growth(case, version, high=False):
    """Explicit cost-driver assumptions, not a fitted/scientific speed claim."""
    ratio = case["size"] / 1000
    if version == "A" and case["part"] != "churn" and case["workload"] != "cancel_churn":
        return ratio**2  # B and/or F grow at fixed scenario mix; A repeatedly scans B
    if case["part"] == "adversarial" and case["workload"] == "deep_book":
        if version in ("B1", "B2"):
            return ratio**2 if high else ratio  # new-level O(P) shift term vs per-event overhead
        if version == "B3":
            return ratio * math.log2(max(2, case["size"])) / math.log2(1000)
    return ratio  # fixed price bound/mix, or constant-live-book cancellation churn


def phase_times(directory, case_id, version, mode):
    path = directory/"cells"/f"{case_id}__{version}__{mode}.log"
    phases = defaultdict(float)
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("action") == "end":
            phases[event["bench_phase"]] += event["elapsed_s"]
    return phases


def build_estimate(directory):
    cells = rows_from(directory/"cells.csv")
    summaries = rows_from(directory/"summary.csv")
    catalog = load()
    smoke = cases_for("smoke", catalog)
    templates = {(c["part"], c["label"]): c for c in smoke}
    cell_map = {(r["case_id"], r["version"], r["mode"]): r for r in cells}
    medians = {(r["case_id"], r["version"], r["phase"]): float(r["median_s"])
               for r in summaries if r["status"] == "ok"}
    details = []
    for part in PARTS:
        for case in cases_for(part, catalog):
            template_part = "official" if part == "million" else case["part"]
            sample = templates[(template_part, case["label"])]
            for version in VERSIONS:
                variants = []
                for multiplier in (0.5, 1.0, 2.0, 3.0):
                    for high in (False, True):
                        factor = growth(case, version, high) * multiplier
                        input_ratio = case["bytes"] / sample["bytes"]
                        phases = phase_times(directory, sample["id"], version, "memory" if part == "churn" else "timing")
                        raw_modes = ("memory",) if part == "churn" else MODES
                        total, timing_stopped = 0.0, False
                        for mode in raw_modes:
                            if timing_stopped and mode != "timing":
                                continue  # recommended --skip-after-stop; explicit not_run rows
                            observed = phase_times(directory, sample["id"], version, mode)
                            wall = float(cell_map[(sample["id"], version, mode)]["wall_s"])
                            overhead = max(0.0, wall - sum(observed.values()))
                            total += overhead + input_ratio * (observed.get("parse", 0) + observed.get("input_hash", 0))
                            total += observed.get("sample_check", 0)
                            if mode == "timing":
                                construction = medians[(sample["id"], version, "construction")]
                                construction *= factor if case["part"] == "liquidation" else 1
                                replay = medians[(sample["id"], version, "replay")] * factor
                                if construction > 600:
                                    total += 600; timing_stopped = True
                                elif replay > 600:
                                    total += construction + 600; timing_stopped = True
                                else:
                                    total += 6 * (construction + replay)
                            else:
                                for name in ("construction", "latency", "memory_peak", "memory_curve", "counts"):
                                    if name not in observed:
                                        continue
                                    scale = 1 if name == "construction" and case["part"] != "liquidation" else factor
                                    predicted = observed[name] * scale
                                    total += min(600, predicted)
                                    if predicted > 600:
                                        break
                        variants.append(total)
                details.append({"part": part, "case_id": case["id"], "version": version,
                                "size": case["size"], "seed": case["seed"],
                                "planning_low_s": min(variants), "planning_high_s": max(variants)})
    parts = []
    for part in PARTS:
        selected = [r for r in details if r["part"] == part]
        row = {"part": part}
        for group, versions in (("A", ("A",)), ("B", ("B1", "B2", "B3"))):
            for bound in ("low", "high"):
                row[f"{group}_{bound}_s"] = sum(r[f"planning_{bound}_s"] for r in selected if r["version"] in versions)
        parts.append(row)
    # Show the unconstrained replay predictions that motivate A's first-trial stops.
    baseline = []
    for size in (100000, 1000000):
        for scenario in ("buildup", "crowded", "mixed", "sweep", "cancel_churn"):
            sample = templates[("official", scenario)]
            case = {**sample, "size": size}
            estimate = medians[(sample["id"], "A", "replay")] * growth(case, "A")
            baseline.append({"scenario": scenario, "size": size,
                             "unconstrained_replay_s": estimate, "first_attempt_cap_s": 600,
                             "predicted_stop": estimate > 600})
    return {"basis": str(directory), "label": "planning estimates only; NOT measured large runs",
            "assumptions": ["M=1000 seed42 only; fixed workload B/P/F relationships from generators",
                            "A growing-book scenarios quadratic; constant-live churn linear",
                            "B variants approximately linear at bounded price count; deep-book B1/B2 linear-to-quadratic",
                            "0.5x..3x sensitivity; not confidence bounds; stop-policy discontinuities possible",
                            "600s per engine phase; skip other instrumentation only after a timing stop",
                            "startup/parse included; latency postprocessing/allocator/GC/cache scaling uncertain"],
            "parts": parts, "baseline_large_replays": baseline, "cells": details}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    report = build_estimate(args.run_dir)
    (args.run_dir/"runtime_estimate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Phase 4 runtime planning (M=1000 smoke extrapolation)", "",
             "These are planning ranges, not measurements, confidence intervals or guaranteed bounds.",
             "Per-phase 600s stopping and --skip-after-stop are included; all B repeats are unchanged.", "",
             "| Part | A hours | B1+B2+B3 hours | Total hours |", "|---|---|---|---|"]
    for row in report["parts"]:
        lo, hi = row["A_low_s"] + row["B_low_s"], row["A_high_s"] + row["B_high_s"]
        lines.append(f"| {row['part']} | {row['A_low_s']/3600:.2f}-{row['A_high_s']/3600:.2f} | "
                     f"{row['B_low_s']/3600:.2f}-{row['B_high_s']/3600:.2f} | {lo/3600:.2f}-{hi/3600:.2f} |")
    lines += ["", "A predicted single-replay seconds before the 600s cap:", "",
              "| Scenario | M | Extrapolated seconds | Predicted first-attempt stop |", "|---|---|---|---|"]
    for row in report["baseline_large_replays"]:
        lines.append(f"| {row['scenario']} | {row['size']} | {row['unconstrained_replay_s']:.1f} | {row['predicted_stop']} |")
    lines += ["", "Assumptions:", ""] + ["- "+text for text in report["assumptions"]]
    lines += ["", "Recommendation: run the three B variants first, then A in a separate resumable batch.",
              "The Q7 construction/rebuild trials dominate the full baseline schedule; leave them overnight.",
              "Do not silently reduce B warm-up/repeats. A's first over-limit trial stops the cell and omits its remaining repeats.",
              "Use --skip-after-stop to avoid repeating known-stopped A cells in slower instrumentation; those modes are not_run, not invented results.",
              "Review the first completed 10k cells before launching 100k/1M if the extrapolation is off."]
    text = "\n".join(lines)+"\n"
    (args.run_dir/"runtime_estimate.md").write_text(text, encoding="utf-8")
    Path("00_docs/RUNTIME_ESTIMATE.md").write_text(text, encoding="utf-8")
    print(text)
    print("RESULT: PASS (runtime estimates only; no engine replay executed)")


if __name__ == "__main__":
    main()
