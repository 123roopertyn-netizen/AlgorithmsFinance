# Limit order book report

**Evidence status:** Canonical clean-tree evidence.

Run label: `canonical`. Recorded code commit: `ffb474170b4849af850e31588f9a1a70dcf08da3`. The saved report contains 73 datasets and 3744 records.

## Specification and boundaries

This project implements a sequential single-venue BTC limit order book with integer cent prices and integer 10^-8 BTC quantities. Better prices execute first and FIFO breaks ties. Trades use the resting maker price. A market sell consumes bids and discards any residual. The model intentionally excludes fees, balances, hidden orders, self-trade checks, simultaneous execution, networking, and historical exchange calibration; it is not a production trading system.

## Correctness evidence

Completed correctness rows passing ordered-result and final-book agreement: 76/76; 15 were stopped by the declared limit and 0 completed rows disagreed. Independent tests additionally cover worked fills, price-time priority, partial fills, cancellation, atomic validation, quantity/proceeds conservation, input immutability, and defensive inspection copies. Agreement is supporting evidence rather than a proof.

## Implementation and revision

Version A stores active makers in one list and scans for duplicates, cancellations, and the best maker. Version B indexes active identifiers and insertion-ordered FIFO price levels, with sorted price keys and eager empty-level cleanup. Both preserve the same API and tests. The revision targets work that grows with active depth while avoiding tombstones under cancellation churn. Detailed invariants, complexity, and AI decisions are recorded in `IMPLEMENTATION_NOTES.md`.

## Runtime and throughput

