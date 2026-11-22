# Limit order book report

**Evidence status:** Canonical clean-tree evidence.

Run label: `canonical`. Recorded code commit: `3d4bacb5eb2527ac9b5be709d8cfad74b2c4da90`. The saved report contains 73 datasets and 3744 records.

## Specification and boundaries

This project implements a sequential single-venue BTC limit order book with integer cent prices and integer 10^-8 BTC quantities. Better prices execute first and FIFO breaks ties. Trades use the resting maker price. A market sell consumes bids and discards any residual. The model intentionally excludes fees, balances, hidden orders, self-trade checks, simultaneous execution, networking, and historical exchange calibration; it is not a production trading system.

## Correctness evidence

Completed correctness rows passing ordered-result and final-book agreement: 76/76; 15 were stopped by the declared limit and 0 completed rows disagreed. Independent tests additionally cover worked fills, price-time priority, partial fills, cancellation, atomic validation, quantity/proceeds conservation, input immutability, and defensive inspection copies. Agreement is supporting evidence rather than a proof.

## Implementation and revision

Version A stores active makers in one list and scans for duplicates, cancellations, and the best maker. Version B indexes active identifiers and insertion-ordered FIFO price levels, with sorted price keys and eager empty-level cleanup. Both preserve the same API and tests. The revision targets work that grows with active depth while avoiding tombstones under cancellation churn. Detailed invariants, complexity, and AI decisions are recorded in `IMPLEMENTATION_NOTES.md`.

## Runtime and throughput

