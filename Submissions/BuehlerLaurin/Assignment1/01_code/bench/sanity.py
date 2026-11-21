"""Phase 3 sanity, not a benchmark: one A/B replay per supplied 10k stream.

Run: python run.py bench.sanity
No warm-up, repeats or speed conclusions. Counters/tracing/profiling are off.
The shared harness times fresh setup separately from pre-parsed engine replay.
The runner retains returned results for an untimed comparison; books retain no
history. Result-list construction is included equally for A and B.
"""
import json
from pathlib import Path
from time import perf_counter

from bench.harness import new_run_dir, time_repeats
from lob import METHODS
from lob.replay import read_events

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ("buildup", "crowded", "mixed", "sweep", "cancel_churn")
LABEL = "sanity, not a benchmark"


def main():
    directory = new_run_dir(tag="phase3_sanity_not_benchmark")
    report = {"label": LABEL, "warmups": 0, "repeats": 1, "counters": False,
              "gc": "enabled (unchanged)", "comparison": "every result and final canonical book, outside timing",
              "boundary": "pre-parsed replay incl. returned result-list construction; no parsing/setup/checking/printing",
              "rows": []}
    print(LABEL)
    for scenario in SCENARIOS:
        path = ROOT / "06_data/supplied" / f"{scenario}_10000.jsonl.gz"
        start = perf_counter()
        events = list(read_events(path))
        parse_s = perf_counter() - start
        assert len(events) == 10000, scenario
        captured = {}
        row = {"scenario": scenario, "events": len(events), "parse_s": parse_s}
        for version in ("A", "B"):
            factory = METHODS[("lob", version)]

            def replay(book):
                return book, [book.process(event) for event in events]

            def capture(result):
                captured[version] = result

            timing = time_repeats(factory, replay, warmup=0, repeats=1, check=capture)
            row[version] = {"setup_s": timing["prep_s"][0], "replay_s": timing["run_s"][0],
                            "parse_setup_replay_s": parse_s + timing["total_s"][0]}
        a, a_results = captured["A"]
        b, b_results = captured["B"]
        assert b.counters is None
        assert len(a_results) == len(b_results) == len(events)
        for event, ra, rb in zip(events, a_results, b_results):
            assert ra == rb, ("A/B result divergence", scenario, event, "A", ra, "B", rb)
        assert a.snapshot() == b.snapshot(), ("A/B final-book divergence", scenario, events[-1])
        row["result_differences"] = 0
        row["final_book_equal"] = True
        report["rows"].append(row)
        print(f"{scenario}: parse={parse_s:.6f}s; A setup={row['A']['setup_s']:.6f}s "
              f"replay={row['A']['replay_s']:.6f}s; B setup={row['B']['setup_s']:.6f}s "
              f"replay={row['B']['replay_s']:.6f}s; result differences=0; final book equal")
        # Release previous results and books outside the next timing region.
        del a, b, a_results, b_results, captured, events
    (directory / "sanity.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {directory}")
    print("RESULT: PASS (sanity, not a benchmark; 50000 event results and five final books agree)")


if __name__ == "__main__":
    main()
