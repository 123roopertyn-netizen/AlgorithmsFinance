#!/usr/bin/env bash
# All Phase 6 benchmarks, one after the other (never in parallel: they would disturb each other's
# timings). Resumable: finished runs are skipped. Leave the machine idle while this runs.
#   bash bench/run_all.sh             # everything
#   bash bench/run_all.sh quick       # only the first steps that need no long runs
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
mkdir -p results
"$PY" -c "from bench.common import write_environment; write_environment()"
"$PY" -m bench.peaks
"$PY" -m bench.correctness
[[ "${1:-}" == "quick" ]] && exit 0
"$PY" -m bench.timing                  # primary timing, rules 1-3
"$PY" -m bench.counters                # separate instrumented runs follow
"$PY" -m bench.memory
"$PY" -m bench.latency
"$PY" -m bench.liquidation
"$PY" -m pytest -q > results/pytest_summary.txt 2>&1 || true
echo "done"
