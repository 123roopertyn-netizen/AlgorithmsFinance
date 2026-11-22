# REVISIONS.md: algorithm changes (Assignment 1)

Every change to the engine: what changed, why, and the evidence.
Version A (`03_code/lob_a.py`) stays unchanged and is kept for comparison.

Notation used for costs:

| Symbol | Meaning |
|---|---|
| B | active (live) orders in the book |
| P | occupied price levels on the side being touched (P ≤ B) |
| F | fills produced by the current event |
| L | price levels emptied by the current event (L ≤ F) |
| D | dead (cancelled) queue entries skipped by the current event |
| H | entries in one side's heap, live plus stale (B-heap only) |
| M | events in a stream (totals only; per-event costs do not depend on M) |

---

## Revision 1: Version A → Version B (two variants)

**Status: design approved by Maurice on 22 Nov 2026 with four decisions
(below). Implementation follows this design.**

Maurice's decisions on the first draft:

1. Compaction accepted: rebuild a side's heap when its entries exceed
   2 × live levels + 16; rebuild a level's deque when more than half its
   entries are cancelled. Tested under cancel_churn (heap) and by repeated
   cancels behind a live FIFO head (deque).
2. Shared core accepted: `lob_b_common.py` holds matching and
   cancellation; `validation.py` stays shared with Version A. The variants
   differ only in the price index.
3. Ask removal fixed: B-sorted stores BOTH sides so the best price is at
   the END of its list, and removes an exhausted best level with `pop()`.
4. Cost wording corrected: linear heap rebuilds are distinguished from
   O(log H) stale pops; submission costs include residual-limit insertion;
   compaction bounds retained entries, not Python dict allocations.

### Why: evidence from Version A

The cProfile run of Version A (`05_results/profile_version_a.txt`, one replay
per supplied 10,000-event file) shows two full-list scans doing almost all
the work:

| Scenario | total (s, cProfile) | `_best_index` (best-price scan) | `_is_live` (duplicate-id scan) |
|---|---|---|---|
| buildup | 7.04 | 74.4% | 24.1% |
| crowded | 5.33 | 71.7% | 26.7% |
| sweep | 6.83 | 77.2% | 21.3% |
| mixed | 0.78 | 58.3% | 27.1% |
| cancel_churn | 0.04 | 2.4% | 2.4% |

- Both scans are O(B) per call. `_best_index` runs F + 1 times per incoming
  order, `_is_live` once per submission. Version A therefore costs about
  B · (F + 2) per event.
- Cost depends on B, not on P: crowded (8 levels) and buildup (1,977 levels)
  take the same time (`05_results/replay_summary.csv`).
- Scaling (`05_results/scaling_version_a.csv`): log-log slope about 2 for
  buildup, crowded, sweep and mixed between 10k and 30k events, because their
  book grows with M. cancel_churn (B ≤ 1) is linear. Four of five 100k runs
  were stopped at the 600 s limit.

### What stays the same

- `validation.py` is shared unchanged; the duplicate-live check is passed in
  as `is_live = self.orders.__contains__`.
- Same interface and outputs: `AddLimitOrder`, `CancelOrder`,
  `FillMarketSell`, `process_event`, `inspect_book`, `assert_invariants`,
  attribute `last_seq`; identical result dicts and canonical book.
- All existing tests run unchanged against both variants.

### Data organisation (both variants)

```
orders      : dict  order_id -> Order          # live orders only
levels[side]: dict  price    -> Level          # occupied levels only
Order       : order_id, side, price_ticks, qty_units, arrival_seq
              qty_units == 0 means "dead" (cancelled, still sitting in a queue)
Level       : queue      deque of Order, arrival order (FIFO)
              live_count number of live orders in queue
              live_qty   sum of their qty_units (aggregate depth)
```

Price-time priority comes from the structure: the best level comes from the
price index (below), and inside a level the deque front is the earliest
arrival. A new order is appended at the back; a partially filled maker stays
at the front, so it keeps its priority. No seq comparisons are needed.

The two variants differ ONLY in the price index, the structure that answers
"what is the best occupied price on this side?". Each uses a signed key per
side so that one rule serves bids and asks.

