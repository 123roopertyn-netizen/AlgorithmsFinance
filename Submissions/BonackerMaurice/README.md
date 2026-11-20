# Search methods for integer IDs: Phase 1 lab (BonackerMaurice)

This project implements LinearSearch, BinarySearch on a sorted copy, and
hash-set membership under one specification. It includes tests written first,
a seeded synthetic-data generator, timing and memory measurements, and a
Streamlit dashboard for reviewers.

**Commit to be audited:** `<fill in>`. This is the commit whose `01_code/` was
measured. Later commits only add results and docs; `01_code/` is identical,
which the source fingerprint in the dashboard verifies.

**Committed results:** `02_results/<fill in>/`

## Run it

Use Python 3.13. Run every command from **`01_code/`**:

```bash
cd Submissions/BonackerMaurice/01_code
python -m pip install -r requirements.txt
python -m pytest                           # expected: 674 passed
python -m tests.mutation_check             # expected: 10/10 mutants killed
python -m benchmarks.run                   # tests, timing, memory -> ../02_results/<run_id>/ (about 1-2 min)
python -m streamlit run dashboard/app.py   # http://localhost:8501
```

Optional commands:

```bash
python -m benchmarks.run --quick                                # small grid, about 15 s (gitignored)
python -m datagen.generator --n 1000 --q 100 --scenario mixed   # inspect one dataset
python -m datagen.generator --n 1000 --q 100 --scenario mixed --out data.json
```

Use `python -m streamlit`, not `streamlit`: on Windows, application-control
policies can block the `streamlit.exe` launcher. No file needs editing to run
the tests, the benchmarks or the dashboard.

## Folder layout

```
00_docs/      DEVLOG.md (process log), REVISIONS.md (v1 -> v2), AI_USAGE.md
01_code/      requirements.txt, pytest.ini, and the Python packages:
  search_algos/   linear.py, binary.py, hashset.py, validation.py, registry.py
  datagen/        generator.py
  benchmarks/     config.py, timing.py, memory.py, environment.py, run.py
  dashboard/      app.py, data.py
  tests/          test_search.py, test_generator.py, test_benchmarks.py, test_dashboard.py, mutation_check.py
02_results/   saved benchmark runs, one folder per run
AGENTS.md     working instructions for AI agents and collaborators
```

The folders are numbered after the course convention. The Python packages
inside `01_code/` keep plain names, because module names cannot start with a
digit.

## Specification

```python
from search_algos import get_method
get_method("linear")([7, 11, 7], [11, 9, 7])   # [True, False, True]
get_method("binary", "v1")(ids, queries)       # any registered version
```

The contract:

- The input is a sequence of Python `int` IDs (`list`, `tuple` or `range`) plus
  a sequence of `int` queries.
- The output is a new `list` with one `bool` per query, in query order.
- Neither input is modified.
- Invalid input raises `TypeError` identically for every method. Invalid input
  means:
  - not a sequence, or a `str` or `bytes` value
  - `bool` elements, floats and other non-`int` values
  - NumPy integers (pass `array.tolist()` instead)

  Validation is O(n + q). It runs in `Method.__call__` only and is **not**
  part of the timings.

| Method | Version | Preparation | Query (each) | Notes |
|---|---|---|---|---|
| LinearSearch | v1 (original) | `list(ids)` copy, O(n) | O(n) | index-based `while` loop |
| LinearSearch | **v2 (current)** | none, O(1) | O(n) | direct `for` iteration |
| BinarySearch | v1 (original) | `sorted(ids)`, O(n log n) | O(log n) | recursive, early exit |
| BinarySearch | **v2 (current)** | `sorted(ids)`, O(n log n) | O(log n) | iterative lower bound |
| Hash set | **v1 (only)** | `set(ids)`, O(n) expected | O(1) expected | `q in s` |

Both search procedures are implemented by hand. `sorted()` and `set()` are the
allowed library parts. Tests enforce this: an AST check bans `in`, `bisect`,
`.index` and `.count` in the search code, and comparison counting checks that
binary search makes at most O(log n) comparisons per query.

## Revisions

**LinearSearch:** v2 removes an unnecessary defensive copy and replaces the
index loop with direct iteration.

**BinarySearch:** v2 replaces recursion with an iterative lower-bound loop.

Both versions are kept and measured. The details and the numbers are in
[00_docs/REVISIONS.md](00_docs/REVISIONS.md).

## Tests

```bash
python -m pytest                  # 674 passed (each run stores tests.txt and tests.xml)
python -m tests.mutation_check    # 10/10 mutants killed: the suite detects wrong behaviour
```

The suite covers:

- the slide example
- empty arrays and queries
- one entry
- duplicates
- unsorted and descending input
- present and absent queries and boundaries
- repeated queries
- negative and huge IDs
- output order and exact `bool` type
- unchanged input
- seeded random cases against an independent reference
- inputs of 100,000 entries
- invalid input
- "by hand" rules (AST check and comparison counts)
- generator properties, including golden checksums
- the measurement protocol (each segment times exactly what it claims)
- provenance
- a dashboard smoke test

The tests were run against stubs before the implementation; see
[00_docs/DEVLOG.md](00_docs/DEVLOG.md).

## Synthetic data (`01_code/datagen/generator.py`)

The generator is separate from the algorithms and from the measurement code.

