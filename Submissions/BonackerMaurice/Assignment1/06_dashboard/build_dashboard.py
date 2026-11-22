"""Build 06_dashboard/dashboard.html from saved results only.

Usage (from Assignment1/):
    python 06_dashboard/build_dashboard.py

Reads ONLY files in 05_results/ (it never replays or benchmarks anything):
    replay_summary.csv            one row per (version, scenario)
    tests_by_case.csv             one row per (test, version)
    scaling_version_*.csv         seconds vs events, one file per version
    scaling_version_*.meta.json   declared time limit
    liquidation_version_*.csv     10/100/200% sales, one file per version
Writes one self-contained HTML file; charts are PNGs embedded as base64.

Extending: every table and chart is keyed by the `version` column, and the
*_version_*.csv files are globbed, so Version B appears as extra
rows/columns/series without code changes. A new result file gets its own
section function added to SECTIONS.
"""

import base64
import csv
import html
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "05_results"
OUT = Path(__file__).resolve().parent / "dashboard.html"

BTC = 100_000_000

# Fixed colour and label per version (never by rank), so a version keeps its
# colour when others are added. Colour always means version in every chart.
VERSION_ORDER = ["a", "b_sorted", "b_heap"]
VERSION_COLORS = {"a": "#2a78d6", "b_sorted": "#eb6834", "b_heap": "#1baf7a"}
VERSION_LABELS = {"a": "Version A", "b_sorted": "Version B-sorted",
                  "b_heap": "Version B-heap"}
SCENARIO_ORDER = ["buildup", "crowded", "mixed", "sweep", "cancel_churn"]


def label(version):
    return VERSION_LABELS.get(version, f"Version {version}")


# ----- loading ----------------------------------------------------------------

def read_csv(name):
    path = RESULTS / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_csv_glob(pattern):
    """Concatenate all matching CSVs (one per version)."""
    rows = []
    for path in sorted(RESULTS.glob(pattern)):
        rows.extend(read_csv(path.name))
    return rows


def scaling_time_limit():
    for path in sorted(RESULTS.glob("scaling_version_*.meta.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        if "time_limit_seconds_per_run" in meta:
            return meta["time_limit_seconds_per_run"]
    return None


# ----- small helpers ----------------------------------------------------------

def versions_in(rows):
    """Engine versions present, in the fixed display order (unknown ones last)."""
    present = {r["version"] for r in rows} - {"none", "all"}
    return [v for v in VERSION_ORDER if v in present] + sorted(present - set(VERSION_ORDER))


def scenarios_in(rows):
    present = {r["scenario"] for r in rows}
    ordered = [s for s in SCENARIO_ORDER if s in present]
    return ordered + sorted(present - set(ordered))


def btc(units):
    """Exact BTC string from integer units (no float rounding)."""
    units = int(units)
    return f"{units // BTC:,}.{units % BTC:08d}"


def html_table(header, rows):
    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in header)
    body = "\n".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row)
                     + "</tr>" for row in rows)
    return f"<table>\n<tr>{head}</tr>\n{body}\n</table>"


def grouped_bars(ax, rows, field, ylabel, fmt):
    """Bars per scenario, one bar per version. Missing rows leave a gap."""
    scenarios = scenarios_in(rows)
    versions = versions_in(rows)
    width = 0.8 / len(versions)
    points = {}                                   # scenario index -> [(x, y)]
    for k, version in enumerate(versions):
        by_scenario = {r["scenario"]: r for r in rows if r["version"] == version}
        xs, ys = [], []
        for i, s in enumerate(scenarios):
            value = by_scenario.get(s, {}).get(field, "")
            if value != "":
                xs.append(i + (k - (len(versions) - 1) / 2) * width)
                ys.append(float(value))
                points.setdefault(i, []).append((xs[-1], ys[-1]))
        ax.bar(xs, ys, width=width * 0.9, label=label(version),
               color=VERSION_COLORS.get(version, "#777777"))
    # Value labels: one centred label when every version has the same value
    # (e.g. book peaks), otherwise one label per bar.
    offset = 0.01 * max((y for pts in points.values() for _, y in pts), default=1)
    for i, pts in points.items():
        if len({y for _, y in pts}) == 1:
            ax.text(i, pts[0][1] + offset, fmt(pts[0][1]), ha="center", va="bottom",
                    fontsize=7)
        else:
            for x, y in pts:
                ax.text(x, y + offset, fmt(y), ha="center", va="bottom", fontsize=7)
    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels(scenarios)
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.set_axisbelow(True)
    if len(versions) > 1:
        ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12),
                  ncol=len(versions), fontsize=8)


