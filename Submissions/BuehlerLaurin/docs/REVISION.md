# Revision: original (v1) vs. revised (v2)

Code: [`membership/original.py`](../membership/original.py) (v1, unchanged since Step 5)
and [`membership/revised.py`](../membership/revised.py) (v2). Both stay in the
repository side by side (LAB_SPEC.md R5).

## 1. What changed

| Method | v1 (original) | v2 (revised) | Changed? |
|---|---|---|---|
| linear | scan per query, early exit | same function, re-exported | no (decision Q4) |
| hash | `set(ids)`, `x in s` | same function, re-exported | no (decision Q4) |
| binary, prepare | `sorted(ids)` copy | `sorted(ids)` copy | no |
| binary, query | recursive, slices the list at each step | iterative lower-bound search on index bounds, inlined in the query loop | **yes** |

Changes to binary search query, in detail:

1. **Removed the unnecessary copies.** v1 calls itself on `arr[:mid]` or `arr[mid+1:]`.
   Every slice copies up to half of the current list, about n/2 + n/4 + ... < n
   elements per query. v2 keeps two indices `lo`, `hi` into the one sorted copy and
   copies nothing.
2. **Recursion replaced by a loop.** No function call per step and no recursion depth
   (v1 needs about log2(n) + 1 nested calls).
3. **No function call per query.** The search loop is written directly inside the loop
   over the queries.
4. **Lower-bound form.** One `<` comparison per step, then one `==` at the end, instead
   of up to two comparisons (`==`, then `<`) per step.

Copy that was **not** removed: the sorted copy in `binary_prepare`. It is required.
Sorting in place (`ids.sort()`) would change the caller's array and break F4.

## 2. Why

- v1's slicing makes one query cost O(n) time and O(n) temporary memory, although the
  comparisons are only O(log n). Binary search loses its point: with slicing, a query
  costs about as much as a linear scan, plus the sorting.
- Recursion costs a Python function call per step and depends on the recursion limit.
  For our n this is not a correctness problem (depth 18 at n = 100,000), only a speed one.
- Laurin's goal (decision Q3): the fastest correct binary search. Two iterative
  candidates were written and both tested; the faster one was chosen by measurement.

## 3. Correctness evidence

- Both v2 candidates (`binary_query_classic`, `binary_query_lower_bound`) and the
  registered v2 pass the full shared test suite. Nothing was weakened.
- New tests added in Step 6 (R4), run for **every** method and version:
  - `test_step6_boundary_cases`: query above a duplicated maximum (lower bound ends at
    `lo == n` and must not read `state[n]`), below a duplicated minimum (classic ends with
    `hi == -1`), inside and next to a run of duplicates, a single element, lengths 16 and 15.
  - `test_exhaustive_small_arrays`: every array of length 0..5 over {0, 1, 2}
    (364 arrays) with queries -1..3, checked against a `set` oracle.
- Result: 578 passed, 0 failed (Step 6). Passing tests are evidence, not proof (R7).

Invariant of the chosen v2 (lower bound): `state[:lo]` < x and `state[hi:]` >= x.
Start `lo = 0`, `hi = n`. Each step keeps the invariant and shrinks `hi - lo`.
At the end `lo == hi` is the first index with a value >= x, so x is present
if and only if `lo < n and state[lo] == x`.

## 4. Choosing between the two v2 candidates

Script: `python -m bench.binary_variants`.
Raw data: `results/raw/binary_variants_20261120T143025Z.csv`, environment in
`..._env.json` (seed 20261120, duplicate policy "allow", q = 100, 5 repeats after
a warm-up, k calls per timed block recorded, fresh sorted copy per repeat).
Note: run on an uncommitted working tree (`git_dirty = true`).

Median query-batch time, divided by q = 100 to give **microseconds per query**:

| n | hit rate | v1 recursive + slicing | v2 classic | v2 lower bound |
|---:|---:|---:|---:|---:|
| 1,000 | 1.0 | 4.89 | 1.93 | **1.38** |
| 1,000 | 0.0 | 5.04 | 1.79 | **1.36** |
| 1,000 | 0.5 | 5.08 | 1.46 | **1.42** |
| 10,000 | 1.0 | 28.83 | 1.98 | **1.91** |
| 10,000 | 0.0 | 30.25 | 2.12 | **1.86** |
| 10,000 | 0.5 | 30.32 | 2.09 | **1.75** |
| 100,000 | 1.0 | 759.72 | 2.60 | **2.46** |
| 100,000 | 0.0 | 452.54 | 2.94 | **2.33** |
| 100,000 | 0.5 | 438.29 | 2.62 | **2.52** |

Interpretation:
- **Lower bound has the lower median in all 9 cells.** The gap is clear for absent and
  mixed queries (about 5-20%). For all-present queries the raw repeats overlap
  (for example n = 1,000: classic 1.30-2.78 us, lower bound 1.32-1.76 us), so there it is
  roughly a tie: classic can stop early on a hit, but pays two comparisons per step.
- **Decision:** `binary_query = binary_query_lower_bound`. The classic variant stays in
  the code and in the tests for comparison.

## 5. Measured effect of the revision (v1 vs. v2), first measurement

- v1 grows roughly linearly with n per query (about 5 → 30 → 450-760 us), as predicted
  by the O(n) copying. v2 grows only slightly (about 1.4 → 1.8 → 2.4 us), as predicted
  by O(log n): log2(1,000) ≈ 10, log2(100,000) ≈ 17.
- Speed-up of the query batch at n = 100,000: about **170-310x**.
- Preparation (`sorted`) is identical in v1 and v2, so the total-time gain is smaller
  when sorting dominates (q = 1). This is measured in Step 7.
- Open observation: v1 at n = 100,000 with hit rate 1.0 (760 us) is slower than with
  0.0 (450 us), although hits can stop early. This cell was measured first; it may be
  noise or a warm-up effect of the memory allocator. To be checked in Step 7.

Final numbers for all methods (q in {1, 100}, preparation, query batch and total time)
follow from `bench/timing.py` in Step 7.
