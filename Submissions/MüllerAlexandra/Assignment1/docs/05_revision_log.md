# Revision log

## Version A: transparent baseline

Version A stores active individual orders in one list. It builds an active-ID
set for validation, scans and sorts eligible makers for each incoming order,
and linearly scans for cancellations. This design was selected for transparent
price-time behavior rather than expected performance.

The baseline-selected contract has 53 passing tests: the original 49 plus four
deterministic generated-stream cases. All five supplied 10,000-event workloads
replay with zero rejected events and valid final canonical books. The first
test attempt exposed and corrected an import error before behavioral tests
ran; no expected result changed.

Before beginning Version B, four deterministic 60-event streams were added.
They use seeds 3, 17, 42, and 99 and compare every event result and canonical
book with a separate test-only reference model. The earlier hand-calculated
expectations remain unchanged. At this checkpoint, the full suite has 54
passes and 51 expected failures, all caused by the intentionally unimplemented
Version B methods or the differential test that invokes Version B.

## User-requested critical review before Version B

Before benchmarking or revising the engine, the user requested a critical
review of whether the tests would withstand grading scrutiny. The review found
gaps in direct nonincreasing-sequence coverage, required-field validation,
sell-side hand-calculated symmetry, partial ask priority, canonical ordering,
and price-level cancellation/reopening behavior. Focused cases were added
without changing any earlier expected result.

The strengthened Version A selection now has 76 passing tests. These additions
were made after Version A and are not represented as pre-Version-A evidence;
they establish a stronger behavioral contract before Version B. The full
pre-revision suite has 77 passes and 74 expected failures, with every failure
caused by the intentionally unimplemented Version B or the differential test
that invokes it.

No Version B algorithmic revision has been made yet. The measured bottleneck,
revision rationale, and tests added for discovered cases will be recorded
without weakening earlier expected outcomes.

## Measurement infrastructure before Version B

Throughput, repeated per-event latency, and memory measurement were implemented
test-first before formal Version A results were inspected. Memory uses separate
state-only and retained-output modes. Its traced boundary excludes preloaded
input but includes empty-book construction, live state, temporary allocations,
the current result, and fixed checkpoint bookkeeping. Final book inspection is
outside tracing. Non-formal 100-event smoke records exercise cancellation churn
and buildup only to validate the harness; they are not used to justify Version
B or claim a performance improvement.

