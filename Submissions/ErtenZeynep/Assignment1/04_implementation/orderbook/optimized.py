"""Optimized order-book interface; behavior is absent in RED."""

from typing import Any


class OptimizedOrderBook:
    """Minimal importable optimized stub for test-first development."""

    def __init__(self) -> None:
        self._last_accepted_seq: int | None = None

    @property
    def last_accepted_seq(self) -> int | None:
        return self._last_accepted_seq

    def canonical_snapshot(self) -> list[dict[str, Any]]:
        return []

    def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Optimized event processing is intentionally absent in RED")

    def AddLimitOrder(self, event: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Optimized AddLimitOrder is intentionally absent in RED")

    def CancelOrder(self, event: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Optimized CancelOrder is intentionally absent in RED")

    def FillMarketSell(self, event: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("Optimized FillMarketSell is intentionally absent in RED")

