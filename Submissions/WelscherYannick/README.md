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
