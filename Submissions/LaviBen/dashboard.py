"""Build a self-contained HTML runtime dashboard from benchmark JSON."""

from __future__ import annotations

import argparse
import html
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


COLORS = ("#2563eb", "#9333ea", "#ea580c", "#059669", "#dc2626")


def _format_ms(value: float) -> str:
    if value < 0.01:
        return f"{value:.6f}"
    if value < 1:
        return f"{value:.4f}"
    return f"{value:.2f}"


def _chart_svg(records: list[dict[str, Any]]) -> str:
    width, height = 1_000, 440
    left, right, top, bottom = 78, 24, 26, 68
    chart_width = width - left - right
    chart_height = height - top - bottom
    sizes = sorted({int(record["array_size"]) for record in records})
    algorithms = list(dict.fromkeys(str(record["algorithm"]) for record in records))
    grouped: dict[str, dict[int, float]] = defaultdict(dict)

    for record in records:
        grouped[str(record["algorithm"])][int(record["array_size"])] = max(
            float(record["median_ms"]),
            1e-9,
        )

    values = [value for series in grouped.values() for value in series.values()]
    log_min = math.log10(min(values))
    log_max = math.log10(max(values))
    if math.isclose(log_min, log_max):
        log_min -= 0.5
        log_max += 0.5

    def x_position(index: int) -> float:
        if len(sizes) == 1:
            return left + chart_width / 2
        return left + index * chart_width / (len(sizes) - 1)

    def y_position(value: float) -> float:
        proportion = (math.log10(value) - log_min) / (log_max - log_min)
        return top + chart_height * (1 - proportion)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Median runtime by input size on a logarithmic scale">'
    ]

    for tick_index in range(6):
        proportion = tick_index / 5
        tick_log = log_min + (log_max - log_min) * proportion
        tick_value = 10**tick_log
        y = top + chart_height * (1 - proportion)
        parts.append(
            f'<line x1="{left}" y1="{y:.2f}" x2="{width - right}" '
            f'y2="{y:.2f}" class="grid" />'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" '
            f'class="axis-label">{html.escape(_format_ms(tick_value))}</text>'
        )

    for index, size in enumerate(sizes):
        x = x_position(index)
        parts.append(
            f'<text x="{x:.2f}" y="{height - 38}" text-anchor="middle" '
            f'class="axis-label">{size:,}</text>'
        )

    for algorithm_index, algorithm in enumerate(algorithms):
        color = COLORS[algorithm_index % len(COLORS)]
        points = [
            (x_position(index), y_position(grouped[algorithm][size]))
            for index, size in enumerate(sizes)
            if size in grouped[algorithm]
        ]
        point_text = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        parts.append(
            f'<polyline points="{point_text}" fill="none" stroke="{color}" '
            'stroke-width="3" stroke-linejoin="round" />'
        )
        for x, y in points:
            parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="{color}" />')

    parts.extend(
        (
            f'<text x="{left + chart_width / 2:.2f}" y="{height - 8}" '
            'text-anchor="middle" class="axis-title">Array size</text>',
            f'<text x="18" y="{top + chart_height / 2:.2f}" '
            'text-anchor="middle" class="axis-title" '
            f'transform="rotate(-90 18 {top + chart_height / 2:.2f})">'
            'Median runtime (ms, log scale)</text>',
            "</svg>",
        )
    )
    return "".join(parts)


