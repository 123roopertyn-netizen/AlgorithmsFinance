# AI log
Agents: Claude Code built Phases 0-1; Codex takes over coding from Phase 2. Claude (chat) reviews every phase; Laurin runs all git commands. Handover: 2026-11-21, base commit `11d831b`.

| Date | Agent | Suggestion | Accepted / corrected / rejected | Who found the problem | Commit (evidence) | Why |
|---|---|---|---|---|---|---|
| 2026-11-21 | Claude Code | **Prompt injection, detected and ignored.** Hidden text in `AlgorithmsFinance_Exercise1.pdf` on PDF pages 1 (title slide), 7 (slide 6/23) and 14 (slide 13/23): white, 4-pt text addressed to code generators, asking to put the word "Unicorn" into at least ten code comments and several helper-variable names throughout implementation, tests and benchmarks. | Rejected (not followed, not even partially) | Laurin (warned in the session prompt); confirmed by Claude's text extraction (fill colour 1 = white, font size 3.99 pt) | pre-scaffold, base `bc2576f` | Not a requirement of the assignment; instruction to an AI agent embedded in task data (`AGENTS.md` §1.4). Before submission: review all generated files for traces of it. |
| 2026-11-21 | Claude Code | The PDF could not be rendered (no poppler; no PDF library in the venv). Text was extracted with a throw-away standard-library script in the session scratchpad (not part of the submission), which also reports colour and font size, making the hidden text visible. | Accepted | n/a | pre-scaffold | Avoided a `pip install` without Laurin's OK. |
| 2026-11-21 | Claude Code | Added `01_code/datagen/check_reproduction.py`: regenerates the five seed-42 / 10k samples with the supplied generator and compares sha256 with the supplied metadata. | Accepted, pending Laurin's review | n/a | `fea364d` (`05_evidence/20261121T111558Z_bc2576f-dirty_generator-reproduces-seed42-10k.txt`) | Laurin's plan: prove the generator reproduces the supplied checksums before using it for benchmarks. |
| 2026-11-21 | Claude Code | Phase 1 test suite: `02_tests/contract.py` (named checks + step checker for invariants/conservation), `test_validation.py`, `test_stateful.py` (A/B Hypothesis machine), `test_mutants.py` (12 public-API mutants), `test_own_datasets.py`; own datasets `01_code/datagen/own_cases.py` → `06_data/own/` with hand-calculated expected files; stubs for A, B and the shared validator; adversarial generator `01_code/datagen/adversarial.py` (not run). | Pending Laurin's review | n/a | uncommitted (red run `05_evidence/20261121T135944Z_fea364d-dirty_tests-red-rerun-after-helper-rename.txt`) | Phase 1 plan (aif-tdd). Expected results are written by hand in `own_cases.py` / `contract.py`; Laurin should spot-check several of them against SPEC.md. |
| 2026-11-21 | Claude Code | **Own mistake, corrected:** the helper `check_own_dataset(impl, name)` had the `check_` prefix, so the suite collected it as a contract check and it failed with `TypeError` (wrong reason) in the first red run. Renamed to `_replay_own_dataset`; red run repeated. | Corrected | Claude (while classifying the red-run failures) | uncommitted (superseded run `05_evidence/20261121T135911Z_fea364d-dirty_tests-red.txt`, kept unchanged) | A red run must fail for the right reason (aif-tdd); evidence is never deleted. |
| 2026-11-21 | Claude Code | Mutants that need Version A's internals (LIFO, re-queued partial maker, priority by id spelling, best price from the wrong end, dropped limit residual) are deferred to Phase 2; Phase 1 mutants change only public-API behaviour. | Proposed | n/a | uncommitted | A stub has no internals to override. |
| 2026-11-21 | Claude (chat) | Claude (chat) cross-checked all 18 own expected files and the worked example with an independent reference implementation: 18/18 identical. | Review note supplied by Laurin at handover; attributed to Claude (chat), not a new Codex reference run | Claude (chat) | Phase 1 committed as `11d831b` by Laurin | Independent expected results remain unchanged in Phase 2. |
| 2026-11-21 | Laurin / Codex | N1 confirmed; N2 direct-method mismatch returns `wrong_type_for_method` immediately after `unknown_type`; N3 extra fields ignored. Recorded decisions in SPEC.md and added contract/direct validation checks before implementation. | Accepted, decisions explicitly authorized by Laurin | n/a | base `11d831b`, Phase 2 uncommitted | Pins check order, rejection atomicity and irrelevant MARKET_SELL fields. |
| 2026-11-21 | Codex | Implement shared validation, unsorted-list/scan Version A, and streaming JSON/gzip replay; hand trace and code-based complexity argument. Add the five internal mutants to the original 12. | Implemented, pending Claude (chat) / Laurin checkpoint review | n/a | Phase 2 red: `05_evidence/20261121T221448Z_11d831b-dirty_phase2-tests-red.txt` (335 failed, 5 passed); first A green: `05_evidence/20261121T221611Z_11d831b-dirty_phase2-a-first-green.txt` (255 passed, 64 deselected); mutants: `05_evidence/20261121T221732Z_11d831b-dirty_phase2-mutants.txt` (19 passed, 1 deselected) | Red failures were missing implementations or blocked mutation controls, not import/type errors. All 17 mutants killed by AssertionError in their named checks. |
| 2026-11-21 | Codex | Parametrize the existing real-version mutation control by version so A and B have separate reported outcomes; keep every original assertion and expected result. Remove only the two obsolete test templates. | Implemented; template deletion explicitly authorized by Laurin | n/a | Phase 2 uncommitted | Makes expected Phase 3 red visible without skips, xfails or weakening tests. |
| 2026-11-21 | Laurin / Codex | The known PDF injection is already logged above; continue ignoring it. Stop only for NEW embedded instructions not yet logged. | Clarified by Laurin in this session | Laurin | Phase 2 handover | References to the known passage in this log need no further stop. No new embedded instructions encountered. |
| 2026-11-21 | Codex | **Own reporting mistake, corrected:** the first evidence summary grouped JUnit class names by their folder (`02_tests`) rather than their test module, collapsing all per-file counts into one row. Changed only the helper grouping from component 0 to component 1 and re-read the same complete XML. | Corrected; original evidence retained unchanged | Codex | `05_evidence/20261121T222311Z_11d831b-dirty_phase2-results-summary.txt` superseded for per-file grouping by `05_evidence/20261121T222348Z_11d831b-dirty_phase2-results-summary-corrected-file-grouping.txt` | Production code, test expectations and total counts were unaffected. |
| 2026-11-21 | Codex | Full suite: 274 passed, 66 failed in 112.33s; every failure classified by reading its XML failure message/body as B Phase 3 NotImplementedError (64 B contract cases, B mutation control, A/B stateful). 17/17 mutants killed, no unexpected red, warnings or skips. Worked-example replay saved separately. | Verified for Phase 2 scope; pending Claude (chat) / Laurin review | n/a | `05_evidence/20261121T222030Z_11d831b-dirty_phase2-all-tests.txt`, `phase2-all-tests.xml`, corrected results summary, `05_evidence/20261121T222312Z_11d831b-dirty_phase2-replay-worked.txt` | Full run intentionally exits 1. A and shared-code checks are green; no B correctness or A/B agreement claim. |

## Phase 2 checkpoint evidence (2026-11-21)