| Experiment | Scenario | M | Levels | Version | Phase | Sale % | Seeds | Repeat coverage | Median seconds | Median events/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 10 | 3 | 15/15 | 0.030691 | 32,616 |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 100 | 3 | 15/15 | 0.070792 | 14,140 |
| liquidation | bid_book | 1000 | 1000 | baseline | application_total | 200 | 3 | 15/15 | 0.071078 | 14,083 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 10 | 3 | 15/15 | 0.003262 | 306,851 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 100 | 3 | 15/15 | 0.003807 | 262,937 |
| liquidation | bid_book | 1000 | 1000 | revised | application_total | 200 | 3 | 15/15 | 0.003786 | 264,427 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 10 | 3 | 15/15 | 3.064555 | 3,263 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 100 | 3 | 7/15 (8 stopped) | 6.894240 | 1,451 |
| liquidation | bid_book | 10000 | 1000 | baseline | application_total | 200 | 3 | 5/15 (10 stopped) | 6.848496 | 1,461 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 10 | 3 | 15/15 | 0.034454 | 290,273 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 100 | 3 | 15/15 | 0.041967 | 238,307 |
| liquidation | bid_book | 10000 | 1000 | revised | application_total | 200 | 3 | 15/15 | 0.041076 | 243,477 |
| liquidation | bid_book | 100000 | 1000 | baseline | application_total | 10 | 3 | 0/15 (15 stopped) | - | - |
| liquidation | bid_book | 100000 | 1000 | baseline | application_total | 100 | 3 | 0/15 (15 stopped) | - | - |
| liquidation | bid_book | 100000 | 1000 | baseline | application_total | 200 | 3 | 0/15 (15 stopped) | - | - |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 10 | 3 | 15/15 | 0.370572 | 269,855 |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 100 | 3 | 15/15 | 0.447895 | 223,269 |
| liquidation | bid_book | 100000 | 1000 | revised | application_total | 200 | 3 | 15/15 | 0.448075 | 223,179 |
| queue_concentration | buildup | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.029479 | 33,923 |
| queue_concentration | buildup | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.027848 | 35,910 |
| queue_concentration | buildup | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.003526 | 283,614 |
| queue_concentration | buildup | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.001817 | 550,358 |
| queue_concentration | buildup | 1000 | 4 | baseline | application_total | - | 3 | 15/15 | 0.029144 | 34,313 |
| queue_concentration | buildup | 1000 | 4 | baseline | engine_replay | - | 3 | 15/15 | 0.027528 | 36,327 |
| queue_concentration | buildup | 1000 | 4 | revised | application_total | - | 3 | 15/15 | 0.003400 | 294,082 |
| queue_concentration | buildup | 1000 | 4 | revised | engine_replay | - | 3 | 15/15 | 0.001649 | 606,597 |
| queue_concentration | buildup | 10000 | 1000 | baseline | application_total | - | 3 | 15/15 | 2.702150 | 3,701 |
| queue_concentration | buildup | 10000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 2.685749 | 3,723 |
| queue_concentration | buildup | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.035632 | 280,650 |
| queue_concentration | buildup | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.019473 | 513,526 |
| queue_concentration | buildup | 10000 | 4 | baseline | application_total | - | 3 | 15/15 | 2.704931 | 3,697 |
| queue_concentration | buildup | 10000 | 4 | baseline | engine_replay | - | 3 | 15/15 | 2.686986 | 3,722 |
| queue_concentration | buildup | 10000 | 4 | revised | application_total | - | 3 | 15/15 | 0.033507 | 298,442 |
| queue_concentration | buildup | 10000 | 4 | revised | engine_replay | - | 3 | 15/15 | 0.017772 | 562,689 |
| queue_concentration | buildup | 100000 | 1000 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| queue_concentration | buildup | 100000 | 1000 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| queue_concentration | buildup | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.385406 | 259,467 |
| queue_concentration | buildup | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.208961 | 478,558 |
| queue_concentration | buildup | 100000 | 4 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| queue_concentration | buildup | 100000 | 4 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| queue_concentration | buildup | 100000 | 4 | revised | application_total | - | 3 | 15/15 | 0.392889 | 254,525 |
| queue_concentration | buildup | 100000 | 4 | revised | engine_replay | - | 3 | 15/15 | 0.211879 | 471,969 |
| stream | buildup | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.031257 | 31,993 |
| stream | buildup | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.029485 | 33,915 |
| stream | buildup | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.003760 | 265,993 |
| stream | buildup | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.002084 | 479,933 |
| stream | buildup | 10000 | 1000 | baseline | application_total | - | 3 | 14/15 (1 stopped) | 3.203840 | 3,121 |
| stream | buildup | 10000 | 1000 | baseline | engine_replay | - | 3 | 14/15 (1 stopped) | 3.187860 | 3,137 |
| stream | buildup | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.035832 | 279,078 |
| stream | buildup | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.019257 | 519,301 |
| stream | buildup | 100000 | 1000 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| stream | buildup | 100000 | 1000 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| stream | buildup | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.413757 | 241,688 |
| stream | buildup | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.206853 | 483,436 |
| stream | cancel_churn | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.002676 | 373,622 |
| stream | cancel_churn | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.001196 | 836,033 |
| stream | cancel_churn | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.002758 | 362,571 |
| stream | cancel_churn | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.001281 | 780,590 |
| stream | cancel_churn | 10000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.026823 | 372,814 |
| stream | cancel_churn | 10000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.012843 | 778,604 |
| stream | cancel_churn | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.028847 | 346,652 |
| stream | cancel_churn | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.013818 | 723,676 |
| stream | cancel_churn | 100000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.298643 | 334,847 |
| stream | cancel_churn | 100000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.134448 | 743,779 |
| stream | cancel_churn | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.299542 | 333,843 |
| stream | cancel_churn | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.139601 | 716,327 |
| stream | crowded | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.030870 | 32,393 |
| stream | crowded | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.029146 | 34,310 |
| stream | crowded | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.004644 | 215,341 |
| stream | crowded | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.001971 | 507,324 |
| stream | crowded | 10000 | 1000 | baseline | application_total | - | 3 | 15/15 | 2.676308 | 3,736 |
| stream | crowded | 10000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 2.660973 | 3,758 |
| stream | crowded | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.032983 | 303,189 |
| stream | crowded | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.017820 | 561,151 |
| stream | crowded | 100000 | 1000 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| stream | crowded | 100000 | 1000 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| stream | crowded | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.405911 | 246,359 |
| stream | crowded | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.206705 | 483,782 |
| stream | mixed | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.006485 | 154,207 |
| stream | mixed | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.004888 | 204,565 |
| stream | mixed | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.003251 | 307,613 |
| stream | mixed | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.001604 | 623,571 |
| stream | mixed | 10000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.425974 | 23,476 |
| stream | mixed | 10000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.410768 | 24,345 |
| stream | mixed | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.031908 | 313,405 |
| stream | mixed | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.017008 | 587,949 |
| stream | mixed | 100000 | 1000 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| stream | mixed | 100000 | 1000 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| stream | mixed | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.371775 | 268,980 |
| stream | mixed | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.170355 | 587,010 |
| stream | mixed | 1000000 | 1000 | baseline | application_total | - | 1 | 0/5 (5 stopped) | - | - |
| stream | mixed | 1000000 | 1000 | baseline | engine_replay | - | 1 | 0/5 (5 stopped) | - | - |
| stream | mixed | 1000000 | 1000 | revised | application_total | - | 1 | 5/5 | 5.283202 | 189,279 |
| stream | mixed | 1000000 | 1000 | revised | engine_replay | - | 1 | 5/5 | 2.072545 | 482,499 |
| stream | sweep | 1000 | 1000 | baseline | application_total | - | 3 | 15/15 | 0.038710 | 25,833 |
| stream | sweep | 1000 | 1000 | baseline | engine_replay | - | 3 | 15/15 | 0.037213 | 26,872 |
| stream | sweep | 1000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.003632 | 275,349 |
| stream | sweep | 1000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.001973 | 506,864 |
| stream | sweep | 10000 | 1000 | baseline | application_total | - | 3 | 13/15 (2 stopped) | 3.665088 | 2,728 |
| stream | sweep | 10000 | 1000 | baseline | engine_replay | - | 3 | 13/15 (2 stopped) | 3.650457 | 2,739 |
| stream | sweep | 10000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.035751 | 279,713 |
| stream | sweep | 10000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.019058 | 524,727 |
| stream | sweep | 100000 | 1000 | baseline | application_total | - | 3 | 0/15 (15 stopped) | - | - |
| stream | sweep | 100000 | 1000 | baseline | engine_replay | - | 3 | 0/15 (15 stopped) | - | - |
| stream | sweep | 100000 | 1000 | revised | application_total | - | 3 | 15/15 | 0.471719 | 211,991 |
| stream | sweep | 100000 | 1000 | revised | engine_replay | - | 3 | 15/15 | 0.221611 | 451,241 |

