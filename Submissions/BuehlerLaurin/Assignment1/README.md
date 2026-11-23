# Assignment 1, limit order book: Laurin Bühler

> Status (2026-11-23): final Version B is B3r. The binding rematch rejected B3r_fast.
> B1/B2/B3/B3r/B3r_fast remain available under explicit names. No adaptive switching.

## Final Version B

**`B` = `B3r`**. [FINAL_SELECTION.md](00_docs/FINAL_SELECTION.md) records the
decision, measurements and qualifications, including both rejected fast
comparisons. B3r uses deque FIFO levels, lazy cancellation, heap prices and
per-side heap rebuilds. This registry update changes no engine logic.

| Replay / registry name | Implementation |
|---|---|
| `B`, `B3r` | Final Version B, `OrderBookB3r` |
| `A` | Baseline, `OrderBookA` |
| `B1` | Original sorted prices + deque, `OrderBookB` (formerly B) |
| `B2` | Sorted prices + OrderedDict levels, `OrderBookB2` |
| `B3` | Heap prices without rebuild, `OrderBookB3` |
| `B3r_fast` | Tested optimisation, tried and rejected, `OrderBookB3rFast` |

From Assignment1 with the venv below active:

Replay defaults to final Version B (B3r) when `--version` is omitted. Use
`--version A` explicitly for the baseline; all explicit names remain available.

```powershell
python run.py lob.replay 06_data/supplied/worked_example.jsonl
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B3r
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version A
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B1
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B2
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B3
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version B3r_fast
python run.py lob.replay 06_data/supplied/mixed_10000.jsonl.gz --version B
```

Saved result labels keep their meaning at the recorded commit: historical B
means B1. Nothing under `03_results` is renamed or remeasured by this update.

Registry verification (2026-11-23): [983 standard tests](05_evidence/20261123T162212Z_dd88f22-dirty_final-b-all-tests.txt)
passed in 909.96 s; [1,995 attack tests](05_evidence/20261123T162213Z_dd88f22-dirty_final-b-attack-suite.txt)
passed in 125.90 s. Both suites have zero failures/skips, including all 17 mutant
kills and all seven registered names. [Registry/source verification](05_evidence/final-b-registry-verification.json)
records source and XML hashes; no engine logic or historical result changed.

## Dashboard (Phase 5)

From Assignment1 with the existing venv active:

```powershell
python -m streamlit run 04_dashboard/app.py
```

Eight tabs cover Overview, Scaling, Original vs revised & variants, Throughput
& latency, Memory, Correctness, Bottleneck explained, and Method & data. Q7
construction and individual sales have separate views; 1M results, actual
latency histogram bins, early/late segments and post-cancellation state are
included. Sources, recorded engine commits and units accompany the views.

When Git and a checkout are available, the app reads a fixed HEAD snapshot using read-only `git show`: only committed
files under `03_results/runs/`, `05_evidence/`, `00_docs/FINAL_SELECTION.md` and
`07_attack/ATTACK_REPORT.md`. Working-tree changes and new local runs are
ignored in that mode. In a ZIP download/copied submission without a checkout,
or when Git is unavailable, it reads those same allowlisted paths from disk and
shows this banner at the top:

> Reading files from disk (no git checkout): values are not verified against a commit.

Disk paths are resolved within the submission root. Recorded run commits remain
visible as metadata, explicitly unverified in disk mode. Engine modules and
generators are never imported or executed.
`.streamlit/config.toml` disables usage telemetry and binds the local server
to 127.0.0.1; there are no remote data, font or chart requests in the app code.

Only complete raw-repeat sets with a matching saved summary and completed
worker enter medians, throughput or fits. Missing, invalid, stopped and not_run
cells stay explicit. A replay `phase_time_limit` can produce `> 600 s` and a
strict speedup lower bound; a subprocess/other timeout cannot. A large-cell
observation remains labelled **A: single trial**. Exponents use the measured
size range only. Memory peak/order is explicitly normalized by the maximum
sampled live count, never by an almost-empty final state.

Both fast comparisons remain visible; the same-session ratio and binding
rejection come from the committed rematch. Correctness counts refer to the
labelled committed evidence source, not uncommitted tests running locally.
Generator commands in Method & data are reconstructions from saved settings,
with local output paths; recorded archive hashes are not presented as hashes
of a regenerated file. Raw repeats, settings, environment and inclusion flags
are available in the tables.

