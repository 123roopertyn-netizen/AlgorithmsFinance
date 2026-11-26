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