Input reading/parsing is measured separately. `engine_replay` includes fresh empty-book construction and event processing; `application_total` adds the paired parse repeat. All displayed values are medians of saved raw repeats, not reciprocal-latency estimates.

## Processing latency

| Experiment | Scenario | M | Levels | Version | Seeds | p50 ns | p95 ns | p99 ns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| queue_concentration | buildup | 1000 | 1000 | baseline | 3 | 29,666 | 51,584 | 57,125 |
| queue_concentration | buildup | 1000 | 1000 | revised | 3 | 1,875 | 2,084 | 2,583 |
| queue_concentration | buildup | 1000 | 4 | baseline | 3 | 27,792 | 51,584 | 57,250 |
| queue_concentration | buildup | 1000 | 4 | revised | 3 | 1,875 | 1,959 | 2,208 |
| queue_concentration | buildup | 10000 | 1000 | baseline | 3 | 265,000 | 506,291 | 658,750 |
| queue_concentration | buildup | 10000 | 1000 | revised | 3 | 1,834 | 2,208 | 2,875 |
| queue_concentration | buildup | 10000 | 4 | baseline | 3 | 261,000 | 502,917 | 637,916 |
| queue_concentration | buildup | 10000 | 4 | revised | 3 | 1,667 | 1,917 | 2,208 |
| queue_concentration | buildup | 100000 | 1000 | revised | 3 | 1,875 | 2,334 | 2,792 |
| queue_concentration | buildup | 100000 | 4 | revised | 3 | 1,792 | 2,208 | 2,542 |
| stream | buildup | 1000 | 1000 | baseline | 3 | 30,667 | 56,917 | 59,292 |
| stream | buildup | 1000 | 1000 | revised | 3 | 2,125 | 2,291 | 2,875 |
| stream | buildup | 10000 | 1000 | baseline | 3 | 270,042 | 562,208 | 658,333 |
| stream | buildup | 10000 | 1000 | revised | 3 | 1,833 | 2,208 | 4,125 |
| stream | buildup | 100000 | 1000 | revised | 3 | 1,834 | 2,292 | 2,750 |
| stream | cancel_churn | 1000 | 1000 | baseline | 3 | 1,167 | 1,584 | 1,667 |
| stream | cancel_churn | 1000 | 1000 | revised | 3 | 1,333 | 1,625 | 1,750 |
| stream | cancel_churn | 10000 | 1000 | baseline | 3 | 1,500 | 1,708 | 1,750 |
| stream | cancel_churn | 10000 | 1000 | revised | 3 | 1,541 | 1,792 | 1,875 |
| stream | cancel_churn | 100000 | 1000 | baseline | 3 | 1,416 | 1,791 | 1,875 |
| stream | cancel_churn | 100000 | 1000 | revised | 3 | 1,459 | 1,750 | 1,917 |
| stream | crowded | 1000 | 1000 | baseline | 3 | 28,417 | 52,459 | 59,750 |
| stream | crowded | 1000 | 1000 | revised | 3 | 1,792 | 2,000 | 2,250 |
| stream | crowded | 10000 | 1000 | baseline | 3 | 267,167 | 503,708 | 604,750 |
| stream | crowded | 10000 | 1000 | revised | 3 | 1,667 | 1,833 | 2,083 |
| stream | crowded | 100000 | 1000 | revised | 3 | 1,792 | 2,208 | 2,500 |
| stream | mixed | 1000 | 1000 | baseline | 3 | 3,917 | 12,417 | 27,666 |
| stream | mixed | 1000 | 1000 | revised | 3 | 1,750 | 2,834 | 3,959 |
| stream | mixed | 10000 | 1000 | baseline | 3 | 29,959 | 122,208 | 268,083 |
| stream | mixed | 10000 | 1000 | revised | 3 | 1,709 | 3,041 | 5,125 |
| stream | mixed | 100000 | 1000 | revised | 3 | 1,750 | 3,292 | 7,250 |
| stream | mixed | 1000000 | 1000 | revised | 1 | 1,833 | 3,209 | 5,334 |
| stream | sweep | 1000 | 1000 | baseline | 3 | 24,833 | 165,042 | 296,666 |
| stream | sweep | 1000 | 1000 | revised | 3 | 2,083 | 4,000 | 6,041 |
| stream | sweep | 10000 | 1000 | baseline | 3 | 215,583 | 1,690,041 | 3,286,208 |
| stream | sweep | 10000 | 1000 | revised | 3 | 1,708 | 3,833 | 5,584 |
| stream | sweep | 100000 | 1000 | revised | 3 | 1,875 | 5,125 | 8,208 |

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
| stream | sweep | 1000 | 1000 | baseline | 3 | 0.036 | 0.066 |
| stream | sweep | 1000 | 1000 | revised | 3 | 0.159 | 0.232 |
| stream | sweep | 10000 | 1000 | revised | 3 | 0.786 | 1.258 |
| stream | sweep | 100000 | 1000 | revised | 3 | 5.739 | 9.534 |

