"""Invalid events are rejected atomically and do not consume sequence rank."""

from copy import deepcopy

import pytest

from limit_order_book.interface import OrderBook

from helpers import cancel_event, limit_event, market_sell_event, resting


@pytest.mark.parametrize(
    "invalid_event",
    [
        {"seq": 2, "event_id": "bad-type", "type": "UNKNOWN"},
        limit_event(2, "bad-side", "HOLD", 99, 1, event_id="bad-side-event"),
        limit_event(2, "bad-price-zero", "BUY", 0, 1),
        limit_event(2, "bad-price-negative", "BUY", -1, 1),
        limit_event(2, "bad-price-float", "BUY", 99.5, 1),
        limit_event(2, "bad-qty-zero", "BUY", 99, 0),
        limit_event(2, "bad-qty-negative", "BUY", 99, -1),
        limit_event(2, "bad-qty-float", "BUY", 99, 1.5),
        limit_event(2, "bad-qty-bool", "BUY", 99, True),
        market_sell_event(2, "bad-market-zero", 0),
        {"seq": 2, "event_id": "missing-quantity", "type": "MARKET_SELL", "order_id": "s"},
        {"seq": 2, "event_id": "missing-target", "type": "CANCEL"},
        {"seq": 2, "event_id": "missing-side", "type": "LIMIT", "order_id": "x", "price_ticks": 99, "qty_units": 1},
    ],
    ids=[
        "unknown-type",
        "unknown-side",
        "zero-price",
        "negative-price",
        "noninteger-price",
        "zero-quantity",
        "negative-quantity",
        "noninteger-quantity",
        "boolean-is-not-integer",
        "zero-market-quantity",
        "missing-quantity",
        "missing-cancel-target",
        "missing-limit-side",
    ],
)
def test_invalid_event_is_rejected_without_state_change(
    book: OrderBook, invalid_event: dict[str, object]
) -> None:
    book.process_event(limit_event(1, "b1", "BUY", 100, 5))
    before = deepcopy(book.inspect_book())

    result = book.process_event(invalid_event)

    assert result["event_id"] == invalid_event["event_id"]
    assert result["status"] == "rejected"
    assert isinstance(result["reason"], str) and result["reason"]
    assert book.inspect_book() == before


def test_sequence_must_be_positive_integer(book: OrderBook) -> None:
    result = book.process_event(limit_event(0, "b0", "BUY", 100, 1))

    assert result["status"] == "rejected"
    assert book.inspect_book() == []


@pytest.mark.parametrize("invalid_seq", [1.5, True], ids=["float", "boolean"])
def test_sequence_must_not_accept_nonintegers(
    book: OrderBook, invalid_seq: object
) -> None:
    event = limit_event(1, "b1", "BUY", 100, 1)
    event["seq"] = invalid_seq

    result = book.process_event(event)

    assert result["status"] == "rejected"
    assert book.inspect_book() == []


def test_rejected_event_does_not_advance_last_accepted_sequence(book: OrderBook) -> None:
    book.process_event(limit_event(1, "b1", "BUY", 100, 1))
    rejected = book.process_event(
        limit_event(3, "invalid", "HOLD", 99, 1, event_id="invalid-event")
    )
    accepted = book.process_event(limit_event(2, "b2", "BUY", 99, 1))

    assert rejected["status"] == "rejected"
    assert accepted["status"] == "resting"
    assert [order["order_id"] for order in book.inspect_book()] == ["b1", "b2"]


def test_duplicate_live_order_identifier_is_rejected(book: OrderBook) -> None:
    book.process_event(limit_event(1, "same", "BUY", 100, 2))
    before = book.inspect_book()

    result = book.process_event(market_sell_event(2, "same", 1))

    assert result["status"] == "rejected"
    assert book.inspect_book() == before


def test_unknown_cancellation_is_valid_and_advances_sequence(book: OrderBook) -> None:
    missing = book.process_event(cancel_event(1, "unknown"))
    later = book.process_event(limit_event(2, "b2", "BUY", 100, 1))

    assert missing == {
        "event_id": "event1",
        "target_order_id": "unknown",
        "status": "not_found",
        "cancelled_qty_units": 0,
    }
    assert later["status"] == "resting"
    assert book.inspect_book() == [resting("b2", "BUY", 100, 1, 2)]

