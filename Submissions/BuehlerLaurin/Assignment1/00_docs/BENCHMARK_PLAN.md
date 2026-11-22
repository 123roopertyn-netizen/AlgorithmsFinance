# Phase 4a checkpoint, 2026-11-22

Base: `5d8d15a` (Phase 3b, committed by Laurin). This checkpoint covers the
benchmark plan, generated inputs and an end-to-end smoke run only. No engine
benchmark at 10k, 100k or 1M was executed. No final B has been selected.

## Selection rule fixed before measurement

The controlling rule is in SPEC.md, recorded before this phase's measurements:

1. Exclude a B candidate that hits 600 s per replay or 4 GiB traced peak,
   exceeds 3x the best B median on an official or own adversarial scenario at
   its largest measured M, or retains memory proportional to event history
   instead of the live book. Compare identical scenario/seed inputs.
2. Among survivors, minimize the geometric mean of the 15 median replay times:
   five official scenarios at 100k, seeds 42/43/44. Within 5%, prefer B1, then
   B2, then B3. Missing/stopped cells are never imputed.
3. Report all results, including losses. Make the decision after Phase 4.

## Inputs and provenance

[DATA_MANIFEST.json](DATA_MANIFEST.json) records all 114 catalog entries,
commands, gzip and decompressed sha256, sizes, seeds, levels, own labels and
generator provenance. There are 105 distinct gzip files (113,456,936 bytes):
nine queue entries reuse official buildup inputs. All files were generated
outside measurement in 196.2 s. All 105 files were subsequently hash-verified.
Data remain under ignored `06_data/generated/phase4/`; commit the small manifest.

| Part | Data / experiments | Full planned cases |
|---|---|---:|
| official | 5 scenarios x 3 sizes (1k/10k/100k) x seeds 42/43/44, levels 1000 | 45 |
| million | 5 scenarios x 1M, seed 43, levels 1000 | 5 |
| queue | buildup, levels 4 and 1000, 3 sizes x 3 seeds | 18 |
| liquidation | own Q7 bid books, 3 sizes x 3 seeds x sells 10/100/200% | 27 |
| adversarial | own deep_book / mid_queue_cancels / repeated_full_sweeps, 3 sizes x 3 seeds | 27 |
| churn | official cancel_churn and own drift, 3 sizes x 3 seeds plus 1M seed 43; memory only | 20 |

The supplied generator is byte-preserved, sha256
`ef7f31545addf576e6071cc20a5930f3e2ed93bfef96d4968150fad763d7fe7d`.
Own adversarial M is exactly the number of events: deep_book uses 90% initial
orders / 10% sells; mid_queue_cancels uses M/2 initial orders plus M/4
cancel/replace pairs; repeated_full_sweeps uses five batches of M/5-1 orders
followed by a sell. Own Q7 M means initial resting bids. Requested sale size is
max(1, ceil(total bid quantity * percent / 100)). Each trial rebuilds the book.
Own drift pins the best bid while adding/cancelling distinct worse prices;
it holds at most two live orders. Its sequence is deterministic across seeds;
seed-labelled copies do not represent independent random drift samples.

Regenerate/verify from Assignment1 with the activated existing venv:

```powershell
python run.py bench.catalog
python run.py bench.catalog --verify
```

## Runner and measurement boundaries

`bench.run_all` defaults to smoke. Each input/version/mode gets an isolated
worker; primary timing uses fresh books for one warm-up plus five measured
replays, counters off and GC enabled identically. Inputs are pre-parsed.
Parsing is timed once separately, book construction is timed for every trial,
and replay includes public dispatch, validation, matching, mutation and result
allocation. For Q7, replay is the one sale and construction includes all bids.
Total is parse + construction + replay; verification/I/O are excluded. Throughput
is replayed events / median replay seconds (one event for a Q7 sale).

The same public replay kernel is used in timing, sample checks and diagnostics.
Every worker compares each sampled result and canonical book against A before
measurement: first 64 + last 64 events, or all inputs if at most 128. This is a
new replay of the sample; omitted middle events can make sampled cancels miss.
Q7 rebuilds both sampled books and derives the sampled sell from those bids.
The sample is a pipeline check, not full-stream independent correctness proof;
the unchanged contract/own/stateful tests remain the correctness evidence.

Parent watchdogs reset at each phase, enforcing 600 s per replay, rather than
600 s for the whole six-trial cell. The same auxiliary cap applies separately
to parsing, sample verification, construction and instrumentation. A first
over-limit trial stops all remaining trials of that cell, for any version.
Completed observations survive in journals. `stopped` retains reason/limit with
blank elapsed result/median; completed lower-size cells remain visible.
The recommended wrapper uses `--skip-after-stop`: other modes for that same
version/input are explicitly `not_run_after_timing_stop`, not measured stops.
No rule is relaxed for a B candidate; any actual candidate limit hit is exposed.

Separate workers produce latency (perf_counter_ns, nearest-rank p50/p95/p99,
event types and early/late 10% segments, log2 distribution histograms), memory
(independent peak and growth passes), and counts. Latency measures closed-loop
service time, excluding network/queueing. Tracing starts after input parsing;
it includes book construction and transient current results, no event history.
Curve sample buffers are allocated before tracing. The peak pass retains its
last result; the curve discards each result. Input objects/RSS/native allocation
are excluded: traced bytes are not process memory or an auxiliary-space proof.
The 4 GiB guard checks traced peak after every event in memory runs; timing
never enables tracing. If preloading 1M itself fails, that is recorded explicitly;
streaming would require a separately documented protocol before comparison.

