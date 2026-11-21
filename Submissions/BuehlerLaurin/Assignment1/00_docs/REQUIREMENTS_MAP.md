# Requirement → evidence map
Update in every phase. A reviewer must be able to check each requirement here in one place.

Sources: `R §…` = package `README.md` section; `S<k>` = slide with footer `k/23` in `AlgorithmsFinance_Exercise1.pdf` (PDF page k+1). See `SPEC.md` for the full rules.

## Model, interface, units
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R1 | Sequential single-venue BTC limit order book in Python, incl. own `FillMarketSell` (R §Task; S2) | A/B implemented and verified | `book_a.py` unchanged; `book_b.py` B1 id index / slot records / deques / signed sorted prices; full Phase 3 suite green. |
| R2 | Document modelling boundaries (no fees, balances, hidden orders, self-trade checks, delays, simultaneity; one venue; not production) (R §Task; S4) | documented in SPEC | SPEC.md Model boundaries; final README/report work remains Phase 7. |
| R3 | Integer `price_ticks` (0.01 USD/BTC) and `qty_units` (1e-8 BTC); integer matching/conservation; round only for display; USD = Σp·q / 1e10 (R §Integer units; S5) | A/B/shared verified | `check_result_types_are_exact_ints`, `check_worked_example_book_and_proceeds`, `check_own_huge_values`; TRACE.md integer proceeds. |
| R4 | `seq` defines arrival order; never priority by id spelling (R §Integer units; S5) | A/B/shared verified | `check_fifo_within_price`, `check_partial_maker_keeps_priority`; LIFO/id-priority/requeue mutants killed; SPEC.md A invariant argument. |
| R5 | Read JSON Lines (+ gzip) with stdlib `json`/`gzip`; replay in `seq` order from an empty book (R §Input files; S6) | A/B verified | `lob/replay.py` unchanged stdlib JSON/gzip reader; both engines replay all five supplied 10k files in the sanity run with 0 result differences and equal final books. |
| R6 | Event types LIMIT / MARKET_SELL / CANCEL with their required fields (R §Input files; S6) | A/B/shared verified | Shared `validation.py` unchanged; 184 direct validation tests and 128 A/B contract cases pass. |
| R7 | Provide `AddLimitOrder`, `CancelOrder`, `FillMarketSell`, an event dispatcher and book inspection; document signatures (R §Input files; S6) | A/B/shared verified | `check_direct_methods_match_process`, `check_direct_methods_validate`, `check_direct_methods_reject_wrong_type`; SPEC.md API/N2. |
| R8 | Supply a command to replay a file (R §Input files) | A/B implemented | Replay command accepts --version A or --version B; unchanged launcher/reader, both versions registered; saved Phase 3 B worked-example replay. |
| R9 | Both versions accept the same event files and return equivalent results (R §Input files) | A/B verified in stated coverage | Stateful differential checks results/books after every generated event; full five-file sanity compares all 50000 results and five final books. Exact intermediate-book coverage documented below. |