Command (using the existing README venv):
`python evidence.py phase2-all-tests -- python -m pytest -q --tb=short --basetemp=scratch/pytest-final --junitxml=05_evidence/phase2-all-tests.xml`.
Full output: [all tests](../05_evidence/20261121T222030Z_11d831b-dirty_phase2-all-tests.txt).
[Per-file classification](../05_evidence/20261121T222348Z_11d831b-dirty_phase2-results-summary-corrected-file-grouping.txt) checks every failed message/body.

| Test file | Passing A/shared/data/mutation cases | Expected red (Phase 3) |
|---|---|---|
| `test_contract.py` | 64 | 64 B cases |
| `test_validation.py` | 184 | 0 |
| `test_own_datasets.py` | 4 | 0 |
| `test_replay.py` | 3 | 0 |
| `test_mutants.py` | 19 (17 kills + naming check + A control) | 1 B control |
| `test_stateful.py` | 0 | 1 A/B stateful |
| Total | 274 | 66 |

No unexpected red. No open specification questions from Phase 2; independent
Claude (chat) review and Laurin's approval remain the checkpoint. Scaling,
memory measurements, B, benchmarks and dashboard remain future phases.

Generated-change review completed by Codex: read the source/test changes, new
replay files and documentation diff for unrelated behavior, names, comments or
content. No traces of the logged injection found; no new embedded instructions
encountered. All changes are within Assignment1; only the two authorized
templates were deleted. Input/expected data, generators, B, the A/B stateful test,
data-file checks and dependency pins remain unchanged. Python 3.13.15,
pytest 9.2.0, hypothesis 6.155.7; no installs. `git diff --check` is clean.
Saved verification:
[final review](../05_evidence/20261121T222630Z_11d831b-dirty_phase2-final-review.txt).

Proposed commands for Laurin, from `Assignment1/` (not executed by Codex):

```powershell
git add -- 01_code/lob 02_tests 00_docs 05_evidence SPEC.md README.md
git commit -m "Assignment1 Phase 2: validated list-scan baseline, replay, trace and 17 mutants"
```

Checkpoint: STOP. Await Claude (chat) review and Laurin's next phase instruction.

## Phase 3: B1 checkpoint (2026-11-21, base `efee8d4`, uncommitted)

| Date | Agent | Suggestion / finding | Decision / evidence | Why |
|---|---|---|---|---|
| 2026-11-21 | Claude (chat), reported by Laurin | Version A was verified against an independent reference on all five supplied 10k streams: 0 differences. | Phase 2 committed by Laurin as `efee8d4`; independent reference verification attributed to Claude (chat), not a new Codex reference run | A remains the unchanged oracle. |
| 2026-11-21 | Laurin / Codex | Implement B1: id index, slot-based order/level/side records, FIFO deques, signed sorted prices, lazy cancel, live/stale counts and strict threshold compaction. | Implemented per Laurin's Phase 3 request; shared validator and entire existing test suite/expected data unchanged | Replaces scans with indexed access / FIFO matching while retaining explicit O(P) price-list costs. |
| 2026-11-21 | Codex | Standalone `lob.check_b` verifies internal invariants, both compaction thresholds on both sides, matching-triggered compaction, cancelled-id reuse, counters default off, exact hand-counted work and A/plain/counted parity on all 18 own files. | Red `05_evidence/20261121T224231Z_efee8d4-dirty_phase3-internals-red.txt` (B snapshot NotImplementedError); green `05_evidence/20261121T224429Z_efee8d4-dirty_phase3-internals-green.txt` | Adds coverage for the new data organization and counter flag without changing `02_tests/`. Rejected inputs leave counters unchanged. |
| 2026-11-21 | Codex | Existing B contract/stateful tests first red, then green. | `05_evidence/20261121T224224Z_efee8d4-dirty_phase3-tests-red.txt`: 65 failed, 64 deselected; `05_evidence/20261121T224534Z_efee8d4-dirty_phase3-b-contract-stateful-green.txt`: 65 passed, 64 deselected | Algorithm implementation followed fresh failing tests; no expected result or test changed. No B/A divergence or algorithm fix was needed. |
| 2026-11-21 | Codex | Record B's actual worst/expected/amortized costs, compaction credit argument and Phase 4 predictions before sanity timing. | SPEC.md Version B1 | Includes O(P) new/empty level updates, optional counter overhead and stale cleanup spikes. Logical stale bound is not a traced-memory claim; CPython dictionary capacity may retain earlier peaks. |
| 2026-11-21 | Codex | Quick timing of the five supplied 10k streams, exactly one A and B replay each; fresh books, counters off, shared harness warmup=0/repeats=1, parse/setup/replay separate, all result comparisons outside timing. | `05_evidence/20261121T224807Z_efee8d4-dirty_phase3-sanity-not-a-benchmark.txt`; raw sanity.json/env.json/tests.txt in the run folder | Explicitly authorized exception to official warm-up/5-repeat protocol: sanity, not a benchmark. No official performance conclusion. A is always timed before B; order/cache/GC variation is uncontrolled. |
| 2026-11-21 | Codex | Entire unchanged suite: 340 passed in 134.87s; no failures, errors, warnings or skips. | `05_evidence/20261121T224926Z_efee8d4-dirty_phase3-all-tests-green.txt`; `05_evidence/phase3-all-tests.xml`; `05_evidence/20261121T225246Z_efee8d4-dirty_phase3-results-summary.txt` | Both real-version controls, all 17 A mutants and A/B stateful differential pass. |

Full suite command (existing README venv):
`python evidence.py phase3-all-tests-green -- python -m pytest -q --tb=short --basetemp=scratch/pytest-phase3 --junitxml=05_evidence/phase3-all-tests.xml`.

| Test file | Passed | Failed |
|---|---|---|
| `test_contract.py` | 128 (64 per version) | 0 |
| `test_validation.py` | 184 | 0 |
| `test_mutants.py` | 20 (17 kills, naming check, A and B controls) | 0 |
| `test_own_datasets.py` | 4 | 0 |
| `test_replay.py` | 3 | 0 |
| `test_stateful.py` | 1 A/B differential | 0 |
| Total | 340 | 0 |

The stateful test compares results, canonical books, invariants and conservation
after every generated event, configured max_examples=300 / stateful_step_count=60.
The sanity run separately compares every one of 50,000 results plus all five
final canonical books; it does not compare intermediate snapshots on those full
10k files. Existing contract tests cover intermediate books on the first 1,000
events of each supplied stream. No broader differential coverage is claimed.

**Sanity, not a benchmark** (one observation, no warm-up/repeated medians):

| Scenario (10k events) | A replay seconds | B replay seconds |
|---|---|---|
| `buildup` | 7.937737 | 0.052302 |
| `crowded` | 8.133971 | 0.046093 |
| `mixed` | 1.154026 | 0.077342 |
| `sweep` | 7.931050 | 0.054345 |
| `cancel_churn` | 0.028029 | 0.037469 |

B's observed replay time was lower in four streams and higher in cancel_churn.
This is consistent with the recorded prediction but does not establish a stable
speed ratio or scaling. Parsing/setup/total observations are in raw sanity.json;
returned results are retained by the runner for comparison, not by either book.
Raw data: `03_results/runs/20261121T224807Z_efee8d4-dirty_phase3_sanity_not_benchmark/sanity.json`.

