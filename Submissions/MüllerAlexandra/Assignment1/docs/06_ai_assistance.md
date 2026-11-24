# AI assistance

AI assistance is being used for repository structure, specification review,
test design, implementation review, measurement design, and documentation.
Each material suggestion will be recorded here as accepted, corrected, or
rejected with the reason and the verification performed.

## Accepted so far

- Separate independent expected-result tests from later differential tests.
- Preserve stage-specific test logs and machine-readable metadata.
- Keep importable Python modules unnumbered while numbering tests, commands,
  evidence, results, and documentation where ordering is meaningful.
- Add a project-local `.gitattributes` policy that keeps text files at LF and
  marks compressed/media files as binary. Git's Windows line-ending warnings
  and the earlier peer-audit reproducer showed why byte-stable checkouts matter.
- Use a list of individual orders for Version A so price-time behavior and
  state mutation remain directly inspectable. Preserve its whole-book scans,
  candidate sorting, and list-removal costs as the baseline rather than
  prematurely introducing the revised data structure.
- Add deterministic small generated streams before Version B. Each engine is
  checked event by event against a separate test-only reference model and
  visible state invariants, rather than treating agreement between submitted
  implementations as independent correctness evidence.
- Before benchmarking or Version B, the user proposed a critical review of
  whether the tests were meaningful and covered grading-relevant edge cases.
  AI audited the suite against the supplied contract and identified missing
  direct cases. The user accepted focused additions for nonincreasing
  sequences, required-field validation, sell-side symmetry, partial ask FIFO,
  canonical ordering, and empty/reopened price-level behavior. No earlier
  expected result was changed.
- Fix the measurement protocol before observing performance results. After a
  guided review and direct comparison with the lecturer's sources, the user
  accepted separate throughput, per-event latency, memory, and diagnostic
  runs; fresh state; saved raw repeats; explicit inclusion boundaries; and a
  test-first helper module.
- For memory measurement, AI proposed separate state-only and retained-output
  runs instead of mixing output-history allocation with the live book. The
  user accepted the test-first contract. Parsing remains outside tracing;
  book construction, state, temporaries, the current result, and fixed
  checkpoint bookkeeping are included; final inspection is outside tracing
  and is identified as diagnostic counting rather than measured allocation.
- AI proposed encoding the lecturer's workload requirements as a verified
  matrix before formal measurement. The user accepted 45 core inputs (five
  scenarios, three sizes, and three seeds) plus one controlled four-level
  buildup input. The copied generator was hash-checked against the lecturer's
  source; every explicit generation setting, metadata file, byte count, and
  checksum is verified before an input enters the saved plan.
- AI proposed a resumable formal runner with a 60-second per-configuration
  limit, applied identically to both versions. The user authorized proceeding
  with that preregistered limit and the explicit phase allocation. Completed
  results are checksum-validated before promotion; stopped tasks retain their
  reason and environment without a fabricated result.
- AI proposed a deterministic liquidation experiment with 1,000 makers over
  100 prices and independent 10%, 100%, and 200% fresh-book sales. The user
  authorized proceeding. The accepted contract separates construction and
  sale timing, retains fill output during sale-memory tracing, and supplements
  primary runs with five small correctness/count diagnostics.
- After reviewing the Version A measurements and walking through the data
  structures, the user accepted an active-order dictionary, per-price
  `OrderedDict` FIFO queues, and sorted occupied-price lists maintained with
  `bisect` for Version B. The revision removes repeated active-book ID-set
  construction, matching scans, and list removal by order position. It adds
  persistent indexes and an `O(P)` list-shift cost when a price level is
  created or removed. Its measured effect is intentionally left open until
  the unchanged formal protocol is rerun.
- AI advised against using a Version-B-only million-event run as comparative
  evidence. The user accepted a limited symmetric extension instead: seed 42,
  five workload families, throughput only, both versions, and the unchanged
  60-second limit. It is isolated from and explicitly dated after the original
  formal matrix; stopped baseline runs remain visible and are not assigned a
  fabricated speedup.

## AI-assisted output corrected so far

- AI specification review identified that the lecture's read-only, aggregated
  `FillMarketSell` is not the assignment engine: Assignment 1 requires
  individual FIFO makers and live-book mutation.
- AI review identified a flaw in the first AI-assisted sequence-state test: it
  rejected an event whose sequence equalled the last accepted sequence, which
  could not detect an erroneous state advance. Before implementation, the test
  was replaced by an invalid sequence-3 event followed by a valid sequence-2
  event, and float/Boolean sequence cases were added. Both pre-implementation
  runs remain preserved.
- The first baseline test attempt exposed an AI-generated incorrect
  standard-library import: `AbstractSet` was imported from `collections.abc`
  instead of `typing`. AI corrected the import before behavioral tests could
  run; no expected result or test was changed.
- The user requested that the proposed measurement procedure be checked
  directly against the lecturer's Assignment 1 PDF and supplied README before
  implementation. AI's source comparison found that the first draft did not
  explicitly name `time.perf_counter`, preserve construction/reset and input
  preparation costs, exclude AI calls, describe the streaming fallback, or
  enumerate the required dashboard evidence. The method was corrected before
  the measurement helpers or benchmark harness were implemented and before any
  performance result was observed.
- After the first latency smoke check, AI compared the implementation with the
  fixed measurement protocol and found that the latency branch ignored the
  configured untimed warm-up. The latency test contract was strengthened first:
  four failures were preserved, covering separate warm-up state, invalid
  warm-up counts, and saved settings. AI then implemented a warm-up on its own
  book followed by a fresh measured book, regenerated the non-formal smoke
  output, and reran the unchanged helper and harness tests. This correction was
  completed before formal measurements and did not change an expected engine
  result.
- Before committing the latency phase, the user requested a further critical
  review rather than accepting passing tests as sufficient. AI found that the
  shared `--repeats` option was silently ignored for latency, the tests covered
  only one warm-up, and the 10% window test did not exercise ceiling behavior.
  The user accepted strengthening the contract before implementation. The
  preserved failing run exposed those gaps; latency now performs five measured
  fresh-book repeats by default, retains repeat and event indices, pools
  within-repeat edge windows, and rejects malformed configurations and records.
- Before any formal pilot, AI review found that raw latency JSON could become
  unnecessarily large and that earlier saved results would make later Git
  metadata look code-dirty. The runner was corrected to save gzip-compressed
  raw JSON and to distinguish assignment-output changes from actual code or
  configuration changes. Timeout records were also strengthened to retain the
  stopping reason, environment, and code commit when no child result exists.
- During the walkthrough, the user identified that the pre-implementation
  suite included the supplied worked example and hand-calculated contract
  cases but omitted the requested small generated streams. Four deterministic
  60-event streams and a separate test-only reference model had been added only
  after Version A and before Version B. The original evidence and expectations
  are preserved; the later tests are not represented as pre-Version-A tests.

## Rejected so far

- AI's initial Version B suggestion included heaps for best-price lookup. That
  part was rejected after the Version A cancellation-churn evidence was
  reviewed: standard lazy deletion can leave stale heap entries whose memory
  grows with level turnover rather than the live book. Sorted unique price
  lists were selected instead. They keep no stale entries and make the
  `O(P)` creation/removal trade-off explicit.

