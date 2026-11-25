# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

BaselineOrderBook retains its original list-based implementation. RevisedOrderBook
uses an active-order ID index, FIFO deques by price, bounded price heaps and lazy
cancellation of non-head queue entries.

A successful cancellation removes its ID immediately and returns the remaining
quantity. Inactive queue entries cannot match or appear in canonical snapshots.
Per-price live-order counts drive bounded cleanup, including behind a live head.

Both versions share routing, validation, integer arithmetic and matching rules.
The original 49 behavioral tests remain unchanged. Heap regressions distinguish
live orders from inactive entries; lazy-cancellation regressions cover the new
storage and cleanup behavior. Benchmarks remain a separate stage.

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

## Revised, stage 4: lazy order cancellation

The previous stage removed arbitrary orders with deque.remove(), an O(Q) search.
Revised now removes the live ID immediately without searching for its deque
position. A cancelled non-head object may stay in its queue until head pruning,
compaction or deletion of an inactive price level.

### Live orders and retained objects

orders_by_id is authoritative. A queued object is active only when:

~~~text
book.orders_by_id.get(order["order_id"]) is order
~~~

The identity check matters if an identifier is reused after its earlier order
has left the live index: an older retained object with the same ID remains
inactive. No active flag or additional fields are added to public order snapshots.

bids_by_price and asks_by_price contain only price levels with at least one live
order, but their deques can also contain inactive entries. _bid_live_counts and
_ask_live_counts hold active order counts at each price, not BTC quantities.

Canonical inspection iterates only the live ID index, so inactive objects never
appear in snapshots. Their old remaining quantities do not represent live depth.

### Cancellation, matching and FIFO

1. Validation completes before any mutation. The accepted sequence and every
   internal index remain unchanged when an event is rejected.
2. Cancellation finds the order through orders_by_id. Removing that ID and
   decrementing its price's live count are expected O(1) operations. The result
   returns the target's remaining quantity, including after partial fills.
3. If the removed object is at the deque head, popleft() removes it directly.
   Otherwise it remains as an inactive entry: no search or deque.remove() occurs.
4. Best-maker selection discards inactive head entries before returning a live
   maker. A partial maker keeps its object, price and original arrival sequence.
   A fully filled maker is removed from the live index and queue head.
5. Compaction filters inactive objects without reordering or copying the live
   order objects. Active FIFO is therefore preserved through cleanup.

Unknown, already cancelled and fully filled orders return not_found with zero
cancelled quantity. Incoming limit residuals still rest at the limit; market
sell residuals never enter the book. Trades still use the resting maker's price.

### Bounded queue cleanup

For one price, let L be its live-order count and R its retained deque length.

- If L becomes zero, clear the deque and delete the price from its live price
  dictionary and live-count dictionary immediately.
- Otherwise, when R > 2 * L + 32, retain only active objects using a stable filter.
- Before returning a maker, discard inactive objects at the deque head.

After each public event, every retained queue has L > 0 and R <= 2 * L + 32.
A single old active head therefore cannot hide unbounded cancellation garbage:
with one live head, its deque holds at most 34 entries. The live counts allow
this threshold check without scanning the queue on every cancellation.

The stable filter uses a temporary list of the L active objects, then clears and
extends the same deque. Cleanup preserves the original order objects and active
arrival order. Each removed inactive entry is released by one cleanup path.

Across the book, retained queue entries are bounded by 2 * B + 32 * P, where B
is active orders and P is active price levels across both sides. This bounds
storage by current live state rather than the historical number of cancellations.

### Price heaps and recreated levels

The previous price-heap policy is retained. Ask heaps contain positive prices;
bid heaps contain negated price keys. Live price dictionaries are authoritative,
and retained-key sets prevent duplicate heap keys on price recreation.

Per side, with P active price levels and H retained heap entries, rebuild when
H > 2 * P + 32, and clear the heap and retained-key set when P becomes zero.
Deleting a price because its live count reaches zero can trigger this maintenance.

A recreated price receives a new empty deque and live count, reusing a retained
heap key if present. No inactive order or old FIFO position is revived. Inactive
price keys are removed when they reach the heap root or during rebuilding.

### Integer representation

The number representation and shared matching arithmetic are unchanged:

- price_ticks is a positive built-in Python int in USD cents per BTC.
  USD 60,000 is 6000000 ticks.
- qty_units is a positive built-in Python int in units of 10^-8 BTC.
  One BTC is 100000000 units.
- seq is a strictly increasing positive built-in Python int.

Floats, booleans and nonpositive submitted numeric values remain rejected.
No matching arithmetic converts through floats. Active quantities stay positive;
an unfilled result may correctly report zero residual after a complete execution.

### Tiny lazy-cancellation example

~~~python
from order_book import RevisedOrderBook

book = RevisedOrderBook()
for seq, order_id, quantity in (
    (1, "Z", 200_000_000), (2, "M", 100_000_000), (3, "A", 100_000_000)
):
    book.process_event({
        "seq": seq, "event_id": f"add-{order_id}", "type": "LIMIT",
        "order_id": order_id, "side": "BUY",
        "price_ticks": 6_000_000, "qty_units": quantity,
    })

