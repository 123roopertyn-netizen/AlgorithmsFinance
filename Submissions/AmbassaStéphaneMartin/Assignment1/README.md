# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

BaselineOrderBook implements matching, validation, cancellation and inspection
using a list of individual resting orders. RevisedOrderBook now reuses those
rules and adds only an orders_by_id dictionary. Its matching and removal storage
is still the same list. FIFO queues and price heaps have not been introduced.

Both versions inherit the shared routing in OrderBook.process_event(). Compare
mode checks ordered results and canonical books after every event. The existing
49 behavioral test cases retain their assertions and expected results.

## Baseline design

The Baseline stores individual resting orders in a list. It scans for the best
opposite-side price and earliest arrival at that price for each maker fill.
Executions use integer quantities and the resting maker's price. A partial maker
retains its arrival sequence; an exhausted maker is removed. Incoming limit
residuals rest, while market sell residuals are returned without resting.

Validation completes before changing the book or accepted sequence. Unknown
cancellations are accepted with not_found; rejected events leave both unchanged.
Inspection returns independent dictionaries in canonical price-time order.

With B active orders at the start of an operation and F maker fills:

- Live-ID lookup and cancellation scan the list: O(B).
- A limit or market sell takes O((F + 1) * B), including scans and removals.
- Inspection sorts and copies the active orders: O(B log B) time and O(B) output.
- Live storage is O(B); the current event's returned fill list uses O(F) space.

These are algorithm bounds, not measured benchmark results.

## Revised, stage 1: orders_by_id

orders_by_id maps each active resting order ID to the same order dictionary held
in the existing list. It is an index into the live book, rather than a copy of
the order or a record of past submissions. For example, A bidding for 2 BTC at
$100 per BTC is represented as:

~~~python
orders_by_id = {
    "A": {
        "order_id": "A",
        "side": "BUY",
        "price_ticks": 10_000,
        "qty_units": 200_000_000,
        "arrival_seq": 1,
    }
}
~~~

The Revised implementation changes four small storage hooks:

1. Construction creates an empty orders_by_id dictionary.
2. _find_order() looks up an active ID in that dictionary.
3. _rest_order() first adds the residual order to the existing list, then indexes
   that exact object. A fully executed incoming limit never enters the index;
   incoming market orders and their unsold residuals never rest.
4. _remove_order() uses the existing list removal, then removes the ID from the
   dictionary after a full maker fill or successful cancellation.

A partial maker fill changes the shared order object's qty_units, so the list
and dictionary immediately show the same remaining quantity. Matching still scans
the list and chooses by price and original arrival sequence. No priority depends
on dictionary iteration order.

Validation still runs before matching or storage changes. Rejected events leave
the list, index and accepted sequence unchanged. An unknown cancellation is valid,
returns not_found, and leaves both storage views unchanged.

### Tiny cancellation example

~~~python
from order_book import RevisedOrderBook

book = RevisedOrderBook()
book.process_event({
    "seq": 1, "event_id": "add-A", "type": "LIMIT",
    "order_id": "A", "side": "BUY",
    "price_ticks": 10_000, "qty_units": 200_000_000,
})
book.process_event({
    "seq": 2, "event_id": "sell-1", "type": "MARKET_SELL",
    "order_id": "S", "qty_units": 100_000_000,
})
assert book.orders_by_id["A"]["qty_units"] == 100_000_000

result = book.process_event({
    "seq": 3, "event_id": "cancel-A", "type": "CANCEL",
    "target_order_id": "A",
})
assert result == {
    "event_id": "cancel-A", "target_order_id": "A",
    "status": "cancelled", "cancelled_qty_units": 100_000_000,
}
assert book.orders_by_id == {}
assert book.inspect_book() == {"bids": [], "asks": []}
~~~

A starts with 2 BTC. The sale consumes 1 BTC. Cancelling A removes only its
remaining 1 BTC from both the index and the list.

### Lookup versus removal cost

For B active orders, dictionary lookup and deletion take expected O(1) time.
However, the existing list removal still takes O(B): it scans for the order's
position and may shift the remaining list entries. Therefore cancellation as a
whole remains O(B). This stage speeds ID lookup and live-ID validation; it does
not make list removal or best-price selection constant time.

The index adds O(B) references. The resting order dictionaries are shared,
so their field data is not duplicated. Matching retains the Baseline's
O((F + 1) * B) bound for F maker fills; canonical inspection still sorts the
active orders. FIFO queues are reserved for a later stage.

### Verification for this stage

The same 49 existing test methods were run in each mode before and after adding
the index. Their assertions, code and expected results are unchanged; only the
test module's status description was updated.

| Mode | Before this stage | After this stage |
| --- | --- | --- |
| Baseline | 49 passed | 49 passed |
| Revised | 39 methods errored | 49 passed |
| Compare | 39 methods errored | 49 passed |

Before the change, Revised and Compare each produced 639 error records across
those 39 methods because generated cases include repeated subtests. Every error
was NotImplementedError from the unfinished Revised handlers. After the change,
all three modes completed with zero failures and zero errors.

Additional checks verified index membership and shared object identity after
1,500 generated events, unchanged state after six rejected events, full-fill
cleanup, incoming residual handling and the cancellation example above.
The Baseline class source hash was identical before and after this stage.

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
