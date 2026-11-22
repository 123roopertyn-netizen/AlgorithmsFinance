"""State-independent event validation interface for the RED checkpoint."""

from typing import Any


def validate_event(event: Any) -> dict[str, Any] | None:
    """Return a rejection dictionary or ``None`` once implemented in Stage 4."""

    raise NotImplementedError("Stateless event validation is intentionally absent in RED")