| | B-sorted (`lob_b_sorted.py`) | B-heap (`lob_b_heap.py`) |
|---|---|---|
| Key | bids `p`, asks `-p` (best = LARGEST key) | bids `-p`, asks `p` (best = SMALLEST key) |
| Index per side | ascending list of keys; best at the END | `heapq` list; best at `heap[0]` |
| Best price | `keys[-1]`, O(1) | `heap[0]` after dropping stale tops |
| Level created | `bisect.insort(keys, key)` | `heappush(heap, key)` |
| Best level exhausted by matching | `keys.pop()` | nothing now (lazy) + compaction check |
| Any level emptied by a cancel | `del keys[bisect_left(keys, key)]` | nothing now (lazy) + compaction check |

### Pseudocode

Shared core in `lob_b_common.py` (identical for both variants; `INDEX_*` are
the variant parts):

```
MATCH(taker_id, taker_side, qty, limit):          # limit None = market order
    maker_side = opposite(taker_side)
    fills = []; remaining = qty
    while remaining > 0:
        p = INDEX_BEST(maker_side)
        if p is None: break                                     # side empty
        if limit is not None and not crosses(taker_side, limit, p): break
        level = levels[maker_side][p]
        while remaining > 0 and level.live_count > 0:
            maker = level.queue[0]
            if maker.qty == 0:                                  # dead entry
                level.queue.popleft(); continue
            t = min(remaining, maker.qty)
            fills.append(fill(maker.order_id, taker_id, p, t))  # resting price
            maker.qty -= t; level.live_qty -= t; remaining -= t
            if maker.qty == 0:                                  # maker exhausted
                level.queue.popleft(); del orders[maker.order_id]
                level.live_count -= 1
        TIDY(maker_side, p, level, best=True)
    return fills, remaining

TIDY(side, p, level, best):
    if level.live_count == 0:                       # level empty: remove it
        del levels[side][p]                         # drops its dead entries too
        if best: INDEX_REMOVE_BEST(side, p)         # matching empties the best level
        else:    INDEX_REMOVE(side, p)              # a cancel can empty any level
    elif len(level.queue) > 2 * level.live_count:   # more than half cancelled
        level.queue = deque(o for o in level.queue if o.qty > 0)   # compaction
```

```
AddLimitOrder(event_id, order_id, side, price, qty, seq):
    fills, remaining = MATCH(order_id, side, qty, limit=price)
    if remaining > 0:                               # residual-limit insertion
        order = Order(order_id, side, price, remaining, seq)
        orders[order_id] = order
        level = levels[side].get(price)
        if level is None:
            level = Level(); levels[side][price] = level
            INDEX_ADD(side, price)
        level.queue.append(order)
        level.live_count += 1; level.live_qty += remaining
    status = "resting" if remaining > 0 else "filled"
    return {event_id, order_id, status, unfilled_qty_units: remaining, fills}

CancelOrder(event_id, target_order_id):
    order = orders.pop(target_order_id, None)
    if order is None:
        return {event_id, target_order_id, "not_found", cancelled_qty_units: 0}
    level = levels[order.side][order.price]
    q = order.qty
    order.qty = 0                         # mark dead; stays in the deque (lazy)
    level.live_count -= 1; level.live_qty -= q
    TIDY(order.side, order.price, level, best=False)
    return {event_id, target_order_id, "cancelled", cancelled_qty_units: q}

FillMarketSell(event_id, order_id, qty):
    fills, remaining = MATCH(order_id, "SELL", qty, limit=None)   # never rests
    status = "filled" if remaining == 0 else ("partial" if fills else "unfilled")
    return {event_id, order_id, status, unfilled_qty_units: remaining, fills}
```

Price index, B-sorted (`skey(BUY, p) = p`, `skey(SELL, p) = -p`):

```
INDEX_BEST(side)            = price_of(keys[side][-1]) if keys[side] else None
INDEX_ADD(side, p)          : bisect.insort(keys[side], skey(side, p))
INDEX_REMOVE_BEST(side, p)  : keys[side].pop()                     # last element
INDEX_REMOVE(side, p)       : del keys[side][bisect_left(keys[side], skey(side, p))]
```