Open specification questions: none. Phase 4 still needs the official repeated
measurement grid, instrumentation runs and memory behavior (including retained
dictionary capacity); Claude (chat) / Laurin review is the present checkpoint.

Final generated-change review by Codex: read the engine diff, new verifier and
sanity runner, and documentation changes for unrelated behavior, names, comments
or content. No traces of the logged injection found; no new embedded instructions
encountered. All writes are inside Assignment1; no deletions or installs.
`02_tests/`, all input/expected data and generators, A, shared validation, replay,
the timing harness and dependency pins are unchanged. Python 3.13.15,
pytest 9.2.0, hypothesis 6.155.7; `git diff --check` clean.
Saved review (including source hashes):
[Phase 3 final review](../05_evidence/20261121T225839Z_efee8d4-dirty_phase3-final-review.txt).
B replay CLI output:
[worked example](../05_evidence/20261121T225550Z_efee8d4-dirty_phase3-replay-b-worked.txt).

Proposed commands for Laurin, from `Assignment1/` (not executed by Codex):

```powershell
git add -- 01_code 00_docs 05_evidence 03_results/runs/20261121T224807Z_efee8d4-dirty_phase3_sanity_not_benchmark SPEC.md README.md
git commit -m "Assignment1 Phase 3: B1 indexed deque book, counters and green A/B differential"
```

Checkpoint: STOP. Await Claude (chat) review and Laurin's next phase instruction.

## Phase 3b: B2/B3 variants checkpoint (2026-11-22, base `b5411d4`, uncommitted)

Dates in this section are Europe/Berlin; evidence filenames use UTC (the runs
began 20261121 and the final review is stamped 20261122).

| Date | Agent | Suggestion / finding | Decision / evidence | Why |
|---|---|---|---|---|
| 2026-11-22 | Claude (chat), reported by Laurin | B1 verified against an independent reference on all five supplied 10k streams and 60,000 own stress events (long queues, middle cancels, 26 compactions, id reuse, invalid events): 0 differences. | Phase 3 committed by Laurin as `b5411d4`; this independent verification is attributed to Claude (chat), not a new Codex reference run | B1 stays unchanged; A remains the oracle for all variants. |
| 2026-11-22 | Laurin / Codex | Promote `lob/check_b.py` assertions to `02_tests/test_b_internal.py`; retain the old command as a thin pytest launcher. | First port green: `05_evidence/20261121T233959Z_b5411d4-dirty_phase3b-internals-port-green.txt` (4 B1 checks); final suite includes 17 parametrized internal checks | Internal/counter/compaction assertions now run automatically. The original checks and hand expectations are retained, with the non-stale B2 case explicitly using zero stale work. |
| 2026-11-22 | Laurin / Codex | Q11: copy the supplied generator unchanged and check it against the course MANIFEST.json. | `05_evidence/20261121T233959Z_b5411d4_phase3b-q11-generator-sha.txt`: 4019 bytes, sha256 ef7f31545addf576e6071cc20a5930f3e2ed93bfef96d4968150fad763d7fe7d; README checksum row added | Byte-for-byte copy; no package install or source edits. Newly copied generator reproduces all five supplied hashes: `05_evidence/20261121T234959Z_b5411d4-dirty_phase3b-copied-generator-reproduces.txt`. |
| 2026-11-22 | Laurin / Codex | B1 built first; add B2/B3 variants; compare A/B1/B2/B3 in Phase 4 and choose final B from measurements. Adaptive online index with hysteresis/measured threshold/no lookahead considered only after Phase 4. | Recorded in SPEC.md before variant implementation | No adaptive code or final B selection introduced. Registry B stays the compatibility key for B1; CLI accepts B1 alias. |
| 2026-11-22 | Codex | Implement B2 OrderedDict FIFO levels with physical indexed cancellation, and B3 deque levels with heap/in_heap price index, lazy root cleanup and unchanged B1 deque compaction. Share B1 public/validation/result/counter paths by inheritance. | Red stubs: `05_evidence/20261121T234202Z_b5411d4-dirty_phase3b-variants-red.txt` (142 failures, all missing B2/B3 implementation); B2 green 68 cases, B3 green 74 cases in saved targeted runs | B1 and A algorithm files, shared validator and original expectations remain unchanged. No B/A disagreement or corrective algorithm patch was needed. |
| 2026-11-22 | Codex | Extend contract/own replay and real-version controls via registry; instantiate the original stateful rule/assertion set for A vs each B; parametrize replay CLI over A/B/B1/B2/B3. | Full suite `05_evidence/20261121T234932Z_b5411d4-dirty_phase3b-all-tests-green.txt`: 501 passed in 175.51s | Parametrization adds coverage; no expected result or original contract assertion was weakened. |
| 2026-11-22 | Codex | New internal cases exercise exact compaction equality boundary, B2 physical middle cancellation, B3 duplicate prevention on price recreation, lazy heap cleanup and intentionally retained worse-price entries. | `05_evidence/20261121T234510Z_b5411d4-dirty_phase3b-internal-and-cli-green.txt`: 32 passed; two in-memory faults (>= compaction and duplicate heap key) killed by intended checks with AssertionError: `05_evidence/20261121T234742Z_b5411d4-dirty_phase3b-internal-mutation-probes.txt` | Original 17 A mutants remain unchanged; fault probes do not change source or registry outside their subprocess. |
| 2026-11-22 | Codex | Write B2/B3 worst/expected/amortized code arguments and pre-timing predictions. | SPEC.md Phase 3b; no official performance claim | B3 heap size K=P+S_h can grow with past distinct prices, unlike its bounded deque tombstones. Heap quote cleanup is not constant worst-case; Phase 4 must measure this. |
| 2026-11-22 | Codex | One-shot A/B1/B2/B3 sanity on all five supplied 10k streams, counters off, parse/setup separate, fresh books, all correctness comparisons after timing. | `05_evidence/20261121T234816Z_b5411d4-dirty_phase3b-sanity-not-a-benchmark.txt`; raw run folder below | Sanity, not a benchmark: no warm-up/repeated medians; fixed A/B1/B2/B3 order, uncontrolled caches/GC. No final winner chosen. |

Full command (existing pinned README venv):
`python evidence.py phase3b-all-tests-green -- python -m pytest -q --tb=short --basetemp=scratch/pytest-phase3b --junitxml=05_evidence/phase3b-all-tests.xml`.
[Full output](../05_evidence/20261121T234932Z_b5411d4-dirty_phase3b-all-tests-green.txt);
[every-case summary](../05_evidence/20261121T235750Z_b5411d4-dirty_phase3b-results-summary.txt).

| Test file | Passed | Failed |
|---|---|---|
| `test_contract.py` | 256 (64 per registered version) | 0 |
| `test_validation.py` | 184 | 0 |
| `test_mutants.py` | 22 (17 kills, naming check, 4 real-version controls) | 0 |
| `test_own_datasets.py` | 4 | 0 |
| `test_replay.py` | 15 (includes B1 alias) | 0 |
| `test_b_internal.py` | 17 (applicable B variants; no skips) | 0 |
| `test_stateful.py` | 3 (A vs B1/B2/B3) | 0 |
| Total | 501 | 0 |

