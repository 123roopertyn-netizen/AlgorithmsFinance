# Assignment 1: limit order book

This project implements and measures two Python versions of a sequential,
single-venue BTC limit order book. The current checkpoint contains the
test-first contract and deliberate implementation stubs; matching logic has
not yet been implemented.

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

1. Specification and independent tests: in progress.
2. Transparent baseline: not implemented.
3. Revised implementation: not implemented.
4. Measurements and dashboard: not started.

