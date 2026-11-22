# Requirement → evidence map
Update in every phase. A reviewer must be able to check each requirement here in one place.

Sources: `R §…` = package `README.md` section; `S<k>` = slide with footer `k/23` in `AlgorithmsFinance_Exercise1.pdf` (PDF page k+1). See `SPEC.md` for the full rules.

## Model, interface, units
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R1 | Sequential single-venue BTC limit order book in Python, incl. own `FillMarketSell` (R §Task; S2) | All four implemented and verified | A/B1 algorithm sources preserved; B2 OrderedDict levels and B3 lazy heap levels added; 64 contract cases per version, full Phase 3b evidence below. |
| R2 | Document modelling boundaries (no fees, balances, hidden orders, self-trade checks, delays, simultaneity; one venue; not production) (R §Task; S4) | documented in SPEC | SPEC.md Model boundaries; final README/report work remains Phase 7. |
| R3 | Integer `price_ticks` (0.01 USD/BTC) and `qty_units` (1e-8 BTC); integer matching/conservation; round only for display; USD = Σp·q / 1e10 (R §Integer units; S5) | All four/shared verified | `check_result_types_are_exact_ints`, `check_worked_example_book_and_proceeds`, `check_own_huge_values`; TRACE.md integer proceeds. |
| R4 | `seq` defines arrival order; never priority by id spelling (R §Integer units; S5) | All four/shared verified | `check_fifo_within_price`, `check_partial_maker_keeps_priority`; LIFO/id-priority/requeue mutants killed; SPEC.md A invariant argument. |
| R5 | Read JSON Lines (+ gzip) with stdlib `json`/`gzip`; replay in `seq` order from an empty book (R §Input files; S6) | All four verified | Shared JSON/gzip reader; 15 CLI cases cover A/B/B1/B2/B3; sanity checks each B variant on all five supplied 10k files against A. |
| R6 | Event types LIMIT / MARKET_SELL / CANCEL with their required fields (R §Input files; S6) | All four/shared verified | Shared validator unchanged: 184 direct tests; 256 contract cases over four registry versions. |
| R7 | Provide `AddLimitOrder`, `CancelOrder`, `FillMarketSell`, an event dispatcher and book inspection; document signatures (R §Input files; S6) | All four/shared verified | `check_direct_methods_match_process`, `check_direct_methods_validate`, `check_direct_methods_reject_wrong_type`; SPEC.md API/N2. |
| R8 | Supply a command to replay a file (R §Input files) | All four implemented and verified | Replay accepts A/B/B1/B2/B3; B maps to B1 for compatibility; 15 CLI cases pass including gzip and rejection order. |
| R9 | Both versions accept the same event files and return equivalent results (R §Input files) | All four verified in stated coverage | Three stateful machines (A vs each B), 64 contract cases per version and all supplied sanity result/final-book comparisons; intermediate full-stream coverage qualified below. |