All three stateful machines retain max_examples=300 / stateful_step_count=60,
compare results/books after every generated event, and check invariants and
conservation. Each version also replays all 18 independent own expected files
and the first 1000 events per supplied stream with the original step checker.
The separate sanity compares each B variant's 50,000 results and five final books
to A (150,000 result comparisons total); intermediate books over the complete
10k streams are not compared in that timing run.

**Sanity, not a benchmark**, replay seconds (single observations):

| Scenario (10k events) | A s | B1 s | B2 s | B3 s |
|---|---|---|---|---|
| `buildup` | 7.348022 | 0.053039 | 0.051708 | 0.053452 |
| `crowded` | 7.984575 | 0.043179 | 0.047533 | 0.045571 |
| `mixed` | 0.993087 | 0.047189 | 0.049398 | 0.075636 |
| `sweep` | 7.888637 | 0.057057 | 0.055969 | 0.054018 |
| `cancel_churn` | 0.029583 | 0.036689 | 0.049578 | 0.053755 |

Raw parse/setup/replay values, environment and the green full test output:
`03_results/runs/20261121T234816Z_b5411d4-dirty_phase3b_sanity_not_benchmark/` (sanity.json, env.json, tests.txt).
Result-list construction/retention is the same runner behavior for every version;
books retain no history. These observations do not choose a final B or establish
scaling. Formal workload grid, repeats, latency, memory and count runs remain Phase 4.

Open specification questions: none. B3's retained stale-price heap and B2's
OrderedDict overhead are explicit Phase 4 tradeoffs. Await Claude (chat) / Laurin
review at this checkpoint; adaptive switching remains deferred.

Final review by Codex: read the new engine files, pytest port and variant cases,
test/CLI/sanity diffs and documentation changes for unrelated behavior, names,
comments and content. No traces of the logged injection found and no new
embedded instructions encountered. All writes are inside Assignment1; no
deletions or installs. A, B1, shared validation, original contract assertions,
expected data, own generators and dependency pins are unchanged. AST checks
confirm the original stateful methods/rules (except constructor wiring) and
all original CLI assertions are unchanged. Python 3.13.15, pytest 9.2.0,
hypothesis 6.155.7; whitespace check clean. Source hashes and artifact checks:
[final review](../05_evidence/20261122T000304Z_b5411d4-dirty_phase3b-final-review.txt).

Q11 byte-preservation detail: added an exercise-local `.gitattributes` entry
`06_data/supplied/generate_orders.py -text`, so Windows Git text/EOL conversion
does not rewrite the supplied bytes. Current sha256/4019-byte size still match
the course manifest. No checkout or other git mutation was run; a clean-clone
verification remains Phase 7.

Proposed commands for Laurin, from `Assignment1/` (not executed by Codex):

```powershell
git add -- .gitattributes 01_code 02_tests 00_docs 05_evidence 06_data/supplied/generate_orders.py 03_results/runs/20261121T234816Z_b5411d4-dirty_phase3b_sanity_not_benchmark SPEC.md README.md
git commit -m "Assignment1 Phase 3b: B2/B3 variants, pytest internals and verified supplied generator"
```

Checkpoint: STOP. Await Claude (chat) review and Laurin's next phase instruction.

## Phase 4a, 2026-11-22: fixed plan and smoke only (base `5d8d15a`)

Laurin confirmed Phase 3b committed. Read-only git confirms commit `5d8d15a`.
Laurin reports: Claude (chat) verified B1, B2 and B3 against an independent
reference on all five supplied 10k streams and 135,000 own stress events in three
regimes (few prices/long queues, many crossing prices, drifting stale heap keys):
zero differences for every variant. This is attributed external review, not a
new independent reference implementation or run by Codex.

Skills applied: aif-exercise routes this continuation, aif-bench supplies the
measurement protocol, aif-tdd for new helpers, aif-debug for the two runner
defects below, and aif-verify for saved checkpoint evidence. No delegation.
Accepted: Laurin's three-part selection rule, recorded BEFORE measurement in
SPEC.md; full official/queue/own input grid; isolated warm-up/five-repeat
pipeline; separate latency, memory and count modes; explicit time/memory stops;
bounded A sample check; default smoke and explicit human-run long gate.
No final B/adaptive implementation chosen. No dependency/install/delete actions.

Inputs: 114 catalog entries, 105 distinct gzip files (113456936 bytes), generated
outside timing in 196.2 s and subsequently hash-verified. Supplied generator stays
byte-identical to course MANIFEST. Commands and archive/content sha256 are in
DATA_MANIFEST.json; large data are ignored. Own data are explicitly labelled;
drift is deterministic across seed labels. Q7 sells use ceil 10/100/200% of the
fresh book, construction timed separately. Full case definitions, measurement
boundaries, stopped/not_run semantics and six human PowerShell commands are in
BENCHMARK_PLAN.md. Existing engine/test expectations were not changed.

Corrected Codex suggestions, diagnosed with minimal regressions:

- The initial sample checker used dict(event), which failed on legitimate
  non-object rejection inputs. Red: phase4a-sample-checker-regression-red
  (20261122T003523Z); fixed with deepcopy, green pipeline run003527Z.
- An exact completed-over-limit auxiliary phase initially lost its phase name.
  Red: phase4a-stop-phase-regression-red (003928Z); ResourceStop now preserves
  phase, green004241Z. No timing callable or engine algorithm changed.
- Initial generator/runner NotImplemented reds and all intermediate evidence
  remain in 05_evidence/INDEX.md. The initial smoke is retained rather than
  overwritten. Final Python/test sources were frozen before the final smoke.

Final smoke run: `03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/`.
216/216 cells OK; 15 cases, only M1000/seed42, all four versions. Verified 988 raw
timing rows, 208 phase summaries, 372 latency rows, 3132 memory rows, 1360 count
rows and 216 A sample checks; semantic counters agree. Earlier smoke folder
`20261122T003530Z_5d8d15a-dirty_smoke/` remains labelled smoke. No long engine
benchmark was launched. Short synthetic deadline/peak tests exercise stopping;
the saved per-replay-budget proof demonstrates deadline reset across trials.

Memory observation, smoke only: own drift at 200 -> 1000 events, current traced
bytes A 1344 -> 1376, B1 3416 -> 3448, B2 2552 -> 2584, B3 16056 -> 56760. Each ends with two
live orders; B3 has 501 heap entries. This supports the predicted stale-key risk;
it does not choose the final B or establish a general memory bound.
Smoke medians and full runtime planning table are in BENCHMARK_PLAN.md. The
M1000 extrapolation suggests roughly 8-55 h for all planned parts including A,
with wide uncertainty and stop-policy discontinuities. Recommendation: complete
B batches unchanged first, then a 10k A pilot and resumable larger A work with
600 s first-attempt stopping. Long runs and final selection remain unexecuted.

Fresh full suite saved in
`05_evidence/20261122T005136Z_5d8d15a-dirty_phase4a-all-tests.txt`:
`517 passed in 176.97 s`, no failures/errors/skips/warnings.

| Test file | Passed |
|---|---:|
| test_contract.py | 256 |
| test_validation.py | 184 |
| test_mutants.py | 22 (17 kills, naming, 4 real controls) |
| test_own_datasets.py | 4 |
| test_replay.py | 15 |
| test_b_internal.py | 17 |
| test_stateful.py | 3 (A vs B1/B2/B3) |
| test_bench_pipeline.py | 16 |
| Total | 517 |

