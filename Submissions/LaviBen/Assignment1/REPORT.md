# Limit order book report

**Evidence status:** PROVISIONAL: this report was produced from a noncanonical or dirty-tree run.

Run label: `provisional_smoke`. Recorded code commit: `8788d13b6a59aadfa9785cbc31967dce2cc4e4fe`. The saved report contains 8 datasets and 232 records.

## Specification and boundaries

This project implements a sequential single-venue BTC limit order book with integer cent prices and integer 10^-8 BTC quantities. Better prices execute first and FIFO breaks ties. Trades use the resting maker price. A market sell consumes bids and discards any residual. The model intentionally excludes fees, balances, hidden orders, self-trade checks, simultaneous execution, networking, and historical exchange calibration; it is not a production trading system.

## Correctness evidence

Saved correctness rows passing ordered-result and final-book agreement: 10/10. Independent tests additionally cover worked fills, price-time priority, partial fills, cancellation, atomic validation, quantity/proceeds conservation, input immutability, and defensive inspection copies. Agreement is supporting evidence rather than a proof.

## Implementation and revision

Version A stores active makers in one list and scans for duplicates, cancellations, and the best maker. Version B indexes active identifiers and insertion-ordered FIFO price levels, with sorted price keys and eager empty-level cleanup. Both preserve the same API and tests. The revision targets work that grows with active depth while avoiding tombstones under cancellation churn. Detailed invariants, complexity, and AI decisions are recorded in `IMPLEMENTATION_NOTES.md`.

## Runtime and throughput

| Scenario | M | Version | Phase | Sale % | Seeds | Median seconds | Median events/s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bid_book | 1000 | baseline | application_total | 10 | 1 | 0.030356 | 32,977 |
| bid_book | 1000 | baseline | application_total | 100 | 1 | 0.068641 | 14,583 |
| bid_book | 1000 | baseline | application_total | 200 | 1 | 0.068096 | 14,700 |
| bid_book | 1000 | revised | application_total | 10 | 1 | 0.003334 | 300,472 |
| bid_book | 1000 | revised | application_total | 100 | 1 | 0.003957 | 253,159 |
| bid_book | 1000 | revised | application_total | 200 | 1 | 0.004043 | 247,601 |
| buildup | 1000 | baseline | application_total | - | 3 | 0.028028 | 35,686 |
| buildup | 1000 | baseline | engine_replay | - | 3 | 0.026441 | 37,824 |
| buildup | 1000 | revised | application_total | - | 3 | 0.003423 | 292,126 |
| buildup | 1000 | revised | engine_replay | - | 3 | 0.001801 | 555,346 |
| cancel_churn | 1000 | baseline | application_total | - | 1 | 0.002717 | 369,158 |
| cancel_churn | 1000 | baseline | engine_replay | - | 1 | 0.001102 | 907,124 |
| cancel_churn | 1000 | revised | application_total | - | 1 | 0.002891 | 346,773 |
| cancel_churn | 1000 | revised | engine_replay | - | 1 | 0.001276 | 783,817 |
| crowded | 1000 | baseline | application_total | - | 1 | 0.028281 | 35,372 |
| crowded | 1000 | baseline | engine_replay | - | 1 | 0.026501 | 37,737 |
| crowded | 1000 | revised | application_total | - | 1 | 0.003496 | 291,031 |
| crowded | 1000 | revised | engine_replay | - | 1 | 0.001716 | 586,012 |
| mixed | 1000 | baseline | application_total | - | 1 | 0.006611 | 151,468 |
| mixed | 1000 | baseline | engine_replay | - | 1 | 0.004974 | 201,047 |
| mixed | 1000 | revised | application_total | - | 1 | 0.003225 | 312,086 |
| mixed | 1000 | revised | engine_replay | - | 1 | 0.001589 | 629,426 |
| sweep | 1000 | baseline | application_total | - | 1 | 0.036787 | 27,183 |
| sweep | 1000 | baseline | engine_replay | - | 1 | 0.035250 | 28,370 |
| sweep | 1000 | revised | application_total | - | 1 | 0.003487 | 287,006 |
| sweep | 1000 | revised | engine_replay | - | 1 | 0.001950 | 512,942 |

Input reading/parsing is measured separately. `engine_replay` includes fresh empty-book construction and event processing; `application_total` adds the paired parse repeat. All displayed values are medians of saved raw repeats, not reciprocal-latency estimates.

## Processing latency

