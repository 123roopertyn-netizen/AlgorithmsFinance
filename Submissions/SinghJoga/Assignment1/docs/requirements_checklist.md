# Assignment requirements checklist

The table below records the original requirements and planned evidence; the
latest completion state is tracked in **Benchmark execution status** below.
The supplied package manifest was checked during setup: all 15 present entries
match their listed byte counts and SHA-256 values; `.DS_Store` is listed in the
manifest but is absent from the package.

| Requirement | Planned tests | Planned implementation | Planned experiments | Evidence | Status |
|---|---|---|---|---|---|
| Integer units, event schema, and model boundaries | Validate prices/quantities as positive integers, explicitly rejecting booleans; check required fields, types, and sequence behavior. | Both versions implement validation; modeling boundaries are recorded in the baseline design. | None. | Parameterized specification tests and `docs/baseline_design.md`. | Verified for Versions A and B |
| Required interfaces and event results | Check `AddLimitOrder`, `CancelOrder`, `FillMarketSell`, event dispatch, and book inspection; assert result field names, statuses, and ordered fills. | Both versions implement the same event interface and observation properties. | Replay the worked example using both versions. | `docs/interface.md`, full test suite, and supplied worked-example test. | Verified for Versions A and B |
| Matching, price-time priority, and quantities | Independently calculate tests for empty/one-order books; smaller, equal, and oversized market sells; multiple makers at one price; multiple price levels; partial fill followed by another sale; crossing and noncrossing limits; identifier order different from arrival; and a long same-price queue. Check maker/taker IDs, execution order, maker prices, and conservation. | Both versions preserve FIFO within a price, best-price selection across levels, original arrival sequence on residuals, and maker-price execution. | Compare both versions after every event, including ordered fills and canonical books. | Independent expected values and passing full suite. | Verified for Versions A and B |
| Validation, cancellation, and invariants | Cover zero, negative, noninteger, boolean, unknown type/side, duplicate live IDs, and nonincreasing sequence. Assert invalid events do not mutate book or accepted sequence. Test cancellation before/after partial fill, after full fill, repeat cancellation, and unknown targets. Check no crossed resting book, positive remaining quantities, and unique active storage. | Both versions validate before mutation; unknown cancel is accepted as `not_found`; remove only remaining quantity; limit residuals rest and market residuals do not. | Include invalid and cancel-heavy streams in parity checks. | Parameterized mutation snapshots and passing specification tests. | Verified for Versions A and B |
| Results, inspection, and accounting | Assert submission/cancel/rejection schemas, statuses, residual quantities, ordered fill records, and canonical inspection sorted by best price then arrival. Check incoming, maker, cancellation, and proceeds conservation. | Both versions return only current-event fills and retain no optional history. | None beyond replay and correctness tests. | Full test suite and design documentation. | Verified for Versions A and B |
| Two implementation versions and generated correctness checks | Run the same tests against both; use small generated event streams and compare after every event to independent expected answers. Confirm specification tests fail for missing behavior before implementation. | Version A remains unchanged; Version B is implemented with indexed queues and bounded lazy heaps. | Compare all three deterministic streams event by event; benchmark parity separately from timing. | Preimplementation failure evidence, parameterized tests, and per-event results/book/sequence comparison. | Verified for correctness and generated parity |
| Supplied benchmark workload families and sizes | Validate each workload's event count, sequence ordering, and metadata before replay. | Replay `buildup`, `crowded`, `mixed`, `sweep`, and `cancel_churn` streams from an empty book. | Use M = 1,000, 10,000, and 100,000; use seeds 42, 43, and 44 across all five families. Try M = 1,000,000 if feasible and record limits or stopped runs. | Generator commands/settings, checksums, and raw result rows. | Pending |
| Submission flood and scaling | Check active-order and occupied-level peak counters independently of the timed run. | Measure book construction and full-stream replay. | Compare versions on identical streams; vary event count, seed, and workload family. | Raw timings, medians, event throughput, active-order and price-level peaks. | Pending |
| Fixed-book liquidation | Independently verify expected maker touches, levels visited, fills, and unfilled quantity. | Build a fresh, identical bid book for each sale size; round 10% quantity up to at least one unit. | Test 10%, 100%, and 200% of available bid quantity; report book construction/reset separately and include matching, state updates, and fill-list creation in sale timing. | Raw sale results, requested quantities, fill counts, depth metrics, and reset timings. | Pending |
| Queue concentration | Assert FIFO and price-time correctness under concentrated and spread-out prices. | Record occupied price levels and queue sizes without changing matching semantics. | Hold initial order count fixed and compare examples such as 4 versus 1,000 prices for both correctness and speed. | Workload settings, operation counts, and raw timings. | Pending |
| Cancellation churn | Check that cancelled orders are absent and active book size stays small. | Track active orders separately from any stale entries or history. | Measure time and memory after many cancellations with few active orders; detect unbounded stale-entry/history accumulation. | Active counts, memory measurements, and churn results. | Pending |
| Timing protocol and latency | Check the timing harness uses identical pre-generated inputs and fresh empty books for each replay. | Use `time.perf_counter`; keep generation, parsing, engine replay, and full-application timing boundaries explicit. | Warm up; retain all five repeats and their median. Report throughput. In a separate instrumentation run, report per-event median, p95, and p99 with a documented percentile convention; sample beginning/end of long uninterrupted submission bursts. | Every raw repeat, median, phase labels, percentile method, throughput, and timing-boundary notes. | Pending |
| Memory and profiling | Check instrumentation does not contaminate primary timing runs. | Use separate `tracemalloc` captures; state whether preloaded input, book, returned fills, and saved history are included. | Measure insertion growth and post-cancellation state; profile separately and explain measured bottlenecks using code and operation counts. Distinguish traced allocations from auxiliary space and total/native memory. | Peak traced bytes, capture boundaries, profile output, and bottleneck analysis. | Pending |
| Results, environment, dashboard, and report | Validate result records include required fields and distinguish timing from memory runs. | Save CSV or JSON with version, scenario, seed, event count, active-order/level peaks, sale quantity where relevant, fill count, phase, repeat, elapsed seconds, and traced peak bytes. Record Python, dependencies, machine, OS, code version, and generator settings. Build a dashboard that loads saved results, not reruns. | Show construction, replay, individual-sale scaling, version comparison, throughput, latency distributions, post-cancellation memory, and correctness outcomes; label units and missing/stopped runs. | Raw result files, environment metadata, dashboard, and short report covering specification, correctness, runtime, memory, profiling, revision, and limitations. | Pending |
| Reproducibility and AI disclosure | Verify clean-environment instructions and supplied worked output. | Keep exact run commands and dependency pins; do not include generated million-event datasets. Record AI suggestions accepted, corrected, or rejected accurately. | Re-run the documented checks when the project is implemented. | README, requirements, test logs, and AI-assistance notes in both design documents; commit identifier and full-project reproducibility remain. | Partial |