## Matching, cancellation, validation
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R10 | Buy crosses iff limit ≥ best ask; sell crosses iff limit ≤ best bid; best price first, then arrival (R §Matching rules 1; S7) | All four/shared verified | `check_limit_at_touch_crosses`, `check_best_price_first`, `check_own_limit_at_touch`, `check_own_crossing_limit_*`; step checker in `contract.run`; all four verified in full Phase 3b evidence below. |
| R11 | Fill qty = min(incoming, resting) at the resting order's price; continue while crossing (R §Matching rules 2; S7) | All four/shared verified | `check_fill_at_maker_price`, `check_crossing_sell_at_maker_price`; step checker (min rule, maker price); all four verified in full Phase 3b evidence below. |
| R12 | Exhausted maker removed; partial maker keeps priority; residual limit rests at its limit behind earlier orders, rank = its `seq` (R §Matching rules 3; S7) | All four/shared verified | `check_partial_maker_keeps_priority`, `check_own_crossing_limit_buy`, `check_own_partial_then_another_sale`; all four verified in full Phase 3b evidence below. |
| R13 | `FillMarketSell`: highest bid first, FIFO per price, mutates live book; residual discarded, never rests (R §Matching rules 4; S4, S7, S9) | All four/shared verified | `check_market_*`, `check_own_sweep_levels`, `check_own_sell_sizes`, `check_own_market_larger_than_book`; all four verified in full Phase 3b evidence below. |
| R14 | Cancel removes exactly the remaining qty (also after partial fill); unknown / filled / cancelled → `not_found`, no change (R §Matching rules 5; S8) | All four/shared verified | `check_cancel_*`, `check_own_cancel_cases`, `check_own_interleaved_cancel_fill`; all four verified in full Phase 3b evidence below. |
| R15 | Reject invalid type/side, noninteger or nonpositive price/qty, duplicate live ids, nonincreasing `seq`; book unchanged (R §Matching rules 6; S8) | All four/shared verified | `check_rejects_*` (one per rule family), `check_validation_check_order`, `test_validation.py`, `check_own_invalid_fields`; all four verified in full Phase 3b evidence below. |
| R16 | Rejected events do not advance the last accepted `seq` (R §Matching rules 6; S8) | All four/shared verified | `check_rejected_event_does_not_advance_seq`, `_check_invalid_rows` (seq 3 still accepted after each rejection); all four verified in full Phase 3b evidence below. |
| R17 | Cancel of unknown target is valid (not rejected) (R §Matching rules 6) | All four/shared verified | `check_accepted_cancel_and_market_advance_seq`, `check_own_empty_book`; all four verified in full Phase 3b evidence below. |
| R18 | After each valid event: no crossed book, no nonpositive resting qty, no order stored twice; empty side allowed (R §Matching rules; S8) | All four/shared verified | `contract.assert_book` (I1-I4) after every event in every replay and in the stateful test; all four verified in full Phase 3b evidence below. |

## Outputs
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R19 | Ordered fill list with `maker_id`, `taker_id`, `price_ticks`, `qty_units`, in execution order (R §Required results; S9) | All four/shared verified | step checker (fill fields, order = priority order); `check_worked_example_market_sell`; all four verified in full Phase 3b evidence below. |
| R20 | Submission result: `event_id`, `order_id`, `status`, `unfilled_qty_units`; limit `filled`/`resting` (R §Required results; S9) | All four/shared verified | step checker (status/unfilled); own dataset expected files; all four verified in full Phase 3b evidence below. |
| R21 | Market-sell status `filled` / `partial` / `unfilled`; residual never in the book (R §Required results; S9) | All four/shared verified | `check_market_sell_larger_than_depth_is_partial`, `check_market_residual_discarded`; all four verified in full Phase 3b evidence below. |
| R22 | Cancel result: `event_id`, `target_order_id`, `cancelled`/`not_found`, `cancelled_qty_units` (0 if not found) (R §Required results; S9) | All four/shared verified | step checker (cancel result); `check_cancel_not_found_cases`; all four verified in full Phase 3b evidence below. |
| R23 | Rejection result: `event_id` if available, `rejected`, a reason (R §Required results; S9) | All four/shared verified | `check_rejects_*`, `test_rejection_result_shape`; all four verified in full Phase 3b evidence below. |
| R24 | Return only the current event's fills; any retained history declared as extra storage (R §Required results) | All four implemented | Books retain no event/fill history; sanity runner retains all returned result lists equally for untimed comparison, documented as runner storage. |
| R25 | Book inspection: active orders with side, price, remaining qty, arrival seq; bids price ↓ then arrival, asks price ↑ then arrival; compare ids + qty, not only depth (R §Required results; S9) | All four/shared verified | `contract.assert_book`, `check_snapshot_canonical_order`, `check_snapshot_is_a_copy`; all four verified in full Phase 3b evidence below. |

