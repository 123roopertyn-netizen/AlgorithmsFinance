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