Inputs are prepared before each fresh `tracemalloc` run and excluded. The live book, indexes/levels, final output, and negligible checkpoint integer bookkeeping are included; prior outputs are released. Native/process allocations are excluded, so these values are neither auxiliary space alone nor RSS.

## Large liquidation

| Setup orders | Version | Sale % | Seeds | Repeat coverage | Median sale seconds |
| --- | --- | --- | --- | --- | --- |
| 1000 | baseline | 10 | 3 | 15/15 | 0.009481 |
| 1000 | baseline | 100 | 3 | 15/15 | 0.049139 |
| 1000 | baseline | 200 | 3 | 15/15 | 0.048852 |
| 1000 | revised | 10 | 3 | 15/15 | 0.000075 |
| 1000 | revised | 100 | 3 | 15/15 | 0.000651 |
| 1000 | revised | 200 | 3 | 15/15 | 0.000646 |
| 10000 | baseline | 10 | 3 | 15/15 | 1.002312 |
| 10000 | baseline | 100 | 3 | 7/15 (8 stopped) | 4.947157 |
| 10000 | baseline | 200 | 3 | 5/15 (10 stopped) | 4.912204 |
| 10000 | revised | 10 | 3 | 15/15 | 0.000716 |
| 10000 | revised | 100 | 3 | 15/15 | 0.007485 |
| 10000 | revised | 200 | 3 | 15/15 | 0.006615 |
| 100000 | baseline | 10 | 3 | 0/15 (15 stopped) | - |
| 100000 | baseline | 100 | 3 | 0/15 (15 stopped) | - |
| 100000 | baseline | 200 | 3 | 0/15 (15 stopped) | - |
| 100000 | revised | 10 | 3 | 15/15 | 0.008904 |
| 100000 | revised | 100 | 3 | 15/15 | 0.084841 |
| 100000 | revised | 200 | 3 | 15/15 | 0.085428 |

