"""Shared order book API and explicit implementation selection.

BaselineOrderBook and RevisedOrderBook are separate implementation scaffolds.
Their matching handlers remain pending. ComparedOrderBook checks both versions
after each event, including rejected events and calls to public handlers.
"""

from copy import deepcopy


IMPLEMENTATIONS = ("baseline", "revised", "compare")


class OrderBook:
    """Common interface for a sequential BTC order book."""

    def process_event(self, event: dict) -> dict:
        """Route an event to its public handler, which validates its fields."""
        if not isinstance(event, dict):
            reason = "event must be a dictionary"
        else:
            event_type = event.get("type")
            if event_type == "LIMIT":
                return self.AddLimitOrder(event)
            if event_type == "MARKET_SELL":
                return self.FillMarketSell(event)
            if event_type == "CANCEL":
                return self.CancelOrder(event)
            reason = "type must be LIMIT, MARKET_SELL or CANCEL"

        result = {"status": "rejected", "reason": reason}
        if isinstance(event, dict) and "event_id" in event:
            result["event_id"] = deepcopy(event["event_id"])
        return result

    def AddLimitOrder(self, event: dict) -> dict:
        """Match a limit order and rest any remaining quantity."""
        raise NotImplementedError("Implement limit order matching.")

    def FillMarketSell(self, event: dict) -> dict:
        """Match a market sell against bids in price-time order."""
        raise NotImplementedError("Implement market sell matching.")

    def CancelOrder(self, event: dict) -> dict:
        """Cancel the target's remaining quantity, or return not_found."""
        raise NotImplementedError("Implement order cancellation.")

    def inspect_book(self) -> dict:
        """Return {"bids": [...], "asks": [...]} in canonical price-time order."""
        raise NotImplementedError("Implement book inspection.")


class BaselineOrderBook(OrderBook):
    """Version A: baseline matching implementation still to be written."""


class RevisedOrderBook(OrderBook):
    """Version B: revised matching implementation still to be written."""


def _same_value(left, right):
    """Compare nested values without treating 1, 1.0 and True as identical."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _same_value(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_value(a, b) for a, b in zip(left, right)
        )
    return left == right


def _comparable_result(result):
    if not isinstance(result, dict):
        raise AssertionError("An event handler must return a dictionary.")
    if result.get("status") == "rejected":
        reason = result.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise AssertionError("A rejected result needs a nonempty reason.")
        # Each version may explain the same rejection in its own words.
        return {key: value for key, value in result.items() if key != "reason"}
    return result


def _book_snapshot(book):
    snapshot = book.inspect_book()
    if not isinstance(snapshot, dict) or not all(
        isinstance(snapshot.get(side), list) for side in ("bids", "asks")
    ):
        raise AssertionError("inspect_book() must return bids and asks lists.")
    return deepcopy(snapshot)


class ComparedOrderBook(OrderBook):
    """Run separate Baseline and Revised books and detect their first difference."""

    def __init__(self, baseline=None, revised=None):
        self.baseline = BaselineOrderBook() if baseline is None else baseline
        self.revised = RevisedOrderBook() if revised is None else revised
        if self.baseline is self.revised:
            raise ValueError("Comparison requires two separate book instances.")

    def _call(self, method_name, event):
        left = deepcopy(getattr(self.baseline, method_name)(deepcopy(event)))
        right = deepcopy(getattr(self.revised, method_name)(deepcopy(event)))
        event_id = event.get("event_id") if isinstance(event, dict) else None

        # Check state immediately, even when this event was rejected.
        try:
            self.inspect_book()
        except AssertionError as error:
            raise AssertionError(
                f"{method_name}, event_id={event_id!r}: {error}"
            ) from error

        if not _same_value(_comparable_result(left), _comparable_result(right)):
            raise AssertionError(
                f"{method_name}, event_id={event_id!r}: result mismatch; "
                f"Baseline={left!r}; Revised={right!r}"
            )
        return deepcopy(left)

    def process_event(self, event: dict) -> dict:
        return self._call("process_event", event)

    def AddLimitOrder(self, event: dict) -> dict:
        return self._call("AddLimitOrder", event)

    def FillMarketSell(self, event: dict) -> dict:
        return self._call("FillMarketSell", event)

    def CancelOrder(self, event: dict) -> dict:
        return self._call("CancelOrder", event)

    def inspect_book(self) -> dict:
        left = _book_snapshot(self.baseline)
        right = _book_snapshot(self.revised)
        if not _same_value(left, right):
            raise AssertionError(
                f"book state mismatch; Baseline={left!r}; Revised={right!r}"
            )
        return left


def create_order_book(implementation="baseline"):
    """Select baseline, revised or compare; never silently fall back."""
    if implementation == "baseline":
        return BaselineOrderBook()
    if implementation == "revised":
        return RevisedOrderBook()
    if implementation == "compare":
        return ComparedOrderBook()
    raise ValueError(
        f"Unknown implementation {implementation!r}; choose from {IMPLEMENTATIONS}."
    )
