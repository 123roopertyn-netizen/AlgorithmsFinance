# Assignment 1 completion checklist

## Complete locally

- [x] Work is isolated to `Submissions/LaviBen/Assignment1/` on the topic branch.
- [x] Course generator and fixtures are copied byte-for-byte with SHA-256.
- [x] Contract and independent tests predate both implementations.
- [x] The failing tests-first checkpoint commit is recorded and reproducible.
- [x] Baseline and revised matching algorithms are preserved.
- [x] Worked example, conservation, FIFO, crossing, cancellation, validation,
  immutability, differential, fixture, and regression tests pass.
- [x] Revision, invariants, complexity, limitations, and AI decisions are documented.
- [x] Deterministic workload preparation covers five families, three required
  sizes, seeds 42/43/44, queue concentration, and liquidation.
- [x] Timing includes raw repeats, medians, parsing, replay, total application,
  throughput, construction and individual sale phases.
- [x] Latency includes raw per-event values, p50/p95/p99, event types, and
  early/late windows in a separate instrumentation run.
- [x] Memory uses fresh `tracemalloc` runs with explicit boundaries,
  checkpoints, cancellation cleanup, final output alive, and time limits.
- [x] Stopped runs are labeled and preserved; no values are clamped,
  extrapolated, invented, or silently omitted.
- [x] Dashboard and report builders load saved evidence only and are byte-stable.
- [x] Docker packaging is intentionally omitted because it is optional.

## Required before submission

- [x] Explicitly authorize and create the local pre-measurement commit.
- [x] Generate the canonical dataset grid from that committed code.
- [x] Run canonical five-repeat timing/latency/memory measurements from a clean tree.
- [x] Attempt the optional one-million-event case within the declared limit and
  retain stopped evidence if it is infeasible.
- [x] Generate `results/dashboard.html` and `REPORT.md` from canonical results.
- [x] Verify the dashboard visually and reproduce it byte-for-byte.
- [x] Run the complete test suite and final Git scope/secret checks.
- [x] Record audited measurement commit
  `ffb474170b4849af850e31588f9a1a70dcf08da3` in the raw evidence and report.
- [ ] Push only when Ben Lavi explicitly requests it; do not merge the pull request.
