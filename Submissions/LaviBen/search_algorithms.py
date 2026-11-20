"""Membership algorithms with a shared ordered-query contract.

Each public function accepts an integer ID sequence and an ordered query
sequence. It returns one Boolean per query without changing either input.
"""

from __future__ import annotations

from collections.abc import Sequence


def linear_search(ids: Sequence[int], queries: Sequence[int]) -> list[bool]:
    """Search for every query by scanning ``ids`` from left to right."""

    results: list[bool] = []
    for query in queries:
        found = False
        for candidate in ids:
            if candidate == query:
                found = True
                break
        results.append(found)
    return results


def _recursive_contains(
    sorted_ids: Sequence[int],
    query: int,
    low: int,
    high: int,
) -> bool:
    """Return whether ``query`` occurs between inclusive indices low/high."""

    if low > high:
        return False

    middle = low + (high - low) // 2
    candidate = sorted_ids[middle]
    if candidate == query:
        return True
    if candidate < query:
        return _recursive_contains(sorted_ids, query, middle + 1, high)
    return _recursive_contains(sorted_ids, query, low, middle - 1)


def binary_search_recursive_v1(
    ids: Sequence[int],
    queries: Sequence[int],
) -> list[bool]:
    """Version 1: recursively search one sorted copy for every query."""

    sorted_ids = sorted(ids)
    last_index = len(sorted_ids) - 1
    return [
        _recursive_contains(sorted_ids, query, 0, last_index)
        for query in queries
    ]


def binary_search(ids: Sequence[int], queries: Sequence[int]) -> list[bool]:
    """Version 2: iteratively search one sorted copy for every query.

    The iterative loop preserves the same ``O(n log n + q log n)`` time bound
    as version 1 while avoiding one Python function call per search step.
    """

    sorted_ids = sorted(ids)
    results: list[bool] = []

    for query in queries:
        low = 0
        high = len(sorted_ids) - 1
        found = False

        while low <= high:
            middle = low + (high - low) // 2
            candidate = sorted_ids[middle]
            if candidate == query:
                found = True
                break
            if candidate < query:
                low = middle + 1
            else:
                high = middle - 1

        results.append(found)

    return results


def hash_set_membership(
    ids: Sequence[int],
    queries: Sequence[int],
) -> list[bool]:
    """Build one standard-library hash set, then test queries in order."""

    lookup = set(ids)
    return [query in lookup for query in queries]