| Scenario | M | Version | Seeds | p50 ns | p95 ns | p99 ns |
| --- | --- | --- | --- | --- | --- | --- |
| buildup | 1000 | baseline | 3 | 26,417 | 50,000 | 52,125 |
| buildup | 1000 | revised | 3 | 1,792 | 1,917 | 2,500 |
| cancel_churn | 1000 | baseline | 1 | 1,084 | 1,500 | 1,541 |
| cancel_churn | 1000 | revised | 1 | 1,334 | 1,542 | 1,584 |
| crowded | 1000 | baseline | 1 | 26,291 | 49,125 | 51,375 |
| crowded | 1000 | revised | 1 | 1,583 | 1,750 | 1,958 |
| mixed | 1000 | baseline | 1 | 3,750 | 11,125 | 22,500 |
| mixed | 1000 | revised | 1 | 1,666 | 3,083 | 4,750 |
| sweep | 1000 | baseline | 1 | 21,958 | 149,542 | 270,666 |
| sweep | 1000 | revised | 1 | 1,833 | 3,791 | 5,916 |

Latency is instrumented separately with `perf_counter_ns`, retained per event, and summarized with nearest-rank percentiles. Saved records also separate LIMIT, CANCEL, and MARKET_SELL events and compare the first and last 10% (capped at 1,000 events).

## Memory

| Scenario | M | Version | Seeds | Current MiB | Peak MiB |
| --- | --- | --- | --- | --- | --- |
| buildup | 1000 | baseline | 3 | 0.078 | 0.079 |
| buildup | 1000 | revised | 3 | 0.291 | 0.291 |
| cancel_churn | 1000 | baseline | 1 | 0.001 | 0.002 |
| cancel_churn | 1000 | revised | 1 | 0.002 | 0.003 |
| crowded | 1000 | baseline | 1 | 0.078 | 0.079 |
| crowded | 1000 | revised | 1 | 0.122 | 0.123 |
| mixed | 1000 | baseline | 1 | 0.014 | 0.015 |
| mixed | 1000 | revised | 1 | 0.054 | 0.058 |
| sweep | 1000 | baseline | 1 | 0.036 | 0.065 |
| sweep | 1000 | revised | 1 | 0.159 | 0.232 |

Inputs are prepared before each fresh `tracemalloc` run and excluded. The live book, indexes/levels, final output, and negligible checkpoint integer bookkeeping are included; prior outputs are released. Native/process allocations are excluded, so these values are neither auxiliary space alone nor RSS.

## Large liquidation

| Setup orders | Version | Sale % | Seeds | Median sale seconds |
| --- | --- | --- | --- | --- |
| 1000 | baseline | 10 | 1 | 0.008863 |
| 1000 | baseline | 100 | 1 | 0.047336 |
| 1000 | baseline | 200 | 1 | 0.046891 |
| 1000 | revised | 10 | 1 | 0.000075 |
| 1000 | revised | 100 | 1 | 0.000649 |
| 1000 | revised | 200 | 1 | 0.000749 |

Each percentage is evaluated against a freshly rebuilt identical bid book. Saved correctness rows contain requested quantity, makers touched, price levels visited, fills, and unfilled residual.

## Bottleneck and operation counts

| Dataset | M | Active peak | Level peak | Fills | Visited levels | Final active |
| --- | --- | --- | --- | --- | --- | --- |
| liquidation__bid_book__m1000__seed42__levels1000 | 1000 | 1000 | 620 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed42__levels1000 | 1000 | 1000 | 805 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed42__levels4 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed42__levels1000 | 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__cancel_churn__m1000__seed42__levels1000 | 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__crowded__m1000__seed42__levels1000 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__mixed__m1000__seed42__levels1000 | 1000 | 140 | 126 | 374 | 359 | 138 |
| stream__sweep__m1000__seed42__levels1000 | 1000 | 800 | 661 | 496 | 427 | 411 |

The baseline can rescan B active orders for validation and each maker fill; the revision usually performs indexed lookup and FIFO-level access but pays O(P) when inserting or deleting a sorted price key. The active-depth, price-level, and fill counts above explain why performance can vary by workload; no claim assumes the revision wins everywhere.

## Limitations

Stopped saved records: 0. Declared stops are not extrapolated. Results are machine- and interpreter-specific synthetic measurements. Sequential processing excludes networking and queueing, so throughput does not establish live-venue overload capacity. The supplied data are teaching workloads rather than historical or calibrated market data. Passing tests and cross-version agreement do not constitute a formal proof.

## Reproducibility

Python: `3.14.7`; platform: `macOS-15.5-arm64-arm-64bit-Mach-O`; dirty tree: `True`.

Recorded measurement command:

```text
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/run_benchmarks.py --profile smoke --output tmp/benchmark_smoke.json.gz
```

Run `python3 -m unittest discover -s tests -v`, rebuild the dashboard from the saved result file with `python3 dashboard.py`, and consult `MEASUREMENT_PLAN.md` for exact data preparation, timing, latency, and memory boundaries.
