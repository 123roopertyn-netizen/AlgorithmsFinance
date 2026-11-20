"""Streamlit dashboard: shows the SAVED results of the membership lab. It measures nothing.

    .venv/bin/streamlit run dashboard/app.py

Reads results/ (timing_*.csv|json, memory_*.csv|json) written by bench_time.py and
bench_memory.py. If a file is missing, the page says which command creates it.
"""
import altair as alt
import pandas as pd
import streamlit as st

import loaders

st.set_page_config(page_title="Membership lab results", layout="wide")

METHOD_ORDER = ["linear_v1", "binary_v1", "binary_v2", "hash_v1"]
METHOD_COLORS = ["#1b6ca8", "#d95f02", "#9b4dca", "#2a9d3c"]     # distinct, colour-blind safe
METHOD_LABEL = {"linear_v1": "linear v1", "binary_v1": "binary v1 (recursive)",
                "binary_v2": "binary v2 (iterative)", "hash_v1": "hash set v1"}
PHASE_TEXT = {
    "prepare": "Preparation: sorting a copy (binary) or building the set (hash). "
               "Linear search has none (value = call overhead only).",
    "query": "Query batch: all q queries answered, prepared state already built.",
    "total": "Total: method(ids, queries) measured on its own (NOT the sum of the other two).",
}


@st.cache_data
def cached_results(signature):
    return loaders.load_results()


def signature():
    return tuple((name, (loaders.RESULTS_DIR / name).stat().st_mtime)
                 for name in loaders.REQUIRED if (loaders.RESULTS_DIR / name).exists())


missing = loaders.missing_files()
if missing:
    st.title("Membership lab results")
    st.error("Saved results not found: " + ", ".join(missing))
    st.markdown("Create them from the lab folder first:")
    st.code(".venv/bin/python bench_time.py\n.venv/bin/python bench_memory.py", language="bash")
    st.stop()

data = cached_results(signature())
time_summary, time_raw = data["time_summary"], data["time_raw"]
mem_summary, mem_raw = data["mem_summary"], data["mem_raw"]
time_meta, mem_meta = data["time_meta"], data["mem_meta"]
env = time_meta["environment"]

# ---- sidebar ----------------------------------------------------------------------
st.sidebar.header("Settings")
q_options = sorted(int(v) for v in time_summary["q"].unique())
q = st.sidebar.radio("Query count q", q_options, index=len(q_options) - 1, horizontal=True)
hit_rate = st.sidebar.selectbox(
    "Hit rate", ["mixed", "all-present", "all-absent"],
    help="Share of queries found in the array. mixed = (q + 1) // 2 queries present.")
unit_name = st.sidebar.selectbox("Time unit", list(loaders.UNITS), index=2)
factor = loaders.UNITS[unit_name]
per_query = st.sidebar.radio(
    "Time per", ["batch", "query"], horizontal=True,
    help="batch = all q queries together. Per query = batch time / q; it exists for the "
         "phases query and total only, preparation is always per batch.") == "query"
log_y = st.sidebar.checkbox("Logarithmic y axis", value=True)
st.sidebar.caption(f"Units: time in {unit_name}; memory in bytes. Medians of "
                   f"{time_meta['protocol']['repeats']} repeats; bars show min to max.")

st.title("Membership lab: linear, binary and hash set")
st.caption(f"Saved results, seed {time_meta['seed']}, "
           f"Python {env['python_version'].split()[0]}, {env.get('cpu_model', env['machine'])}, "
           f"code commit {env['git_commit'][:7]}. Duplicates: "
           f"{time_meta['generator']['duplicates']}. Showing q = {q}, hit rate = {hit_rate}.")

color = alt.Color("method:N", sort=METHOD_ORDER, title="Method",
                  scale=alt.Scale(domain=METHOD_ORDER, range=METHOD_COLORS))
x_axis = alt.X("n:Q", scale=alt.Scale(type="log"), title="n (number of IDs)",
               axis=alt.Axis(values=[1000, 10000, 100000], format="~s"))


