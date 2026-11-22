# Assignment 1, limit order book: Laurin Bühler

> Status (2026-11-22): Phase 3b variants A/B1/B2/B3 ready for review; 501 tests pass.
> B is the compatibility registry key for B1; B1 is also accepted by replay.
> Final B is selected from Phase 4 measurements; adaptive switching is deferred.

## Clean-environment run path (PowerShell, from this folder)
```powershell
python -m venv "$env:USERPROFILE\.venvs\aif-a1"
& "$env:USERPROFILE\.venvs\aif-a1\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
python -m pytest -q                                   # Phase 3b: 501 passed
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version A
python run.py bench.run_all                           # (planned) writes 03_results/runs/<run>/
python -m streamlit run 04_dashboard/app.py           # (planned) http://localhost:8501, reads 03_results/ only
```
`run.py` puts `01_code/` on the import path and runs a module; `pytest.ini` does the same for tests. No install step.

## Environment
- Developed on Windows 11 with Python 3.13.15 (the course generator was checked with 3.11.9; it reproduces the supplied files byte for byte under 3.13.15, see below).
- **Tools are always called as modules** (`python -m pytest`, `python -m pip`, `python -m streamlit`), never through `pytest.exe` and similar launchers: Windows Smart App Control on the author's machine blocks unsigned executables.
- **`hypothesis` is pinned to 6.155.7 (< 6.156) on purpose.** Newer versions ship a native extension module that Smart App Control blocks, so the test suite would not start. All test evidence in `05_evidence/` is produced with the pinned version.
- The engine, the event reader and the data generator use the Python standard library only; `pandas` and `streamlit` are used only by the dashboard.

## Expected output (worked example)

Replay prints one JSON result per input event. The first five limits return
`resting` with no fills and their full quantities as `unfilled_qty_units`.
The sixth result is:

```json
{"event_id": "event6", "order_id": "s1", "status": "filled", "unfilled_qty_units": 0, "fills": [{"maker_id": "b1", "taker_id": "s1", "price_ticks": 6000000, "qty_units": 100000000}, {"maker_id": "b2", "taker_id": "s1", "price_ticks": 6000000, "qty_units": 100000000}, {"maker_id": "b3", "taker_id": "s1", "price_ticks": 5990000, "qty_units": 300000000}, {"maker_id": "b4", "taker_id": "s1", "price_ticks": 5970000, "qty_units": 100000000}]}
```

Final book (via `snapshot()`, not printed as an extra replay line): b4 retains
400000000 units at 5970000 ticks, arrival_seq 4; a1 retains 200000000 units at
6010000 ticks, arrival_seq 5. Integer gross proceeds = 3594000000000000 tick-units
= 359400.00 USD. Hand trace: `00_docs/TRACE.md`.

Replay also accepts `.jsonl.gz` and `--version B1`, `B2` or `B3` (`B` remains the B1 alias). Events stream in file order; the shared validator rejects
nonincreasing seq without advancing the last accepted seq. Each book starts empty;
neither inputs nor result history are retained by the replay command.

Phase 3b verification and the authorized one-shot sanity command:

```powershell
python evidence.py phase3b-internals -- python -m pytest 02_tests/test_b_internal.py -q
python evidence.py phase3b-sanity-not-a-benchmark -- python run.py bench.sanity
```

`02_tests/test_b_internal.py` runs automatically with the full suite. It checks
A/plain/counted parity on all 18 original own expected files, internal structure
and applicable cancellation/compaction/heap boundaries for each B variant.
`python run.py lob.check_b` is retained as a thin launcher for those same pytest
checks. Stateful and CLI tests are parametrized across variants; original
contract assertions, expected data, A, B1 and shared validation remain unchanged.

`bench.sanity` runs A/B1/B2/B3 once each per supplied file, fresh books, counters
off, parsing/setup/replay separate and correctness checks outside timing. It
uses the shared harness with warmup=0/repeats=1 (Laurin's authorized sanity
exception). Returned result lists are retained equally for comparison; engine
objects keep no history. The observations are **sanity, not a benchmark**.

