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
| Benchmarks | TODO (Phase 6) | `results/` |
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

Result statuses in the saved tables: `ok`, `stopped` (rule 1), `not_run` (rule 3).
A single replay of 60 s or less is "fast"; the exact numbers (60 s, 600 s) are the declared
constants of `bench/`.

## Measured-data definitions

TODO (Phase 6).

## Submitted code version

TODO: commit identifier.
