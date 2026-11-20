"""Tests for the memory script: structure, fresh traces, and sensible byte counts."""
import sys
import tracemalloc
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bench_memory  # noqa: E402
from datagen import generate  # noqa: E402
from membership import METHODS  # noqa: E402


def cell(rows, method, phase, field="median_current_bytes"):
    (row,) = [r for r in rows if r["method"] == method and r["phase"] == phase]
    return row[field]


@pytest.fixture(scope="module")
def results():
    return bench_memory.run_benchmark([1000], [1, 100], ["mixed"], repeats=2, seed=3)


def test_rows_cover_all(results):
    raw, summary = results
    assert len(summary) == 1 * 2 * 1 * len(METHODS) * 3
    assert len(raw) == len(summary) * 2


def test_tracing_is_off_afterwards(results):
    assert not tracemalloc.is_tracing()


def test_linear_has_no_prepared_structure(results):
    _, summary = results
    one = [r for r in summary if r["q"] == 1]
    assert cell(one, "linear_v1", "prepare") == 0


def test_sorted_copy_is_one_pointer_per_id(results):
    _, summary = results
    one = [r for r in summary if r["q"] == 1]
    ids = generate(1000, 1, "mixed", "none", 3).ids
    assert cell(one, "binary_v1", "prepare") == sys.getsizeof(sorted(ids))   # 8n + header
    assert cell(one, "binary_v2", "prepare") == cell(one, "binary_v1", "prepare")


def test_set_needs_more_memory_than_sorted_copy(results):
    _, summary = results
    one = [r for r in summary if r["q"] == 1]
    assert cell(one, "hash_v1", "prepare") > cell(one, "binary_v1", "prepare") > 0


def test_total_peak_contains_structure_and_output(results):
    _, summary = results
    hundred = [r for r in summary if r["q"] == 100]
    for method in METHODS:
        prepared = cell(hundred, method, "prepare")
        output = cell(hundred, method, "query")
        assert cell(hundred, method, "total", "median_peak_bytes") >= prepared + output \
            or method == "linear_v1"
        assert cell(hundred, method, "total", "median_peak_bytes") >= \
            cell(hundred, method, "total")
        assert cell(hundred, method, "query", "median_peak_bytes") >= output


def test_output_grows_with_q(results):
    _, summary = results
    for method in METHODS:
        small = cell([r for r in summary if r["q"] == 1], method, "total")
        large = cell([r for r in summary if r["q"] == 100], method, "total")
        assert large > small


def test_input_is_not_traced():
    data = generate(2000, 3, "mixed", "none", 1)
    ids_bytes = sys.getsizeof(data.ids)
    rows = bench_memory.measure_method("linear_v1", data, repeats=1)
    total = [r for r in rows if r["phase"] == "total"][0]
    assert total["peak_bytes"] < ids_bytes / 10          # far below the size of the input
