# Assignment 1: Build and benchmark a limit order book

Submission of Bastian Bundschuh for *Algorithms in Finance* (take-home exercise, due
26 November 2026, 18:00). Task and data: `docs/ASSIGNMENT_README.md`,
`docs/AlgorithmsFinance_Exercise1.pdf`.

**Status: Phase 1 (tests written, red).** Engines are stubs; sections marked TODO
are filled in later phases.

A sequential, single-venue BTC limit order book in Python with price-time (FIFO) priority,
in two versions:

| Version | Data organization | File |
|---|---|---|
| A (baseline) | list of orders per side, found by scanning | `lob/version_a.py` |
| B (revision) | price levels with FIFO queues + order index (planned) | `lob/version_b.py` |

All rules, units, result formats and decisions: **`SPEC.md`**.
Model boundaries: one venue, no fees, balances, hidden orders, self-trade checks or
network delay; synthetic data only; not a production trading system.

## Setup

Python 3.11 or newer. From this folder (`Submissions/BundschuhBastian/Assignment1/`):

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

## Commands

| Step | Command | Writes |
|---|---|---|
| Check supplied data | `.venv/bin/python tools/verify_data.py` | `results/data_checksums.json` |
| Tests | `.venv/bin/python -m pytest -q` | nothing |
| Replay a file | `.venv/bin/python -m lob.replay data/worked_example.jsonl --version A` | stdout |
| Generate data | TODO (Phase 5: `bench/make_data.sh`) | `data/generated/` (not committed) |
| Benchmarks | `bash bench/run_all.sh` (Phase 6; several hours, see below) | `results/` |
| Dashboard | TODO (Phase 7) | loads `results/` only |

## Tests

`.venv/bin/python -m pytest -q`: 328 tests; every test with a `book` runs for A and B.
Every event in a test goes through `tests/helpers.py::step()`, which checks invariants
I1-I7 and price-time order after that event (see `SPEC.md` section 4).

| File | What it covers |
|---|---|
| `tests/test_validation.py` | 86 malformed events (non-dict, missing fields, `None`, `True`, floats, `nan`/`inf`, unhashable values, wrong case, duplicate live ids), first-failing-check order (D9), seq bookkeeping, id reuse after fill/cancel, extra fields ignored, no shared objects with the caller |
| `tests/test_matching.py` | empty book, one order, sell smaller/equal/larger than depth, FIFO at one price, several prices, partial fill keeps priority, id spelling vs arrival, 1000-order queue, crossing limit buys/sells at resting prices, equality cross, emptied level recreated, huge integers |
| `tests/test_cancel.py` | cancel before/after partial/full fill, repeat/unknown/near-miss ids, head/middle/tail of queue, only order at best price, cancel everything, add/cancel churn |
| `tests/test_worked_and_files.py` | worked example (file and by hand), replay command, reader edge cases, the five supplied 10,000-event files with outcomes derived from the generator |

Phase 1 red run (stubs): `docs/test_logs/phase1_red.txt`.

## Expected worked-example output

`data/worked_example.jsonl`: makers fill `b1:1, b2:1, b3:3, b4:1` BTC; 4 BTC stay on `b4`;
the ask `a1` is unchanged; gross value 3,594,000,000,000,000 tick-units = **359,400.00 USD**.
Full expected result: `data/worked_expected.json`. TODO: paste the replay output here.

## Folder layout

```
SPEC.md               rules + decisions D1-D19 (Phase 0)
lob/                  common.py (reader, reasons, display), version_a.py, version_b.py, replay.py
tests/                hand-calculated, worked example, invariants, A-vs-B equivalence
tools/                verify_data.py, own small generator (Phase 4)
bench/                timing, latency, memory, counters, liquidation (Phase 6)
results/              saved raw results + environment metadata
dashboard/            Streamlit app that only loads results/ (Phase 7)
data/                 supplied 10,000-event files + worked example (unchanged)
docs/                 course assignment README and slides (unchanged copies)
generate_orders.py    course generator (unchanged)
MANIFEST.json         course checksum manifest (unchanged)
AI_LOG.md             accepted / corrected / rejected AI suggestions
```

