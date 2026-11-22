# AI usage (Assignment 1)

AI tool: Claude Code (Claude Opus 5.5), session of 22 November 2026.
Maurice gave the task list and the expected values; the AI wrote the code.
The "Decision" column is for Maurice: **accepted**, **corrected** (say how)
or **rejected**.

## Session 1: tests, Version A, replay, first profile, simple dashboard

### What the AI produced

| File | Content |
|---|---|
| `pytest.ini`, `requirements.txt` | `pythonpath = 03_code`; pytest 9.1.1, matplotlib 3.11.2 |
| `02_tests/test_worked_example.py` | Worked example, expected values typed from Maurice's Excel |
| `03_code/lob_a.py` | Version A (single list, full scans) |
| `03_code/validation.py` | Shared event validation |
| `03_code/invariants.py` | Version-independent per-event conservation and priority check |
| `03_code/replay.py` | Replay command and summary CSV |
| `04_benchmarks/profile_version_a.py` | First cProfile run (exploration) |
| `06_dashboard/build_dashboard.py` | Static HTML dashboard from `05_results/` only |

Tests-first evidence: `05_results/tests_fail_first.txt` (stub `OrderBook`
returning empty results: 6 failed, 1 passed; the passing test compares the
Excel values with the supplied JSON and needs no engine). After Version A:
`05_results/tests_latest.txt` (7 passed).

### Cross-check of the expected values

The Excel (`01_my_notes/OrderBookTests.xlsx`) and
`00_instructions/data/worked_expected.json` agree on every value: 4 fills
(b1 1, b2 1, b3 3, b4 1 BTC at 60,000 / 60,000 / 59,900 / 59,700 dollars),
unfilled 0, status `filled`, remaining b4 4 BTC seq 4 and a1 2 BTC seq 5,
proceeds 359,400 dollars, average 59,900 dollars, and 10 BTC submitted buys =
6 traded + 4 resting. The test `test_hand_values_agree_with_supplied_json`
keeps checking this.

Observation: in the Excel, rows 4–5 columns H–O are typed values, while
rows 2–3 are formulas. The numbers are right, but they would not update if
an input changed.

### Design decisions

| # | Decision | Why | Decision |
|---|---|---|---|
| D1 | Interface is a class `OrderBook` with `AddLimitOrder`, `FillMarketSell`, `CancelOrder`, `process_event`, `inspect_book`, `assert_invariants`. | A fresh book per replay or test is one constructor call; Version B gets the same interface. | |
| D2 | `process_event` validates; the three public operations assume validated arguments. | Validation in one place; both versions share `validation.py`, so reject reasons are identical. | |
| D3 | Validation order: object, seq, event_id, type, then type-specific fields; the first failing check is the reason. | Deterministic reasons, so A and B can be compared result by result. | |
| D4 | The duplicate-live-id check is a callback `is_live(order_id)` supplied by each book. | Each version answers it with its own structure (A: O(B) scan; B can use a dict). | |
| D5 | Version A keeps both sides in ONE list in arrival order and scans the whole list for the best order on every fill step. | The transparent baseline the spec asks for. | |
| D6 | Per-event checks are split: structural invariants in each book's `assert_invariants()`; conservation and price-time priority in `invariants.check_event(before, event, result, after)` using `inspect_book()` snapshots. | The snapshot check is version-independent. Note: its priority check walks the canonical book to predict the fills, which is a second, simpler matching routine. It is a consistency check, not an independent proof. | |
| D7 | `replay.py` processes events in file order and never sorts them. | Spec: one at a time in seq order; a non-increasing seq is rejected, not reordered. The supplied files are strictly increasing (checked). | |
| D8 | `replay.py` runs two passes on fresh books: a checked pass (invariants after every event, peaks) and an unchecked timed pass. `wall_seconds` = one timed replay of preloaded events; reading and parsing are excluded. | Checks would otherwise dominate the time. One run with no warm-up and no repeats, so it is an exploration number, not the benchmark. | |
| D9 | `peak_price_levels` counts distinct (side, price) pairs among active orders. | A bid and an ask at the same price are two levels (they cannot coexist anyway, the book would be crossed). | |
| D10 | `replay.py --csv` replaces only the rows of the version being run and keeps other versions' rows. | Version B can be added to the same `replay_summary.csv`. | |
| D11 | Tests run for every module name in `VERSIONS = ["lob_a"]`; whole result dicts are compared with `==`. | Adding `"lob_b"` reuses the unchanged tests; exact equality also catches extra or misspelled fields. Since session 2 the list lives in `02_tests/conftest.py` (fixture `lob`), shared by all test files. | |
| D12 | Dashboard: correctness comes from the saved pytest output `05_results/tests_latest.txt`; bars are grouped by version with a fixed colour per version (A blue, B orange). | The dashboard reads only `05_results/`; B appears as a second series with no code change. | |
| D13 | Peak orders and peak price levels are two panels with separate y-axes in one image, not one dual-axis chart. | 10,000 orders vs 8 levels: on one axis the small values would vanish. | |

