"""Version A: transparent baseline (unsorted list per side + scan, SPEC.md Q15).

STUB for the Phase 1 red run: no engine code yet. Every public method raises
NotImplementedError until Phase 2.
"""


class OrderBookA:
    """Version A order book. Public API as in SPEC.md (Interface)."""

    def process(self, event):
        """Validate `event`, route it by its type and return the result dict."""
        raise NotImplementedError("Version A: Phase 2")

    def AddLimitOrder(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version A: Phase 2")

    def CancelOrder(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version A: Phase 2")

    def FillMarketSell(self, event):  # noqa: N802 - name required by the assignment
        raise NotImplementedError("Version A: Phase 2")

    def snapshot(self):
        """Active orders in canonical order (bids price desc, asks price asc, then arrival)."""
        raise NotImplementedError("Version A: Phase 2")

    def best_bid(self):
        raise NotImplementedError("Version A: Phase 2")

    def best_ask(self):
        raise NotImplementedError("Version A: Phase 2")
