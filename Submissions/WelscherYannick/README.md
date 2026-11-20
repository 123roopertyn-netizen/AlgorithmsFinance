# Lab: Search methods (Phase 1)

Submission of Yannick Welscher for *Algorithms in Finance*, Phase 1:
implement and measure linear search, binary search on a sorted copy, and
membership with a standard-library hash set; revise one method and compare
both versions.

## Quick start

All commands run from this folder, `Submissions/WelscherYannick/`. Tested
with Python 3.13.15 on macOS (Apple M4 Pro); the pinned packages need
Python 3.11 or newer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest                    # expected: 172 passed
.venv/bin/python bench/benchmark.py           # timing, about 1-2 minutes, writes results/
.venv/bin/python bench/memory.py              # memory, a few seconds, writes results/
.venv/bin/streamlit run dashboard/app.py      # dashboard on http://localhost:8501
```

The committed `results/` already contain a full run, so the dashboard works
without rerunning the benchmarks. Rerunning overwrites them with values from
your machine. `--quick` on either benchmark script writes a small smoke run
to `results/quick/` instead (ignored by git). No file needs to be edited.

## Project structure

| Path | Content |
|---|---|
| `src/interface.py` | The specification and the two-stage `Method` (`prepare`, `query`) |
| `src/search_v1.py` | v1: linear, recursive binary, hash set |
| `src/search_v2.py` | v2 (revision): iterative binary; linear and hash imported from v1 |
| `src/registry.py` | All versions; tests and benchmarks iterate over it |
| `src/datagen.py` | Synthetic-data generator (seed, hit rate, duplicate rate) |
| `tests/` | Contract checks, mutant tests, tests for generator, measurement and dashboard code |
| `bench/benchmark.py` | Runtime measurement |
| `bench/memory.py` | Memory measurement |
| `results/` | Raw measurements and metadata of the committed run |
| `dashboard/` | Streamlit dashboard: `app.py` (views), `data.py` (loading, summaries), `theme.py` (design) |
| `AI_LOG.md` | AI suggestions accepted, corrected or rejected |

## Specification

Input: an integer array `ids` (may be empty, unsorted, with duplicates) and
an ordered list `queries`. Output: one `bool` per query, in query order;
entry i is `True` exactly when `queries[i]` occurs in `ids`. Neither input is
modified. Any sequence of ints is accepted (list or tuple, ints beyond 64
bits). Each method is split into `prepare(ids)` and `query(state, queries)`
so that preparation and the query batch can be timed separately;
`contains_all` runs both. `query` never changes the prepared state, and the
state does not follow later changes to `ids`. Full text: docstring of
`src/interface.py`.
Example from the slides: array `[7, 11, 7]`, queries `[11, 9, 7]` →
`[True, False, True]`.

## Tests

```bash
.venv/bin/python -m pytest        # expected: 172 passed, in about 10 seconds
```

| File | Tests | What it checks |
|---|---|---|
| `tests/test_search.py` | 110 | 18 contract checks for each of the 3 methods in both versions (108), plus agreement of the methods within each version (2) |
| `tests/test_mutants.py` | 10 | Nine deliberately broken methods must each fail a check; a correct reference must pass all |
| `tests/test_datagen.py` | 23 | Generator: determinism, sizes, exact hit and duplicate rates, invalid settings |
| `tests/test_benchmark.py` | 4 | Timing code: fresh state per repeat, output schema, result check |
| `tests/test_memory.py` | 8 | Memory code counts a known allocation, the sorted and the tuple copy and the output, but not the input |
| `tests/test_dashboard_data.py` | 11 | Dashboard numbers agree with the raw result files |
| `tests/test_dashboard_app.py` | 6 | The dashboard renders without exceptions, also after changing each filter |

The contract checks (`tests/contract.py`) cover the cases from the slides:
empty array and queries, one entry, duplicates, unsorted input, first and last
matches, absent queries, negative ids, output order, return type, unchanged
input, repeated calls on one prepared state, and comparison with an
independent reference (`q in ids`) on generated data. Four checks were added
in my review: ints beyond 64 bits, tuples as input, a prepared state that
must not follow later changes to `ids`, and binary-search boundaries for
sorted arrays of every length from 0 to 8, queried at each element and in
each gap. The tests were written before the implementation and failed against
stubs (43 failures) before v1 existed; the state check failed against linear
search (2 failures) before it was fixed (see below). Passing tests are
evidence, not a proof of correctness.

## Synthetic data

`src/datagen.py` builds `(ids, queries)` from `n`, `q`, `hit_rate`,
`duplicate_rate` and `seed`, with its own random generator:

* **Ids:** distinct integers from a range of 10·(n + q) + 10 values around
  zero, so negative ids occur. The array is shuffled, so it is unsorted.
* **Duplicates:** `int(n · duplicate_rate)` entries repeat an earlier id; at
  least one id stays unique. The benchmarks use 0.1.
* **Hits:** `round(hit_rate · q)` queries are drawn with replacement from the
  array's ids, so a hit may be queried more than once. The other queries are
  distinct ids that are guaranteed to be absent. Query order is shuffled.
* **Position of hits:** hits sit at random positions in the array, so linear
  search needs about n/2 comparisons per hit on average and n per miss.
  Querying only the first or last element would make linear search look much
  better or worse.
* **Reproducibility:** the same settings give the same data within one Python
  version; Python's `random` module does not guarantee the same stream across
  versions.

## Revision: v1 to v2

**What changed.** Binary search in `src/search_v1.py` is recursive: each step
calls `_binary_search_recursive` on the left or right half. `src/search_v2.py`
does the same search in a `while lo < hi` loop. The half-open range
`[lo, hi)`, the midpoint `(lo + hi) // 2` and the comparisons are identical, so
the revision changes one thing only. Linear search, hash membership and binary
preparation are imported from v1 unchanged. Both versions are kept and are
registered in `src/registry.py`.

