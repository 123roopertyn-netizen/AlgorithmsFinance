# Assignment 1 — BTC limit order book

Name: Stéphane Martin Ambassa

Build and compare a Baseline and a Revised sequential BTC limit order book.
The teacher's instructions are in [ASSIGNMENT.md](ASSIGNMENT.md).

## Current status

BaselineOrderBook retains its original list-based implementation. RevisedOrderBook
uses an active-order ID index, FIFO deques by price, bounded price heaps and lazy
cancellation of non-head queue entries.

A successful cancellation removes its ID immediately and returns the remaining
quantity. Inactive queue entries cannot match or appear in canonical snapshots.
Per-price live-order counts drive bounded cleanup, including behind a live head.

Both versions share routing, validation, integer arithmetic and matching rules.
The original 49 behavioral tests remain unchanged. Heap regressions distinguish
live orders from inactive entries; lazy-cancellation regressions cover the new
storage and cleanup behavior. The benchmark runner is documented below.

## Baseline design

The Baseline stores individual resting orders in a list. It scans for the best
opposite-side price and earliest arrival at that price for each maker fill.
Executions use integer quantities and the resting maker's price. A partial maker
retains its arrival sequence; an exhausted maker is removed. Incoming limit
residuals rest, while market sell residuals are returned without resting.

Validation completes before changing the book or accepted sequence. Unknown
cancellations are accepted with not_found; rejected events leave both unchanged.
Inspection returns independent dictionaries in canonical price-time order.

With B active orders at the start of an operation and F maker fills:

- Live-ID lookup and cancellation scan the list: O(B).
- A limit or market sell takes O((F + 1) * B), including scans and removals.
- Inspection sorts and copies the active orders: O(B log B) time and O(B) output.
- Live storage is O(B); the current event's returned fill list uses O(F) space.

These are algorithm bounds, not measured benchmark results.

## Revised, stage 4: lazy order cancellation

The previous stage removed arbitrary orders with deque.remove(), an O(Q) search.
Revised now removes the live ID immediately without searching for its deque
position. A cancelled non-head object may stay in its queue until head pruning,
compaction or deletion of an inactive price level.

### Live orders and retained objects

orders_by_id is authoritative. A queued object is active only when:

~~~text
book.orders_by_id.get(order["order_id"]) is order
~~~

The identity check matters if an identifier is reused after its earlier order
has left the live index: an older retained object with the same ID remains
inactive. No active flag or additional fields are added to public order snapshots.

bids_by_price and asks_by_price contain only price levels with at least one live
order, but their deques can also contain inactive entries. _bid_live_counts and
_ask_live_counts hold active order counts at each price, not BTC quantities.

Canonical inspection iterates only the live ID index, so inactive objects never
appear in snapshots. Their old remaining quantities do not represent live depth.

### Cancellation, matching and FIFO

1. Validation completes before any mutation. The accepted sequence and every
   internal index remain unchanged when an event is rejected.
2. Cancellation finds the order through orders_by_id. Removing that ID and
   decrementing its price's live count are expected O(1) operations. The result
   returns the target's remaining quantity, including after partial fills.
3. If the removed object is at the deque head, popleft() removes it directly.
   Otherwise it remains as an inactive entry: no search or deque.remove() occurs.
4. Best-maker selection discards inactive head entries before returning a live
   maker. A partial maker keeps its object, price and original arrival sequence.
   A fully filled maker is removed from the live index and queue head.
5. Compaction filters inactive objects without reordering or copying the live
   order objects. Active FIFO is therefore preserved through cleanup.

Unknown, already cancelled and fully filled orders return not_found with zero
cancelled quantity. Incoming limit residuals still rest at the limit; market
sell residuals never enter the book. Trades still use the resting maker's price.

### Bounded queue cleanup

For one price, let L be its live-order count and R its retained deque length.

- If L becomes zero, clear the deque and delete the price from its live price
  dictionary and live-count dictionary immediately.
- Otherwise, when R > 2 * L + 32, retain only active objects using a stable filter.
- Before returning a maker, discard inactive objects at the deque head.