B1 uses slot records, an id index, deque FIFO levels and signed sorted prices;
compaction requires stale > live and stale > 32. B2 uses OrderedDict FIFO levels
and direct cancellation, with no stale records. B3 keeps B1's deques but uses
lazy price heaps/in_heap sets; stale heap prices can accumulate until they reach
the root. All default to counters off; use `count_operations=True` and
`.counters.as_dict()` for diagnostic work counts. B3 adds heap work counters;
public quote cleanup does not change counters. SPEC.md documents complete
complexity bounds, tradeoffs and predictions.

Raw sanity data/environment/tests:
`03_results/runs/20261121T234816Z_b5411d4-dirty_phase3b_sanity_not_benchmark/`.
The per-file test/timing tables are in `00_docs/AI_LOG.md` (Phase 3b).
Phase 4 compares A, B1, B2 and B3 and chooses the final B from measurements.
An adaptive online index with hysteresis and a measured threshold (no lookahead)
is considered only after Phase 4. Fresh-venv and official runtime/memory work
remain later phases; see `05_evidence/INDEX.md` for current evidence.

## Layout (read in this order)
| Folder | Contents |
|---|---|
| `SPEC.md`, `README.md` | what is asked, how to run it |
| `00_docs/` | report, requirements → evidence map, hand trace, AI log, revision log, learning note |
| `01_code/<pkg>/` | the implementations (registry `METHODS` in `__init__.py`) |
| `01_code/datagen/`, `01_code/bench/` | own data generators; measurement scripts + `harness.py` |
| `02_tests/` | contract checks, tests, mutant / differential tests |
| `03_results/runs/` | one folder per benchmark run (raw CSVs, `env.json`, `tests.txt`) |
| `04_dashboard/` | dashboard; reads saved results only |
| `05_evidence/` | saved test/check logs with commit and timestamp, `INDEX.md` |
| `06_data/` | `supplied/` sample files (course); `own/` own edge-case datasets with expected results; `generated/` is git-ignored (commands + sha256 below) |

## Data generation (commands + sha256)
All data are synthetic teaching data from the course package, not historical exchange records.

**Supplied package check** (2026-11-21): all 20 entries of the course `MANIFEST.json` plus the five `*.metadata.json` checksums match (`.DS_Store` listed in the manifest is absent, OS clutter):
```powershell
python evidence.py manifest-package -- python verify_manifest.py "<package dir>" --metadata
```
The five 10,000-event samples and the worked example pair are copied unchanged to `06_data/supplied/` and re-checked there (`05_evidence/*manifest-supplied-copies*`, `*worked-files-sha*`).

**Generator reproduction**: the supplied `generate_orders.py` (sha256 `ef7f3154…7fe7d`) regenerates all five seed-42 / 10k / 1,000-level samples with identical sha256 (`05_evidence/*generator-reproduces-seed42-10k*`):
```powershell
python run.py datagen.check_reproduction --generator 06_data/supplied/generate_orders.py
```

| Supplied file (streams: seed 42, 10,000 events, levels 1000) | sha256 |
|---|---|
| `generate_orders.py` (4019 bytes, unchanged; Q11) | `ef7f31545addf576e6071cc20a5930f3e2ed93bfef96d4968150fad763d7fe7d` |
| `buildup_10000.jsonl.gz` | `441db8ecf37103113abfed079fbe4bdbe212bb7acbc31be0d344bab67c9b95b5` |
| `crowded_10000.jsonl.gz` | `112bc3ad120eb436e45608ef11ff804aed35aef24e43d4c10e5adda3b26577b6` |
| `mixed_10000.jsonl.gz` | `f5a027da6b31209d5e83c56bfbf8626604bb5f91e4176b784ff8a1dac1974a16` |
| `sweep_10000.jsonl.gz` | `c50755964212445574359b0fe4011f908ad2833edc900d49ecfa25948cca334f` |
| `cancel_churn_10000.jsonl.gz` | `7aef5f014e6d1e5d01cb37c7ff7b02cfcc5a30f185de8a4b33db2d32b3d9d933` |

