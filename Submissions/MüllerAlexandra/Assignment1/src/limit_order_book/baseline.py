"""Transparent baseline order book; deliberately unimplemented checkpoint."""

from __future__ import annotations

from .interface import BookSnapshot, Event, EventResult


class BaselineOrderBook:
    """Version A will prioritize transparent, directly inspectable logic."""

    def process_event(self, event: Event) -> EventResult:
        raise NotImplementedError("baseline dispatcher is not implemented")

    def add_limit_order(self, event: Event) -> EventResult:
        raise NotImplementedError("baseline limit matching is not implemented")

    def cancel_order(self, event: Event) -> EventResult:
        raise NotImplementedError("baseline cancellation is not implemented")

    def fill_market_sell(self, event: Event) -> EventResult:
        raise NotImplementedError("baseline market sell is not implemented")

    def inspect_book(self) -> BookSnapshot:
        raise NotImplementedError("baseline inspection is not implemented")