## Matching, cancellation, validation
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R10 | Buy crosses iff limit ≥ best ask; sell crosses iff limit ≤ best bid; best price first, then arrival (R §Matching rules 1; S7) | A/B/shared verified | `check_limit_at_touch_crosses`, `check_best_price_first`, `check_own_limit_at_touch`, `check_own_crossing_limit_*`; step checker in `contract.run`; both versions verified in full Phase 3 evidence below. |
| R11 | Fill qty = min(incoming, resting) at the resting order's price; continue while crossing (R §Matching rules 2; S7) | A/B/shared verified | `check_fill_at_maker_price`, `check_crossing_sell_at_maker_price`; step checker (min rule, maker price); both versions verified in full Phase 3 evidence below. |
| R12 | Exhausted maker removed; partial maker keeps priority; residual limit rests at its limit behind earlier orders, rank = its `seq` (R §Matching rules 3; S7) | A/B/shared verified | `check_partial_maker_keeps_priority`, `check_own_crossing_limit_buy`, `check_own_partial_then_another_sale`; both versions verified in full Phase 3 evidence below. |
| R13 | `FillMarketSell`: highest bid first, FIFO per price, mutates live book; residual discarded, never rests (R §Matching rules 4; S4, S7, S9) | A/B/shared verified | `check_market_*`, `check_own_sweep_levels`, `check_own_sell_sizes`, `check_own_market_larger_than_book`; both versions verified in full Phase 3 evidence below. |
| R14 | Cancel removes exactly the remaining qty (also after partial fill); unknown / filled / cancelled → `not_found`, no change (R §Matching rules 5; S8) | A/B/shared verified | `check_cancel_*`, `check_own_cancel_cases`, `check_own_interleaved_cancel_fill`; both versions verified in full Phase 3 evidence below. |
| R15 | Reject invalid type/side, noninteger or nonpositive price/qty, duplicate live ids, nonincreasing `seq`; book unchanged (R §Matching rules 6; S8) | A/B/shared verified | `check_rejects_*` (one per rule family), `check_validation_check_order`, `test_validation.py`, `check_own_invalid_fields`; both versions verified in full Phase 3 evidence below. |
| R16 | Rejected events do not advance the last accepted `seq` (R §Matching rules 6; S8) | A/B/shared verified | `check_rejected_event_does_not_advance_seq`, `_check_invalid_rows` (seq 3 still accepted after each rejection); both versions verified in full Phase 3 evidence below. |
| R17 | Cancel of unknown target is valid (not rejected) (R §Matching rules 6) | A/B/shared verified | `check_accepted_cancel_and_market_advance_seq`, `check_own_empty_book`; both versions verified in full Phase 3 evidence below. |
| R18 | After each valid event: no crossed book, no nonpositive resting qty, no order stored twice; empty side allowed (R §Matching rules; S8) | A/B/shared verified | `contract.assert_book` (I1-I4) after every event in every replay and in the stateful test; both versions verified in full Phase 3 evidence below. |

## Outputs
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R19 | Ordered fill list with `maker_id`, `taker_id`, `price_ticks`, `qty_units`, in execution order (R §Required results; S9) | A/B/shared verified | step checker (fill fields, order = priority order); `check_worked_example_market_sell`; both versions verified in full Phase 3 evidence below. |
| R20 | Submission result: `event_id`, `order_id`, `status`, `unfilled_qty_units`; limit `filled`/`resting` (R §Required results; S9) | A/B/shared verified | step checker (status/unfilled); own dataset expected files; both versions verified in full Phase 3 evidence below. |
| R21 | Market-sell status `filled` / `partial` / `unfilled`; residual never in the book (R §Required results; S9) | A/B/shared verified | `check_market_sell_larger_than_depth_is_partial`, `check_market_residual_discarded`; both versions verified in full Phase 3 evidence below. |
| R22 | Cancel result: `event_id`, `target_order_id`, `cancelled`/`not_found`, `cancelled_qty_units` (0 if not found) (R §Required results; S9) | A/B/shared verified | step checker (cancel result); `check_cancel_not_found_cases`; both versions verified in full Phase 3 evidence below. |
| R23 | Rejection result: `event_id` if available, `rejected`, a reason (R §Required results; S9) | A/B/shared verified | `check_rejects_*`, `test_rejection_result_shape`; both versions verified in full Phase 3 evidence below. |
| R24 | Return only the current event's fills; any retained history declared as extra storage (R §Required results) | A/B implemented | Neither engine retains trade history; each call returns its own fills. Sanity runner retains result lists for untimed comparison, explicitly outside engine storage. |
| R25 | Book inspection: active orders with side, price, remaining qty, arrival seq; bids price ↓ then arrival, asks price ↑ then arrival; compare ids + qty, not only depth (R §Required results; S9) | A/B/shared verified | `contract.assert_book`, `check_snapshot_canonical_order`, `check_snapshot_is_a_copy`; both versions verified in full Phase 3 evidence below. |

