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

## Corrected so far

- The lecture's read-only, aggregated `FillMarketSell` is not the assignment
  engine: Assignment 1 requires individual FIFO makers and live-book mutation.
- The first sequence-state test rejected an event whose sequence equalled the
  last accepted sequence. That could not detect an erroneous state advance.
  Before implementation, it was replaced by an invalid sequence-3 event
  followed by a valid sequence-2 event, and float/Boolean sequence cases were
  added. Both pre-implementation runs remain preserved.

## Rejected so far

- None.