A's counted adapter delegates matching/mutations to unchanged A; observer scans
are diagnostic overhead only. A's curve marks price count -1 (unobserved) to
avoid allocating a price set under tracing; its counted run records exact
active/price peaks. B levels/heaps are observed without quote cleanup. Counts
mark non-applicable fields, not misleading zero comparisons.

Each run stores raw CSVs, derived summaries, per-cell jobs/journals/logs,
env.json (Python/packages/OS/CPU/commit/source hash/GC/limits), a spec snapshot,
checks and tests.txt. Interrupted sessions resume by source+limit identity;
completed and stopped cells are not repeated, duplicate timing keys are rejected.
New long sessions require committed source and explicit `--allow-long`.

## Smoke evidence (pipeline only)

Final run:
`03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/`.
Its verification.json checks 216/216 cells OK, 15 cases, only M=1000 / seed 42,
all four versions, 988 raw timing records, 208 phase summaries, 372 latency
rows, 3132 memory rows, 1360 count rows and 216 sample checks. Semantic counts
agree across versions. No stopped/error cells. The earlier smoke is preserved
in `20261122T003530Z_5d8d15a-dirty_smoke/`; use the final run for planning.

Official replay medians in milliseconds, smoke only:

| Scenario | A | B1 | B2 | B3 |
|---|---:|---:|---:|---:|
| buildup | 65.591 | 4.916 | 4.534 | 4.899 |
| crowded | 72.157 | 4.029 | 3.761 | 3.814 |
| mixed | 15.153 | 4.404 | 4.040 | 4.971 |
| sweep | 59.851 | 6.663 | 5.013 | 5.671 |
| cancel_churn | 2.487 | 3.584 | 3.325 | 3.713 |

Own drift traced current bytes at events 200 -> 1000: A 1344 -> 1376;
B1 3416 -> 3448; B2 2552 -> 2584; B3 16056 -> 56760. All end at two live
orders; B3 retains 501 heap entries. This is the predicted stale-key risk,
requiring the full growth experiment and code argument for the robustness
decision; it is not a final selection from smoke.

## Runtime estimate and commands for Laurin

[RUNTIME_ESTIMATE.md](RUNTIME_ESTIMATE.md) and the run's runtime_estimate.json
give the derivation and sensitivity. A's growing-book work is extrapolated
quadratically; constant-live churn linearly. B is approximately linear at
bounded P; deep B1/B2 range up to quadratic. Ranges vary these assumptions by
0.5x..3x and include parsing/startup and per-phase stops. They are planning
estimates, not measured long runtimes, confidence intervals or guaranteed bounds.
Near 600 s, completing five repeats versus stopping the first trial creates a
large discontinuity. Tracing/allocator/GC/cache effects add uncertainty.

At 100k, A's unconstrained single-replay estimates are buildup 656 s, crowded
722 s, mixed 152 s, sweep 599 s, cancel_churn 0.25 s. At 1M: approximately
65,591 / 72,157 / 15,153 / 59,851 / 2.5 s. Most 1M A cells should attempt one
trial and stop at 600 s, not run for these unconstrained estimates.

After Claude review and Laurin's commit, from Assignment1, run one command per
part below. Each uses the pinned existing venv, runs B1/B2/B3 first then A,
and resumes the common `phase4` session. None was executed in Phase 4a.

| Part | Exact PowerShell command | B-only hours | Full A+B hours |
|---|---|---:|---:|
| official | `& .\01_code\bench\long_runs.ps1 -Part official -AllowLong` | 0.14-0.43 | 2.61-15.75 |
| million | `& .\01_code\bench\long_runs.ps1 -Part million -AllowLong` | 0.29-1.18 | 0.98-1.91 |
| queue | `& .\01_code\bench\long_runs.ps1 -Part queue -AllowLong` | 0.06-0.17 | 1.13-7.19 |
| liquidation | `& .\01_code\bench\long_runs.ps1 -Part liquidation -AllowLong` | 0.09-0.32 | 1.76-14.83 |
| adversarial | `& .\01_code\bench\long_runs.ps1 -Part adversarial -AllowLong` | 0.10-3.43 | 1.66-14.65 |
| churn | `& .\01_code\bench\long_runs.ps1 -Part churn -AllowLong` | 0.07-0.30 | 0.09-0.39 |

To keep work manageable, append `-CandidatesOnly` to each command first; all
B warm-ups/repeats stay unchanged. Then use `-BaselineOnly -MaxSize 10000` for
an A pilot and inspect observed scaling. Resume the same command with
`-BaselineOnly` to fill larger A cells, allowing overnight execution; no
completed cells repeat. All six full parts total roughly 8-55 hours under the
model, dominated by A construction and instrumented growing-book work.
An A stop skips its remaining repeats and optional instrumentation visibly.
Do not silently discard required B cells or choose B from partial results.
Change `-Session phase4` only for a deliberately new run (required after code
or limit changes). Interrupted in-flight cells have no completed CSV key;
inspect their journal before manually retrying, since raw duplicate keys are
deliberately rejected rather than merged silently.

Open questions: none about implementation. Long timings, robust-memory
conclusions, winner, dashboard and fresh-venv reproduction remain later work.

## Proposed commit (Laurin only; not executed)

From Assignment1:

```powershell
git add -- 01_code/bench 01_code/datagen/benchmark_own.py 02_tests/test_bench_pipeline.py SPEC.md README.md 00_docs 05_evidence 03_results/runs/20261122T003530Z_5d8d15a-dirty_smoke 03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke
git commit -m "Assignment1 Phase 4a: benchmark plan, data manifest and smoke pipeline"
```

Generated data and scratch are excluded. A pre-existing modification to
`../AGENTS.md` is outside this phase's scope and is excluded from this proposal.