| Experiment | Scenario | M | Levels | Version | Phase | Sale % | Seeds | Median seconds | Median events/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 10 | 3 | 0.030877 | 32,419 |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 100 | 3 | 0.068855 | 14,538 |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 200 | 3 | 0.068566 | 14,599 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 10 | 3 | 0.003261 | 306,941 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 100 | 3 | 0.003818 | 262,171 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 200 | 3 | 0.003816 | 262,296 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 10 | 3 | 2.808623 | 3,561 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 100 | 3 | 6.754368 | 1,481 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 200 | 3 | 6.732400 | 1,486 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 10 | 3 | 0.033943 | 294,643 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 100 | 3 | 0.039692 | 251,962 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 200 | 3 | 0.039293 | 254,526 |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 10 | 3 | 0.451426 | 221,522 |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 100 | 3 | 0.547992 | 182,486 |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 200 | 3 | 0.545297 | 183,388 |
| queue_concentration | buildup | 1000 | 1000 | baseline | application_total | - | 3 | 0.028474 | 35,119 |
| queue_concentration | buildup | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.026844 | 37,252 |
| queue_concentration | buildup | 1000 | 1000 | revised | application_total | - | 3 | 0.003441 | 290,578 |
| queue_concentration | buildup | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001815 | 551,002 |
| queue_concentration | buildup | 1000 | 4 | baseline | application_total | - | 3 | 0.028330 | 35,298 |
| queue_concentration | buildup | 1000 | 4 | baseline | engine_replay | - | 3 | 0.026727 | 37,416 |
| queue_concentration | buildup | 1000 | 4 | revised | application_total | - | 3 | 0.003236 | 308,984 |
| queue_concentration | buildup | 1000 | 4 | revised | engine_replay | - | 3 | 0.001617 | 618,429 |
| queue_concentration | buildup | 10000 | 1000 | baseline | application_total | - | 3 | 2.622954 | 3,812 |
| queue_concentration | buildup | 10000 | 1000 | baseline | engine_replay | - | 3 | 2.605811 | 3,838 |
| queue_concentration | buildup | 10000 | 1000 | revised | application_total | - | 3 | 0.035071 | 285,133 |
| queue_concentration | buildup | 10000 | 1000 | revised | engine_replay | - | 3 | 0.017803 | 561,691 |
| queue_concentration | buildup | 10000 | 4 | baseline | application_total | - | 3 | 2.606720 | 3,836 |
| queue_concentration | buildup | 10000 | 4 | baseline | engine_replay | - | 3 | 2.589808 | 3,861 |
| queue_concentration | buildup | 10000 | 4 | revised | application_total | - | 3 | 0.034447 | 290,302 |
| queue_concentration | buildup | 10000 | 4 | revised | engine_replay | - | 3 | 0.017187 | 581,828 |
| queue_concentration | buildup | 100000 | 1000 | revised | application_total | - | 3 | 0.461015 | 216,913 |
| queue_concentration | buildup | 100000 | 1000 | revised | engine_replay | - | 3 | 0.202825 | 493,035 |
| queue_concentration | buildup | 100000 | 4 | revised | application_total | - | 3 | 0.446263 | 224,083 |
| queue_concentration | buildup | 100000 | 4 | revised | engine_replay | - | 3 | 0.196934 | 507,784 |
| stream | buildup | 1000 | 1000 | baseline | application_total | - | 3 | 0.028626 | 34,933 |
| stream | buildup | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.026977 | 37,069 |
| stream | buildup | 1000 | 1000 | revised | application_total | - | 3 | 0.003445 | 290,262 |
| stream | buildup | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001805 | 554,017 |
| stream | buildup | 10000 | 1000 | baseline | application_total | - | 3 | 2.846746 | 3,513 |
| stream | buildup | 10000 | 1000 | baseline | engine_replay | - | 3 | 2.829549 | 3,534 |
| stream | buildup | 10000 | 1000 | revised | application_total | - | 3 | 0.036140 | 276,702 |
| stream | buildup | 10000 | 1000 | revised | engine_replay | - | 3 | 0.017990 | 555,861 |
| stream | buildup | 100000 | 1000 | revised | application_total | - | 3 | 0.460224 | 217,286 |
| stream | buildup | 100000 | 1000 | revised | engine_replay | - | 3 | 0.200295 | 499,264 |
| stream | cancel_churn | 1000 | 1000 | baseline | application_total | - | 3 | 0.002512 | 398,083 |
| stream | cancel_churn | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.001122 | 891,100 |
| stream | cancel_churn | 1000 | 1000 | revised | application_total | - | 3 | 0.002767 | 361,451 |
| stream | cancel_churn | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001269 | 787,737 |
| stream | cancel_churn | 10000 | 1000 | baseline | application_total | - | 3 | 0.026635 | 375,445 |
| stream | cancel_churn | 10000 | 1000 | baseline | engine_replay | - | 3 | 0.011606 | 861,639 |
| stream | cancel_churn | 10000 | 1000 | revised | application_total | - | 3 | 0.028286 | 353,533 |
| stream | cancel_churn | 10000 | 1000 | revised | engine_replay | - | 3 | 0.012855 | 777,900 |
| stream | cancel_churn | 100000 | 1000 | baseline | application_total | - | 3 | 0.288683 | 346,401 |
| stream | cancel_churn | 100000 | 1000 | baseline | engine_replay | - | 3 | 0.115329 | 867,081 |
| stream | cancel_churn | 100000 | 1000 | revised | application_total | - | 3 | 0.300751 | 332,501 |
| stream | cancel_churn | 100000 | 1000 | revised | engine_replay | - | 3 | 0.127709 | 783,028 |
| stream | crowded | 1000 | 1000 | baseline | application_total | - | 3 | 0.028611 | 34,951 |
| stream | crowded | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.026955 | 37,099 |
| stream | crowded | 1000 | 1000 | revised | application_total | - | 3 | 0.003250 | 307,653 |
| stream | crowded | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001614 | 619,723 |
| stream | crowded | 10000 | 1000 | baseline | application_total | - | 3 | 2.642681 | 3,784 |
| stream | crowded | 10000 | 1000 | baseline | engine_replay | - | 3 | 2.622336 | 3,813 |
| stream | crowded | 10000 | 1000 | revised | application_total | - | 3 | 0.035009 | 285,640 |
| stream | crowded | 10000 | 1000 | revised | engine_replay | - | 3 | 0.017416 | 574,181 |
| stream | crowded | 100000 | 1000 | revised | application_total | - | 3 | 0.455193 | 219,687 |
| stream | crowded | 100000 | 1000 | revised | engine_replay | - | 3 | 0.195456 | 511,624 |
| stream | mixed | 1000 | 1000 | baseline | application_total | - | 3 | 0.007030 | 142,241 |
| stream | mixed | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.005253 | 190,364 |
| stream | mixed | 1000 | 1000 | revised | application_total | - | 3 | 0.003602 | 277,611 |
| stream | mixed | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001621 | 616,729 |
| stream | mixed | 10000 | 1000 | baseline | application_total | - | 3 | 0.441307 | 22,660 |
| stream | mixed | 10000 | 1000 | baseline | engine_replay | - | 3 | 0.425052 | 23,527 |
| stream | mixed | 10000 | 1000 | revised | application_total | - | 3 | 0.033160 | 301,572 |
| stream | mixed | 10000 | 1000 | revised | engine_replay | - | 3 | 0.016832 | 594,095 |
| stream | mixed | 100000 | 1000 | revised | application_total | - | 3 | 0.352584 | 283,621 |
| stream | mixed | 100000 | 1000 | revised | engine_replay | - | 3 | 0.167834 | 595,825 |
| stream | mixed | 1000000 | 1000 | revised | application_total | - | 1 | 8.346482 | 119,811 |
| stream | mixed | 1000000 | 1000 | revised | engine_replay | - | 1 | 2.179653 | 458,789 |
| stream | sweep | 1000 | 1000 | baseline | application_total | - | 3 | 0.037730 | 26,504 |
| stream | sweep | 1000 | 1000 | baseline | engine_replay | - | 3 | 0.036152 | 27,661 |
| stream | sweep | 1000 | 1000 | revised | application_total | - | 3 | 0.003543 | 282,277 |
| stream | sweep | 1000 | 1000 | revised | engine_replay | - | 3 | 0.001949 | 512,963 |
| stream | sweep | 10000 | 1000 | baseline | application_total | - | 3 | 3.755908 | 2,662 |
| stream | sweep | 10000 | 1000 | baseline | engine_replay | - | 3 | 3.735259 | 2,677 |
| stream | sweep | 10000 | 1000 | revised | application_total | - | 3 | 0.040099 | 249,380 |
| stream | sweep | 10000 | 1000 | revised | engine_replay | - | 3 | 0.019533 | 511,963 |
| stream | sweep | 100000 | 1000 | revised | application_total | - | 3 | 0.427929 | 233,683 |
| stream | sweep | 100000 | 1000 | revised | engine_replay | - | 3 | 0.217126 | 460,561 |

