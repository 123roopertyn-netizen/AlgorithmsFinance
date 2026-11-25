# Assignment 1 — A limit order book that survives a growing market

Laurin Bühler · Algorithms in Finance (FIN71055) · Frankfurt School · November 2026

**Final Version B = B3r**: per-price FIFO queues with lazy cancellation, a heap price index and a per-side heap rebuild. On the five official workloads at 10,000 events B3r is 21x to 186x faster than the baseline A; at 100,000 events A exceeds the declared 600 s limit on three workloads while B3r needs under half a second. A is faster on `cancel_churn`, where the live book stays tiny. Every number in this report comes from committed result files (section 11) and can be inspected in the dashboard (`python -m streamlit run 04_dashboard/app.py`).

## 1. Task and model boundaries

We implement a **sequential, single-venue limit order book** for BTC with limit orders, market sells and cancellations, and benchmark a transparent baseline (A) against a revised design (B). Prices are integer ticks (cents per BTC), quantities integer units (10^-8 BTC); dollars appear only for display. Matching follows price-time priority and executes at the resting maker's price.

This is a model, not a trading system: one venue, one event at a time, no fees, balances, hidden orders, self-trade prevention, network or queueing delays. All workloads are **synthetic** (the course generator plus our own generators); none are calibrated to historical exchange data. Measurements are single-threaded CPython timings on one laptop (section 10).

## 2. Specification

The full specification is `SPEC.md`; each rule cites the assignment README or slide it comes from. The essentials:

- **Interface** (identical in A and B): `AddLimitOrder`, `CancelOrder`, `FillMarketSell`, a dispatcher `process(event)`, and inspection via `snapshot()`, `best_bid()`, `best_ask()`.
- **Validation** (one shared, ordered validator for all versions): object type, `seq` present, positive integer and strictly increasing, `type` known, required fields present, identifiers non-empty strings, side `BUY`/`SELL`, price and quantity positive integers (`bool` and `100.0` rejected), no duplicate *live* order identifier. A rejected event changes neither the book nor the last accepted `seq`. Cancelling an unknown, filled or cancelled order is valid and returns `not_found`.
- **Outputs** follow the README field names; fills are returned in execution order with maker, taker, price and quantity.
- **Decisions** where the task was open (Q1–Q15, N1–N3 in `SPEC.md`), e.g. unknown extra fields are ignored, `event_id` uniqueness is not enforced (memory would grow with M), and a market sell may not reuse a live order identifier.

## 3. Design

### Version A — transparent baseline (oracle)
One unsorted Python list of resting orders per side, kept in arrival order. Every lookup scans the list.

```
insert(e):            # LIMIT
  validate(e)                                  # duplicate-id check scans all orders: O(B)
  while e.qty > 0:
    m = best resting order on the other side   # full scan: O(B); ties -> earliest in list
    if m is None or not crosses(e.price, m.price): break
    q = min(e.qty, m.qty); emit fill(m, e, m.price, q)
    e.qty -= q; m.qty -= q
    if m.qty == 0: remove m from list          # O(B) shift
  if e.qty > 0: append e to its side           # keeps arrival order

cancel(id):  scan both sides for id (O(B)); remove it; else not_found
market_sell(e): same loop against bids, no price limit; residual discarded
```

### Version B = B3r — revised design
- `orders`: dict `order_id -> record` holding **live orders only** (O(1) expected lookups).
- Per side: `levels`: dict `price -> Level(deque of records, live count, stale count)`; FIFO per price.
- Per side: a **heap** of price keys (bids negated) with an `in_heap` set, so the best price is at the top; empty levels are removed lazily.
- **Lazy cancel**: a cancelled record is marked dead and removed from `orders`; it is skipped when it reaches the queue head. A queue is compacted when stale > live and stale > 32.
- **Heap rebuild** (the revision over B3): when a side's stale heap keys exceed its live levels (and 32), the existing heap list is filtered to live prices and re-heapified.

