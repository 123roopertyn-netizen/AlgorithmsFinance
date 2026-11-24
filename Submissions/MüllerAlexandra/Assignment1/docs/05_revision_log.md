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

The formal runner was fixed before any Version A pilot. It preregisters 114
tasks per version and applies a 60-second wall-clock limit to every child
configuration. Validated results are promoted atomically from pending paths as
gzip-compressed JSON. Timeout and failure statuses remain visible with their
environment and code version; they never contain an inferred result.

The remaining Version A stress method was fixed before execution: a
1,000-maker, 100-level deterministic bid book is rebuilt for every 10%, 100%,
and 200% sale, with construction, sale, and sale-memory boundaries kept
separate. Five 1,000-event diagnostic streams provide operation counts and
final invariant checks outside primary timing.

## Version B: indexed FIFO price levels

Formal Version A results identified active-book size, rather than historical
event count alone, as the relevant bottleneck. Buildup latency rose strongly
from early to late windows and large active-book runs timed out, whereas the
100,000-event cancellation-churn workload completed while retaining almost no
active orders. This supports revising the repeated `O(B)` scans and list
shifts.

Version B therefore uses an active-order dictionary, one `OrderedDict` FIFO
queue per occupied side and price, and sorted occupied-price lists maintained
with `bisect`. An earlier heap proposal was not adopted: lazy heap deletion
would permit stale price entries to accumulate during cancellation churn.

After implementation, the complete unchanged suite plus the pre-revision
contract tests passes: 214 tests. The five supplied 10,000-event streams also
replay under Version B with zero rejected events and valid final books. No
Version B speed or memory improvement is claimed at this checkpoint; the same
preregistered formal tasks and stress settings must be rerun first.

## Optional million-event extension

After both formal matrices and stress runs were saved, the README's request to
try one million events if feasible was revisited. A separate paired extension
was selected: throughput only, seed 42, all five workload families, and both
versions under the existing 60-second limit. The original matrix remains
unchanged. Three extension-contract tests were preserved failing before the
harness existed and then passing as part of the 217-test full suite.

