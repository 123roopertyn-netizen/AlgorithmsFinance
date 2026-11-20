"""The dashboard must agree with the raw results it displays."""

import statistics

import pytest
from data import (
    fmt_bytes, fmt_seconds, headline, load_memory, load_metadata, load_timing,
    memory_summary, noise_bound, revision_ratios, timing_summary,
)


@pytest.fixture(scope="module")
def timing():
    return load_timing()


@pytest.fixture(scope="module")
def memory():
    return load_memory()


def test_saved_results_are_complete(timing, memory):
    assert len(timing) == 15 * 6 * 5
    assert len(memory) == 15 * 6 * 3
    assert load_metadata("timing")["code"]["uncommitted_changes_in_src_or_bench"] is False
    assert load_metadata("memory")["code"]["uncommitted_changes_in_src_or_bench"] is False


def test_timing_summary_matches_raw_medians(timing):
    summary = timing_summary(timing)
    for _, row in summary.sample(20, random_state=0).iterrows():
        raw = timing[(timing["scenario"] == row["scenario"]) & (timing["version"] == row["version"])
                     & (timing["method"] == row["method"])]
        for col in ("prepare_s", "query_batch_s", "total_s"):
            assert row[f"{col}_median"] == pytest.approx(statistics.median(raw[col]))
            assert row[f"{col}_min"] == raw[col].min()
            assert row[f"{col}_max"] == raw[col].max()


def test_memory_summary_matches_raw(memory):
    summary = memory_summary(memory)
    row = summary[(summary["n"] == 100_000) & (summary["method"] == "hash")].iloc[0]
    raw = memory[(memory["scenario"] == row["scenario"]) & (memory["method"] == "hash")
                 & (memory["version"] == row["version"])]
    assert row["prepare_current_B"] == statistics.median(raw["prepare_current_B"])


def test_revision_ratio_is_v2_over_v1(timing):
    summary = timing_summary(timing)
    ratios = revision_ratios(summary)
    r = ratios[(ratios["scenario"] == 0) & (ratios["method"] == "binary")].iloc[0]
    s = summary[(summary["scenario"] == 0) & (summary["method"] == "binary")].set_index("version")
    assert r["query_batch_s_ratio"] == pytest.approx(
        s.loc["v2", "query_batch_s_median"] / s.loc["v1", "query_batch_s_median"])


def test_headline_matches_readme_claims(timing, memory):
    summary = timing_summary(timing)
    ratios = revision_ratios(summary)
    h = headline(summary, memory_summary(memory), ratios)
    assert 0.08 < h["speedup_min"] <= h["speedup_max"] < 0.16
    assert h["noise"] == pytest.approx(noise_bound(ratios)) and h["noise"] < 0.07
    assert h["fastest_q1"][0] == "linear"
    assert h["fastest_q100"][0] == "hash"
    assert 4.5 < h["hash_vs_sorted"] < 5.5


@pytest.mark.parametrize("value,text", [(2.5e-3, "2.5 ms"), (46e-9, "46 ns"), (1.2, "1.2 s")])
def test_fmt_seconds(value, text):
    assert fmt_seconds(value) == text


@pytest.mark.parametrize("value,text", [(920, "920 B"), (800_056, "781 KiB"), (4_194_520, "4 MiB")])
def test_fmt_bytes(value, text):
    assert fmt_bytes(value) == text
