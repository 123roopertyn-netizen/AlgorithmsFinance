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

## Tests (written before the implementation)

`python -m pytest -q tests` runs every test against **both** versions.

| File | What it checks | Expected values from |
|---|---|---|
| `test_worked_example.py` | the course example: fills b1:1, b2:1, b3:3, b4:1 BTC, 359,400 dollars, remaining book | course `worked_expected.json` |
| `test_matching.py` | empty book; one order; sells smaller than, equal to and larger than depth; several makers at one price; several price levels; partial fill then another sale; cancellation before/after partial and full fills; repeated and unknown cancels; crossing buys and sells at resting prices; residual limits; identifiers whose spelling differs from arrival order; a queue of 1,000 orders at one price | calculated by hand |
| `test_validation.py` | 25 kinds of invalid events (type, side, zero/negative/float/string/bool prices and quantities, missing fields, duplicate live identifiers, nonincreasing seq) leave the book and the last accepted seq unchanged | the rules in the assignment |
| `test_invariants.py` | after every event of 20 random streams: no crossed book, positive quantities, no order stored twice, canonical order; incoming quantity = fills + residual; each maker loses exactly its fills at its own price; cancels remove exactly the residual; fills follow price-time priority; market residuals never rest | checked from snapshots, independent of the implementation |
| `test_equivalence.py` | versions A and B give identical results and books after every event (30 random streams, the five supplied 10,000-event samples) | comparison between versions |

Before any implementation, both versions were empty stubs. The run is saved in
`evidence/step3_tests_before_implementation.txt`: 152 tests failed and 37 passed. The only
passes were the empty-book test for each version (an empty stub is a correct empty book) and
all 35 equivalence tests (30 random streams, 5 samples), because two empty stubs trivially
agree with each other. This is why agreement between
versions is only extra evidence and never replaces the hand-calculated expected results.