After each public event, every retained queue has L > 0 and R <= 2 * L + 32.
A single old active head therefore cannot hide unbounded cancellation garbage:
with one live head, its deque holds at most 34 entries. The live counts allow
this threshold check without scanning the queue on every cancellation.

The stable filter uses a temporary list of the L active objects, then clears and
extends the same deque. Cleanup preserves the original order objects and active
arrival order. Each removed inactive entry is released by one cleanup path.

Across the book, retained queue entries are bounded by 2 * B + 32 * P, where B
is active orders and P is active price levels across both sides. This bounds
storage by current live state rather than the historical number of cancellations.

### Price heaps and recreated levels

The previous price-heap policy is retained. Ask heaps contain positive prices;
bid heaps contain negated price keys. Live price dictionaries are authoritative,
and retained-key sets prevent duplicate heap keys on price recreation.

Per side, with P active price levels and H retained heap entries, rebuild when
H > 2 * P + 32, and clear the heap and retained-key set when P becomes zero.
Deleting a price because its live count reaches zero can trigger this maintenance.

A recreated price receives a new empty deque and live count, reusing a retained
heap key if present. No inactive order or old FIFO position is revived. Inactive
price keys are removed when they reach the heap root or during rebuilding.

### Integer representation

The number representation and shared matching arithmetic are unchanged:

- price_ticks is a positive built-in Python int in USD cents per BTC.
  USD 60,000 is 6000000 ticks.
- qty_units is a positive built-in Python int in units of 10^-8 BTC.
  One BTC is 100000000 units.
- seq is a strictly increasing positive built-in Python int.

Floats, booleans and nonpositive submitted numeric values remain rejected.
No matching arithmetic converts through floats. Active quantities stay positive;
an unfilled result may correctly report zero residual after a complete execution.

### Tiny lazy-cancellation example

~~~python
from order_book import RevisedOrderBook

book = RevisedOrderBook()
for seq, order_id, quantity in (
    (1, "Z", 200_000_000), (2, "M", 100_000_000), (3, "A", 100_000_000)
):
    book.process_event({
        "seq": seq, "event_id": f"add-{order_id}", "type": "LIMIT",
        "order_id": order_id, "side": "BUY",
        "price_ticks": 6_000_000, "qty_units": quantity,
    })

cancel = book.process_event({
    "seq": 4, "event_id": "cancel-M", "type": "CANCEL",
    "target_order_id": "M",
})
assert cancel["cancelled_qty_units"] == 100_000_000
assert "M" not in book.orders_by_id
assert [order["order_id"] for order in book.bids_by_price[6_000_000]] == ["Z", "M", "A"]
assert [order["order_id"] for order in book.inspect_book()["bids"]] == ["Z", "A"]

first = book.process_event({
    "seq": 5, "event_id": "partial-Z", "type": "MARKET_SELL",
    "order_id": "S1", "qty_units": 100_000_000,
})
assert first["fills"][0]["maker_id"] == "Z"
second = book.process_event({
    "seq": 6, "event_id": "finish-book", "type": "MARKET_SELL",
    "order_id": "S2", "qty_units": 200_000_000,
})
assert [fill["maker_id"] for fill in second["fills"]] == ["Z", "A"]
assert book.orders_by_id == {}
assert book.bids_by_price == {}
assert book.bid_price_heap == []
~~~

M remains physically queued below the cleanup threshold but is absent from live
depth. It never executes. Z retains priority after its partial fill, and A follows.

### Expected, amortized and worst-case costs

Let R be the target deque's retained length, L its live count, P active price
levels on the relevant side, H retained heap entries, and B total live orders.
The following expected costs use expected O(1) dictionary/set operations.

| Work | Cost |
| --- | --- |
| Find an active order and remove its ID | Expected O(1) |
| Decrement its price's live count | Expected O(1) |
| Remove the exact deque head, if applicable | O(1) |
| Skip T inactive queue heads during maker selection | Expected O(T) |
| Compact one price queue | Expected O(R), with O(L) temporary references |
| Clear an inactive-only price queue | O(R) reference cleanup |
| Discard S stale heap roots | O(S log(H + 1)) |
| Rebuild a price heap and its retained-key set | O(H + P) |
| Canonical snapshot | O(B log B) time and O(B) output |