**Why.** Every recursive step is a Python function call with its own stack
frame. Up to about log2(n) + 1 calls per query (about 18 for n = 100,000) add
call overhead that a loop avoids. The loop also cannot hit Python's recursion
limit, although that limit is far from reached at these sizes.

**Correctness after the revision.** The full test suite ran unchanged against
both versions: 118 tests passed at that point (14 contract checks for each
method of each version, one cross-method check per version, generator tests
and mutant tests; the later tests bring the total to 172). No expected result
was changed. The revision did not reveal any new
case that needed an additional test. Passing tests are evidence, not a proof of
correctness.

**Expected effect.** Lower query-batch time for binary search in v2; the same
preparation time, since `sorted()` is shared. Whether the gain is measurable is
checked in the benchmark, not assumed.

**Measured effect.** In all 15 scenarios the median query-batch time of v2
binary search is 7–15 % below v1 (ratio v2/v1 between 0.848 and 0.933), and
the ranges of the five repeats do not overlap. For comparison, linear and hash
search run identical code in both versions; their v1/v2 medians differ by at
most 2.6 % in the query batch and at most 7.0 % in the total time. The total
time of binary search barely changes, because sorting dominates it (see
below). In memory, v1 needs a few hundred bytes more at its query peak (see
the memory section). The first measurement, before the fix below, gave
9–15 %.

**Later fix found in review: linear search copies.** My review added a check
that the prepared state must not follow later changes to `ids`. In v1, linear
`prepare` returned the given array itself, so the check failed (for v1, and
for v2, which imports linear search). `prepare` now copies the array into a
tuple. This is a correction of v1, not part of the v1 → v2 revision: it
changes both versions in the same way. Cost: about 2 ns and 8 bytes per entry
(214 µs and 800,040 bytes at n = 100,000). All measurements below were rerun
after the fix.

## Runtime measurement

```bash
.venv/bin/python bench/benchmark.py           # full grid, about 1-2 minutes
.venv/bin/python bench/benchmark.py --quick   # smoke run into results/quick/ (not committed)
```

Definitions are in the docstring of `bench/benchmark.py`. In short:

* **Scenarios:** n ∈ {1,000; 10,000; 100,000}, q ∈ {1; 100}, hit rate 1.0
  (all present), 0.0 (all absent) and 0.5 (mixed; only for q = 100, since one
  query cannot be mixed). Duplicate rate 0.1, seed 20261120. Every method and
  version gets the same arrays and queries per scenario.
* **Timed separately** with `time.perf_counter`, unit seconds:
  `prepare_s` (one `prepare` call), `query_batch_s` (the complete batch of q
  queries, not per query) and `total_s` (prepare plus query, timed as its own
  run).
* Warm-up with growing call counts, then 5 repeats; each measurement averages
  `number` back-to-back calls so it lasts at least 20 ms. Fresh preparation in
  every repeat. GC paused while timing. Median is the reported statistic.
* Not timed: data generation, result checks, printing, file writing.

**Saved results** (`results/`):
* `timing_raw.csv`: one row per scenario, version, method and repeat (450 rows)
  with all three times and the call counts used.
* `timing_metadata.json`: Python version, machine, clock resolution, loop
  overhead per call, git commit of the measured code, generator settings and
  the generated data per scenario.

