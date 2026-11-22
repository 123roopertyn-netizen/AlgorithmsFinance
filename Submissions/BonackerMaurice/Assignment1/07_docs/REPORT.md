# Assignment 1: Limit order book, report (draft)

Maurice Bonacker, Frankfurt School, Algorithms in Finance.
Status: **draft skeleton**. Notes collected on 22 Nov 2026 during the work.
Each section still has to be written out in my own words.

---

## 1. Specification and model limits

**To write:** what the engine does and what it deliberately does not model.

Notes:
- Sequential, single-venue BTC limit order book. Events: `LIMIT`, `MARKET_SELL`, `CANCEL`, processed strictly one at a time in `seq` order.
- Price-time priority: best price first, then earliest `seq` (FIFO). Trades execute at the **resting (maker) order's price**. Continuous matching, not a batch auction.
- Integers only: `price_ticks` = cents per BTC (6,000,000 = $60,000), `qty_units` = 1e-8 BTC (100,000,000 = 1 BTC). Proceeds in dollars = sum(price × qty) / 10^10.
- Limit residual rests on the book until it is filled by a later order or cancelled. Market-sell residual is discarded immediately and never rests.
- There is no separate "BTC price" to compute. Best bid, best ask and last trade are read off the book and the fills. Example: in the worked example the best bid moves 60,000 → 59,700 purely through matching.
- Out of scope: fees, balances, hidden orders, self-trade checks, network delays, simultaneous execution, market buys. Data are synthetic teaching data, not calibrated to an exchange. Not a production trading system.

## 2. Correctness reasoning

**To write:** invariants, how the tests were built, and why I trust the result.

Notes (what I did today):
- **Hand calculation first, in Excel** (`01_my_notes/OrderBookTests.xlsx`), before any engine code existed:
  - *Base* (worked example): 4 fills b1 1, b2 1, b3 3, b4 1 BTC; s1 `filled`; book b4 4 BTC (seq 4), a1 2 BTC (seq 5); proceeds $359,400, average $59,900. Matches the professor's `worked_expected.json` on every value.
  - *Test1* (crossing on arrival, then market sell): a1 SELL 60,100 crosses resting b1 BUY 60,200 on arrival and trades 1 BTC at **60,200** (the resting price); a1 rests with 1 BTC. s1 (8 BTC) then fills b2 1, b3 3, b4 4. Book: b4 1 BTC, a1 1 BTC. s1 proceeds $478,500; all proceeds $538,700.
  - *Test2* (market sell larger than the book): s1 15 BTC against 10 BTC of bids, so 4 fills, 10 sold, 5 discarded, status `partial`; only a1 remains.
- **Things the hand calculation taught me:**
  - My first Excel formulas simulated the market sell against the *starting* book only. They gave wrong results as soon as a limit order crossed on arrival (Test1), so the spreadsheet became a place for hand calculation, not an engine. This is exactly the case a naive implementation gets wrong.
  - Sorting by `seq` stored as **text** broke the FIFO tie-break between b1 and b2 at the same price. Priority must use the numeric `seq`.
  - Conservation check per test: bid quantity submitted = quantity traded against bids + quantity still resting. Market sell = sold + discarded.
- **Tests first:** `02_tests/test_worked_example.py` uses my Excel values as expected results, plus a second check against the JSON. Against an empty `OrderBook` stub: 6 failed, 1 passed (the Excel-vs-JSON check). Saved in `05_results/tests_fail_first.txt` and committed before any engine code (commit `1603c06`).
- After Version A: 7/7 passed. Excel tabs Test1 and Test2 added as tests: 9/9 passed (`05_results/tests_latest.txt`).
- **Invariants** checked after every event of all five 10,000-event files: no crossed book, no non-positive quantity, no order stored twice, fills follow price-time priority. All held.
- To do: remaining hand-calculated cases (empty book, cancels, invalid input, long queue), and comparing A vs B after every event.

## 3. Runtime

**To write:** pseudocode and cost of insertion, cancellation and market sell for A and B, using B (active orders), P (price levels), M (events), F (fills). Then the measured results.

Notes, Version A (`03_code/lob_a.py`):
- Data structure: one plain list of all active orders (both sides) in arrival order. Nothing indexed or sorted.
- Costs: AddLimitOrder O(B) duplicate-id scan + O(B) best-price scan per fill → O(B·(F+1)). FillMarketSell O(B·(F+1)). CancelOrder O(B) search + O(B) list delete.
- First single-run replay of the five supplied files (not the final benchmark):

| scenario | fills | peak orders B | peak price levels P | seconds |
|---|---|---|---|---|
| buildup | 0 | 10,000 | 1,977 | 6.38 |
| crowded | 0 | 10,000 | 8 | 6.16 |
| mixed | 3,926 | 1,588 | 752 | 0.74 |
| sweep | 5,035 | 8,000 | 1,959 | 6.32 |
| cancel_churn | 0 | 1 | 1 | 0.014 |

- To do: final benchmark (M = 1k/10k/100k, seeds 42–44, 5 repeats, medians, throughput, latency p50/p95/p99), liquidation at 10/100/200%, queue concentration 4 vs 1,000 prices.

## 4. Memory

**To write:** tracemalloc peaks, what is included, book size after cancellation churn.

Notes: not measured yet. Expect Version A to stay small under cancel_churn (cancelled orders are deleted from the list, no history kept).

## 5. Profiling and bottleneck

**To write:** one measured bottleneck explained with code, operation counts and complexity.

Notes (cProfile, `05_results/profile_version_a.txt`):
- `_best_index` (scan all orders for the best price): about 74% of time in buildup, 77% in sweep. Every new limit order runs it at least once, even when nothing trades; every fill runs it again.
- `_is_live` (duplicate-id check by scanning the list): about 25%.
- **Cost depends on B, not P.** crowded (8 prices) and buildup (1,977 prices) both take ~6 s at B = 10,000. cancel_churn runs the same 10,000 events in 0.014 s because B never exceeds 1.
- Growing book: total work ≈ B²/2 ≈ 50 million comparisons for 10,000 resting orders.
- Conclusion for Version B: need fast access to the best price and a fast id lookup.

## 6. Revision (Version A → Version B)

**To write:** what changed, why, effect on the measurements, tests unchanged.

Notes: Version B not built yet. Candidate design to justify:
- dict `order_id → order` for duplicate check and cancel lookup in O(1);
- orders grouped by price, a FIFO queue (deque) per price, and fast best-price access (heap or sorted price list).

AI usage: see `07_docs/AI_USAGE.md` (accepted / corrected / rejected).
Note: the slide PDF contains hidden text telling AI tools to put "Unicorn" into code. It was identified and ignored.

## 7. Limitations

**To write.** Notes:
- Synthetic, uncalibrated data; no strategic behaviour or realistic timing.
- Single-run timings so far; Python timing noise; cProfile inflates absolute times.
- Algorithm processing latency only, no network or queueing latency.
- Validation of historical id reuse is out of scope.