Logical cancellation is expected O(1), without a deque-position search. The
complete cancellation operation can additionally compact a queue, clear an
inactive level, or rebuild a heap. An individual cancellation can therefore cost
O(R + H + P) under the expected hash-operation model. Guaranteed O(1) cancellation
latency is not claimed.

Queue compaction is amortized over accumulated inactive entries: it runs only
after inactive entries outnumber live entries plus the slack. Stable filtering
and head pruning remove each inactive object once; their aggregate queue-cleanup
work can be charged across the order lifecycle. The occasional linear scan is
still visible in a particular cancellation or fill. Heap rebuilding is likewise
amortized across stale price keys, while each stale-root pop costs logarithmic work.

The live-count, queue and heap bounds keep engine storage O(B + P + H), hence
O(B + P + 1) with the per-side heap bounds. Cancelling behind an old live head does
not retain storage proportional to event history. Snapshots and comparison-mode
copies are additional returned/verification storage.

Worst-case cleanup pauses, heap maintenance and snapshot sorting remain
limitations. This stage contains no timing or memory benchmark claims.

### Verification for this stage

The starting revision was 1a9f776 with a clean working tree. Python 3.14.5 ran the
same original 49 tests before and after the change.

| Original suite mode | Before lazy cancellation | After lazy cancellation |
| --- | --- | --- |
| Baseline | 49 passed | 49 passed |
| Revised | 49 passed | 49 passed |
| Compare | 49 passed | 49 passed |

All six runs had zero failures, errors or skips. The Baseline class source hash
was unchanged, and the entire original test_order_book.py file was byte-for-byte
unchanged, including all assertions and expected results.

Ten new lazy-cancellation regressions were added and run before implementation.
Against the previous eager code, four methods produced eight side-specific
assertion failures: the no-scan probe detected deque.remove(), and the retention
checks confirmed the old implementation still removed entries eagerly. There
were no test errors in that expected red phase. After implementation, all 10 pass.

All 10 existing heap regressions passed before and after. Their internal queue
checks now distinguish live objects from inactive retained entries and verify
per-price live counts and queue bounds. Raw-state rejection checks include those
counts. Active FIFO views filter by object identity. Public expected results and
all other heap test method assertions were audited unchanged.

Every focused-test event uses ComparedOrderBook, comparing ordered results and
canonical snapshots against Baseline. Coverage includes cancelled makers never
executing, partial-maker FIFO through compaction, partial cancellation quantities,
not_found results, price recreation, identifier reuse without ghost execution,
large exact integers, rejected-event atomicity and bounded churn behind old heads.

Additional checks verified the same live-queue, heap, ID-index and count
invariants after 3,000 generated events across all five scenarios and seeds
42, 43 and 44. The runnable lazy-cancellation example above also passed.
These are correctness checks, not timing or memory benchmarks.

## Benchmark runner

benchmark.py uses only the standard library. It measures the implemented Baseline
and Revised directly. The dashboard is a later stage. Run these commands from
this Assignment1 directory.

### Reproduce the smoke and small path checks

Use a new output directory for each run; existing results are never overwritten.

~~~console
python -B benchmark.py run --counts 1000 --seeds 42 --scenarios buildup crowded mixed sweep cancel_churn --experiments replay --out results/smoke_repeat --worker-seconds 60 --campaign-seconds 300 --label smoke-validation
python -B benchmark.py run --counts 120 --seeds 42 --experiments market-sell queue-concentration cancel-churn --out results/small_repeat --worker-seconds 60 --campaign-seconds 300 --label small-path-validation
python -B -m unittest -v test_benchmark
python -B -m unittest -v test_order_book test_price_heaps test_lazy_cancellation
~~~

### Prepare the required larger campaign

The saved results/full_campaign_plan.json describes 45 workload cases:
five scenarios, counts 1000/10000/100000, and seeds 42/43/44. Each case runs
both versions, giving 90 version cases. Planning does not generate or measure data.
These larger preparation and execution commands are provided for later use;
they have not been launched in this stage.

