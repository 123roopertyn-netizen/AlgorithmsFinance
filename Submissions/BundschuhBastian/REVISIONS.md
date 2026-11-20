# Revisions

Version 1 stays in `membership.py` unchanged. Version 2 is added next to it, so both can be
tested and timed. Only binary search was revised. `linear_search` and `hash_set_membership`
have no v2.

## v1 -> v2: `binary_search_recursive` -> `binary_search_iterative`

| | v1 (`binary_v1`) | v2 (`binary_v2`) |
|---|---|---|
| Search loop | recursive helper `_search_recursive` | `while low <= high` loop inside the method |
| Calls per query | up to about log2(n) + 1 Python function calls | 0 extra calls |
| Extra memory per query | O(log n) recursion stack | O(1) |
| No queries | still sorts the copy | returns `[]` at once, no sort |
| Correctness idea | same invariant: if the query is in the array, it lies in `low..high` | same |

### What changed and why

1. **Recursion replaced by a loop.** Each recursive call creates a new stack frame (the
   interpreter's record of one call). The loop reuses the same variables `low`, `high`,
   `middle`. This saves the call overhead and makes stack memory O(1) instead of O(log n).
   Asymptotic time stays O(log n) per query. How much faster it is in seconds is
   measured in step 5, not claimed here.
2. **Early return for an empty query list.** v1 sorted a copy of the array even when there
   was nothing to answer. That is O(n log n) work and O(n) memory for no output. v2 returns
   `[]` before sorting.

### What did NOT change (and why)

- **The sorted copy stays.** I looked for an unnecessary copy to remove. In v1 there was
  none except the empty-query case above. `sorted(ids)` is required: the input may be
  unsorted, binary search needs sorted data, and the input must stay unchanged, so
  `ids.sort()` is not allowed. v1 also never sliced the list (it passed `low`/`high`), so
  no hidden copies per recursion step.
- Expected results of all tests are unchanged.

### Tests

- All existing tests now run for four methods: `linear_v1`, `binary_v1`, `binary_v2`,
  `hash_v1`. No expected result was changed or weakened.
- Added (run for all methods unless noted): tuple and range input, many equal values,
  unsorted queries with repeats.
- Added for v2 only: `test_binary_v2_does_not_sort_without_queries` (no iteration over the
  input when queries are empty).
- Call depth tests (version-independent, replace an earlier test that used
  `sys.setrecursionlimit` and depended on the Python version): `max_python_call_depth`
  uses `sys.setprofile` to count the deepest nesting of Python-level `call` events
  (restored in a `finally` block; C calls such as `sorted()` are not counted).
  On 200,000 sorted IDs: `binary_v2` has depth 1 (the method itself; asserted `< 3`),
  `binary_v1` has depth 21 (asserted `>= 15`, about log2(n) plus the method and the list
  comprehension). On 200 IDs `binary_v1` has depth 11, so its depth grows with n.
  Depth was measured on Python 3.11.0 only; the test does not use the recursion limit.

Result: 307 passed.