Price index, B-heap (`hkey(BUY, p) = -p`, `hkey(SELL, p) = p`; lazy
deletion plus compaction):

```
INDEX_BEST(side):
    heap = heaps[side]
    while heap and price_of(heap[0]) not in levels[side]:   # stale top
        heappop(heap)                                       # O(log H) each
    return price_of(heap[0]) if heap else None
INDEX_ADD(side, p):    heappush(heaps[side], hkey(side, p))
INDEX_REMOVE(side, p) = INDEX_REMOVE_BEST(side, p):         # nothing removed now
    if len(heaps[side]) > 2 * len(levels[side]) + 16:       # compaction
        heaps[side] = [hkey(side, q) for q in levels[side]]
        heapify(heaps[side])                                # O(P), linear
```

A level that empties and is later re-created gets pushed again, so a price
can appear twice in a heap. That is harmless: a copy counts as valid only
while the level exists, and compaction removes duplicates.

### Compaction: what it bounds and what it does not

Without compaction, lazy deletion could grow without bound while the live
book stays small:

- **Deque dead entries:** a long-lived live order at the front of a level
  with many cancels behind it would keep every cancelled entry. Rule: when
  more than half of a level's entries are cancelled
  (`len(queue) > 2 · live_count`), rebuild the queue from its live entries.
  After every event each level holds at most 2 × its live orders, so total
  queue entries ≤ 2B.
- **Heap stale prices:** in cancel_churn (one BUY, then its cancel) the bid
  heap is never asked for its best price (BUYs look at the ask side), so
  without compaction every emptied level's price would stay: H would grow
  with M (about 5,000 entries at 10k events) while B ≤ 1. Rule: when a level
  is removed and `H > 2 · (live levels on that side) + 16`, rebuild. Then
  H ≤ 2P + 16 after every event, so log H = O(log P).

What compaction does NOT guarantee: it bounds the retained queue and heap
entries, but not Python's own allocations. CPython dicts (`orders`,
`levels[side]`) do not shrink their hash tables when keys are deleted, and a
rebuilt deque or list may keep spare capacity. Memory measured after a large
book has been cancelled down can therefore still reflect the peak book, not
the current B. The memory experiment must report this, not assume it away.

### Costs per operation

Claim types:

- **Worst-case:** always holds.
- **Expected:** average over hash behaviour. This assumes Python's
  randomised string hashing spreads the ids; a pathological set of colliding
  keys can make one dict operation O(B).
- **Amortized:** averaged over the whole stream. A single event can cost
  more, but the extra work is charged to earlier cancels or level removals,
  each of which pays for it at most once.

Building blocks:

| Step | Version A | B-sorted | B-heap |
|---|---|---|---|
| Duplicate-live check (validation) | O(B) worst (list scan) | O(1) expected (dict) | O(1) expected (dict) |
| Best-price lookup | O(B) worst (full scan) | O(1) worst (`keys[-1]`) | O(1) when `heap[0]` is live. Each stale top popped costs O(log H) worst; a stale entry is popped at most once, so amortized O(log H) per level removal. |
| One fill | O(B) worst (rescan for the next maker) + O(B) list delete if the maker is exhausted | O(1) (`popleft` worst O(1); `orders` delete expected O(1)) | same as B-sorted |
| Dead entry skipped (each of D) | none (A has no dead entries) | O(1) each; each is created by one cancel and skipped at most once → amortized O(1) per cancel | same |
| Best level exhausted by matching | inside the O(B) scans | O(1) amortized (`pop()` at the end; amortized because the list may occasionally shrink its allocation) | O(1) now (dict delete, lazy) + compaction check. A triggered rebuild is O(P), linear (`heapify`). It needs more than P + 16 stale entries first, so amortized O(1) per removal. |
| Residual-limit insertion | O(1) amortized (`list.append`) | `orders` insert O(1) expected (amortized for table resizes) + `deque.append` O(1) worst. If the price level is new: O(log P) search + O(P) list shift worst (`insort`). | same, but a new level costs O(log H) worst (`heappush`) |
| Level emptied by a cancel | – | O(log P) search + O(P) shift worst (`del` at any index; O(1) shift if it is the best level) | O(1) expected (lazy) + linear rebuild when triggered, amortized O(1) |
| Deque compaction | – | O(len(queue)), linear, when triggered; triggered only when dead entries outnumber live ones, so amortized O(1) per cancel | same |

