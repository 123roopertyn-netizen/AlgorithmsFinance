# Report: a limit order book, a baseline and a revision

Huang Jiaxin · Algorithms in Finance · Assignment 1

Notation: **M** incoming events, **B** active orders, **P** occupied price levels (both
sides), **F** maker fills of one event, **L** price levels emptied by one event.

## 1. Specification

Input: a stream of events in `seq` order, starting from an empty book (LIMIT, MARKET_SELL,
CANCEL; fields and units as in the assignment README). Prices are integer ticks of 0.01 USD
per BTC, quantities integer units of 1e-8 BTC; all matching and conservation checks use
integers.

Output per event: the fills in execution order (`maker_id`, `taker_id`, `price_ticks`,
`qty_units`) and a status (`filled`/`resting` for limits; `filled`/`partial`/`unfilled` for
market sells; `cancelled`/`not_found` for cancels; `rejected` with a reason for invalid
events). `snapshot()` returns the active orders in canonical order.

Rules: better price first; FIFO by arrival at equal prices; trades at the resting order's
price; partial fills keep their priority; a limit residual rests with its own `seq` as
arrival rank; a market-sell residual is discarded; a rejected event changes nothing, not
even the last accepted `seq`. Model boundaries: one venue, sequential, all orders eligible,
no fees, balances, hidden orders, self-trade checks or delays. Not a production system.

## 2. Correctness

### Invariants (hold after every accepted event)

1. **Price-time order.** Version A: among all orders of one side, the matching loop always
   picks the best price and, at that price, the smallest `seq`. Version B: each price
   level's deque holds its active orders in increasing `seq`, because orders are only ever
   appended (with strictly increasing `seq`) and removed from the front or lazily marked
   inactive; the heap top, after skipping prices that have no level, is the best price.
   So both versions take the same next maker.
2. **Quantity conservation.** Each trade subtracts the same amount `min(q_in, q_rest)` from
   the incoming and the resting order, so incoming quantity = sum of its fills + returned
   residual, and each maker loses exactly its fills. A cancel removes exactly the
   remaining quantity. Proceeds are the integer sum of price × quantity.
3. **Book shape.** No crossed book: an incoming order stops trading only when it is
   exhausted or the best opposite price no longer crosses its limit, so anything it leaves
   resting is below the best ask (bids) or above the best bid (asks). No resting quantity
   ≤ 0: exhausted makers are removed in the same step. No order stored twice: an order
   enters the book only once, and the duplicate-live-id check rejects reuse.
4. **Version B bookkeeping.** `index` holds exactly the active orders; `live[side][p]`
   equals the number of active orders in that deque; a level exists iff it has an active
   order. Stale deque entries and stale heap prices never affect results, because they are
   skipped before they could be used.

Termination: every iteration of a matching loop either removes a maker, reduces the
incoming quantity to zero, or stops.

### Evidence

* Tests were written first and failed on empty stubs (`evidence/step3_...`).
* 201 tests pass on both versions (`evidence/final_tests.txt`): the course example
  (359,400 USD), hand-calculated cases for every situation listed in the assignment,
  25 kinds of invalid events, invariant and conservation checks after every event of 20
  random streams, and agreement of A and B after every event on 30 random streams and the
  five supplied 10,000-event samples.
* The benchmarks re-check correctness: A and B give identical liquidation results, and a
  full liquidation of concentrated and spread-out books fills in price-time order.
* Agreement between two versions is only extra evidence: on the empty stubs, the
  equivalence tests passed trivially.

## 3. Two versions: pseudocode and cost

### Version A (baseline): one list of all active orders

```
AddLimitOrder(e):
    validate e                         # duplicate-id check: scan the list, O(B)
    while e.qty > 0:
        m = best opposite order        # scan the list, O(B)
        if m is None or m.price does not cross e.limit: break
        trade min(e.qty, m.qty) at m.price
        if m.qty == 0: list.remove(m)  # O(B)
    if e.qty > 0: append e             # O(1) amortized
FillMarketSell(e): same loop on the bids without a limit; residual discarded
CancelOrder(e):    find target by scanning, O(B); list.remove, O(B)
```