Input reading/parsing is measured separately. `engine_replay` includes fresh empty-book construction and event processing; `application_total` adds the paired parse repeat. All displayed values are medians of saved raw repeats, not reciprocal-latency estimates.

## Processing latency

| Experiment | Scenario | M | Levels | Version | Seeds | p50 ns | p95 ns | p99 ns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| queue_concentration | buildup | 1000 | 1000 | baseline | 3 | 26,500 | 49,958 | 51,917 |
| queue_concentration | buildup | 1000 | 1000 | revised | 3 | 1,833 | 1,958 | 2,291 |
| queue_concentration | buildup | 1000 | 4 | baseline | 3 | 26,666 | 49,334 | 51,958 |
| queue_concentration | buildup | 1000 | 4 | revised | 3 | 1,625 | 1,791 | 2,125 |
| queue_concentration | buildup | 10000 | 1000 | baseline | 3 | 258,375 | 493,833 | 533,708 |
| queue_concentration | buildup | 10000 | 1000 | revised | 3 | 1,708 | 2,042 | 2,250 |
| queue_concentration | buildup | 10000 | 4 | baseline | 3 | 258,584 | 516,917 | 648,167 |
| queue_concentration | buildup | 10000 | 4 | revised | 3 | 1,666 | 1,833 | 2,000 |
| queue_concentration | buildup | 100000 | 1000 | revised | 3 | 1,833 | 2,291 | 2,750 |
| queue_concentration | buildup | 100000 | 4 | revised | 3 | 1,791 | 2,167 | 2,458 |
| stream | buildup | 1000 | 1000 | baseline | 3 | 28,041 | 50,500 | 52,541 |
| stream | buildup | 1000 | 1000 | revised | 3 | 1,834 | 2,042 | 2,334 |
| stream | buildup | 10000 | 1000 | baseline | 3 | 265,958 | 502,666 | 628,833 |
| stream | buildup | 10000 | 1000 | revised | 3 | 1,708 | 2,042 | 2,333 |
| stream | buildup | 100000 | 1000 | revised | 3 | 1,833 | 2,333 | 2,833 |
| stream | cancel_churn | 1000 | 1000 | baseline | 3 | 1,209 | 1,500 | 1,542 |
| stream | cancel_churn | 1000 | 1000 | revised | 3 | 1,416 | 1,625 | 1,708 |
| stream | cancel_churn | 10000 | 1000 | baseline | 3 | 1,375 | 1,583 | 1,708 |
| stream | cancel_churn | 10000 | 1000 | revised | 3 | 1,417 | 1,625 | 1,791 |
| stream | cancel_churn | 100000 | 1000 | baseline | 3 | 1,375 | 1,583 | 1,708 |
| stream | cancel_churn | 100000 | 1000 | revised | 3 | 1,417 | 1,708 | 1,833 |
| stream | crowded | 1000 | 1000 | baseline | 3 | 26,750 | 49,791 | 52,750 |
| stream | crowded | 1000 | 1000 | revised | 3 | 1,625 | 1,791 | 1,958 |
| stream | crowded | 10000 | 1000 | baseline | 3 | 260,125 | 499,666 | 607,791 |
| stream | crowded | 10000 | 1000 | revised | 3 | 1,666 | 1,833 | 2,083 |
| stream | crowded | 100000 | 1000 | revised | 3 | 1,750 | 2,167 | 2,458 |
| stream | mixed | 1000 | 1000 | baseline | 3 | 4,000 | 12,917 | 24,875 |
| stream | mixed | 1000 | 1000 | revised | 3 | 1,709 | 3,083 | 4,542 |
| stream | mixed | 10000 | 1000 | baseline | 3 | 29,916 | 114,209 | 258,000 |
| stream | mixed | 10000 | 1000 | revised | 3 | 1,709 | 3,042 | 5,291 |
| stream | mixed | 100000 | 1000 | revised | 3 | 1,708 | 3,083 | 5,208 |
| stream | mixed | 1000000 | 1000 | revised | 1 | 1,792 | 3,333 | 5,625 |
| stream | sweep | 1000 | 1000 | baseline | 3 | 22,291 | 158,875 | 297,542 |
| stream | sweep | 1000 | 1000 | revised | 3 | 1,833 | 3,916 | 6,000 |
| stream | sweep | 10000 | 1000 | baseline | 3 | 212,042 | 1,591,458 | 3,403,208 |
| stream | sweep | 10000 | 1000 | revised | 3 | 1,750 | 3,792 | 5,792 |
| stream | sweep | 100000 | 1000 | revised | 3 | 1,792 | 4,750 | 7,500 |

