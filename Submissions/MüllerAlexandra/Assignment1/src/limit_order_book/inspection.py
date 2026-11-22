"""Canonical snapshot helpers; implementation follows the failing tests."""

from __future__ import annotations

from collections.abc import Iterable

from .interface import BookSnapshot
from .models import RestingOrder


def canonical_snapshot(orders: Iterable[RestingOrder]) -> BookSnapshot:
    """Return bids then asks in the assignment's canonical order."""

    raise NotImplementedError("canonical inspection is not implemented")

