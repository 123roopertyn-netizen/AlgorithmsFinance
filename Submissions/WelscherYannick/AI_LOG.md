# AI log

Required by the lab (slide 59): which AI suggestions were accepted, corrected or
rejected. Tool: Claude Code (Claude Sonnet 5.5 for steps 1–2, Claude Opus 5.5 from
step 3 on). Entries are added as the work
progresses. "Pending review" means the suggestion is in the code but has not yet
been checked and confirmed by me.

| Date | Suggestion by Claude | Decision | Notes |
|---|---|---|---|
| 2026-11-20 | Repository layout: `src/`, `tests/`, `bench/`, `results/`, `dashboard/` | Accepted | Algorithms, generator, tests and measurement code stay separate (slide 58). |
| 2026-11-20 | Two-stage API per method: `prepare(ids)` and `query(state, queries)`, plus `contains_all` | Accepted | Needed to time preparation and query batch separately (slide 60). |
| 2026-11-20 | Revision options for v2: recursive to iterative, remove a copy, or both | Accepted (option 1) | I chose recursive to iterative binary search (v1 recursive, v2 iterative). |
| 2026-11-20 | No Docker; pinned `requirements.txt`; Co-Authored-By trailer on commits | Accepted | Docker is optional on slide 64. |
| 2026-11-20 | Test suite as reusable contract checks run against every version and method | Pending review | `tests/contract.py`, `tests/test_search.py`. |
| 2026-11-20 | Mutant tests: broken methods that the suite must reject (tests of the tests) | Pending review | `tests/test_mutants.py`. Shows the tests detect wrong behaviour before implementation. |
| 2026-11-20 | Synthetic-data generator with seed, hit rate and duplicate rate | Pending review | `src/datagen.py`, `tests/test_datagen.py`. |
| 2026-11-20 | v1 implementation: linear scan with early exit, recursive binary search on `sorted(ids)` (half-open range), built-in `set` lookup | Pending review | `src/search_v1.py`. All 75 tests pass. Linear `prepare` returns the given array without copying; `query` only reads it. |
| 2026-11-20 | v2 revision: iterative binary search with the same range, midpoint and comparisons as v1; linear, hash and binary preparation imported from v1 | Pending review | `src/search_v2.py`, registered in `src/registry.py`. 118 tests pass, no expected result changed. Claude deliberately did not add other micro-optimisations (e.g. caching `s[mid]`) so the comparison isolates recursion vs. loop. |