| Setting | Value |
|---|---|
| Array length n | 1,000; 10,000; 100,000 |
| Query count q | 1; 100 |
| Scenarios (target hit rate) | `all_present` (1.0), `all_absent` (0.0), `mixed` (0.5). q = 1 `mixed` is not measured: one query cannot be half present |
| Duplicate policy | `allow`: IDs drawn with replacement from `[0, 2n)` (`unique` available) |
| Seed | 2026 (string-seeded `random.Random`) |

- The array depends only on (seed, n, policy), so every q and scenario for the
  same n uses the identical array.
- **Hit placement:** present queries sit at stratified *first-occurrence*
  positions, which is where a linear scan stops, spread evenly over the array.
  The average scan length for a hit is about n/2 for every n and q, and is
  saved as `mean_first_hit_frac`. A single random hit position would make q = 1
  linear timings depend on chance.
- Absent queries are drawn uniformly from the ID range minus the array. The
  query order is shuffled.
- The SHA-256 checksums of every array and query list are saved in
  `datasets.csv`. A golden-checksum test detects whether a Python version
  generates different data.

## Measurement definitions

All timings use `time.perf_counter()` and are stored in **seconds per call**.

| Segment | What one call is |
|---|---|
| `prepare` | `prepare(ids)`: copy, sort, set construction, or nothing; includes freeing the result |
| `query` | one **complete batch** of q queries on a state prepared freshly for each repeat (not timed); a warm-cache, steady-state figure |
| `total` | `prepare(ids)` plus the complete batch, timed together (measured, not summed; total ≠ prepare + query) |

- **Per-query** values are derived (batch / q) and labelled as derived.
- **Calibration** also serves as the warm-up. It picks
  `calls_per_measurement` (plus a 25% margin) so that one measurement lasts at
  least 10 ms. Short calls are looped, and the elapsed time is divided by the
  number of calls.
- **5 repeats** per (dataset, method, version, segment), with the method order
  rotated each repeat. The **median** is reported and every raw repeat is kept.
- **gc** is disabled inside timed loops (as `timeit` does). `gc.collect()` runs
  between measurements.
- **Excluded from timing:** data generation, validation, tests, preflight
  correctness checks, printing, memory tracing and the dashboard.
- **Harness overhead:** `noop_call_s` and `noop_lambda_call_s` in `run.json`
  are tens of nanoseconds. They are not subtracted. The dashboard marks
  medians within 10× of them as overhead-dominated.
- **Memory** is measured with `tracemalloc` in a separate process after
  timing, with a fresh tracing run per (dataset, method):
  - *Included:* the prepared structure, the output list, transient buffers in
    the peaks, and about 100 bytes of harness objects (`memory_baseline` in
    `run.json`).
  - *Excluded:* the input array and queries (built before tracing started) and
    native allocations that tracemalloc cannot see.

The definitions are also saved verbatim in every `02_results/<run_id>/run.json`.

## Results (`02_results/<run_id>/`)

| File | Content |
|---|---|
| `run.json` | status, grid, methods, current versions, definitions, test summary, harness overhead, memory baseline, `source_unchanged` |
| `environment.json` | Python, OS, CPU, RAM, timer resolution, package versions, git commit/branch/dirty, source fingerprint |
| `tests.txt`, `tests.xml` | test output from the same run |
| `datasets.csv` | every dataset's settings, realized hit rate, `mean_first_hit_frac` and checksums |
| `timings_raw.csv` | every repeat: segment, `calls_per_measurement`, `elapsed_s` |
| `timings_summary.csv` | median, min and max per (dataset, method, version, segment) |
| `memory.csv` | tracemalloc bytes per (dataset, method, version) |

`run_id` = `<UTC timestamp>_<git short sha>[_dirty][_quick]`.

- A run without `_dirty` was made from committed code, so its sha identifies the
  measured code.
- `source.sha256` in `environment.json` identifies the measured code without
  git.

Timings depend on the machine, so compare ratios and slopes rather than
absolute values across machines.

## Dashboard (`01_code/dashboard/`)

`python -m streamlit run dashboard/app.py` reads saved results only and never
runs a benchmark. It shows:

- **Provenance:** commit, warnings, source-fingerprint check, environment, and
  the reproduce commands.
- **Test evidence:** the counts and the per-test table.
- **Definitions and inputs:** what each segment includes and excludes, and every
  dataset.
- **Runtime against n:** log–log, with prepare, query batch and total shown
  separately.
- **v1 against v2:** speed-ups, and a same-code control: binary v1 and v2 share
  `prepare`, so their ratio shows the noise level.
- **Scaling check:** fitted slopes next to the expected orders.
- **Memory:** the tracemalloc table.
- **Raw repeats:** every measurement, with downloads.
- **Spot check:** type your own IDs and queries and compare every method side by
  side.

## Dependencies

- Python 3.13.15.
- The algorithms, generator and benchmarks use the standard library only.
- `01_code/requirements.txt` pins pytest 9.1.1 and, for the dashboard only,
  streamlit 1.67.0, altair 6.3.0 and pandas 3.0.6.

## Known limitations

- Passing tests are evidence, not proof of correctness.
- Timings depend on the machine and its load. Absolute values do not transfer
  between machines.
- At q = 1, query-batch times for binary search and the hash set are close to
  the harness overhead. The dashboard flags these values.
- Query-batch timings are warm-cache figures: the same structure is queried
  repeatedly. Cold-cache costs are higher.
- IDs are dense small integers (< 2^30). This is a best case for hashing (no
  collisions) and for CPython's integer comparisons. Large or sparse IDs would
  be slower.
- tracemalloc misses native allocations and does not equal auxiliary space. See
  the included and excluded lists above.
