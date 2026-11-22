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

## Pending suggestions

- For Version B, consider an active-order dictionary, FIFO containers grouped
  by price, and heaps for locating the best bid and ask. This remains pending:
  it will be accepted, corrected, or rejected only after Version A is measured
  and the data structures, invariants, and trade-offs are reviewed.

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
- During the walkthrough, the user identified that the pre-implementation
  suite included the supplied worked example and hand-calculated contract
  cases but omitted the requested small generated streams. Four deterministic
  60-event streams and a separate test-only reference model had been added only
  after Version A and before Version B. The original evidence and expectations
  are preserved; the later tests are not represented as pre-Version-A tests.

## Rejected so far

- None.