| Operation | Time | Notes |
|---|---|---|
| non-crossing insertion | Θ(B) | two scans: duplicate check and best opposite order |
| market sell / crossing limit | Θ((F + 1) · B) | one scan and possibly one removal per fill |
| cancel | Θ(B) | scan and removal |
| inspection | Θ(B log B) | sort for the canonical order |
| space | Θ(B) + Θ(F) output | no history; inactive orders are removed at once |

A stream of M non-crossing submissions therefore costs Θ(M²).

### Version B (revision): price levels, FIFO deques, heaps, an id index

```
AddLimitOrder(e):
    validate e                         # duplicate check: dict lookup, O(1)
    while e.qty > 0:
        p = best opposite price        # heap top; pop stale prices first
        if p is None or p does not cross e.limit: break
        q = deque at p
        while e.qty > 0 and q has a live order:
            m = q.front; if m is inactive: popleft; continue      # lazy cancel
            trade min(e.qty, m.qty) at p; if m.qty == 0: popleft, delete from index
        if level p has no live order: delete level (and maybe rebuild the heap)
    if e.qty > 0: append to deque at e.limit (new level: heap push), add to index
CancelOrder(e):
    m = index.pop(target) or return not_found       # O(1)
    mark m inactive; live -= 1
    if live == 0: delete the level; elif the deque is mostly stale: rebuild the deque
```

| Operation | Time | Notes |
|---|---|---|
| non-crossing insertion | O(1), or O(log P) for a new level | dict check, deque append, heap push |
| market sell / crossing limit | O(F + L log P) plus amortized O(1) per stale entry | each fill O(1); each emptied level one heap pop |
| cancel | O(1) amortized | lazy; level deletion O(1); compaction amortized |
| inspection | O(B + P log P) | sort the price levels, walk the deques |
| space | O(B + P) after compaction | without compaction: grows with all cancels |

**Lazy cleanup and the amortized claim.** Cancel does not search the deque; the entry is
removed when it reaches the front, or when its level loses its last live order. Two rules
bound the leftovers: a deque is rebuilt when it holds more than 2·live + 8 entries, and a
heap when it holds more than 2·(levels) + 16 prices. A rebuild of size k is triggered only
after more than k/2 cheap operations created garbage, so the cost per operation is
**O(1) amortized** (not worst case: a single cancel can trigger an O(k) rebuild).

## 4. Runtime

*Filled in from the final run (results/timing_raw.csv, dashboard tabs "Replay scaling",
"A vs B", "Large liquidation", "Queue concentration", "Cancellation churn").*

## 5. Latency

*Filled in from the final run (results/latency_summary.csv).*

## 6. Memory

*Filled in from the final run (results/memory.csv, memory_growth.csv).*

## 7. Profiling and the main bottleneck

*Filled in from the final run (results/profile_*.txt, operation_counts.csv).*

## 8. The revision

*Filled in: what changed from A to B, why, its measured effect, and where it does not win.*

## 9. Extras

1. **Price impact of a large sale**: average fill price and its distance from the best bid
   for 10 %, 100 % and 200 % sales (dashboard tab "Large liquidation").
2. **Lazy cleanup with and without compaction** (`B_nocompact`): time and memory under
   cancellation churn, and the number of stale entries left behind.
3. **Docker and one-command reproduction** (`run_all.sh`).

## 10. Limitations

* Synthetic, uncalibrated data; sequential replay of one venue. Processing latency excludes
  queueing and network delays and cannot tell when a live venue would overload.
* Timings come from one laptop inside Docker; they vary between runs and machines.
* Version A could not finish the largest workloads within the declared limit; those runs
  are reported as stopped, not extrapolated.
* tracemalloc sees Python allocations only; it is neither auxiliary space nor total
  process memory.
* The liquidation, latency and memory experiments use seed 42 only, to keep the total
  run time manageable; the replay grid uses seeds 42, 43 and 44.

## 11. Use of AI

*To be written by Jiaxin.*
