# Requirements and evidence map

PDF references use physical page numbers (the deck also has slide numbers).

| PDF pages | Requirement | Planned implementation / evidence |
| --- | --- | --- |
| 3, 12-13 | Tests and workloads before implementation; per-event conservation | tests/test_contract.py; results/evidence/tests_before.txt; unchanged test hash |
| 4-10 | Integer units, event contract, price/FIFO, cancellation, validation | orderbook/; tests; worked-example replay |
| 14 | Preserve baseline and justified revision; invariants and costs | baseline.py; revised.py; docs/REPORT.md |
| 16-18 | Five workloads; 1k/10k/100k; seeds 42/43/44; million attempt; queue and sale stresses | benchmark.py; raw results; environment; generator checksums |
| 19 | perf_counter; warmup; five raw repeats; fresh state; parsing/reset boundaries | benchmark.py; results/timing_raw.csv |
| 20 | Separate per-event latency; percentiles; beginning/end | results/latency_raw.csv; documented nearest-rank convention |
| 21 | Separate tracemalloc; growth/churn; output retained; no history leak | results/memory.csv; operation counters; report |
| 23 | Dashboard reads saved results; correctness; missing/stopped runs | dashboard.py; dashboard.html; results verification |
| 24 | Clean run path, report, dependencies, code version, no million-event upload | README.md; requirements.txt; provenance; final verification |
| 26 | Preserve supplied teaching data and generator | assignment/; data/; generate_orders.py |

Status and exact evidence counts will be filled from executed checks, not plans.
