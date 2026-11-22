"""JSON Lines and gzip replay helpers; implementation follows the tests."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

from .interface import Event, EventResult, OrderBook


def iter_events(path: Path) -> Iterator[dict[str, object]]:
    """Yield JSON events from a plain or gzip-compressed JSON Lines file."""

    raise NotImplementedError("event stream reading is not implemented")


def replay_events(book: OrderBook, events: Iterable[Event]) -> list[EventResult]:
    """Process events in iteration order and return one result per event."""

    raise NotImplementedError("event replay is not implemented")

