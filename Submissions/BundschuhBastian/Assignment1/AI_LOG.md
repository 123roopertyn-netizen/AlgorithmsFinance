# AI log

Tool: Claude (Claude Opus 5.5 in Phases 0-1, Claude Sonnet 5.5 from Phase 2), used as a tutor and coding assistant. Bastian sets the
specification decisions, the order of the phases and reviews every step. This log records
what was accepted, corrected or rejected, with evidence (commit hashes, test output).

## Phase 0: setup and specification

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| Folder `Submissions/BundschuhBastian/Assignment1/`, same conventions as the lab (venv, pytest.ini, AI log) | accepted | course README; lab submission |
| `SPEC.md` with decision IDs D1-D19 and fixed reason codes, so A and B return identical results | accepted by Bastian | needed for exact A-vs-B comparison |
| D1: `bool` and float are not integers (`type(x) is int`) | accepted by Bastian | `isinstance(True, int)` is True in Python |
| D5: duplicate live ID check also for MARKET_SELL | accepted by Bastian | spec says "duplicate live submission identifiers" |
| Record decompressed sha256 in addition to the .gz sha256 | accepted | regenerating `mixed` seed 42 with Python 3.13 / zlib-ng gave a different .gz hash but identical decompressed content |

## Phase 1: tests first

Bastian's instruction: no "elegant" tests; concrete edge cases that could crash the code.

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| `tests/helpers.py::step()`: after EVERY event check no mutation of the caller's event, I1-I3 (not crossed, qty > 0, id once, canonical order, best bid/ask agree), result keys, I4-I7 conservation, price-time order of fills | accepted | uses only the public interface, not `lob.common`, so shared-code bugs cannot hide |
| 86 bad events (non-dict input, `None`, `True`, `1.0`, `nan`, `inf`, unhashable lists/dicts as `type` / ids, lower-case side, missing fields), each sent into a book where a wrong accept WOULD trade | accepted | a missing check shows up as a changed book, not only a wrong status |
| D9 order tests (several errors in one event) | accepted | A and B must report the same reason |
| Hand-calculated matching/cancel cases incl. long queue (1000 orders, ids counting down), stale best price after emptying a level, cancel head/middle/tail, churn, huge ints | accepted | list in README "Tests" |
| Supplied-file tests with outcomes derived from `generate_orders.py` | corrected | first draft claimed the last `sweep` sale is `partial`. Checking the file showed the earlier sells (414,709,280,000 units) exceed all bids (205,760,000,000), so the last sale is `unfilled`. Test now computes this from the file |
| Red run against stubs | accepted | 328 tests: 2 passed (reader, implemented in Phase 0), all other failures/errors are `NotImplementedError` only: `docs/test_logs/phase1_red.txt` |
| Cross-check of the hand-calculated expected values with a throwaway naive engine kept OUTSIDE the repo | accepted | catches arithmetic slips in the tests before Phase 2; all 328 agreed. It is not a test oracle: no expected value was copied from it |

## Phase 2: Version A

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| Version A as one list of `[id, price, qty, seq]` per side, every lookup a scan; shared `validate()` in `lob/common.py` | accepted | matches the agreed design; expected cost O(B) per insert and cancel. Commit 22b3da0 |
| First check of "all A tests pass" with `pytest -k "not B"` | corrected | `-k` is case-insensitive and also matched names such as "book", so it deselected 278 of 328 tests and only 50 ran. Re-checked by listing every failure and error: none outside `[B...]`; 163 `[A...]` tests passed |

## Phase 3: Version B and speed

