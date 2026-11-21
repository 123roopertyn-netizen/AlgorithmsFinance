# Implementation and revision notes

## Complexity symbols and measurement boundary

- `B`: active resting orders at the operation being analyzed.
- `P`: occupied price levels at that operation.
- `M`: incoming events replayed from an initially empty book.
- `F`: makers filled by one incoming submission.
- `L`: occupied price levels exhausted by that submission, with
  `L <= min(F, P)`.

All costs below include validation, live-ID checks, state/index updates,
cleanup and construction of the current event's result. They exclude JSON or
gzip parsing. Producing `F` fill dictionaries necessarily costs `O(F)` time
and live result memory. A replay of `M` events is the sum of the individual
event costs at their changing `B`, `P`, `F` and `L`; it is not valid to treat
`M` as a proxy for active book size. Cancellation churn can have large `M`
while `B` remains zero or very small.

## Version A: transparent baseline

`BaselineOrderBook` keeps every active maker in one Python list. It searches
that list for the best eligible price and earliest sequence before every fill.
Cancellation and duplicate-live-ID detection also scan the list. This makes
the price-time rule easy to inspect and provides a deliberately simple
comparison version.

Simplified matching pseudocode:

```text
validate the complete event
while incoming quantity remains:
    scan all active makers
    select eligible best price, then smallest arrival sequence
    if no eligible maker: stop
    execute min(incoming quantity, maker quantity) at maker price
    reduce both quantities and remove an exhausted maker
rest a positive limit residual; discard a market residual
```

Validation of a limit or market submission includes an `O(B)` duplicate-live
scan. A noncrossing limit insertion is therefore `O(B)` even though appending
its residual is `O(1)`. A matching limit or market sell is `O(B*F)` in the
worst case because it rescans the active list for every maker and list removal
can also shift `O(B)` references. Constructing its ordered fills is `O(F)`.
Cancellation validation is `O(1)`, followed by an `O(B)` target scan/removal.
Canonical inspection is `O(B log B)`. The active book uses `O(B)` memory and
has no inactive entries or retained fill history; while a result is alive,
the operation additionally uses `O(F)` output memory.

## Version B: indexed price levels

`RevisedOrderBook` groups active makers by side and price. Each price level is
an insertion-ordered dictionary: its first value is the FIFO maker, while an
identifier can be cancelled directly. A separate active-order dictionary
provides live-ID lookup. Sorted integer price-key lists expose the highest bid
and lowest ask; negative ask keys put both best prices at the list end.

Simplified matching pseudocode:

```text
validate the complete event
while incoming quantity remains:
    read the best opposite price key
    stop if absent or not crossed
    take the first maker from that price-level dictionary
    execute at maker price and reduce both quantities
    remove an exhausted maker and eagerly delete an empty level
rest a positive limit residual; discard a market residual
```

Submission validation, including live-ID lookup, is `O(1)` average. Resting a
noncrossing limit at an existing level is `O(1)` average; creating a level is
`O(P)` because its key is inserted into a sorted list. A limit or market-sell
fill is `O(1)` average until it empties a level; eagerly deleting that price
key is `O(P)`. Matching plus ordered result construction is therefore
`O(F + L*P)`. Cancellation and its index updates are `O(1)` average unless the
target was the level's final maker, when price-key deletion makes it `O(P)`.
Canonical inspection is `O(B log B)`. Active storage is `O(B + P)`, with no
inactive/tombstone entries or retained fill history; a live result adds
`O(F)` output memory.

This design intentionally uses eager level cleanup instead of heap tombstones.
It avoids retaining cancelled orders or an unbounded stale-entry history in
the cancellation-churn workload. Sorted price-key maintenance is a candidate
bottleneck for the later measurements; no performance claim is made before
those measurements exist.

## Invariants supporting correctness

After every accepted event:

1. Every active identifier names exactly one positive-quantity resting order.
2. A baseline list position never defines priority; comparison uses price and
   original arrival sequence explicitly.
