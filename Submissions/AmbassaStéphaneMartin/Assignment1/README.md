# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

This project is at the test-first stage. The categorized tests, implementation
selector, comparison wrapper and external file dispatcher are present.
BaselineOrderBook and RevisedOrderBook are separate scaffolds: their matching,
cancellation, event validation and book inspection methods still raise
NotImplementedError. Behavioral tests are expected to fail until those methods
are implemented. Passing tests against test doubles only verifies the supporting
comparison and file-handling code.

## Common interface

Both versions expose:

- process_event(event): return the current event's result.
- inspect_book(): return {"bids": [...], "asks": [...]}.
- AddLimitOrder(event), FillMarketSell(event), CancelOrder(event): public handlers.

Each resting order contains order_id, side, price_ticks, qty_units and arrival_seq.
Bids sort by descending price, then arrival sequence. Asks sort by ascending price,
then arrival sequence. One BTC is 100,000,000 quantity units; one price tick is
$0.01 per BTC.

The validation tests require positive built-in integers for prices, quantities
and sequences, excluding booleans, floats and other numeric types. Sequences must
increase after accepted events. Missing required fields, invalid values and
duplicate live submission IDs are rejected without changing the book or consuming
the rejected sequence. event_id must be a nonblank string; results preserve the
supplied ID rather than deriving it from seq.

## Run tests

Use Python 3.11 or newer. The test runner uses only the standard library.
Open a terminal in this Assignment1 folder and select a version:

~~~console
python -B test_order_book.py --implementation baseline
python -B test_order_book.py --implementation revised
python -B test_order_book.py --implementation compare
~~~

The default is compare. It gives separate copies of each event to Baseline and
Revised and compares ordered results and full canonical books immediately after
each event, including rejected events. Numeric types must also agree: 1, 1.0 and
True are different. Rejection reason wording may differ, but each version must
return a nonempty reason.

Run one category:

~~~console
python -B test_order_book.py --implementation compare --category market-sells
~~~

Selectors: market-sells, price-time, limit-orders, cancellations, validation,
integration. Omitting --category runs all six categories.

Optional, if pytest is already installed:

~~~console
python -m pytest -q test_order_book.py
~~~

Pytest discovery uses comparison mode by default. The original independently
calculated market-sell expectations remain part of the suite.

## Replay event files

The external dispatcher exposes replay_file(path, book). It reads .jsonl or
.jsonl.gz files, calls the supplied book's process_event() in file order, and
returns the event results in that order. In comparison mode, both versions are
checked after every replayed event.

~~~console
python -B dispatcher.py data/worked_example.jsonl --implementation baseline
python -B dispatcher.py data/worked_example.jsonl --implementation revised
python -B dispatcher.py data/mixed_10000.jsonl.gz --implementation compare
~~~

The command prints the selected implementation, ordered results and final book.
Its saved result list is additional replay storage, separate from the live book.

Paths supplied to the command are relative to the terminal's working directory.
The test suite resolves reference fixtures relative to its own file. Missing
paths, directories and unsupported extensions are checked. Malformed JSON and
non-object records report the source path and line number. Blank lines are
ignored. A later file error does not undo earlier accepted events.

The two replay tests use temporary .jsonl and .jsonl.gz files containing LIMIT,
MARKET_SELL and CANCEL events with custom event_id values. Both must preserve
those IDs, return the independently expected results and finish with an empty book.

## Supplied materials

ASSIGNMENT.md, generate_orders.py and the data/ fixtures were provided with the
teacher's assignment. The reference six-BTC sale fills b1, b2, b3, then b4 for
1, 1, 3 and 1 BTC, respectively, yielding $359,400. The independent reference
assertions and generated-stream conservation checks remain in the tests.
