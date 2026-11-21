"""Shared input validation for Version A and Version B (SPEC.md, Validation; Q2-Q5, Q13, Q14).

One module for both versions, so they cannot diverge on bad input. Consequence: the
A/B differential test cannot catch validation bugs, so every rule has its own
contract check (02_tests/contract.py) and direct test (02_tests/test_validation.py).

Interface (fixed in SPEC.md):
    validate(event, last_seq, is_live) -> str | None
        reason code of the FIRST failing rule in the fixed check order, or None if valid.
        `last_seq`: seq of the last accepted event (0 before the first one).
        `is_live(order_id) -> bool`: True if the id is currently resting in the book.
    rejection(event, reason) -> dict
        {"event_id": <event_id if a non-empty str, else None>, "status": "rejected", "reason": reason}

STUB for the Phase 1 red run: the constants below are specification data; the
functions raise NotImplementedError until Phase 2.
"""

EVENT_TYPES = ("LIMIT", "MARKET_SELL", "CANCEL")
SIDES = ("BUY", "SELL")

# Required fields per type, in the order in which a missing one is reported
# (`event_id` first for every type; `seq` and `type` are checked earlier).
REQUIRED_FIELDS = {
    "LIMIT": ("event_id", "order_id", "side", "price_ticks", "qty_units"),
    "MARKET_SELL": ("event_id", "order_id", "qty_units"),
    "CANCEL": ("event_id", "target_order_id"),
}

# Reason codes (SPEC.md, Q2). `missing_field:<name>` and `bad_id:<name>` carry the field name.
NOT_AN_OBJECT = "not_an_object"
BAD_SEQ = "bad_seq"
NONINCREASING_SEQ = "nonincreasing_seq"
UNKNOWN_TYPE = "unknown_type"
MISSING_FIELD = "missing_field:"
BAD_ID = "bad_id:"
UNKNOWN_SIDE = "unknown_side"
BAD_PRICE = "bad_price"
BAD_QTY = "bad_qty"
DUPLICATE_LIVE_ORDER_ID = "duplicate_live_order_id"


def validate(event, last_seq, is_live):
    raise NotImplementedError("shared validation: Phase 2")


def rejection(event, reason):
    raise NotImplementedError("shared validation: Phase 2")