def figure_to_img(fig, alt):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    return f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{data}">'


# ----- sections ---------------------------------------------------------------

def section_correctness(summary):
    tests = read_csv("tests_by_case.csv")
    parts = ["<h2>Correctness</h2>"]
    if not tests:
        parts.append("<p>No saved test results (05_results/tests_by_case.csv missing).</p>")
    else:
        versions = versions_in(tests)
        has_none = any(r["version"] == "none" for r in tests)
        # One row per (test, source), in file order; one column per version.
        # version "all" = one test comparing all versions: shown in every column.
        cases = {}
        for r in tests:
            cases.setdefault((r["test"], r["source"]), {})[r["version"]] = r["result"]
        header = (["test", "source of expected values"]
                  + [label(v) for v in versions]
                  + (["no engine needed"] if has_none else []))
        rows = []
        for (test, source), by_version in cases.items():
            cols = [by_version.get(v, by_version.get("all", "n/a")) for v in versions]
            if has_none:
                cols.append(by_version.get("none", ""))
            rows.append([test, source] + cols)
        passed = sum(r["result"] == "pass" for r in tests)
        parts.append(f"<p>Test cases: {passed} of {len(tests)} pass "
                     "(05_results/tests_by_case.csv). n/a = the test is not "
                     "defined for that version (white-box tests of one variant).</p>")
        parts.append(html_table(header, rows))

    diff = read_csv("differential_tests.csv")
    if diff:
        total = lambda k: sum(int(r[k]) for r in diff)  # noqa: E731
        bad = sum(r["result"] != "pass" for r in diff)
        parts.append(
            f"<p>Differential test (05_results/differential_tests.csv, versions "
            f"{html.escape(diff[0]['versions'].replace('|', ', '))}): "
            f"{len(diff)} seeded random streams, {total('events'):,} events "
            f"({total('rejected'):,} rejected, {total('crossing_limits'):,} crossing "
            f"limits, {total('market_sells'):,} market sells, {total('cancelled'):,} "
            f"cancels, {total('not_found'):,} not_found). Results and books compared "
            f"after every event: {total('mismatching_events')} mismatching events, "
            f"{total('invariant_failures')} invariant failures, {bad} failed streams.</p>")

    flags = []
    for version in versions_in(summary):
        oks = [f"{r['scenario']} {r['invariants_ok']}"
               for r in summary if r["version"] == version]
        flags.append(f"{label(version)}: " + ", ".join(oks))
    if flags:
        parts.append("<p>Invariants OK after every event (replay of the five "
                     "supplied 10,000-event files): " + "; ".join(flags) + ".</p>")
    return "\n".join(parts)


def section_summary_table(summary):
    cols = list(summary[0].keys())
    return (
        "<h2>Replay summary (05_results/replay_summary.csv)</h2>\n"
        "<p>wall_seconds: one plain replay of preloaded events on a fresh book, "
        "in seconds; file reading and checks excluded; single run, not the "
        "benchmark. peak_active_orders in orders, peak_price_levels in occupied "
        "(side, price) levels.</p>\n"
        + html_table(cols, [[r[c] for c in cols] for r in summary]))


def section_wall_time(summary):
    fig, ax = plt.subplots(figsize=(9, 3.6))
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