def y_axis(title):
    return alt.Y("value:Q", scale=alt.Scale(type="log" if log_y else "linear",
                                            zero=not log_y), title=title)


def time_chart(frame, title):
    base = alt.Chart(frame).encode(x=x_axis, color=color)
    bars = base.mark_rule(opacity=0.45).encode(
        y=alt.Y("low:Q", scale=alt.Scale(type="log" if log_y else "linear", zero=not log_y)),
        y2="high:Q")
    line = base.mark_line(point=alt.OverlayMarkDef(size=60)).encode(
        y=y_axis(title), strokeDash=alt.StrokeDash("version:N", legend=None),
        tooltip=[alt.Tooltip("method:N"), alt.Tooltip("n:Q"),
                 alt.Tooltip("value:Q", format=".4g", title="median"),
                 alt.Tooltip("low:Q", format=".4g", title="min"),
                 alt.Tooltip("high:Q", format=".4g", title="max"),
                 alt.Tooltip("calls_per_repeat:Q", title="calls per repeat")])
    return (bars + line).properties(height=300)


tab_time, tab_total, tab_versions, tab_memory, tab_raw, tab_env = st.tabs(
    ["Time vs n", "Total vs prepare + query", "v1 vs v2", "Memory", "Raw repeats",
     "Environment"])

# ---- time vs n --------------------------------------------------------------------
with tab_time:
    st.markdown("One curve per method. **Preparation, query batch and total are shown "
                "separately.** Binary v1 and v2 are the solid orange (v1) and dashed purple (v2) "
                "curves. The vertical bar at each point is the min to max of the repeats.")
    selection = time_summary[(time_summary["q"] == q) & (time_summary["hit_rate"] == hit_rate)]
    for phase in loaders.PHASES:
        frame = loaders.scaled_times(selection, phase, per_query, factor)
        unit_text = f"{unit_name.split(' ')[1].strip('()')} {frame['per'].iloc[0]}"
        st.subheader(phase.capitalize())
        st.caption(PHASE_TEXT[phase] + f" Unit: {unit_text}; q = {q}; hit rate = {hit_rate}.")
        st.altair_chart(time_chart(frame, f"{phase} ({unit_text})"), width="stretch")

