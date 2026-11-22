# Revision log

## Phase 3, 2026-11-21: A -> B1 (base `efee8d4`, uncommitted)

Laurin selected candidate B1. A stays unchanged as the oracle; Claude (chat)'s
independent verification of A on all five supplied 10k streams (0 differences)
was reported by Laurin at handover. Codex has not rerun that independent code.

The revision changes the storage/matching organization: live id index, slot-based
records, per-price deque FIFO, sorted signed prices with the best at the tail,
lazy cancellation with level live/stale counts and threshold compaction. This
replaces A's repeated whole-side scans with indexed access and head matching;
new/removed price levels still cost O(P) list movement. Shared validation and
every existing test/expected result are preserved. Optional counters use the
same engine methods, are off by default and are checked for result/state parity.

Predictions and code-based bound types, including compaction credits, are in
SPEC.md Version B1. The standalone diagnostic checks the new internal invariants
and compaction thresholds without editing `02_tests/`. The authorized Phase 3
timing is **sanity, not a benchmark**: one observation per version/scenario,
no warm-up or repeated medians; official speed/memory claims wait for Phase 4.

Verification: `05_evidence/20261121T224926Z_efee8d4-dirty_phase3-all-tests-green.txt`
reports 340 passed. No B/A disagreement occurred; tests and A were unchanged.
The new internal diagnostic passed both cancellation- and fill-driven compaction
and counter/plain parity. Sanity observations (replay only, seconds):

| Scenario (10k events) | A replay seconds | B replay seconds |
|---|---|---|
| `buildup` | 7.937737 | 0.052302 |
| `crowded` | 8.133971 | 0.046093 |
| `mixed` | 1.154026 | 0.077342 |
| `sweep` | 7.931050 | 0.054345 |
| `cancel_churn` | 0.028029 | 0.037469 |

These one-shot values are **sanity, not a benchmark**; raw parse/setup/replay and
environment metadata are in `03_results/runs/20261121T224807Z_efee8d4-dirty_phase3_sanity_not_benchmark/`.
B was observed slower on cancel_churn, where live books are small. Official
measurements, profiling and any further optimization remain future phases.

## Phase 3b, 2026-11-22: preserve A/B1; add B2 and B3 (base `b5411d4`)

B2 replaces only the level queue organization with OrderedDict so keyed cancels
physically remove their linked node, with no stale records or compaction. B3
keeps B1's deque/compaction logic and replaces the sorted price list with a lazy
heap/in_heap set. Public validation, status/result construction and counter
flag semantics are shared from B1. A/B1 sources and all original expected data
are unchanged. Internal assertions move into pytest; stateful and CLI checks
are parametrized across variants without weakening their assertions.

Fresh red stubs preceded algorithm code (142 failures for missing B2/B3);
final verification: 501 passed. Targeted internal checks also detect the two
in-memory compaction/heap faults with AssertionError. Q11 generator copy matches
MANIFEST.json and regenerates all five supplied streams byte-identically.

Predictions and full bound types were recorded in SPEC.md before the one-shot
sanity. Observations below are **sanity, not a benchmark** (seconds):

| Scenario (10k events) | A s | B1 s | B2 s | B3 s |
|---|---|---|---|---|
| `buildup` | 7.348022 | 0.053039 | 0.051708 | 0.053452 |
| `crowded` | 7.984575 | 0.043179 | 0.047533 | 0.045571 |
| `mixed` | 0.993087 | 0.047189 | 0.049398 | 0.075636 |
| `sweep` | 7.888637 | 0.057057 | 0.055969 | 0.054018 |
| `cancel_churn` | 0.029583 | 0.036689 | 0.049578 | 0.053755 |

Raw evidence: `03_results/runs/20261121T234816Z_b5411d4-dirty_phase3b_sanity_not_benchmark/`.
Formal measurements choose final B in Phase 4. B3's lazy heap can retain distinct
cancelled prices until they reach its root; there is no unrequested heap
compaction/adaptive index. Adaptive switching is only considered after Phase 4.

## Phase 4a, 2026-11-22: measurement pipeline, no engine revision

Base `5d8d15a`. Selection criteria were fixed in SPEC before generation/smoke.
Added a data catalog with exact commands/hashes; generated and verified the full
planned inputs outside measurement (114 entries, 105 physical files). Added
isolated primary timing and separate latency/memory/count workers, per-replay
watchdogs, explicit stops, metadata, sample oracle checks and raw repeat CSVs.
Added own Q7/drift generators and a counted A observer adapter; A and every B
engine remain unchanged. The existing harness gains optional phase watchdog
and non-retained curve-observer support; its existing default timing path is
preserved. Sixteen new pipeline tests accompany the unchanged 501 engine tests.

Corrected two runner defects before the final smoke: sample cloning must support
non-object rejected events (deepcopy, not dict conversion); completed over-limit
phases must retain their actual phase in the stop record. Each has saved minimal
red/green evidence. These changes do not alter order-book behavior or expectations.

Final smoke at 1k/seed42: 216 cells OK, five repeats plus warm-up, separate
instrumentation and counter parity. Full suite: 517 passed in 176.97s. B3 drift
retains501 heap keys at two live orders, consistent with its documented risk;
no final exclusion/winner is declared. No 10k/100k/1M engine benchmark was run.
BENCHMARK_PLAN.md and RUNTIME_ESTIMATE.md hand long execution to Laurin after
review/commit. No algorithm optimization, adaptive variant or speed claim was
introduced in this phase.
