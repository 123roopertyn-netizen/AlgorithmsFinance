import gzip
import json
import math
import statistics
from pathlib import Path


def load_events(path):
    """Parse JSONL, transparently supporting the supplied gzip inputs."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate_event_stream(events, expected_count=None):
    if expected_count is not None and len(events) != expected_count:
        raise ValueError(
            f"expected {expected_count} events, found {len(events)}"
        )
    previous_seq = 0
    for position, event in enumerate(events, start=1):
        seq = event.get("seq")
        if type(seq) is not int or seq <= previous_seq:
            raise ValueError(f"nonincreasing or invalid seq at position {position}")
        previous_seq = seq
    return len(events)


def ceil_percent(quantity, percent):
    if type(quantity) is not int or quantity < 0:
        raise ValueError("quantity must be a nonnegative integer")
    if type(percent) is not int or percent <= 0:
        raise ValueError("percent must be a positive integer")
    if quantity == 0:
        return 0
    return max(1, (quantity * percent + 99) // 100)


def percentile_nearest_rank(values, percentile):
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered) / 100))
    return ordered[rank - 1]


def summarize_seconds(values, event_count):
    if not values:
        raise ValueError("timing summary requires at least one repeat")
    median_seconds = statistics.median(values)
    return {
        "median_seconds": median_seconds,
        "throughput_events_per_second": (
            event_count / median_seconds if median_seconds > 0 else None
        ),
    }


def phase_row(phase, repeat=None, status="completed", elapsed_seconds=None):
    return {
        "phase": phase,
        "repeat": repeat,
        "status": status,
        "elapsed_seconds": elapsed_seconds,
        "traced_current_bytes": None,
        "traced_peak_bytes": None,
        "active_order_peak": None,
        "occupied_price_level_peak": None,
        "fill_count": None,
    }


def stopped_phase_row(status, duration_seconds, peak_working_set_bytes=None):
    row = phase_row("worker_stop", status=status)
    row["duration_until_stop_seconds"] = duration_seconds
    row["peak_working_set_bytes_observed"] = peak_working_set_bytes
    return row


def replay_without_history(book, events):
    """Replay events without keeping per-event output objects."""
    for event in events:
        book.process_event(event)


def replay_fresh(book_type, events):
    """Create an isolated book and replay events; used by correctness checks."""
    book = book_type()
    replay_without_history(book, events)
    return book


def book_state_counts(book):
    """Return logical and container-entry counts for diagnostic passes only."""
    if hasattr(book, "_orders_by_id"):
        active_orders = len(book._orders_by_id)
        bid_queues = book._bids_by_price
        ask_queues = book._asks_by_price
        bid_heap = book._bid_heap
        ask_heap = book._ask_heap
        bid_members = book._bid_heap_members
        ask_members = book._ask_heap_members
        price_levels = len(bid_queues) + len(ask_queues)
        queue_entries = sum(len(queue) for queue in bid_queues.values())
        queue_entries += sum(len(queue) for queue in ask_queues.values())
        heap_entries = len(bid_heap) + len(ask_heap)
        heap_members = len(bid_members) + len(ask_members)
        id_entries = active_orders
        order_entries = queue_entries + id_entries
        physical_storage_entries = (
            order_entries + price_levels + heap_entries + heap_members
        )
        return {
            "active_orders": active_orders,
            "occupied_price_levels": price_levels,
            "physical_order_entries": order_entries,
            "physical_queue_entries": queue_entries,
            "physical_id_entries": id_entries,
            "physical_price_level_entries": price_levels,
            "physical_heap_entries": heap_entries,
            "physical_heap_members": heap_members,
            "physical_storage_entries": physical_storage_entries,
        }

    orders = book._orders
    active_orders = len(orders)
    active_levels = {(order["side"], order["price_ticks"]) for order in orders}
    return {
        "active_orders": active_orders,
        "occupied_price_levels": len(active_levels),
        "physical_order_entries": active_orders,
        "physical_queue_entries": 0,
        "physical_id_entries": 0,
        "physical_price_level_entries": 0,
        "physical_heap_entries": 0,
        "physical_heap_members": 0,
        "physical_storage_entries": active_orders,
    }


def _price_visits(before_book, event, result):
    if result.get("status") == "rejected" or event["type"] == "CANCEL":
        return 0

    fills = result.get("fills", [])
    visited = {fill["price_ticks"] for fill in fills}
    if event["type"] != "LIMIT" or result.get("unfilled_qty_units", 0) <= 0:
        return len(visited)

    opposite_side = "asks" if event["side"] == "BUY" else "bids"
    opposite_orders = before_book[opposite_side]
    has_terminal_non_crossing_level = any(
        (
            order["price_ticks"] > event["price_ticks"]
            if event["side"] == "BUY"
            else order["price_ticks"] < event["price_ticks"]
        )
        for order in opposite_orders
    )
    if has_terminal_non_crossing_level:
        non_crossing_prices = [
            order["price_ticks"]
            for order in opposite_orders
            if (
                order["price_ticks"] > event["price_ticks"]
                if event["side"] == "BUY"
                else order["price_ticks"] < event["price_ticks"]
            )
        ]
        if non_crossing_prices:
            visited.add(non_crossing_prices[0])
    return len(visited)


def counter_replay(book_type, events):
    """Heavy diagnostic: inspect state and count fills separately from timing."""
    book = book_type()
    peaks = book_state_counts(book)
    fill_count = 0
    maker_touches = 0
    visited_price_levels = 0

    for event in events:
        before_book = book.inspect_book()
        result = book.process_event(event)
        counts = book_state_counts(book)
        for name in (
            "active_orders",
            "occupied_price_levels",
            "physical_storage_entries",
        ):
            peak_name = f"{name}_peak"
            peaks[peak_name] = max(peaks.get(peak_name, 0), counts[name])

        fills = result.get("fills", [])
        fill_count += len(fills)
        maker_touches += len(fills)
        visited_price_levels += _price_visits(before_book, event, result)

    final_counts = book_state_counts(book)
    return {
        "active_order_peak": peaks.get("active_orders_peak", 0),
        "occupied_price_level_peak": peaks.get(
            "occupied_price_levels_peak", 0
        ),
        "physical_storage_peak": peaks.get("physical_storage_entries_peak", 0),
        "fill_count": fill_count,
        "maker_touches": maker_touches,
        "visited_price_levels": visited_price_levels,
        "final_state": final_counts,
    }
