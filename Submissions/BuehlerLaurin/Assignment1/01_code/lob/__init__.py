"""Registry: METHODS = {(name, version): class}. Each call of a class gives a fresh empty book.

Phase 1 (red run): both versions are NotImplementedError stubs, so every contract
check fails for the right reason instead of collecting nothing.
Public API (SPEC.md, Q1): AddLimitOrder, CancelOrder, FillMarketSell, process,
snapshot, best_bid, best_ask.
"""
from lob.book_a import OrderBookA
from lob.book_b import OrderBookB

METHODS = {("lob", "A"): OrderBookA, ("lob", "B"): OrderBookB}
