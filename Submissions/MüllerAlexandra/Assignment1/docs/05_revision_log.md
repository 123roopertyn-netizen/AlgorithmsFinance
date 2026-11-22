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

No Version B algorithmic revision has been made yet. The measured bottleneck,
revision rationale, and tests added for discovered cases will be recorded
without weakening earlier expected outcomes.

