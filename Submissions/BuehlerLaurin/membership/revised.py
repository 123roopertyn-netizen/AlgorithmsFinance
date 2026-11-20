"""Revised versions (v2) of the three membership methods.

Shared specification: see ``membership/__init__.py`` (LAB_SPEC.md F1-F6).

Decisions (LAB_SPEC.md section 4):
    Q3  binary: the fastest correct hand-written binary search we can find:
        iterative, index-based, no slicing copies. O(log n) per query.
        Candidate variants are compared by measurement in Step 6.
    Q4  linear and hash: unchanged. The v1 functions are re-exported here so
        that every method has a "revised" entry in the registry.

Status: binary search v2 is a stub that raises NotImplementedError (R1).
The original module is never edited by the revision (R5).
"""

from __future__ import annotations

from collections.abc import Sequence

# Q4: unchanged in v2, reused from v1.
from membership.original import (  # noqa: F401  (re-exported)
    hash_prepare,
    hash_query,
    linear_prepare,
    linear_query,
)


def binary_prepare(ids: Sequence[int]) -> list[int]:
    """Return a sorted copy of ``ids``. The caller's sequence is not sorted in place."""
    raise NotImplementedError


def binary_query(state: list[int], queries: Sequence[int]) -> list[bool]:
    """For each query, run an iterative, index-based binary search on ``state``."""
    raise NotImplementedError
