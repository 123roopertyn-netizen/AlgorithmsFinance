# Lab 1 search methods

Run from the repository root with Python 3.10 or newer:

```powershell
.\.venv\Scripts\python.exe -m pip install -r Submissions\VoronkovMaksim\requirements.txt
.\.venv\Scripts\python.exe -m pytest Submissions\VoronkovMaksim\tests -q
```

The four functions in `search.py` are `linear_search_v1`, `binary_search_v1`, `binary_search_v2`, and `hash_search_v1`. Each accepts lists of integer IDs and queries and returns one Boolean per query. Invalid values raise `TypeError`; the original IDs and queries stay unchanged. Binary methods sort a copy. The V2 revision replaces recursive calls with a `while` loop to avoid recursion overhead and reduce auxiliary space used by each search.

## Manual example

For `ids = [7, 11, 7]` and `queries = [11, 9, 7]`, every method returns `[True, False, True]`.

- Linear search checks `7`, then `11` for query `11` and stops. For `9`, it checks all three IDs and finds no match. For `7`, it matches the first ID.
- Binary search first sorts a **copy** to `[7, 7, 11]`. For `11`, it compares the middle `7`, then the rightmost `11`. For `9`, it compares `7`, then `11`, and finds no match. For `7`, the middle value matches immediately.

The earlier test-first run failed to import the absent `search.py` module. The algorithm and generator tests passed after implementation.

## Fixed inputs for the later comparison

Run `.\.venv\Scripts\python.exe Submissions\VoronkovMaksim\save_datasets.py` from the repository root to create or verify 18 JSON files in `data/`. The files cover `n = 1,000, 10,000, 100,000`, `q = 1, 100`, and present, absent, and mixed queries. They record the original unsorted IDs, query order, requested and actual hit rates, seed `42`, and `allow_duplicates = true`. All methods must later load the same file; sorting and set construction happen in the methods, not in the saved inputs.

The generator rounds `q × hit_rate` to the nearest whole hit, with half rounded up. Thus **mixed with one query contains one present query**: requested hit rate `0.5`, actual hit rate `1.0`. For 100 queries, mixed contains exactly 50 hits. The script validates every file against the generator and refuses to overwrite an existing file that differs from these fixed inputs.

## Runtime measurement

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe Submissions\VoronkovMaksim\benchmark.py
```

The script loads all 18 saved JSON files and writes `results/timings.csv`. It checks that all four methods agree and leave the inputs unchanged before timing. It warms each method, then makes five measurements with fresh preparation state. Preparation is sorting a copy for binary search, set construction for hash search, and zero for linear search. Query timing runs the same search loops as the public functions, without repeating input validation. For short operations, several query batches are timed together and divided by their count. Inputs, validation, and printing are outside the timed regions.

The CSV has five `raw` rows and one `median` row per method and dataset (432 rows total). Time columns are in **seconds**. Each median time column is calculated independently; median total can differ slightly from median preparation plus median query. The CSV also records the batch count, seed, Python and machine details, and the Git HEAD at measurement time. Results depend on the machine and current load.

## Static performance charts

From the repository root, generate all charts from the saved CSV with:

```powershell
.\.venv\Scripts\python.exe Submissions\VoronkovMaksim\dashboard.py
```

The script reads `results/timings.csv` and writes **18 PNG files** to `results/charts/`: total, preparation, and query-batch time for each query count and hit-rate scenario. It also writes `results/summary.csv` with 72 median rows in milliseconds. The original raw measurements remain in `results/timings.csv`. Charts use a logarithmic array-size axis so all three sizes are visible. No benchmarks are rerun. There are no saved memory measurements to summarize.