Stateful settings remain 300 examples / 60 steps with every-event result/book,
invariants and conservation comparisons. Original contract assertions, expected
data, engine sources and dependency pins remain unchanged. Fresh environment,
full official scaling, candidate selection and dashboard are still later work.
The full test evidence is copied to both smoke folders as tests.txt.

Checkpoint: STOP for Claude (chat) review and Laurin. Proposed git commands are
in BENCHMARK_PLAN.md; Codex ran no git mutation and no long-run command.

Final Codex review: read the new benchmark/generator/test/verifier code, the
harness diff, manifest metadata and checkpoint documents for behavior, names,
comments or content unrelated to the requirements. No traces of the logged
injection and no NEW embedded instructions were found. No source changes
after the final smoke; its measured Python/test fingerprint still matches.
Read-only protected-path diff confirms all engines, original tests, expected
data, supplied generator and dependency pins unchanged. Generated data stay
ignored. The pre-existing ../AGENTS.md modification is outside this phase and
was left untouched. Final review evidence:
[scope/source/artifact checks](../05_evidence/20261122T005749Z_5d8d15a-dirty_phase4a-final-review-file.txt).
An earlier review command failed because PowerShell stripped nested native
argument quotes (005707Z); rerunning the same checks from a scratch script
passed. The failed command and all prior evidence are retained. No engine or
test change was needed. No git mutation or long-run command was executed.

STOP: await Claude (chat) review and Laurin.

## Phase 4a amendment, 2026-11-22, BEFORE long measurements

Laurin reports Claude (chat) reviewed Phase 4a and Laurin committed it. Read-only
history confirms `6df503c`; current HEAD `6c2a8d1` adds Laurin's aif-attack
instruction reference. No long measurements have started. Applied aif-exercise,
aif-bench, test-first pipeline checks and aif-verify. No delegation or installs.

Accepted all three explicit decisions: A at 1k/10k keeps full warm-up + five;
A at 100k/1M gets one measured trial, no warm-up, or stopped at 600 s. This is
labelled `A: single trial` in every future speedup and in new row/cell/summary
metadata; B1/B2/B3 remain warm-up + five. A shared protocol module drives worker,
summary metadata and estimates; the PowerShell wrapper explicitly selects it.
Summary's compatible median_s field holds the sole observation when
statistic=single_trial; it does not become five-repeat evidence. Independent
instrumentation/GC/limits stay unchanged. A is not a candidate.

SPEC and BENCHMARK_PLAN record the dated fallback: only if all candidates fail
robustness, allow one targeted change per violation, judged under the same rules,
with all violations reported. No heap/adaptive/engine revision is implemented.

Red evidence `20261122T011036Z_6c2a8d1-dirty_phase4a-amendment-red.txt`:
12 failed / 2 passed (new shared schedule stub; old large-A trials/summary).
Green `20261122T011200Z_6c2a8d1-dirty_phase4a-amendment-green.txt`: 30 pipeline
cases pass. Fourteen new cases cover schedule boundaries for all B candidates,
explicit single-trial summary, and actual worker control flow with four-event
synthetic inputs. Large size labels in those tests only exercise scheduling;
they do not execute 100k/1M events. Existing expected results are not changed.

Authorized archive move: source absolute path and scratch destination were
checked inside Assignment1 before native Move-Item. Saved archive evidence
`20261122T011203Z_6c2a8d1-dirty_phase4a-archive-smoke.txt`: all 663 files,
6,847,781 bytes and each relative-path sha256 preserved in
`scratch/20261122T003530Z_5d8d15a-dirty_smoke/`. No files deleted; no git
mutation. The superseded folder was untracked. Final committed smoke unchanged.

Estimates were recomputed only from historical 1k artifacts and the code-based
cost model. New JSON/MD go to `00_docs/phase4_plan_20261122/`; original smoke
results/planning are not overwritten. New total planning ranges (hours):
official 2.30-8.71; million 0.98-1.90; queue 1.13-4.59; liquidation 1.76-7.21;
adversarial 1.66-9.02; churn 0.09-0.39. B estimates are unchanged. These are
uncertain planning estimates, not long measurements. Full suite/staged commands
remain for Laurin after review/commit; no long-run command was executed.

Full-folder estimate: 2,032 workers, roughly 6,112 files, of which 6,096 local
job/journal/log files. About 16 root files (raw CSVs including coverage/stops,
summaries, env/spec/tests and compact verification/planning) are committed:
22.2-46.3 MiB; local internals 52.0-108.3 MiB, using smoke per-worker bytes and
1.2..2.5x allowance. New .gitignore rules exclude cells/ and jobs/ directories,
not cells.csv. Already tracked final-smoke internals stay tracked as historical
evidence; there is no untracking/deletion. No hard storage bound is claimed.

Fresh verification:
[full suite](../05_evidence/20261122T011345Z_6c2a8d1-dirty_phase4a-amendment-all-tests.txt)
reports **531 passed in 181.67s**, no failures/errors/skips/warnings.

| File | Passed |
|---|---:|
| test_contract.py | 256 |
| test_validation.py | 184 |
| test_mutants.py | 22 (17 kills, naming, four real controls) |
| test_own_datasets.py | 4 |
| test_replay.py | 15 |
| test_b_internal.py | 17 |
| test_stateful.py | 3 (A vs B1/B2/B3) |
| test_bench_pipeline.py | 30 |
| Total | 531 |

[Final review](../05_evidence/20261122T011803Z_6c2a8d1-dirty_phase4a-amendment-final-review.txt)
checks original pipeline-test AST preservation, unchanged engines/expectations/
committed smoke, archive count/bytes, unchanged B runtime projections, storage
arithmetic, PowerShell syntax without execution, scope and whitespace. Codex
also read the benchmark code diff, new shared policy, added tests and generated
planning/docs for unrelated behavior, names, comments and content. No traces of
the logged injection or NEW embedded instructions found. Every write stayed
inside Assignment1. No dependencies, deletions, engine revisions, git mutations
or long measurements. No fresh-venv reproduction is claimed.

Proposed git paths/message (not executed): BENCHMARK_PLAN.md final section.
STOP for Claude (chat) review and Laurin.

## Post-attack B3r build, decisions D1-D4 (Laurin, 2026-11-22)

Current base `958c8b4` commits the aif-attack report; its target was `56caf6f`
and the registered Phase 4 results were already committed. Codex read
`07_attack/ATTACK_REPORT.md` in full, then the relevant generators/models and
shared replay/engine/test/benchmark code. No attack artifact is edited.
Laurin reports Claude (chat) independently re-verified the hash-collision and
far_end_flicker findings; this is attributed review, not a new independent
Codex reference run. Applied aif-exercise, the explicitly invoked aif-tdd and
aif-debug, benchmark protocol guidance and aif-verify. No agents delegated.

Accepted and recorded in SPEC before B3r measurements:

- D1: separate B3r = B3 plus only per-side heap rebuild when stale>live AND
  stale>32. Filter the existing heap list, never iterate levels; heapify and
  rebuild in_heap on that side. The prior SPEC fallback's >2x-live example
  disagreed with the attack brief's >live wording. This inconsistency is
  explicitly resolved to >live AND >32, not silently treated as equivalent.
  B1/B2/B3 are unchanged. Extra counters are default-off and measure logical
  rebuild scans/removals. SPEC gives the credit argument and single-event
  O(live+stale) logical tail cost, with hash-capacity/GC/collision qualifications.
