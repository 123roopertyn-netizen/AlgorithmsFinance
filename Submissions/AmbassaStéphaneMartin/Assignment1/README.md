# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

BaselineOrderBook retains its original list-based implementation. RevisedOrderBook
uses an order-ID index, FIFO deques by side and price, and standard-library heapq
price indexes. Ask heap keys are positive prices; bid heap keys are negated prices.
Original prices in orders, fills and canonical snapshots remain positive integers.

Both versions share routing, validation, integer matching arithmetic and result
construction. Revised overrides storage and best-price selection. Per-order
cancellation still removes orders immediately from their deques and orders_by_id.

Compare mode checks ordered results and canonical books after every event.
The original 49 behavioral tests and expected results are preserved. Focused
heap regressions are in test_price_heaps.py. This stage adds no benchmarks.

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

## Revised, stage 3: price heaps

The previous stage used max() and min() over occupied price levels. Revised now
selects prices with heapq while preserving the existing FIFO deques and matching
rules. Baseline and the shared validation and matching code are unchanged.

### Live levels versus retained heap entries

- bids_by_price and asks_by_price contain only active, nonempty price queues.
  Their keys are original positive price_ticks.
- orders_by_id contains exactly the active resting orders and shares each order
  object with its deque. Partial fills update that shared object's quantity.
- bid_price_heap is a min-heap of negated integer bid prices.
- ask_price_heap is a min-heap of original positive integer ask prices.
- _bid_heap_keys and _ask_heap_keys record every retained heap key, including
  inactive keys. Each price has at most one retained key per side.

The live price dictionaries are authoritative. A heap stores only prices, never
orders or arrival sequences. Its retained entries can therefore outnumber active
price levels without retaining cancelled orders.

### Price lifecycle and recreation

1. Appending to an active level changes only its deque and orders_by_id.
2. Creating a level pushes its signed price key only if that key is not already
   retained. The resting order joins the tail using its original arrival sequence.
3. A partial maker stays at the head. A full fill or cancellation immediately
   removes the order from its deque and the ID index. An empty live level is
   deleted immediately; its heap key may temporarily remain.
4. _best_order() inspects the heap root. If its decoded price is inactive, it pops
   the key and removes it from the retained-key set, continuing until a live price
   is found. The live deque's head is the next maker.
5. If a deleted price becomes active again before its key was removed, the new
   queue reuses that retained key. If root cleanup or rebuilding already removed
   it, creation pushes a fresh key. There are no duplicate heap keys and no heap
   references to the old queue or cancelled makers.

FIFO at a price, partial-maker priority and execution at the resting maker's
price are unchanged. Incoming limit residuals rest at their limit price; market
sell residuals do not enter the book. Validation completes before any heap or
queue mutation, so rejected events leave all indexes and the accepted seq intact.

### Bounded cleanup policy

For each side independently, let P be the number of active price levels and H
the number of retained heap entries.

- When P is zero, the heap and retained-key set are cleared immediately.
- When H > 2 * P + 32, the heap is rebuilt from the current live price keys using
  heapq.heapify(), and its retained-key set is rebuilt to match.
- Otherwise stale keys remain until root cleanup or a later rebuild.

The bound H <= 2 * P + 32 holds after every public event, with H = 0 when P = 0.
The constant 32 is _HEAP_REBUILD_SLACK. Membership sets prevent repeated recreation
of one retained price from adding duplicate keys. The threshold also bounds growth
from churn over many distinct inactive prices hidden behind a better live price.

Only price-key cleanup is lazy. Per-order cancellation remains eager:
popleft() for a head order, deque.remove() for an order elsewhere in its queue,
immediate deletion from orders_by_id, and deletion of empty live price levels.

### Integer representation

Number representation and matching arithmetic are unchanged:

- price_ticks is a strictly positive built-in Python int in USD cents per BTC.
  USD 60,000 is 6000000 ticks.
- qty_units is a strictly positive built-in Python int in units of 10^-8 BTC.
  One BTC is 100000000 units.
- seq is a strictly increasing positive built-in Python int.

Floats, booleans and nonpositive submitted numeric values remain rejected.
Negation is confined to bid heap keys. Orders, fills, queues and snapshots retain
their original positive prices, including integers larger than 2^53.

### Tiny price recreation example

~~~python
from order_book import RevisedOrderBook

book = RevisedOrderBook()
for seq, order_id, price in ((1, "better", 6_100_000), (2, "old", 6_000_000)):
    book.process_event({
        "seq": seq, "event_id": f"add-{order_id}", "type": "LIMIT",
        "order_id": order_id, "side": "BUY",
        "price_ticks": price, "qty_units": 100_000_000,
    })

