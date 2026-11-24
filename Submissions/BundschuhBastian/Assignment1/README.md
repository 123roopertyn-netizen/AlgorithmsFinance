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
bench/                timing, latency, memory, counts, liquidation (Phase 6)
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
- **Timing** (`bench/bench_time.py`, Phase 6a). `time.perf_counter` around the replay loop only;
  the garbage collector stays **enabled** (default Python behaviour); `gc.collect()` runs before each
  replay, outside the timed region, so that every replay starts from the same heap state. Each run
  parses its file once (gzip + JSON, saved as `parse_seconds`, not part of the replay time). Every
  replay (warm-up and the 5 timed ones) uses a fresh empty book; results are discarded, not stored.
  Throughput = events divided by the median replay seconds (the single measurement if
  `repeats=1`). Output: `results/time_raw.csv` (one row per replay; the median of the run is on every
  row of that run) and `results/env.json` (Python, macOS, machine, git commit, constants).
  *Change record:* the first draft of these rules disabled `gc` during replays. Bastian decided to
  keep it enabled; a first benchmark run started with `gc` disabled was stopped after 33 runs
  (the 1,000-event streams and the first 10,000-event run) and its files were discarded, so no
  reported number comes from it.
  *Incident, run 1 (machine state):* the first full 6a grid showed Version B on `buildup` with
  100,000 events at about 0.20 s for seeds 42 and 43 and about 0.09 s for seed 44, each stable inside
  its own run. The code and the data did not change between those runs, so the machine changed state
  (Bastian was using it; it may also have been on battery). That file is kept unchanged as evidence
  (`results/time_raw_run1.csv`, `results/env_run1.json`) and no reported number comes from it. Run 1
  did not record the start time or the power state, so the cause is not proven. Changes for run 2:
  (1) every row has `start_utc` (start of its run), `power_source` (`ac`/`battery`),
  `battery_percent` and `low_power_mode` (read with `pmset`), and `env.json` has `power_at_start`;
  (2) a **canary** runs before and after each block of runs (a block = all runs of one scenario and
  one event count): Version B, `mixed`, 100,000 events, seed 42, warm-up + 5 repeats, same rules as
  every run, saved in `results/canary_raw.csv` with `block` and `canary_point`. If the canary
  median differs between points, or from the start, the runs in between were taken on a machine in a
  different state and are not comparable; they are re-run, not corrected. (3) The whole grid is run
  again into a new `results/time_raw.csv`. The machine must be on AC power, Low Power Mode off, and
  not used during the run.
- **Instrumented runs, Phase 6b** (`bench/bench_latency.py`, `bench_memory.py`, `bench_counts.py`)
  are separate runs, never part of the primary timing, one after the other, under the same
  conditions as timing run 2: AC power, Low Power Mode off, machine idle. Every result row has
  `start_utc`, `power_source`, `battery_percent`, `low_power_mode`. Each module runs in blocks (one
  module and one event count) with the canary of run 2 before and after the block
  (`results/canary_raw.csv`); a block whose canary medians differ clearly is repeated. Streams: seed
  42; latency and memory 10,000 and 100,000 events, counters 1,000 and 10,000 (small M). A runs at
  100,000 events only if its timing run at that size and scenario finished with a median below 60 s
  (same threshold as rule 3); otherwise `not_run`. No instrumented run uses the 1,000,000-event files.
  Each run is a child process with the 600 s limit.
- **Latency** (`results/latency_summary.csv`). `perf_counter_ns` before and after every `process`
  call, gc enabled as in the timing runs; the cost of the timer pair is measured and reported
  (`timer_overhead_ns`), not subtracted. Nearest-rank percentiles: for n sorted values, the p-th
  percentile is the value at rank ceil(p/100 * n), 1-based (p50, p95, p99). Rows per event type
  (`ALL`, `LIMIT`, `CANCEL`, `MARKET_SELL`; no row if the window holds none of that type) and per
  window: `all`, `first1000`, `last1000` (the first and the last 1,000 events of the stream, to see
  how latency changes while the book grows; asked for `buildup` and `crowded`, computed for every
  scenario), plus 20 equal chunks in order (`latency_by_position.csv`). It is processing time per
  event only, not queueing, not 1 / throughput.
  *gc test* (`python -m bench.bench_latency --gc-test`, `results/latency_gc_test.csv`): B on `buildup`
  with 100,000 events, gc off and gc on, each twice, canary before and after. Max latency: gc on
  13.1 ms and 12.4 ms (at events 91,228 and 44,613, with a second spike of 7.1 and 7.8 ms), gc off
  0.82 ms and 0.88 ms. So the ~12 ms spikes are garbage-collector pauses (full collections while
  the book holds ~10^5 live records). With gc off the largest remaining events sit at 10,922,
  21,845, 43,690 and 87,381, a doubling pattern that fits a dict or list resize; that explanation
  was not tested.
- **Memory** (`results/memory.csv`). `tracemalloc`, started after the events are loaded, with a fresh
  book. Counted: Python allocations made during the replay that are still alive at the moment of
  measuring: book structures, the order index, the current result dict and fill list (discarded
  after each event), temporary objects. `peak_bytes` is the maximum of that sum during the replay
  (`reset_peak` at the start); `final_bytes` is the sum after the last event ("after replay").
  Also every 10% of the events (`checkpoints_bytes`) and, for `insert_then_cancel`, after the
  insertions. Not counted: the input event list, the interpreter, native memory, allocator slack
  and fragmentation. No trade history is kept (SPEC D16). tracemalloc slows the replay, so no
  timing comes from these runs, and the numbers are not total process memory.
- **Counters** (`results/counters.csv`). The engines are wrapped, not modified. A: records examined by
  the scans (`scan_is_live`, `scan_best_index`, `scan_cancel`). B: elements moved when a price
  level is inserted or deleted in the sorted price list, levels dropped, compactions and records
  moved. Both: `fills`, `levels_visited` (distinct fill prices per event, summed).
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
