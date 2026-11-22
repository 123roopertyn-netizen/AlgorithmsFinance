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
