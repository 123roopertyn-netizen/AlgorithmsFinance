"""Dashboard views disclose missing runs and keep both versions visible."""

from __future__ import annotations

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_PATH = PROJECT_ROOT / "dashboard" / "12_app.py"


def selectbox(app: AppTest, label: str):
    """Return the uniquely labelled select box from a rendered application."""
    matches = [box for box in app.selectbox if box.label == label]
    assert len(matches) == 1
    return matches[0]


def chart_specs(app: AppTest) -> list[dict[str, object]]:
    """Decode every emitted Vega-Lite specification."""
    return [json.loads(chart.proto.spec) for chart in app.get("vega_lite_chart")]


def test_default_dashboard_is_paired_status_aware_and_log_scaled() -> None:
    app = AppTest.from_file(str(DASHBOARD_PATH), default_timeout=30).run()

    assert not app.exception
    assert selectbox(app, "Experiment group").value == "formal"
    assert selectbox(app, "Configured price levels per side").value == 1_000
    assert selectbox(app, "Latency seed").value == 43
    assert selectbox(app, "Memory mode").value == "memory_state"
    assert selectbox(app, "Memory scenario").value == "cancel_churn"
    assert selectbox(app, "Memory event count").value == 100_000

    coverage = next(
        table.value
        for table in app.dataframe
        if list(table.value.columns)
        == [
            "version",
            "event_count",
            "seed",
            "outcome",
            "timeout_seconds",
            "median_throughput_events_per_second",
        ]
    )
    assert coverage[["event_count", "seed", "version"]].head(4).values.tolist() == [
        [1_000, 42, "baseline"],
        [1_000, 42, "revised"],
        [1_000, 43, "baseline"],
        [1_000, 43, "revised"],
    ]

    latency_table = next(
        table.value
        for table in app.dataframe
        if {"scope", "median_us", "p95_us", "p99_us"}.issubset(
            table.value.columns
        )
    )
    assert set(latency_table["version"]) == {"baseline", "revised"}

    specs = chart_specs(app)
    latency_spec = next(
        spec
        for spec in specs
        if spec.get("facet", {}).get("column", {}).get("field") == "percentile"
    )
    latency_encoding = latency_spec["spec"]["encoding"]
    assert latency_encoding["y"]["scale"]["type"] == "log"
    assert latency_encoding["xOffset"]["field"] == "version"

    throughput_spec = next(
        spec
        for spec in specs
        if spec.get("encoding", {}).get("y", {}).get("field")
        == "throughput_events_per_second"
    )
    assert throughput_spec["encoding"]["x"]["scale"]["type"] == "log"
    assert throughput_spec["encoding"]["y"]["scale"]["type"] == "log"
    assert throughput_spec["encoding"]["y"]["title"] == "Events/second (log)"
    assert throughput_spec["padding"]["left"] == 55

    repeat_distribution_spec = next(
        spec
        for spec in specs
        if spec.get("facet", {}).get("column", {}).get("field") == "version"
        and spec.get("spec", {}).get("mark", {}).get("type") == "boxplot"
    )
    assert (
        repeat_distribution_spec["spec"]["encoding"]["y"]["scale"]["type"]
        == "log"
    )

    liquidation_specs = [
        spec
        for spec in specs
        if spec.get("encoding", {}).get("x", {}).get("field") == "sale_label"
    ]
    assert {spec["title"] for spec in liquidation_specs} == {
        "Fresh-book construction",
        "Market sell",
    }
    assert all(
        spec["encoding"]["y"]["scale"]["type"] == "log"
        and spec["padding"]["left"] == 55
        for spec in liquidation_specs
    )
    assert (
        liquidation_specs[0]["encoding"]["y"]["scale"]["domain"]
        == liquidation_specs[1]["encoding"]["y"]["scale"]["domain"]
    )

    pair_table = next(
        table.value
        for table in app.dataframe
        if "all_recorded_counts_and_final_invariants_equal" in table.value.columns
    )
    assert pair_table["both_versions_present"].all()
    assert pair_table[
        "all_recorded_counts_and_final_invariants_equal"
    ].all()


def test_stopped_extension_runs_remain_visible_without_fabricated_points() -> None:
    app = AppTest.from_file(str(DASHBOARD_PATH), default_timeout=30).run()

    selectbox(app, "Experiment group").select("extension_1m").run()
    selectbox(app, "Throughput scenario").select("buildup").run()

    assert not app.exception
    assert any(
        "No completed throughput measurement exists" in message.value
        for message in app.info
    )
    warning_text = " ".join(message.value for message in app.warning)
    assert "baseline" in warning_text
    assert "revised" in warning_text
    assert "stopped_timeout" in warning_text

    coverage = next(
        table.value
        for table in app.dataframe
        if list(table.value.columns)
        == [
            "version",
            "event_count",
            "seed",
            "outcome",
            "timeout_seconds",
            "median_throughput_events_per_second",
        ]
    )
    assert set(coverage["version"]) == {"baseline", "revised"}
    assert set(coverage["outcome"]) == {"stopped_timeout"}
    assert coverage["median_throughput_events_per_second"].isna().all()
