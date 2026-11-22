# Canonical saved-result archive

This directory contains evidence produced from clean measurement commit
`3d4bacb5eb2527ac9b5be709d8cfad74b2c4da90` using
`measurement_integrity_revision: 3`. It replaces the superseded archive from
`ffb474170b4849af850e31588f9a1a70dcf08da3` after timing, lifecycle,
repeat-accounting, diagnostic-boundary and presentation defects were repaired.

The archive contains:

- `raw_measurements.json.gz`: canonical raw repeats, medians, latency samples,
  operation counts, correctness, memory, environment, settings, checksums and
  stopped-run evidence;
- `dashboard.html`: dependency-free dashboard generated only from that saved
  result; and
- `CHECKSUMS.json`: sizes and SHA-256 fingerprints for the raw report,
  dashboard, and root `REPORT.md`.

The dashboard renders a latency ECDF from saved samples, shows
requested/processed diagnostic coverage, exposes partial/stopped/missing work,
and grants canonical status only to clean revision-3 evidence.

The raw report contains 73 datasets and 3,744 records, including the declared
one-million-event attempt and labeled stopped evidence. All 76 completed
correctness rows agree, 15 correctness attempts stopped at the declared limit,
and no timing repeat is missing. The dashboard and root report rebuild
byte-for-byte from the raw report; `CHECKSUMS.json` fingerprints all three.
Files in `tmp/` remain ignored smoke or byte-stability checks and are not
submission evidence.
