# Search Algorithms — LaviBen

Tests-first implementation and runtime comparison of three ways to answer
ordered membership queries over integer IDs:

1. manual linear search;
2. manual binary search over a sorted copy; and
3. Python standard-library hash-set membership.

All methods return one Boolean per query in the original query order and leave
the supplied ID array unchanged. The recursive binary-search version is kept
beside the revised iterative version for direct comparison.

## Quick start

Python 3.10 or newer is sufficient; there are no third-party dependencies.

```bash
cd Submissions/LaviBen
python3 -m unittest discover -s tests -v
python3 benchmark.py
python3 dashboard.py
```

Open `results/runtime_dashboard.html` in a browser to inspect the generated
dashboard.

## Example

```python
from search_algorithms import binary_search, hash_set_membership, linear_search

ids = [7, 11, 7]
queries = [11, 9, 7]
expected = [True, False, True]

assert linear_search(ids, queries) == expected
assert binary_search(ids, queries) == expected
assert hash_set_membership(ids, queries) == expected
assert ids == [7, 11, 7]
```

## Implementations

| Function | Approach | Total time for `n` IDs and `q` queries | Extra working space* |
|---|---|---:|---:|
| `linear_search` | Scan IDs for each query | `O(nq)` | `O(1)` |
| `binary_search_recursive_v1` | Sort once, recursively halve each search range | `O(n log n + q log n)` | `O(n + log n)` |
| `binary_search` | Sort once, iteratively halve each search range | `O(n log n + q log n)` | `O(n)` |
| `hash_set_membership` | Build a set once, then perform membership lookups | Expected `O(n + q)` | `O(n)` |

\*Excluding the required `O(q)` result list. Hash-table lookup is expected
`O(1)` per query; adversarial collisions can make the worst case slower.

`sorted(ids)` creates the binary-search copy, so the caller's array is never
sorted in place. Linear and binary search procedures are implemented directly;
the core does not delegate to `list.index`, `bisect`, or another search helper.

## Tests-first evidence

The tests were created before either implementation module. The first run
exited with code `1` because `search_algorithms` and `synthetic_data` were
missing. Version 1 then passed all seven original tests. After review, boundary
and generator cases were added; the final suite contains ten passing tests.

The shared cases cover:

- empty arrays and empty queries;
- one present or absent entry;
- duplicates and unsorted inputs;
- negative IDs, repeated queries, and boundary misses;
- present and absent queries in a deliberately mixed order;
- exact Boolean output order and type; and
- unchanged list and tuple inputs.

See [`DEVELOPMENT_LOG.md`](DEVELOPMENT_LOG.md) for the failing baseline, manual
trace, revision record, and AI-use disclosure.

## Synthetic data and measurement

`synthetic_data.py` uses a local seeded random generator and guarantees the
requested number of hits and misses. It is independent of both the algorithms
and benchmark code. Larger arrays intentionally contain duplicate IDs.

`benchmark.py` measures all four preserved implementations on identical data.
Data generation is excluded from timing; each algorithm's own sorting or set
construction is included. Seven runs per case are summarized by the median and
written to JSON and CSV. `dashboard.py` turns the JSON into a self-contained
HTML dashboard without external JavaScript or plotting libraries.

On the recorded 10,000-ID, 500-query case, the observed medians were:

| Implementation | Median runtime |
|---|---:|
| Hash set membership | 0.151958 ms |
| Binary search iterative v2 | 1.200667 ms |
| Binary search recursive v1 | 1.279875 ms |
| Linear search | 28.626750 ms |

These values describe one machine and one run; rerun the benchmark before
making environment-independent performance claims.

## Project layout

| Path | Purpose |
|---|---|
| `search_algorithms.py` | Required methods and preserved recursive version |
| `synthetic_data.py` | Deterministic input generation |
| `benchmark.py` | Correctness-checked runtime measurement and JSON/CSV output |
| `dashboard.py` | Self-contained HTML dashboard generation |
| `tests/` | Shared algorithm, generator, and pipeline tests |
| `results/` | Recorded measurements and generated dashboard |
| `DEVELOPMENT_LOG.md` | Test-first, trace, revision, and AI-use evidence |

## Phase 2 — Audit

The selected classmate implementation, reproduction steps, correctness
findings, and performance evidence will be added here during Phase 2.
