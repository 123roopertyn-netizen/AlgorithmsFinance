"""Tests for all membership methods. Every test runs once per method.

The oracle for expected answers is written by hand or uses Python's `in` operator.
`in` is used ONLY inside the tests, never inside the methods under test.
"""
import copy
import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from membership import METHODS  # noqa: E402


@pytest.fixture(params=sorted(METHODS), ids=sorted(METHODS))
def method(request):
    return METHODS[request.param]


def oracle(ids, queries):
    return [q in ids for q in queries]


# ---- slide example and tiny cases -------------------------------------------------

def test_slide_example(method):
    assert method([7, 11, 7], [11, 9, 7]) == [True, False, True]


def test_empty_array(method):
    assert method([], [1, 2, 3]) == [False, False, False]


def test_empty_queries(method):
    assert method([1, 2, 3], []) == []


def test_both_empty(method):
    assert method([], []) == []


def test_one_entry_present(method):
    assert method([4], [4]) == [True]


def test_one_entry_absent(method):
    assert method([4], [5, 3, 0, -4]) == [False, False, False, False]


# ---- duplicates, order of the array ------------------------------------------------

def test_duplicates(method):
    assert method([5, 5, 5, 5], [5, 6, 4]) == [True, False, False]


def test_duplicates_mixed(method):
    ids = [3, 1, 3, 2, 1, 3]
    assert method(ids, [1, 2, 3, 0, 4]) == [True, True, True, False, False]


def test_unsorted_input(method):
    ids = [90, -5, 42, 7, 1000, 0, 13]
    assert method(ids, [7, 90, 1000, -5, 8, 14]) == [True, True, True, True, False, False]


def test_descending_input(method):
    ids = [9, 7, 5, 3, 1]
    assert method(ids, [9, 1, 5, 2, 10, 0]) == [True, True, True, False, False, False]


# ---- positions: first, last, middle, just outside ----------------------------------

@pytest.mark.parametrize("n", [1, 2, 3, 4, 5, 8, 9, 16, 17])
def test_every_position_and_every_gap(method, n):
    ids = [10 * i for i in range(n)]            # 0, 10, ..., 10(n-1)
    present = ids
    absent = [-1] + [10 * i + 5 for i in range(n)]   # below first, gaps, above last
    assert method(ids, present) == [True] * n
    assert method(ids, absent) == [False] * (n + 1)


def test_first_and_last_of_unsorted(method):
    ids = [50, 20, 80, 10, 70]       # first = 50, last = 70, min = 10, max = 80
    assert method(ids, [50, 70, 10, 80]) == [True, True, True, True]


def test_smaller_and_larger_than_all(method):
    ids = [10, 20, 30]
    assert method(ids, [9, 31, -10**9, 10**9]) == [False] * 4


def test_negative_and_large_values(method):
    ids = [-2**63, -1, 0, 2**63 - 1]
    assert method(ids, [-2**63, 2**63 - 1, -2, 1]) == [True, True, False, False]


# ---- output shape and order --------------------------------------------------------

def test_output_order_follows_queries(method):
    ids = [1, 2, 3]
    queries = [3, 9, 1, 8, 2, 7]
    assert method(ids, queries) == [True, False, True, False, True, False]


def test_repeated_queries_in_one_batch(method):
    assert method([1, 2], [2, 2, 3, 3, 2]) == [True, True, False, False, True]


def test_output_is_list_of_bool(method):
    out = method([1, 2, 3], [2, 5])
    assert isinstance(out, list)
    assert all(type(x) is bool for x in out)
    assert len(out) == 2


# ---- input unchanged ---------------------------------------------------------------

def test_input_unchanged(method):
    ids = [9, 3, 7, 3, 1]
    queries = [3, 4, 9]
    ids_before, queries_before = copy.deepcopy(ids), copy.deepcopy(queries)
    ids_object = ids
    method(ids, queries)
    assert ids == ids_before            # same values, same order (not sorted in place)
    assert queries == queries_before
    assert ids is ids_object


def test_input_unchanged_when_empty(method):
    ids, queries = [], []
    method(ids, queries)
    assert ids == [] and queries == []


def test_output_is_not_the_input(method):
    queries = [1]
    out = method([1], queries)
    assert out is not queries


# ---- repeated calls ----------------------------------------------------------------

def test_repeated_calls_same_result(method):
    ids = [8, 2, 6, 4]
    queries = [2, 3, 8, 9]
    first = method(ids, queries)
    second = method(ids, queries)
    third = method(ids, queries)
    assert first == second == third == [True, False, True, False]


def test_no_state_leaks_between_arrays(method):
    assert method([1, 2, 3], [3]) == [True]
    assert method([4, 5, 6], [3]) == [False]     # 3 was in the previous array only
    assert method([1, 2, 3], [3]) == [True]


def test_output_lists_are_independent(method):
    first = method([1], [1])
    first.append(False)
    assert method([1], [1]) == [True]


# ---- random tests against the oracle ----------------------------------------------

@pytest.mark.parametrize("seed", range(20))
def test_random_against_oracle(method, seed):
    rng = random.Random(seed)
    n = rng.randint(0, 60)
    q = rng.randint(0, 60)
    ids = [rng.randint(-30, 30) for _ in range(n)]       # small range -> many duplicates
    queries = [rng.randint(-35, 35) for _ in range(q)]   # some present, some absent
    snapshot = list(ids)
    assert method(ids, queries) == oracle(ids, queries)
    assert ids == snapshot


def test_all_methods_agree_on_larger_input():
    rng = random.Random(2024)
    ids = [rng.randrange(10_000) for _ in range(2_000)]
    queries = [rng.randrange(-100, 10_100) for _ in range(500)]
    expected = oracle(ids, queries)
    for name, fn in METHODS.items():
        assert fn(ids, queries) == expected, name
