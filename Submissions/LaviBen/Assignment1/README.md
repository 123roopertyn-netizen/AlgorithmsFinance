# Assignment 1 - limit order book

- Student: Ben Lavi
- Submission path: `Submissions/LaviBen/Assignment1/`
- Branch: `lavi/assignment1-limit-order-book`
- Language target: Python 3.10+

## Current implementation status

The interface and expected behavior are frozen in `CONTRACT.md`. The supplied
generator and fixtures are copied byte-for-byte and recorded in
`fixtures/CHECKSUMS.json`.

Tests were written and run before either implementation; the original failing
run remains recorded in `TESTS_FIRST_BASELINE.md`. Both preserved versions now
exist:

- `BaselineOrderBook` transparently scans a list of individual active orders.
- `RevisedOrderBook` uses indexed FIFO price levels, an active-order index and
  sorted price keys with eager cleanup.

The shared contract suite, the added regression cases and all fixture checks
currently pass. Both versions also produced identical ordered results on every
event in all five supplied 10,000-event streams. This agreement supplements
the independently calculated examples and invariants; it is not a proof.

Run from this directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Expected result at this checkpoint: `Ran 37 tests` followed by `OK`. The 23
algorithm/fixture tests include a full 50,000-event supplied-stream replay;
ten tests cover the separate
measurement framework and its stopped-run behavior, two cover the dashboard,
and two cover the generated short report.

Replay the worked example with either version:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/replay.py \
  fixtures/worked_example.jsonl --version baseline --trace
PYTHONDONTWRITEBYTECODE=1 python3 tools/replay.py \
  fixtures/worked_example.jsonl --version revised --trace
```

Both traces fill makers `b1`, `b2`, `b3`, then `b4`, leave four BTC on `b4`,
leave the two-BTC ask unchanged and imply gross proceeds of `359400.00` USD.

The canonical benchmark was run from clean measurement commit
`ffb474170b4849af850e31588f9a1a70dcf08da3`. It covers 72 required datasets
plus one one-million-event mixed attempt and saves 3,744 records. All 76
completed correctness comparisons agree; 15 large liquidation correctness
attempts and other slow baseline phases are explicitly stopped at the equal
five-second limit. See `MEASUREMENT_PLAN.md`, `REPORT.md`, and
`results/CHECKSUMS.json`. `dashboard.py` and `build_report.py` load saved
results only; they never rerun benchmarks.

Rebuild both derived artifacts exactly with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 dashboard.py \
  --results results/raw_measurements.json.gz \
  --output results/dashboard.html
PYTHONDONTWRITEBYTECODE=1 python3 build_report.py \
  --results results/raw_measurements.json.gz \
  --output REPORT.md
```

Open `results/dashboard.html` in a browser. The dashboard is dependency-free,
works offline, exposes raw repeats/settings/environment, and changes filters
without running measurement code.

## Frozen public API

Both `BaselineOrderBook` and `RevisedOrderBook` expose:

- `ProcessEvent`
- `AddLimitOrder`
- `CancelOrder`
- `FillMarketSell`
- `InspectBook`
- read-only `last_accepted_seq`

All event and result field names, validation precedence, rejection reasons,
ordering rules, and invariants are defined in `CONTRACT.md` and exercised by
the same tests.

## Implement and revise evidence

`IMPLEMENTATION_NOTES.md` records pseudocode, invariants, runtime and space
reasoning, the meaningful data-structure revision, the discovered validation
regression and AI-use decisions. The unchanged 20-test suite passed before the
two algorithm regression cases were added; the algorithm suite then reached
22 tests. Measurement, dashboard, and report tests were subsequently written
test-first.

## Supplied teaching data

`tools/generate_orders.py`, the worked example, and the five compressed
10,000-event streams are unmodified teaching assets. They are synthetic and
not calibrated historical exchange data. Generated 100,000- and
1,000,000-event streams remain untracked. Their exact commands are in
`MEASUREMENT_PLAN.md`; the canonical raw report records every dataset setting
and checksum, including one-million-event SHA-256
`ce4213a66317d9565327e231f8cc84aa5f04e01253ba225feff4f9be7db08120`.

The source package manifest also listed `.DS_Store`, but that file was absent
from the package and is intentionally not recreated or submitted.