## Benchmark limits and run rules (declared before any benchmark was run)

These rules apply to Version A and Version B alike, to every scenario, seed and event count.
They were fixed by Bastian before the first benchmark run (commit of this section: see
`git log -- README.md`). No missing value is ever invented or extrapolated.

1. **Time limit: 10 minutes (600 s) per single replay.** A replay is one pass of one event file
   through one fresh, empty book. It applies to every kind of run (timing, latency, memory,
   counters). A replay that reaches the limit is killed and recorded as `status=stopped`, with
   the limit, the elapsed time at the kill and the number of events processed so far. Its
   remaining repeats are skipped (not run, not estimated).
2. **Repeats.** The first replay of a (version, file) pair is always timed.
   - If it takes **60 s or less**, it counts as the warm-up and is followed by **5 timed
     replays**. All 5 raw times and their median are saved.
   - If it takes **more than 60 s**, it is used as the one and only measurement: no warm-up, no
     further replays, `repeats=1` is recorded.
   Every replay starts from a fresh empty book. Parsing the file is timed separately from the
   replay.
3. **Version A on 1,000,000-event files.** A runs on a 1,000,000-event file only if A on the
   100,000-event file of the same scenario (seed 42) finished with a replay time **below 60 s**.
   Otherwise the run is recorded as `status=not_run` with the reason (A at 100,000 events took
   X s, or was stopped). Version B runs on all files.

Result statuses in the saved tables: `ok`, `stopped` (rule 1), `not_run` (rule 3 and the
instrumented-run rule below), `error` (the run crashed; the error text is saved, nothing is
estimated). The numbers 60 s and 600 s are the declared constants in `bench/common.py`.

Details of how the rules are applied (also fixed before the first run):

- **Enforcement.** Every run is a child process. The parent measures wall-clock time and, at 600 s,
  stops the child. Events processed at the stop = the `seq` of the event being processed (the
  generator numbers events 1, 2, 3, ...). Stops during a liquidation sale have no event count.
- **Timing.** `time.perf_counter` around the replay loop only; `gc.collect()` before and
  `gc` disabled during each replay (like `timeit`); results are discarded, not stored; parsing
  (gzip + JSON) is timed separately and saved as `parse_seconds`. Throughput = events divided by
  the median replay seconds (the single measurement if `repeats=1`).
- **Instrumented runs** (latency, `tracemalloc` memory, operation counters) are separate runs and
  never part of the primary timing. They use seed 42 and 10,000 events (counters also 1,000) for A
  and B, and 100,000 events for B. A runs at 100,000 events only if its timing run at that size
  and scenario finished with a median below 60 s (same threshold as rule 3); otherwise `not_run`.
  No instrumented run uses the 1,000,000-event files.
- **Latency.** `perf_counter_ns` before and after every `process` call; the cost of the timer pair
  is measured and reported, not subtracted. Percentiles by the nearest-rank rule: for n sorted
  values, the p-th percentile is the value at rank ceil(p/100 * n), 1-based (p50, p95, p99).
  Early versus late: first 5% and last 5% of the events, and 20 equal chunks in order.
- **Memory.** `tracemalloc`, events loaded before tracing starts (so the input is not counted);
  counted are the book, the result dicts and fill lists while alive, and temporary objects. No
  trade history is kept. Not counted: interpreter, native memory, allocator slack.
- **Liquidation.** Book = first N BUY limits of the generator stream, N in {1,000; 10,000;
  100,000}, with 1,000 price levels (`buildup`) or 4 (`crowded`); sells of ceil(10%), 100% and
  200% of the bid quantity; fresh book per trial; only the sell is timed (build time saved
  separately). If a trial is stopped at the limit, the remaining sale sizes of the same book are
  `not_run`, because they would repeat the same construction. Rule 2 applies per (version, book,
  sale size), with one trial (build + sell) as the "replay".
- **Queue concentration.** `buildup`, 100,000 events, seed 42, 4 / 16 / 64 / 256 / 1,000 / 4,000
  price levels; price-time correctness by A-vs-B comparison on 5,000-event versions of the same.


## Measured-data definitions

TODO (Phase 6).

## Submitted code version

TODO: commit identifier.
