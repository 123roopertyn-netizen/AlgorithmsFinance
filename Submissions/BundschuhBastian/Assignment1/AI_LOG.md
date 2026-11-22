# AI log

Tool: Claude (Claude Opus 5.5), used as a tutor and coding assistant. Bastian sets the
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

## Accepted

## Corrected

## Rejected