cancel = book.process_event({
    "seq": 4, "event_id": "cancel-M", "type": "CANCEL",
    "target_order_id": "M",
})
assert cancel["cancelled_qty_units"] == 100_000_000
assert "M" not in book.orders_by_id
assert [order["order_id"] for order in book.bids_by_price[6_000_000]] == ["Z", "M", "A"]
assert [order["order_id"] for order in book.inspect_book()["bids"]] == ["Z", "A"]

first = book.process_event({
    "seq": 5, "event_id": "partial-Z", "type": "MARKET_SELL",
    "order_id": "S1", "qty_units": 100_000_000,
})
assert first["fills"][0]["maker_id"] == "Z"
second = book.process_event({
    "seq": 6, "event_id": "finish-book", "type": "MARKET_SELL",
    "order_id": "S2", "qty_units": 200_000_000,
})
assert [fill["maker_id"] for fill in second["fills"]] == ["Z", "A"]
assert book.orders_by_id == {}
assert book.bids_by_price == {}
assert book.bid_price_heap == []
~~~

M remains physically queued below the cleanup threshold but is absent from live
depth. It never executes. Z retains priority after its partial fill, and A follows.

### Expected, amortized and worst-case costs

Let R be the target deque's retained length, L its live count, P active price
levels on the relevant side, H retained heap entries, and B total live orders.
The following expected costs use expected O(1) dictionary/set operations.

| Work | Cost |
| --- | --- |
| Find an active order and remove its ID | Expected O(1) |
| Decrement its price's live count | Expected O(1) |
| Remove the exact deque head, if applicable | O(1) |
| Skip T inactive queue heads during maker selection | Expected O(T) |
| Compact one price queue | Expected O(R), with O(L) temporary references |
| Clear an inactive-only price queue | O(R) reference cleanup |
| Discard S stale heap roots | O(S log(H + 1)) |
| Rebuild a price heap and its retained-key set | O(H + P) |
| Canonical snapshot | O(B log B) time and O(B) output |

Logical cancellation is expected O(1), without a deque-position search. The
complete cancellation operation can additionally compact a queue, clear an
inactive level, or rebuild a heap. An individual cancellation can therefore cost
O(R + H + P) under the expected hash-operation model. Guaranteed O(1) cancellation
latency is not claimed.

Queue compaction is amortized over accumulated inactive entries: it runs only
after inactive entries outnumber live entries plus the slack. Stable filtering
and head pruning remove each inactive object once; their aggregate queue-cleanup
work can be charged across the order lifecycle. The occasional linear scan is
still visible in a particular cancellation or fill. Heap rebuilding is likewise
amortized across stale price keys, while each stale-root pop costs logarithmic work.

The live-count, queue and heap bounds keep engine storage O(B + P + H), hence
O(B + P + 1) with the per-side heap bounds. Cancelling behind an old live head does
not retain storage proportional to event history. Snapshots and comparison-mode
copies are additional returned/verification storage.

Worst-case cleanup pauses, heap maintenance and snapshot sorting remain
limitations. This stage contains no timing or memory benchmark claims.

### Verification for this stage

The starting revision was 1a9f776 with a clean working tree. Python 3.14.5 ran the
same original 49 tests before and after the change.

| Original suite mode | Before lazy cancellation | After lazy cancellation |
| --- | --- | --- |
| Baseline | 49 passed | 49 passed |
| Revised | 49 passed | 49 passed |
| Compare | 49 passed | 49 passed |

All six runs had zero failures, errors or skips. The Baseline class source hash
was unchanged, and the entire original test_order_book.py file was byte-for-byte
unchanged, including all assertions and expected results.

Ten new lazy-cancellation regressions were added and run before implementation.
Against the previous eager code, four methods produced eight side-specific
assertion failures: the no-scan probe detected deque.remove(), and the retention
checks confirmed the old implementation still removed entries eagerly. There
were no test errors in that expected red phase. After implementation, all 10 pass.

All 10 existing heap regressions passed before and after. Their internal queue
checks now distinguish live objects from inactive retained entries and verify
per-price live counts and queue bounds. Raw-state rejection checks include those
counts. Active FIFO views filter by object identity. Public expected results and
all other heap test method assertions were audited unchanged.

Every focused-test event uses ComparedOrderBook, comparing ordered results and
canonical snapshots against Baseline. Coverage includes cancelled makers never
executing, partial-maker FIFO through compaction, partial cancellation quantities,
not_found results, price recreation, identifier reuse without ghost execution,
large exact integers, rejected-event atomicity and bounded churn behind old heads.

Additional checks verified the same live-queue, heap, ID-index and count
invariants after 3,000 generated events across all five scenarios and seeds
42, 43 and 44. The runnable lazy-cancellation example above also passed.
These are correctness checks, not timing or memory benchmarks.

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

Run the lazy-cancellation regressions:

~~~console
python -B -m unittest -v test_lazy_cancellation
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