~~~console
python -B benchmark.py plan --out results/full_plan_repeat.json
python -B benchmark.py prepare --out results/full_prepared.json
python -B benchmark.py run --out results/full_campaign --worker-seconds 3600 --campaign-seconds 86400 --label full-campaign
python -B benchmark.py run --experiments market-sell queue-concentration cancel-churn --out results/full_experiments --worker-seconds 3600 --campaign-seconds 86400 --label full-experiments
~~~

Defaults select the required three counts, three seeds, five scenarios and both
versions. --versions accepts only baseline and revised. --experiments defaults
to replay. The controlled experiments use the same counts and seeds by default.
The extra experiment names use hyphens; the supplied cancel_churn scenario uses
an underscore.

All selected missing datasets are generated before measurement starts. Matching
supplied data files are reused only after metadata and SHA-256 checks. Files with
other settings are preserved; newly generated files and their metadata go under
data/benchmark/. Replay workloads use generate_orders.events and its supplied
write_stream function. The controlled passive bid books and anchored churn stream
use benchmark.py generators and the supplied write_stream; metadata identifies
their distinct construction. Teacher fixtures, including worked_example.jsonl
and worked_expected.json, are preserved.

### Measurement boundaries and calculations

Every primary timing case has one untimed full warm-up and five measured
repetitions. Each repetition constructs a fresh empty book. Events are loaded and
validated before engine timing. Garbage collection is enabled and explicitly run
before each repetition, outside the timing clocks. Book destruction is also
outside primary timing. Worker startup, imports, validation, checksums, writing
results, canonical inspection, comparison mode and diagnostic counters are excluded.

Separate I/O workers measure binary file reading, gzip decompression, and UTF-8
decoding/JSON parsing with time.perf_counter(). Validation is outside these clocks.
Decompression is null for uncompressed input. I/O uses an untimed warm-up and five
repetitions, so these are warm-cache measurements; no cold-cache claim is made.

Primary timing reports initialization_seconds separately. Ordinary replay has
construction_seconds=null; controlled sales time their setup order submissions
as construction_seconds. replay_seconds times only the measured stream or sale.
All event processing uses process_event(). Returned results are immediately
discarded during replay, including their destruction. A single-sale result is
retained until its clock stops so fills and residual can be recorded afterward.

~~~text
total_compute_seconds = initialization_seconds + (construction_seconds or 0) + replay_seconds
throughput_events_per_second = processed_events / replay_seconds
~~~

The total is calculated within each raw repetition, then summarized by its median.
It is not the sum of component medians. I/O is reported separately; independent
medians are not presented as an end-to-end wall time. A zero-duration clock sample
produces null throughput rather than infinity.

Latency is a separate instrumentation run, with a clock around each event call.
Appending samples happens after the clock. Ordinary replay supplies one sample
per event in one instrumented pass. Each controlled single-sale case supplies five
samples using fresh identical books. Clock overhead is not subtracted. The median
averages the middle pair for even sample counts; P95 and P99 use nearest rank:
sorted_samples[ceil(p * sample_count) - 1], without interpolation. All raw samples
are saved beside their worker checkpoints with event_id, sequence and repetition.
Instrumented latency is never used as primary replay time.

Memory uses tracemalloc in a separate worker process, with five independently
traced fresh-book repetitions. Loading, imports and warm-up precede tracing.
The reported incremental allocations include book construction, setup, matching,
temporary fill results and cleanup. Preloaded input objects, result-history storage
and canonical snapshots are excluded; the runner saves no event-result history.
Orders can reference existing input strings/integers, whose earlier allocations
are therefore excluded. Current bytes are sampled after garbage collection while
the book remains alive; peak bytes include transient allocations and memory-run
instrumentation. This measures traced Python allocations, not total process RSS
or native allocator reservations. Construction and churn checkpoints are separate.

A diagnostic run records active-order and occupied-price peaks after every event.
It also records retained queue and heap entries separately from live orders.
Ordered-result and final canonical-book digests are checked between versions.
Fill counts, rejected-event counts, cancelled quantities and residual quantities
come from this run, outside primary replay timing. Stream quantities are sums of
the corresponding returned fields (including limit residuals); sale quantities
refer to that one sale. Baseline retained entries describe list storage, and its
heap metrics are null.

### Controlled experiments