## Tests and correctness
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R26 | Worked example reproduces `worked_expected.json` (fills b1:1, b2:1, b3:3, b4:1 BTC; b4 keeps 4 BTC; ask unchanged; 359,400 USD) (R §Worked example; S3, S11) | A/B verified | Both versions pass `check_worked_example_market_sell` and `check_worked_example_book_and_proceeds`; Phase 2 hand trace unchanged. |
| R27 | Tests written first and seen failing for missing/incorrect behaviour (R §Worked example; S11) | Phases 1-3 verified | Historical Phase 1/2 red evidence retained; Phase 3 red: `20261121T224224Z_efee8d4-dirty_phase3-tests-red.txt` (65 failed against stub); green: `20261121T224926Z_efee8d4-dirty_phase3-all-tests-green.txt` (340 passed). |
| R28 | Independent expected outcomes for the listed cases: empty book; one order; zero/negative/invalid input; sell < / = / > depth; several makers at one price; several levels; partial fill then another sale; cancel before/after partial or full fill; repeat/unknown cancel; crossing buys and sells; noncrossing residual limits; id order ≠ arrival order; long queue (R §Worked example; S11) | A/B verified | All 18 original own expected files unchanged; both versions pass all check_own cases. Standalone diagnostic also checks plain/counted B against A and those expectations. |
| R29 | Conservation: incoming = fills + residual; maker loses exactly its fills; cancel removes exactly the residual; proceeds = Σ price·qty; discarded market residual not counted as liquidity (R §Worked example; S12) | A/B/shared verified | step checker `contract.step_check` (C1-C6) after every event; both versions verified in full Phase 3 evidence below. |
| R30 | Small generated tests; compare A and B after **every** event incl. ordered fills and canonical books (R §Worked example; S12) | A/B stateful green | Unchanged `02_tests/test_stateful.py`: after-every-event result/book comparison, invariants and conservation; configured 300 examples, 60 stateful steps; full Phase 3 run passes. |
| R31 | Explain invariants for price-time priority and quantity conservation (R §Implement and revise; S12, S13) | A/B arguments and checks documented | SPEC.md A/B invariant arguments and compaction proof; TRACE.md unchanged. Standalone B diagnostic checks index/deque bijection, live/stale totals, price lists and no empty levels. |

## Implementation and revision
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R32 | Version A: clear baseline (e.g. scanning/sorting a list of orders) (R §Implement and revise; S13) | A preserved and verified | `book_a.py` unchanged from `efee8d4`; 64 A contract cases and A control pass in the full Phase 3 suite. |
| R33 | Version B: justified data organisation or measured revision (R §Implement and revise; S13) | B1 implemented and verified | Laurin selected B1: `book_b.py`; slot records, id index, per-price FIFO deques, signed sorted prices, lazy cancellation and compaction; SPEC.md code argument and prediction. |
| R34 | Own matching logic; no existing matching engine; library lists/dicts/queues/sorting/heaps allowed (R §Implement and revise; S13) | A/B implemented | Own standard-library matching logic in `book_a.py` and `book_b.py`; no matching library or plain-dict FIFO. |
| R35 | Pseudocode + runtime/space for insertion, cancellation, market sell in the measured versions, using B, P, M, F; include validation, output construction, index updates, inactive entries, cleanup; state worst-case/expected/amortized (R §Implement and revise; S13) | A/B code arguments documented; official scaling Phase 4 | SPEC.md A/B pseudocode and per-operation worst/expected/amortized bounds incl. hashing/retained capacity, output, price movement and compaction credits; one-shot sanity is not a scaling benchmark. |
| R36 | Preserve both versions; rerun unchanged tests after revision; add tests for found bugs without weakening expectations (R §Implement and revise; S13) | A preserved; all existing tests unchanged and green | Entire `02_tests/`, original expected data and generators unchanged. B added beside A; 340 passed including the A/B stateful test and both real-version controls. |
| R37 | Record what changed and why, and AI suggestions accepted / corrected / rejected (R §Implement and revise; S13) | Phase 3 recorded | AI_LOG.md and REVISION.md: authorized B1 revision, counter flag, red/green evidence, attributed independent A review, sanity observations and limitations; pending Claude (chat) / Laurin review. |

## Data
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R38 | Use only synthetic data; no historical exchange data; state it is not calibrated (R §Synthetic data, §What is shared; S15, S25) | documented | SPEC.md Model boundaries/Input domain; supplied data and explicitly own synthetic cases only; no real exchange data. |
| R39 | Generate larger inputs with the supplied generator **outside timing**; record commands + sha256 (R §Synthetic data; S16) | partial | Supplied package verified: `05_evidence/20261121T111536Z_bc2576f-dirty_manifest-package.txt`; sample copies: `05_evidence/20261121T111537Z_bc2576f-dirty_manifest-supplied-copies.txt`, `05_evidence/20261121T111636Z_bc2576f-dirty_worked-files-sha.txt`; generator reproduces seed 42/10k: `05_evidence/20261121T111558Z_bc2576f-dirty_generator-reproduces-seed42-10k.txt` |

