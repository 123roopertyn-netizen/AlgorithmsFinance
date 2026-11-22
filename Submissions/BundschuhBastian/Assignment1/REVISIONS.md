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