Latency is instrumented separately with `perf_counter_ns`, retained per event, and summarized with nearest-rank percentiles. Saved records also separate LIMIT, CANCEL, and MARKET_SELL events and compare the first and last 10% (capped at 1,000 events).

## Memory

| Experiment | Scenario | M | Levels | Version | Seeds | Current MiB | Peak MiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| queue_concentration | buildup | 1000 | 1000 | baseline | 3 | 0.078 | 0.079 |
| queue_concentration | buildup | 1000 | 1000 | revised | 3 | 0.290 | 0.290 |
| queue_concentration | buildup | 1000 | 4 | baseline | 3 | 0.078 | 0.079 |
| queue_concentration | buildup | 1000 | 4 | revised | 3 | 0.122 | 0.123 |
| queue_concentration | buildup | 10000 | 1000 | baseline | 3 | 0.769 | 0.770 |
| queue_concentration | buildup | 10000 | 1000 | revised | 3 | 1.429 | 1.430 |
| queue_concentration | buildup | 10000 | 4 | baseline | 3 | 0.769 | 0.770 |
| queue_concentration | buildup | 10000 | 4 | revised | 3 | 1.086 | 1.087 |
| queue_concentration | buildup | 100000 | 1000 | revised | 3 | 13.472 | 14.033 |
| queue_concentration | buildup | 100000 | 4 | revised | 3 | 13.704 | 13.880 |
| stream | buildup | 1000 | 1000 | baseline | 3 | 0.078 | 0.079 |
| stream | buildup | 1000 | 1000 | revised | 3 | 0.290 | 0.290 |
| stream | buildup | 10000 | 1000 | baseline | 3 | 0.769 | 0.770 |
| stream | buildup | 10000 | 1000 | revised | 3 | 1.429 | 1.430 |
| stream | buildup | 100000 | 1000 | revised | 3 | 13.472 | 14.033 |
| stream | cancel_churn | 1000 | 1000 | baseline | 3 | 0.001 | 0.002 |
| stream | cancel_churn | 1000 | 1000 | revised | 3 | 0.002 | 0.003 |
| stream | cancel_churn | 10000 | 1000 | baseline | 3 | 0.001 | 0.002 |
| stream | cancel_churn | 10000 | 1000 | revised | 3 | 0.002 | 0.003 |
| stream | cancel_churn | 100000 | 1000 | baseline | 3 | 0.001 | 0.002 |
| stream | cancel_churn | 100000 | 1000 | revised | 3 | 0.002 | 0.003 |
| stream | crowded | 1000 | 1000 | baseline | 3 | 0.078 | 0.079 |
| stream | crowded | 1000 | 1000 | revised | 3 | 0.122 | 0.123 |
| stream | crowded | 10000 | 1000 | baseline | 3 | 0.769 | 0.770 |
| stream | crowded | 10000 | 1000 | revised | 3 | 1.086 | 1.087 |
| stream | crowded | 100000 | 1000 | revised | 3 | 13.704 | 13.880 |
| stream | mixed | 1000 | 1000 | baseline | 3 | 0.016 | 0.017 |
| stream | mixed | 1000 | 1000 | revised | 3 | 0.061 | 0.061 |
| stream | mixed | 10000 | 1000 | baseline | 3 | 0.127 | 0.129 |
| stream | mixed | 10000 | 1000 | revised | 3 | 0.394 | 0.432 |
| stream | mixed | 100000 | 1000 | revised | 3 | 2.601 | 2.841 |
| stream | mixed | 1000000 | 1000 | revised | 1 | 23.107 | 23.108 |
| stream | sweep | 1000 | 1000 | baseline | 3 | 0.036 | 0.066 |
| stream | sweep | 1000 | 1000 | revised | 3 | 0.159 | 0.232 |
| stream | sweep | 10000 | 1000 | revised | 3 | 0.786 | 1.258 |
| stream | sweep | 100000 | 1000 | revised | 3 | 5.739 | 9.534 |

