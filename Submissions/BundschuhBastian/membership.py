"""Membership of queries in an integer ID array, three methods (Classes 3-4, Lab Phase 1).

Common interface for every method:
    method(ids, queries) -> list[bool]
One bool per query, same order as `queries`. `ids` and `queries` are never changed.

Version 1 (this file, step 3). Both search procedures are written by hand.
Allowed library parts: sorted() and set(). The operator `in` on a list is not used.
"""


def linear_search(ids, queries):
    """For each query, scan `ids` from the first entry until a match or the end.

    Time: O(n) per query, so O(n * q) for q queries. Extra memory: O(q) for the output.
    """
    result = []
    for query in queries:
        found = False
        for item in ids:
            if item == query:
                found = True
                break
        result.append(found)
    return result


def _search_recursive(sorted_ids, query, low, high):
    """Is `query` among sorted_ids[low..high] (both ends included)?

    Invariant: if `query` is anywhere in sorted_ids, it lies in sorted_ids[low..high].
    Each call either finds it or cuts the range to at most half. Empty range -> absent.
    """
    if low > high:
        return False
    middle = (low + high) // 2
    value = sorted_ids[middle]
    if value == query:
        return True
    if value < query:
        return _search_recursive(sorted_ids, query, middle + 1, high)
    return _search_recursive(sorted_ids, query, low, middle - 1)


def binary_search_recursive(ids, queries):
    """Sort a copy once, then answer every query by recursive binary search.

    Preparation: sorted() builds a new sorted list, O(n log n) time, O(n) memory.
    Per query: O(log n) time, recursion depth O(log n). Extra memory: O(n + q).
    """
    sorted_ids = sorted(ids)            # new list; `ids` itself stays as it was
    last = len(sorted_ids) - 1
    return [_search_recursive(sorted_ids, query, 0, last) for query in queries]


def hash_set_membership(ids, queries):
    """Build a Python set once, then answer every query with a hash lookup.

    Preparation: set(ids) is O(n) on average. Per query: O(1) on average, O(n) worst case
    (many hash collisions). Extra memory: O(n + q). Duplicates collapse inside the set.
    """
    lookup = set(ids)
    return [query in lookup for query in queries]


# Registry used by the tests (and later by the timing/memory scripts).
# Name -> function. Version 2 entries are added in step 4.
METHODS = {
    "linear_v1": linear_search,
    "binary_v1": binary_search_recursive,
    "hash_v1": hash_set_membership,
}
