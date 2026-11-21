"""Phase 3 diagnostic checks, separate from the unchanged pytest suite.

Run: python run.py lob.check_b
Checks B's internal invariants, compaction thresholds and counter/plain parity.
Own expected files are read only; A is the event-by-event oracle.
"""
import copy
import json
from pathlib import Path

from datagen.own_cases import C, L, M, CASE_NAMES
from lob import OrderBookA, OrderBookB
from lob.replay import read_events

ROOT = Path(__file__).resolve().parents[2]


def assert_internal(book):
    """Index bijection, live/stale counts, FIFO and the post-event stale bound."""
    found = {}
    for side, name in ((book.bids, "BUY"), (book.asks, "SELL")):
        assert side.prices == sorted(set(side.prices))
        assert set(side.prices) == {side.sign * p for p in side.levels}
        for price, level in side.levels.items():
            live = [order for order in level.queue if order.alive]
            dead = [order for order in level.queue if not order.alive]
            assert len(live) == level.live > 0
            assert len(dead) == level.stale
            assert level.stale <= max(level.live, 32)
            assert [r.arrival_seq for r in live] == sorted(r.arrival_seq for r in live)
            for record in live:
                assert record.side == name and record.price_ticks == price and record.qty_units > 0
                assert record.order_id not in found
                found[record.order_id] = record
    assert found == book.orders
    assert all(book.orders[key] is record for key, record in found.items())


def books():
    plain = OrderBookB()
    # This is also the first red diagnostic against the original B stub.
    assert plain.snapshot() == []
    counted = OrderBookB(count_operations=True)
    assert plain.counters is None
    assert counted.counters is not None
    return OrderBookA(), plain, counted


def send(engines, event):
    """Compare all results/books; show the exact event on the first divergence."""
    a, plain, counted = engines
    before = counted.counters.as_dict()
    results = []
    for engine in engines:
        sent = copy.deepcopy(event)
        results.append(engine.process(sent))
        assert sent == event, ("input mutated", event)
    assert results[0] == results[1] == results[2], ("result divergence", event, results)
    snapshots = [engine.snapshot() for engine in engines]
    assert snapshots[0] == snapshots[1] == snapshots[2], ("book divergence", event, snapshots)
    assert a.last_seq == plain.last_seq == counted.last_seq
    assert (a.best_bid(), a.best_ask()) == (plain.best_bid(), plain.best_ask()) == (
        counted.best_bid(), counted.best_ask()), event
    for engine in (plain, counted):
        assert_internal(engine)
    if results[0]["status"] == "rejected":
        assert counted.counters.as_dict() == before, ("rejection changed counters", event)
    return results[0]


def own_cases():
    for name in CASE_NAMES:
        engines = books()
        expected = json.loads((ROOT / "06_data/own" / f"{name}.expected.json").read_text(encoding="utf-8"))
        events = list(read_events(ROOT / "06_data/own" / f"{name}.jsonl"))
        assert len(events) == len(expected["results"])
        for event, want in zip(events, expected["results"]):
            assert send(engines, event) == want, (name, event, want)
        assert engines[1].snapshot() == expected["final_book"], name
    print("18 own cases: A == B plain == B counted after every event; original expectations match")


def cancel_compaction():
    for side in ("BUY", "SELL"):
        engines = books()
        for i in range(65):
            send(engines, L(i + 1, f"o{i}", side, 100, 2))
        for i in range(32):
            send(engines, C(66 + i, f"o{i}"))
        levels = engines[1].bids.levels if side == "BUY" else engines[1].asks.levels
        level = levels[100]
        assert (level.live, level.stale, len(level.queue)) == (33, 32, 65)
        assert engines[2].counters.compactions == 0
        send(engines, C(98, "o32"))
        assert (level.live, level.stale, len(level.queue)) == (32, 0, 32)
        counters = engines[2].counters
        assert (counters.compactions, counters.stale_compacted, counters.compaction_records_scanned) == (1, 33, 65)
        # Delete every survivor, then recreate the same level and reuse an id.
        for i in range(33, 65):
            send(engines, C(99 + i, f"o{i}"))
        assert not levels and engines[1].best_bid() is None and engines[1].best_ask() is None
        send(engines, L(200, "o0", side, 100, 3))
    print("Cancel compaction: both sides, strict >32 and >live thresholds, complete deletion and recreation")


def match_compaction():
    engines = books()
    for i in range(96):
        send(engines, L(i + 1, f"o{i}", "BUY", 100, 2))
    for j, i in enumerate(range(63, 96)):
        send(engines, C(97 + j, f"o{i}"))
    level = engines[1].bids.levels[100]
    assert (level.live, level.stale) == (63, 33)
    assert engines[2].counters.compactions == 0
    send(engines, M(130, "s", 62))
    assert (level.live, level.stale, len(level.queue)) == (32, 0, 32)
    c = engines[2].counters
    assert (c.compactions, c.stale_compacted, c.compaction_records_scanned) == (1, 33, 65)
    print("Matching compaction: fills can trigger the same stale/live threshold")


def hand_counted_counters():
    engines = books()
    for event in (L(1, "b1", "BUY", 100, 5), L(2, "b2", "BUY", 100, 5),
                  C(3, "b1"), M(4, "s", 3)):
        send(engines, event)
    c = engines[2].counters
    assert (c.accepted_events, c.limit_events, c.market_sell_events, c.cancel_events) == (4, 2, 1, 1)
    assert (c.levels_visited, c.makers_touched, c.fills, c.unfilled_qty_units) == (1, 1, 1, 10)
    assert (c.stale_skipped, c.stale_compacted, c.stale_discarded, c.compactions) == (1, 0, 0, 0)
    assert (c.active_order_peak, c.price_level_peak) == (2, 1)
    # Reusing a cancelled id must not revive an old tombstone.
    send(engines, L(5, "b1", "BUY", 100, 1))
    send(engines, M(6, "s2", 10))
    assert engines[1].snapshot() == []
    print("Hand-counted counters and cancelled-id reuse: exact; counters default off")


def main():
    own_cases()
    cancel_compaction()
    match_compaction()
    hand_counted_counters()
    print("RESULT: PASS (B internals, compaction, counters and event-by-event oracle parity)")


if __name__ == "__main__":
    main()