```
insert(e):
  validate(e)                                         # O(1) expected
  while e.qty > 0 and other side non-empty:
    p = best price of other side                       # pop stale heap keys first
    if not crosses(e.price, p): break
    L = levels[p]; drop dead records at L.head
    m = L.head; q = min(e.qty, m.qty); emit fill(m, e, p, q)
    if m.qty == 0: L.popleft(); del orders[m.id]       # partial maker keeps its place
    if L.live == 0: delete level p; maybe_rebuild_heap(side)
  if e.qty > 0:
    if e.price in levels: levels[e.price].append(e)    # O(1)
    else: create level; heappush(price) if not in_heap # O(log P)
    orders[e.id] = e

cancel(id):
  r = orders.pop(id) or return not_found               # O(1) expected
  r.dead = True; L.live -= 1; L.stale += 1
  if L.stale > L.live and L.stale > 32: compact L      # amortized O(1)
  if L.live == 0: delete level; maybe_rebuild_heap(side)

maybe_rebuild_heap(side):
  stale = len(heap) - len(levels)
  if stale > len(levels) and stale > 32:
    heap = [k for k in heap if price(k) in levels]; heapify(heap); in_heap = set(heap)
```

### Where the design comes from
Price levels with FIFO queues and an order-id map are the standard order-book organisation (Selph, *How to Build a Fast Limit Order Book*, 2011; formal definitions in Gould et al., 2013). Lazy deletion in a heap is described in the Python `heapq` documentation; rebuilding once garbage outweighs live data is global rebuilding (Overmars, 1983) with the table-contraction argument of Cormen et al. The combination, the per-side rebuild and its two pitfalls (section 9) are our own, derived from measurements and the attack. We rejected a price-indexed array (one slot per tick, as in high-performance C engines): the task has no price bound, Python loses the array's cache advantage, and the expected gain on the supplied ~1,000 price levels was small.

## 4. Correctness reasoning

**Invariants** checked after every accepted event (`SPEC.md` I1–I7): the resting book is never crossed; every resting quantity is positive; no order is stored twice; within a price, orders are in arrival (`seq`) order, never identifier order; fills execute at the maker's price; a partially filled maker keeps its position; rejected events leave state and last `seq` unchanged. For B3r additionally: inspection never shows dead records or empty levels.

**Conservation** (C1–C6): incoming quantity = sum of its fills + returned residual; a maker loses exactly its fills; a cancel removes exactly the residual; proceeds = sum of price x quantity; a market residual never rests; total resting quantity changes only by these amounts.

**Why B3r preserves them.** Priority: the heap top is always the best *live* price because stale keys are popped before use and the rebuild only removes keys whose level no longer exists; within a level the deque keeps arrival order and dead records are skipped, never reordered. Conservation: every fill decrements taker and maker by the same `q`; a cancel removes the record from `orders` and its residual from the level's live count in one step.

**Evidence** (tests were written first; the red run is saved in `05_evidence/`):

| Check | Result |
|---|---|
| Contract checks with hand-calculated results (worked example, every README edge case, 18 own datasets, 81 invalid-event cases) | all pass for A, B1, B2, B3, B3r, B3r_fast |
| Full test suite / attack suite | 1,032 / 1,995 tests pass |
| Mutants (deliberately broken versions, e.g. LIFO, partial maker re-queued, wrong book side) | 17/17 killed, plus 2 rebuild-trap mutants |
| A vs every B variant after every event (Hypothesis state machine) | no difference |
| Independent reference (written separately from the engines) vs B3r: supplied 50,000 events + 135,000 stress events | 0 differences |
| Red-team attack on the final B: fuzzer power check, then 1,152,000 every-event comparisons | 7/7 planted bugs found; 0 differences |

Agreement between two implementations is only supporting evidence; it is backed here by independent hand-calculated results and an independent oracle.

## 5. Complexity

Symbols: B active orders, P occupied price levels, F fills of an event, L levels emptied by it, S stale entries skipped, M incoming events.

| Operation | A | B3r |
|---|---|---|
| Validation | O(B) worst (duplicate-id scan) | O(1) expected (dict) |
| Insert, non-crossing | O(B) | O(1) expected; O(log P) if a new level is created |
| Insert/market sell with F fills | O((F+1)·B) worst | O(F + L·log P + S) amortized; S is paid by earlier cancels |
| Cancel | O(B) worst | O(1) expected + amortized compaction/rebuild |
| Best bid/ask | O(B) | O(1) amortized (stale pops paid by level removals) |
| Snapshot | O(B log B) | O(B + P log P) |
| Space | O(B) | O(B + P) live, plus stale ≤ max(live, 32) per level and ≤ max(P, 32) heap keys per side |

