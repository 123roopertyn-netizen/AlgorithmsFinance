"""Membership of queries in an integer ID array, three methods (Classes 3-4, Lab Phase 1).

Common interface for every method:
    method(ids, queries) -> list[bool]
One bool per query, same order as `queries`. `ids` and `queries` are never changed.

STEP 1: these are STUBS. They only exist so the tests can be run and seen to fail.
"""


def linear_search(ids, queries):
    raise NotImplementedError("step 3")


def binary_search_recursive(ids, queries):
    raise NotImplementedError("step 3")


def hash_set_membership(ids, queries):
    raise NotImplementedError("step 3")


# Registry used by the tests (and later by the timing/memory scripts).
# Name -> function. Version 2 entries are added in step 4.
METHODS = {
    "linear_v1": linear_search,
    "binary_v1": binary_search_recursive,
    "hash_v1": hash_set_membership,
}
