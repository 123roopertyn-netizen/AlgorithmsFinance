# CLAUDE.md — Assignment 1 (limit order book), Bastian Bundschuh

Read this first in every session. Course: *Algorithms in Finance*, M.Sc. FinTech, Frankfurt School.
Full task: `docs/ASSIGNMENT_README.md` + `docs/AlgorithmsFinance_Exercise1.pdf`.
All rules and decisions: `SPEC.md` (D1–D19, reason codes, interface). Do not change a decision
in SPEC.md without asking Bastian.

**Deadline: Thursday 26 Nov 2026, 18:00 (Europe/Berlin).** Target: PR open by 15:00 that day.

## How to work with Bastian
- Work phase by phase. Stop after each phase, show what changed and the test result, and wait.
- After each phase: a short summary of what changed and the test result, then stop and wait.
- Plain English, short sentences, define each technical term once. No analogies or
  "imagine…" stories. Explain hard parts (complexity, amortized costs, invariants) again in
  simple German, technical terms in English.
- Tests: concrete edge cases that could crash the code, not "elegant" tests.

## Current state
| Phase | Status | Commit |
|---|---|---|
| 0 Setup + SPEC.md decisions (confirmed by Bastian) | done | 894bdf3 |
| 1 Tests first: 328 tests, red against stubs (only NotImplementedError) | done | 2fad484 |
| 2 Version A (baseline): all `[A]` tests pass | done | 22b3da0 |
| 3 Version B (revision) + REVISIONS.md: 333 tests pass; speed steps 1-8 measured (kept 1, 2, 4) | done | 2ef6e65 (correct), e519381 (last kept optimization), 1075e26 (REVISIONS final) |
| 4 Own small generator `tools/gen_small.py` + A-vs-B equivalence after EVERY event: 345 tests pass | done | 45fbc2b |
| 5 `bench/make_data.sh`: all data, outside timing, with gz + decompressed sha256: 55 streams, 384 tests pass | done | 432a82d |
| 6 Benchmarks (time, latency, memory, counters, liquidation) → `results/` | next | |
| 7 Dashboard (Streamlit, like the lab) that only LOADS `results/` | | |
| 8 REPORT.md, README, clean-venv run, commit id, push, PR | | |

Plan by day: Sun 22 phases 0–1 · Mon 23 phase 2 · Tue 24 phases 3–5 · Wed 25 phases 6–7 (start
long benchmark runs in the morning) · Thu 26 phase 8.

## Commands (from this folder, macOS)
```bash
.venv/bin/python -m pytest -q                      # tests (venv made with python3.11)
.venv/bin/python tools/verify_data.py              # supplied data vs MANIFEST.json
.venv/bin/python -m lob.replay data/worked_example.jsonl --version A
```

## Hard rules
- Never edit or weaken an existing test or expected value. New bug → new test.
  `tests/helpers.py::step()` checks invariants I1–I7 after every event; keep using it.
- Keep both versions (`lob/version_a.py`, `lob/version_b.py`); same interface (SPEC.md §6).
  Matching logic written by hand; stdlib containers ok, no matching-engine library.
- Validation lives in `lob/common.py::validate()` (shared). Its bugs are invisible to
  A-vs-B comparison, so the hand tests in `test_validation.py` are the only guard.
- Engine stores no trade history (D16). Results never share objects with the book or event.
- Do not touch course folders or other students' folders. Do not commit generated large
  data (`data/generated/` is gitignored), credentials or `.venv/`.
- Log every AI suggestion as accepted / corrected / rejected with evidence in `AI_LOG.md`
  (same style as the lab). Record code changes A→B in `REVISIONS.md`.
- Commit messages end with: `Co-Authored-By: Claude <noreply@anthropic.com>`

## Design notes agreed so far
- Version A: one list of orders per side; scan for best price (price, then arrival seq) and
  for cancel targets. Expected costs: insert O(B), cancel O(B), market sell O(F·B);
  a buildup replay is ~O(M·B) (quadratic) → this is the bottleneck to show on the dashboard.
