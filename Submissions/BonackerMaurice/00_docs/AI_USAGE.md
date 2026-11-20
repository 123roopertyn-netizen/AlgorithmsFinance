# AI usage

Slide 58 says: "If you used AI, explain which suggestions you accepted,
corrected, or rejected."

**Tool:** Claude Code (Anthropic), desktop app.

**Date:** 2026-11-20. The initial build used high reasoning effort.
Refinements may use a faster model.

## What the AI produced

The first version of every file in this folder was generated from the lab
slides, following the instructions in `AGENTS.md`:

- the project structure and `AGENTS.md`
- the tests (written before the implementations, see `DEVLOG.md`) and
  `tests/mutation_check.py`
- the implementations: LinearSearch v1/v2, BinarySearch v1/v2 and the hash set
- the synthetic-data generator
- the timing and memory measurement code and the run orchestrator
- the Streamlit dashboard, written by a separate AI agent from the results
  format spec
- an independent AI review of the build, acting as a Phase 2 auditor; the
  findings and how they were handled are below

## Decisions for Maurice to record

Fill this in yourself: what you checked, kept, changed or threw away, and why.

| Suggestion | Accepted / corrected / rejected | Why / what you changed |
|---|---|---|
| Split each method into `prepare` + `query` so preparation can be timed separately | | |
| v1 → v2 revisions (no copy plus direct iteration; recursive → iterative) | | |
| Identical `TypeError` validation for all methods, excluded from timing | | |
| Measure `total` directly instead of summing prepare + query | | |
| Calibrated batching of short calls (`min_measure_seconds`), gc disabled in timed loops | | |
| Generator: IDs from `[0, 2n)` with duplicates, exact hit counts, q=1 "mixed" rounds up | | |
| Dashboard content for reviewers (provenance, test evidence, same-code control, slopes, spot check) | | |
| Review findings (see below) | | |

## Review findings and how they were handled

An AI reviewer audited the build (algorithms, tests, generator, benchmarks) as a
Phase 2 auditor would. The algorithms were correct on everything it tried. The
findings were about how far the claims can be trusted:

| # | Severity | Finding | Handling |
|---|---|---|---|
| 1 | High | A q=1 "present" timing rested on one random hit position (0.06·n at n=1k, 0.76·n at 10k), so the fitted linear slope came out about 1.5. With duplicates, first hits sat at about 0.4·n, not 0.5·n | **Fixed:** hits are placed at stratified *first-occurrence* positions, `mean_first_hit_frac` (≈ 0.50) is saved per dataset, and tests were added |
| 2 | Medium | Nothing tested the measurement protocol: 4 protocol mutants (prepare timed as free, query including prepare, preflight off, input built inside tracing) survived | **Fixed:** call-counting probe tests per segment, a fresh-state test, preflight tests and a memory test |
| 3 | Medium | Nothing enforced "implemented by hand": a secretly linear binary search, `in` in linear search, and a list-based "hash" all survived | **Fixed:** an AST ban on `in`/bisect/index/count, comparison-counting bounds, prepared-state checks, and 2 new mutants (10/10 killed) |
| 4 | Medium | binary v2 returned `numpy.bool_` for NumPy int input | **Fixed:** validation accepts Python `int` only; NumPy users pass `.tolist()`. Test added |
| 5 | Medium | Query timings are warm-cache; total ≠ prepare + query | **Documented** in the `query`/`total` definitions |
| 6 | Medium | Provenance could claim a clean tree without git; run_id hid dirty runs; code could change mid-run | **Fixed:** `dirty: None` when unknown, a `_dirty` run_id suffix, a source SHA-256 checked at start and end, and a `status` field |
| 7 | Low | `prepare`/`total` include freeing the result | **Documented** |
| 8 | Low | The overhead was measured with a bare call, not the real wrappers | **Fixed:** `noop_call_s` (partial) and `noop_lambda_call_s` (lambda) |
| 9 | Low | Calibration could fall below the target duration | **Fixed:** 25% margin; the duration is derivable from the raw CSV |
| 10 | Low | Memory includes harness bytes | **Documented,** and the no-op baseline is saved as `memory_baseline` |
| 11 | Low | A failing test would leak the Windows user name into public result files | **Fixed:** home and user paths are redacted in `tests.txt`/`tests.xml`. Test added |
| 12 | Low | Dense small IDs are a best case for hashing and comparisons | **Documented** (README limitations) |
| 13 | Low | q=1 "mixed" is really all-present | **Fixed:** removed from the grid |
| 14 | Low | Cross-version determinism was overstated | **Fixed** the wording, and added golden-checksum and shuffle tests |
| 15 | Low | Smaller items | **Fixed:** expected slopes for binary corrected, psutil version recorded, memory phase checks checksums, preflight checks exact `bool`. **Not changed:** a cold-cache timing variant and a large-ID sensitivity run (out of scope) |
