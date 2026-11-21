"""Replay JSON Lines (plain or gzip) in file order from a fresh book.

Usage: python run.py lob.replay <file.jsonl[.gz]> --version A|B
No sorting: seq order is validated by the engine, and rejections stay in place.
"""
import argparse
import gzip
import json
from pathlib import Path

from lob import METHODS


def read_events(path):
    """Stream parsed events without retaining the input file or result history."""
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--version", choices=("A", "B"), default="A")
    args = parser.parse_args()
    book = METHODS[("lob", args.version)]()
    for event in read_events(args.path):
        print(json.dumps(book.process(event)))


if __name__ == "__main__":
    main()
