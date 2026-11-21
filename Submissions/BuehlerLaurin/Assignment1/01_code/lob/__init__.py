"""Registry: METHODS = {(name, version): class}. Each call of a class gives a fresh empty book.

Phase 3: A is the list/scan baseline; B uses indexed levels and compacted deques.
Public API (SPEC.md, Q1): AddLimitOrder, CancelOrder, FillMarketSell, process,
snapshot, best_bid, best_ask.
"""
from lob.book_a import OrderBookA
from lob.book_b import OrderBookB

METHODS = {("lob", "A"): OrderBookA, ("lob", "B"): OrderBookB}