Each percentage is evaluated against a freshly rebuilt identical bid book. Saved correctness rows contain requested quantity, makers touched, price levels visited, fills, and unfilled residual.

## Bottleneck and operation counts

| Dataset | Requested / processed | Active peak | Level peak | Fills | Visited levels | Final active |
| --- | --- | --- | --- | --- | --- | --- |
| liquidation__bid_book__m100000__seed42__levels1000 | 1000 / 1000 | 1000 | 620 | 0 | 0 | 1000 |
| liquidation__bid_book__m100000__seed43__levels1000 | 1000 / 1000 | 1000 | 621 | 0 | 0 | 1000 |
| liquidation__bid_book__m100000__seed44__levels1000 | 1000 / 1000 | 1000 | 634 | 0 | 0 | 1000 |
| liquidation__bid_book__m10000__seed42__levels1000 | 1000 / 1000 | 1000 | 620 | 0 | 0 | 1000 |
| liquidation__bid_book__m10000__seed43__levels1000 | 1000 / 1000 | 1000 | 621 | 0 | 0 | 1000 |
| liquidation__bid_book__m10000__seed44__levels1000 | 1000 / 1000 | 1000 | 634 | 0 | 0 | 1000 |
| liquidation__bid_book__m1000__seed42__levels1000 | 1000 / 1000 | 1000 | 620 | 0 | 0 | 1000 |
| liquidation__bid_book__m1000__seed43__levels1000 | 1000 / 1000 | 1000 | 621 | 0 | 0 | 1000 |
| liquidation__bid_book__m1000__seed44__levels1000 | 1000 / 1000 | 1000 | 634 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed42__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed43__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| queue_concentration__buildup__m100000__seed44__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed42__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed43__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| queue_concentration__buildup__m10000__seed44__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed42__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed43__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| queue_concentration__buildup__m1000__seed44__levels4 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__buildup__m100000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__buildup__m100000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__buildup__m100000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__buildup__m10000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__buildup__m10000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__buildup__m10000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__buildup__m1000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__cancel_churn__m100000__seed42__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m100000__seed43__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m100000__seed44__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed42__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed43__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m10000__seed44__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed42__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed43__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__cancel_churn__m1000__seed44__levels1000 | 1000 / 1000 | 1 | 1 | 0 | 0 | 0 |
| stream__crowded__m100000__seed42__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m100000__seed43__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m100000__seed44__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m10000__seed42__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m10000__seed43__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m10000__seed44__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m1000__seed42__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m1000__seed43__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__crowded__m1000__seed44__levels1000 | 1000 / 1000 | 1000 | 8 | 0 | 0 | 1000 |
| stream__mixed__m1000000__seed43__levels1000 | 1000 / 1000 | 181 | 161 | 354 | 341 | 179 |
| stream__mixed__m100000__seed42__levels1000 | 1000 / 1000 | 140 | 126 | 374 | 359 | 138 |
| stream__mixed__m100000__seed43__levels1000 | 1000 / 1000 | 181 | 161 | 354 | 341 | 179 |
| stream__mixed__m100000__seed44__levels1000 | 1000 / 1000 | 162 | 152 | 390 | 381 | 162 |
| stream__mixed__m10000__seed42__levels1000 | 1000 / 1000 | 140 | 126 | 374 | 359 | 138 |
| stream__mixed__m10000__seed43__levels1000 | 1000 / 1000 | 181 | 161 | 354 | 341 | 179 |
| stream__mixed__m10000__seed44__levels1000 | 1000 / 1000 | 162 | 152 | 390 | 381 | 162 |
| stream__mixed__m1000__seed42__levels1000 | 1000 / 1000 | 140 | 126 | 374 | 359 | 138 |
| stream__mixed__m1000__seed43__levels1000 | 1000 / 1000 | 181 | 161 | 354 | 341 | 179 |
| stream__mixed__m1000__seed44__levels1000 | 1000 / 1000 | 162 | 152 | 390 | 381 | 162 |
| stream__sweep__m100000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__sweep__m100000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__sweep__m100000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__sweep__m10000__seed42__levels1000 | 1000 / 1000 | 1000 | 805 | 0 | 0 | 1000 |
| stream__sweep__m10000__seed43__levels1000 | 1000 / 1000 | 1000 | 801 | 0 | 0 | 1000 |
| stream__sweep__m10000__seed44__levels1000 | 1000 / 1000 | 1000 | 775 | 0 | 0 | 1000 |
| stream__sweep__m1000__seed42__levels1000 | 1000 / 1000 | 800 | 661 | 496 | 427 | 411 |
| stream__sweep__m1000__seed43__levels1000 | 1000 / 1000 | 800 | 666 | 510 | 442 | 389 |
| stream__sweep__m1000__seed44__levels1000 | 1000 / 1000 | 800 | 647 | 483 | 419 | 418 |

