"""Tests for the dashboard: data helpers on the saved results and a headless app run."""
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "dashboard"))
import loaders  # noqa: E402

pytestmark = pytest.mark.skipif(loaders.missing_files(), reason="no saved results")


@pytest.fixture(scope="module")
def results():
    return loaders.load_results()


def test_total_vs_sum_matches_check_total_csv(results):
    mine = loaders.total_vs_sum(results["time_summary"])
    saved = pd.read_csv(ROOT / "results" / "total_consistency.csv").sort_values(
        loaders.KEY).reset_index(drop=True)
    assert len(mine) == len(saved) == 72
    assert mine["ratio"].tolist() == pytest.approx(saved["ratio_total_over_sum"].tolist())
    assert mine["spread_total"].tolist() == pytest.approx(saved["spread_total"].tolist())
    assert mine["ranges_overlap"].tolist() == saved["ranges_overlap"].tolist()


def test_scaled_times_units_and_per_query(results):
    summary = results["time_summary"]
    batch = loaders.scaled_times(summary, "total", False, 1e6)
    query = loaders.scaled_times(summary, "total", True, 1e6)
    assert (batch["value"] == batch["median_seconds_per_batch"] * 1e6).all()
    assert (query["value"] * query["q"]).tolist() == pytest.approx(batch["value"].tolist())
    prepare = loaders.scaled_times(summary, "prepare", True, 1.0)
    assert (prepare["per"] == "per batch").all()      # preparation has no per-query value


def test_version_comparison_ratio(results):
    versions = loaders.version_comparison(results["time_summary"])
    assert len(versions) == 3 * 2 * 3 * 3             # n * q * hit rates * phases
    row = versions.iloc[0]
    assert row["v2_over_v1"] == pytest.approx(row["v2_iterative"] / row["v1_recursive"])


def test_memory_table_shape(results):
    table = loaders.memory_table(results["mem_summary"], 100, "mixed", "median_peak_bytes")
    assert list(table.columns) == ["method", "phase", "n = 1,000", "n = 10,000", "n = 100,000"]
    assert len(table) == 4 * 3


def test_missing_results_are_reported(tmp_path):
    assert set(loaders.missing_files(tmp_path)) == set(loaders.REQUIRED)
    with pytest.raises(FileNotFoundError):
        loaders.load_results(tmp_path)


def test_dashboard_does_not_import_the_algorithms_or_benchmarks():
    import ast
    imported = set()
    for name in ("app.py", "loaders.py"):
        tree = ast.parse((ROOT / "dashboard" / name).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                imported.add((node.module or "").split(".")[0])
    assert not imported & {"membership", "datagen", "bench_time", "bench_memory", "check_total"}


def test_app_runs_without_errors_for_every_setting():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=90).run()
    assert not app.exception
    assert [t.label for t in app.tabs] == ["Time vs n", "Total vs prepare + query", "v1 vs v2",
                                           "Memory", "Raw repeats", "Environment"]
    for q in app.sidebar.radio[0].options:
        for hit in ("mixed", "all-present", "all-absent"):
            app.sidebar.radio[0].set_value(int(q) if q.isdigit() else q)
            app.sidebar.selectbox[0].set_value(hit)
            app.run()
            assert not app.exception, (q, hit)


def test_app_shows_message_when_results_are_missing(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(loaders, "RESULTS_DIR", tmp_path)
    app = AppTest.from_file(str(ROOT / "dashboard" / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert any("Saved results not found" in e.value for e in app.error)
