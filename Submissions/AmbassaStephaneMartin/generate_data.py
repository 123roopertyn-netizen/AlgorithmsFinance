import json
import random
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
BASE_SEED = 2026


def save_case(name, ids, queries, expected, **metadata):
    """Save one dataset and its expected Boolean answers."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    case = {
        "name": name,
        "ids": ids,
        "queries": queries,
        "expected": expected,
        "metadata": {
            "n_ids": len(ids),
            "n_queries": len(queries),
            **metadata,
        },
    }

    path = DATA_DIR / f"{name}.json"
    path.write_text(
        json.dumps(case, indent=2) + "\n",
        encoding="utf-8",
    )


def generate_random_case(n_ids, n_queries, hit_rate, seed):
    """Generate data with a controlled proportion of successful queries."""
    rng = random.Random(seed)

    # Stored IDs are even integers. Duplicates are allowed.
    ids = [
        2 * rng.randint(-n_ids, n_ids)
        for _ in range(n_ids)
    ]

    n_hits = round(n_queries * hit_rate)

    # Successful queries are sampled from the actual array.
    labelled_queries = [
        (rng.choice(ids), True)
        for _ in range(n_hits)
    ]

    # Odd integers cannot occur in our even-integer array.
    labelled_queries += [
        (2 * rng.randint(-n_ids, n_ids) + 1, False)
        for _ in range(n_queries - n_hits)
    ]

    # Shuffle each query together with its correct answer.
    rng.shuffle(labelled_queries)

    queries = [query for query, _ in labelled_queries]
    expected = [answer for _, answer in labelled_queries]

    return ids, queries, expected


def main():
    small_cases = [
        ("both_empty", [], [], []),
        (
            "empty_ids",
            [],
            [1, -1, 1],
            [False, False, False],
        ),
        ("empty_queries", [3, 1, 3], [], []),
        (
            "single_id",
            [7],
            [7, 6, 7],
            [True, False, True],
        ),
        (
            "duplicates_and_negatives",
            [4, -2, 4, 0],
            [-2, 3, 4, -2, 0],
            [True, False, True, True, True],
        ),
        (
            "large_integers",
            [-(10**30), 10**30],
            [10**30, 0, -(10**30)],
            [True, False, True],
        ),
    ]

    for name, ids, queries, expected in small_cases:
        save_case(
            name, ids, queries, expected,
            category="correctness",
        )

    for n_ids in (100, 1_000, 10_000):
        # Reusing this seed keeps the ID array identical across hit rates.
        seed = BASE_SEED + n_ids

        for hit_rate in (0.0, 0.5, 1.0):
            ids, queries, expected = generate_random_case(
                n_ids=n_ids,
                n_queries=1_000,
                hit_rate=hit_rate,
                seed=seed,
            )

            name = f"n{n_ids}_q1000_hit{int(hit_rate * 100)}"

            save_case(
                name, ids, queries, expected,
                category="benchmark",
                seed=seed,
                target_hit_rate=hit_rate,
            )

    print(f"Saved 15 datasets to {DATA_DIR}")


if __name__ == "__main__":
    main()