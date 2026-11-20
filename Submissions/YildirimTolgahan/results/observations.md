# Current Windows measurements

CPython 3.13.12; grouped timeit protocol. n=100,000, q=100, 50 hits, unique IDs.
These are fresh local measurements, separate from the supplied Linux run.

| Method / version | Preparation (ms) | Query batch (microseconds) | Total (ms) | Peak (KiB) |
|---|---:|---:|---:|---:|
| linear / original | 1.438050 | 634702.900 | 433.852900 | 782.24 |
| linear / revised | 0.000175 | 469921.100 | 610.020100 | 0.94 |
| binary / original | 44.700700 | 1069.900 | 55.008100 | 1171.79 |
| binary / revised | 38.036300 | 820.033 | 42.574500 | 1171.79 |
| hash_set / original | 15.019800 | 21.509 | 15.615100 | 6144.26 |
| hash_set / revised | 16.652100 | 18.358 | 13.939800 | 6144.26 |

Preparation, query and total are independent phase measurements; values need not add up.
Five rounds are descriptive evidence, not a statistical significance test.
The unchanged hash-set control illustrates measurement variation. Removing the linear
copy reduces prepared storage; iteration removes recursive search frames, but sorting
still contributes most of the binary-search total. Compare all workloads and raw
rounds in dashboard.html and raw_repeats.csv before drawing a broader conclusion.