Inputs are prepared before each fresh `tracemalloc` run and excluded. The live book, indexes/levels, final output, and negligible checkpoint integer bookkeeping are included; prior outputs are released. Native/process allocations are excluded, so these values are neither auxiliary space alone nor RSS.

## Large liquidation

| Setup orders | Version | Sale % | Seeds | Median sale seconds |
| --- | --- | --- | --- | --- |
| 1000 | baseline | 10 | 3 | 0.009509 |
| 1000 | baseline | 100 | 3 | 0.047190 |
| 1000 | baseline | 200 | 3 | 0.047306 |
| 1000 | revised | 10 | 3 | 0.000075 |
| 1000 | revised | 100 | 3 | 0.000645 |
| 1000 | revised | 200 | 3 | 0.000638 |
| 10000 | baseline | 10 | 3 | 0.925485 |
| 10000 | baseline | 100 | 3 | 4.851468 |
| 10000 | baseline | 200 | 3 | 4.844833 |
| 10000 | revised | 10 | 3 | 0.000672 |
| 10000 | revised | 100 | 3 | 0.006088 |
| 10000 | revised | 200 | 3 | 0.005958 |
| 100000 | revised | 10 | 3 | 0.009018 |
| 100000 | revised | 100 | 3 | 0.085337 |
| 100000 | revised | 200 | 3 | 0.084580 |