**Amortization.** Each cancel pays two credits: one for skipping or popping its dead record later, one for copying it once during compaction. Compaction and heap rebuild run only when garbage exceeds live data, so they are prepaid. Dict costs are *expected* (hashing), not worst case. Declared worst case of a single event: a rebuild or a purge of many stale heap keys costs O(live + stale), measured at 57 ms in an adversarial case (section 9).

Measured growth agrees with the analysis: from 1k to 10k events A's replay time grows with exponent **2.09** (buildup, crowded), **2.13** (sweep), 1.91 (mixed); B3r with **0.92-1.06**, and stays at about 1.0 from 10k to 100k.

## 6. Runtime

Protocol (README "Runtime"): `time.perf_counter`, one warm-up and five measured repeats, every raw repeat saved and the median reported; events pre-generated and pre-parsed; a fresh book per replay; parsing, construction and replay timed separately plus their total; tracing and counters in separate runs; identical inputs (SHA-256 per cell), settings and limits for all versions. Declared limits: 600 s per replay, 4 GiB traced. Sizes 1k/10k/100k, seeds 42/43/44, all five workloads, plus 1M (seed 43).

**Median replay speedup A/B3r** (median over seeds):

| Workload | 1k | 10k | 100k |
|---|---:|---:|---:|
| buildup | 11x | 170x | > 1,295x (A stopped at 600 s) |
| crowded | 17x | 186x | > 1,300x (A stopped) |
| sweep | 10x | 139x | > 1,260x (A stopped) |
| mixed | 2.8x | 21x | 299x |
| cancel_churn | **0.7x** | **0.8x** | **0.7x** |

At 1M events B3r needs about 5-7 s per workload; A was stopped at 600 s on four of five (A at 100k/1M is a single declared trial, section 10). B3r's throughput at 100k is 210,000-265,000 events/s.

**Where B does not win.** In `cancel_churn` add/cancel pairs keep almost no orders live, so A scans a handful of entries while B3r pays fixed per-event costs (record object, dict updates, validation). Both grow linearly; the difference is a constant factor, not complexity.

**Large liquidation** (fresh bid-only book, rebuilt before every trial; one market sell of 10/100/200 % of the quantity): at 10k orders the sale itself is 866x-1,165x faster in B3r and book construction 71x-100x faster. On a 10,000-order book a 10 % sale touched 1,003 makers on 100 price levels and a 100 % sale all 10,000 makers on 1,000 levels; on a 100,000-order book B3r's 10 % sale took 15 ms and the 100 % sale 132 ms. A 200 % sale costs the same as 100 %: once the book is empty the remainder is returned as unfilled. **Queue concentration** (same order count on 4 vs 1,000 prices) changes A's speedup only slightly (167x vs 189x at 10k): A's cost is driven by B, not by P.

**Latency.** In a separate instrumented run, B3r's per-event processing time on buildup at 100k has median 4.1 us and p99 11.2 us, with no drift as the book grows (early 4.0/11.3 us, late 4.1/12.0 us; nearest-rank percentiles). Cancels are cheapest (about 2 us), market sells have the widest tail. These are engine processing times: they exclude network and queueing delay, and reciprocal throughput is not a tail-latency estimate. Rare maxima of tens of milliseconds in large runs are Python generation-2 garbage collections, not order-book work: in a 100,000-order deep book the slowest event (26 ms) contained the one gen-2 collection, and with GC disabled the maximum fell to 3.5 ms. GC stays enabled for all versions.

## 7. Memory

Measured with `tracemalloc` in separate runs. **Included**: the book after construction and the current event's returned result; **excluded**: the pre-parsed input and any history of past results. Traced allocations are neither auxiliary space alone nor total process memory.

