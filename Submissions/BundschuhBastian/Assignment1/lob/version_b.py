"""Version B: revised data organization (Phase 3).

Per side:
  - `levels`: dict  price -> OrderedDict(order_id -> [qty, arrival_seq])
    The OrderedDict keeps FIFO order inside a price. Deleting any order is O(1), and a
    partial fill changes the qty in place, so the order keeps its place in the queue.
  - `keys`: sorted list of occupied prices (bisect). Asks are stored negated (-price), so
    on BOTH sides the best price is the LAST element: best price O(1), remove best O(1).
    A new or emptied price level costs O(P) (list insert / delete in the middle).
One index for both sides: order_id -> (is_bid, price). It answers "is this id live?" and
finds a cancel target in O(1). Empty price levels are removed at once, so there are no
stale entries.

Interface: SPEC.md section 6. Final design and the A -> B changes: REVISIONS.md.
"""
from __future__ import annotations

from bisect import bisect_left, insort
from collections import OrderedDict

from lob.common import (BUY, CANCEL, LIMIT, SELL, is_valid_fast, rejected_result,
                        validate)

QTY, SEQ = 0, 1     # positions inside an order record [qty, arrival_seq]


class _Side:
    """One side of the book (all bids or all asks)."""

    __slots__ = ("is_bid", "levels", "keys")

    def __init__(self, is_bid: bool) -> None:
        self.is_bid = is_bid
        self.levels: dict[int, OrderedDict] = {}
        self.keys: list[int] = []      # sorted ascending; best price is keys[-1]

    def key(self, price: int) -> int:
        return price if self.is_bid else -price

    def price_of(self, key: int) -> int:
        return key if self.is_bid else -key

    def best_price(self) -> int | None:
        return self.price_of(self.keys[-1]) if self.keys else None

    def add(self, order_id: str, price: int, qty: int, seq: int) -> None:
        level = self.levels.get(price)
        if level is None:
            level = self.levels[price] = OrderedDict()
            insort(self.keys, self.key(price))
        level[order_id] = [qty, seq]

    def remove(self, order_id: str, price: int) -> list:
        """Remove one order; drop its price level if it becomes empty. Returns the record."""
        level = self.levels[price]
        rec = level.pop(order_id)
        if not level:
            self.drop_level(price)
        return rec

    def drop_level(self, price: int) -> None:
        del self.levels[price]
        k = self.key(price)
        if self.keys[-1] == k:
            self.keys.pop()
        else:
            del self.keys[bisect_left(self.keys, k)]


class OrderBookB:
    """Revised limit order book (price levels + FIFO queues + order index)."""

    name = "B"

    def __init__(self) -> None:
        self.last_seq = 0
        self._bids = _Side(True)
        self._asks = _Side(False)
        self._index: dict[str, tuple[bool, int]] = {}    # order_id -> (is_bid, price)

    # --- entry point -------------------------------------------------------------
    def process(self, event: dict) -> dict:
        if not is_valid_fast(event, self.last_seq, self._index):
            reason = validate(event, self.last_seq, self._index.__contains__)
            if reason is not None:
                return rejected_result(event, reason)  # last_seq stays unchanged
        self.last_seq = event["seq"]
        if event["type"] == LIMIT:
            return self.AddLimitOrder(event)
        if event["type"] == CANCEL:
            return self.CancelOrder(event)
        return self.FillMarketSell(event)

    # --- the three operations (assume a validated event) -------------------------
    def AddLimitOrder(self, event: dict) -> dict:  # noqa: N802 (name from the spec)
        is_buy = event["side"] == BUY
        order_id = event["order_id"]
        price = event["price_ticks"]
        remaining = event["qty_units"]
        opposite, own = (self._asks, self._bids) if is_buy else (self._bids, self._asks)
        fills: list[dict] = []
        keys = opposite.keys
        # Only call the matching loop if the order can cross the best opposite price.
        if keys and (price >= -keys[-1] if is_buy else price <= keys[-1]):
            fills, remaining = self._take(opposite, order_id, remaining, price)
        if remaining > 0:
            levels = own.levels                     # inlined _Side.add (hot path)
            level = levels.get(price)
            if level is None:
                level = levels[price] = OrderedDict()
                insort(own.keys, price if is_buy else -price)
            level[order_id] = [remaining, event["seq"]]
            self._index[order_id] = (is_buy, price)
        return {"event_id": event["event_id"], "order_id": order_id,
                "status": "resting" if remaining > 0 else "filled",
                "unfilled_qty_units": remaining, "fills": fills}

    def FillMarketSell(self, event: dict) -> dict:  # noqa: N802
        fills, remaining = self._take(self._bids, event["order_id"], event["qty_units"], None)
        status = "filled" if remaining == 0 else ("partial" if fills else "unfilled")
        return {"event_id": event["event_id"], "order_id": event["order_id"],
                "status": status, "unfilled_qty_units": remaining, "fills": fills}

    def CancelOrder(self, event: dict) -> dict:  # noqa: N802
        target = event["target_order_id"]
        where = self._index.pop(target, None)
        if where is None:
            return {"event_id": event["event_id"], "target_order_id": target,
                    "status": "not_found", "cancelled_qty_units": 0, "fills": []}
        is_bid, price = where
        rec = (self._bids if is_bid else self._asks).remove(target, price)
        return {"event_id": event["event_id"], "target_order_id": target,
                "status": "cancelled", "cancelled_qty_units": rec[QTY], "fills": []}

    # --- inspection ----------------------------------------------------------------
    def snapshot(self) -> list[dict]:
        out: list[dict] = []
        for side, name in ((self._bids, BUY), (self._asks, SELL)):
            for key in reversed(side.keys):        # best price first = canonical order
                price = side.price_of(key)
                for oid, rec in side.levels[price].items():     # FIFO = arrival order
                    out.append({"order_id": oid, "side": name, "price_ticks": price,
                                "qty_units": rec[QTY], "arrival_seq": rec[SEQ]})
        return out

    def best_bid(self) -> int | None:
        return self._bids.best_price()

    def best_ask(self) -> int | None:
        return self._asks.best_price()

    # --- matching ------------------------------------------------------------------
    def _take(self, side: _Side, taker_id: str, qty: int,
              limit_price: int | None) -> tuple[list[dict], int]:
        """Trade against `side` from the best price until qty is used up, the side is
        empty, or the best price no longer crosses `limit_price` (None = no limit).
        Returns (fills, remaining quantity)."""
        fills: list[dict] = []
        is_bid = side.is_bid
        index = self._index
        while qty > 0 and side.keys:
            price = side.price_of(side.keys[-1])
            if limit_price is not None and (
                    price < limit_price if is_bid else price > limit_price):
                break
            level = side.levels[price]
            while qty > 0 and level:
                maker_id, rec = next(iter(level.items()))     # oldest order at this price
                traded = qty if qty < rec[QTY] else rec[QTY]
                fills.append({"maker_id": maker_id, "taker_id": taker_id,
                              "price_ticks": price, "qty_units": traded})
                qty -= traded
                if traded == rec[QTY]:
                    del level[maker_id]
                    del index[maker_id]
                else:
                    rec[QTY] -= traded
            if not level:
                side.drop_level(price)
        return fills, qty
