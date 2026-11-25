# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

BaselineOrderBook retains its original list-based implementation. RevisedOrderBook
now stores resting orders in side-specific price dictionaries:
bids_by_price for BUY orders and asks_by_price for SELL orders. Each price maps to
a collections.deque, and orders_by_id indexes the same live order objects.

Both versions share routing, validation, integer matching arithmetic and result
construction. Revised overrides storage operations. It scans occupied prices
with max() or min(); price heaps and benchmarking are later stages.

Compare mode checks ordered results and canonical books after every event.
The existing 49 behavioral test cases retain their assertions and expected results.

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

## Revised, stage 2: FIFO queues by price

The previous stage added orders_by_id while retaining the Baseline list.
This stage replaces Revised's flat storage with two dictionaries of FIFO deques:

- bids_by_price[price_ticks]: BUY orders at that price.
- asks_by_price[price_ticks]: SELL orders at that price.
- orders_by_id[order_id]: the same active order object stored in exactly one deque.

The Baseline class is preserved. Revised inherits its validation and matching
rules and overrides the storage hooks called by those rules.

### Matching and index lifecycle

1. Storage initialization creates the three empty dictionaries.
2. A resting limit residual is appended to its side's deque at its integer price
   and added to orders_by_id. Accepted arrival sequences strictly increase, so
   appending preserves original arrival order, including for residual limits.
3. _best_order() chooses max(bids_by_price) for bids or min(asks_by_price) for asks,
   then returns that deque's first order. Dictionary insertion order and
   identifier spelling do not determine execution priority.
4. A partial maker remains at the queue head with its original arrival sequence.
   Its quantity changes on the shared object, immediately updating the index view.
5. An exhausted head is removed with popleft(). A cancellation removes the target
   from its actual deque. The index entry is deleted, and an empty price level is
   removed immediately.

Execution still occurs at the resting maker's price. Incoming limit residuals
rest at their own limit price; unfilled market sell quantities never enter a queue
or the ID index. Rejected events leave the queues, index and accepted sequence
unchanged. Unknown cancellations retain their valid not_found behavior.

Inspection still returns independent snapshots in canonical price-time order.
It iterates the live ID index, then applies the same sorting as Baseline.

### Integer representation

All submitted prices, quantities and arrival sequences remain strictly positive
built-in Python int values. Booleans, floats, zero and negative submitted numeric
values are rejected by the inherited validation.

- price_ticks represents USD cents per BTC: USD 60,000 is 6000000 ticks.
- qty_units represents units of 10^-8 BTC: one BTC is 100000000 units.
- seq is the strictly increasing original arrival sequence.

Queues and indexes store those integers unchanged. Matching uses only integer
comparisons, min() and subtraction; no float conversions or rescaling were added.

### Tiny FIFO and cancellation example

~~~python
from collections import deque
from order_book import RevisedOrderBook

book = RevisedOrderBook()
for seq, order_id in enumerate(("Z", "A"), start=1):
    book.process_event({
        "seq": seq, "event_id": f"add-{order_id}", "type": "LIMIT",
        "order_id": order_id, "side": "BUY",
        "price_ticks": 6_000_000, "qty_units": 100_000_000,
    })

queue = book.bids_by_price[6_000_000]
assert isinstance(queue, deque)
assert [order["order_id"] for order in queue] == ["Z", "A"]

sale = book.process_event({
    "seq": 3, "event_id": "sell-half", "type": "MARKET_SELL",
    "order_id": "S1", "qty_units": 50_000_000,
})
assert sale["fills"][0]["maker_id"] == "Z"
assert queue[0] is book.orders_by_id["Z"]
assert queue[0]["qty_units"] == 50_000_000
assert queue[0]["arrival_seq"] == 1

cancel = book.process_event({
    "seq": 4, "event_id": "cancel-A", "type": "CANCEL",
    "target_order_id": "A",
})
assert cancel["cancelled_qty_units"] == 100_000_000
assert [order["order_id"] for order in queue] == ["Z"]
assert set(book.orders_by_id) == {"Z"}

book.process_event({
    "seq": 5, "event_id": "fill-Z", "type": "MARKET_SELL",
    "order_id": "S2", "qty_units": 50_000_000,
})
assert book.orders_by_id == {}
assert book.bids_by_price == {}
assert book.asks_by_price == {}
~~~

Z trades before A because Z arrived first. Its partial fill retains that priority.
Cancelling A leaves Z in place. Completing Z removes the now-empty bid price level.

### Lookup, removal and cleanup costs

Let B be active orders, P occupied prices on the selected side, Q the length of
the target price queue, and F the number of maker fills.

| Operation | Cost in this stage |
| --- | --- |
| Find an active order by ID | Expected O(1) |
| Select the highest bid or lowest ask | O(P) price scan |
| Append to an existing price queue | Expected O(1), including index update |
| Remove a completed maker or cancel the queue head | Expected O(1) |
| Cancel an order elsewhere in its deque | O(Q) |
| Canonical book inspection | O(B log B) time and O(B) output |

Cancellation finds the target and its price queue directly through the index,
without scanning prices. Finding the order is expected O(1), but searching and
removing a non-head order from deque is O(Q). Total cancellation is therefore
expected O(1) at the head and O(Q) otherwise. It is not uniformly constant time.

Removal is eager: cancelled and fully filled orders leave both the queue and the
index immediately. Empty price levels are deleted immediately. There are no
inactive queue entries, tombstones or deferred cleanup costs in this stage.

Matching pays the O(P) best-price scan for each selected maker, plus queue updates
and O(F) fill-list construction: O((F + 1) * (P + 1)) is an upper bound. Live
storage uses O(B + P); queue and index entries reference the same order objects.
No price heaps or timing/memory benchmarks are part of this stage.

### Verification for this stage

The same existing 49 tests were run with Python 3.14.5 before and after this stage.

| Mode | Before FIFO queues | After FIFO queues |
| --- | --- | --- |
| Baseline | 49 passed | 49 passed |
| Revised | 49 passed | 49 passed |
| Compare | 49 passed | 49 passed |

All six runs completed with zero failures, errors or skips. The collected test
names were identical. The Baseline class source fingerprint was unchanged.
The existing test code, assertions and expected results were verified unchanged;
only the test module's storage-description docstring was updated.

Additional checks compared Baseline and Revised after each event and verified
that queue membership and orders_by_id contain the same shared live objects:

- 3,000 generated events across the five existing scenarios and three seeds.
- 27 directed events covering bid/ask FIFO, middle and head cancellations,
  partial-maker priority, full-fill cleanup, limit/market residuals and exact
  integers larger than 2^53.
- 36 rejected numeric inputs with unchanged queues, index and accepted sequence.
- 404 structural cleanup events checking immediate removal of empty price levels.
- The runnable FIFO/cancellation example above.

These are correctness checks; no timing or memory benchmarks were performed.

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