- Peak traced memory on the official workloads at 10k (excluding cancel_churn): A 0.3-1.9 MB, B3r 0.95-2.9 MB; B3r at 100k: 3.7-15.6 MB; on cancel_churn both stay around 10 KB. B3r usually pays for speed with per-order records, the id index and level objects; on crowded it needs less than A (1.1 vs 1.9 MB).
- **After cancellation churn** the book returns to its live size: B3r ends at about 3 KB with zero live orders even after 1,000,000 events; no history accumulates.
- **Stale entries and delayed cleanup.** B3 (the version before the revision) kept emptied price keys in its heap until they reached the top. With prices drifting away from the best price they never did: **37 MB for 2 live orders after 1M events**. B3r's rebuild bounds this to about 5 KB (heap of 18 entries). Lazy queue entries are bounded by the compaction rule; the attack showed up to 32 dead records can remain pinned per live level, a constant-factor cost we document.

## 8. Profiling and bottlenecks

**A's bottleneck** is the rescan after every fill: matching an incoming order with F fills scans the whole side F+1 times, and the duplicate-id check scans every order on each insert. Operation counters (separate `counts` runs, dashboard tab *Bottleneck explained*) make this visible: on buildup, A's duplicate-id check scans 499,500 records for 1,000 events and 49,995,000 for 10,000 events, exactly M(M-1)/2, and its best-order search scans another 249,964 and 24,999,375. Ten times more events cost a hundred times more work, which is why A's measured exponent is about 2 and why it stops at 100k.

**B1's bottleneck** (a sorted price list) is the insert far from the best price: every new deep level shifts the list (O(P) per insert). It is invisible on the supplied data (≤ ~1,000 levels near the best price) but makes B1 3x slower than B3 on `deep_book` and 18x slower on the attack scenario `far_end_flicker`.

**B3r's profile**: on the supplied 10k streams about one third of per-event time is input validation (three `isinstance`-based integer checks per event) rather than book work, and at 100k events JSON parsing costs as much as the whole replay (461 vs 463 ms on buildup). This motivated B3r_fast (section 9).

## 9. Revision and selection

The selection rule was fixed in `SPEC.md` **before** the candidate measurements: (1) a robustness filter excluding any candidate that hits a limit, is more than 3x slower than the best variant on any official or own adversarial scenario, or keeps memory proportional to history; (2) among survivors, the lowest geometric mean of the 15 official 100k median replay times; (3) a fallback allowing one targeted revision per violation if nobody passes.

| Candidate | Official 100k geomean | Violation |
|---|---:|---|
| B1 sorted price list + deques | 0.4244 s | `deep_book` 3.06x slower than B3 (borderline; 2.80x in a re-run; 18.4x on `far_end_flicker`) |
| B2 sorted list + OrderedDict levels | 0.4726 s | `deep_book` 3.02x; 10-15 % slower overall |
| B3 heap + deques | 0.4289 s | memory grows with history (37 MB, section 7) |
| **B3r** = B3 + heap rebuild | **0.4247 s** | none in throughput; see the spike below |

No candidate passed, so the fallback produced **B3r**. Its rebuild avoids two pitfalls found by our red-team attack: rebuilding from the `levels` dict (13x slower, because a Python dict keeps its peak capacity) and counting stale keys over both sides while rebuilding one (299x slower). Tests now check that rebuild work stays at most 2 heap entries per cancel; measured: exactly 2.00.

**One interpretation made after measuring, stated openly.** In `spike_purge_at_threshold` the timed replay is a single sell that purges 100,000 stale heap keys: 57 ms for B3r vs 0.03 ms for B1. Read literally, the 3x filter excludes B3r too. We keep B3r because this single-event spike was declared as an accepted tail-latency cost before measuring, and because over the stream that creates the situation B3r is faster (construction + sell 1.78 s vs 4.63 s for B1).

