import pytest

from benchmarks.metrics import (
    ceil_percent,
    percentile_nearest_rank,
    replay_fresh,
    stopped_phase_row,
    summarize_seconds,
)
from benchmarks.run_benchmarks import (
    _config_id,
    _make_queue_events,
    _receive_worker_message,
)
from orderbook.baseline import OrderBook as BaselineBook
from orderbook.revised import OrderBook as RevisedBook


@pytest.mark.parametrize(
    ("quantity", "percent", "expected"),
    [(1, 10, 1), (101, 10, 11), (101, 100, 101), (101, 200, 202)],
)
def test_ceil_percent_uses_integer_ceiling(quantity, percent, expected):
    assert ceil_percent(quantity, percent) == expected


def test_timing_summary_uses_median_and_nearest_rank_percentiles():
    values = list(range(1, 21))

    assert percentile_nearest_rank(values, 95) == 19
    assert percentile_nearest_rank(values, 99) == 20
    assert summarize_seconds([1.0, 3.0, 2.0], 10) == {
        "median_seconds": 2.0,
        "throughput_events_per_second": 5.0,
    }


@pytest.mark.parametrize("book_type", [BaselineBook, RevisedBook])
def test_replay_fresh_returns_independent_engine_state(book_type):
    first = replay_fresh(
        book_type,
        [
            {
                "seq": 1,
                "event_id": "add",
                "type": "LIMIT",
                "order_id": "bid",
                "side": "BUY",
                "price_ticks": 6000000,
                "qty_units": 10,
            },
            {
                "seq": 2,
                "event_id": "partial",
                "type": "MARKET_SELL",
                "order_id": "sell",
                "qty_units": 5,
            },
        ],
    )
    second = replay_fresh(
        book_type,
        [
            {
                "seq": 1,
                "event_id": "add",
                "type": "LIMIT",
                "order_id": "bid",
                "side": "BUY",
                "price_ticks": 6000000,
                "qty_units": 10,
            }
        ],
    )

    first.process_event(
        {
            "seq": 3,
            "event_id": "cancel",
            "type": "CANCEL",
            "target_order_id": "bid",
        }
    )
    assert first.inspect_book() == {"bids": [], "asks": []}
    assert second.inspect_book() == {
        "bids": [
            {
                "order_id": "bid",
                "side": "BUY",
                "price_ticks": 6000000,
                "qty_units": 10,
                "seq": 1,
            }
        ],
        "asks": [],
    }


def test_queue_concentration_changes_realized_prices_not_order_quantities():
    concentrated = _make_queue_events(1000, 4, 42)
    spread = _make_queue_events(1000, 1000, 42)

    assert len(concentrated) == len(spread) == 1000
    assert [event["qty_units"] for event in concentrated] == [
        event["qty_units"] for event in spread
    ]
    assert len({event["price_ticks"] for event in concentrated}) == 4
    assert len({event["price_ticks"] for event in spread}) == 1000


def test_stopped_run_record_does_not_report_zero_elapsed_time():
    row = stopped_phase_row("stopped_timeout", 12.5, 2048)

    assert row["phase"] == "worker_stop"
    assert row["status"] == "stopped_timeout"
    assert row["elapsed_seconds"] is None
    assert row["duration_until_stop_seconds"] == 12.5
    assert row["peak_working_set_bytes_observed"] == 2048


def test_closed_worker_pipe_is_reported_as_ipc_error():
    class ClosedPipe:
        def poll(self, timeout=0):
            return True

        def recv(self):
            raise OSError("pipe closed")

    message = _receive_worker_message(ClosedPipe())

    assert message["kind"] == "ipc_error"
    assert "pipe closed" in message["error"]


def test_queue_attempt_ids_are_shortened_for_windows_paths():
    case = {"case_id": "queue_concentration_prices1000_M10000"}

    assert _config_id(case, "baseline") == "queue_prices1000_M10000__baseline"
