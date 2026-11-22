# Measurement-integrity regression baseline

Date: 21 November 2026 (Europe/Berlin)
Interpreter: CPython 3.14.7
Implementation checkpoint: `80e487b03686d5f7b36f05a3b84fb10e5199c5db`

The regression expectations below were added before changing measurement,
dashboard, report, or order-book implementation code. The matching-engine
implementation was unchanged for these runs.

## Measurement regressions

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_measurement.py' -v
```

Observed result:

- Exit status: `1`
- Tests run: `15`
- Failures: `3`
- Errors: `3`
- `compare_versions` inspected each canonical book once rather than after all
  three diagnostic events (`[1, 1]` calls instead of `[3, 3]`).
- The prior parsed input was released after the next timing window opened.
- Liquidation-book cleanup occurred at clock counts `5, 9, 13, 17, 21`
  instead of outside the windows at multiples of four.
- A sale skipped after build timeout had no `attempted` marker and carried the
  build elapsed time.
- Timing summaries had no explicit partial-completion status.
- Report validation rejected the intended explicit unattempted timing record
  with `elapsed_seconds: null`.

## Saved-result presentation regressions

Commands:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_dashboard.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_reporting.py' -v
```

Observed result:

- Dashboard exit status: `1`; one of two tests failed because stopped,
  partial, and missing evidence was not identified together and no completion
  status was exposed.
- Report exit status: `1`; one of two tests failed because partial timing
  summaries were not disclosed.

## Full-suite checkpoint

The first full-suite attempt was manually interrupted with exit status `130`
after more than three minutes in the new supplied-stream state comparison.
The first presentation regression had already failed and every preceding
matching-contract test had passed. The delay came from duplicate public book
inspection in the new test, not matching. Before any implementation change,
the test was narrowed to the required two canonical inspections per event by
removing two redundant invariant inspections; no expected result was weakened.

These failures establish that the new regression suite detects the reviewed
measurement and saved-evidence defects before their fixes.

## Strict timeout-instrumentation boundary

A subsequent read-only review identified that completed clocks stopped after
the timeout context exited, so alarm-handler teardown was included. Two
deterministic context-order tests were added before that code changed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_measurement.py' -v
```

Observed result:

- Exit status: `1`
- Tests run: `2`
- Failures: `2`
- Replay order was `clock1`, timeout entry, processing, timeout exit, `clock2`
  instead of placing both clock reads inside the context.
- All 24 liquidation clock reads occurred while the timeout context was
  inactive.

This extended the same cleanup-outside-timing contract; it did not change an
existing expected result.

## Legacy evidence labeling

After the lifecycle fix, two presentation regressions were added to prevent
the superseded clean-tree archive from still receiving a canonical label:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_dashboard.DashboardTests.test_legacy_clean_report_is_marked_superseded -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_reporting.py' -v
```

Observed result:

- Dashboard exit status: `1`; one test ran and failed because the legacy report
  had no superseded label and still contained the canonical clean-tree label.
- Report exit status: `1`; three tests ran and one failed because the legacy
  report was rendered as `Canonical clean-tree evidence.`

The saved report needed a corrected-measurement revision marker before either
builder could safely grant canonical status.

## Partial-summary chart treatment

The dashboard suite was then strengthened to require ordinary timing curves to
plot complete repeat sets only while partial summaries remain in the explicit
exception table:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_dashboard.py' -v
```

Observed result: exit status `1`; three tests ran and one failed because the
dashboard neither stated this rule nor filtered timing/liquidation curves by
`completion_status`.

## Null source in derived application totals

A compatibility regression covered the schema-valid case where a source
operation was not attempted and therefore has a null elapsed value:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  tests.test_measurement.MeasurementContractTests.test_application_total_handles_unattempted_null_source -v
```

Observed result: exit status `1`; one test ran and errored with `TypeError`
because `append_application_totals` called `float(None)`. The expected derived
record retains the known parse duration, marks the operation unattempted, and
keeps the combined record stopped rather than omitting it.

## Dashboard placeholder preservation