Operations (F fills over L emptied levels, D dead entries skipped; since
H ≤ 2P + 16, log H = O(log P)):

| Operation | Version A | B-sorted | B-heap |
|---|---|---|---|
| AddLimitOrder = validation + matching + residual-limit insertion + output | O(B · (F + 2)) worst | O(F + D + L) for matching, + insertion: O(1) expected if its level exists, O(log P + P) worst if the level is new. Amortized (D charged to cancels): O(F + L) + insertion. | O(F + D) + O(log P) per stale top popped + insertion: O(1) expected (existing level) or O(log P) (new level) + compaction share. Amortized: O(F + (L + 1) · log P). |
| CancelOrder, not_found | O(B) worst | O(1) expected | O(1) expected |
| CancelOrder, level stays | O(B) worst (scan + list delete) | O(1) expected + amortized O(1) deque compaction | same as B-sorted |
| CancelOrder, level emptied | O(B) worst | O(log P + P) worst | O(1) expected + amortized O(1) heap-rebuild share |
| FillMarketSell = validation + matching + output (never inserts) | O(B · (F + 2)) worst | O(F + D + L); amortized O(F + L) | O(F + D) + O(log P) per stale top popped; amortized O(F + (L + 1) · log P) |
| inspect_book (checks only, not the hot path) | O(B log B) | O(B + P) (walks the levels via the key list) | O(B + P log P) (sorts the level keys) |
| Space (retained entries) | O(B) | O(B + P): ≤ 2B queue entries, P keys | O(B + P): ≤ 2B queue entries, H ≤ 2P + 16 |

Totals over a stream of M events with F_tot fills:

- Version A: about Σ over events of B_t · (F_t + 2), which is quadratic in M
  whenever B grows with M.
- B-sorted: O(M + F_tot) expected/amortized, plus O(P) list shifting for
  each new level and each cancel that empties a non-best level.
