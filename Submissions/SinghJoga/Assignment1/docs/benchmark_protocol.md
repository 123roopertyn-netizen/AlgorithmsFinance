# Benchmark protocol

## Commands

Run commands from this assignment directory with its local interpreter:

```powershell
.\.venv\Scripts\python.exe benchmarks\run_benchmarks.py --smoke --run-id smoke_final_04
.\.venv\Scripts\python.exe benchmarks\run_benchmarks.py --run-id full_20261125
```

The smoke command uses 25 generated events per supplied workload family,
40 fixed-book orders, 1,000 queue-concentration orders, and 20 anchored churn
cycles. It executes every experiment and measurement mode, but is not a
performance sample. The full command uses all five families at M =
1,000/10,000/100,000, seeds 42/43/44, a 1,000-order fixed book, 10,000
queue-concentration orders, and 5,000 anchored churn cycles. This is 49
scenarios and 98 version/configuration runs. It does not launch one-million
event runs.

Resume an interrupted or partial run without overwriting its attempts:

```powershell
.\.venv\Scripts\python.exe benchmarks\run_benchmarks.py --resume full_20261125
```

Completed configurations are skipped. A retry of an incomplete configuration
gets a new attempt number, progress file, and artifact directory. Resume accepts
only time/memory-limit overrides; it verifies saved workload settings and input
checksums before continuing. Use a new run ID rather than reusing a completed
directory for a new matrix.

The smoke timeout path was also checked with an intentionally tiny limit:

```powershell
.\.venv\Scripts\python.exe benchmarks\run_benchmarks.py --smoke --run-id smoke_timeout_validation_01 --time-limit-seconds 0.001
```

This command is expected to return exit code 2 because its 18 configurations
are recorded as `stopped_timeout`; the records have null elapsed timing rather
than fabricated zeroes.

## Workloads and validation

The supplied generator creates every workload outside measurement. Existing
supplied gzip files are reused only for matching settings (M=10,000, seed 42,
levels 1,000); other generated inputs are saved under the run's `inputs/`.
Generated settings and SHA-256 checksums are recorded in `metadata.json` and
per-attempt JSON. Fixed-book, queue-concentration, and anchored-churn inputs
are generated before timing and also receive checksums.

Each input is checked for its event count and strictly increasing integer
sequence. Before measurements, baseline and revised outputs, accepted
sequences, and canonical books are compared after every event up to the
configured parity limit (default 1,000). Fixed-book parity additionally checks
10%, 100%, and 200% sells on independent fresh books. The full correctness
suite remains the independent expected-answer check; parity is not treated as
a substitute for it.

The fixed book's 10% sale is integer ceiling, `max(1, (Q*10 + 99)//100)` for
positive available quantity `Q`. The 100% and 200% sizes use the full integer
quantity and twice that quantity. Each sale starts from an identical rebuilt
book. Queue concentration holds order count and seeded quantity sequence
constant while assigning orders to 4 or 1,000 prices; the counter record gives
both requested and realized occupied price counts. Churn alternates transient
orders and cancels while an anchor order at another price remains active.

## Timing boundaries

Every primary phase is warmed once and timed for five repeats with
`time.perf_counter`; each repeat and the median are retained.

| Phase | Included in timed interval |
|---|---|
| `input_read_parse` | Opening the JSONL/gzip input, reading it, and parsing all event objects. |
| `empty_engine_construction` | Constructing a new empty engine. |
| `engine_replay` | Processing a pre-parsed, identical event list against a fresh engine. Engine construction is outside this interval. |
| `total_application` | Reading/parsing the input, constructing a fresh engine, and replaying the complete stream. |
| `initial_book_construction` | Replaying the pre-parsed fixed-book submissions into a fresh engine. |
| `sell_operation_{10,100,200}pct` | Rebuilding the same initial book before the timer, then matching the sale, mutating the book, and constructing the returned fills. |
| `total_application_sell_{10,100,200}pct` | Reading/parsing fixed-book submissions, constructing the engine/book, and processing the sale. |

The fixed-book sale event itself is constructed before timing, like the
pre-generated input. The sale result is not retained as a history; only its
fill count is read after the timer. Primary timing excludes generation,
parity/correctness checks, counters, inspection, printing, result-file writes,
latency output, profiling, and memory tracing. No full-book inspection or sort
runs inside primary timed replay. Output construction for fills remains part
of the event processing interval.

## Separate diagnostics

