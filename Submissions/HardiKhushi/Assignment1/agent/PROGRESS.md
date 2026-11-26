# Assignment 1 progress

## 1. Read-only review and organization (26 November 2026)

User approved inspection, then organization, then end-to-end completion while
retaining per-commit approval. Existing Assignment1 was empty; Git was clean at
ae01998ab1e03c20d5063fd96519d216854ede73 on audit/liuhaina.
All supplied substantive files matched their original manifest. Missing .DS_Store
is irrelevant macOS metadata and is not invented or added.
PDF text was read using macOS PDFKit because Poppler and Python PDF packages
were unavailable; no dependencies were installed.
Preserved source instructions/data, created an isolated Assignment1 layout,
working agreement, AI instruction/decision records and requirements checklist.
Earlier search algorithms, results and peer-audit evidence remain untouched.
No engine implementation has been written yet. No commit is authorized yet.

## 2. Tests before code

Stage 1 committed with explicit approval as 8270fac; post-commit status clean.
Wrote independent contract tests and deterministic workload checks before any
engine Python file existed. Executed the full suite: failures from missing
orderbook modules are preserved in results/evidence/tests_before.txt; exact
test hashes and return code in tests_before.json. Expected values cover the
worked sale, crossing limits, FIFO, residuals, cancellation, atomic validation,
long queues, generated sale oracles and per-event conservation/differential checks.
Generator checks execute independently of missing engines. No test result has
been weakened to accommodate an implementation.

## 3. Baseline implementation

Tests-first checkpoint committed with explicit approval as 35125e8; clean status
verified. Implemented Version A using a list of individual active orders and
explicit best-price/arrival scans, shared atomic validation/result formatting,
standard-library JSON/gzip reader and replay CLI. The revision did not exist
when the baseline suite ran. All 22 baseline-stage tests completed successfully
(21 passed; the revision comparison was explicitly skipped). Exact test file
hashes still match the red-run record. Log: results/evidence/tests_baseline.txt.

## 4. Revised price-queue implementation

Baseline committed with approval as 52a6c5e; post-commit status clean.
Preserved Version A; added Version B with sorted occupied prices, OrderedDict
FIFO queues and a live identifier index. Cancellation deletes immediately;
there are no stale orders or retained event/trade histories. Price-list updates
remain O(P), rather than claiming logarithmic insertion. OrderedDict avoids
repeated scans over deleted prefixes of a plain dict used as a FIFO queue.
All 43 tests passed, including unchanged original contract test hashes, 4,500
generated events compared after every event, quantity/maker conservation and
new storage/churn regression tests. Log: results/evidence/tests_revised.txt.

## 5. Measurement and evidence

Revision committed with approval as 3276644; post-commit status clean.
Added and passed four measurement-definition tests (47 total). The protocol
smoke run passed before the full experiment. Executed all 90 primary version/
scenario/seed/size configurations, plus construction/application, separate
tracemalloc and latency/counter/depth diagnostics, fixed fresh-book 10/100/200%
sales at 4/1000 available prices, and million-event streaming cancellation churn.
The same four-second wall deadline applied to both engines. Saved 2,478 raw/
diagnostic records, 257 timing summary groups and 642,536 per-event latency
samples. There were 48 stopped timed trials across phases; these remain labelled.
All original test hashes and 12 actual measured-source hashes match. Independent
verification recomputed medians/throughput, all saved percentiles, matrix coverage,
input checksums and memory invariants. All 47 tests passed again. Baseline/revised
completed medians paired in 33 cases: revision faster in 24 and slower in all
nine tiny-active-book churn cases. Million-event streaming parse and both engines
completed warmup plus five repetitions. Generated large inputs remain ignored.

Second verification exported each of the four approved commits: organization
had no engine; tests-only reproduced 37 expected missing-module errors out of
40 tests; baseline passed 21 with one skip; revision passed 43. Evidence is in
results/evidence/checkpoints/ and checkpoint_verification.json. The exporter
initially used a subfolder cwd for a repository-relative archive path; corrected
the helper, reran successfully, and did not change engines or measured results.
