"""Hand-calculated tests from 01_my_notes/OrderBookTests.xlsx, tabs Test1, Test2.

Inputs: the event rows 2-7 (columns A-G) of each tab.
Expected values: ONLY the block "EXPECTED RESULT (hand calculation)" from
row 24 down. The formula columns J-O above it are NOT used: they ignore
crossing on arrival.

The Excel works in BTC and dollars; here: 1 BTC = 100_000_000 qty_units,
$1 = 100 price_ticks, proceeds in dollars = sum(p * q) / 10**10.
"""

from fractions import Fraction

BTC = 100_000_000
USD = 100
TICK_UNITS_PER_USD = 10**10


# --- helpers -----------------------------------------------------------------

def limit(seq, order_id, side, usd, btc):
    return {"seq": seq, "event_id": f"event{seq}", "type": "LIMIT",
            "order_id": order_id, "side": side,
            "price_ticks": usd * USD, "qty_units": btc * BTC}


def market_sell(seq, order_id, btc):
    return {"seq": seq, "event_id": f"event{seq}", "type": "MARKET_SELL",
            "order_id": order_id, "qty_units": btc * BTC}


def replay(lob, events):
    book = lob.OrderBook()
    results = [book.process_event(e) for e in events]
    return results, book


def status_rows(results):
    """(event_id, order_id, status, unfilled BTC) per event, as in the Excel."""
    return [(r["event_id"], r["order_id"], r["status"],
             Fraction(r["unfilled_qty_units"], BTC)) for r in results]


def fill_rows(results):
    """(event_id, maker, taker, price USD, qty BTC) in execution order."""
    return [(r["event_id"], f["maker_id"], f["taker_id"],
             Fraction(f["price_ticks"], USD), Fraction(f["qty_units"], BTC))
            for r in results for f in r["fills"]]


def book_rows(book):
    """(order_id, side, price USD, qty BTC, seq) in canonical book order."""
    return [(o["order_id"], o["side"], Fraction(o["price_ticks"], USD),
             Fraction(o["qty_units"], BTC), o["arrival_seq"])
            for o in book.inspect_book()]


def gross(fills):
    return sum(f["price_ticks"] * f["qty_units"] for f in fills)


def check_submission_conservation(events, results):
    """Each submission: incoming qty = its fills (as taker) + returned residual."""
    for e, r in zip(events, results):
        assert e["qty_units"] == sum(f["qty_units"] for f in r["fills"]) \
            + r["unfilled_qty_units"], e["event_id"]


def bid_side_traded(events, results):
    """Quantity traded by BUY limit orders, whether as maker or as taker."""
    buy_ids = {e["order_id"] for e in events
               if e["type"] == "LIMIT" and e["side"] == "BUY"}
    return sum(f["qty_units"] for r in results for f in r["fills"]
               if f["maker_id"] in buy_ids or f["taker_id"] in buy_ids)


# --- Excel tab Test1 ---------------------------------------------------------

def test_Test1(lob):
    """Excel tab Test1: b1 BUY 60,200 crosses a1 SELL 60,100 on arrival,
    then market sell s1 8 BTC is filled."""
    # Input: tab Test1, rows 2-7, columns A-G.
    events = [
        limit(1, "b1", "BUY", 60_200, 1),
        limit(2, "b2", "BUY", 60_000, 1),
        limit(3, "b3", "BUY", 59_900, 3),
        limit(4, "b4", "BUY", 59_700, 5),
        limit(5, "a1", "SELL", 60_100, 2),
        market_sell(6, "s1", 8),
    ]
    results, book = replay(lob, events)

    # Tab Test1, rows 27-33 "Event results".
    assert status_rows(results) == [
        ("event1", "b1", "resting", 1),
        ("event2", "b2", "resting", 1),
        ("event3", "b3", "resting", 3),
        ("event4", "b4", "resting", 5),
        ("event5", "a1", "resting", 1),   # crosses b1 on arrival, 1 BTC rests
        ("event6", "s1", "filled", 0),
    ]

    # Tab Test1, rows 36-40 "Fills (in execution order)".
    assert fill_rows(results) == [
        ("event5", "b1", "a1", 60_200, 1),
        ("event6", "b2", "s1", 60_000, 1),
        ("event6", "b3", "s1", 59_900, 3),
        ("event6", "b4", "s1", 59_700, 4),
    ]

    # Tab Test1, rows 43-45 "Book after all events".
    assert book_rows(book) == [
        ("b4", "BUY", 59_700, 1, 4),
        ("a1", "SELL", 60_100, 1, 5),
    ]

    # Tab Test1, rows 48-52 "Totals".
    all_fills = [f for r in results for f in r["fills"]]
    s1_fills = results[5]["fills"]
    assert len(all_fills) == 4                                        # B48
    assert sum(f["qty_units"] for f in all_fills) == 9 * BTC          # B49
    assert gross(s1_fills) == 478_500 * TICK_UNITS_PER_USD            # B50
    # B51 average 59,812.50 USD = 5,981,250 ticks, exact in integers.
    s1_sold = sum(f["qty_units"] for f in s1_fills)
    assert gross(s1_fills) == 5_981_250 * s1_sold
    assert gross(all_fills) == 538_700 * TICK_UNITS_PER_USD           # B52

    # Row 53: bids 10 BTC submitted = 9 traded + 1 resting.
    submitted_bids = sum(e["qty_units"] for e in events[:4])
    resting_bids = sum(o["qty_units"] for o in book.inspect_book()
                       if o["side"] == "BUY")
    assert submitted_bids == 10 * BTC
    assert bid_side_traded(events, results) == 9 * BTC
    assert submitted_bids == bid_side_traded(events, results) + resting_bids

    # Per submission: a1 2 = 1 filled + 1 resting; s1 8 = 8 sold + 0 discarded.
    check_submission_conservation(events, results)
    assert all(o["order_id"] != "s1" for o in book.inspect_book())