The baseline can rescan B active orders for validation and each maker fill; the revision usually performs indexed lookup and FIFO-level access but pays O(P) when inserting or deleting a sorted price key. The active-depth, price-level, and fill counts above explain why performance can vary by workload; no claim assumes the revision wins everywhere.

## Limitations

Stopped saved records: 582. Partial timing summaries: 16. Missing timing repeats: 0. Repeat coverage is shown in timing tables; declared stops and missing work are not extrapolated. Results are machine- and interpreter-specific synthetic measurements. Sequential processing excludes networking and queueing, so throughput does not establish live-venue overload capacity. The supplied data are teaching workloads rather than historical or calibrated market data. Passing tests and cross-version agreement do not constitute a formal proof.

## Reproducibility

Python: `3.14.7`; platform: `macOS-15.5-arm64-arm-64bit-Mach-O`; dirty tree: `False`.

Recorded measurement command:

```text
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3 tools/run_benchmarks.py --profile canonical --time-limit-seconds 5 --output results/raw_measurements.json.gz
```

Time-limit scope: engine replay, per-event latency, liquidation build/sale, bounded correctness attempts, and memory tracing; input parsing and derived application totals are not independently limited

Run `python3 -m unittest discover -s tests -v`, rebuild the dashboard from the saved result file with `python3 dashboard.py`, and consult `MEASUREMENT_PLAN.md` for exact data preparation, timing, latency, and memory boundaries.