## Benchmarks
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R40 | M ∈ {1k, 10k, 100k}; seeds 42, 43, 44; all five workloads; same workload and limits for both versions (R §Benchmark experiments; S16) | todo | |
| R41 | Try 1M events; declare time/memory limit; report stopped runs, never invent results (R §Benchmark experiments; S16) | todo | |
| R42 | Submission flood: construction + full replay scaling; active-order and price-level peaks (R §Benchmark experiments 1; S16, S17) | todo | |
| R43 | Large liquidation: same fresh bid book, 10 % (ceil, ≥ 1 unit) / 100 % / 200 %; count makers touched, levels visited, fills, unfilled; never reuse a depleted book (R §Benchmark experiments 2; S17) | todo | |
| R44 | Queue concentration: fixed initial order count, vary prices (e.g. 4 vs 1,000); correctness and speed (R §Benchmark experiments 3; S16) | todo | |
| R45 | Cancellation churn: time and memory with few active orders; detect stale-entry / history growth (R §Benchmark experiments 4; S17, S20) | todo | |
| R46 | Operation counts in separate small diagnostic runs; counters separate from primary timing; no 1-D extrapolation without controlling depth, fills, mix (R §Benchmark experiments; S17, S18) | partial Phase 3; official instrumentation Phase 4 | B optional `count_operations=True` counters verified by standalone diagnostic; off during sanity timing. Official counts.csv and controlled driver sweeps remain Phase 4. |
| R47 | `time.perf_counter`, warm-up, 5 repeats, every raw repeat + median; same pre-generated events; fresh empty book per replay (R §Time and latency; S18) | todo | |
| R48 | Parsing (JSON/gzip) reported separately from engine replay; total application time optional; book construction/copying not hidden (R §Time and latency; S18) | todo | |
| R49 | Fixed-book sell tests: construction/reset separate; measured sell incl. matching, state updates, fill-list construction (R §Time and latency; S18) | todo | |
| R50 | Exclude tests, printing, AI calls, dashboard rendering from timing (S18) | todo | |
| R51 | Throughput = events / replay seconds (R §Time and latency; S19) | todo | |
| R52 | Separate instrumentation run: per-event times, median / p95 / p99 with documented convention; split by event type; early vs late in floods; not from 1/throughput; state exclusions (queueing/network) (R §Time and latency; S19, S17) | todo | |
| R53 | `tracemalloc` in a separate run: peak traced bytes, state what is included (input, book, fills, history) (R §Memory; S20) | todo | |
| R54 | Book growth during insertion and after cancellation churn; explain stale entries / delayed cleanup (R §Memory; S20) | todo | |
| R55 | Explain why traced allocation ≠ auxiliary space ≠ process/native memory; stream input if preloading too large, boundary explicit (R §Memory; S20) | todo | |

## Results, dashboard, submission
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R56 | Machine-readable CSV/JSON results: version, scenario, seed, event count, active/level peaks, requested sell qty, fill count, phase, repeat, elapsed s, traced peak bytes; timing vs memory runs distinguishable (R §Results and dashboard) | todo | |
| R57 | Record Python, dependencies, machine, OS, code version, generator settings (R §Results and dashboard; S23) | todo | |
| R58 | Dashboard loads saved results only (no rerun) (R §Results and dashboard; S22) | todo | |
| R59 | Dashboard shows construction, replay and individual-sale scaling; A vs B; throughput and latency distributions; memory incl. post-cancellation; correctness table; workload settings; raw repeats; units; missing/stopped runs labelled (R §Results and dashboard; S22) | todo | |
| R60 | Explain at least one measured bottleneck with code, operation counts and complexity; revision need not win everywhere (R §Results and dashboard; S22) | todo | |
| R61 | Submission path `Submissions/BuehlerLaurin/Assignment1/`; course folders and other students' work unchanged (R §Submit; S23) | partial | Folder scaffolded 2026-11-21; final check at Phase 7 |
| R62 | Include both versions, tests, own generators and exact run commands (R §Submit; S23) | partial; Phase 3 A/B code and commands present | Both versions, unchanged tests/generators, replay command, internal verifier and sanity runner present; official benchmark/run commands remain later phases. |
| R63 | Include saved raw results, environment/settings metadata, dashboard code, dependency versions (R §Submit; S23) | todo | |
| R64 | Short report: specification, correctness, runtime, memory, profiling, revision, limitations (R §Submit; S23) | todo | |
| R65 | README: clean-environment run path, expected worked-example output, measured-data definitions (R §Submit; S23) | partial Phase 3 | README current test/replay/verifier/sanity commands and worked output; measured-data definitions and fresh-venv verification remain later phases. |
| R66 | Submitted commit identifier recorded (R §Submit; S23) | todo | |
| R67 | No million-event datasets uploaded; generator commands + checksums instead (R §Submit; S23) | todo | |
| R68 | No credentials or proprietary data in the public submission (R §Submit) | todo | |
| R69 | Due 26 Nov 2026, 18:00:00h (R §Task, §Submit; S23) | todo | |

