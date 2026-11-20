"""Reproducible runtime measurements for all search implementations."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from search_algorithms import (
    binary_search,
    binary_search_recursive_v1,
    hash_set_membership,
    linear_search,
)
from synthetic_data import generate_search_case


SearchMethod = Callable[[Sequence[int], Sequence[int]], list[bool]]

ALGORITHMS: tuple[tuple[str, SearchMethod], ...] = (
    ("Linear search", linear_search),
    ("Binary search recursive v1", binary_search_recursive_v1),
    ("Binary search iterative v2", binary_search),
    ("Hash set membership", hash_set_membership),
)


@dataclass(frozen=True)
class BenchmarkResult:
    algorithm: str
    array_size: int
    query_count: int
    repeats: int
    median_ms: float
    minimum_ms: float
    maximum_ms: float


def _query_count_for(array_size: int) -> int:
    """Scale query work while keeping the largest linear case practical."""

    return min(500, max(10, array_size // 10))


def benchmark_case(
    array_size: int,
    query_count: int,
    *,
    repeats: int,
    seed: int,
    hit_rate: float,
) -> list[BenchmarkResult]:
    """Measure every algorithm on exactly the same generated input."""

    if repeats < 1:
        raise ValueError("repeats must be at least 1")

    ids, queries = generate_search_case(
        array_size,
        query_count,
        seed=seed,
        hit_rate=hit_rate,
    )
    original_ids = ids.copy()
    lookup = set(ids)
    expected = [query in lookup for query in queries]
    measurements: list[BenchmarkResult] = []

    for algorithm_name, search in ALGORITHMS:
        # Correctness is checked outside the timed region. One warm-up call
        # reduces one-off interpreter effects without hiding setup costs such
        # as sorting or set construction inside each algorithm call.
        if search(ids, queries) != expected:
            raise AssertionError(f"{algorithm_name} returned incorrect results")
        if ids != original_ids:
            raise AssertionError(f"{algorithm_name} changed the input IDs")

        durations_ms: list[float] = []
        for _ in range(repeats):
            started = perf_counter_ns()
            result = search(ids, queries)
            elapsed_ns = perf_counter_ns() - started
            if result != expected:
                raise AssertionError(
                    f"{algorithm_name} changed behavior during measurement"
                )
            durations_ms.append(elapsed_ns / 1_000_000)

        if ids != original_ids:
            raise AssertionError(f"{algorithm_name} changed the input IDs")

        measurements.append(
            BenchmarkResult(
                algorithm=algorithm_name,
                array_size=array_size,
                query_count=query_count,
                repeats=repeats,
                median_ms=round(median(durations_ms), 6),
                minimum_ms=round(min(durations_ms), 6),
                maximum_ms=round(max(durations_ms), 6),
            )
        )

    return measurements


def run_benchmarks(
    sizes: Sequence[int],
    *,
    repeats: int = 7,
    seed: int = 2026,
    hit_rate: float = 0.5,
) -> list[BenchmarkResult]:
    """Measure all sizes, varying the seed while preserving reproducibility."""

    results: list[BenchmarkResult] = []
    for index, array_size in enumerate(sizes):
        if array_size < 0:
            raise ValueError("benchmark sizes must be non-negative")
        results.extend(
            benchmark_case(
                array_size,
                _query_count_for(array_size),
                repeats=repeats,
                seed=seed + index,
                hit_rate=hit_rate,
            )
        )
    return results


def write_results(
    results: Sequence[BenchmarkResult],
    output_directory: Path,
    *,
    seed: int,
    hit_rate: float,
) -> tuple[Path, Path]:
    """Write the same measurements to machine-readable JSON and CSV."""

    output_directory.mkdir(parents=True, exist_ok=True)
    json_path = output_directory / "benchmark_results.json"
    csv_path = output_directory / "benchmark_results.csv"
    rows = [asdict(result) for result in results]

    payload = {
        "metadata": {
            "seed": seed,
            "hit_rate": hit_rate,
            "clock": "time.perf_counter_ns",
            "summary_statistic": "median",
            "data_generation_timed": False,
            "algorithm_setup_timed": True,
        },
        "results": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    fieldnames = list(BenchmarkResult.__dataclass_fields__)
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    return json_path, csv_path


def _parse_sizes(raw_sizes: str) -> list[int]:
    sizes = [int(value.strip()) for value in raw_sizes.split(",") if value.strip()]
    if not sizes:
        raise argparse.ArgumentTypeError("at least one size is required")
    if any(size < 0 for size in sizes):
        raise argparse.ArgumentTypeError("sizes must be non-negative")
    return sizes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        type=_parse_sizes,
        default=_parse_sizes("0,10,100,1000,5000,10000"),
        help="comma-separated array sizes",
    )
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--hit-rate", type=float, default=0.5)
    parser.add_argument("--output", type=Path, default=Path("results"))
    arguments = parser.parse_args()

    results = run_benchmarks(
        arguments.sizes,
        repeats=arguments.repeats,
        seed=arguments.seed,
        hit_rate=arguments.hit_rate,
    )
    json_path, csv_path = write_results(
        results,
        arguments.output,
        seed=arguments.seed,
        hit_rate=arguments.hit_rate,
    )
    print(f"Wrote {json_path} and {csv_path}")


if __name__ == "__main__":
    main()
