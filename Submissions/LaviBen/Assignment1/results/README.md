# Superseded saved-result archive

This directory preserves evidence produced from clean measurement commit
`ffb474170b4849af850e31588f9a1a70dcf08da3`, but it is no longer accepted as
current canonical evidence. Later audits found timing and evidence-integrity
defects in that revision: prior parse/liquidation objects could be released in
a following timing window, timeout instrumentation was included in completed
elapsed values, unequal repeat sets could be omitted, large operation-count
runs were unbounded, correctness objects survived into later phases, and
skipped, partial, or missing work was not presented precisely enough. The
archive predates `measurement_integrity_revision: 3`.

The archive contains:

- `raw_measurements.json.gz`: canonical raw repeats, medians, latency samples,
  operation counts, correctness, memory, environment, settings, checksums and
  stopped-run evidence;
- `dashboard.html`: dependency-free dashboard generated only from that saved
  result; and
- `CHECKSUMS.json`: sizes and SHA-256 fingerprints for the raw report,
  dashboard, and root `REPORT.md`.

The current dashboard builder additionally renders a latency ECDF from saved
samples, shows requested/processed diagnostic coverage, and grants canonical
status only to clean revision-3 evidence. Rebuilding this legacy archive with
the current builder must still label it superseded.

The raw report contains 73 datasets and 3,744 records, including the declared
one-million-event attempt and labeled stopped evidence. Its checksums remain
useful for provenance, but none of these artifacts should be cited as final
performance or memory evidence. They will be replaced only after the corrected
measurement code is explicitly authorized for commit and a new canonical run
is made from a clean tree. Revision-3 smoke checks remain provisional. Files in
`tmp/` remain ignored smoke or byte-stability checks and are not submission
evidence.
