# REVISIONS: Version A -> Version B

## 1. Data organization (Phase 3a, commit 2ef6e65)

| | Version A | Version B |
|---|---|---|
| Book | one list of `[id, price, qty, seq]` per side | per side: `dict price -> OrderedDict(order_id -> [qty, seq])` + sorted list of prices (asks stored as `-price`, so the best price is always the last element) |
| Index | none (scan) | `dict order_id -> (is_bid, price)` |
| Best price | O(B) scan | O(1) |
| Insert | O(B) (the scan for "is id live?") | O(1) at an existing price; O(P) for a new price (list insert) |
| Cancel | O(B) | O(1) at the level + O(P) if the level becomes empty |
| One fill | O(B) (find best, `list.pop`) | O(1) (+ O(1) pop of the best price when a level empties) |
| Empty levels | n/a | removed at once, so no stale entries |

`OrderedDict` (not a plain `dict`): `next(iter(...))` for the oldest order stays O(1) after many
deletions at the front; a plain dict would skip over deleted slots.

## 2. Speed optimizations (Phase 3b)

Method for every row (`tools/ab_timing.py`): same machine, same stream (100,000 events, seed 42,
`python generate_orders.py --scenario {mixed,buildup} --events 100000 --seed 42 --out
data/generated/{scenario}_100000_s42.jsonl.gz`), parsing excluded, `gc` disabled while timing,
before and after run **interleaved**, 11 repeats, median. Output (all results + final snapshot)
must be identical, and all tests must pass. Profile first (`cProfile`).

Baseline profile (committed B): `validate()` is ~50% of the time on both streams.

| # | Change | mixed before -> after | buildup before -> after | Tests |
|---|---|---|---|---|
| 1 | `is_valid_fast()`: one-pass accept test for good events; only if it says "not sure" run the reference `validate()` (so reason codes cannot differ). New fuzz test `tests/test_validation_fast.py`. | 0.1993 s -> 0.1742 s (-12.6%) | 0.2198 s -> 0.2003 s (-8.9%) | 332 pass |
| 2 | `AddLimitOrder`: call the matching loop `_take` only if the order crosses the best opposite price (one comparison); inline `_Side.add` (no method call per insert). | 0.1747 s -> 0.1677 s (-4.0%) | 0.2009 s -> 0.1827 s (-9.0%) | 332 pass |
| 3 (rejected) | `_take`: iterate the level with `for ... in level.items()` and delete used-up makers afterwards, instead of `next(iter(level.items()))` per fill. | 0.1670 s -> 0.1678 s (+0.5%) | 0.1833 s -> 0.1812 s (-1.2%) | 332 pass; reverted (within noise: few fills per event in these streams) |
| 4 | `is_valid_fast` takes the order index itself (`order_id not in live_ids`) instead of a callable: one function call less per event. Fuzz test adapted (same checks). | 0.1671 s -> 0.1618 s (-3.2%) | 0.1836 s -> 0.1767 s (-3.7%) | 332 pass |

Cumulative (committed B `2ef6e65` vs now, same method): mixed 0.1995 s -> 0.1617 s (-19.0%),
buildup 0.2285 s -> 0.1748 s (-23.5%), identical output.

Not tried yet: heap + lazy deletion instead of the sorted price list (bisect); `__slots__` /
list records vs the current `[qty, seq]` lists; inlining validation into `process`.
| 5 (rejected) | Inline the fast validation into `process()` (no `is_valid_fast` call). | 0.1607 s -> 0.1624 s (+1.1%) | 0.1784 s -> 0.1799 s (+0.8%) | 333 pass; reverted (a function call is not the cost) |

New test from this step, kept: `tests/test_process_fuzz.py` feeds fuzzed good and bad events to A and B `process()` and requires identical results and snapshots (covers every reason code and every status).
| 6 (rejected) | Best price with a heap + lazy deletion (bids stored as `-price`; emptied levels stay in the heap until they reach the top) instead of the sorted list + bisect. | 0.1610 s -> 0.1682 s (+4.5%) | 0.1736 s -> 0.1856 s (+7.0%) | 333 pass; not kept. With ~1,000 levels, `list.insert` / `del` is one C memmove and cheaper than heap pushes plus stale-entry cleanup. Amortized cost of the heap is also worse for memory (stale entries grow with cancel churn). |