Each percentage is evaluated against a freshly rebuilt identical bid book. Saved correctness rows contain requested quantity, makers touched, price levels visited, fills, and unfilled residual.

## Bottleneck and operation counts

| Dataset | M | Active peak | Level peak | Fills | Visited levels | Final active |
| --- | --- | --- | --- | --- | --- | --- |
| liquidation__bid_book__m100000__seed42__levels1000 | 100000 | 100000 | 1000 | 0 | 0 | 100000 |
| liquidation__bid_book__m100000__seed43__levels1000 | 100000 | 100000 | 1000 | 0 | 0 | 100000 |
| liquidation__bid_book__m100000__seed44__levels1000 | 100000 | 100000 | 1000 | 0 | 0 | 100000 |
| liquidation__bid_book__m10000__seed42__levels1000 | 10000 | 10000 | 1000 | 0 | 0 | 10000 |
| liquidation__bid_book__m10000__seed43__levels1000 | 10000 | 10000 | 1000 | 0 | 0 | 10000 |
| liquidation__bid_book__m10000__seed44__levels1000 | 10000 | 10000 | 1000 | 0 | 0 | 10000 |
| liquidation__bid_book__m1000__seed42__levels1000 | 1000 | 1000 | 620 | 0 | 0 | 1000 |
| liquidation__bid_book__m1000__seed43__levels1000 | 1000 | 1000 | 621 | 0 | 0 | 1000 |
| liquidation__bid_book__m1000__seed44__levels1000 | 1000 | 1000 | 634 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed42__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| queue_concentration__buildup__m100000__seed42__levels4 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| queue_concentration__buildup__m100000__seed43__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| queue_concentration__buildup__m100000__seed43__levels4 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| queue_concentration__buildup__m100000__seed44__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| queue_concentration__buildup__m100000__seed44__levels4 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| queue_concentration__buildup__m10000__seed42__levels1000 | 10000 | 10000 | 1977 | 0 | 0 | 10000 |
| queue_concentration__buildup__m10000__seed42__levels4 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| queue_concentration__buildup__m10000__seed43__levels1000 | 10000 | 10000 | 1989 | 0 | 0 | 10000 |
| queue_concentration__buildup__m10000__seed43__levels4 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| queue_concentration__buildup__m10000__seed44__levels1000 | 10000 | 10000 | 1987 | 0 | 0 | 10000 |
| queue_concentration__buildup__m10000__seed44__levels4 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| queue_concentration__buildup__m1000__seed42__levels1000 | 1000 | 1000 | 805 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed42__levels4 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed43__levels1000 | 1000 | 1000 | 801 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed43__levels4 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed44__levels1000 | 1000 | 1000 | 775 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed44__levels4 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__buildup__m100000__seed42__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| stream__buildup__m100000__seed43__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| stream__buildup__m100000__seed44__levels1000 | 100000 | 100000 | 2000 | 0 | 0 | 100000 |
| stream__buildup__m10000__seed42__levels1000 | 10000 | 10000 | 1977 | 0 | 0 | 10000 |
| stream__buildup__m10000__seed43__levels1000 | 10000 | 10000 | 1989 | 0 | 0 | 10000 |
| stream__buildup__m10000__seed44__levels1000 | 10000 | 10000 | 1987 | 0 | 0 | 10000 |
| stream__buildup__m1000__seed42__levels1000 | 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed43__levels1000 | 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed44__levels1000 | 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__cancel_churn__m100000__seed42__levels1000 | 100000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m100000__seed43__levels1000 | 100000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m100000__seed44__levels1000 | 100000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed42__levels1000 | 10000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed43__levels1000 | 10000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed44__levels1000 | 10000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed42__levels1000 | 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed43__levels1000 | 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed44__levels1000 | 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__crowded__m100000__seed42__levels1000 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| stream__crowded__m100000__seed43__levels1000 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| stream__crowded__m100000__seed44__levels1000 | 100000 | 100000 | 8 | 0 | 0 | 100000 |
| stream__crowded__m10000__seed42__levels1000 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| stream__crowded__m10000__seed43__levels1000 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| stream__crowded__m10000__seed44__levels1000 | 10000 | 10000 | 8 | 0 | 0 | 10000 |
| stream__crowded__m1000__seed42__levels1000 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m1000__seed43__levels1000 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m1000__seed44__levels1000 | 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__mixed__m1000000__seed43__levels1000 | 1000000 | 151350 | 912 | 390254 | 379475 | 151349 |
| stream__mixed__m100000__seed42__levels1000 | 100000 | 15118 | 894 | 38988 | 37945 | 15113 |
| stream__mixed__m100000__seed43__levels1000 | 100000 | 15358 | 908 | 38797 | 37739 | 15357 |
| stream__mixed__m100000__seed44__levels1000 | 100000 | 15158 | 884 | 39216 | 38243 | 15155 |
| stream__mixed__m10000__seed42__levels1000 | 10000 | 1588 | 752 | 3926 | 3853 | 1587 |
| stream__mixed__m10000__seed43__levels1000 | 10000 | 1634 | 753 | 3905 | 3811 | 1622 |
| stream__mixed__m10000__seed44__levels1000 | 10000 | 1495 | 717 | 4002 | 3908 | 1491 |
| stream__mixed__m1000__seed42__levels1000 | 1000 | 140 | 126 | 374 | 359 | 138 |
| stream__mixed__m1000__seed43__levels1000 | 1000 | 181 | 161 | 354 | 341 | 179 |
| stream__mixed__m1000__seed44__levels1000 | 1000 | 162 | 152 | 390 | 381 | 162 |
| stream__sweep__m100000__seed42__levels1000 | 100000 | 80000 | 2000 | 50035 | 10971 | 39936 |
| stream__sweep__m100000__seed43__levels1000 | 100000 | 80000 | 2000 | 49934 | 11010 | 40076 |
| stream__sweep__m100000__seed44__levels1000 | 100000 | 80000 | 2000 | 50037 | 11038 | 40001 |
| stream__sweep__m10000__seed42__levels1000 | 10000 | 8000 | 1959 | 5035 | 1954 | 3938 |
| stream__sweep__m10000__seed43__levels1000 | 10000 | 8000 | 1966 | 4997 | 1977 | 3998 |
| stream__sweep__m10000__seed44__levels1000 | 10000 | 8000 | 1967 | 5055 | 2006 | 3967 |
| stream__sweep__m1000__seed42__levels1000 | 1000 | 800 | 661 | 496 | 427 | 411 |
| stream__sweep__m1000__seed43__levels1000 | 1000 | 800 | 666 | 510 | 442 | 389 |
| stream__sweep__m1000__seed44__levels1000 | 1000 | 800 | 647 | 483 | 419 | 418 |

The baseline can rescan B active orders for validation and each maker fill; the revision usually performs indexed lookup and FIFO-level access but pays O(P) when inserting or deleting a sorted price key. The active-depth, price-level, and fill counts above explain why performance can vary by workload; no claim assumes the revision wins everywhere.

## Limitations

Stopped saved records: 524. Declared stops are not extrapolated. Results are machine- and interpreter-specific synthetic measurements. Sequential processing excludes networking and queueing, so throughput does not establish live-venue overload capacity. The supplied data are teaching workloads rather than historical or calibrated market data. Passing tests and cross-version agreement do not constitute a formal proof.

## Reproducibility

Python: `3.14.7`; platform: `macOS-15.5-arm64-arm-64bit-Mach-O`; dirty tree: `False`.

Recorded measurement command:

```text
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/run_benchmarks.py --profile canonical --time-limit-seconds 5 --output results/raw_measurements.json.gz
```

Run `python3 -m unittest discover -s tests -v`, rebuild the dashboard from the saved result file with `python3 dashboard.py`, and consult `MEASUREMENT_PLAN.md` for exact data preparation, timing, latency, and memory boundaries.
