"""Version B: fast version (data organisation chosen in Phase 3 from the candidates in SPEC.md).

STUB for the Phase 1 red run: no engine code yet. Every public method raises
NotImplementedError until Phase 3.
"""


class OrderBookB:
    """Version B order book. Same public API as Version A (SPEC.md, Q1)."""

    def process(self, event):
        """Validate `event`, route it by its type and return the result dict."""
        raise NotImplementedError("Version B: Phase 3")

    def AddLimitOrder(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version B: Phase 3")

    def CancelOrder(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version B: Phase 3")

    def FillMarketSell(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version B: Phase 3")

    def snapshot(self):
        """Active orders in canonical order (bids price desc, asks price asc, then arrival)."""
        raise NotImplementedError("Version B: Phase 3")

    def best_bid(self):
        raise NotImplementedError("Version B: Phase 3")

    def best_ask(self):
        raise NotImplementedError("Version B: Phase 3")