The committed results were measured at commit `302dc8f` (after the linear
fix) without uncommitted changes, on an Apple M4 Pro (macOS 26.5.1, Python
3.13.15). Timings depend on the machine.

**Results (v2, medians).** Total time, with preparation / query batch in
brackets.

One query, all absent:

| n | linear | binary | hash |
|---|---|---|---|
| 1,000 | 6.55 µs (702 ns / 5.91 µs) | 26 µs (25.6 µs / 590 ns) | 5.45 µs (5.48 µs / 45.2 ns) |
| 10,000 | 92.2 µs (20.2 µs / 71.5 µs) | 515 µs (527 µs / 781 ns) | 111 µs (114 µs / 45.2 ns) |
| 100,000 | 997 µs (214 µs / 755 µs) | 8.93 ms (8.92 ms / 956 ns) | 2.29 ms (2.25 ms / 44.4 ns) |

100 queries, hit rate 0.5:

| n | linear | binary | hash |
|---|---|---|---|
| 1,000 | 451 µs (721 ns / 445 µs) | 80 µs (26 µs / 54.2 µs) | 6.38 µs (5.3 µs / 948 ns) |
| 10,000 | 5.2 ms (19.7 µs / 5.17 ms) | 565 µs (537 µs / 73.2 µs) | 112 µs (141 µs / 882 ns) |
| 100,000 | 56.9 ms (214 µs / 55.1 ms) | 8.99 ms (8.84 ms / 100 µs) | 2.23 ms (2.22 ms / 900 ns) |

* With one query, linear search has the lowest total time in 5 of 6
  scenarios: its preparation is only a copy, and one scan is usually cheaper
  than sorting or building a set. The exception is n = 1,000 with an absent
  query, where the hash set is slightly faster (5.45 µs against 6.55 µs).
* With 100 queries, hash membership is fastest; linear search grows with n·q.
* Binary search never wins in these scenarios: sorting costs more than building
  the set, and its O(log n) queries cannot make up for that at q ≤ 100.
* Linear preparation is the tuple copy, about 2 ns per entry (214 µs at
  n = 100,000); before the fix it was only the call overhead (about 15 ns).

## Memory measurement

```bash
.venv/bin/python bench/memory.py           # full grid, a few seconds
.venv/bin/python bench/memory.py --quick   # smoke run into results/quick/
```

Separate from the timing run, same scenarios and data. `tracemalloc` with a
fresh session per run and `gc.collect()` before it; definitions are in the
docstring of `bench/memory.py`. Three runs per method:

| Column | Traced | Kept alive when read | Includes |
|---|---|---|---|
| `prepare_current_B` / `prepare_peak_B` | `prepare(ids)` | state | prepared structure; peak also temporaries |
| `query_current_B` / `query_peak_B` | `query(state, queries)` | output | output list; peak also temporaries |
| `total_current_B` / `total_peak_B` | both | state and output | both |

**Never included:** the given input (built before tracing), interpreter
overhead, native allocations outside Python's allocators, and call-stack
frames. None of the columns is auxiliary space in the strict sense: the input
is always excluded, the output is part of query and total. Unit: bytes.

Saved in `results/memory_raw.csv` (270 rows: 15 scenarios × 6 method/version
pairs × 3 repeats) and `results/memory_metadata.json`, measured at commit
`302dc8f` (after the linear fix) without uncommitted changes. All three
repeats gave identical values.

**Results (100 queries, hit rate 0.5, medians, bytes):**

| n | method | prepare current | prepare peak | query current | query peak v1 / v2 | total peak |
|---|---|---|---|---|---|---|
| 1,000 | linear | 8,040 | 8,040 | 920 | 1,016 / 1,016 | 9,056 |
| 1,000 | binary | 8,056 | 12,088 | 920 | 1,540 / 1,128 | 12,088 |
| 1,000 | hash | 32,984 | 41,224 | 920 | 968 / 968 | 41,224 |
| 10,000 | linear | 80,040 | 80,040 | 920 | 1,016 / 1,016 | 81,056 |
| 10,000 | binary | 80,056 | 120,096 | 920 | 1,732 / 1,128 | 120,096 |
| 10,000 | hash | 524,504 | 655,624 | 920 | 968 / 968 | 655,624 |
| 100,000 | linear | 800,040 | 800,040 | 920 | 1,016 / 1,016 | 801,056 |
| 100,000 | binary | 800,056 | 1,199,960 | 920 | 1,860 / 1,128 | 1,199,960 |
| 100,000 | hash | 4,194,520 | 6,291,720 | 920 | 968 / 968 | 6,291,720 |

* **Linear:** the tuple copy is 8 bytes per entry plus a 40-byte header
  (800,040 = 8 · 100,000 + 40). Its peak equals its final size, because a
  tuple is built without temporary buffers. Before the fix, linear allocated
  nothing in preparation.