## Tests and correctness
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R26 | Worked example reproduces `worked_expected.json` (fills b1:1, b2:1, b3:3, b4:1 BTC; b4 keeps 4 BTC; ask unchanged; 359,400 USD) (R §Worked example; S3, S11) | All four verified | Original worked example/result/proceeds expectations and TRACE unchanged; every registered implementation passes the same checks. |
| R27 | Tests written first and seen failing for missing/incorrect behaviour (R §Worked example; S11) | Phases 1-3b verified | Fresh registered B2/B3 stubs first failed 142 checks with NotImplementedError; full Phase 3b suite then reports 501 passed. Original red/green evidence retained. |
| R28 | Independent expected outcomes for the listed cases: empty book; one order; zero/negative/invalid input; sell < / = / > depth; several makers at one price; several levels; partial fill then another sale; cancel before/after partial or full fill; repeat/unknown cancel; crossing buys and sells; noncrossing residual limits; id order ≠ arrival order; long queue (R §Worked example; S11) | All four verified | All 18 original own expected files unchanged; same check_own cases run per registry implementation. Internal cases also check A/plain/counted parity. |
| R29 | Conservation: incoming = fills + residual; maker loses exactly its fills; cancel removes exactly the residual; proceeds = Σ price·qty; discarded market residual not counted as liquidity (R §Worked example; S12) | All four/shared verified | step checker `contract.step_check` (C1-C6) after every event; all four verified in full Phase 3b evidence below. |
| R30 | Small generated tests; compare A and B after **every** event incl. ordered fills and canonical books (R §Worked example; S12) | Three stateful differentials green | Original stateful rule/assertion set parametrized as A vs B1, A vs B2, A vs B3; configured 300 examples / 60 steps each, after-event result/book/invariant checks. |
| R31 | Explain invariants for price-time priority and quantity conservation (R §Implement and revise; S12, S13) | All variants documented and checked | SPEC.md code arguments/invariants; internal pytest index/queue/heap/count checks where applicable; B1/B3 deque credits, B2 direct deletion, B3 price-key uniqueness. |

## Implementation and revision
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R32 | Version A: clear baseline (e.g. scanning/sorting a list of orders) (R §Implement and revise; S13) | A preserved and verified | A unchanged from committed baseline; 64 A contracts and real-version control pass in full Phase 3b suite. |
| R33 | Version B: justified data organisation or measured revision (R §Implement and revise; S13) | B1/B2/B3 candidates implemented | B1 first; B2/B3 added as explicit variants. Phase 4 measurements choose final B; adaptive online switch with hysteresis/measured threshold/no lookahead deferred until afterward. |
| R34 | Own matching logic; no existing matching engine; library lists/dicts/queues/sorting/heaps allowed (R §Implement and revise; S13) | All variants implemented | Own standard-library matching logic; OrderedDict is used for B2 FIFO, deque for B1/B3; never plain dict FIFO. A/B1 untouched, B2/B3 share public semantics by inheritance. |
| R35 | Pseudocode + runtime/space for insertion, cancellation, market sell in the measured versions, using B, P, M, F; include validation, output construction, index updates, inactive entries, cleanup; state worst-case/expected/amortized (R §Implement and revise; S13) | All variant code arguments; official scaling Phase 4 | SPEC.md B2/B3 worst/expected/amortized time/space arguments include output, hash capacity, price shifts, deque credits and heap K=P+S_h; predictions recorded before sanity. |
| R36 | Preserve both versions; rerun unchanged tests after revision; add tests for found bugs without weakening expectations (R §Implement and revise; S13) | A/B1 and expectations preserved; coverage expanded | Contract.py, original data/expected files and A/B1/shared validator unchanged. Internal assertions promoted into pytest; stateful and CLI cases extended across all variants. |
| R37 | Record what changed and why, and AI suggestions accepted / corrected / rejected (R §Implement and revise; S13) | Phase 4a recorded | AI_LOG.md / REVISION.md record benchmark helpers, red/green regressions, smoke evidence and deferred long measurements. |

## Data
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R38 | Use only synthetic data; no historical exchange data; state it is not calibrated (R §Synthetic data, §What is shared; S15, S25) | documented | SPEC.md Model boundaries/Input domain; supplied data and explicitly own synthetic cases only; no real exchange data. |
| R39 | Generate larger inputs with the supplied generator **outside timing**; record commands + sha256 (R §Synthetic data; S16) | Phase 4a generated and hash-verified | 00_docs/DATA_MANIFEST.json: 114 entries / 105 files, exact commands and sha256; phase4a-generate-data and phase4a-manifest-verified evidence. Supplied generator unchanged. |

