# Saved canonical results

This directory is intentionally reserved for evidence produced from a clean,
committed Assignment 1 tree:

- `raw_measurements.json.gz`: canonical raw repeats, medians, latency samples,
  operation counts, correctness, memory, environment, settings, checksums and
  stopped-run evidence;
- `dashboard.html`: dependency-free dashboard generated only from that saved
  result; and
- optional manifest/checksum files derived from the same report.

Do not copy files from `tmp/` here. Smoke files identify a dirty tree and are
only pipeline tests. Canonical mode refuses to run before the measurement code
is committed and the Assignment 1 tree is clean.