## Setup verification

| Item | Evidence | Status |
|---|---|---|
| Assignment-local environment | `.venv` uses Python 3.14.7; pytest 9.2.0 is installed and importable from that environment. | Verified |
| Supplied package checksums | 15 present manifest entries match size and SHA-256; `.DS_Store` is missing as noted above. | Verified |

## Preimplementation specification-test coverage

The existing FIFO and best-price tests in `tests/test_price_time.py` are
preserved. `tests/test_specification.py` adds independent, literal expected
fills/books for empty books, the three one-bid market-sell depth cases,
partial-then-subsequent fills with maker priority, a five-order same-price
queue whose IDs are not in arrival order, cancellation lifecycle cases,
crossing limit buys and sells across multiple makers, resting-maker execution
prices, equality and worse-price boundaries, residual limit orders, and the
supplied worked example. Accepted submission assertions include quantity
conservation and positive fills; representative books are checked for no
cross, positive resting sizes, and unique active IDs. Integer tick-times-unit
proceeds are asserted against a hand-calculated constant.

The validation tests cover unknown event type and side, missing common and
type-specific fields, zero/negative/noninteger/boolean prices, quantities, and
sequences, duplicate live submission IDs, and equal/lower sequences. They
assert rejection reason, unchanged canonical book, unchanged last accepted
sequence, valid `not_found` cancellation sequence advancement, and reuse of a
rejected sequence. The additional read-only `last_accepted_seq` observation is
documented in `docs/interface.md`; its initial value is chosen as `None`.

