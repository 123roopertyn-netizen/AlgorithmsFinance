"""Revised order book; deliberately unimplemented test-first checkpoint."""

from __future__ import annotations

from .interface import BookSnapshot, Event, EventResult


class RevisedOrderBook:
    """Version B will use a measured and justified data-organization revision."""

    def process_event(self, event: Event) -> EventResult:
        raise NotImplementedError("revised dispatcher is not implemented")

    def add_limit_order(self, event: Event) -> EventResult:
        raise NotImplementedError("revised limit matching is not implemented")

    def cancel_order(self, event: Event) -> EventResult:
        raise NotImplementedError("revised cancellation is not implemented")

    def fill_market_sell(self, event: Event) -> EventResult:
        raise NotImplementedError("revised market sell is not implemented")

    def inspect_book(self) -> BookSnapshot:
        raise NotImplementedError("revised inspection is not implemented")