- market-sell: build the same passive BUY book afresh, then sell 10%, 100% or 200%
  of its available quantity. Requested quantity is (depth_units * percent + 99) // 100:
  integer ceiling avoids zero-unit requests and float rounding. Setup and matching
  have distinct clocks. processed_events is one, so throughput is sales per second.
- queue-concentration: keep order count, quantities and arrival order identical,
  comparing requested 4 versus 1000 levels and an exact-depth sale. Actual occupied
  levels are min(order_count, requested_levels). Counts at least 1000 exercise the
  full 4-versus-1000 comparison; the 120-order path check has 4 versus 120 levels.
- cancel-churn: keep an old active head at one price, insert and cancel younger
  orders, then cancel the head. N requested pairs produce 2*N+2 events. Diagnostics
  and memory capture both the state before that final cancellation and the empty
  book afterward. This tests retained storage even when the queue head stays live.

Prices, quantities and sequences remain positive built-in Python integers in the
existing cents, 10^-8 BTC and sequence units. Matching arithmetic is unchanged.
Only clocks and statistics use floating-point values.

### Executed price levels for a measured sale

price_levels_visited counts distinct executed prices in one measured sale:

~~~python
len({fill["price_ticks"] for fill in result["fills"]})
~~~

It is zero when the sale has no fills. Several makers at the same price count as
one level; a price counts only if a fill actually executes there. This is separate
from fill_count (maker executions) and actual_controlled_price_levels (initial
occupied prices). An oversized sale counts executed levels while its unsold
remainder is reported separately in unfilled_qty_units.

For market-sell and queue-concentration cases, timing raw rows calculate this
count after the primary replay timer stops, alongside fill count and residual.
Diagnostic sale rows calculate it in the separate untimed phase. Summaries report
the median of complete repetitions, and Baseline/Revised diagnostic comparisons
explicitly check it. I/O, latency, memory and ordinary replay rows use null; their
measurement phases and result-disposal behavior are unchanged. Market prices,
quantities and sequences retain their existing built-in integer representation.

Reproduce the correction checks using new output directories:

~~~console
python -B -m unittest -v test_order_book test_price_heaps test_lazy_cancellation test_benchmark
python -B benchmark.py run --counts 1000 --seeds 42 --scenarios buildup crowded mixed sweep cancel_churn --experiments replay --out results/smoke_price_levels --worker-seconds 60 --campaign-seconds 300 --label smoke-validation
python -B benchmark.py run --counts 120 --seeds 42 --experiments market-sell queue-concentration cancel-churn --out results/small_price_levels --worker-seconds 60 --campaign-seconds 300 --label small-path-validation
~~~

If an output directory already exists, choose a new name. Previously recorded
benchmark results are historical and are not rewritten with this new metric.

Correction verification started from a clean checkout of 3f97e5e. The complete
command above passed all 89 tests: the original 69 correctness tests and 20
benchmark tests. Five focused tests were added, preserving all 15 earlier benchmark
test methods and their assertions. Hand-built cases independently expect 1, 3, 3
and 0 executed levels for same-price makers, multiple prices, an oversized sale
and a sale with no bids, respectively. The clock-boundary test checks that fill
prices are read only after the primary timer has stopped. A comparison regression
also detects a level-count mismatch even when the result/book digests agree.

Both requested repeat campaigns completed, with five timing repetitions per
version/case and all five measurement phases retained:

| New results directory | Phase jobs | Raw rows | Summary rows | Diagnostic comparisons |
| --- | ---: | ---: | ---: | ---: |
| results/smoke_price_levels | 45 | 145 | 45 | 5 passed |
| results/small_price_levels | 54 | 174 | 54 | 6 passed |

Representative sale results below agree for Baseline and Revised, every timing
repetition, and diagnostic records. Residuals use integer quantity units:

| Case, 120 initial orders | Maker fills | Executed price levels | Unsold qty_units |
| --- | ---: | ---: | ---: |
| Market sell, 10% | 12 | 12 | 0 |
| Market sell, 100% | 120 | 120 | 0 |
| Market sell, 200% | 120 | 120 | 5917000000 |
| Queue concentration, 4 prices, exact-depth sale | 120 | 4 | 0 |
| Queue concentration, 1000 requested / 120 actual prices, exact-depth sale | 120 | 120 | 0 |