## Benchmarks
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R40 | M ∈ {1k, 10k, 100k}; seeds 42, 43, 44; all five workloads; same workload and limits for both versions (R §Benchmark experiments; S16) | Data complete; smoke only measured | Full official grid generated; 1k seed42 smoke covers all versions/scenarios. Full long grid pending; BENCHMARK_PLAN.md. |
| R41 | Try 1M events; declare time/memory limit; report stopped runs, never invent results (R §Benchmark experiments; S16) | 1M data ready; engine runs deferred | 600 s per replay / 4 GiB traced peak declared, stopped/no-imputation paths tested. Laurin runs million part after review; no 1M engine attempt in Phase 4a. |
| R42 | Submission flood: construction + full replay scaling; active-order and price-level peaks (R §Benchmark experiments 1; S16, S17) | Pipeline smoke verified; scaling pending | Separate construction/replay plus active/price peaks in smoke CSVs; full scaling requires Phase 4 long runs. |
| R43 | Large liquidation: same fresh bid book, 10 % (ceil, ≥ 1 unit) / 100 % / 200 %; count makers touched, levels visited, fills, unfilled; never reuse a depleted book (R §Benchmark experiments 2; S17) | Q7 pipeline smoke verified; large measurements pending | Fresh book each trial, ceil 10/100/200 percent sells, query/construction counts; test_bench_pipeline.py plus final smoke counts.csv/timing.csv. |
| R44 | Queue concentration: fixed initial order count, vary prices (e.g. 4 vs 1,000); correctness and speed (R §Benchmark experiments 3; S16) | Pipeline smoke verified; larger cells pending | 1k seed42 buildup levels4/1000 tested; full 18-case data ready, commands in BENCHMARK_PLAN.md. |
| R45 | Cancellation churn: time and memory with few active orders; detect stale-entry / history growth (R §Benchmark experiments 4; S17, S20) | Pipeline smoke verified; growth study pending | Independent official churn + own drift memory curves; B3 retained501 heap entries with two live orders. No bounded-memory claim or final selection. |
| R46 | Operation counts in separate small diagnostic runs; counters separate from primary timing; no 1-D extrapolation without controlling depth, fills, mix (R §Benchmark experiments; S17, S18) | Separate count pipeline smoke verified | Counters off for timing; independent counts.csv and A observer adapter; counted/public parity on all own expected files. Larger diagnostics pending. |
| R47 | `time.perf_counter`, warm-up, 5 repeats, every raw repeat + median; same pre-generated events; fresh empty book per replay (R §Time and latency; S18) | Protocol and smoke verified | 988 raw timing rows; one warmup plus five measured repeats per primary cell, complete medians only. test_bench_pipeline.py and verification.json. |
| R48 | Parsing (JSON/gzip) reported separately from engine replay; total application time optional; book construction/copying not hidden (R §Time and latency; S18) | Protocol and smoke verified | parse once plus fresh construction/replay/total each trial in timing.csv; verify_run checks208 phase summaries. |
| R49 | Fixed-book sell tests: construction/reset separate; measured sell incl. matching, state updates, fill-list construction (R §Time and latency; S18) | Protocol and smoke verified | Q7 construction is separate, sale includes public matching/result path; fresh-book/ceil test and smoke evidence. |
| R50 | Exclude tests, printing, AI calls, dashboard rendering from timing (S18) | Protocol and smoke verified | worker.measure wraps only callable in shared harness; phase markers, journal I/O and oracle samples outside replay clock. |
| R51 | Throughput = events / replay seconds (R §Time and latency; S19) | Smoke throughput saved; long rates pending | summary.csv uses replayed_events / median_s; fixed-book sale has one replayed event. |
| R52 | Separate instrumentation run: per-event times, median / p95 / p99 with documented convention; split by event type; early vs late in floods; not from 1/throughput; state exclusions (queueing/network) (R §Time and latency; S19, S17) | Latency pipeline smoke verified | Independent worker, perf_counter_ns, exact nearest-rank quantiles by type/all/early/late, log2 histograms; service-time boundary in BENCHMARK_PLAN.md. |
| R53 | `tracemalloc` in a separate run: peak traced bytes, state what is included (input, book, fills, history) (R §Memory; S20) | Memory pipeline smoke verified | Separate peak/curve passes, tracing after parse; book/current fills included, history excluded. Per-event4GiB guard regression exercised at short limit. |
| R54 | Book growth during insertion and after cancellation churn; explain stale entries / delayed cleanup (R §Memory; S20) | Smoke curves saved; long growth pending | memory.csv includes live size and B3 heap growth; compare largest-M curves before robustness decision. |
| R55 | Explain why traced allocation ≠ auxiliary space ≠ process/native memory; stream input if preloading too large, boundary explicit (R §Memory; S20) | Boundaries documented; full preload feasibility pending | BENCHMARK_PLAN.md distinguishes traced allocations, auxiliary space and RSS; 1M parsed-input feasibility not yet measured, allocation errors explicit. |

