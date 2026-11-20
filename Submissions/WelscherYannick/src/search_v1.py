"""Version 1 of the three search methods.

Stubs only: the tests are written first and must fail until the methods are
implemented (slide 59, step 1).
"""

from interface import Method


def _not_implemented(*args, **kwargs):
    raise NotImplementedError("search_v1 is not implemented yet")


METHODS = {
    "linear": Method("linear", _not_implemented, _not_implemented),
    "binary": Method("binary", _not_implemented, _not_implemented),
    "hash": Method("hash", _not_implemented, _not_implemented),
}