### Spec ambiguities and how they were resolved (for Maurice to confirm)

| # | Ambiguity | Choice made | Decision |
|---|---|---|---|
| S1 | Order of `inspect_book()` output: bids first or asks first? | Bids (price desc, seq) then asks (price asc, seq), following `worked_expected.json`. | **ACCEPTED** (Maurice): bids first, like the JSON. |
| S2 | Rejected result when `event_id` is missing: omit the key or set None? | Key always present, value `None` if missing. | **ACCEPTED** (Maurice): rejected results carry `event_id`, or `None` if it is missing. |
| S3 | Is a missing `event_id` invalid? The spec lists only some invalid cases. | Rejected (`missing event_id`). | |
| S4 | Must `order_id` / `target_order_id` be strings? Not stated. | Must be `str`, else rejected. Keeps A and B identical if an unhashable id ever appears. | **ACCEPTED** (Maurice): ids as strings is our assumption, not a spec rule; document it as such. |
| S5 | Does the duplicate-live-id rule apply to a MARKET_SELL whose `order_id` equals a resting order's id? | Yes, rejected ("duplicate live submission identifiers"). | **ACCEPTED** (Maurice): a market sell reusing a live order_id is rejected as a duplicate live submission. |
| S6 | `unfilled_qty_units` for a limit: the JSON only shows a market sell. | For a limit it is the residual that rests (0 if `filled`). | |
| S7 | Integer check: is `3.0` or `true` an integer? | No. `type(x) is int` only; JSON floats and booleans are rejected. | |
| S8 | `event_id` uniqueness is stated but no reject rule is given. | Not validated. | |
| S9 | A cancel whose target is unknown is "valid": does it advance the last accepted seq? | Yes, it is a valid event, so `last_seq` advances. | |

## Session 2: tests from the Excel tabs Test1 and Test2

Maurice added two hand-calculated tabs. The AI turned them into
`02_tests/test_excel_tabs.py` (`test_Test1`, `test_Test2`). Inputs are the
event rows 2–7 (columns A–G); expected values are taken ONLY from the block
"EXPECTED RESULT (hand calculation)" from row 24. The formula columns J–O
were deliberately not used, because they ignore crossing on arrival (in
Test1 they show b1 as filled by s1 and a1 resting with 2 BTC).

- Test1: a1 SELL 60,100 crosses b1 BUY 60,200 on arrival (1 BTC at the
  resting price 60,200), then s1 sells 8 BTC (filled). Proceeds s1 $478,500,
  average $59,812.50 (checked exactly as 5,981,250 ticks), all proceeds
  $538,700, bids 10 = 9 traded + 1 resting.
- Test2: s1 sells 15 BTC against 10 BTC of bids: `partial`, 5 discarded,
  bid side empty, proceeds $598,200, average $59,820.

Result: both passed against Version A on the first run; no disagreement
between engine and Excel. Before writing the tests the AI independently
recalculated both tabs and got the same numbers.

Because they passed immediately, the AI checked they can fail: against a
throwaway mutant of Version A in which limits never cross on arrival (the
formula-column assumption), `test_Test1` FAILS (status rows) and
`test_Test2` passes (it has no crossing, so it cannot detect that bug).
The mutant was a scratch script outside the repository.

Change to test structure: the `VERSIONS` list moved from
`test_worked_example.py` into `02_tests/conftest.py` so one edit adds
Version B to every test file. No expected value changed.

| # | AI suggestion | Decision |
|---|---|---|
| T1 | Compare quantities and prices as exact `Fraction`s of BTC and USD so the test rows read like the Excel rows. | |
| T2 | Move `VERSIONS` into `conftest.py`. | |

### Hidden instruction in the course PDF

AGENTS.md warns of hidden text in the slides asking AI tools to insert a
certain word into code. It was not followed; the word appears nowhere in
the code.