def section_scaling(_summary):
    rows = read_csv_glob("scaling_version_*.csv")
    if not rows:
        return "<h2>Scaling</h2>\n<p>No scaling results saved yet.</p>"
    limit = scaling_time_limit()
    # The limit covers the whole child process (load + replay + counting), so a
    # stopped run has NO replay time: it is listed in text, never plotted.
    stopped_text = (f"stopped: {limit} s limit for load + replay reached; "
                    "replay time not measured" if limit else
                    "stopped: time limit reached; replay time not measured")

    # Small multiples: one panel per scenario, colour = version, shared log axes.
    scenarios = scenarios_in(rows)
    versions = versions_in(rows)
    ncols = 3
    nrows = -(-(len(scenarios) + 1) // ncols)          # +1 panel for the legend
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.2 * nrows),
                             sharex=True, sharey=True, squeeze=False)
    axes = axes.ravel()
    stopped_rows = []
    for ax, scenario in zip(axes, scenarios):
        notes = []
        for version in versions:
            sel = sorted((r for r in rows if r["version"] == version
                          and r["scenario"] == scenario), key=lambda r: int(r["events"]))
            ok = [r for r in sel if r["status"] == "ok"]
            ax.plot([int(r["events"]) for r in ok], [float(r["seconds"]) for r in ok],
                    marker="o", markersize=4, linewidth=2,
                    color=VERSION_COLORS.get(version, "#777777"), label=label(version))
            stopped = [r for r in sel if r["status"] == "stopped"]
            stopped_rows += stopped
            notes += [f"{label(version)}, M = {int(r['events']):,}: stopped"
                      for r in stopped]
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(scenario, loc="left", fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(color="#e5e5e5", linewidth=0.8, which="major")
        ax.set_axisbelow(True)
        if notes:     # text only: a stopped run has no replay time to plot
            ax.text(0.98, 0.04, "\n".join(notes), transform=ax.transAxes,
                    ha="right", va="bottom", fontsize=7, color="#555555")
    for ax in axes[len(scenarios):]:
        ax.axis("off")
    handles, labels_ = axes[0].get_legend_handles_labels()
    axes[len(scenarios)].legend(handles, labels_, loc="center", frameon=False)
    fig.supxlabel("events M (log scale)", fontsize=10)
    fig.supylabel("replay time (seconds, log scale)", fontsize=10)
    fig.suptitle("Engine replay time vs events (single runs, seed 42)",
                 x=0.01, ha="left", fontsize=11)
    fig.tight_layout()
    if stopped_rows:
        items = "\n".join(
            f"<li>{label(r['version'])}, {html.escape(r['scenario'])}, "
            f"M = {int(r['events']):,}: {html.escape(stopped_text)}</li>"
            for r in stopped_rows)
        stopped_html = ("<p>Stopped runs (not in the chart; a line ends at its "
                        f"last measured point):</p>\n<ul>\n{items}\n</ul>")
    else:
        stopped_html = "<p>No run was stopped.</p>"
    return (
        "<h2>Scaling (05_results/scaling_version_*.csv)</h2>\n"
        "<p>Seconds = one replay of preloaded events on a fresh book, engine "
        "only, invariant checks off; data generation and file reading "
        "excluded. Only measured replay times are plotted.</p>\n"
        + figure_to_img(fig, "replay time vs events") + "\n" + stopped_html)


def section_liquidation(_summary):
    rows = read_csv_glob("liquidation_version_*.csv")
    if not rows:
        return "<h2>Large liquidation</h2>\n<p>No liquidation results saved yet.</p>"
    first = rows[0]
    intro = (
        f"<p>Fresh bid book from the first {int(first['book_events']):,} events of "
        f"sweep_10000 ({int(first['bid_orders']):,} bid orders on "
        f"{int(first['bid_price_levels']):,} price levels, "
        f"{btc(first['bid_qty_units'])} BTC of bids). Each sale runs on its own "
        "freshly built book. Single runs, seconds.</p>")
    header = ["version", "sale size (% of bid qty)", "requested (BTC)", "fills",
              "makers touched", "price levels visited", "unfilled (BTC)", "status",
              "build (seconds)", "sell (seconds)"]
    order = {v: i for i, v in enumerate(VERSION_ORDER)}
    rows = sorted(rows, key=lambda r: (order.get(r["version"], 99), int(r["sale_pct"])))
    table = [[label(r["version"]), f"{r['sale_pct']}%",
              btc(r["requested_qty_units"]), r["fills"], r["makers_touched"],
              r["price_levels_visited"], btc(r["unfilled_qty_units"]), r["status"],
              r["build_seconds"], r["sell_seconds"]] for r in rows]
    return ("<h2>Large liquidation (05_results/liquidation_version_*.csv)</h2>\n"
            + intro + "\n" + html_table(header, table))


SECTIONS = [section_correctness, section_summary_table, section_wall_time,
            section_peaks, section_scaling, section_liquidation]


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
table {{ border-collapse: collapse; font-size: 0.9em; margin-bottom: 1em; }}
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