* **Binary:** the sorted copy is 8 bytes per entry plus a 56-byte list header
  (800,056 = 8 · 100,000 + 56); it holds references to the existing int
  objects, not new ints. The peak is about 1.5 times that, consistent with
  the temporary merge buffer of Python's sort.
* **Hash:** the set stores its table, not the entries: 4,194,520 bytes for
  about 90,000 distinct ids at n = 100,000 is a table of 262,144 slots of
  16 bytes. The peak includes the old table during the last resize. The set
  needs about 5 times the memory of the sorted copy, in exchange for the
  faster preparation and queries measured above.
* **Output:** 920 bytes for 100 booleans, the size of the list itself
  (`sys.getsizeof` gives the same value); `True` and `False` are shared
  objects.
* **v1 versus v2:** only the binary query peak differs. v1 is 220 to 764 bytes
  higher, growing with n. The frames themselves are not traced, but each
  pending recursive call keeps its own int objects for `lo`, `hi` and `mid`
  alive. This is the O(log n) extra space of the recursion, visible
  indirectly. The total peak is unaffected because the preparation dominates
  it.

## Dashboard

```bash
.venv/bin/streamlit run dashboard/app.py
```

Opens on http://localhost:8501 (port set in `.streamlit/config.toml`). The
dashboard only reads `results/`; it never runs a benchmark. To refresh it,
rerun `bench/benchmark.py` and `bench/memory.py`. All medians, ratios and
headline numbers are computed from the raw repeat values in `dashboard/data.py`;
`tests/test_dashboard_data.py` checks them against the raw files.

* **Filters** (one row, apply to all views): number of queries, hit rate,
  versions shown, log or linear time axis. The line below the filters always
  states q, the generated hit rate, the duplicate rate and the units.
* **Runtime:** time against n with one curve per method, preparation, query
  batch and total in separate charts; v2 solid, v1 dashed; markers are medians,
  whiskers the min–max of the five repeats.
* **Revision v1 → v2:** v2/v1 ratio of the binary query batch for every
  scenario, with the noise band measured on identical code, and binary
  search over n for the selected scenario.
* **Memory:** prepared structure and peak per method, plus a table of all
  memory columns for the selected scenario.
* **Raw data:** every repeat for the selected scenario, and the full CSV files
  for download.
* **Environment:** machine, Python, clock, commits and generator settings for
  both runs, the generated data per scenario and the full metadata.

Design: dark navy with rounded glass cards, loosely inspired by the base tones
of Roberts Space Industries (approximated; no official colour codes, logo or
name). The three data colours were checked with a palette validator against
the card background, including colour-blind separation. Lines are also
distinguished by labels and version by line style, so colour is never the only
cue. All colours are defined in `dashboard/theme.py`.

## Known measurement shortcomings

* **Total below preparation.** For binary and hash search, `total_s` is in
  many repeats smaller than `prepare_s` alone (e.g. hash, n = 10,000,
  q = 100, mixed: preparation 141 µs, total 112 µs), although the total
  includes the preparation. The median gap reaches 21 % in the current run
  (about 10 % in the first run), mostly at n = 10,000. It never occurs for
  linear search. Two
  explanations were tested and rejected: (1) the previous structure staying
  alive while the next one is built in the preparation loop, and (2) a cold
  cache for the first measurement of each method (an untimed warm-up call did
  not remove the gap). The cause is open. Differences of this size between
  separately timed runs should therefore not be interpreted. The v1/v2
  comparison is not affected: it compares the same column of the same
  scenario.
* The loop overhead (about 5.5 ns per call) is included in all times, not
  subtracted. It matters only for the smallest values (hash queries with
  q = 1, about 46 ns).
* `perf_counter` resolution on this machine is about 42 ns; single calls are
  therefore never timed alone.
* Memory: `tracemalloc` sees only Python-level allocations. Process memory
  (RSS, e.g. with `psutil`) was not measured. The recursion of v1 shows up
  only through the int objects it keeps alive, not through its frames.

## Use of AI

The code and this README were written with Claude Code (Anthropic), in a
dialogue in which I set the requirements and made the design decisions, for
example the choice of the revision and the dashboard design. `AI_LOG.md`
lists every suggestion and whether I accepted, corrected or rejected it,
including the cases where an AI claim was wrong and how it was found. Commits
written with the AI carry a `Co-Authored-By: Claude` line.

## Commit for the audit

Reviewers should audit exactly one recorded commit and run it without editing
any file. The commit is recorded here once the submission is final; until then
this section is a placeholder.
