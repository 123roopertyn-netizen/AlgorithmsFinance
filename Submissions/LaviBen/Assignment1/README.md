# Assignment 1 - limit order book

- Student: Ben Lavi
- Submission path: `Submissions/LaviBen/Assignment1/`
- Branch: `lavi/assignment1-limit-order-book`
- Language target: Python 3.10+

## Current tests-first status

The interface and expected behavior are frozen in `CONTRACT.md`. The supplied
generator and fixtures are copied byte-for-byte and recorded in
`fixtures/CHECKSUMS.json`.

Tests were written before either order-book implementation. At this checkpoint,
`orderbook.baseline` and `orderbook.revised` intentionally do not exist. The
first full test run must therefore fail and its command/result must be recorded
before implementation begins.

Run from this directory:

```bash
python3 -m unittest discover -s tests -v
```

The intended final project will preserve both a transparent baseline and a
revised implementation. This checkpoint contains no matching-engine code,
benchmark runner, saved measurement, or dashboard.

## Frozen public API

Both `BaselineOrderBook` and `RevisedOrderBook` will expose:

- `ProcessEvent`
- `AddLimitOrder`
- `CancelOrder`
- `FillMarketSell`
- `InspectBook`
- read-only `last_accepted_seq`

All event and result field names, validation precedence, rejection reasons,
ordering rules, and invariants are defined in `CONTRACT.md` and exercised by
the same tests.

## Supplied teaching data

`tools/generate_orders.py`, the worked example, and the five compressed
10,000-event streams are unmodified teaching assets. They are synthetic and
not calibrated historical exchange data. Generated 100,000- and
1,000,000-event streams will remain untracked; later documentation will record
their exact commands and checksums.

The source package manifest also listed `.DS_Store`, but that file was absent
from the package and is intentionally not recreated or submitted.
