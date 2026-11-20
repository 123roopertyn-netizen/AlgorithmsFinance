"""Original versions (v1) of the three membership methods.

Shared specification: see ``membership/__init__.py`` (LAB_SPEC.md F1-F6).
Every function leaves its arguments unchanged and returns a new list.

Planned v1 behaviour (implemented in Step 5):
    linear  prepare: return ids as is (no copy)          O(1)
            query:   scan ids per query, stop at a match O(n) per query, O(n*q) total
    binary  prepare: sorted copy, ``sorted(ids)``        O(n log n)
            query:   recursive binary search that slices the list (decision Q3).
                     Slicing copies up to n/2 elements per step, so one query
                     costs O(n), not O(log n). Kept naive on purpose; fixed in v2.
    hash    prepare: ``set(ids)``                        expected O(n)
            query:   ``x in s`` per query               expected O(1) per query

Status: stubs. Every function raises NotImplementedError so the tests fail (R1).
"""

from __future__ import annotations

from collections.abc import Sequence


def linear_prepare(ids: Sequence[int]) -> Sequence[int]:
    """Return the input itself as the state (no copy, no preparation cost)."""
    raise NotImplementedError


def linear_query(state: Sequence[int], queries: Sequence[int]) -> list[bool]:
    """For each query, scan ``state`` from the left and stop at the first match."""
    raise NotImplementedError


def binary_prepare(ids: Sequence[int]) -> list[int]:
    """Return a sorted copy of ``ids``. The caller's sequence is not sorted in place."""
    raise NotImplementedError


def binary_query(state: list[int], queries: Sequence[int]) -> list[bool]:
    """For each query, run a recursive, slicing binary search on the sorted ``state``."""
    raise NotImplementedError


def hash_prepare(ids: Sequence[int]) -> set[int]:
    """Return a ``set`` built from ``ids``."""
    raise NotImplementedError


def hash_query(state: set[int], queries: Sequence[int]) -> list[bool]:
    """For each query, look it up in the set ``state``."""
    raise NotImplementedError