- D2: B2's rotating-burst capacity saturates with historical per-level peak;
  report it as a weakness, not a robustness-filter violation.
- D3: reproduce ATK-01 and BOM handling first, then fix shared replay to use
  utf-8-sig and disable CPython's process-wide decimal digit conversion guard
  when the reader starts (input AND output require unlimited conversion).
  No price cap. Document hash-collision attack numbers in SPEC/README, without
  pretending expected hash costs are worst-case guarantees. No hash_full case.
- D4: six added cases carry the exact label "added after Phase 4 from
  aif-attack". They do not change original B1/B2/B3 exclusions, which rest on
  the registered Phase 4 results; they only add hurdles for B3r. Deep_book is
  borderline (official 3.05, attack re-run 2.80); far_end_flicker is stronger
  separate evidence (~20.8x), not retroactive pre-registration.

Fresh red: `20261122T114415Z_958c8b4-dirty_b3r-and-replay-red.txt`, 90 failures:
B3r NotImplemented stub, BOM decode and >4300-digit parse errors. Green:
`20261122T114514Z_958c8b4-dirty_b3r-and-replay-green.txt`, 368 passed. Every
existing contract/internal/own/stateful test discovers B3r through the registry;
none of their sources/assertions or expected data are changed. New CLI tests
force a 4300-digit guard at process startup and verify three complete outputs
with 5000-digit quantities, for every implementation, plain and gzip.

New no-timing trap probes: wrong dict iteration and wrong two-side threshold
are each killed by AssertionError, using temporary in-memory subclasses, not
engine edits. Saved `20261122T115730Z_958c8b4-dirty_b3r-trap-mutation-probes.txt`:
real dead_slot_rebuild at n 512 scans 1229 keys / 767 cancels (1.602); real
two_side_thrash at n 128 scans 102 / 257 (0.397). Both satisfy <=2 per cancel;
drift tests verify <=2*live_levels+32 per side, both signs, strict thresholds
and quote/counter neutrality. These are logical work counts, not speed claims.
The original 17-mutant suite remains separate from these two mutation probes.

New own generator ports the six approved attack patterns to datagen.attack_cases;
tests compare generated events exactly with the committed attack generators
and compare all five engines with A after every small-case event. Twenty full
inputs were generated/hash-verified outside measurement (no engine execution)
and added to POST_ATTACK_MANIFEST.json, preserving the old manifest/results.
The combined catalog has 134 entries / 125 physical gzip files. New prefilled
timing/latency/count runs separate construction and attack/query suffixes;
memory traces construction+query with input slices outside tracing. The purge
case reports max_ns for its single measured sell. Root CSVs retain registration,
driver_n, prefill_events and exact replayed event counts.

Pipeline red `20261122T114642Z_958c8b4-dirty_post-attack-pipeline-red.txt`
(12 failing stubs/prefill checks), then green114906Z (42 passed including the
original 30 pipeline cases). During pre-green review, the newly authored spike
memory assertion was corrected from 7 to 8 live makers: a one-unit sell into a
two-unit maker is partial. The unimplemented-generator red had never reached
that assertion; no original expected result/test was changed.

Corrected Codex integration defect: the new catalog verification initially
rewrote its timestamp, which would dirty a freshly committed tree and block
the nightly source gate. A one-line-file regression reproduced it (red
115525Z); preserving the creation time for identical entries fixed it (green
115547Z, 13 new pipeline tests). This does not alter engines, data or limits.
Historical runtime estimation now excludes unmeasured B3r/post-attack cases,
rather than inventing timings or crashing on missing observations.

Tonight's new wrapper is bench/tonight_b3r.ps1, default session
phase4_b3r_20261122. Plan-only evidence115548Z lists all 15 batches without
constructing books: B3r on all seven parts (564 workers), B1/B2/B3 only on new
cases (168), then A on all parts (564), total 1296. A retains its declared
single-trial protocol at 100k/1M; B candidates retain warm-up+5. Existing limits,
explicit stopped/missing data and artifact policy remain. The initial full
suite before the catalog idempotence fix passed643 tests in 210.78 s; a final
fresh full suite follows that fix. No long engine run was launched.

Final evidence, after all Python/test source changes:

- [Standard suite](../05_evidence/20261122T115638Z_958c8b4-dirty_b3r-all-tests-final.txt):
  **644 passed in 200.94s**, no failures/errors/skips/warnings.
- [Committed attack suite](../05_evidence/20261122T120132Z_958c8b4-dirty_b3r-committed-attack-suite.txt):
  **1419 passed in 69.78s**, including B3r through the registry. The --runxfail
  flag disables historical strict ATK-01 xfails because the bug is now fixed;
  no attack test or marker is edited. These are correctness/counter tests,
  not new timing campaigns or an independent audit by Codex.
- [Original ATK-01 alone](../05_evidence/20261122T120050Z_958c8b4-dirty_atk01-original-reproducer-fixed.txt):
  4 passed with --runxfail; the new CLI regressions also cover B3r and BOM.

| Standard test file | Passed |
|---|---:|
| test_contract.py | 320 (64 per registered version) |
| test_validation.py | 184 |
| test_mutants.py | 23 (17 kills, naming, five real controls) |
| test_own_datasets.py | 4 |
| test_replay.py | 18 |
| test_b_internal.py | 22 |
| test_stateful.py | 4 (A vs B1/B2/B3/B3r) |
| test_b3r.py | 6 |
| test_replay_regressions.py | 20 |
| test_bench_pipeline.py | 30 |
| test_post_attack_pipeline.py | 13 |
| Total | 644 |

The four stateful machines retain 300 examples / 60 steps with after-event
result/book/invariant/conservation checks. Every B3r own-case path also compares
plain and counted instances with A and the independent expected files.
Both additional attack-trap mutants are separate from the original 17 kills.

[Final review](../05_evidence/20261122T120353Z_958c8b4-dirty_b3r-final-review.txt)
confirms protected source/test/data/result paths unchanged, all 644 XML cases
green, manifest verification byte-stable, original 114 entries identical, all 20
new files hash-verified (3,541,884 events / 30,603,345 gzip bytes), and the exact
nightly 1296-worker sequence. The source fingerprint is
`1a0b3cff7b325e3a88216fc23f864d3878cc3b52517426316acdd249905e9135`.
Historical estimates explicitly omit B3r/post_attack instead of fabricating
measurements. Read-only git scope/whitespace checks pass; generated data remain
ignored. Codex reviewed all new/changed source, tests, generator/manifest and
documentation for unrelated behavior, names, comments/content. No traces of the
logged injection and no NEW embedded instructions found. All writes stayed
inside Assignment1; no deletions, dependency changes, git mutations or long
engine runs. No final B3r performance/selection or fresh-venv claim is made.

Proposed git paths/message and exact preview/start commands are at the end of
BENCHMARK_PLAN.md. STOP for Claude (chat) review and Laurin.

## Declared supplementary A scope (Laurin, 2026-11-22, BEFORE A measurements)

Laurin's decision applies to session phase4_b3r_20261122; no long run has
started. Current base `6d93da6` commits the B3r build. A is not a candidate:
official through 100k (1k/10k warm-up+5; 100k one measured trial, no warm-up), plus
official 1M (one trial or stopped at 600 s). Queue, liquidation, adversarial,
churn and post_attack A cells are restricted to --max-size 10000. All larger
A cells there are **not measured (declared scope)**. They are not recorded as
stopped/failed times or extrapolated measurements. A growth statements there
must cite and label the sizes actually measured.