**Own data (labelled *own*, separate from the supplied files):**
- `06_data/own/`: 18 small hand-designed edge-case streams with hand-calculated expected results (`<case>.expected.json`), written by `python run.py datagen.own_cases`; `python run.py datagen.own_cases --check` verifies that the committed files match the generator. Overview: `06_data/own/INDEX.md`.
- `01_code/datagen/adversarial.py`: own adversarial benchmark scenarios (`deep_book`, `mid_queue_cancels`, `repeated_full_sweeps`; see SPEC.md). Phase 4 inputs are generated under ignored `06_data/generated/phase4/own/`.

Phase 4a generated the full planned data grid outside timing: official 1k/10k/100k
at seeds 42/43/44, 1M seed 43, queue concentration and own adversarial/Q7/drift
inputs. [DATA_MANIFEST.json](00_docs/DATA_MANIFEST.json) contains 114 catalog
entries (105 distinct gzip files), exact commands, settings and sha256. Generated
data remain ignored; commit the manifest. Generate and verify with:

```powershell
python run.py bench.catalog
python run.py bench.catalog --verify
```

## Measurement definitions
The complete protocol, limits, estimates and exact long-run PowerShell commands
are in [BENCHMARK_PLAN.md](00_docs/BENCHMARK_PLAN.md). Fixed selection criteria
are in SPEC.md. Primary replay uses pre-parsed events, fresh books, counters off,
GC enabled, one warm-up and five measured repeats; seconds and raw trials are
saved. Parsing and construction are separate. Liquidation rebuilds each bid
book before the measured sale. Throughput is events / median replay seconds.
Independent runs measure nearest-rank latency p50/p95/p99 in ns, traced memory
including book/current fills but excluding parsed input/history, and operation
counts. Traced memory is not RSS. Missing/stopped values remain explicit.

Safe default (only M=1000, seed 42, all experiments and versions):

```powershell
python evidence.py phase4-smoke -- python run.py bench.run_all --part smoke
```

Long runs require explicit authorization flags and committed source. Laurin runs
the six commands in BENCHMARK_PLAN.md after review/commit; they have not been
executed here. The wrapper uses the existing venv and supports B-only batches,
A pilots and resumption without reducing B repeats.

## Results summary (3–5 lines)

Phase 4a final smoke: `03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/`.
All 216 cells and sampled A comparisons pass; 988 raw timing records and separate
latency/memory/count CSVs are saved. B3's drift heap grows with a two-order live
book (501 retained heap entries at event 1000); investigate using the planned
growth experiment. Smoke does not choose the final B. Long runs remain pending.

## Revision summary

## Evidence block
Commit to audit: <hash> (filled in by Laurin)
Tests (Phase 4a): `python -m pytest -q --tb=short --basetemp=scratch/pytest-phase4a --junitxml=05_evidence/phase4a-all-tests.xml` -> `517 passed in 176.97s` (per-file table in `00_docs/AI_LOG.md`)
Benchmark (Phase 4a smoke only): `python run.py bench.run_all --part smoke --session phase4a_smoke_final` -> `03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/`, 216/216 cells OK; full grid pending.
Fresh-venv check: pending Phase 7 (existing pinned venv used through Phase 4a)

Q11 completed 2026-11-22: `06_data/supplied/generate_orders.py` was copied
byte-for-byte from the course package and checked against its MANIFEST.json
(entry size 4019 bytes and the sha256 above). Evidence:
`05_evidence/20261121T233959Z_b5411d4_phase3b-q11-generator-sha.txt`.
The evidence timestamp is UTC; the local session date is 2026-11-22.
The exercise-local `.gitattributes` marks this supplied file `-text` to preserve
its exact bytes under Windows Git line-ending conversion.
