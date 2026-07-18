#!/usr/bin/env python
"""Render data/contributions.json as an animated 53-week x 7-day heatmap SVG.

Boxes pop in with a brief brightness flash, staggered diagonally by week and
day-of-week, using CSS keyframes that play once on load (with a
prefers-reduced-motion fallback). Month labels run along the top, Mon/Wed/Fri
labels down the left, plus a Less->More legend and a real stats footer.

Usage: python render_heatmap_svg.py [data/contributions.json] [out.svg]
"""
import json
import sys
from datetime import datetime, timedelta

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BOX = 11
GAP = 3
CELL = BOX + GAP
LEFT_PAD = 28
TOP_PAD = 20
WEEKS = 53
DAYS = 7
STAGGER = 0.012
DUR = 0.55

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}  # grid row index -> label (row 0 = Sun)


def load_data(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def level_to_color(level: int) -> str:
    idx = max(0, min(level, len(PALETTE) - 1))
    return PALETTE[idx]


def build_svg(data: dict) -> str:
    days = data["days"]
    stats = data.get("stats", {})

    by_date = {d["date"]: d for d in days}
    if days:
        last_date = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()
    else:
        last_date = datetime.utcnow().date()

    grid_end = last_date
    # Walk back to the most recent Sunday (grid column start), then WEEKS-1 more weeks back.
    sunday_offset = (grid_end.weekday() + 1) % 7  # Mon=0..Sun=6 -> Sun=0..Sat=6
    grid_start = grid_end - timedelta(days=sunday_offset + 7 * (WEEKS - 1))

    width = LEFT_PAD + WEEKS * CELL + 20
    height = TOP_PAD + DAYS * CELL + 60

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, Menlo, monospace" font-size="11">',
        "<style>",
        "  .box { transform-box: fill-box; transform-origin: center; opacity: 0; "
        "animation: pop 0.55s ease-out both, flash 0.7s ease-out both; }",
        "  @keyframes pop { 0% { opacity: 0; transform: scale(0.2); } "
        "60% { opacity: 1; transform: scale(1.1); } 100% { opacity: 1; transform: scale(1); } }",
        "  @keyframes flash { 0% { filter: brightness(2.4); } 45% { filter: brightness(2.4); } "
        "100% { filter: brightness(1); } }",
        "  @media (prefers-reduced-motion: reduce) { .box { opacity: 1 !important; animation: none !important; } }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#0d1117" />',
    ]

    last_month = None
    for w in range(WEEKS):
        for d in range(DAYS):
            cell_date = grid_start + timedelta(days=w * 7 + d)
            date_str = cell_date.isoformat()
            entry = by_date.get(date_str)
            level = entry["level"] if entry else 0
            count = entry["count"] if entry else 0
            x = LEFT_PAD + w * CELL
            y = TOP_PAD + d * CELL
            delay = (w + d) * STAGGER

            if d == 0 and cell_date.day <= 7 and cell_date.month != last_month:
                last_month = cell_date.month
                parts.append(
                    f'<text x="{x}" y="{TOP_PAD - 6}" fill="#7d8590" font-weight="600">'
                    f"{MONTH_NAMES[cell_date.month - 1]}</text>"
                )
            if w == 0 and d in DOW_LABELS:
                parts.append(
                    f'<text x="0" y="{y + BOX - 1}" fill="#7d8590" font-weight="600">'
                    f"{DOW_LABELS[d]}</text>"
                )

            if cell_date <= grid_end:
                parts.append(
                    f'<rect class="box" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2.5" '
                    f'fill="{level_to_color(level)}" style="animation-delay:{delay:.3f}s">'
                    f"<title>{count} contribution{'s' if count != 1 else ''} on {date_str}</title></rect>"
                )

    # Legend
    legend_y = TOP_PAD + DAYS * CELL + 24
    legend_x = LEFT_PAD
    parts.append(f'<text x="{legend_x}" y="{legend_y + 9}" fill="#7d8590">Less</text>')
    lx = legend_x + 34
    for level, color in enumerate(PALETTE):
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="2.5" fill="{color}" />')
        lx += CELL
    parts.append(f'<text x="{lx + 4}" y="{legend_y + 9}" fill="#7d8590">More</text>')

    # Stats footer
    total = stats.get("total_contributions", sum(d.get("count", 0) for d in days))
    streak = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    footer_y = legend_y + 24
    parts.append(
        f'<text x="{legend_x}" y="{footer_y}" fill="#e6edf3" font-weight="700">{total}</text>'
    )
    parts.append(
        f'<text x="{legend_x + len(str(total)) * 7 + 6}" y="{footer_y}" fill="#7d8590">'
        f"contributions in the last year  &#183;  streak {streak}  &#183;  longest {longest}</text>"
    )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/contributions.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "contrib-heatmap.svg"
    data = load_data(src)
    svg = build_svg(data)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out}")