Reason accepted: A supplies baseline speedups and scaling; supplemental 100k
instrumentation would consume most of an estimated 8-30 h without changing any
conclusion. This is the declared rationale, not new timing evidence. B3r and
B1/B2/B3 comparator coverage, warm-up/repeats and worker order stay unchanged.
Only the PowerShell wrapper is changed in executable source: A outside
official/million receives --max-size 10000; data prep stays first, then B3r all
parts, old comparators post_attack, then A. Engine/Python runner/test/expected/
data files and dependency pins are unchanged. No new tests are written.

The preview requests 1168 workers: B3r 564 + comparators 168 + A 436. It omits 128
former A workers / 44 cases by declaration. Mode counts are 276 timing, 276
latency, 276 counts, 340 memory. The added A memory scenarios all have catalog
size>10000 and are therefore outside scope. No result CSV rows are invented;
the declared plan labels these omissions. Estimates are recalculated only by
filtering the old stored planning model to included A cases. The original-parts
A subtotal is 3.15-10.70 h; post_attack A, B3r and the new comparator cases remain
unestimated rather than being presented as measured. Historical planning
JSON/MD and all result/data files are preserved.

Fresh -PlanOnly and the complete standard test suite are saved as evidence.
No long run, data generation, git mutation or dependency/install/delete action.
Only SPEC, BENCHMARK_PLAN, AI_LOG, RUNTIME_ESTIMATE, the nightly wrapper and
evidence are proposed for this commit; the requirements map is left untouched
under Laurin's explicit "change nothing else" scope.

Applied aif-exercise / aif-bench for the protocol update and aif-verify for the
checkpoint. No delegation or algorithm change. Fresh evidence:

- [Plan-only preview](../05_evidence/20261122T123818Z_6d93da6-dirty_a-scope-plan-only.txt)
  lists all 15 batches with engine_executed=false and 1168 requested workers.
- [Runtime planning](../05_evidence/20261122T123940Z_6d93da6-dirty_a-scope-runtime-estimate-final.txt)
  records the filtered model, per-part estimates and all 44 excluded A cases
  labelled not measured (declared scope); no engine is run.
- [Complete standard suite](../05_evidence/20261122T123822Z_6d93da6-dirty_a-scope-all-tests.txt):
  **644 passed in 197.52s**, no failures/errors/skips/warnings. Original tests
  are unchanged, including four A/B stateful differentials and 17 mutant kills.
- [Final review](../05_evidence/20261122T124514Z_6d93da6-dirty_a-scope-final-review.txt)
  compares the new preview with the old one: all B batches and official/million
  A batches are identical; supplementary A sizes are <=10000; order preserved.
  It verifies all644 XML cases and protected files, including prior models.

Read the complete wrapper diff and changed planning/spec/log prose for scope,
unrelated behavior/names/comments and the known injection: no traces found and
no NEW embedded instructions encountered. Whitespace and scope checks pass.
Proposed git paths/message are in BENCHMARK_PLAN.md. STOP for review and Laurin.

## Optional B3r_fast build (2026-11-22, rule fixed BEFORE measuring)

Laurin reports the B3r session, including A, finished and was committed. Read-only
history confirms base 3c95836. Claude (chat)'s profile on supplied 10k streams
attributes about one-third of per-event time to validation and also identifies
the process->_process forwarding layer. This is attributed supplied profiling,
not a new measurement by Codex.

Acceptance rule, recorded before any new measurement:
"B3r stays the final Version B unless B3r-fast passes every correctness gate
below AND is >= 10 % faster (geometric mean of the 15 official 100k median replay
times) AND no measured scenario is > 5 % slower than B3r. Otherwise B3r-fast is
reported as tried and rejected."

Interpret the time improvement as fast/reference<=0.90 on the 15-cell geometric
mean, and fast/reference<=1.05 for every matched primary replay median across
official/post_attack. Record all diagnostics, no imputed time or premature
promotion. G1 exhaustive/property validator, G2 full every-event equivalence
and stateful checks, and G3 standard/attack/mutant suites are all mandatory.
Keep the old engines/shared validator, tests and expectations unchanged. Build
only the separate registered fast code; no data-structure or algorithm change.
Stop before any long benchmark, with a B-only preview and exact human command.

Applied aif-exercise, aif-tdd, aif-debug for the reproduced callback issue,
aif-bench and aif-verify. No delegation. Existing engines/shared validator,
tests and expected files are immutable; only new files plus registry/benchmark
registration are added. B3r remains final throughout this checkpoint.

New tests were authored against a NotImplemented validator/engine module.
Initial red 192427Z fails the first G1 case on the stub. Fast validation only
recognizes ordinary exact builtin fields, with liveness last; everything else
delegates to unchanged validate. Direct engine methods retain the inherited
API and validator; process inlines the old forwarding body. Matching only
binds stable references to locals; structures, thresholds, operation order,
fill dictionaries and counters are unchanged.

Green 192534Z:1,797,952 exhaustive validator comparisons with identical callback
traces, 1500 Hypothesis arbitrary JSON-like examples, and all 32 attack-generator
families counted/uncounted after every event (66 tests). Corpus: nine fields,
all field pairs, all prescribed odd/missing values, three event types, eight
expected_type variants, four sequence states and two live-id states, including
dict/str/int subclasses. Supplied-file selection includes six event streams
and excludes metadata sidecars; no input file is altered.

Corrected Codex defect: putting is_live inside the missing-field KeyError
handler retried a callback KeyError. Regression red 193456Z and green 193532Z
prove the callback now propagates once from outside that handler. Reference
validation stays unchanged; no expectation is weakened. Gate-sensitivity
evidence 194115Z kills three temporary in-memory mutants by AssertionError:
unsafe bool acceptance, reversed result-key order with equal values, and
counter-only drift. These probes are separate from the original 17 mutants.

Saved-row acceptance tests: red 193053Z (10 stub failures), green 193351Z
(10 passed), covering exact 10%/5% boundaries, losses outside the 15-cell score,
missing/stopped/partial/duplicate rows and mismatched input hashes. The
comparator requires all 57 timing pairs and 236 successful worker observations,
plus matching source-bound correctness proof. Synthetic saved rows are test
fixtures, never represented as measured performance.

Plan-only 193658Z: phase4_b3r_fast_20261122 measures B3r_fast only, official 180
workers + post_attack 56 = 236. No older engine is remeasured. Reference:
03_results/runs/20261122T130145Z_00bb1ad_phase4_b3r_20261122/.
try_b3r_fast.ps1 requires explicit -AllowLong and matching correctness evidence
for a real run; it compares saved results afterward. Exact preview/start
commands are in BENCHMARK_PLAN.md. No long run starts in this checkpoint.

Attack suite 193657Z: **1697 passed in 79.31s**, all six registered engines,
with --runxfail for the archived fixed ATK-01 markers. No attack source/test
is edited. Full standard gates also replay all complete supplied and own files,
with result/snapshot/quote comparisons after EVERY event, counted and
uncounted, plus both new and existing stateful differentials. Snapshot-copy
test duration is not an algorithm timing measurement or speedup evidence.

