"""Event validation entry point; implementation follows the failing tests."""

from __future__ import annotations

from .interface import Event


def validate_event(event: Event, last_accepted_seq: int) -> None:
    """Raise a validation error for an invalid event without mutating state."""

    raise NotImplementedError("event validation is not implemented")

