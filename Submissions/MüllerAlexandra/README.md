# Membership search lab

This project compares three ways to answer an ordered batch of integer-ID
membership queries:

1. explicitly implemented linear search;
2. explicitly implemented binary search on a library-sorted copy; and
3. membership in a standard-library hash set.

The original binary search is recursive. The required revised version is
iterative, and both versions are preserved and measured. Every public method
returns one real Boolean per query in the original query order and leaves the
given ID array unchanged.

## Requirements

- Python 3.12 (measurements were developed with Python 3.12.10)
- Dependencies pinned in `requirements.txt`

Docker was not used because packaging is optional for this lab.

## Setup on Windows PowerShell

From `Submissions/MüllerAlexandra`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The repository's root `.gitignore` excludes `.venv`, caches, and compiled
Python files.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Expected result: `58 passed`. The tests apply the same specification to linear
search, original recursive binary search, revised iterative binary search, and
hash-set membership. Cases cover empty IDs and queries, one entry, duplicates,
unsorted input, negative and zero IDs, present and absent queries, output
order, Boolean output types, and preservation of the input array. Additional
tests cover deterministic synthetic data, benchmark interfaces, measurement
smoke runs, and dashboard data transformations.

The first test run occurred before implementation: 27 algorithm tests failed
with `NotImplementedError`, while 12 generator tests passed. After the original
three implementations, all 39 tests passed. The final suite has 58 passing
tests. See `DEVELOPMENT_NOTES.md` for the hand trace, revision, and AI-use log.

## Synthetic data

`synthetic_data.py` is independent of algorithms, measurement, and rendering.
It uses a private seeded `random.Random` instance. Each saved result records:

- input length and query count;
- seed;
- requested and actual hit rate;
- query scenario; and
- duplicate policy.

The default benchmark uses `duplicate_policy="allow"`, which deliberately
generates IDs from a smaller value range and therefore includes duplicates.
A genuinely mixed query batch is impossible when `q=1`, so that one
combination is explicitly omitted and recorded in the saved settings. Mixed
queries are included for `q=100`.

## Benchmark

First commit the algorithms, tests, generator, benchmark, dashboard, dependency
file, and documentation. Supply that code commit's hash to the measurement
command:

```powershell
.\.venv\Scripts\python.exe benchmark.py --code-version <MEASURED_CODE_COMMIT>
```

Do not include the angle brackets. The default fixed matrix is:

- `n` in `{1,000, 10,000, 100,000}`;
- `q` in `{1, 100}`;
- all-present and all-absent batches for both query counts;
- 50% mixed batches for `q=100`;
- duplicate policy `allow`; and
- base seed `20261120`.

The script warms up each method, then performs five repeats and reports the
median. Calls too short for useful direct timing are executed together and
divided by the number of calls; the loop count is stored with every record.
Every method/version receives the identical generated IDs and ordered queries
for a configuration.

Three elapsed quantities are measured independently with
`time.perf_counter()`:

- **preparation:** seconds per preparation; sorting or set construction is
  included, while linear search has no prepared structure;
- **query batch:** seconds per complete ordered query batch against the
  prepared state; and
- **total:** seconds per fresh preparation followed by one complete query
  batch.

The independent total can differ slightly from preparation plus query medians.
Data generation, tests, printing, AI calls, dashboard rendering, and memory
tracing are excluded. Fresh state is constructed inside every combined timing
call, so an earlier sorted copy or hash set is never treated as free.

Raw output is written to:

- `results/raw_benchmark.json` — raw repeats, medians, batching counts,
  generator settings, units and definitions, environment, and code version;
- `results/benchmark_summary.csv` — one flattened summary row per
  configuration and method/version.

## Memory measurement

Memory measurement is a separate run and is never mixed with timing. The input
and queries are generated before `tracemalloc.start()`, so their allocation is
excluded. Then a fresh preparation and complete query batch are run. The
prepared sorted copy or set and returned Boolean list remain alive when
`get_traced_memory()` reads current and peak traced bytes, so both are included.

`tracemalloc` reports traced Python allocations, not every native allocation,
and the measurement is not a direct proof of theoretical auxiliary-space
complexity. The dashboard displays current and peak values in KiB; the raw file
keeps bytes.

## Dashboard

Generate results first, then run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open the local URL shown by Streamlit (normally `http://localhost:8501`). The
dashboard loads `results/raw_benchmark.json`; changing filters never reruns a
benchmark. It shows separate preparation, query-batch, and total charts with
one curve per method/version, plus the memory table, raw repeats, loop counts,
seeds, settings, definitions, code version, and machine/Python details.

## Project files

- `algorithms.py` — original methods, preserved recursive binary search, and
  revised iterative binary search
- `synthetic_data.py` — deterministic input generation
- `benchmark.py` — timing, memory measurement, and saved result export
- `dashboard.py` — Streamlit result viewer
- `dashboard_data.py` — testable result-loading transformations
- `tests/` — shared behavioral and supporting tests
- `DEVELOPMENT_NOTES.md` — trace, revision rationale, and AI-use record
- `requirements.txt` — pinned direct dependencies
- `results/` — generated raw JSON and CSV measurements

## Interpretation limits

Passing tests provide evidence, not a proof of correctness. Runtime results
describe the recorded Python version, machine, host load, and measured code
version. They should not be generalized to every platform or input
distribution without further experiments.