The dashboard byte-stability test was extended with saved text equal to its
HTML template placeholder names:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_dashboard.py' -v
```

Observed result: exit status `1`; three tests ran and one failed because
sequential global replacement rewrote placeholder-like text inside the
embedded saved report. Template substitution must process only placeholders in
the original template, never recursively alter inserted evidence.

## Fresh-audit integrity revision gate

The report test was changed first to require canonical evidence produced by
measurement-integrity revision 3; revision 2 must remain explicitly
superseded:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_reporting.py' -v
```

Observed result before changing `build_report.py`:

- Exit status: `1`
- Tests run: `3`
- Failures: `1`
- A clean canonical report carrying `measurement_integrity_revision: 2` was
  still presented as `Canonical clean-tree evidence.` instead of superseded.

After raising the report gate to revision 3, the same command exited `0` with
all three tests passing.

## Direct-method contract and boundary cases

Operation-specific contract tests and independent boundary/FIFO examples were
added before changing `orderbook/common.py`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python3 -m unittest \
  test_contract test_validation
```

Observed result before implementation:

- Exit status: `1`
- Tests run: `16`
- Failures: `6`
- Both implementations allowed `AddLimitOrder(CANCEL)`,
  `CancelOrder(MARKET_SELL)`, and `FillMarketSell(LIMIT)` to mutate state rather
  than rejecting the wrong operation type atomically.
- The newly added negative/zero/noninteger, ask-FIFO, and crossing-residual
  expected-value cases already passed.

After freezing and enforcing the direct-method contract, the focused and
broader algorithm suite ran 21 tests with exit status `0`. The matching
implementations in `baseline.py` and `revised.py` did not change.

## Fresh-audit measurement regressions

The fresh-audit measurement expectations were added before changing
`measurement/metrics.py` or `tools/run_benchmarks.py`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_measurement.py'
```

Observed result before implementation:

- Exit status: `1`
- Tests run: `24`
- Failures: `9`
- Errors: `3`
- Unpaired parse/replay repeats were silently omitted from derived totals.
- Timing summaries did not disclose expected or missing repeat counts.
- Operation diagnostics had no timeout and processed full streams instead of
  the configured diagnostic prefix.
- Only 16 of 24 tracked liquidation correctness objects were released before
  timing began.
- The revision-3 integrity marker was absent.
- Report validation accepted non-Boolean flags, contradictory summaries,
  negative memory, incorrect latency percentiles, and duplicate raw repeats.

After implementation, the suite contained 25 tests and exited `0`. A real
single-dataset smoke report also validated as measurement-integrity revision 3.

## Missing-repeat report disclosure

The report regression was added before changing the report aggregation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_reporting.py' -v
```

Observed result before implementation: exit status `1`; four tests ran and one
failed because a summary with two completed, one stopped, and two missing
repeats was rendered as `2/3`. The report also omitted the total missing-repeat
count. After the fix, the same suite exited `0` and renders
`2/5 (1 stopped, 2 missing)` plus the missing total.

The same report suite was then extended before implementation to require
bounded operation-count coverage. It exited `1` with one failure because the
table labeled the processed diagnostic prefix as full `M` and omitted the
requested count. After changing the table to `Requested / processed`, the five
reporting tests exited `0` and render values such as `100 / 100`.

## Latency distribution and revision-3 dashboard gate

Dashboard tests were extended before implementation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_dashboard.py' -v
```

Observed result before implementation: exit status `1`; four tests ran and
three failed. The dashboard had no ECDF, still granted canonical status to
revision 2, omitted expected/missing repeat fields, and labeled prefix
operation counts only by processed `M`. After implementation, all four tests
passed. The embedded JavaScript also passed `node --check`; the ECDF consumes
only the report's saved `samples_ns` values.

## Fully stopped summary coverage

Canonical report review exposed that a fully stopped timing-summary row was
excluded before aggregation, understating grouped repeat coverage. The report
test was added before changing `build_report.py`:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests \
  -p 'test_reporting.py' -v
```

Observed result before implementation: exit status `1`; six tests ran and one
failed because two completed repeats plus three stopped repeats and a second
fully stopped five-repeat row rendered as `2/5 (3 stopped)` instead of
`2/10 (8 stopped)`. After including fully stopped summaries in aggregation,
all six reporting tests exited `0`.
