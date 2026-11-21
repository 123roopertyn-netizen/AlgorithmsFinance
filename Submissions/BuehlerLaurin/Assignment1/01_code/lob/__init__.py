"""Registry: METHODS = {(name, version): class}. Each call of a class gives a fresh empty book.

Phase 2: A is the transparent list/scan baseline; B stays a Phase 3 stub.
Public API (SPEC.md, Q1): AddLimitOrder, CancelOrder, FillMarketSell, process,
snapshot, best_bid, best_ask.
"""
from lob.book_a import OrderBookA
from lob.book_b import OrderBookB

METHODS = {("lob", "A"): OrderBookA, ("lob", "B"): OrderBookB}