Dashboard smoke/interaction and numerical checks:

```powershell
python -m pytest 02_tests/test_dashboard.py -q
python 04_dashboard/verify_saved.py                  # optional developer audit; requires Git
```

The [per-tab audit](05_evidence/dashboard-audit.json) traces sample displayed
values to their CSV/JSON/XML files. It is saved-file analysis, not measurement.

Phase 5 verification: [999 standard tests](05_evidence/20261123T190332Z_87ed911-dirty_dashboard-all-tests.txt)
passed in 785.23 s; [16 dashboard gates on the latest committed snapshot](05_evidence/20261123T191536Z_337cc61-dirty_dashboard-current-head-smoke.txt)
passed in 17.79 s. [Final verification](05_evidence/dashboard-verification.json)
records source and XML hashes. All eight tabs and interactive selections render;
headline numbers match CSVs. No new benchmark or engine change.

## Clean-environment run path (PowerShell, from this folder)
```powershell
python -m venv "$env:USERPROFILE\.venvs\aif-a1"
& "$env:USERPROFILE\.venvs\aif-a1\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
python -m pytest -q                                   # latest checkpoint: 1027 passed
python run.py lob.replay 06_data/supplied/worked_example.jsonl --version A
python run.py bench.run_all                           # (planned) writes 03_results/runs/<run>/
python -m streamlit run 04_dashboard/app.py           # localhost:8501; labelled disk fallback without Git
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

Replay also accepts `.jsonl.gz` and every name in the Final Version B table. Events stream in file order; the shared validator rejects
nonincreasing seq without advancing the last accepted seq. Each book starts empty;
neither inputs nor result history are retained by the replay command.

Malformed JSON, invalid UTF-8, UTF-16 and an unexpected additional BOM stop
replay with one stderr line, `<file>:<line>: <problem>`, and a non-zero exit
code. There is no traceback for these input errors. Line numbers include blank
lines; results from earlier valid lines remain on stdout. Valid JSON events
still use the unchanged validator and may produce normal JSON rejections.
One leading UTF-8 BOM, CRLF/bare-CR newlines, gzip and unbounded integers remain
supported. A BOM character inside a JSON string is ordinary data.

Pre-report robustness verification: [1,027 standard tests](05_evidence/20261123T194432Z_47c0048-dirty_robustness-all-tests.txt)
passed in 713.57 s; [1,995 attack tests](05_evidence/20261123T194432Z_47c0048-dirty_robustness-attack-suite.txt)
passed in 95.10 s. This includes 28 new regression cases and all eight tabs in
temporary no-checkout/no-Git copies. [Final review and source/XML hashes](05_evidence/robustness-verification.json)
confirm unchanged engines, validator, existing expectations and stored results.

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
GC enabled, one warm-up and five measured repeats for B and small A; seconds and raw trials are
saved. Parsing and construction are separate. Liquidation rebuilds each bid
book before the measured sale. Throughput is events / median replay seconds.
Declared 2026-11-22 before long measurements: A at 100k/1M uses one measured
trial, no warm-up (or stopped at 600 s); speedups must say **A: single trial**.
For these A cells, throughput uses that sole observation. Selection fallback
and the CSV/metadata commit policy are in BENCHMARK_PLAN.md. Future per-cell
jobs/journals/logs stay local through .gitignore; the superseded smoke is archived
intact in scratch. Historical final smoke results remain unchanged.

Optional B3r_fast (2026-11-22): B3r remains final unless every correctness gate
passes, the 15-cell official 100k geometric-mean replay time falls by at least 10%,
and no matched scenario median rises by more than 5%. This is a separate
constant-factor variant: exact-builtin common-case validation with reference
fallback, inlined process dispatch and local bindings in unchanged matching.
It preserves B3r's structures, thresholds, API, output order and counters.
Direct methods retain the inherited reference validator. No speedup is claimed
from correctness tests. The completed optional B-only session and its original
cross-session rejection remain historical. The corrected comparison follows.

Historical rematch protocol (2026-11-22, fixed before that measurement): the completed
cross-session trial stays **tried and rejected**. Session noise confounded its
per-cell 5% bound, so Laurin permits ONE binding same-session timing-only attempt.
Both versions alternate order by case on official + post_attack, warm-up+5.
Require current correctness proof, 15-cell official 100k geometric mean <= 0.90,
and median(seed ratios) <= 1.05 for every workload x size scenario. Otherwise
B3r stays final; no further re-measurement. The historical entry point was
`01_code/bench/rematch_fast.ps1`; its single measurement attempt is consumed.
The old cross-session wrapper/result remain historical; do not rerun them.
BENCHMARK_PLAN.md records the corrected method, one-attempt guard and report
that preserves both comparisons. The attempt is now complete and rejected;
FINAL_SELECTION.md is authoritative. Do not restart the rematch.
Historical rematch [standard tests](05_evidence/20261122T205138Z_ddbc434-dirty_rematch-all-tests.txt)
passed (848 in 713.71 s), as did the [attack suite](05_evidence/20261122T205139Z_ddbc434-dirty_rematch-attack-suite.txt)
(1,697 in 80.63 s). The [rematch proof](05_evidence/b3r_fast_rematch_correctness.json)
binds those tests to the rematch source, before the final registry update.

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
Tests (optional fast checkpoint): `python -m pytest -q -s --tb=short --basetemp=scratch/pytest-b3r-fast --junitxml=05_evidence/b3r-fast-all-tests.xml` -> `848 passed in 648.79s` (per-file table in `00_docs/AI_LOG.md`); committed attack suite -> `1697 passed in 79.31s` with --runxfail.
Benchmark (Phase 4a smoke only): `python run.py bench.run_all --part smoke --session phase4a_smoke_final` -> `03_results/runs/20261122T004602Z_5d8d15a-dirty_smoke/`, 216/216 cells OK; full grid pending.
Fresh-venv check: pending Phase 7 (existing pinned venv used through Phase 4a)

Q11 completed 2026-11-22: `06_data/supplied/generate_orders.py` was copied
byte-for-byte from the course package and checked against its MANIFEST.json
(entry size 4019 bytes and the sha256 above). Evidence:
`05_evidence/20261121T233959Z_b5411d4_phase3b-q11-generator-sha.txt`.
The evidence timestamp is UTC; the local session date is 2026-11-22.
The exercise-local `.gitattributes` marks this supplied file `-text` to preserve
its exact bytes under Windows Git line-ending conversion.

## Post-attack fallback B3r (2026-11-22)

B3r is registered alongside A/B1/B2/B3 (`--version B3r`). It inherits B3 and
adds one change: when a side has more stale heap keys than live levels AND more
than 32 stale keys, filter that side's existing heap list, heapify, and rebuild
in_heap. No levels-dict iteration or cross-side threshold is used. This adds
expected amortized O(1) cleanup per staled key, with a single-event
O(live+stale) logical-key spike. The per-side heap bound is 2*live_levels+32;
allocated hash capacity and GC remain separate costs. Default-off counters
record heap_rebuilds, heap_rebuild_keys_scanned and heap_rebuild_stale_removed.

Replay now accepts UTF-8 BOMs (plain/gzip) and arbitrary-length integers. Entering
the shared reader disables CPython's process-wide decimal conversion digit
guard, covering both JSON input and returned integer output; SPEC has no bound.

No price cap is added. Valid prices k*(2**61-1) collide in CPython integer hashes,
so dict/set costs lose their expected constant-time guarantee. At16000 levels
the committed attack measured A 5.75 s, B1 4.30s, B2 4.31s, B3 9.10s versus B3's
0.085s normal-hash control (107x slowdown, quadratic exponent 2.00). B3r retains
these hash structures. These are attributed attack results, independently
re-verified by Claude (chat) according to Laurin, not fresh Codex timings.
hash_full is not included in the added benchmark catalog.

B2's rotating-burst memory saturates with per-level historical peak capacity:
it is a reported weakness, not a filter violation. Deep_book is borderline
(official 3.05, attack re-run 2.80); far_end_flicker gives stronger evidence
(about 20.8x B1/B3). Post-attack cases cannot retroactively change the original
exclusions; B3r must pass them as additional requirements.

The current human-run schedule, source/data provenance and limits are in
[BENCHMARK_PLAN.md](00_docs/BENCHMARK_PLAN.md), section "Tonight's B3r session".
It runs B3r on all parts, B1/B2/B3 only on added cases, then A under its declared
baseline protocol. A new combined manifest is
[POST_ATTACK_MANIFEST.json](00_docs/POST_ATTACK_MANIFEST.json); generated files
remain ignored. Current checkpoint starts no long engine run.