# ---- total vs prepare + query -----------------------------------------------------
with tab_total:
    comparison = loaders.total_vs_sum(time_summary)
    selected = comparison[(comparison["q"] == q) & (comparison["hit_rate"] == hit_rate)]
    st.markdown(
        "`total` is measured **on its own**; `prepare + query` is the sum of two other "
        "measurements. Both are shown, with the **spread** (max / min of the repeats). "
        "They can differ because the phases run as separate blocks at different moments "
        "(see the explanation below).")
    long = pd.concat([
        selected.assign(measure="measured total", value=selected["measured_total"] * factor,
                        low=selected["total_low"] * factor, high=selected["total_high"] * factor),
        selected.assign(measure="prepare + query", value=selected["prepare_plus_query"] * factor,
                        low=selected["sum_low"] * factor, high=selected["sum_high"] * factor)])
    long["method_label"] = long["method"].map(METHOD_LABEL)
    measure_color = alt.Color("measure:N", title="Measure", scale=alt.Scale(
        domain=["measured total", "prepare + query"], range=["#1b6ca8", "#e08a00"]))
    base = alt.Chart(long).encode(
        x=alt.X("n:O", title="n (number of IDs)", axis=alt.Axis(labelAngle=0, format="~s")),
        xOffset=alt.XOffset("measure:N"), color=measure_color)
    scale = alt.Scale(type="log" if log_y else "linear", zero=not log_y)
    layers = (
        base.mark_rule(opacity=0.8, strokeWidth=3).encode(
            y=alt.Y("low:Q", scale=scale), y2="high:Q")
        + base.mark_point(size=70, filled=True).encode(
            y=alt.Y("value:Q", scale=scale, title=f"time per batch ({unit_name})"),
            tooltip=["method", "n", "measure", alt.Tooltip("value:Q", format=".4g"),
                     alt.Tooltip("low:Q", format=".4g", title="min"),
                     alt.Tooltip("high:Q", format=".4g", title="max")])
    ).properties(width=105, height=300)
    chart = layers.facet(column=alt.Column(
        "method_label:N", title=None, sort=[METHOD_LABEL[m] for m in METHOD_ORDER])
    ).resolve_scale(y="independent")
    st.caption("One panel per method, own y axis. Point = median, bar = min to max of the "
               "repeats (the spread). Blue = measured total, orange = prepare + query.")
    st.altair_chart(chart, width="stretch")
    table = selected[["method", "n", "measured_total", "prepare_plus_query", "ratio",
                      "spread_prepare", "spread_query", "spread_total", "ranges_overlap"]].copy()
    table["measured_total"] *= factor
    table["prepare_plus_query"] *= factor
    st.dataframe(
        table, hide_index=True, width="stretch",
        column_config={
            "measured_total": st.column_config.NumberColumn(f"measured total ({unit_name})",
                                                            format="%.4g"),
            "prepare_plus_query": st.column_config.NumberColumn(
                f"prepare + query ({unit_name})", format="%.4g"),
            "ratio": st.column_config.NumberColumn("total / (prepare + query)", format="%.3f"),
            "spread_prepare": st.column_config.NumberColumn("spread prepare", format="%.2f"),
            "spread_query": st.column_config.NumberColumn("spread query", format="%.2f"),
            "spread_total": st.column_config.NumberColumn("spread total", format="%.2f"),
            "ranges_overlap": st.column_config.CheckboxColumn(
                "ranges overlap", help="[min, max] of total overlaps the summed ranges")})
    ratios = comparison["ratio"]
    st.markdown(
        f"**All {len(comparison)} configurations (every n, q, hit rate, method):** ratio from "
        f"{ratios.min():.2f} to {ratios.max():.2f}; {int(((ratios >= 0.97) & (ratios <= 1.03)).sum())}"
        f" within 3 %, {int((ratios < 0.97).sum())} below 0.97, {int((ratios > 1.03).sum())} above "
        f"1.03; ranges overlap in {int(comparison['ranges_overlap'].sum())}, "
        f"not in {int((~comparison['ranges_overlap']).sum())}.")
    note = time_meta.get("total_vs_prepare_plus_query", {}).get("explanation")
    if note:
        with st.expander("Why total and prepare + query differ", expanded=True):
            st.write(note)

# ---- v1 vs v2 ---------------------------------------------------------------------
with tab_versions:
    st.markdown("Binary search v1 (recursive) against v2 (iterative), same data and same "
                "sorted copy. v2 / v1 below 1 means v2 is faster.")
    versions = loaders.version_comparison(time_summary)
    chosen = versions[(versions["q"] == q) & (versions["hit_rate"] == hit_rate)].copy()
    for column in ("v1_recursive", "v2_iterative"):
        chosen[column] = chosen[column] * factor
    st.dataframe(
        chosen[["phase", "n", "v1_recursive", "v2_iterative", "v2_over_v1"]],
        hide_index=True, width="stretch",
        column_config={
            "v1_recursive": st.column_config.NumberColumn(f"v1 median ({unit_name})",
                                                          format="%.4g"),
            "v2_iterative": st.column_config.NumberColumn(f"v2 median ({unit_name})",
                                                          format="%.4g"),
            "v2_over_v1": st.column_config.NumberColumn("v2 / v1", format="%.3f")})
    query_ratio = versions[versions["phase"] == "query"]["v2_over_v1"]
    total_ratio = versions[versions["phase"] == "total"]["v2_over_v1"]
    st.markdown(
        f"Over all configurations the **query phase** ratio is {query_ratio.min():.2f} to "
        f"{query_ratio.max():.2f}; the **total** ratio is {total_ratio.min():.2f} to "
        f"{total_ratio.max():.2f}, because sorting the copy dominates the total.")

