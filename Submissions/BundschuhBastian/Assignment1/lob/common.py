"""Shared, non-matching code for both order book versions.

Contains: units, reason codes (SPEC.md D9), event reading, canonical snapshot order (D15),
USD display (D17), and the validation entry point (stub until Phase 2).
No matching logic lives here; each version implements matching on its own.
"""
from __future__ import annotations

import gzip
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Callable, Iterator

# --- units (SPEC.md section 2) -------------------------------------------------------
TICK_USD = Decimal("0.01")          # one price tick in USD per BTC
UNITS_PER_BTC = 100_000_000         # qty_units per BTC
VALUE_UNITS_PER_USD = 10**10        # price_ticks * qty_units per USD

# --- event vocabulary ------------------------------------------------------------------
LIMIT, MARKET_SELL, CANCEL = "LIMIT", "MARKET_SELL", "CANCEL"
EVENT_TYPES = (LIMIT, MARKET_SELL, CANCEL)
BUY, SELL = "BUY", "SELL"

# --- reason codes, in check order (SPEC.md D9) --------------------------------------
MALFORMED_EVENT = "malformed_event"
INVALID_SEQ = "invalid_seq"
NONINCREASING_SEQ = "nonincreasing_seq"
INVALID_EVENT_ID = "invalid_event_id"
UNKNOWN_TYPE = "unknown_type"
INVALID_ORDER_ID = "invalid_order_id"
UNKNOWN_SIDE = "unknown_side"
INVALID_PRICE = "invalid_price"
INVALID_QTY = "invalid_qty"
INVALID_TARGET_ORDER_ID = "invalid_target_order_id"
DUPLICATE_LIVE_ORDER_ID = "duplicate_live_order_id"

# Marker key the reader puts on a line that is not a JSON object (-> malformed_event).
PARSE_ERROR_KEY = "_parse_error"


def read_events(path: str | Path) -> Iterator[dict]:
    """Yield one dict per line of a JSON Lines file (gzip if the name ends in .gz).

    A line that is not a JSON object yields {PARSE_ERROR_KEY: <line number>} so the
    engine can reject it (D9, reason malformed_event) instead of crashing.
    Blank lines are skipped.
    """
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                obj = None
            yield obj if isinstance(obj, dict) else {PARSE_ERROR_KEY: line_no}


def load_events(path: str | Path) -> list[dict]:
    """Read a whole file into a list (used to separate parsing from replay timing)."""
    return list(read_events(path))


def snapshot_sort_key(order: dict) -> tuple:
    """Canonical order (D15): bids first by price desc, then asks by price asc; FIFO."""
    if order["side"] == BUY:
        return (0, -order["price_ticks"], order["arrival_seq"])
    return (1, order["price_ticks"], order["arrival_seq"])


def gross_value(fills: list[dict]) -> int:
    """Sum of price_ticks * qty_units over fills (integer tick-units, I7)."""
    return sum(f["price_ticks"] * f["qty_units"] for f in fills)


def proceeds_usd(value_units: int) -> str:
    """Display only (D17): tick-units -> USD string with 2 decimals, round half up."""
    usd = Decimal(value_units) / Decimal(VALUE_UNITS_PER_USD)
    return str(usd.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def validate(event: dict, last_seq: int, is_live: Callable[[str], bool]) -> str | None:
    """Return None if the event is valid, else the first failing reason code (D1-D9).

    `is_live(order_id)` must answer whether that order is currently active in the book.
    Implemented in Phase 2 (tests first).
    """
    raise NotImplementedError("validate: Phase 2")