## Optional / not required
| ID | Item (source) | Status | Note |
|---|---|---|---|
| O1 | Docker packaging (R §Submit; S23: optional) | out of scope | unless time remains |
| O2 | Peer audit (R §Submit: not required) | todo | Laurin's choice: Codex audit with `aif-review` (Phase 6) |
| O3 | Retaining full trade history (R §Required results: optional) | out of scope | not retained; would grow with M |


## Phase 2 verification (2026-11-21, base `11d831b`, uncommitted)

All A/shared verification rows above refer to
[full test output](../05_evidence/20261121T222030Z_11d831b-dirty_phase2-all-tests.txt) and the
[complete failure classification](../05_evidence/20261121T222348Z_11d831b-dirty_phase2-results-summary-corrected-file-grouping.txt).
The run command is recorded in the evidence header; raw case results are in
`05_evidence/phase2-all-tests.xml`.

| Test file | Pass | Expected red (Phase 3) |
|---|---|---|
| `test_contract.py` | 64 A | 64 B |
| `test_validation.py` | 184 shared | 0 |
| `test_own_datasets.py` | 4 data | 0 |
| `test_replay.py` | 3 A CLI | 0 |
| `test_mutants.py` | 19 (17 mutants + 2 controls) | 1 B control |
| `test_stateful.py` | 0 | 1 A/B |
| Total | 274 | 66 |

All 17 mutants are runnable and killed by AssertionError in their named checks;
non-AssertionError failures are explicitly rejected by the mutation harness.
No unexpected red, warnings or skips. B and the stateful test remain unchanged
stubs/test source, respectively. Expected files and data generators are unchanged.
The table does not claim B correctness, A/B agreement, measured complexity,
bounded traced memory, benchmark results or fresh-environment reproducibility.
Those checks remain in their selected later phases.

## Phase 3 verification (2026-11-21, base `efee8d4`, uncommitted)

Full output: [340 passed](../05_evidence/20261121T224926Z_efee8d4-dirty_phase3-all-tests-green.txt).
[Per-file summary](../05_evidence/20261121T225246Z_efee8d4-dirty_phase3-results-summary.txt)
checks every XML case for absence of failure/error/skip.

| File | Passed | Failed |
|---|---|---|
| `test_contract.py` | 128 (64 per version) | 0 |
| `test_validation.py` | 184 | 0 |
| `test_mutants.py` | 20 (17 kills + naming + A/B controls) | 0 |
| `test_own_datasets.py` | 4 | 0 |
| `test_replay.py` | 3 | 0 |
| `test_stateful.py` | 1 | 0 |
| Total | 340 | 0 |

No warning, error or skipped cases. All 17 existing mutants remain killed;
mutation subclasses still target A as originally written, while both real-version
controls pass. No tests or expected results were modified for B.

The stateful differential compares A/B results, snapshots, invariants and
conservation after every generated event (configured max_examples=300,
stateful_step_count=60). Both versions also pass per-event step checks on the
first 1000 events of each supplied stream. The one-shot sanity checks every
result on all 50000 supplied events and all five final books; it does not
compare intermediate books over those complete 10k streams.

New standalone verifier (not a modification of `02_tests/`):
[internal/counter checks](../05_evidence/20261121T224429Z_efee8d4-dirty_phase3-internals-green.txt).
It exercises all 18 own expected files through A / B plain / B counted, checks
index/deque/price/count consistency, stale bounds, cancellation/fill compaction,
level deletion/recreation, id reuse, exact hand-counted work and counter atomicity.

Sanity, not a benchmark:
[one-shot output](../05_evidence/20261121T224807Z_efee8d4-dirty_phase3-sanity-not-a-benchmark.txt),
raw `03_results/runs/20261121T224807Z_efee8d4-dirty_phase3_sanity_not_benchmark/`
contains sanity.json, env.json and tests.txt. Formal repeated timings,
latency/memory/counter runs, official workload grid and fresh-venv checks remain
in their selected later phases. SPEC.md includes the pre-timing prediction and
allocated-dictionary-capacity limitation alongside the compaction credit bound.
