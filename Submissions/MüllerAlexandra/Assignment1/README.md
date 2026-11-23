# Assignment 1: limit order book

This project implements and measures two Python versions of a sequential,
single-venue BTC limit order book. The transparent list-based Version A is
implemented and verified. Version B remains a deliberate implementation stub
until Version A is measured and the revision is justified.

## Environment

- Python 3.12.10
- Dependencies pinned in `requirements.txt`

From `Submissions/MüllerAlexandra/Assignment1`:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe -m pip install -e .
..\.venv\Scripts\python.exe -m pytest
```

The existing course-lab virtual environment is one directory above this
project. A clean environment may instead install the same requirements in its
own virtual environment.

## Test-first evidence

Use the evidence runner from the project root:

```powershell
..\.venv\Scripts\python.exe scripts\00_run_tests.py --stage 01_before_implementation
```

The runner records the exact command, output, exit code, UTC time, Python and
pytest versions, platform, Git branch and commit, and pre-run working-tree
state. It refuses to overwrite an existing run.

The first run is expected to collect successfully and fail because the two
order-book classes deliberately raise `NotImplementedError`. The original
pre-implementation run is preserved, followed by a reviewed run after a
sequence-state test was strengthened. Passing tests are not expected until
the corresponding implementation checkpoint.

## Public interface

Both `BaselineOrderBook` and `RevisedOrderBook` provide:

- `process_event(event)`
- `add_limit_order(event)`
- `cancel_order(event)`
- `fill_market_sell(event)`
- `inspect_book()`

The two versions accept identical event dictionaries and return plain
dictionaries. Book inspection is canonical: bids by decreasing price and
arrival sequence, followed by asks by increasing price and arrival sequence.

## Supplied data

The files under `data/supplied/` are byte-for-byte copies of the assignment
package's worked example and five 10,000-event synthetic workloads. Larger
files belong under `data/generated/` and are not committed.

## Development status

1. Specification and independent tests: strengthened by pre-revision critical review.
2. Transparent baseline: implemented and passing its applicable contract tests.
3. Revised implementation: not implemented.
4. Throughput harness: smoke-verified; formal measurements not started.
5. Per-event latency harness: smoke-verified; formal measurements not started.
6. Memory, experiment matrix, and dashboard: not implemented.

Validate the baseline against all supplied 10,000-event streams:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\03_validate_supplied.py --version baseline
```

The baseline deliberately uses a list of individual resting orders. It scans
and sorts that list during matching and scans it during cancellation. This is
the transparent Version A to preserve before a measured data-organization
revision.

## Non-formal benchmark smoke check

The smoke check exercises input parsing, checksumming, fresh-state warm-up and
repeats, exclusive JSON persistence, and environment metadata on only the
first 100 events. It is harness verification, not a formal performance result:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\04_benchmark.py `
  --version baseline `
  --input data\supplied\cancel_churn_10000.jsonl.gz `
  --max-events 100 `
  --warmups 1 `
  --repeats 2 `
  --out evidence\05_benchmark_smoke\05_baseline_cancel_churn_100.json
```

The command refuses to overwrite an existing result. Choose a new explicitly
labelled output path to repeat the smoke check.

The separate latency smoke check performs one untimed replay on its own book,
then records each event on a new empty book. It retains raw nanoseconds and
summarizes overall, per-event-type, and early/late-window latency:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\04_benchmark.py `
  --phase latency `
  --version baseline `
  --input data\supplied\cancel_churn_10000.jsonl.gz `
  --max-events 100 `
  --warmups 1 `
  --repeats 5 `
  --out evidence\06_latency_smoke\06_baseline_cancel_churn_100.json
```

Every measured repeat uses a new empty book, and raw records retain both repeat
and event indices. Like the throughput smoke check, this verifies
instrumentation and persistence; its 100-event timings are not formal
performance evidence.

