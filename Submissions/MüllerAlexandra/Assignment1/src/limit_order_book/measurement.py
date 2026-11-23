"""Deterministic measurement arithmetic and fresh-state replay helpers."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import ceil
from statistics import median
from time import perf_counter
from typing import TypeVar

from .interface import Event, OrderBook


Number = TypeVar("Number", int, float)
Clock = Callable[[], float]
BookFactory = Callable[[], OrderBook]
ThroughputRecord = dict[str, int | float]


def nearest_rank_percentile(
    samples: Sequence[Number], percentile: float
) -> Number:
    """Return a percentile using the documented one-based nearest-rank rule."""

    if not samples:
        raise ValueError("percentile requires at least one sample")
    if isinstance(percentile, bool) or not 0 < percentile <= 100:
        raise ValueError("percentile must be greater than 0 and at most 100")
    ordered = sorted(samples)
    rank = ceil(percentile / 100 * len(ordered))
    return ordered[rank - 1]


def latency_summary_ns(samples: Sequence[int]) -> dict[str, int | float]:
    """Summarize raw processing-latency samples expressed in nanoseconds."""

    if not samples:
        raise ValueError("latency summary requires at least one sample")
    invalid = any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in samples
    )
    if invalid:
        raise ValueError("latency samples must be nonnegative integers")
    return {
        "sample_count": len(samples),
        "median_ns": median(samples),
        "p95_ns": nearest_rank_percentile(samples, 95),
        "p99_ns": nearest_rank_percentile(samples, 99),
    }


def throughput_events_per_second(event_count: int, elapsed_seconds: float) -> float:
    """Calculate processed events per replay second."""

    if isinstance(event_count, bool) or not isinstance(event_count, int) or event_count <= 0:
        raise ValueError("event_count must be a positive integer")
    if isinstance(elapsed_seconds, bool) or elapsed_seconds <= 0:
        raise ValueError("elapsed_seconds must be positive")
    return event_count / elapsed_seconds


def measure_throughput_repeats(
    book_factory: BookFactory,
    events: Sequence[Event],
    *,
    warmups: int = 1,
    repeats: int = 5,
    clock: Clock = perf_counter,
) -> list[ThroughputRecord]:
    """Replay preloaded events with a fresh book for every warm-up and repeat."""

    if isinstance(warmups, bool) or not isinstance(warmups, int) or warmups < 0:
        raise ValueError("warmups must be a nonnegative integer")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats <= 0:
        raise ValueError("repeats must be a positive integer")
    if not events:
        raise ValueError("events must not be empty")

    for _ in range(warmups):
        book = book_factory()
        for event in events:
            book.process_event(event)

    records: list[ThroughputRecord] = []
    event_count = len(events)
    for repeat in range(1, repeats + 1):
        construction_started = clock()
        book = book_factory()
        construction_seconds = clock() - construction_started

        replay_started = clock()
        for event in events:
            book.process_event(event)
        replay_seconds = clock() - replay_started

        if construction_seconds < 0:
            raise ValueError("clock produced negative construction time")
        throughput = throughput_events_per_second(event_count, replay_seconds)
        records.append(
            {
                "repeat": repeat,
                "event_count": event_count,
                "construction_seconds": construction_seconds,
                "replay_seconds": replay_seconds,
                "total_engine_seconds": construction_seconds + replay_seconds,
                "throughput_events_per_second": throughput,
            }
        )
    return records
