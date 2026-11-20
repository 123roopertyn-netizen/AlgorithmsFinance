# Development log

## 1. Tests before implementation

The shared algorithm and generator tests were written before
`search_algorithms.py` or `synthetic_data.py` existed.

Command:

```bash
python3 -m unittest discover -s tests -v
```

Observed pre-implementation result: exit code `1`, with two import errors:
`No module named 'search_algorithms'` and `No module named 'synthetic_data'`.
This confirms the tests detected the missing behavior instead of passing
without exercising an implementation.

## 2. Version 1 and manual trace

Version 1 implemented manual linear search, recursive binary search over one
sorted copy, and membership using Python's standard-library `set`. The first
complete run passed all seven tests.

Manual trace for IDs `[7, 11, 7]` and queries `[11, 9, 7]`:

- Linear search:
  - `11`: compare with `7`, then `11` -> `True`.
  - `9`: compare with `7`, `11`, and `7` -> `False`.
  - `7`: compare with the first `7` -> `True`.
- Binary search first creates `[7, 7, 11]` without changing the input:
  - `11`: `(low=0, high=2, middle=1, value=7)`, then
    `(low=2, high=2, middle=2, value=11)` -> `True`.
  - `9`: inspect `7`, then `11`; the bounds become `low=2, high=1` ->
    `False`.
  - `7`: the first midpoint value is `7` -> `True`.
- Hash-set membership builds `{7, 11}` and checks the queries in their given
  order -> `[True, False, True]`.

All three methods therefore return `[True, False, True]`, and the original ID
array remains `[7, 11, 7]`.

## 3. Revision

The original public binary search called a recursive helper once per search
step. Version 2 replaces that public implementation with a `while low <= high`
loop. The revision:

- preserves the same sorted-copy and ordered-query contract;
- preserves version 1 as `binary_search_recursive_v1`;
- avoids repeated Python function-call overhead and recursion-stack space; and
- makes the index updates visible in one function, which simplifies tracing.

Review also identified missing boundary coverage. A shared case now searches
below the minimum, at the minimum, within a duplicate run, at the maximum, and
above the maximum. Generator tests were extended to zero queries and 0%/100%
hit rates. No expected result was weakened.

After the revision, all eight core/generator tests passed. Two additional
pipeline tests verify that every implementation is measured and that JSON, CSV,
and HTML artifacts can be regenerated. The final result is ten passing tests.

In the recorded 10,000-ID benchmark, the iterative median was `1.200667 ms`
versus `1.279875 ms` for the recursive version. That result supports the local
revision decision but is not a proof that every machine or input will show the
same difference.

## 4. AI use

OpenAI Codex assisted with implementation, test design, benchmarking, and
documentation. The human author remains responsible for reviewing the code and
claims.

Accepted suggestions:

- use one shared case table so all search methods face identical tests;
- sort once per binary-search call rather than once per query;
- retain recursive version 1 and make iterative version 2 the public method;
- construct guaranteed misses from a disjoint integer range rather than retry
  random values;
- use a local seeded random generator, `perf_counter_ns`, repeated runs, and a
  median summary; and
- generate a dependency-free dashboard from machine-readable benchmark data.

Corrected suggestions or execution issues:

- `pytest` was initially considered, but it was unavailable in the environment;
  the solution uses standard-library `unittest` with no loss of required
  coverage.
- the first shell wrapper used zsh's reserved variable name `status` after the
  deliberately failing test run; it was changed to `test_exit`, and the
  pre-implementation run was repeated to record exit code `1` cleanly.
- boundary and extreme-hit-rate cases were added after reviewing the first
  passing suite.

Rejected suggestions:

- using `bisect` or `list.index`, because both search procedures must be
  implemented directly;
- sorting the caller's list in place, because the input must remain unchanged;
- timing synthetic-data generation, because the assignment requires generation
  to remain separate from algorithm measurement; and
- adding NumPy, pandas, or a charting package, because the standard library is
  sufficient and keeps the submission easier to reproduce.