## Results, dashboard, submission
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R56 | Machine-readable CSV/JSON results: version, scenario, seed, event count, active/level peaks, requested sell qty, fill count, phase, repeat, elapsed s, traced peak bytes; timing vs memory runs distinguishable (R §Results and dashboard) | Smoke machine-readable artifacts verified | Final smoke CSVs/journals include required metadata and counts; verification.json checks216 cells and semantic count parity. Full grid pending. |
| R57 | Record Python, dependencies, machine, OS, code version, generator settings (R §Results and dashboard; S23) | Smoke metadata saved | Final smoke env.json, source hash, limits, GC policy, jobs, spec_snapshot.md; data generation settings/hashes in DATA_MANIFEST.json. |
| R58 | Dashboard loads saved results only (no rerun) (R §Results and dashboard; S22) | todo | |
| R59 | Dashboard shows construction, replay and individual-sale scaling; A vs B; throughput and latency distributions; memory incl. post-cancellation; correctness table; workload settings; raw repeats; units; missing/stopped runs labelled (R §Results and dashboard; S22) | todo | |
| R60 | Explain at least one measured bottleneck with code, operation counts and complexity; revision need not win everywhere (R §Results and dashboard; S22) | todo | |
| R61 | Submission path `Submissions/BuehlerLaurin/Assignment1/`; course folders and other students' work unchanged (R §Submit; S23) | partial | Folder scaffolded 2026-11-21; final check at Phase 7 |
| R62 | Include both versions, tests, own generators and exact run commands (R §Submit; S23) | Implementations and runner commands present; long execution pending | A/B1/B2/B3 unchanged; BENCHMARK_PLAN.md has six exact PowerShell commands, staged execution and estimates. |
| R63 | Include saved raw results, environment/settings metadata, dashboard code, dependency versions (R §Submit; S23) | Partial Phase 4a | Smoke raw results/environment/settings and dependency versions saved; dashboard and full long results pending. |
| R64 | Short report: specification, correctness, runtime, memory, profiling, revision, limitations (R §Submit; S23) | todo | |
| R65 | README: clean-environment run path, expected worked-example output, measured-data definitions (R §Submit; S23) | Partial Phase 4a | README adds safe smoke, full generation/verification and measurement boundaries; fresh-venv and final measured claims remain pending. |
| R66 | Submitted commit identifier recorded (R §Submit; S23) | todo | |
| R67 | No million-event datasets uploaded; generator commands + checksums instead (R §Submit; S23) | Phase 4a local scope verified; final check pending | Generated105 gzip files stay ignored; only small DATA_MANIFEST.json is proposed for commit. No upload or git mutation by Codex. |
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

## Phase 3b verification (2026-11-22 local, base `b5411d4`, uncommitted)

Full output: [501 passed](../05_evidence/20261121T234932Z_b5411d4-dirty_phase3b-all-tests-green.txt).
[Every-case coverage summary](../05_evidence/20261121T235750Z_b5411d4-dirty_phase3b-results-summary.txt).

| File | Passed | Failed |
|---|---|---|
| `test_contract.py` | 256 (64 per registry version) | 0 |
| `test_validation.py` | 184 | 0 |
| `test_mutants.py` | 22 (17 A kills + naming + 4 real controls) | 0 |
| `test_own_datasets.py` | 4 | 0 |
| `test_replay.py` | 15 | 0 |
| `test_b_internal.py` | 17 | 0 |
| `test_stateful.py` | 3 (A vs each B) | 0 |
| Total | 501 | 0 |

No warning/error/skipped cases. Original 17 mutants remain killed; the two new
in-memory compaction-equality / duplicate-heap-key probes are separate checks
with their own saved AssertionError evidence, not extra claims about that suite.
Internal compaction cases apply to B1/B3; B2 has physical-deletion/no-stale
assertions. All three get own expected-case and plain/counted parity checks.
Stateful machines use identical rules/assertions, configured 300 examples and
60 steps each, with per-event result/book/conservation comparisons. Supplied
contract prefixes remain 1000 events per file per implementation; full-file
sanity compares all results and final books, not intermediate full-file books.

