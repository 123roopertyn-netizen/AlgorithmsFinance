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
| 2026-11-20 | Test suite as reusable contract checks run against every version and method | Corrected | `tests/contract.py`, `tests/test_search.py`. In my review I added four checks: ints beyond 64 bits, tuples as input, a prepared state that must not follow later changes to `ids`, and binary-search boundaries for every length 0–8. The state check exposed a bug in linear search (see below). |
| 2026-11-20 | Mutant tests: broken methods that the suite must reject (tests of the tests) | Corrected | `tests/test_mutants.py`. Kept; extended by a ninth mutant whose state aliases the input, to show the new state check catches it. |
| 2026-11-20 | Synthetic-data generator with seed, hit rate and duplicate rate | Accepted | `src/datagen.py`, `tests/test_datagen.py`. At my request the README now documents the hit and duplicate policies, including that hits sit at random positions (about n/2 comparisons per hit for linear search). |
| 2026-11-20 | v1 implementation: linear scan with early exit, recursive binary search on `sorted(ids)` (half-open range), built-in `set` lookup | Pending review | `src/search_v1.py`. All 75 tests pass. Linear `prepare` returns the given array without copying; `query` only reads it. |
| 2026-11-20 | v2 revision: iterative binary search with the same range, midpoint and comparisons as v1; linear, hash and binary preparation imported from v1 | Pending review | `src/search_v2.py`, registered in `src/registry.py`. 118 tests pass, no expected result changed. Claude deliberately did not add other micro-optimisations (e.g. caching `s[mid]`) so the comparison isolates recursion vs. loop. |
| 2026-11-20 | Runtime benchmark: warm-up with growing call counts, `number` calls per measurement, 5 repeats with fresh state, rotated order, GC paused, raw CSV plus metadata | Pending review | `bench/benchmark.py`, `tests/test_benchmark.py`. Full run at commit `09dafe7`. |
| 2026-11-20 | Analysis of the results, including the "total below preparation" anomaly; two explanations tested in throwaway experiments and rejected | Pending review | Documented as an open shortcoming in the README instead of adjusting the numbers. The console log was not committed because it contained a local absolute path. |
| 2026-11-20 | Memory measurement with three fresh tracemalloc sessions per method (prepare, query, total), input built before tracing | Pending review | `bench/memory.py`, `tests/test_memory.py`. Full run at commit `6b79fc8`. |
| 2026-11-20 | Claude's first docstring claimed the recursion of v1 is invisible to tracemalloc | Corrected | The smoke run showed a higher v1 query peak; Claude traced it to int objects kept alive by pending recursive calls and fixed the docstring before committing. |
| 2026-11-20 | Dashboard design: dark navy glass cards with pastel accents | Corrected | I asked for a modern, rounded look with pastel colours based on the base tones of Roberts Space Industries. Claude approximated those tones (no official codes), validated the data colours for contrast and colour-blind separation, and used lighter pastel tints only for UI accents. |
| 2026-11-20 | Dashboard in Streamlit + Plotly: filters, runtime, revision, memory, raw data and environment views; summaries computed from raw files | Pending review | `dashboard/`, `tests/test_dashboard_data.py`. |
| 2026-11-20 | README claims "linear is fastest with one query" and "noise at most 6.4 %" | Corrected | The dashboard's computed headline showed linear wins 5 of 6 scenarios (hash wins at n = 1,000, absent query) and that 6.4 % applies to the total, 4.9 % to the query batch. README fixed. |
| 2026-11-20 | Final README: quick start, structure, specification, test overview, AI use, placeholder for the audit commit | Pending review | Commands checked by Claude in a fresh clone of the branch: install, 140 tests, both benchmark scripts (`--quick`) and a headless run of the dashboard, without editing any file. |
| 2026-11-20 | Fix for the bug found by my new check: linear `prepare` copies `ids` into a tuple | Accepted | Tests were committed failing first (`e8dc99c`, 2 failures), then fixed (`302dc8f`). One memory test that used linear as an example of "no copy" now uses its own aliasing method. Timing and memory were rerun at `302dc8f`; README numbers updated (revision gain now 7–15 %, linear copy about 2 ns and 8 bytes per entry). |
| 2026-11-20 | Dashboard smoke test (`tests/test_dashboard_app.py`) and relative output path in `bench/benchmark.py` | Pending review | Added after the fresh-clone check; 146 tests pass. The benchmark change only affects the final print, not the measurement. |
