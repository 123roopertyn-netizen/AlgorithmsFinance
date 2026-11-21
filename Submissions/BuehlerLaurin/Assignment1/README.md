# Assignment 1, limit order book: Laurin Bühler

> Status (2026-11-21): Phase 2 baseline A, shared validation and replay implemented;
> awaiting Claude (chat) / Laurin review. B remains a Phase 3 stub, so the full
> suite intentionally has B-related failures. Benchmark/dashboard work is planned.

## Clean-environment run path (PowerShell, from this folder)
```powershell
python -m venv "$env:USERPROFILE\.venvs\aif-a1"
& "$env:USERPROFILE\.venvs\aif-a1\Scripts\Activate.ps1"
python -m pip install -r requirements.txt
python -m pytest -q                                   # includes expected Phase 3 B failures
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

Replay also accepts `.jsonl.gz` and `--version B` (B currently raises its Phase 3
`NotImplementedError`). Events stream in file order; the shared validator rejects
nonincreasing seq without advancing the last accepted seq. Each book starts empty;
neither inputs nor result history are retained by the replay command.

To run the currently implemented A/shared/data/CLI checks and all 17 mutants:

```powershell
python evidence.py phase2-a-check -- python -m pytest -q -k "not lob-B and not TestDifferential" --basetemp=scratch/pytest-a-check
```

The full suite keeps B contract checks, the B mutation control and the A/B
stateful test red until Phase 3. No xfails/skips conceal those missing behaviors.
The existing venv and pinned dependencies were used; no fresh-venv or benchmark
claim is made in Phase 2. See `05_evidence/INDEX.md` for saved runs.

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
python run.py datagen.check_reproduction --generator "<package dir>\generate_orders.py"
```

| File (seed 42, 10,000 events, levels 1000) | sha256 |
|---|---|
| `buildup_10000.jsonl.gz` | `441db8ecf37103113abfed079fbe4bdbe212bb7acbc31be0d344bab67c9b95b5` |
| `crowded_10000.jsonl.gz` | `112bc3ad120eb436e45608ef11ff804aed35aef24e43d4c10e5adda3b26577b6` |
| `mixed_10000.jsonl.gz` | `f5a027da6b31209d5e83c56bfbf8626604bb5f91e4176b784ff8a1dac1974a16` |
| `sweep_10000.jsonl.gz` | `c50755964212445574359b0fe4011f908ad2833edc900d49ecfa25948cca334f` |
| `cancel_churn_10000.jsonl.gz` | `7aef5f014e6d1e5d01cb37c7ff7b02cfcc5a30f185de8a4b33db2d32b3d9d933` |

**Own data (labelled *own*, separate from the supplied files):**
- `06_data/own/`: 18 small hand-designed edge-case streams with hand-calculated expected results (`<case>.expected.json`), written by `python run.py datagen.own_cases`; `python run.py datagen.own_cases --check` verifies that the committed files match the generator. Overview: `06_data/own/INDEX.md`.
- `01_code/datagen/adversarial.py`: own adversarial benchmark scenarios for Phase 4 (`deep_book`, `mid_queue_cancels`, `repeated_full_sweeps`; see SPEC.md). Not run yet; output will go to `06_data/generated/own/`.

Benchmark streams (M = 1k / 10k / 100k, seeds 42 / 43 / 44, five scenarios, 1M attempted) will be generated outside timing into `06_data/generated/` (git-ignored); the exact commands and their sha256 will be listed here.

## Measurement definitions
Units, what each phase contains, per call vs per batch, percentile convention, memory boundary.

## Results summary (3–5 lines)

## Revision summary

## Evidence block
Commit to audit: <hash> (filled in by Laurin)
Tests (Phase 2): `python -m pytest -q --tb=short --basetemp=scratch/pytest-final --junitxml=05_evidence/phase2-all-tests.xml` → `66 failed, 274 passed in 112.33s` (all 66 expected red for Phase 3 B; see `00_docs/AI_LOG.md` per-file table)
Benchmark: <command> → 03_results/runs/<run folder>/
Fresh-venv check: pending Phase 7 (existing pinned venv used in Phase 2)
