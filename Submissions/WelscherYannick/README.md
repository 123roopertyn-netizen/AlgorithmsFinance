# Lab: Search methods (Phase 1)

Submission of Yannick Welscher for *Algorithms in Finance*.

Work in progress. Run commands, expected test results and measurement
definitions will be added here.

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

**Correctness after the revision.** The full test suite runs unchanged against
both versions: 118 tests pass (14 contract checks for each method of each
version, one cross-method check per version, generator tests and mutant
tests). No expected result was changed. The revision did not reveal any new
case that needed an additional test. Passing tests are evidence, not a proof of
correctness.

**Expected effect.** Lower query-batch time for binary search in v2; the same
preparation time, since `sorted()` is shared. Whether the gain is measurable is
checked in the benchmark, not assumed.

**Measured effect.** In all 15 scenarios the median query-batch time of v2
binary search is 9–15 % below v1 (ratio v2/v1 between 0.850 and 0.912), and
the ranges of the five repeats do not overlap. For comparison, linear and hash
search run identical code in both versions; their v1/v2 medians differ by 1.3 %
(median) and at most 6.4 %. The total time barely changes, because sorting
dominates it (see below).

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

The committed results were measured at commit `09dafe7` without uncommitted
changes, on an Apple M4 Pro (macOS 26.5.1, Python 3.13.15). Timings depend on
the machine.

**Results (v2, medians).** Total time, with preparation / query batch in
brackets.

One query, all absent:

| n | linear | binary | hash |
|---|---|---|---|
| 1,000 | 5.94 µs (15.1 ns / 6.06 µs) | 25.7 µs (25.3 µs / 586 ns) | 5.31 µs (5.4 µs / 46.1 ns) |
| 10,000 | 66.9 µs (15.5 ns / 69.3 µs) | 482 µs (499 µs / 761 ns) | 100 µs (104 µs / 46.1 ns) |
| 100,000 | 798 µs (15.1 ns / 795 µs) | 8.58 ms (8.63 ms / 930 ns) | 2.2 ms (2.17 ms / 45.9 ns) |

100 queries, hit rate 0.5:

| n | linear | binary | hash |
|---|---|---|---|
| 1,000 | 446 µs (15.5 ns / 473 µs) | 79.2 µs (25.3 µs / 52.9 µs) | 6.2 µs (5.34 µs / 938 ns) |
| 10,000 | 5.47 ms (15.4 ns / 5.59 ms) | 605 µs (559 µs / 72.3 µs) | 110 µs (112 µs / 894 ns) |
| 100,000 | 61.8 ms (15.3 ns / 57.9 ms) | 8.8 ms (8.88 ms / 96.4 µs) | 2.19 ms (2.18 ms / 884 ns) |

* With one query, linear search is fastest overall: it prepares nothing, and
  one scan is cheaper than sorting or building a set.
* With 100 queries, hash membership is fastest; linear search grows with n·q.
* Binary search never wins in these scenarios: sorting costs more than building
  the set, and its O(log n) queries cannot make up for that at q ≤ 100.
* Linear "preparation" (about 15 ns) is only the call overhead of returning the
  array.

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
`6b79fc8` without uncommitted changes. All three repeats gave identical
values.

**Results (100 queries, hit rate 0.5, medians, bytes):**

| n | method | prepare current | prepare peak | query current | query peak v1 / v2 | total peak |
|---|---|---|---|---|---|---|
| 1,000 | linear | 0 | 0 | 920 | 1,016 / 1,016 | 1,016 |
| 1,000 | binary | 8,056 | 12,088 | 920 | 1,540 / 1,128 | 12,088 |
| 1,000 | hash | 32,984 | 41,224 | 920 | 968 / 968 | 41,224 |
| 10,000 | linear | 0 | 0 | 920 | 1,016 / 1,016 | 1,016 |
| 10,000 | binary | 80,056 | 120,096 | 920 | 1,732 / 1,128 | 120,096 |
| 10,000 | hash | 524,504 | 655,624 | 920 | 968 / 968 | 655,624 |
| 100,000 | linear | 0 | 0 | 920 | 1,016 / 1,016 | 1,016 |
| 100,000 | binary | 800,056 | 1,199,960 | 920 | 1,860 / 1,128 | 1,199,960 |
| 100,000 | hash | 4,194,520 | 6,291,720 | 920 | 968 / 968 | 6,291,720 |

* **Linear** allocates nothing in preparation: it keeps the given array.
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

## Known measurement shortcomings

* **Total below preparation.** For binary and hash search, `total_s` is in
  many repeats smaller than `prepare_s` alone (e.g. binary, n = 10,000, q = 1:
  preparation 499 µs, total 482 µs), although the total includes the
  preparation. The gap is up to about 10 %, mostly at n = 10,000. Two
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