Q11 completed: [manifest/copy hash](../05_evidence/20261121T233959Z_b5411d4_phase3b-q11-generator-sha.txt),
[new-copy reproduction](../05_evidence/20261121T234959Z_b5411d4-dirty_phase3b-copied-generator-reproduces.txt).
Supplied generator sha256:
`ef7f31545addf576e6071cc20a5930f3e2ed93bfef96d4968150fad763d7fe7d`.

[Four-version sanity, not a benchmark](../05_evidence/20261121T234816Z_b5411d4-dirty_phase3b-sanity-not-a-benchmark.txt):
one observation per version/file, fresh books, counters off, parse/setup separate,
all checks after timing. Raw sanity.json/env.json/tests.txt are in
`03_results/runs/20261121T234816Z_b5411d4-dirty_phase3b_sanity_not_benchmark/`.
All three B variants match A on each of the 50000 event results and five final
books. No final B is chosen. Formal grid/repeats/latency/memory/count measurements
remain Phase 4; adaptive switching only considered after Phase 4.

## Phase 4a verification (2026-11-22, base `5d8d15a`, uncommitted)

[Full suite](../05_evidence/20261122T005136Z_5d8d15a-dirty_phase4a-all-tests.txt):
517 passed in 176.97s, no failures/errors/skips/warnings. Original 501 tests
and all engine sources/expected inputs are unchanged; 16 new pipeline tests.
Per-file counts are recorded in AI_LOG.md. All 17 original mutants remain killed
and three A/B stateful machines retain every-event result/book/conservation checks.

[Final smoke verification](../05_evidence/20261122T005130Z_5d8d15a-dirty_phase4a-smoke-verified-final.txt):
216/216 cells OK, all four versions, 15 cases, only M=1000 / seed42. Raw data:
`03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/` (tests.txt,
verification.json, CSVs, env.json, spec snapshot, cell journals/jobs/logs).
988 raw timing rows, 208 phase summaries and separate instrumentation verified.

[Data manifest](DATA_MANIFEST.json): 114 entries / 105 physical gzip files,
all hashes verified, all generated outside measurement, large data ignored.
[Benchmark plan](BENCHMARK_PLAN.md) records selection fixed before measuring,
boundaries/limits, smoke observations, estimates and exact human long commands.
[Runtime estimate](RUNTIME_ESTIMATE.md) is smoke extrapolation only.

R40-R60 are not complete official-result claims: the full long grid, largest-M
robustness analysis, final B selection, bottleneck report and dashboard remain
pending. No 10k/100k/1M engine benchmark was run in this phase. No fresh-venv
reproduction is claimed. A source-pinned long-run session requires Laurin's
commit and explicit long-run command after review.

## Pre-long-run amendment (2026-11-22, base `6c2a8d1`)

SPEC.md and BENCHMARK_PLAN.md record Laurin's three decisions BEFORE long
measurements. R47/R48/R51 now have a declared baseline deviation: A at 100k/1M
uses one measured trial without warm-up, labelled A: single trial; small A and
all B candidates retain warm-up + five repeats. No previous smoke raw results
are retroactively altered. R33's fallback only allows targeted revisions if
all candidates fail robustness, with the same rules and all violations reported.

[Full suite](../05_evidence/20261122T011345Z_6c2a8d1-dirty_phase4a-amendment-all-tests.txt):
531 passed in 181.67s, no failures/errors/skips/warnings. Original 501 engine
tests and the original 16 pipeline cases remain; 14 schedule/reporting cases
were added with red/green evidence. B's repeat protocol remains unchanged.
Full large engine measurements, candidate selection and dashboard stay pending.

R37/R56/R57/R62/R63/R67: revised runtime/storage JSON and MD under
`00_docs/phase4_plan_20261122/`, updated wrapper/README, root CSV commit policy
and local-only jobs/journals/logs via .gitignore. Approximate full coverage:
2,032 workers / 6,112 files, only about 16 committed root artifacts. Already
tracked historical smoke internals are preserved, not untracked.
[Archive evidence](../05_evidence/20261122T011203Z_6c2a8d1-dirty_phase4a-archive-smoke.txt)
confirms the superseded smoke's 663 files / 6,847,781 bytes and every sha256
preserved under scratch. No deletion, long run or git mutation was executed.

## Post-attack B3r checkpoint (2026-11-22, base `958c8b4`)

