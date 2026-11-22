"""Replay interfaces reserved for implementation after the RED checkpoint."""

from pathlib import Path
from typing import Any


def replay_file(path: str | Path, engine: Any) -> list[dict[str, Any]]:
    """Replay JSONL or gzipped JSONL once Stage 4 implementation is authorized."""

    raise NotImplementedError("Replay processing is intentionally absent in RED")


def main(argv: list[str] | None = None) -> int:
    raise NotImplementedError("Replay command-line processing is intentionally absent in RED")


if __name__ == "__main__":
    raise SystemExit(main())

