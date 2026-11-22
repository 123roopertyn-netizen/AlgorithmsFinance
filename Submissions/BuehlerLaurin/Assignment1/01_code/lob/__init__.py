"""Registry: METHODS = {(name, version): class}. Each call of a class gives a fresh empty book.

Phase 3b: A baseline plus B (= B1), B2 and B3 for the Phase 4 comparison.
Public API (SPEC.md, Q1): AddLimitOrder, CancelOrder, FillMarketSell, process,
snapshot, best_bid, best_ask.
"""
from lob.book_a import OrderBookA
from lob.book_b import OrderBookB
from lob.book_b2 import OrderBookB2
from lob.book_b3 import OrderBookB3

METHODS = {("lob", "A"): OrderBookA, ("lob", "B"): OrderBookB,
           ("lob", "B2"): OrderBookB2, ("lob", "B3"): OrderBookB3}
