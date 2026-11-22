"""Run the full test suite and save one row per test case.

Usage (from Assignment1/):
    python 04_benchmarks/export_test_results.py

Writes 05_results/tests_by_case.csv with columns
    test, source, version, result
- test:    test function name (without the version parameter)
- source:  the test's @pytest.mark.source label (where expected values come from)
- version: a / b for tests that run an engine; "none" for tests that need no engine
- result:  pass / fail (a setup error counts as fail)
Exit code: pytest's exit code.
"""

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "05_results" / "tests_by_case.csv"


class Collector:
    def __init__(self):
        self.info = {}      # nodeid -> (test, source, version)
        self.result = {}    # nodeid -> pass / fail

    def pytest_collection_modifyitems(self, items):
        for item in items:
            marker = item.get_closest_marker("source")
            source = marker.args[0] if marker else "unlabelled"
            params = getattr(item, "callspec", None)
            module = params.params.get("lob") if params else None
            version = module.removeprefix("lob_") if module else "none"
            self.info[item.nodeid] = (item.originalname, source, version)

    def pytest_runtest_logreport(self, report):
        if report.failed:
            self.result[report.nodeid] = "fail"
        elif report.when == "call" and report.nodeid not in self.result:
            self.result[report.nodeid] = "pass"


def main():
    collector = Collector()
    code = pytest.main(["-q", "-p", "no:cacheprovider", str(ROOT / "02_tests")],
                       plugins=[collector])
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["test", "source", "version", "result"])
        for nodeid, (test, source, version) in collector.info.items():
            writer.writerow([test, source, version,
                             collector.result.get(nodeid, "not run")])
    print(f"wrote {OUT.relative_to(ROOT)}")
    return int(code)


if __name__ == "__main__":
    sys.exit(main())