# ---- memory -----------------------------------------------------------------------
with tab_memory:
    st.markdown("Bytes allocated while the method runs (`tracemalloc`, fresh trace per "
                "method and phase, input built before tracing, output kept alive). "
                "**Not included: the input.** "
                f"Repeats: {mem_meta['repeats']}. Exact byte counts are from "
                f"Python {env['python_version'].split()[0]}.")
    field = st.radio("Value", ["median_current_bytes", "median_peak_bytes"], horizontal=True,
                     format_func=lambda f: "current (still allocated after the call)"
                     if "current" in f else "peak (largest at any moment)")
    memory_view = loaders.memory_table(mem_summary, q, hit_rate, field)
    st.dataframe(memory_view, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(c, format="%d")
                                for c in memory_view.columns[2:]})
    phase_mem = st.selectbox("Phase for the chart", loaders.PHASES, index=0)
    st.caption("Binary v1 and v2 sort the same copy, so their curves lie on top of each "
               "other in the prepare phase. The y axis is symmetric-log so that 0 bytes "
               "(linear search has no structure) can be shown.")
    chart_frame = mem_summary[(mem_summary["q"] == q) & (mem_summary["hit_rate"] == hit_rate)
                              & (mem_summary["phase"] == phase_mem)].rename(
        columns={field: "value"})
    st.altair_chart(
        alt.Chart(chart_frame).mark_line(point=True).encode(
            x=x_axis, color=color, strokeDash=alt.StrokeDash("version:N", legend=None),
            y=alt.Y("value:Q", scale=alt.Scale(type="symlog" if log_y else "linear"),
                    title=f"{phase_mem}: bytes"),
            tooltip=["method", "n", alt.Tooltip("value:Q", format=",.0f")]).properties(
                height=300), width="stretch")
    for key, text in mem_meta["included"].items():
        st.markdown(f"- **{key}**: {text}")

# ---- raw repeats ------------------------------------------------------------------
with tab_raw:
    st.markdown("Every saved repeat (seconds, not converted). `seconds_per_batch` = repeat "
                "time / `calls_per_repeat`. `seconds_per_query` is empty for preparation.")
    methods = st.multiselect("Methods", METHOD_ORDER, default=METHOD_ORDER)
    phases = st.multiselect("Phases", loaders.PHASES, default=loaders.PHASES)
    raw_view = time_raw[(time_raw["q"] == q) & (time_raw["hit_rate"] == hit_rate)
                        & time_raw["method"].isin(methods) & time_raw["phase"].isin(phases)]
    st.caption(f"{len(raw_view)} timing repeats for q = {q}, hit rate = {hit_rate}")
    st.dataframe(raw_view, hide_index=True, width="stretch")
    st.caption("Memory repeats (bytes)")
    st.dataframe(mem_raw[(mem_raw["q"] == q) & (mem_raw["hit_rate"] == hit_rate)
                         & mem_raw["method"].isin(methods) & mem_raw["phase"].isin(phases)],
                 hide_index=True, width="stretch")

# ---- environment ------------------------------------------------------------------
with tab_env:
    left, right = st.columns(2)
    with left:
        st.subheader("Timing run")
        st.json({"seed": time_meta["seed"], "generator": time_meta["generator"],
                 "units": time_meta["units"], "protocol": time_meta["protocol"],
                 "phases": time_meta["phases"], "started_utc": time_meta["started_utc"],
                 "finished_utc": time_meta["finished_utc"]}, expanded=1)
    with right:
        st.subheader("Machine, Python, git")
        st.json(env, expanded=1)
        st.subheader("Memory run")
        st.json({k: v for k, v in mem_meta.items() if k != "environment"}, expanded=1)
        mem_env = mem_meta["environment"]
        if mem_env.get("git_commit") != env.get("git_commit"):
            st.info(f"Memory results were produced at code commit {mem_env['git_commit'][:7]}, "
                    f"timing results at {env['git_commit'][:7]}.")
    st.subheader("Datasets")
    st.dataframe(pd.DataFrame(time_meta["datasets"]), hide_index=True, width="stretch")
