"""Shared pytest setup: every test that uses the `lob` fixture runs once per
order-book version listed here."""

import importlib

import pytest

VERSIONS = ["lob_a"]  # add "lob_b" here once Version B exists


@pytest.fixture(params=VERSIONS)
def lob(request):
    """The order-book module under test (lob_a, later lob_b)."""
    return importlib.import_module(request.param)