Bastian's rules: correct B first (commit before optimizing), then one change at a time with a
cProfile first and before/after timings on `mixed` and `buildup` at 100,000 events, all tests green,
each step in `REVISIONS.md`.

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| B = per side `price -> OrderedDict(order_id -> [qty, seq])`, sorted price list (asks stored as `-price`), index `order_id -> (is_bid, price)`, empty levels removed at once | accepted | 333 tests pass; replay output equals A on all five supplied 10,000-event files (2ef6e65) |
| `OrderedDict` instead of a plain dict for the FIFO queue | accepted (my choice, not in SPEC) | plain dict keeps deleted slots at the front, so finding the oldest order can get slow |
| First timing method (`gc` on, 5 repeats, before/after run in separate processes) | corrected | repeats ranged 0.26-0.36 s; a 12% gain was invisible. Replaced by `tools/ab_timing.py`: interleaved before/after, `gc` off during timing, 11 repeats, median, output compared |
| 1: `is_valid_fast()` in `common.py`; falls back to the reference `validate()` for the reason | accepted | mixed -12.6%, buildup -8.9%. Fuzz test `tests/test_validation_fast.py` checks it never accepts what `validate()` rejects (741407e). This touches shared code that CLAUDE.md calls the only guard: please review |
| 2: skip `_take` when the order cannot cross; inline `add` | accepted | -4.0% / -9.0% (e49a5ea) |
| 3: iterate the level instead of `next(iter(...))` | rejected | +0.5% / -1.2%, inside noise; reverted |
| 4: pass the order index (container) to `is_valid_fast` | accepted | -3.2% / -3.7% (e519381) |
| 5: inline validation into `process()` | rejected | +1.1% / +0.8%. Kept the A-vs-B fuzz test written for it (`tests/test_process_fuzz.py`; all reason codes and statuses occur) |
| 6: heap + lazy deletion instead of bisect | rejected | +4.5% / +7.0%; 333 tests passed but slower |
| 7: `__slots__` records | rejected | +1.5% / +4.2% |
| 8: tuple records | rejected | -1.1% / -2.4%, inside the ~2% noise |
| Run the other three scenarios at 100,000 events before pushing | accepted (Bastian's request) | all between 0.12 and 0.21 s; A and B identical on `cancel_churn` 100,000 (same checksum) |

Cumulative speed-up of kept steps: mixed -19.0%, buildup -23.5% (0.1995 -> 0.1617 s and
0.2285 -> 0.1748 s). Numbers depend on this machine and are repeated in `REVISIONS.md`.

## Phase 4: own generator and A-vs-B equivalence

| Suggestion | Decision | Reason / evidence |
|---|---|---|
| `tools/gen_small.py`: stdlib-only, stateless generator with four profiles (`tight`, `wide`, `single_level`, `dirty`): small price and id pools, ids whose text order differs from arrival order, reused and duplicate live ids, unknown cancels, oversized market sells, `seq` gaps and non-increasing `seq`, corrupted and non-dict events | accepted | deterministic per seed (test); sample output checked by hand: a BUY reusing a live SELL id is rejected as `duplicate_live_order_id` |
| `tests/test_equivalence.py`: 40 seeds x 250 events x 4 profiles in lock step; both books go through `helpers.step()` (independent I1-I7) and then results, snapshots, best bid/ask must be equal after EVERY event | accepted | 12 new tests, 345 in total pass |
| Same comparison on the five supplied 10,000-event files | corrected to a cheaper check | a full snapshot after every event is O(M*B) on `buildup`/`crowded`. Now results and best prices are compared after every event, the full book every 200 events and at the end. Stated in the test docstring |
| Coverage test so the comparison cannot be vacuous | accepted | requires every status, all 11 reason codes, >=3 fills, fills over >=2 levels and 2 makers at one price to occur |
| Mutation check of the new tests (bugs planted in B, then restored; `git status` clean afterwards) | accepted | (1) touching prices no longer cross, (2) a partial fill moves the maker to the back of its queue, (3) cancel leaves an empty price level: all three fail. Mutation 1 fails with `crossed book: bid 104 >= ask 104` from the independent checker, not from a crash |
| My first mutation run | corrected | two `sed -i` commands failed on macOS (needs `-i ''`), so mutation 1 never ran and "4 passed" meant nothing. Redone with Python edits |
| Pyright: `__doc__.splitlines()` may be `None` | accepted | fixed with `(__doc__ or "")`; pyright reports 0 errors on the new files |

## Accepted

## Corrected

## Rejected
