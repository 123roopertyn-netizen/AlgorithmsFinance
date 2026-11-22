"""Version B: revised data organization (Phase 3).

Planned data organization: per side a dict price -> FIFO queue of orders, a sorted list of
occupied prices (bisect), and an index order_id -> location for O(1) cancel.
Final design and its justification go into REVISIONS.md. Interface: SPEC.md section 6.
"""
from __future__ import annotations


class OrderBookB:
    """Revised limit order book. Stub until Phase 3."""

    name = "B"

    def __init__(self) -> None:
        self.last_seq = 0

    def process(self, event: dict) -> dict:
        raise NotImplementedError("OrderBookB.process: Phase 3")

    def AddLimitOrder(self, event: dict) -> dict:  # noqa: N802 (name from the spec)
        raise NotImplementedError("OrderBookB.AddLimitOrder: Phase 3")

    def FillMarketSell(self, event: dict) -> dict:  # noqa: N802
        raise NotImplementedError("OrderBookB.FillMarketSell: Phase 3")

    def CancelOrder(self, event: dict) -> dict:  # noqa: N802
        raise NotImplementedError("OrderBookB.CancelOrder: Phase 3")

    def snapshot(self) -> list[dict]:
        raise NotImplementedError("OrderBookB.snapshot: Phase 3")

    def best_bid(self) -> int | None:
        raise NotImplementedError("OrderBookB.best_bid: Phase 3")

    def best_ask(self) -> int | None:
        raise NotImplementedError("OrderBookB.best_ask: Phase 3")