book.process_event({
    "seq": 3, "event_id": "cancel-old", "type": "CANCEL",
    "target_order_id": "old",
})
assert 6_000_000 not in book.bids_by_price
assert -6_000_000 in book.bid_price_heap

book.process_event({
    "seq": 4, "event_id": "recreate-price", "type": "LIMIT",
    "order_id": "new", "side": "BUY",
    "price_ticks": 6_000_000, "qty_units": 100_000_000,
})
assert book.bid_price_heap.count(-6_000_000) == 1

result = book.process_event({
    "seq": 5, "event_id": "sell-two", "type": "MARKET_SELL",
    "order_id": "S", "qty_units": 200_000_000,
})
assert [fill["maker_id"] for fill in result["fills"]] == ["better", "new"]
assert [fill["price_ticks"] for fill in result["fills"]] == [6_100_000, 6_000_000]
assert book.orders_by_id == {}
assert book.bids_by_price == {}
assert book.bid_price_heap == []
~~~

The recreated level uses the new order's queue. The retained price key neither
restores the cancelled maker nor changes the order of prices or FIFO arrivals.

### Costs and remaining limitations

Let B be active orders, P active price levels on one side, H retained heap entries,
Q the target deque's length, and S the stale roots discarded by one selection.

| Operation | Cost excluding a threshold rebuild |
| --- | --- |
| Find an active order by ID | Expected O(1) |
| Read the best price when the root is live | Expected O(1) |
| Discard S stale roots while finding the best price | O(S log(H + 1)) |
| Create a price with a new heap key | O(log(H + 1)) |
| Recreate a price whose key is still retained | Expected O(1) |
| Append to an active price queue | Expected O(1) |
| Remove a completed maker or cancel the queue head | Expected O(1) |
| Cancel an order elsewhere in its deque | O(Q) |
| Canonical book inspection | O(B log B) time and O(B) output |

Price dictionaries and retained-key sets use expected O(1) hash operations.
H is not the same as P: inactive price keys can remain in a heap.

A threshold rebuild costs O(H + P): constructing and heapifying the live keys
costs O(P), while discarding old heap/set entries can cost O(H). Clearing an empty
side costs O(H). Rebuilding is amortized across accumulated stale keys, but an
individual operation can still pay that linear cleanup cost. Root pops likewise
cost O(log(H + 1)) each; their cost is not a free constant-time lookup.

Thus total cancellation is not uniformly O(1). Its order lookup is expected O(1);
its deque removal is O(1) at the head or O(Q) elsewhere. If the level disappears
and triggers rebuilding or clearing, that cancellation also pays O(H + P) cleanup.
A conservative worst-case bound is O(Q + H + P), with Q replaced by 1 at the head.

Matching still builds F fill records and can trigger stale-root pops and rebuilds.
A single event has no universal O(log P) bound. Live storage is O(B + P + H);
the cleanup bound reduces retained price-index storage to O(P + 1) per side.
FIFO queues and orders_by_id remain synchronized without inactive order entries.

Arbitrary-order cancellation optimization and measured performance comparisons
remain later stages. No timing or memory benchmark results are claimed here.

### Verification for this stage

The starting revision was 2d7a68b with a clean working tree. Python 3.14.5 ran the
same original 49 tests before and after adding heaps, explicitly selecting each
implementation mode.

| Mode | Before price heaps | After price heaps |
| --- | --- | --- |
| Baseline | 49 passed | 49 passed |
| Revised | 49 passed | 49 passed |
| Compare | 49 passed | 49 passed |

All six runs had zero failures, errors or skips. The Baseline class source hash
was unchanged, and the complete original test_order_book.py file was byte-for-byte
unchanged, including every assertion and expected result.

All 10 additional regressions in test_price_heaps.py passed. They cover cancelled
best prices, bid/ask ordering, positive original prices and large exact integers,
recreation before and after stale-root cleanup, recreation after rebuilding,
same-price and distinct-price cancellation churn, preservation of every live
price during rebuilding, empty-book cleanup, rejected-event immutability,
partial-maker priority and immediate per-order cancellation.

The regressions check heap order, unique retained keys, the H <= 2 * P + 32 bound,
queue/index membership and shared order identity after each event, comparing
public results and snapshots against Baseline.

Additional correctness checks applied those same invariants after 3,000 generated
events across the five existing scenarios and seeds 42, 43 and 44. The runnable
README price-recreation example also passed. No benchmark measurements were made.

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

Run the focused heap regression tests separately:

~~~console
python -B -m unittest -v test_price_heaps
~~~

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