# --- Excel tab Test2 ---------------------------------------------------------

def test_Test2(lob):
    """Excel tab Test2: market sell s1 15 BTC is larger than the 10 BTC bid
    book: partial, 5 BTC discarded."""
    # Input: tab Test2, rows 2-7, columns A-G.
    events = [
        limit(1, "b1", "BUY", 60_000, 1),
        limit(2, "b2", "BUY", 60_000, 1),
        limit(3, "b3", "BUY", 59_900, 3),
        limit(4, "b4", "BUY", 59_700, 5),
        limit(5, "a1", "SELL", 60_100, 2),
        market_sell(6, "s1", 15),
    ]
    results, book = replay(lob, events)

    # Tab Test2, rows 27-33 "Event results".
    assert status_rows(results) == [
        ("event1", "b1", "resting", 1),
        ("event2", "b2", "resting", 1),
        ("event3", "b3", "resting", 3),
        ("event4", "b4", "resting", 5),
        ("event5", "a1", "resting", 2),   # no bid at or above 60,100
        ("event6", "s1", "partial", 5),   # only 10 BTC of bids, 5 discarded
    ]

    # Tab Test2, rows 36-40 "Fills (in execution order)".
    assert fill_rows(results) == [
        ("event6", "b1", "s1", 60_000, 1),
        ("event6", "b2", "s1", 60_000, 1),
        ("event6", "b3", "s1", 59_900, 3),
        ("event6", "b4", "s1", 59_700, 5),
    ]

    # Tab Test2, rows 43-44 "Book after all events": the bid side is empty.
    assert book_rows(book) == [
        ("a1", "SELL", 60_100, 2, 5),
    ]

    # Tab Test2, rows 48-54 "Totals".
    all_fills = [f for r in results for f in r["fills"]]
    s1_fills = results[5]["fills"]
    assert len(all_fills) == 4                                        # B48
    assert sum(f["qty_units"] for f in all_fills) == 10 * BTC         # B49
    assert gross(s1_fills) == 598_200 * TICK_UNITS_PER_USD            # B50
    s1_sold = sum(f["qty_units"] for f in s1_fills)
    assert gross(s1_fills) == 59_820 * USD * s1_sold                  # B51
    assert gross(all_fills) == 598_200 * TICK_UNITS_PER_USD           # B52

    # Row 53: bids 10 BTC submitted = 10 traded + 0 resting.
    submitted_bids = sum(e["qty_units"] for e in events[:4])
    resting_bids = sum(o["qty_units"] for o in book.inspect_book()
                       if o["side"] == "BUY")
    assert submitted_bids == 10 * BTC
    assert resting_bids == 0
    assert submitted_bids == bid_side_traded(events, results) + resting_bids

    # Row 54: s1 15 = 10 sold + 5 discarded; the residual never rests.
    assert results[5]["unfilled_qty_units"] == 5 * BTC
    check_submission_conservation(events, results)
    assert all(o["order_id"] != "s1" for o in book.inspect_book())
