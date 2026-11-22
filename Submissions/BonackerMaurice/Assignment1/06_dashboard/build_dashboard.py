"""Build 06_dashboard/dashboard.html from saved results only.

Usage (from Assignment1/):
    python 06_dashboard/build_dashboard.py

Reads ONLY files in 05_results/ (it never replays or benchmarks anything):
    replay_summary.csv   one row per (version, scenario)
    tests_latest.txt     saved `python -m pytest -q` output
Writes one self-contained HTML file; charts are PNGs embedded as base64.

Extending: every chart groups bars by the `version` column, so Version B
rows in replay_summary.csv appear as a second series without code changes.
A later benchmark CSV gets its own section function added to SECTIONS.
"""

import base64
import csv
import html
import io
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "05_results"
OUT = Path(__file__).resolve().parent / "dashboard.html"

# Fixed colour per version (never by rank), so A keeps its colour when B is added.
VERSION_COLORS = {"a": "#2a78d6", "b": "#eb6834"}
SCENARIO_ORDER = ["buildup", "crowded", "mixed", "sweep", "cancel_churn"]


# ----- loading ----------------------------------------------------------------

def read_csv(name):
    path = RESULTS / name
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_test_summary():
    """(passed, failed, text line) from the saved pytest output, or None."""
    path = RESULTS / "tests_latest.txt"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    last = [line for line in text.splitlines() if line.strip()][-1]
    passed = re.search(r"(\d+) passed", last)
    failed = re.search(r"(\d+) failed", last)
    return (int(passed.group(1)) if passed else 0,
            int(failed.group(1)) if failed else 0,
            last.strip("= "))


# ----- charts -----------------------------------------------------------------

def scenarios_in(rows):
    present = {r["scenario"] for r in rows}
    ordered = [s for s in SCENARIO_ORDER if s in present]
    return ordered + sorted(present - set(ordered))


def grouped_bars(ax, rows, field, ylabel, fmt):
    """Bars per scenario, one bar per version. Missing rows leave a gap."""
    scenarios = scenarios_in(rows)
    versions = sorted({r["version"] for r in rows})
    width = 0.8 / len(versions)
    for k, version in enumerate(versions):
        by_scenario = {r["scenario"]: r for r in rows if r["version"] == version}
        xs, ys = [], []
        for i, s in enumerate(scenarios):
            value = by_scenario.get(s, {}).get(field, "")
            if value != "":
                xs.append(i + (k - (len(versions) - 1) / 2) * width)
                ys.append(float(value))
        bars = ax.bar(xs, ys, width=width * 0.9, label=f"Version {version.upper()}",
                      color=VERSION_COLORS.get(version, "#777777"))
        ax.bar_label(bars, labels=[fmt(y) for y in ys], fontsize=8, padding=2)
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)
    if len(versions) > 1:
        ax.legend(frameon=False)


def figure_to_img(fig, alt):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{data}">'


# ----- sections ---------------------------------------------------------------

def section_correctness(summary):
    tests = read_test_summary()
    if tests is None:
        test_text = "Tests: no saved pytest output (05_results/tests_latest.txt missing)."
    else:
        passed, failed, line = tests
        test_text = f"Tests: {passed} passed, {failed} failed ({html.escape(line)})."
    parts = []
    for version in sorted({r["version"] for r in summary}):
        flags = [f"{r['scenario']} {r['invariants_ok']}"
                 for r in summary if r["version"] == version]
        parts.append(f"Version {version.upper()}: " + ", ".join(flags))
    inv_text = ("Invariants OK after every event: " + "; ".join(parts) + "."
                if parts else "Invariants: no replay summary.")
    return f"<h2>Correctness</h2>\n<p>{test_text}<br>{inv_text}</p>"


def section_summary_table(summary):
    cols = list(summary[0].keys())
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    body = "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(r[c]))}</td>" for c in cols) + "</tr>"
        for r in summary)
    return (
        "<h2>Replay summary (05_results/replay_summary.csv)</h2>\n"
        "<p>wall_seconds: one plain replay of preloaded events on a fresh book, "
        "in seconds; file reading and checks excluded; single run, not the "
        "benchmark. peak_active_orders in orders, peak_price_levels in occupied "
        "(side, price) levels.</p>\n"
        f"<table>\n<tr>{head}</tr>\n{body}\n</table>")


def section_wall_time(summary):
    fig, ax = plt.subplots(figsize=(7, 3.6))
    grouped_bars(ax, summary, "wall_seconds", "wall time (seconds)",
                 lambda y: f"{y:.3f}")
    ax.set_title("Replay wall time per scenario (10,000 events)", loc="left")
    return "<h2>Wall time</h2>\n" + figure_to_img(fig, "wall time per scenario")


def section_peaks(summary):
    # Two panels with their own axes: orders and price levels have very
    # different scales, and one shared axis would hide the small values.
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 3.6))
    grouped_bars(left, summary, "peak_active_orders", "peak active orders (orders)",
                 lambda y: f"{y:,.0f}")
    left.set_title("Peak active orders", loc="left")
    grouped_bars(right, summary, "peak_price_levels",
                 "peak occupied price levels (levels)", lambda y: f"{y:,.0f}")
    right.set_title("Peak occupied price levels", loc="left")
    for ax in (left, right):
        ax.tick_params(axis="x", labelsize=8)
    return "<h2>Book size</h2>\n" + figure_to_img(fig, "peak orders and price levels")


SECTIONS = [section_correctness, section_summary_table, section_wall_time,
            section_peaks]


def main():
    summary = read_csv("replay_summary.csv")
    if not summary:
        raise SystemExit("05_results/replay_summary.csv is missing or empty")
    body = "\n\n".join(section(summary) for section in SECTIONS)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Order book results</title>
<style>
body {{ font-family: sans-serif; max-width: 1100px; margin: 2em auto; padding: 0 16px; }}
table {{ border-collapse: collapse; font-size: 0.9em; }}
th, td {{ border: 1px solid #ccc; padding: 3px 8px; text-align: right; }}
img {{ max-width: 100%; }}
</style>
</head>
<body>
<h1>Limit order book: saved results</h1>
<p>Built from files in 05_results/ only. Synthetic teaching data, not
exchange records.</p>

{body}
</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