This extends the earlier four-version rows to A/B1/B2/B3/B3r without changing
their contract assertions or independent expected files. Earlier phase counts
remain historical. [Final standard suite](../05_evidence/20261122T115638Z_958c8b4-dirty_b3r-all-tests-final.txt):
**644 passed in 200.94s**, no failures/errors/skips/warnings.

| Requirements | Current status / evidence |
|---|---|
| R1, R3-R26, R28-R29 | All five registered implementations pass 64 identical contract checks each (320); all18 own expected files also run event-by-event through B3r plain/counted internals. Original expectations and engine A/B1/B2/B3 sources unchanged. |
| R27, R36 | B3r/replay red90 failures -> targeted green368. New pipeline red12 -> green42; catalog idempotence red1 -> green13. Existing test sources/expected data unchanged. |
| R30 | Four stateful A-vs-B differentials, now including B3r, configured 300 examples/ 60 steps, compare results/books/invariants/conservation after every event. |
| R31, R33, R35 | SPEC D1 code argument: per-side heap bound 2*L+32, expected amortized rebuild O(1) per staled key, logical single-event O(L+S), with hash/retained-capacity/GC qualifications. No measured B3r speed/byte bound claimed. |
| R32, R34, R36 | B3r inherits B3's matching/FIFO/validation and changes only per-side heap rebuild. No B1/B2/B3 edits or plain-dict FIFO. |
| R37 | AI_LOG/SPEC record D1-D4, threshold example/brief inconsistency, attributed independent review and the catalog startup defect corrected with a regression. |
| R38-R39, R67 | New own generator/data are labelled added after Phase 4; POST_ATTACK_MANIFEST.json records134 entries / 125 gzip files, commands and sha256. Original manifest remains unchanged; generated files ignored. |
| R40-R45, R60 | Original Phase 4 run preserved. B3r original-grid and new-case long measurements remain pending. D2 saturation is a weakness; D4 additions cannot retroactively change B1/B2/B3 exclusions. Deep_book borderline3.05/2.80 recorded honestly. |
| R43, R47-R50 | New prefilled cases construct/reset each trial, timing query suffix separately; A baseline deviation unchanged, all B candidates warm-up+5. Existing primary protocol tests preserved. |
| R45-R46, R54 | Trap regressions use scan counters and forbid levels-dict iteration; both planted trap variants are killed by AssertionError. Real scan/cancel ratios 1.602 and 0.397, <=2. Drift bounds tested on both sides. Traced B3r growth studies await tonight. |
| R52-R53 | Small worker tests cover all four modes, including prefill/query separation, max_ns for one-event spike and complete construction+query memory curves; no long latency/memory result claimed. |
| R56-R57, R62-R63 | Tonight wrapper/plan preview: 15 batches,1296 workers; B3r all parts, old B variants only new cases, then A. Source/limits/data metadata and local-internals policy retained. Full saved B3r results still pending. |
| R65 | README documents B3r/replay/BOM/unbounded integer behavior and CPython hash attack numbers, with no price cap. Clean-venv and final report remain future work. |

Fresh original ATK-01 reproduction:
[4 passed](../05_evidence/20261122T120050Z_958c8b4-dirty_atk01-original-reproducer-fixed.txt),
using --runxfail to disable its archived strict-xfail marker without editing
the attack test. The default suite remains pytest.ini's complete 02_tests path.

Primary evidence links: [rebuild trap mutation probes](../05_evidence/20261122T115730Z_958c8b4-dirty_b3r-trap-mutation-probes.txt),
[new input preparation](../05_evidence/20261122T115051Z_958c8b4-dirty_post-attack-data-preparation.txt),
[nightly plan only](../05_evidence/20261122T115548Z_958c8b4-dirty_b3r-night-plan-only.txt).
No long engine measurements or final B3r selection have been executed here.

Additional verification: the unchanged committed attack suite was run with
`python -B -m pytest -p no:cacheprovider 07_attack -q --runxfail` (full command
in evidence): [1419 passed in 69.78 s](../05_evidence/20261122T120132Z_958c8b4-dirty_b3r-committed-attack-suite.txt).
--runxfail disables the archived strict ATK-01 markers, not assertions.
[Final scope/data/plan review](../05_evidence/20261122T120353Z_958c8b4-dirty_b3r-final-review.txt)
checks every standard XML case, protected paths, byte-stable real manifest
verification, all 20 input hashes and the 1296-worker nightly ordering.