**Controlled optimisation: B3r_fast — tried and rejected.** Profiling showed validation as the largest single cost, so we built B3r_fast: the same algorithm, with a fast path for ordinary valid events that falls back to the unchanged validator for everything else. Identical behaviour was shown by 146,514 every-event comparisons, 300,000 random validator cases and all test suites. Rule fixed before measuring: at least 10 % faster on the official grid and no scenario more than 5 % slower.
1. Cross-session comparison: 11.3 % faster, but rejected; several cells exceeded 5 %, and analysis showed session noise (two B3r reference cells were about 2x faster than the same cell for every other version and seed).
2. Binding same-session rematch, with alternating order per case and the method fixed and committed beforehand: **12.7 % faster**, faster on 25 of 27 scenarios and within the bound on 26, but one cell failed (`dead_slot_rebuild` at 1k: 3.66 vs 3.42 ms, ratio 1.068). **Rejected; B3r stays final.**

The lesson: per-scenario bounds need a minimum measured duration or confidence intervals, otherwise sub-millisecond noise decides. We did not re-measure a third time; B3r_fast remains in the repository as a tested, documented variant.

## 10. Limitations

- **Synthetic workloads only**; no calibration to real exchange flow. Our adversarial and attack scenarios are deliberately extreme.
- **One machine, CPython only, GC enabled.** Session-to-session noise of up to ±30-50 % appeared in individual cells; medians over seeds and the geometric mean over 15 cells are the robust figures.
- **Declared deviations for the baseline A** (decided and committed before A was measured): at 100k and 1M a single trial without warm-up; on the supplementary experiments (queue, liquidation, churn, adversarial, post-attack) only up to 10k. Speedups where A was stopped are **lower bounds**. B3r runs the full protocol everywhere.
- **Latency** is closed-loop engine processing time; it says nothing about queueing under load or the rate at which a live venue would overload.
- **Known weak spots of B3r**: the declared O(live + stale) single-event spike; up to 32 dead records pinned per live level; prices that are multiples of 2^61 - 1 collide in Python's integer hash and make every dict-based version quadratic (documented, not capped, because the task allows any positive price); malformed input files are rejected with one error line rather than processed.
- **Memory** figures are traced Python allocations under the boundary stated in section 7, not process RSS.

## 11. Reproducibility and use of AI

**Reproduce** (Windows, Python 3.13; exact commands, expected outputs and the submitted commit are in `README.md`):
```
python -m pip install -r requirements.txt
python -m pytest                                           # full suite
python run.py lob.replay 06_data/supplied/worked_example.jsonl   # final Version B by default
python -m streamlit run 04_dashboard/app.py                # dashboard from committed results
```
Large inputs are regenerated with the supplied `generate_orders.py` (commands and SHA-256 in `00_docs/DATA_MANIFEST.json`); million-event files are not committed. Result folders: `03_results/runs/20261122T012525Z_5eaeb03_phase4/` (candidates), `…130145Z_00bb1ad_phase4_b3r_20261122/` (B3r, A baseline, post-attack), `…200528Z_8a22753_…b3r_fast…/` and `…210801Z_e4fd928_…rematch…/` (B3r_fast). Each records machine, Python and dependency versions in `env.json`. The selection is documented in `00_docs/FINAL_SELECTION.md`, the attack in `07_attack/ATTACK_REPORT.md`.

**AI use.** Code was written by AI coding agents (Claude Code, Codex) under rules in `AGENTS.md`: git and all pushes stayed with me, tests came before code, and each phase ended at a checkpoint that I reviewed with a separate AI assistant, which re-checked results with independently written code. The full record is `00_docs/AI_LOG.md`. In summary:
- **Accepted**: the B1 design from the literature; the B3r revision after measurement; the attack's rebuild guidance (filter the heap, count per side); the replay fixes (unbounded integers, byte-order marks, clear input errors).
- **Corrected**: a benchmark harness that validated only the last repeat; a test helper misread as a contract check (the first red run is kept as superseded); a native Hypothesis build blocked by Windows Smart App Control (version pinned); an inconsistent rebuild threshold (2x vs 1x live, resolved and logged); a dashboard that only worked inside a git checkout (disk fallback added); a miscount in our own write-up (26 → 25 of 27 scenarios).
- **Rejected**: hidden instructions embedded in the assignment PDF asking AI tools to insert a specific word into code (logged, never followed); a price cap against hash collisions (it would change the specification); a price-indexed array; selecting a variant per input file (lookahead); and B3r_fast, by our own pre-registered rule.
