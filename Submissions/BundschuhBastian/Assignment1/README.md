# Assignment 1: Build and benchmark a limit order book

Submission of Bastian Bundschuh for *Algorithms in Finance* (take-home exercise, due
26 November 2026, 18:00). Task and data: `docs/ASSIGNMENT_README.md`,
`docs/AlgorithmsFinance_Exercise1.pdf`.

**Status: Phase 0 (setup and specification).** Engines are stubs; sections marked TODO
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

## Measured-data definitions

TODO (Phase 6).

## Submitted code version

TODO: commit identifier.
