# AmbassaStephaneMartin

Name: Stéphane Martin Ambassa

Initial identification submission for Algorithms in Finance. The implementation will follow.

## Test-first plan

The project will compare a manually implemented linear search, a manually
implemented binary search on a sorted copy, and Python set membership. All three
will have the interface `method(ids, queries) -> list[bool]` and receive the same
tests. The original ID array and query list must retain their values and order.

The planned module is `search_algorithms.py`, exporting `linear_search`,
`binary_search`, and `hash_set_membership`. It has not been implemented yet.

| Test group | What it checks |
| --- | --- |
| Empty arrays and queries | One answer per query, including zero answers |
| Singleton and boundaries | First/last positions and missing neighboring IDs |
| Unsorted and reverse-sorted arrays | Correct answers without sorting the input in place |
| Duplicates and repeated queries | Every query gets its own answer in the original order |
| Negative, zero, and very large IDs | Integer equality without loss of precision |
| All hits and all misses | Correct handling of both extremes |
| Input preservation and repeated calls | Neither input is modified; answers reflect the current array |
| Seeded random cases and all 15 saved datasets | Agreement with independent expected answers |
| Synthetic data validation | Correct labels, metadata, hit rates, and repeatable generation |

Every shared search check also requires a list containing actual Boolean values,
not integer `0`/`1` substitutes. The suite uses only Python's standard library.
Timing measurements will be added separately; correctness tests do not enforce
machine-dependent runtime thresholds.

## Reproduce the data and run tests

Open a terminal in `Submissions/AmbassaStephaneMartin/` and run:

```console
python --version
python generate_data.py
python -B -m unittest discover -s tests -p test_data.py -v
python -B -m unittest discover -s tests -v
```

The data command creates six small correctness datasets and nine benchmark
datasets. Benchmarks use 100, 1,000, or 10,000 stored IDs, 1,000 queries, and
0%, 50%, or 100% successful queries. Seeds and dataset dimensions are saved in
each file's metadata. For a given array size, all three hit-rate variants use
the same input array. Record the Python version when reproducing results.

Random benchmark IDs are even integers. Successful queries are sampled from
the actual array; missing queries are odd integers spread across the value
range. Query/answer pairs are shuffled together. This gives known labels
without relying on a search implementation. It is a controlled synthetic
distribution, rather than a claim about every real financial workload.

Validated with Python 3.14.5: all seven data-only tests passed. The shared search
contract defines 15 test methods reused by each of the three implementations,
for 45 search tests. The full test command is expected to report
`ModuleNotFoundError: No module named 'search_algorithms'` until the three search
functions are implemented. This is the intended failing state before
implementation, not a completed correctness result for the algorithms.