- B-heap: O((M + F_tot) · log P) amortized.
- For a fixed price range (the generator's `levels` = 1,000 per side), both
  B variants should be close to linear in M.

### Hypotheses for the measurements (to be tested, not claimed)

1. buildup, crowded, sweep and mixed, which are quadratic in Version A,
   become close to linear in M for both B variants.
2. crowded (P = 8): levels are almost never created or removed, so the two
   variants should be nearly equal; the time goes into dict and deque work.
3. buildup (P up to 2,000): each price level is created once and then
   reused, so index work is rare. Expect B-sorted ≈ B-heap.
4. sweep: many best-bid levels are exhausted. B-sorted removes each with an
   O(1) `pop()`; B-heap does a lazy O(log P) `heappop` on the next lookup.
   Expect B-sorted slightly faster, possibly within noise.
5. cancel_churn: every event creates or removes a level of a 0–1-level book.
   Both should be cheap. B-heap does a little extra work (stale entries,
   periodic compaction). Retained entries must stay flat as M grows; check
   with the compaction tests and later with tracemalloc.
6. Memory per order is higher in B than in A (dict entry, deque slot and an
   Order object instead of one list slot). Measure it; do not assume.

### Implementation

- `03_code/lob_b_common.py`: Order, Level and the shared core
  (process_event, AddLimitOrder, CancelOrder, FillMarketSell, MATCH, TIDY,
  inspect_book, shared invariant checks).
- `03_code/lob_b_sorted.py`, `03_code/lob_b_heap.py`: `OrderBook`
  subclasses that implement only the price index (INDEX_BEST, INDEX_ADD,
  INDEX_REMOVE_BEST, INDEX_REMOVE, ordered prices for `inspect_book`, index
  invariants).
- `--version` choices become `a`, `b_sorted`, `b_heap` (module `lob_<version>`)
  in replay.py, scaling.py and liquidation.py.
- `assert_invariants()` for B also checks: every live order sits in its
  level's queue in arrival order, `live_count` and `live_qty` match the live
  entries, no empty level exists, dead entries are not in `orders`, queue
  length ≤ 2 · live_count, the index matches the occupied prices exactly
  (sorted) or covers them with H ≤ 2P + 16 and a valid heap order (heap),
  and the book is not crossed.

### Evidence after implementation (22 Nov 2026)

**Correctness**

- Tests first: with stub `OrderBook`s for both variants, the unchanged
  suite gave 22 failed (every B case), 12 passed (every A case):
  `05_results/tests_fail_first_version_b.txt`.
- After implementation: 40 of 40 pass (`05_results/tests_by_case.csv`).
  That is all 12 hand-calculated and JSON test cases for A, B-sorted and
  B-heap, plus the differential test and the three compaction tests.
- Differential test (`05_results/differential_tests.csv`): 300 seeded
  streams, 52,287 events. After every event, the result dicts,
  `inspect_book()` and `last_seq` were identical across the three versions,
  and invariants and conservation held: 0 mismatching events, 0 failures.
  Planted bugs in throwaway copies were caught: a LIFO queue in 295 of 300
  streams, a wrong cancelled quantity in 297 of 300.
- Compaction tests fail when compaction is switched off (throwaway copies):
  the heap reached 17 entries with 0 levels at seq 34 of cancel_churn, and
  the deque bound broke.
- Replay of the five supplied 10k files with `--check`: invariants OK after
  every event for both variants. Fills, rejects, not_found cancels, peaks
  and final book sizes are identical to Version A
  (`05_results/replay_summary.csv`).

**Performance** (`05_results/scaling_version_*.csv`; single runs, engine
time only, seconds)

| scenario | A 30k | A 100k | B-sorted 30k | B-sorted 100k | B-heap 30k | B-heap 100k | B slope 10k→100k (sorted / heap) |
|---|---|---|---|---|---|---|---|
| buildup | 51.9 | stopped | 0.088 | 0.273 | 0.071 | 0.296 | 0.83 / 1.05 |
| crowded | 57.5 | stopped | 0.067 | 0.296 | 0.068 | 0.257 | 1.00 / 1.07 |
| mixed | 11.5 | stopped | 0.078 | 0.298 | 0.080 | 0.305 | 0.89 / 1.08 |
| sweep | 91.0 | stopped | 0.095 | 0.347 | 0.104 | 0.297 | 1.08 / 1.00 |
| cancel_churn | 0.023 | 0.184 | 0.059 | 0.220 | 0.072 | 0.212 | 0.86 / 1.08 |

Large liquidation (`05_results/liquidation_version_*.csv`, 4,062 bids on
981 levels):

| | 10% sale | 100% sale | 200% sale |
|---|---|---|---|
| A | 0.377 s | 2.390 s | 2.545 s |
| B-sorted | 0.0003 s | 0.0033 s | 0.0042 s |
| B-heap | 0.0005 s | 0.0043 s | 0.0044 s |

Book build (8,000 events) took about 5 s in A and 0.015–0.022 s in either
B variant.

**Hypotheses checked against these single runs**

1. Supported: all five scenarios are close to linear in M for both B
   variants (log-log slopes 0.83–1.08 between 10k and 100k). A's slope is
   about 2 on four of them.
2. and 3. Consistent: on crowded and buildup the two variants differ by
   15% and 8% at 100k, within the noise below.
4. Not supported, inconclusive: on sweep, B-sorted was faster at 30k (by
   9%) but B-heap was faster at 100k (by 14%).
5. The compaction tests pass and fail when compaction is off. Note:
   Version A is FASTER than both B variants on cancel_churn up to 30k
   (0.023 s vs 0.059 / 0.072 s). With B ≤ 1, A's scans are trivially short,
   while B creates an Order, a Level, a deque and an index entry for every
   submission and removes them on the cancel.
6. Not measured yet (tracemalloc run still to do).

**Noise.** For each variant there are two independent single runs of the
same code on the same 10k files: the 10k row in `replay_summary.csv` and
the 10k row in `scaling_version_*.csv`. They differ by 16–64% for B-sorted
and 8–36% for B-heap. The two variants differ from each other by 2–17% at
100k, which is inside that band. **The single runs cannot identify a winner
between B-sorted and B-heap on any scenario.** The final benchmark (warm-up,
5 repeats, medians, raw repeats kept) has to decide, and may still find
them equal.
