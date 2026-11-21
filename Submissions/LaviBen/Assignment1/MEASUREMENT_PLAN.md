# Measurement stages and reproducibility

## Status

Stages 7-9 are implemented:

1. deterministic benchmark input preparation with settings and SHA-256;
2. primary timing, throughput, separate per-event latency, correctness and
   operation-count runs; and
3. fresh `tracemalloc` runs with explicit inclusion boundaries.

The current evidence is a **provisional smoke run**, not a canonical result.
The runner refuses `--profile canonical` while the Assignment 1 tree is dirty.
This enforces the project rule that measurement code must be committed before
canonical measurement and prevents results from naming the wrong code version.

## Dataset grid

Canonical preparation creates:

- all five course workload families at `M = 1,000; 10,000; 100,000`, seeds
  `42`, `43`, and `44`, with 1,000 available price levels;
- queue-concentration inputs with the same event counts and seeds at 4 versus
  1,000 available prices; and
- bid-only liquidation setup books with the same event counts and seeds.

Every dataset is generated before timing and stored under ignored
`generated/benchmark/`. Its metadata records experiment, scenario, event
count, seed, levels, units, generator, compressed size, compressed SHA-256 and
canonical event SHA-256. One verified immutable event tuple is shared by both
versions. Generated large inputs remain outside Git.

Smoke preparation uses 1,000 events and seed 42 while retaining all five
families, both concentration cases and one liquidation setup:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_benchmarks.py --profile smoke
```

Canonical preparation, after the measurement code is committed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_benchmarks.py --profile canonical
```

## Timing and latency definitions

Run the provisional smoke measurements:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_benchmarks.py \
  --profile smoke \
  --output tmp/benchmark_smoke.json.gz
```

After committing the code and confirming a clean tree, the intended canonical
command is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_benchmarks.py \
  --profile canonical \
  --time-limit-seconds 5 \
  --output results/raw_measurements.json.gz
```

The five-second limit applies independently and equally to every version,
repeat, latency run, and memory run. It is deliberately finite so quadratic
baseline cases produce explicit stopped evidence instead of making the full
grid impractical. Completed smaller cases remain measured normally; stopped
values are not extrapolated.

Before that run, add one feasible million-event attempt without expanding the
entire grid to that size:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_benchmarks.py \
  --profile canonical --sizes 1000000 --seeds 43 --scenarios mixed \
  --skip-special --output-dir generated/million
cp generated/million/stream__mixed__m1000000__seed43__levels1000.jsonl.gz \
  generated/benchmark/
cp generated/million/stream__mixed__m1000000__seed43__levels1000.jsonl.gz.metadata.json \
  generated/benchmark/
```

The same canonical runner then includes that dataset, applies the same limit
to both versions, and retains either completed or stopped evidence.

The report records the exact executable and argument vector actually used.
Canonical mode uses five raw repeats and reports their median; smoke mode uses
two repeats only to test the pipeline.

- `input_read_parse`: gzip reading plus JSON decoding, measured separately.
- `engine_replay`: fresh empty-book construction plus the complete prepared
  event batch. Input generation and parsing are excluded.
- `application_total`: paired input reading/parsing plus engine replay (or
  paired parsing plus liquidation build and sale).
- `book_build`: fresh liquidation-book construction from every setup order.
- `individual_sale`: matching, state/index updates and fill-list construction
  for one 10%, 100%, or 200% sale against its own freshly built book.
- `build_plus_sale`: the corresponding construction and sale times combined.

Both versions receive the same inputs, warmup prefix, repeat count and
per-phase time limit. A stopped run is saved with elapsed time, completed event
count and reason; it is never omitted or extrapolated. Parsing, latency,
operation counting and memory tracing do not run inside primary timing.

Latency instrumentation saves every per-event duration in nanoseconds and
reports nearest-rank median, 95th and 99th percentiles overall, by event type,
and for early versus late windows. Each window is the first or last 10% of the
instrumented stream, capped at 1,000 events. Nearest-rank means sorting `n`
samples and selecting rank `ceil(p/100*n)`, with minimum rank one. These are
in-process algorithm times, not network or queueing latency.

## Operation counts and correctness

Separate runs save event/status counts, fills, filled quantity, market
residual, active-order peak, occupied-price-level peak and final book size.
Liquidation records also save requested quantity, makers touched, price levels
visited and unfilled residual. Ordered results and canonical final books are
compared between versions on diagnostic streams and every liquidation size.

## Memory boundary

Input events are fully prepared before tracing. Each version and liquidation
size gets a fresh tracing run:

1. collect garbage;
2. start `tracemalloc`;
3. construct a fresh book and process the measured workload;
4. read current and peak traced bytes while the book and final returned output
   are alive; and
5. stop tracing.

The input tuple is excluded. The book, active indexes/price levels and final
output are included. Prior per-event outputs are not retained, matching the
engine's no-history design. Allocation checkpoints at 10%, 50%, and 100% show
growth and post-cancellation state. Their containers are allocated before
tracing; retained integer readings add negligible bookkeeping. Python
allocations observed by `tracemalloc` are included; native/process allocations
are not. A memory phase uses the same declared time limit and records
partial/stopped evidence rather than hanging.

## Provisional smoke evidence

The latest ignored smoke report contains eight datasets and 232 validated
records: raw timing repeats and medians, 14,000 raw event-latency samples,
operation counts, correctness records and 20 fresh memory records. No smoke
phase stopped. The report identifies the tree as dirty and labels itself
`provisional_smoke`; it must not be copied into canonical results.
