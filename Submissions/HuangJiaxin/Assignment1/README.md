# Assignment 1: Build and benchmark a limit order book

Huang Jiaxin, Algorithms in Finance, take-home exercise. Due 26 November 2026, 18:00.

A sequential, single-venue BTC limit order book in Python with price-time (FIFO) priority,
two implementation versions (a transparent baseline and a revision), tests written first,
time and memory benchmarks, and a dashboard built from saved results.

Work in progress. The project follows the five steps from Class 1, one commit each:
(1) set up the repository, (2) synthetic data, (3) tests first, (4) implementation and
revision, (5) measurements, dashboard and documentation.

## Data

All event data are synthetic teaching data from the course generator, not historical
exchange records, and not calibrated to any exchange.

* `data/supplied/`: the course package files, unchanged (five 10,000-event samples with
  seed 42, the worked example and its expected result, and the course `MANIFEST.json`).
* `generate_orders.py`: the course generator, unchanged (its SHA-256 matches the course
  manifest).
* `python make_data.py` generates every benchmark input **outside timing** into
  `data/generated/` (not committed) and records the exact command, settings and SHA-256 of
  each file in `data/generated_manifest.json`. `python make_data.py --million` adds the
  one-million-event streams.
  * Main grid: 5 scenarios × M ∈ {1,000; 10,000; 100,000} × seeds {42, 43, 44}, 1,000 price
    levels per side.
  * Queue concentration: `buildup` with 4 price levels per side, M ∈ {10,000; 100,000},
    seeds {42, 43, 44}, compared with the same streams at 1,000 levels.
* Check: the generator reproduces the five supplied samples byte for byte
  (`make_data.py` verifies the supplied checksums; the seed-42, 10,000-event files in the
  generated manifest have the same SHA-256 as the supplied ones).
* `lob/events_io.py` reads JSON Lines files, plain or gzip-compressed, either streamed
  (`iter_events`) or preloaded (`read_events`). Reading and parsing are timed separately
  from the matching engine.
