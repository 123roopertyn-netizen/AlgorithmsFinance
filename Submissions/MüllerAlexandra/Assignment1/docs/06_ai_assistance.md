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

## Corrected so far

- The lecture's read-only, aggregated `FillMarketSell` is not the assignment
  engine: Assignment 1 requires individual FIFO makers and live-book mutation.
- The first sequence-state test rejected an event whose sequence equalled the
  last accepted sequence. That could not detect an erroneous state advance.
  Before implementation, it was replaced by an invalid sequence-3 event
  followed by a valid sequence-2 event, and float/Boolean sequence cases were
  added. Both pre-implementation runs remain preserved.
- The first baseline test attempt exposed an incorrect standard-library
  import: `AbstractSet` was imported from `collections.abc` instead of
  `typing`. The import was corrected before behavioral tests could run; no
  expected result or test was changed.

## Rejected so far

- None.

