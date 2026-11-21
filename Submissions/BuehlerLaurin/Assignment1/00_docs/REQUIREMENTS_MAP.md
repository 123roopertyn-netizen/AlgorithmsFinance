# Requirement → evidence map
Update in every phase. A reviewer must be able to check each requirement here in one place.

Sources: `R §…` = package `README.md` section; `S<k>` = slide with footer `k/23` in `AlgorithmsFinance_Exercise1.pdf` (PDF page k+1). See `SPEC.md` for the full rules.

## Model, interface, units
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R1 | Sequential single-venue BTC limit order book in Python, incl. own `FillMarketSell` (R §Task; S2) | todo | |
| R2 | Document modelling boundaries (no fees, balances, hidden orders, self-trade checks, delays, simultaneity; one venue; not production) (R §Task; S4) | todo | |
| R3 | Integer `price_ticks` (0.01 USD/BTC) and `qty_units` (1e-8 BTC); integer matching/conservation; round only for display; USD = Σp·q / 1e10 (R §Integer units; S5) | todo | |
| R4 | `seq` defines arrival order; never priority by id spelling (R §Integer units; S5) | todo | |
| R5 | Read JSON Lines (+ gzip) with stdlib `json`/`gzip`; replay in `seq` order from an empty book (R §Input files; S6) | todo | |
| R6 | Event types LIMIT / MARKET_SELL / CANCEL with their required fields (R §Input files; S6) | todo | |
| R7 | Provide `AddLimitOrder`, `CancelOrder`, `FillMarketSell`, an event dispatcher and book inspection; document signatures (R §Input files; S6) | todo | |
| R8 | Supply a command to replay a file (R §Input files) | todo | |
| R9 | Both versions accept the same event files and return equivalent results (R §Input files) | todo | |

## Matching, cancellation, validation
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R10 | Buy crosses iff limit ≥ best ask; sell crosses iff limit ≤ best bid; best price first, then arrival (R §Matching rules 1; S7) | todo | |
| R11 | Fill qty = min(incoming, resting) at the resting order's price; continue while crossing (R §Matching rules 2; S7) | todo | |
| R12 | Exhausted maker removed; partial maker keeps priority; residual limit rests at its limit behind earlier orders, rank = its `seq` (R §Matching rules 3; S7) | todo | |
| R13 | `FillMarketSell`: highest bid first, FIFO per price, mutates live book; residual discarded, never rests (R §Matching rules 4; S4, S7, S9) | todo | |
| R14 | Cancel removes exactly the remaining qty (also after partial fill); unknown / filled / cancelled → `not_found`, no change (R §Matching rules 5; S8) | todo | |
| R15 | Reject invalid type/side, noninteger or nonpositive price/qty, duplicate live ids, nonincreasing `seq`; book unchanged (R §Matching rules 6; S8) | todo | |
| R16 | Rejected events do not advance the last accepted `seq` (R §Matching rules 6; S8) | todo | |
| R17 | Cancel of unknown target is valid (not rejected) (R §Matching rules 6) | todo | |
| R18 | After each valid event: no crossed book, no nonpositive resting qty, no order stored twice; empty side allowed (R §Matching rules; S8) | todo | |

## Outputs
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R19 | Ordered fill list with `maker_id`, `taker_id`, `price_ticks`, `qty_units`, in execution order (R §Required results; S9) | todo | |
| R20 | Submission result: `event_id`, `order_id`, `status`, `unfilled_qty_units`; limit `filled`/`resting` (R §Required results; S9) | todo | |
| R21 | Market-sell status `filled` / `partial` / `unfilled`; residual never in the book (R §Required results; S9) | todo | |
| R22 | Cancel result: `event_id`, `target_order_id`, `cancelled`/`not_found`, `cancelled_qty_units` (0 if not found) (R §Required results; S9) | todo | |
| R23 | Rejection result: `event_id` if available, `rejected`, a reason (R §Required results; S9) | todo | |
| R24 | Return only the current event's fills; any retained history declared as extra storage (R §Required results) | todo | |
| R25 | Book inspection: active orders with side, price, remaining qty, arrival seq; bids price ↓ then arrival, asks price ↑ then arrival; compare ids + qty, not only depth (R §Required results; S9) | todo | |

## Tests and correctness
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R26 | Worked example reproduces `worked_expected.json` (fills b1:1, b2:1, b3:3, b4:1 BTC; b4 keeps 4 BTC; ask unchanged; 359,400 USD) (R §Worked example; S3, S11) | todo | |
| R27 | Tests written first and seen failing for missing/incorrect behaviour (R §Worked example; S11) | todo | |
| R28 | Independent expected outcomes for the listed cases: empty book; one order; zero/negative/invalid input; sell < / = / > depth; several makers at one price; several levels; partial fill then another sale; cancel before/after partial or full fill; repeat/unknown cancel; crossing buys and sells; noncrossing residual limits; id order ≠ arrival order; long queue (R §Worked example; S11) | todo | |
| R29 | Conservation: incoming = fills + residual; maker loses exactly its fills; cancel removes exactly the residual; proceeds = Σ price·qty; discarded market residual not counted as liquidity (R §Worked example; S12) | todo | |
| R30 | Small generated tests; compare A and B after **every** event incl. ordered fills and canonical books (R §Worked example; S12) | todo | |
| R31 | Explain invariants for price-time priority and quantity conservation (R §Implement and revise; S12, S13) | todo | |

## Implementation and revision
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R32 | Version A: clear baseline (e.g. scanning/sorting a list of orders) (R §Implement and revise; S13) | todo | |
| R33 | Version B: justified data organisation or measured revision (R §Implement and revise; S13) | todo | |
| R34 | Own matching logic; no existing matching engine; library lists/dicts/queues/sorting/heaps allowed (R §Implement and revise; S13) | todo | |
| R35 | Pseudocode + runtime/space for insertion, cancellation, market sell in the measured versions, using B, P, M, F; include validation, output construction, index updates, inactive entries, cleanup; state worst-case/expected/amortized (R §Implement and revise; S13) | todo | |
| R36 | Preserve both versions; rerun unchanged tests after revision; add tests for found bugs without weakening expectations (R §Implement and revise; S13) | todo | |
| R37 | Record what changed and why, and AI suggestions accepted / corrected / rejected (R §Implement and revise; S13) | todo | |

## Data
| ID | Requirement (short, with source) | Status | Evidence |
|---|---|---|---|
| R38 | Use only synthetic data; no historical exchange data; state it is not calibrated (R §Synthetic data, §What is shared; S15, S25) | todo | |
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
| R46 | Operation counts in separate small diagnostic runs; counters separate from primary timing; no 1-D extrapolation without controlling depth, fills, mix (R §Benchmark experiments; S17, S18) | todo | |
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
| R62 | Include both versions, tests, own generators and exact run commands (R §Submit; S23) | todo | |
| R63 | Include saved raw results, environment/settings metadata, dashboard code, dependency versions (R §Submit; S23) | todo | |
| R64 | Short report: specification, correctness, runtime, memory, profiling, revision, limitations (R §Submit; S23) | todo | |
| R65 | README: clean-environment run path, expected worked-example output, measured-data definitions (R §Submit; S23) | todo | |
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