`tests/fixtures/generated_seed_{13,37,91}.jsonl` are deterministic 18-event
valid streams generated separately from engine and measurement code. Their
cycle, random choices, ranges, and regeneration command are recorded in
`tests/fixtures/README.md`. Fixture reproducibility/shape checks pass. The
event-by-event comparison now checks ordered results, accepted sequence, and
canonical inspection for both versions after each event in all three streams.

### Pre-code suite result (historical evidence)

The complete suite was collected with no import or collection errors:

```text
Command: python -m pytest -q --tb=short
Result: 66 collected; 3 passed; 63 failed
Failure reason: all 63 failures raise NotImplementedError from the baseline
scaffold; the engine and inspection behavior are intentionally unimplemented.
Evidence: results/specification_tests_before_code.txt
```

### Version A verification

After implementation, `python -m pytest -q` completed with **66 passed**.
The three fixture reproducibility/shape checks remain included; the 63
preimplementation `NotImplementedError` failures now pass against Version A.
Final output is saved in `results/tests_baseline.txt`. Earlier pre-code
evidence above remains unchanged.

### Version B preimplementation regression result

Before Version B behavior was added, the focused regression/parity command
collected successfully and reported **10 failed, 3 passed**. All 10 failures
were `NotImplementedError` from the Version B scaffold; the three passing
cases were fixture reproducibility checks. Evidence is preserved in
`results/revised_tests_before_code.txt`.

### Both-version verification

The full suite now parameterizes specification tests over both versions and
compares generated streams after every event. Final output is saved in
`results/tests_revised.txt`: **131 passed**. Version B's seven focused
storage regressions also pass, including the bounded-heap assertion under
repeated churn.

### Remaining gaps

- Full-size benchmark cases and the optional one-million-event feasibility
  run remain pending; no full-size performance claim has been made.
- The dashboard and final assignment report remain pending.
- Full-project reproducibility and a commit identifier remain pending.

### Benchmark execution status

The benchmark helper tests cover integer-ceiling liquidation quantities,
nearest-rank percentiles and median/throughput calculations, fresh book
isolation for both engines, queue-concentration quantity/price counts, closed
worker-pipe errors, and stopped rows with null elapsed time.

After adding these checks, the complete assignment suite passed **142 tests**
with `.\.venv\Scripts\python.exe -m pytest -q`. Exact output is saved in
`results/tests_benchmark_infrastructure.txt`; the earlier 131-test Version B
evidence remains unchanged.

The final all-mode smoke command was:

```text
.\.venv\Scripts\python.exe benchmarks\run_benchmarks.py --smoke --run-id smoke_final_04
```

It completed **18/18** version/configuration runs: all five supplied workload
families, 10%/100%/200% fresh-book sells, 4-versus-1,000-price queue
concentration, and anchored cancellation churn. It recorded five primary
timing repeats per measured phase, 18 latency summaries and raw event streams,
94 memory checkpoints, and two bounded profiles. Parity checks passed all
smoke workload events and fixed-sale cases. This validates infrastructure
only; the small workloads do not establish comparative performance.

Timeout recording was exercised separately with a 0.001-second limit. All 18
configurations were recorded as `stopped_timeout`, with null elapsed time
rather than zero. That run returns the documented nonzero status because the
workers were intentionally stopped.

A first Windows smoke attempt exposed a pipe-EOF error on normal worker
shutdown. Its partial progress was preserved; pipe closure handling was fixed,
and the final smoke run completed cleanly. Measurement boundaries, limits,
resume behavior, and exact full-run commands are in
`docs/benchmark_protocol.md`.
