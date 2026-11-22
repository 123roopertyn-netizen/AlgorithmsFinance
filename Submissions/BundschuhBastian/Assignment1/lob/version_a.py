"""Version A: transparent baseline (Phase 2).

Planned data organization: one Python list of order records per side; best price and
cancel targets are found by scanning the list. Interface: SPEC.md section 6.
"""
from __future__ import annotations


class OrderBookA:
    """Baseline limit order book. Stub until Phase 2."""

    name = "A"

    def __init__(self) -> None:
        self.last_seq = 0

    def process(self, event: dict) -> dict:
        raise NotImplementedError("OrderBookA.process: Phase 2")

    def AddLimitOrder(self, event: dict) -> dict:  # noqa: N802 (name from the spec)
        raise NotImplementedError("OrderBookA.AddLimitOrder: Phase 2")

    def FillMarketSell(self, event: dict) -> dict:  # noqa: N802
        raise NotImplementedError("OrderBookA.FillMarketSell: Phase 2")

    def CancelOrder(self, event: dict) -> dict:  # noqa: N802
        raise NotImplementedError("OrderBookA.CancelOrder: Phase 2")

    def snapshot(self) -> list[dict]:
        raise NotImplementedError("OrderBookA.snapshot: Phase 2")

    def best_bid(self) -> int | None:
        raise NotImplementedError("OrderBookA.best_bid: Phase 2")

    def best_ask(self) -> int | None:
        raise NotImplementedError("OrderBookA.best_ask: Phase 2")