- **Latency:** A warm-up replay is followed by one fresh diagnostic replay.
  Raw JSONL contains event position, sequence, type, and elapsed processing
  seconds. File writes are outside each per-event timer. Median uses
  `statistics.median`; p95/p99 use nearest rank, `sorted_values[ceil(p*n)-1]`.
  Early and late windows are the first/last `ceil(M/10)` events; each reports
  its own percentiles and process-time throughput. This includes the buildup
  stream's early/late growth comparison. Throughput is reported separately
  from latency and is not inferred from reciprocal total-run throughput.
- **Counters:** A separate full replay inspects canonical state before each
  event. `active_order_peak` and `occupied_price_level_peak` are logical
  maxima; physical storage entries include version-specific ID/queue/heap
  containers. `fill_count` is returned fill records, and `maker_touches`
  counts maker orders filled (one touch per fill record). `visited_price_levels`
  counts distinct price levels from which fills occurred plus the first
  terminal noncrossing level considered by limit matching, where applicable;
  cancellations do not count as matching price visits. These are semantic
  operation counters, not a reconstruction of every internal list/dictionary
  probe.
- **Profile:** A separate `cProfile` replay saves `.prof` and top cumulative
  text output. It is bounded to `min(profile_event_limit, M)` events and is
  enabled for the smallest mixed workload in the selected run.
- **Memory:** Each run uses a fresh `tracemalloc` session, with input events
  already parsed and prepared. Traced allocations include engine construction,
  active book structures, matching and transient outputs; the most recent event
  result is retained at checkpoints, not full output history. Checkpoints are
  recorded at quarter-stream positions and after final insertion/churn state.
  Diagnostic checkpoint bookkeeping is itself a small traced allocation.
  Input lists, JSON parsing, native allocations, allocator fragmentation, and
  total process memory are not represented by `tracemalloc`.

Primary timing, counters, latency, profiling, and memory have separate phase
records; instrumentation is not mixed into primary timings.

## Limits, saved output, and interpretation

Defaults are a **300-second wall-time limit and 4,096 MiB process-memory limit
per version/configuration** for the full matrix. Smoke defaults are 60 seconds
and 2,048 MiB. The same limits apply to baseline and revised. The timeout clock
starts immediately before opening the progress log and spawning that
configuration's worker. It covers worker startup, all five-repeat timing
phases, counters, latency, profiling, memory tracing, IPC, parent progress-log
flushes, and worker shutdown. It is one cap for the entire version/configuration
run, not a separate cap per phase.

Workload generation, parity validation, environment/code-hash collection,
configuration setup, and final result-JSON serialization happen outside that
clock. A timeout may therefore occur during primary replay or any diagnostic
phase; completed phase rows and individual timing repeats are flushed to the
progress log and copied into the attempt record. A phase median is emitted only
after all five repeats for that phase finish. An incomplete repeat set has no
summary/median row and the configuration status remains stopped.

On Windows, the parent samples process peak working set through
`GetProcessMemoryInfo`; on Linux it samples `/proc/<pid>/status` `VmHWM`.
Sampling starts immediately and repeats at 50 ms intervals. Crossing the
configured threshold terminates the worker and records `stopped_memory_limit`.
This is **sampled termination, not an operating-system hard memory cap**;
memory can overshoot between samples. Timeouts use a spawned worker process,
are checked while it runs, and terminate it when the deadline is reached.
Stopped/error attempts include a status, duration, observed memory, and
`elapsed_seconds: null`; partial phase rows remain in the progress JSONL.

Each run is saved under `results/benchmarks/<run-id>/`:

- `metadata.json`: settings, environment, code hashes, input checksums, and
  pre-measurement parity outcomes.
- `records/*attempt*.json`: per-phase raw repeats, summaries, diagnostics,
  status, and limits.
- `records/*.progress.jsonl`: incrementally flushed rows, including partial
  work if a worker stops.
- `artifacts/`: raw per-event latency files and profiling artifacts.
- `inputs/`: generated input streams and sidecars; supplied inputs are
  referenced by path and checksum rather than copied.

Rows include implementation version, experiment/scenario/seed, event count,
generator settings, input checksums, phase/repeat, elapsed or traced bytes,
active/price-level peaks, fills/sell quantities where relevant, completion
status, Python/dependency/machine/Git information, code hashes, and limits.
The benchmark runner does not claim a speedup; this task runs only smoke-scale
workloads, not the requested full matrix.

AI assistance was used to draft the runner, tests, and this protocol. The
separate-measurement design was retained. A Windows smoke run exposed a closed
pipe at normal worker shutdown; that behavior was corrected by treating pipe
EOF explicitly and preserving completion/error status. Deadline checks were
also tightened to use the remaining timeout. No supplied files or engine
behavior were changed for this benchmark task.
