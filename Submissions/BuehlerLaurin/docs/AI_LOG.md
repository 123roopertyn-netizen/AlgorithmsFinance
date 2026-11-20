# AI log

AI tool used: Claude Code (Claude Opus 5.5), working under the rules in `AGENTS.md`.
For each step: what the AI suggested, and whether it was accepted, corrected or rejected, and why.

| Step | Suggestion | Decision | Reason |
|---|---|---|---|
| 1 | Create `AGENTS.md` with working rules (git, scope, measurement) | Accepted | Rules written by Laurin in the master prompt; the AI only created the file. |
| 2 | Folder skeleton as in the master prompt, plus `results/raw/.gitkeep`, `results/memory/.gitkeep` and a local `.gitignore` | Accepted | Git does not track empty folders; caches should not be committed. |
| 2 | Use `py -3.13` for the venv instead of `python` | Accepted | `python` resolves to the Microsoft Store alias on this machine; 3.13 is installed and has mature wheels for pandas/streamlit. |
| 3 | Restate the slides as `LAB_SPEC.md` with requirement IDs (F1, T2, M4, ...) | Accepted | Lets docstrings, tests and docs point to the exact requirement they cover. |
| 3 | Duplicate policy `"unique"`/`"allow"`, benchmark with `"allow"` | Accepted | The slides require saving a duplicate policy but do not define one. |
| 3 | "Mixed" = hit rate 0.5 | Accepted | Simplest symmetric reading of "mixed". |
| 3 | v1 binary search with list slicing, v2 iterative without copies | Corrected | Laurin accepted the slicing v1 but added: v2 must be the fastest correct variant, chosen by measurement, not just "iterative". |
| 3 | v2 of linear/hash = unchanged v1 code | Accepted | Avoids inventing changes that blur the v1/v2 comparison. |
| 3 | `list[int]` input, no type validation | Accepted | Matches the slide wording "integer ID array". |
| 3 | Skip Docker | Accepted | Optional in the slides. |
| 4 | Two-phase interface `prepare(ids) -> state`, `query(state, queries)`, registry `METHODS` of frozen `MethodSpec` dataclasses | Accepted | Required by the master prompt; lets preparation be timed separately (I5) and lets one test suite cover every method (F5). |
| 4 | Generator: present IDs even (`2x`), absent queries odd (`2x+1`) from the same span | Accepted | Absent queries are guaranteed absent and spread across the range. A disjoint range *above* all IDs would make binary search always take the same branch on misses and bias the timing. |
| 4 | Default `id_range = 2n`, number of hits `floor(hit_rate*q + 0.5)` | Accepted | With "allow", about 21% of the entries are repeats. Rounding half up gives 1 hit for q=1, hit rate 0.5. The realized hit rate is saved. |
| 4 | Static AST test that linear/binary search functions use no `in` comparison, `bisect`, `.index` or `.count` | Accepted | Turns the rule "searches are hand-written" (F6) into a check that runs automatically. |
| 4 | Generator implemented now, not stubbed | Accepted | The lab says synthetic data comes first (T5); only the algorithms must fail before implementation (R1). |
| 5 | v1 binary search as a recursive helper that slices (`arr[:mid]`, `arr[mid+1:]`) | Accepted | Decision Q3: naive v1 on purpose, so the revision has a measurable effect. |
| 5 | Name the helper `binary_contains_recursive` (no leading underscore) | Accepted | The static F6 test only inspects functions starting with `linear_`/`binary_`; a `_helper` would have escaped the check. |
| 5 | Linear `prepare` returns the caller's list itself (no copy) | Accepted | No preparation cost; safe because `linear_query` only reads it. |
| 5 | `hash_query` as a list comprehension with `x in state` | Accepted | `in` on a set is allowed (F6); the ban applies to lists inside the searches. |
| 6 | Write two v2 candidates (classic three-way, lower bound) and choose by measurement | Accepted | Decision Q3: "fastest correct algorithm". Theory alone does not settle it: classic stops early on hits, lower bound has a shorter loop. |
| 6 | Inline the search loop into the query loop (no helper call per query) | Accepted | Saves one Python function call per query; v1 keeps its helper unchanged. |
| 6 | Keep the sorted copy in `binary_prepare` | Accepted | It is the one *necessary* copy: sorting in place would break F4. The removed copies are the slices. |
| 6 | `BINARY_V2_CANDIDATES` registry, included in the test fixture but not in `METHODS` | Accepted | Both candidates must pass the same tests (F5), while the benchmark grid keeps exactly one v1 and one v2 per method. |
| 6 | New tests: boundary cases with duplicate min/max, power-of-two lengths, exhaustive arrays of length 0..5 over {0,1,2} | Accepted | Cases the lower-bound form makes risky (`lo == n`, first copy in a duplicate run). Added, nothing weakened (R4). |
| 6 | Write `bench/env.py` and `bench/binary_variants.py` already in Step 6 | Accepted | The choice of v2 needs saved, reproducible evidence with environment metadata (I6). |
| 6 | Choose `lower_bound` as v2 | Accepted | Lower median in all 9 cells; clearly faster on absent and mixed queries, a tie within noise on all-present queries. |
| 7 | Measure `total_s` as its own timed block (`query(prepare(ids), queries)`), and also save `prep_s + query_batch_s` | Accepted | The slides ask for the "combined elapsed time"; the sum is kept as a cross-check (median ratio 0.99). |
| 7 | Disable garbage collection inside timed blocks | Accepted | Same convention as `timeit`; keeps random GC pauses out of short measurements. Documented in the module docstring. |
| 7 | Measure methods round-robin in a seeded random order per repeat | Accepted | Prevents slow drift of the machine from always hitting the same method (the cause suspected in Step 6). |
| 7 | Measure and save the timing-loop overhead (`overhead_per_call_s`, about 4e-8 s) instead of subtracting it | Accepted | Subtracting would hide a correction inside the data; saving it lets a reader judge the q = 1 values, where it is about 20% of a hash query. |
| 7 | Smoke tests for the benchmark (`tests/test_bench.py`) | Accepted | Reviewers can check that the measurement code runs and writes complete files without waiting a minute. |
| 7 | Explain v1's hit-vs-miss difference by allocator noise | Corrected | First idea was "warm-up order" (Step 6). Interleaving did not remove it; the raw repeats are bimodal, so the documented explanation is noise from large allocations, backed by the raw values. |
