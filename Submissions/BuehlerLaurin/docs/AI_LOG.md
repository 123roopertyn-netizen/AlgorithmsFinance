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