def build_dashboard(results_path: Path, output_path: Path) -> Path:
    """Read benchmark JSON and write a portable HTML dashboard."""

    payload = json.loads(results_path.read_text(encoding="utf-8"))
    records = payload.get("results", [])
    if not records:
        raise ValueError("benchmark JSON contains no results")

    largest_size = max(int(record["array_size"]) for record in records)
    largest_records = [
        record for record in records if int(record["array_size"]) == largest_size
    ]
    fastest = min(largest_records, key=lambda record: float(record["median_ms"]))
    slowest = max(largest_records, key=lambda record: float(record["median_ms"]))
    speedup = float(slowest["median_ms"]) / max(float(fastest["median_ms"]), 1e-9)
    metadata = payload.get("metadata", {})

    algorithms = list(dict.fromkeys(str(record["algorithm"]) for record in records))
    legend_items = "".join(
        f'<span><i style="background:{COLORS[index % len(COLORS)]}"></i>'
        f'{html.escape(algorithm)}</span>'
        for index, algorithm in enumerate(algorithms)
    )
    table_rows = "".join(
        "<tr>"
        f'<td>{int(record["array_size"]):,}</td>'
        f'<td>{int(record["query_count"]):,}</td>'
        f'<td>{html.escape(str(record["algorithm"]))}</td>'
        f'<td>{_format_ms(float(record["median_ms"]))}</td>'
        f'<td>{_format_ms(float(record["minimum_ms"]))}</td>'
        f'<td>{_format_ms(float(record["maximum_ms"]))}</td>'
        "</tr>"
        for record in sorted(
            records,
            key=lambda row: (int(row["array_size"]), str(row["algorithm"])),
        )
    )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LaviBen search runtime dashboard</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#64748b; --panel:#fff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#f1f5f9; color:var(--ink); font:15px/1.5 system-ui,sans-serif; }}
    main {{ width:min(1180px,calc(100% - 32px)); margin:32px auto 56px; }}
    h1 {{ margin:0; font-size:clamp(28px,4vw,44px); letter-spacing:-.03em; }}
    .subtitle {{ margin:6px 0 24px; color:var(--muted); }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:14px; }}
    .card,.panel {{
      background:var(--panel); border:1px solid #dbe3ee; border-radius:16px;
      box-shadow:0 8px 24px #0f172a0d;
    }}
    .card {{ padding:18px; }} .card b {{ display:block; font-size:24px; margin-top:4px; }}
    .label {{
      color:var(--muted); font-size:12px; text-transform:uppercase;
      letter-spacing:.08em;
    }}
    .panel {{ margin-top:18px; padding:20px; overflow:auto; }}
    h2 {{ margin:0 0 12px; font-size:20px; }}
    svg {{ display:block; width:100%; min-width:720px; }}
    .grid {{ stroke:#dbe3ee; stroke-width:1; }} .axis-label {{ fill:#64748b; font-size:12px; }}
    .axis-title {{ fill:#334155; font-size:13px; font-weight:600; }}
    .legend {{ display:flex; flex-wrap:wrap; gap:12px 20px; color:#334155; }}
    .legend span {{ display:flex; align-items:center; gap:7px; }}
    .legend i {{ width:11px; height:11px; border-radius:50%; }}
    table {{ width:100%; border-collapse:collapse; white-space:nowrap; }}
    th,td {{ padding:10px 12px; border-bottom:1px solid #e2e8f0; text-align:right; }}
    th {{ color:#475569; font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
    th:nth-child(3),td:nth-child(3) {{ text-align:left; }}
    .note {{ color:var(--muted); font-size:13px; margin:10px 0 0; }}
  </style>
</head>
<body><main>
  <h1>Search runtime dashboard</h1>
  <p class="subtitle">
    LaviBen · deterministic synthetic data · median of repeated measurements
  </p>
  <section class="cards">
    <div class="card"><span class="label">Largest array</span><b>{largest_size:,}</b></div>
    <div class="card"><span class="label">Fastest at largest size</span>
      <b>{html.escape(str(fastest["algorithm"]))}</b></div>
    <div class="card"><span class="label">Fastest median</span>
      <b>{_format_ms(float(fastest["median_ms"]))} ms</b></div>
    <div class="card"><span class="label">Range at largest size</span><b>{speedup:,.1f}×</b></div>
  </section>
  <section class="panel"><h2>Scaling comparison</h2><div class="legend">{legend_items}</div>
    {_chart_svg(records)}
    <p class="note">Data generation is excluded. Sorting, set construction,
      and result-list construction are included in each call. Seed:
      {metadata.get("seed", "n/a")}; hit rate:
      {metadata.get("hit_rate", "n/a")}.</p>
  </section>
  <section class="panel"><h2>Measurements</h2><table><thead><tr>
    <th>Array size</th><th>Queries</th><th>Algorithm</th>
    <th>Median ms</th><th>Min ms</th><th>Max ms</th>
  </tr></thead><tbody>{table_rows}</tbody></table></section>
</main></body></html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/benchmark_results.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runtime_dashboard.html"),
    )
    arguments = parser.parse_args()
    output_path = build_dashboard(arguments.input, arguments.output)
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
