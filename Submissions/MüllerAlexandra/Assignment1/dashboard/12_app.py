"""Interactive dashboard over saved Assignment 1 measurements."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = Path(
    os.environ.get(
        "ASSIGNMENT1_DASHBOARD_DATA",
        PROJECT_ROOT / "results" / "summary" / "13_dashboard_data.json.gz",
    )
)


@st.cache_data
def load_data(path: Path) -> dict[str, object]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def frame(data: dict[str, object], key: str) -> pd.DataFrame:
    return pd.DataFrame(data[key])


def mib(series: pd.Series) -> pd.Series:
    return series / (1024 * 1024)


st.set_page_config(page_title="Limit order book measurements", layout="wide")
st.title("Limit order book: baseline versus indexed revision")
st.caption(
    "Saved synthetic measurements only. Timings exclude network and queuing delay; "
    "tracemalloc is Python allocation, not total process memory."
)

if not DATA_PATH.is_file():
    st.error(
        "Dashboard data is missing. Run: python scripts/11_build_dashboard_data.py"
    )
    st.stop()

data = load_data(DATA_PATH)
statuses = frame(data, "statuses")
throughput = frame(data, "throughput_summaries")
comparisons = frame(data, "throughput_comparisons")

completed = int((statuses["outcome"] == "completed").sum())
timeouts = int((statuses["outcome"] == "stopped_timeout").sum())
failures = int((statuses["outcome"] == "failed").sum())
metric_columns = st.columns(4)
metric_columns[0].metric("Recorded tasks", len(statuses))
metric_columns[1].metric("Completed", completed)
metric_columns[2].metric("Stopped at limit", timeouts)
metric_columns[3].metric("Failed", failures)

tab_throughput, tab_latency, tab_memory, tab_liquidation, tab_correctness, tab_raw = st.tabs(
    ["Throughput", "Latency", "Memory", "Liquidation", "Correctness", "Raw records"]
)

with tab_throughput:
    st.subheader("Replay throughput and scaling")
    groups = sorted(throughput["experiment_group"].unique())
    selected_group = st.selectbox("Experiment group", groups)
    grouped = throughput[throughput["experiment_group"] == selected_group]
    selected_scenario = st.selectbox(
        "Throughput scenario", sorted(grouped["scenario"].unique())
    )
    grouped = grouped[grouped["scenario"] == selected_scenario]
    selected_levels = st.selectbox(
        "Available price setting", sorted(grouped["levels"].unique())
    )
    selected = grouped[grouped["levels"] == selected_levels].copy()
    selected["throughput_events_per_second"] = selected[
        "median_throughput_events_per_second"
    ]
    chart = (
        selected.groupby(["version", "event_count"], as_index=False)[
            "throughput_events_per_second"
        ]
        .median()
        .sort_values("event_count")
    )
    st.line_chart(
        chart,
        x="event_count",
        y="throughput_events_per_second",
        color="version",
    )
    st.dataframe(
        selected[
            [
                "version",
                "scenario",
                "event_count",
                "seed",
                "levels",
                "median_construction_seconds",
                "median_replay_seconds",
                "throughput_events_per_second",
            ]
        ].sort_values(["scenario", "event_count", "seed", "version"]),
        width="stretch",
        hide_index=True,
    )
    st.subheader("Matched completed pairs")
    st.caption("Speedup is omitted whenever either version stopped or is missing.")
    comparison_view = comparisons[
        (comparisons["experiment_group"] == selected_group)
        & (comparisons["scenario"] == selected_scenario)
        & (comparisons["levels"] == selected_levels)
    ]
    st.dataframe(comparison_view, width="stretch", hide_index=True)
    st.subheader("Stopped and failed runs")
    st.dataframe(
        statuses[statuses["outcome"] != "completed"],
        width="stretch",
        hide_index=True,
    )

with tab_latency:
    st.subheader("Per-event processing latency")
    latency = frame(data, "latency_summaries")
    latency["median_us"] = latency["median_ns"] / 1_000
    latency["p95_us"] = latency["p95_ns"] / 1_000
    latency["p99_us"] = latency["p99_ns"] / 1_000
    scenario = st.selectbox("Latency scenario", sorted(latency["scenario"].unique()))
    latency_view = latency[latency["scenario"] == scenario]
    latency_count = st.selectbox(
        "Latency event count", sorted(latency_view["event_count"].unique())
    )
    latency_view = latency_view[latency_view["event_count"] == latency_count]
    latency_seed = st.selectbox("Latency seed", sorted(latency_view["seed"].unique()))
    latency_view = latency_view[latency_view["seed"] == latency_seed]
    st.bar_chart(latency_view, x="scope", y="median_us", color="version")
    st.dataframe(latency_view, width="stretch", hide_index=True)
    st.caption("Units are microseconds; percentiles use the saved nearest-rank convention.")

with tab_memory:
    st.subheader("Traced Python allocation")
    memory = frame(data, "memory_finals")
    memory["current_mib"] = mib(memory["current_bytes"])
    memory["peak_mib"] = mib(memory["peak_bytes"])
    st.dataframe(memory, width="stretch", hide_index=True)
    checkpoints = frame(data, "memory_checkpoints")
    checkpoints["current_mib"] = mib(checkpoints["current_bytes"])
    memory_scenario = st.selectbox(
        "Memory trajectory scenario", sorted(checkpoints["scenario"].unique())
    )
    trajectory = checkpoints[checkpoints["scenario"] == memory_scenario]
    memory_count = st.selectbox(
        "Memory event count", sorted(trajectory["event_count"].unique())
    )
    trajectory = trajectory[trajectory["event_count"] == memory_count]
    memory_seed = st.selectbox("Memory seed", sorted(trajectory["seed"].unique()))
    trajectory = trajectory[trajectory["seed"] == memory_seed]
    memory_mode = st.selectbox("Memory mode", sorted(trajectory["mode"].unique()))
    trajectory = trajectory[trajectory["mode"] == memory_mode]
    st.line_chart(trajectory, x="event_index", y="current_mib", color="version")
    st.caption(
        "State-only and retained-output modes are separate. Post-cancellation state "
        "must not be confused with retained result history."
    )

with tab_liquidation:
    st.subheader("Fresh-book 10%, 100%, and 200% market sells")
    liquidation = frame(data, "liquidation_summaries")
    liquidation_columns = st.columns(2)
    liquidation_columns[0].bar_chart(
        liquidation, x="sale_size", y="median_construction_seconds", color="version"
    )
    liquidation_columns[1].bar_chart(
        liquidation, x="sale_size", y="median_sale_seconds", color="version"
    )
    st.dataframe(liquidation, width="stretch", hide_index=True)
    st.subheader("Raw timing repeats")
    st.dataframe(
        frame(data, "liquidation_repeats"), width="stretch", hide_index=True
    )
    st.subheader("Sale memory and operation counts")
    st.dataframe(
        frame(data, "liquidation_memory"), width="stretch", hide_index=True
    )

with tab_correctness:
    st.subheader("Diagnostic replay outcomes")
    diagnostics = frame(data, "diagnostics")
    st.dataframe(diagnostics, width="stretch", hide_index=True)
    invariant_columns = [
        "final_unique_order_ids",
        "final_positive_quantities",
        "final_uncrossed",
    ]
    all_invariants = bool(diagnostics[invariant_columns].all(axis=None))
    no_rejections = bool((diagnostics["rejected_events"] == 0).all())
    st.success(
        f"All final invariants: {all_invariants}; all diagnostic streams accepted: {no_rejections}."
    )

with tab_raw:
    st.subheader("Task statuses and settings")
    st.dataframe(statuses, width="stretch", hide_index=True)
    st.subheader("Raw throughput repeats")
    st.dataframe(
        frame(data, "throughput_repeats"), width="stretch", hide_index=True
    )
    st.subheader("Stress settings")
    st.dataframe(frame(data, "stress_settings"), width="stretch", hide_index=True)

st.divider()
st.subheader("Measured bottleneck")
st.markdown(
    """
Version A rebuilds an active-ID set and scans the active list for every event;
matching also sorts candidates and shifts the list when makers are removed.
Its work therefore grows with active book depth `B`. Version B indexes active
IDs and groups FIFO makers by price, removing those repeated `B` scans. The
saved buildup early/late latency and timeout records expose this difference,
while cancellation churn shows that a large event count `M` alone is not the
bottleneck when active depth remains near zero. Version B pays higher live-state
memory and `O(P)` sorted-list shifts when price levels appear or disappear.
"""
)