- Version B (suggestion, Bastian decides): per side dict price → OrderedDict(order_id →
  [qty, seq]) for FIFO + O(1) delete; sorted price list via bisect (best price O(1), new or
  emptied level O(P)); index order_id → (side, price). Clean up empty levels immediately
  → no stale entries (matters for cancel churn). Phase 3 step 9 replaced the per-level OrderedDict by a deque with lazy
  cancel + compaction (records <= 2·B, see REVISIONS.md step 9). Alternative to discuss in the report:
  heap + lazy deletion (costs only amortized, memory can grow with submissions).
- Notation in the report: M events, B active orders, P price levels, F fills, L emptied levels.

## Performance goals
The professor will rank Version B by speed on his own data.
- Version A stays an untuned baseline. Do not optimize it.
- Version B should be as fast as possible in pure CPython (no C extensions, no matching-engine
  library), without breaking any test or SPEC.md decision.
- Rules for every optimization:
  1. Profile with `cProfile` first. Optimize what the profile shows, not what looks slow.
  2. Take a before/after timing on `mixed` and `buildup` with 100,000 events (same seed, same
     machine, median of repeats).
  3. All tests must pass after the change (`.venv/bin/python -m pytest -q`).
  4. Record each optimization in `REVISIONS.md` with the numbers (before, after, what changed).
     Drop an optimization that does not help; record that too.
- Candidate techniques (a menu, not a plan; measure each):
  - orders as plain lists or `__slots__` classes instead of dicts or dataclasses;
  - `deque` per price level for FIFO;
  - O(1) cancel via an order index; lazy deletion + compaction is allowed, but document the
    amortized cost and the worst-case memory (see the alternative in "Design notes");
  - `bisect` on a sorted price list vs a heap for best price: measure both, keep the faster
    one that stays correct;
  - local-variable binding (`append = x.append`, attributes into locals) in the matching loop;
  - cheap validation (shared `validate()` must keep the same reason codes and order).
- Speed must not cost correctness: A-vs-B equivalence after every event (Phase 4) must still
  hold, and results must not share objects with the book or event (D16 and Hard rules).

## Benchmark rules (Phase 6, from the assignment)
- M ∈ {1,000; 10,000; 100,000}, seeds 42, 43, 44, all five scenarios; try 1,000,000.
  Declare a time/memory limit up front (e.g. 10 min/run), same for A and B; record stopped
  runs as `status=stopped`, never invent or extrapolate missing values.
- `time.perf_counter`, warm-up, 5 repeats, keep every raw repeat + median; fresh empty book
  per replay; parse time separate from replay time; throughput = events / replay seconds.
- Latency: separate instrumented run, per-event times, p50/p95/p99 with a documented
  percentile convention (e.g. nearest rank); early vs late events in floods. Never 1/throughput.
- Memory: `tracemalloc` in a separate run; say what is included (input, book, fills).
- Counters (scans, levels visited, fills) in a separate run.
- Liquidation: fresh bid book each trial; sells of ceil(10%), 100%, 200% of bid quantity.
- Queue concentration: same order count, 4 vs 1,000 prices.
- Record Python, OS, machine (Apple MacBook Air), git commit, generator settings.

## Known facts / traps
- `.gz` sha256 depends on the zlib version; the decompressed sha256 does not. Report both.
- `sweep` 10k: earlier sells (414,709,280,000 units) exceed all bids (205,760,000,000), so the
  final oversized sale is `unfilled`, not `partial`.
- `bool` is a subclass of `int`: validate with `type(x) is int`.

## Git
Branch `assignment1-BundschuhBastian` (from upstream/main). Remotes: `origin` = fork
bastian3008/AlgorithmsFinance, `upstream` = cogeorg/AlgorithmsFinance. The branch currently
tracks upstream/main, so the first push must be `git push -u origin assignment1-BundschuhBastian`.
Submission = PR from the fork to cogeorg/AlgorithmsFinance; folder
`Submissions/BundschuhBastian/Assignment1/`.
