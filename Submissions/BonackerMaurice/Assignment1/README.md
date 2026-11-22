# Assignment 1 — Limit order book (Maurice Bonacker)

Work in progress. Due 26 November 2026, 18:00.

## Replay your own event file

Run this from `Assignment1/`. The engine and `replay.py` use only the
standard library, so nothing needs to be installed.

```bash
python 03_code/replay.py my_events.jsonl --version b_sorted --results my_results.jsonl --print-book
```

| Option | Meaning |
|---|---|
| `my_events.jsonl` | Your file: `.jsonl` or `.jsonl.gz`, one JSON event per line. Several files can be given; `--results` takes exactly one. |
| `--version a` / `b_sorted` / `b_heap` | Which engine to use. All three give identical results. A is the slow list-scan baseline. |
| `--results OUT.jsonl` | Writes one JSON result per non-empty input line, in file order. |
| `--print-book` | Prints the final book after the summary line. |
| `--check` | Also checks the book's invariants after every event. Slow: use it on small files. |
| `--csv OUT.csv` | Writes one summary row per file. |

### Input: one event per line

```json
{"seq": 1, "event_id": "e1", "type": "LIMIT", "order_id": "b1", "side": "BUY", "price_ticks": 6500000, "qty_units": 100000000}
{"seq": 2, "event_id": "e2", "type": "MARKET_SELL", "order_id": "m1", "qty_units": 40000000}
{"seq": 3, "event_id": "e3", "type": "CANCEL", "target_order_id": "b1"}
```

Units:

- `price_ticks` is in cents (USD 0.01). 6500000 means USD 65,000.00 per BTC.
- `qty_units` is in 1e-8 BTC. 100000000 means 1 BTC.

### Output

**Console.** One summary line per file:

```
version=b_sorted  scenario=my_events  events=5  fills=1  rejected=1  not_found_cancels=0  peak_active_orders=  peak_price_levels=  final_book_size=1  invariants_ok=not checked  wall_seconds=0.000034
```

- `events` counts the non-empty lines, malformed ones included.
- The peaks and `invariants_ok` are only filled in with `--check`.

**`--results`.** One JSON object per non-empty input line, in file order. Its
shape depends on the event:

| Event | Result |
|---|---|
| LIMIT | `{"event_id", "order_id", "status": "filled" \| "resting", "unfilled_qty_units", "fills"}`. For `resting`, `unfilled_qty_units` is the quantity that rests. |
| MARKET_SELL | Same keys, with `"status": "filled" \| "partial" \| "unfilled"`. An unfilled rest is discarded and never rests. |
| CANCEL | `{"event_id", "target_order_id", "status": "cancelled" \| "not_found", "cancelled_qty_units"}` |
| any rejected event | `{"event_id", "status": "rejected", "reason"}` |
| malformed line | `{"event_id": null, "status": "rejected", "reason": "malformed JSON line <n>"}` |

Each fill is `{"maker_id", "taker_id", "price_ticks", "qty_units"}` and trades
at the resting (maker) order's price.

Example. The input file has six lines:

1. bid `b1`
2. an empty line
3. ask `a1`
4. a market sell `m1`
5. a line that is cut off
6. a cancel of `a1`

It gives these results:

```
{"event_id": "e1", "order_id": "b1", "status": "resting", "unfilled_qty_units": 100000000, "fills": []}
{"event_id": "e2", "order_id": "a1", "status": "resting", "unfilled_qty_units": 30000000, "fills": []}
{"event_id": "e3", "order_id": "m1", "status": "filled", "unfilled_qty_units": 0, "fills": [{"maker_id": "b1", "taker_id": "m1", "price_ticks": 6500000, "qty_units": 40000000}]}
{"event_id": null, "status": "rejected", "reason": "malformed JSON line 5"}
{"event_id": "e4", "target_order_id": "a1", "status": "cancelled", "cancelled_qty_units": 30000000}
```

**`--print-book`.** After the summary line it prints a header line, then one
JSON object per resting order:

```
final book: 1 resting orders (bids best first, then asks best first; FIFO within a price)
{"order_id": "b1", "side": "BUY", "price_ticks": 6500000, "qty_units": 60000000, "arrival_seq": 1}
```

- Bids come first, highest price first, then asks, lowest price first.
- Within one price, orders are in arrival order.
- To keep the book in a file, redirect the output, e.g.
  `... --print-book > final_book.txt`.

### Assumptions

- **Ids.** `order_id` and `target_order_id` must be JSON strings. A number
  such as `7` is rejected, and `"7"` and `7` are not the same id. `event_id`
  must be present and is echoed back unchanged.
- **File order is processing order.** Events are processed one at a time,
  exactly in file order, and are never sorted.
- **seq must increase.** `seq` must be a positive integer greater than the
  last accepted `seq`. An event with a non-increasing `seq` is rejected, not
  reordered. A rejected event does not use up its `seq`.
- **Malformed lines are rejected, and the replay continues.** A line that is
  not valid JSON gives the malformed-line result above. This includes invalid
  UTF-8 and nesting too deep to parse. `<n>` is the 1-based line number in the
  (decompressed) file, counting empty lines. The book is not touched.
  Empty or whitespace-only lines are skipped and give no result.
- **Other invalid events are rejected with a reason.** This covers valid JSON
  that is not a valid event: a non-object, a missing field, an unknown `type`,
  a `side` other than `BUY` / `SELL` (case-sensitive), or a wrong number type.
  The book and the last accepted `seq` stay unchanged.
- **Numbers.** `seq`, `price_ticks` and `qty_units` must be JSON integers
  greater than 0. `100.0`, `"100"` and `true` are rejected. There is no upper
  limit.
- **Extra fields** in an event are ignored.
- **Duplicate ids.** An `order_id` is a duplicate only while an order with
  that id is still resting. After it is filled or cancelled, the id can be
  used again.
- **Cancel targets.** Cancelling an id that is not resting (unknown, already
  filled or cancelled, or a market sell, which never rests) gives
  `not_found` with `cancelled_qty_units` 0.
- **Reason texts** are for people and may change. Only
  `malformed JSON line <n>` is a fixed format.
