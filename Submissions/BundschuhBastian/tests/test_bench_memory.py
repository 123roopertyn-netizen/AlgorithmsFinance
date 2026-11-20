"""Tests for the memory script: structure, fresh traces, and byte counts that scale as expected.

Exact byte counts depend on the Python version (tracemalloc and the interpreter add a small
constant overhead, e.g. 400 bytes on 3.10). So the tests allow a constant overhead of
OVERHEAD bytes and check how the numbers GROW with n and q instead of exact values.
"""
import sys
import tracemalloc
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bench_memory  # noqa: E402
from datagen import generate  # noqa: E402
from membership import METHODS  # noqa: E402

OVERHEAD = 1024            # allowed constant, version-dependent bytes
SMALL, LARGE = 1000, 5000  # two sizes to measure growth


def cell(rows, method, phase, n, q, field="median_current_bytes"):
    (row,) = [r for r in rows if r["method"] == method and r["phase"] == phase
              and r["n"] == n and r["q"] == q]
    return row[field]


@pytest.fixture(scope="module")
def summary():
    _, rows = bench_memory.run_benchmark([SMALL, LARGE], [1, 100], ["mixed"],
                                         repeats=2, seed=3)
    return rows


def test_rows_cover_all(summary):
    assert len(summary) == 2 * 2 * 1 * len(METHODS) * 3


def test_tracing_is_off_afterwards(summary):
    assert not tracemalloc.is_tracing()


def test_linear_prepare_is_small_and_does_not_grow_with_n(summary):
    small = cell(summary, "linear_v1", "prepare", SMALL, 1)
    large = cell(summary, "linear_v1", "prepare", LARGE, 1)
    assert small <= OVERHEAD and large <= OVERHEAD      # no structure is built
    assert abs(large - small) <= OVERHEAD               # and 5x more ids add nothing


@pytest.mark.parametrize("method", ["binary_v1", "binary_v2"])
def test_sorted_copy_grows_about_8_bytes_per_id(summary, method):
    small = cell(summary, method, "prepare", SMALL, 1)
    large = cell(summary, method, "prepare", LARGE, 1)
    per_id = (large - small) / (LARGE - SMALL)          # one pointer per id
    assert 7.5 <= per_id <= 8.5
    assert small >= 8 * SMALL                           # at least the pointer array


def test_both_binary_versions_prepare_the_same_amount(summary):
    for n in (SMALL, LARGE):
        v1 = cell(summary, "binary_v1", "prepare", n, 1)
        v2 = cell(summary, "binary_v2", "prepare", n, 1)
        assert abs(v1 - v2) <= OVERHEAD


def test_set_grows_faster_than_sorted_copy(summary):
    set_growth = (cell(summary, "hash_v1", "prepare", LARGE, 1)
                  - cell(summary, "hash_v1", "prepare", SMALL, 1)) / (LARGE - SMALL)
    sorted_growth = (cell(summary, "binary_v1", "prepare", LARGE, 1)
                     - cell(summary, "binary_v1", "prepare", SMALL, 1)) / (LARGE - SMALL)
    assert set_growth > 2 * sorted_growth               # hash table is larger than n pointers
    assert cell(summary, "hash_v1", "prepare", LARGE, 1) > \
        cell(summary, "binary_v1", "prepare", LARGE, 1)


def test_total_peak_contains_structure_and_output(summary):
    for method in METHODS:
        for n in (SMALL, LARGE):
            prepared = cell(summary, method, "prepare", n, 100)
            output = cell(summary, method, "query", n, 100)
            peak = cell(summary, method, "total", n, 100, "median_peak_bytes")
            assert peak + OVERHEAD >= prepared + output
            assert peak >= cell(summary, method, "total", n, 100)    # peak >= current
            assert cell(summary, method, "query", n, 100, "median_peak_bytes") >= output


def test_output_grows_with_q(summary):
    for method in METHODS:
        small = cell(summary, method, "total", LARGE, 1)
        large = cell(summary, method, "total", LARGE, 100)
        assert large - small > 400                      # about 8 bytes x 99 more queries


def test_output_does_not_grow_with_n(summary):
    for method in METHODS:
        small = cell(summary, method, "total", SMALL, 100)
        large = cell(summary, method, "total", LARGE, 100)
        assert abs(large - small) <= OVERHEAD


def test_input_is_not_traced():
    data = generate(20_000, 3, "mixed", "none", 1)
    ids_bytes = sys.getsizeof(data.ids)                 # about 160 kB
    rows = bench_memory.measure_method("linear_v1", data, repeats=1)
    total = [r for r in rows if r["phase"] == "total"][0]
    assert total["peak_bytes"] < ids_bytes / 10         # far below the size of the input
