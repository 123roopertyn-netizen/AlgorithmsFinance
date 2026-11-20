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