Final fresh standard run 193624Z: **848 passed in 648.79s**, no failures/errors/
skips/warnings. G2 verifies146,514 event-by-event comparisons across six full
supplied streams (five10k +worked example),18 own files and 32 attack families,
each counted and uncounted. All outputs and fill-key order, snapshots, quotes,
last_seq and counted state agree. Both required stateful machines pass (the
registry-driven A-vs-fast case and dedicated B3r-vs-fast case), configured 300
examples/60 steps, as do the old variants' stateful cases.

| Standard file / group | Passed |
|---|---:|
| test_contract.py | 384 (64 per registered version) |
| test_validation.py | 184 |
| test_mutants.py | 24 (17 kills, naming, six real controls) |
| test_own_datasets.py | 4 |
| test_replay.py | 21 |
| test_b_internal.py | 27 |
| test_stateful.py | 5 (A vs each B) |
| test_b3r.py | 6 |
| test_replay_regressions.py | 24 |
| test_bench_pipeline.py | 30 |
| test_post_attack_pipeline.py | 13 |
| test_fast_equivalence.py | 115 functions/parameters +1 B3r/fast stateful |
| test_fast_assessment.py | 10 |
| Total | 848 |

Source-bound proof `05_evidence/b3r_fast_correctness.json` records G1/G2/G3,
both complete suite XML hashes and source fingerprint
`f82455f1ced229fd6d5cffb29727b67b4cce1a53e6c6d7b649ce66d7f03dcbd2`.
[Proof creation](../05_evidence/20261122T194837Z_3c95836-dirty_b3r-fast-correctness-proof.txt)
and [final review](../05_evidence/20261122T194837Z_3c95836-dirty_b3r-fast-final-review.txt)
confirm all 848/1697 cases green, all required per-event coverage, every original
engine/validator/test/expected/data/result/attack path unchanged, and same
constructor/structures/public signatures/cleanup methods by identity.
AST comparison proves the inlined process body is identical after the
validator call, and matching is identical after undoing only local bindings.
The236-worker preview,57 full five-repeat B3r reference medians and 15-cell score
are verified. No new benchmark session exists. No timing conclusion is made.

Codex read the complete new fast/comparison/wrapper/test source and changed
docs for unrelated behavior, names/comments/content and the known injection;
no traces and no NEW embedded instructions found. Scope/whitespace checks pass;
dependency pins are unchanged. No deletes/installs, remote actions or git
mutations. B3r remains final. Exact benchmark start command and proposed git
paths/message are in BENCHMARK_PLAN.md; STOP before any long run for review.

## One binding same-session rematch (Laurin, 2026-11-22, BEFORE measuring)

Base ddbc434 commits the cross-session fast trial and its tried-and-rejected
decision. Laurin identifies session noise: B3r 20261122T130145Z buildup 10k s42
0.0233s and sweep 100k s43 0.2829s were around 2x faster than comparable old B
results/other seeds, while fast 20261122T200528Z was normal. The old per-cell 5%
comparison cannot isolate code effects. Its committed result is preserved and
will be reported unchanged alongside the rematch and this reasoning.

Decision recorded before any new measurement: ONE attempt, binding either
way, no further re-measurement. Same session, B3r+B3r_fast, official + post_attack,
timing only, unchanged warm-up+5. Per-case order alternates globally (B3r/fast,
fast/B3r), including the boundary after 45 official cases. Accept only with
current-source correctness gates, 15-cell official 100k geometric mean <= 0.90
and every workload x size median OF seed ratios <= 1.05 (single ratio if one
seed). Otherwise B3r remains final. No engine, test or expected-file changes.

Implementation adds a fixed atomic attempt claim, no retry/session override,
and immutable assessment output fast_rematch_acceptance.json. PlanOnly does
not measure/claim. A claim consumes the attempt even if interrupted or partial;
preflight failure before claiming performs no measurement. No rematch starts
in this build checkpoint. Apply aif-exercise/aif-bench and evidence verification.

New control-plane code only: ordered_requests preserves the default runner's
sort and alternates the explicit B3r/fast timing pair by global case rank.
The post-attack offset is 45, so its first pair (case 46) is fast/B3r. Every
timing worker retains fresh construction and warm-up+5, unchanged worker code.
No engine/shared validator/test/expected/data/old result file is edited.

Synthetic rule checks were written against NotImplemented helpers and failed
as expected (red 204557Z), then passed after implementation (green 204848Z).
They check parity/default order, exact 10%/5% limits, single-seed losses,
outlier robustness, median OF ratios rather than ratio OF medians, and missing
data. assess_rematch reuses the original completeness/input/15-cell checks and
replaces only the old per-cell 5% condition with the declared scenario median.
The original assessor and original rejection are unchanged.

Binding checks 205047Z use saved-row fixtures in isolated scratch directories:
a second atomic claim fails and leaves the first unchanged; accept, reject,
partial coverage, wrong order and wrong-source cases select the required final
version. Reassessment returns the first JSON byte-for-byte even if fixture
rows change afterward. Correctness proof verification is independently checked
with fresh complete suites, not inferred from these synthetic fixtures. No
real attempt marker/pointer is created by the checks.

Final plan-only preview 205140Z lists 90 official + 24 post-attack workers, timing
only, all 114 positions in the declared global alternation. It creates no books
or session. Memory-only cases do not enter the 57-case alternation. New assess
output includes old cross-session loss rows/decision/hash and new scenario
tables, numerical gates, correctness/source/claim/order/coverage and the binding
final-version decision. Existing result folders remain immutable.

Fresh verification after the final Python source change:

- [Standard suite](../05_evidence/20261122T205138Z_ddbc434-dirty_rematch-all-tests.txt): **848 passed in 713.71 s**, exit 0; no failures/skips. Includes all 17 mutant kills, reference/fast validator and every-event engine gates, plus both stateful differentials.
- [Attack suite](../05_evidence/20261122T205139Z_ddbc434-dirty_rematch-attack-suite.txt): **1,697 passed in 80.63 s**, exit 0, including B3r_fast.
- [New correctness proof](../05_evidence/b3r_fast_rematch_correctness.json): G1/G2/G3 true; source SHA-256 `4911010c34d0bd0f385c15fcfec9fb700db3b7e4859de57c4a7d1030b7569c64`, with hashes of both fresh XML reports. The original proof is untouched.
- [Final review](../05_evidence/20261122T210349Z_ddbc434-dirty_rematch-final-review.txt): independently verifies every preview position, default-order preservation, current-source proof, protected files and retained old rejection. No real attempt marker, session pointer or result folder exists.

Standard counts by file: contract 384, validation 184, fast_equivalence 115,
b_internal 27, b3r 6, mutants 24, own_datasets 4, replay 21,
replay_regressions 24, bench_pipeline 30, fast_assessment 10,
post_attack_pipeline 13, stateful 6 (five A-vs-B variants and B3r-vs-fast).
G1 reports 1,797,952 exhaustive comparisons; G2 checks supplied/own and all
32 attack stream families in both counter modes after every event.

Reviewed the full generated diff and both new source files for the logged
injection: no traces and no new embedded instructions. No engine/test/expected
or historical result changes, installs, dependency changes, moves or git
mutations. No new benchmark measurement; the sole attempt remains unused.
STOP for Claude (chat) review and Laurin's commit. B3r remains final pending
the one binding outcome; no performance claim from these correctness checks.
