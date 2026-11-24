# Assignment 1: limit order book

This project implements and measures two Python versions of a sequential,
single-venue BTC limit order book. The transparent list-based Version A is
implemented and measured. The indexed FIFO-price-level Version B is implemented
and passes the unchanged behavioral contract; its formal measurements remain
to be run.

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

The formal input plan contains 45 core configurations (five scenarios, three
event counts, and seeds 42, 43, and 44) plus one additional four-level buildup
stream for the controlled queue-concentration comparison. Generate missing
streams and verify all metadata and checksums outside timing with:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\06_prepare_inputs.py `
  --generate `
  --plan-out experiments\08_input_plan.json
```

The command refuses to replace the saved plan. Generated compressed streams
remain ignored; their small metadata files and the complete verified plan are
committed for reproducibility.

Formal tasks use a preregistered 60-second wall-clock limit per configuration,
identically for both implementations. The runner saves gzip-compressed raw
results only after validation and otherwise saves an explicit failure or
timeout status without inventing a measurement:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\07_run_formal.py `
  --version baseline `
  --resume
```

Filters such as `--phase`, `--scenario`, `--event-count`, `--seed`, and
`--task-id` support pilots and review. Formal execution begins only from a
committed runner checkpoint.

After completing the original 114-task matrix for both versions, an optional
one-million-event extension was defined separately. It uses seed 42, all five
workload families, throughput only, and the same warm-up, five repeats, and
60-second limit for both versions. Large generated inputs remain ignored; the
verified plan and metadata are retained:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\09_prepare_million_inputs.py --generate
..\.venv\Scripts\python.exe scripts\10_run_million.py --version baseline --resume
..\.venv\Scripts\python.exe scripts\10_run_million.py --version revised --resume
```

Extension results are stored below `results/extension_1m/` and are not counted
as part of the original formal matrix.

## Development status

1. Specification and independent tests: strengthened by pre-revision critical review.
2. Transparent baseline: implemented and passing its applicable contract tests.
3. Revised implementation: implemented; full 214-test suite passes.
4. Throughput: formal Version A matrix recorded.
5. Per-event latency: formal Version A representative matrix recorded.
6. Memory: formal Version A state and retained-output matrices recorded.
7. Formal input matrix: generated and checksum-verified; Version A recorded.
8. Timeout-aware formal runner: 114 Version A task statuses recorded.
9. Liquidation and diagnostic harness: Version A formal stress run recorded.
10. Dashboard: not implemented.
11. Optional one-million-event extension: test-first harness implemented;
    inputs and measurements not yet generated.

Validate the baseline against all supplied 10,000-event streams:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\03_validate_supplied.py --version baseline
```

Use `--version revised` to validate Version B against the same supplied
streams.

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

Memory is measured separately with input parsing completed before
`tracemalloc` starts. Run state-only and retained-output modes independently:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\05_measure_memory.py `
  --version baseline `
  --mode memory_state `
  --input data\supplied\cancel_churn_10000.jsonl.gz `
  --max-events 100 `
  --checkpoints 10 `
  --out evidence\07_memory_smoke\07_baseline_cancel_churn_100_state.json

..\.venv\Scripts\python.exe scripts\05_measure_memory.py `
  --version baseline `
  --mode memory_retained_output `
  --input data\supplied\cancel_churn_10000.jsonl.gz `
  --max-events 100 `
  --checkpoints 10 `
  --out evidence\07_memory_smoke\07_baseline_cancel_churn_100_retained_output.json
```

The additional buildup smoke record uses the same state-only command with
`buildup_10000.jsonl.gz`. These 100-event records verify boundaries, growth
samples, and persistence; their byte values are not formal A-versus-B results.

The separate stress command rebuilds a deterministic 1,000-maker, 100-level
bid book for every 10%, 100%, and 200% liquidation repeat. It also runs
correctness diagnostics on the five 1,000-event seed-42 workloads:

```powershell
$env:PYTHONPATH = "src"
..\.venv\Scripts\python.exe scripts\08_run_stress.py `
  --version baseline `
  --order-count 1000 `
  --price-levels 100 `
  --warmups 1 `
  --repeats 5 `
  --diagnostic-events 1000 `
  --out results\stress\baseline\10_stress_and_diagnostic.json.gz
```