The saved audit independently consumes the input orders in integer price-time
order to check each sale's level count, maker count and residual, then checks all
raw records, summary medians, worker checkpoints and diagnostic comparisons. It
also verifies the current source hashes, reviewed HEAD and dirty working-tree
metadata in both manifests. All 263 protected engine, generator, dispatcher,
existing correctness-test, workload and prior-result files remain unchanged.

The report and its input snapshot are saved under results/small_price_levels/.
With the recorded code and checkout unchanged, rerun the audit using:

~~~console
python -B results/small_price_levels/audit.py
~~~

See results/small_price_levels/verification.json for the complete audit. These
remain smoke and small-path validation runs; no larger campaign was launched.

### Artifacts, provenance and limits

Each results directory contains manifest.json, raw.jsonl, summaries.jsonl and
workers/ checkpoints, job descriptions and raw latency samples. Every raw row
identifies case, experiment, phase, version, scenario, seed, requested count,
actual event count, levels and repetition. Unused metrics are explicit JSON null.
Shared I/O rows have version=null. Summary rows contain medians of complete raw
repetitions, plus expected and completed repetition counts. Single-pass latency
and diagnostics summaries have one aggregate row. No incomplete group receives
a fabricated median.

The manifest records Python, standard-library/zlib versions, OS/machine details,
clock resolution, code Git revision and dirty state, source-file SHA-256 values,
workload settings/checksums, worker environment and measurement boundaries.
No third-party dependency is required. PYTHONHASHSEED=0 is fixed for workers,
bytecode writing is disabled, and version order alternates across cases.

Default limits are 60 seconds per worker, 1800 seconds for the measurement
campaign, 128 MiB for each compressed/decoded input payload, and 512 MiB of
traced allocations in memory runs. Override with --worker-seconds,
--campaign-seconds, --payload-mib and --traced-mib. Workload generation precedes
the measurement deadline and has no separate timeout. The allocation cap is
checked between events, so one event can exceed it before detection. There is no
OS RSS hard cap. Large Baseline runs or diagnostics may exceed the chosen wall
limit: increasing it is an explicit choice, not a promise of completion.

A timed-out worker is terminated. Completed repetitions survive in checkpoints;
remaining repetitions are stopped with null measurements. Jobs past the campaign
deadline are not_run, and failing workers report error. Such summaries and the
campaign are marked incomplete and the command exits with code 2. Output
serialization and process launch time are outside primary measurements.

### Smoke verification on 2026-11-25

On Python 3.14.5, results/smoke_1000_seed42 completed all five scenarios at
1000 events and seed 42, both versions, with five primary timing repetitions.
All 45 phase jobs completed: 145 raw aggregate rows and 45 summary rows, plus
10000 individual latency samples. All five diagnostic result/book comparisons
passed, with zero rejected workload events.

| Scenario | Baseline median replay, ms | Revised median replay, ms |
| --- | ---: | ---: |
| buildup | 53.830 | 2.739 |
| crowded | 55.104 | 2.337 |
| mixed | 9.453 | 2.422 |
| sweep | 60.618 | 3.417 |
| cancel_churn | 1.909 | 2.044 |

These are local smoke measurements, not completed larger-campaign evidence or a
general performance ranking. The supplied cancellation stream usually has almost
no standing depth, which differs from the anchored churn experiment. Detailed
latency, throughput, initialization, memory and diagnostic metrics are in the
machine-readable summaries.

results/small_experiment_validation completed all six controlled cases on small
120-order books / 120 churn pairs: 54 phase jobs, 174 raw aggregate rows and
54 summary rows. All six cross-version diagnostic comparisons passed. Revised
churn peaked at 35 retained entries while two orders were live; before final
cancellation it held 19 entries for one live order (18 inactive), then zero.
Median traced current memory fell from 7200 to 1672 bytes across that final
cancellation; Baseline fell from 792 to 424 bytes. These include the respective
empty-book structures and are incremental allocation measurements.