3. A revised price-level dictionary is insertion ordered, so its first maker
   has the smallest remaining arrival sequence at that price.
4. Revised price keys and level dictionaries have a one-to-one relationship;
   empty levels are removed immediately.
5. Matching stops before a noncrossing residual rests, so no resting bid
   crosses the best resting ask.
6. Every execution subtracts the same integer quantity from the incoming and
   maker quantities and records the resting maker's integer price.
7. Partial makers remain in place; full fills and cancellations remove the
   maker from every structure exactly once.
8. Validation finishes before mutation and only accepted events advance
   `last_accepted_seq`.

## Revision and test record

- At checkpoint commit
  `8788d13b6a59aadfa9785cbc31967dce2cc4e4fe`, the pre-implementation run had
  20 tests: four fixture/generator tests passed and 16 behavioral tests failed
  because the `orderbook` package was absent.
- The unchanged 20-test suite passed after Version A and Version B were added.
- Manual replay of the worked example produced the expected maker order,
  quantities, final book and `359400.00` USD proceeds in both versions.
- A review found that set membership on a list-valued `type` or `side` raised
  `TypeError` instead of returning a rejection. A regression test was added
  first and reproduced the error for both versions. Validation was then
  changed to establish string type before membership comparison.
- A second regression test cancels the middle maker in a same-price queue and
  confirms the surviving makers retain FIFO priority.
- The algorithm/fixture suite reached 22 passing tests after those regressions.
  A 23rd test now replays all 50,000 supplied events through fresh books; both
  versions must return equal results for every event and equal final canonical
  books.
- Ten additional tests cover deterministic measurement inputs, stable gzip
  storage, liquidation sizing, latency breakdowns, percentile convention,
  diagnostics, memory boundaries, report validation and explicit stopped-run
  labeling, including bounded liquidation correctness diagnostics. Two
  dashboard tests and two short-report tests verify required saved-result views
  and byte-stable generation. The complete suite now has 37 passing tests.

## AI use

OpenAI Codex assisted with implementation and review.

Accepted suggestions:

- centralize the frozen validation and result contract while keeping the two
  storage and matching algorithms separate;
- use integer-only matching and explicit price-time keys;
- use insertion-ordered price-level dictionaries plus an active-order index;
- add a regression test before correcting the unhashable-value crash; and
- replay identical supplied events through fresh instances of both versions;
- pre-generate checksummed benchmark inputs and separate timing, latency,
  operation counting and memory tracing; and
- build a dependency-free dashboard and report from saved results only.

Corrected suggestions:

- direct set membership was initially used for event `type` and `side`; this
  was corrected after a list-valued input exposed an unhandled `TypeError`;
  and
- the first short-report table omitted liquidation percentage, making three
  application-total rows appear duplicated; the percentage column and a
  regression assertion were added without changing measurements; and
- the first full canonical attempt revealed that liquidation correctness built
  the slow baseline outside its declared limit; a failing regression test was
  recorded, then construction, sale, and inspection were placed inside the
  same bounded diagnostic attempt with explicit stopped evidence.

Rejected suggestions:

- lazy heap deletion, because stale order/price entries complicate memory
  interpretation and can accumulate under cancellation churn;
- floating-point prices or quantities, because the assignment requires exact
  integer conservation; and
- an external matching-engine library, because the matching algorithms must
  be implemented in this project;
- presenting a dirty-tree smoke run as final evidence; canonical mode refuses
  that run until the measurement code has a clean recorded commit; and
- a third-party dashboard framework, because a self-contained offline HTML
  dashboard meets the saved-data requirement without extra dependencies.

Passing tests and cross-version agreement are evidence, not proof of
correctness. The benchmark and memory framework measures rather than assumes
that Version B is faster or smaller on every workload. Current smoke evidence
is provisional; canonical claims wait for a clean recorded code commit.
