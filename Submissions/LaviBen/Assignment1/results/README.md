# Saved canonical results

This directory contains canonical evidence produced from clean measurement
commit `ffb474170b4849af850e31588f9a1a70dcf08da3`:

- `raw_measurements.json.gz`: canonical raw repeats, medians, latency samples,
  operation counts, correctness, memory, environment, settings, checksums and
  stopped-run evidence;
- `dashboard.html`: dependency-free dashboard generated only from that saved
  result; and
- `CHECKSUMS.json`: sizes and SHA-256 fingerprints for the raw report,
  dashboard, and root `REPORT.md`.

The raw report contains 73 datasets and 3,744 records, including the declared
one-million-event attempt and labeled stopped evidence. Files in `tmp/` remain
ignored smoke or byte-stability checks and are not submission evidence.