The existing 69 correctness tests passed before and after the benchmark work.
All 15 benchmark checks passed, including independently known throughput,
percentiles, exact integer sale quantities, medians of compute totals, fresh-book
clock boundaries, checkpoint recovery and storage bounds. The engine, generator,
three existing test files and 12 supplied data/reference files were verified
byte-for-byte unchanged. See results/verification.json for the recorded audit.


## Common interface

Both versions expose:

- process_event(event): return the current event's result.
- inspect_book(): return {"bids": [...], "asks": [...]}.
- AddLimitOrder(event), FillMarketSell(event), CancelOrder(event): public handlers.

Each resting order contains order_id, side, price_ticks, qty_units and arrival_seq.
Bids sort by descending price, then arrival sequence. Asks sort by ascending price,
then arrival sequence. One BTC is 100,000,000 quantity units; one price tick is
$0.01 per BTC.

The validation tests require positive built-in integers for prices, quantities
and sequences, excluding booleans, floats and other numeric types. Sequences must
increase after accepted events. Missing required fields, invalid values and
duplicate live submission IDs are rejected without changing the book or consuming
the rejected sequence. event_id must be a nonblank string; results preserve the
supplied ID rather than deriving it from seq.

## Run tests

Use Python 3.11 or newer. The test runner uses only the standard library.
Open a terminal in this Assignment1 folder.

Run all 69 tests in one command:

~~~console
python -B -m unittest -v test_order_book test_price_heaps test_lazy_cancellation
~~~

This runs the original 49 tests in their default Compare mode, plus the 10 heap
and 10 lazy-cancellation regressions. Both regression suites also compare Revised
against Baseline. The combined command was verified with all 69 tests passing.

To run the original 49 tests with an explicit version, use:

~~~console
python -B test_order_book.py --implementation baseline
python -B test_order_book.py --implementation revised
python -B test_order_book.py --implementation compare
~~~

The default is compare. It gives separate copies of each event to Baseline and
Revised and compares ordered results and full canonical books immediately after
each event, including rejected events. Numeric types must also agree: 1, 1.0 and
True are different. Rejection reason wording may differ, but each version must
return a nonempty reason.

Run one category:

~~~console
python -B test_order_book.py --implementation compare --category market-sells
~~~

Selectors: market-sells, price-time, limit-orders, cancellations, validation,
integration. Omitting --category runs all six categories.

Run the focused heap regression tests separately:

~~~console
python -B -m unittest -v test_price_heaps
~~~

Run the lazy-cancellation regressions:

~~~console
python -B -m unittest -v test_lazy_cancellation
~~~

Optional, if pytest is already installed:

~~~console
python -m pytest -q test_order_book.py
~~~

Pytest discovery uses comparison mode by default. The original independently
calculated market-sell expectations remain part of the suite.

## Replay event files

The external dispatcher exposes replay_file(path, book). It reads .jsonl or
.jsonl.gz files, calls the supplied book's process_event() in file order, and
returns the event results in that order. In comparison mode, both versions are
checked after every replayed event.

~~~console
python -B dispatcher.py data/worked_example.jsonl --implementation baseline
python -B dispatcher.py data/worked_example.jsonl --implementation revised
python -B dispatcher.py data/mixed_10000.jsonl.gz --implementation compare
~~~

The command prints the selected implementation, ordered results and final book.
Its saved result list is additional replay storage, separate from the live book.

Paths supplied to the command are relative to the terminal's working directory.
The test suite resolves reference fixtures relative to its own file. Missing
paths, directories and unsupported extensions are checked. Malformed JSON and
non-object records report the source path and line number. Blank lines are
ignored. A later file error does not undo earlier accepted events.

The two replay tests use temporary .jsonl and .jsonl.gz files containing LIMIT,
MARKET_SELL and CANCEL events with custom event_id values. Both must preserve
those IDs, return the independently expected results and finish with an empty book.

## Supplied materials

ASSIGNMENT.md, generate_orders.py and the data/ fixtures were provided with the
teacher's assignment. The reference six-BTC sale fills b1, b2, b3, then b4 for
1, 1, 3 and 1 BTC, respectively, yielding $359,400. The independent reference
assertions and generated-stream conservation checks remain in the tests.
