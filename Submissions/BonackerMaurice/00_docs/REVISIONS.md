# Revisions

Both versions of each revised method stay registered in
`01_code/search_algos/registry.py`, are tested by the same suite, and are measured on
identical inputs. `CURRENT` names the version that represents the submission.

| Method | v1 (original) | v2 (revised) | Current |
|---|---|---|---|
| LinearSearch | `list(ids)` copy, then an index-based `while` scan | no copy, direct `for` iteration | v2 |
| BinarySearch | `sorted()` copy, then a recursive search with early exit | `sorted()` copy, then an iterative lower-bound search | v2 |
| Hash membership | `set(ids)`, then `q in s` | (not revised) | v1 |

## Revision 1: LinearSearch v1 → v2

**What changed:**

1. `prepare` no longer copies the input. v1 made a defensive `list(ids)` so the
   caller's array "cannot change". The scan only reads, though, so the copy
   protects nothing. It costs O(n) time and about 8 bytes per element (one list
   of references) on every call.
2. The scan iterates directly (`for value in data`) instead of using an index
   (`while i < n: data[i] ... i += 1`). This removes the index arithmetic and
   the `data[i]` lookup per element. Python's list iterator does both in C.

**Expected effect:**

- `prepare` drops from O(n) to O(1).
- The traced memory for preparation drops from about 8n bytes to 0.
- The query batch gets faster by a constant factor, and the complexity stays
  O(n·q).

**Evidence:**

<!-- Fill from the committed full run: prepare, query and total medians at n=100,000,
q=100 (mixed) for v1 and v2, the speed-up, and memory.csv prepare_peak_bytes. -->

## Revision 2: BinarySearch v1 → v2

**What changed:** the recursive search `_contains_recursive(a, x, lo, hi)`
became an iterative lower-bound loop. The loop narrows to the first index whose
value is `>= x` and then checks that one index.

**Why:**

- Every recursive call costs a Python function call (a frame plus argument
  passing). The loop runs one comparison per iteration with no calls.
- The recursion depth is only about log₂ n (17 at n = 100,000), so v1 is
  correct here. The iterative form still removes any dependence on the
  recursion limit.

**Trade-off:** v1 can return early when `a[mid] == x`. v2 always runs about
⌈log₂ n⌉ + 1 iterations. The comparison should therefore look at
`all_present` separately from `all_absent`.

**Control:** `prepare` is the same function (`sorted`) in both versions. Their
`prepare` ratio should be about 1.0. Any deviation shows the measurement noise
level, and the dashboard shows it as the "same-code control".

**Evidence:**

<!-- Fill from the committed full run: query-batch medians at n=100,000, q=100 for
all_present and all_absent, v1 vs v2, and the same-code control ratio. -->

## Tests rerun after the revision

The suite is parametrized over every registered method and version, so v1 and
v2 always run the same tests. Result: see `02_results/<run_id>/tests.txt` of the
committed run.
