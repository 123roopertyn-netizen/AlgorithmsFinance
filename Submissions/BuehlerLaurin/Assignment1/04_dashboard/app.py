"""Results dashboard: reads saved results only, never runs a benchmark.

Run from the exercise root:  streamlit run 04_dashboard/app.py     (http://localhost:8501)

The project root is the parent of 04_dashboard/.

Reads one run folder 03_results/runs/<UTC stamp>_<commit>[_tag]/ with the standard files
(see aif-bench "Results schema"); every file is optional and missing ones are shown
as "not measured":
  timing.csv   version, workload, seed, size, phase, repeat, seconds, status, repeats_requested, [inner, ...]
               (a stopped/failed cell writes one row with its status and empty seconds; rows whose
                status is not 'ok', and cells with fewer completed than requested repeats, are
                excluded from all medians, curves, ratios and throughput, and listed in Overview)
  latency.csv  version, workload, size, event_type, segment, n, p50_ns, p95_ns, p99_ns, max_ns
  memory.csv   version, workload, size, measure, processed, current_bytes, peak_bytes, includes
  counts.csv   version, workload, size, counter, value
  env.json     from harness.env_info()
  tests.txt    test output of this commit
and 00_docs/REPORT.md (section "Profiling and one explained bottleneck") plus 05_evidence/INDEX.md.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent          # parent of 04_dashboard/
RUNS = ROOT / "03_results" / "runs"

st.set_page_config(page_title="Results dashboard", layout="wide")


@st.cache_data
def load_csv(path: str) -> pd.DataFrame | None:
    p = Path(path)
    return pd.read_csv(p) if p.exists() else None


@st.cache_data
def load_text(path: str) -> str | None:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else None


def not_measured(name: str) -> None:
    st.info(f"{name}: not measured in this run (file missing).")


CELL = ["version", "workload", "seed", "size", "phase"]


def ok_mask(df: pd.DataFrame) -> pd.Series:
    """Rows that are completed measurements. Stopped/failed rows never enter a median."""
    if "status" not in df:
        return pd.Series(True, index=df.index)
    return df["status"].fillna("ok").astype(str).eq("ok")


def validate_timing(df: pd.DataFrame) -> pd.DataFrame:
    """Mark rows that must never enter an aggregate, BEFORE any median or count.

    An 'ok' row becomes 'invalid(...)' when its seconds are missing, non-finite or <= 0,
    or when the same cell + repeat id appears more than once (all copies are invalid:
    the file cannot tell which one is real). Completed repeats are then distinct ids.
    """
    d = df.copy()
    if "status" not in d:
        d["status"] = "ok"
    d["status"] = d["status"].fillna("ok").astype(str)
    ok = d["status"].eq("ok")
    secs = pd.to_numeric(d["seconds"], errors="coerce")
    bad_secs = ok & ~(np.isfinite(secs) & (secs > 0))
    d.loc[bad_secs, "status"] = "invalid(seconds missing, non-finite or <= 0)"
    keys = [c for c in CELL + ["repeat"] if c in d]
    if "repeat" in d:
        dup = d["status"].eq("ok") & d.duplicated(subset=keys, keep=False)
        d.loc[dup, "status"] = "invalid(duplicate repeat id)"
    return d


def cell_status(df: pd.DataFrame) -> pd.DataFrame:
    """One row per benchmark cell: completed vs requested repeats and non-ok statuses."""
    keys = [c for c in CELL if c in df]
    d = df.assign(_ok=ok_mask(df), _status=df["status"].fillna("ok").astype(str) if "status" in df else "ok")
    g = d.groupby(keys, dropna=False)
    out = g["_ok"].sum().rename("completed").to_frame()
    out["requested"] = g["repeats_requested"].max() if "repeats_requested" in d else pd.NA
    out["statuses"] = g["_status"].agg(lambda s: ",".join(sorted(set(s) - {"ok"})) or "ok")
    req = pd.to_numeric(out["requested"], errors="coerce")
    out["complete"] = (out["statuses"] == "ok") & (req.isna() | (out["completed"] >= req))
    return out.reset_index()


runs = sorted([d for d in RUNS.glob("*") if d.is_dir()], reverse=True) if RUNS.exists() else []
if not runs:
    st.warning(f"No run folders found in {RUNS}. Run the benchmark scripts first.")
    st.stop()

run = Path(st.sidebar.selectbox("Run (UTC stamp _ commit _ tag)", [str(r) for r in runs],
                                format_func=lambda s: Path(s).name))
st.sidebar.caption("Official results come from runs on a clean commit (no '-dirty').")
timing = load_csv(str(run / "timing.csv"))
latency = load_csv(str(run / "latency.csv"))
memory = load_csv(str(run / "memory.csv"))
counts = load_csv(str(run / "counts.csv"))
env_txt = load_text(str(run / "env.json"))
env = json.loads(env_txt) if env_txt else {}
timing = validate_timing(timing) if timing is not None else None      # before ANY aggregation
status = cell_status(timing) if timing is not None else None
timing_ok = timing[ok_mask(timing)] if timing is not None else None   # completed rows only

st.title("Results dashboard")
st.caption(f"Run `{run.name}` · Python {env.get('python', '?')} · {env.get('platform', '?')} · "
           f"commit {str(env.get('git_commit', '?'))[:7]}{' (dirty)' if env.get('git_dirty') else ''}")

tabs = st.tabs(["Overview", "Scaling", "A vs B", "Throughput & latency", "Memory",
                "Operation counts", "Correctness", "Bottleneck", "Raw data & environment"])

# ---- Overview: settings, coverage, stopped / missing runs
with tabs[0]:
    if timing is None:
        not_measured("Timing")
    else:
        st.subheader("Coverage: completed vs requested repeats per cell")
        st.dataframe(status)
        if "repeats_requested" not in timing:
            st.warning("timing.csv has no 'repeats_requested' column: partial cells cannot be detected.")
        invalid = timing[timing["status"].str.startswith("invalid")]
        if len(invalid):
            st.subheader("Invalid rows (excluded)")
            st.error(f"{len(invalid)} rows have duplicate repeat ids or unusable seconds. "
                     "Their cells count as partial. Fix the benchmark script; do not edit the CSV by hand.")
            st.dataframe(invalid)
        incomplete = status[~status["complete"]]
        st.subheader("Stopped / failed / partial cells")
        if len(incomplete):
            st.dataframe(incomplete)
            st.caption("These cells are excluded from every median, curve, ratio and throughput below.")
        else:
            st.success("None.")
        st.caption("Units: seconds unless stated. Medians over completed repeats; raw repeats in the last tab.")

# ---- Scaling: time vs size, one curve per version, per phase
with tabs[1]:
    if timing is None:
        not_measured("Timing")
    else:
        c1, c2, c3 = st.columns(3)
        wl = c1.selectbox("Workload", sorted(timing["workload"].unique()))
        phases = sorted(timing["phase"].unique())
        ph = c2.selectbox("Phase", phases, index=phases.index("run") if "run" in phases else 0)
        logy = c3.checkbox("plot log10(seconds)", value=True)
        d = timing_ok[(timing_ok["workload"] == wl) & (timing_ok["phase"] == ph)]
        med = d.groupby(["size", "version"])["seconds"].median().unstack("version").sort_index()
        inc = status[(~status["complete"]) & (status["workload"] == wl) & (status["phase"] == ph)]
        for _, r in inc.iterrows():
            med.loc[r["size"], r["version"]] = float("nan")          # no point for a stopped/partial cell
        if len(inc):
            st.warning("Stopped/partial (no point plotted): " + ", ".join(
                f"{r['version']} @ size {r['size']} ({r['statuses']}, {r['completed']}/{r['requested']} repeats)"
                for _, r in inc.iterrows()))
        import numpy as np
        st.line_chart(np.log10(med.where(med > 0)) if logy else med)
        st.caption(f"Median {'log10 ' if logy else ''}seconds per '{ph}' vs input size, one line per version. "
                   "Exact values in the table.")
        st.dataframe(med)

# ---- A vs B: ratio of medians
with tabs[2]:
    if timing is None or timing["version"].nunique() < 2:
        not_measured("Version comparison")
    else:
        vs = sorted(timing["version"].unique())
        a, b = st.columns(2)
        va = a.selectbox("Baseline", vs, index=0)
        vb = b.selectbox("Revision", vs, index=len(vs) - 1)
        keys = ["workload", "size", "phase"]
        med = timing_ok.groupby(keys + ["version"])["seconds"].median().unstack("version")
        bad = status[~status["complete"]].groupby(keys + ["version"]).size().unstack("version")
        if va in med and vb in med:
            out = med[[va, vb]].copy()
            out["speedup (baseline / revision)"] = out[va] / out[vb]
            out["note"] = ""
            for v in (va, vb):
                if v in bad:
                    hit = bad[v].reindex(out.index).fillna(0) > 0
                    out.loc[hit, [v, "speedup (baseline / revision)"]] = float("nan")
                    out.loc[hit, "note"] = out.loc[hit, "note"].where(out.loc[hit, "note"] == "",
                                                                      out.loc[hit, "note"] + "; ") + f"{v} stopped/partial/invalid"
            out.loc[out["note"] != "", "note"] += ": speedup unavailable"
            st.dataframe(out.reset_index())
            st.caption("> 1 means the revision is faster. It does not have to win everywhere; explain losses. "
                       "No lower bound is shown for stopped cells: the time limit covers the whole subprocess "
                       "(setup, parsing, all repeats), not the compared median.")

# ---- Throughput & latency
with tabs[3]:
    if timing is not None and {"phase", "size"} <= set(timing.columns):
        r = timing_ok[timing_ok["phase"] == "run"]
        if len(r):
            thr = r.groupby(["workload", "version", "size"])["seconds"].median().reset_index()
            thr["events_per_s"] = thr["size"] / thr["seconds"]
            inc = status[(~status["complete"]) & (status["phase"] == "run")][["workload", "version", "size"]]
            thr = thr.merge(inc.drop_duplicates().assign(_inc=True), how="left", on=["workload", "version", "size"])
            thr.loc[thr["_inc"].fillna(False).astype(bool), "events_per_s"] = float("nan")
            thr = thr.drop(columns="_inc")
            st.subheader("Throughput (events / median replay seconds)")
            st.dataframe(thr)
    if latency is None:
        not_measured("Latency")
    else:
        st.subheader("Per-event processing latency (closed-loop service time, nearest-rank percentiles, ns)")
        st.dataframe(latency)
        st.caption("Not response time under load; not derived from 1/throughput.")

# ---- Memory
with tabs[4]:
    if memory is None:
        not_measured("Memory")
    else:
        st.caption("tracemalloc traced Python allocations, separate run from timing. "
                   "'includes' states whether input, structures, outputs and history are counted.")
        peaks = memory[memory["measure"] == "peak"] if "measure" in memory else memory
        st.dataframe(peaks)
        if "measure" in memory and (memory["measure"] == "curve").any():
            cur = memory[memory["measure"] == "curve"]
            wl = st.selectbox("Workload (memory over time)", sorted(cur["workload"].unique()))
            c = cur[cur["workload"] == wl].pivot_table(index="processed", columns="version",
                                                      values="current_bytes", aggfunc="max")
            st.line_chart(c)
            st.caption("Current traced bytes vs events processed. After churn it must follow the live size, "
                       "not the event count.")

# ---- Operation counts
with tabs[5]:
    if counts is None:
        not_measured("Operation counts")
    else:
        st.caption("Counter run, separate from timing. Use it to explain the timing curves.")
        st.dataframe(counts.pivot_table(index=["workload", "size", "counter"], columns="version",
                                        values="value", aggfunc="max"))

# ---- Correctness
with tabs[6]:
    tests = load_text(str(run / "tests.txt"))
    st.subheader("Test output of this commit")
    st.code(tests[-3000:] if tests else "tests.txt missing", language="text")
    idx = load_text(str(ROOT / "05_evidence" / "INDEX.md"))
    st.subheader("Evidence index")
    st.markdown(idx if idx else "_05_evidence/INDEX.md missing_")

# ---- Bottleneck explanation
with tabs[7]:
    rep = load_text(str(ROOT / "00_docs" / "REPORT.md"))
    if rep and "bottleneck" in rep.lower():
        start = rep.lower().find("bottleneck")
        sec_start = rep.rfind("\n## ", 0, start)
        sec_end = rep.find("\n## ", start)
        st.markdown(rep[sec_start if sec_start >= 0 else start: sec_end if sec_end > 0 else None])
    else:
        st.info("Write the bottleneck explanation in 00_docs/REPORT.md (code + operation counts + complexity).")

# ---- Raw data & environment
with tabs[8]:
    for name, df in [("timing.csv", timing), ("latency.csv", latency), ("memory.csv", memory),
                     ("counts.csv", counts)]:
        with st.expander(name, expanded=False):
            st.dataframe(df) if df is not None else st.write("missing")
    with st.expander("env.json", expanded=False):
        st.json(env)
