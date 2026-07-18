#!/usr/bin/env python
"""Hand-authored neofetch-style info card SVG.

Wrapped in the same terminal-window chrome as the ASCII portrait (traffic-
light dots + title bar). Parodies real neofetch output — OS/Host/Uptime/
Shell/etc. field names repurposed with actual resume data — followed by the
classic ANSI color-swatch strip and a blinking ready-prompt cursor. Rows
fade + rise into place on a short stagger. Set STATIC=1 to emit a frozen
(no-animation) frame, useful for local Quick Look previews.

Usage: python make_info_card.py [out.svg]
"""
import os
import sys

WIDTH = 490
LINE_H = 22
PAD_X = 20
KEY_W = 80
TITLE_BAR_H = 30
HEADER_Y = 60
DIVIDER_Y = 68
FIELDS_TOP = 90
SWATCH = 16
SWATCH_GAP = 6
STAGGER = 0.05
DUR = 0.4
EASE = "0.2 0.8 0.2 1"

TITLE = "arv1ndofficial@github: ~$ neofetch"
USER = "arv1ndofficial"
HOST = "github"
FIELDS = [
    ("OS", "Senior Data & AI Engineer"),
    ("Host", "M2P Fintech (prev: TCS)"),
    ("Uptime", "5+ years"),
    ("Shell", "Python, SQL, Scala"),
    ("Stack", "Spark, Iceberg, Trino, Airflow"),
    ("Cloud", "AWS, Kubernetes, Databricks"),
    ("AI/ML", "RAG, MCP, ChromaDB, LLMs"),
    ("Location", "Chennai, India"),
]
SWATCH_COLORS = [
    "#21262d", "#f85149", "#3fb950", "#d29922",
    "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9",
]

STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def reveal_open(delay: float, dy: int = 5) -> str:
    if STATIC:
        return "<g>"
    return (
        f'<g opacity="0" transform="translate(0,{dy})">'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" '
        f'dur="{DUR}s" fill="freeze" />'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="0 {dy}" to="0 0" begin="{delay:.2f}s" dur="{DUR}s" fill="freeze" '
        f'calcMode="spline" keySplines="{EASE}" />'
    )


def build_svg() -> str:
    swatch_y = FIELDS_TOP + LINE_H * len(FIELDS) + 10
    prompt_y = swatch_y + SWATCH + 28
    height = prompt_y + 14

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, Menlo, monospace">',
        "<defs>",
        '<linearGradient id="ibg" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0" stop-color="#111722" />',
        '<stop offset="1" stop-color="#0d1117" />',
        "</linearGradient>",
        "</defs>",
        f'<rect width="{WIDTH}" height="{height}" rx="12" fill="url(#ibg)" />',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" '
        f'fill="none" stroke="#30363d" />',
        f'<line x1="0" y1="{TITLE_BAR_H}" x2="{WIDTH}" y2="{TITLE_BAR_H}" stroke="#30363d" />',
        '<circle cx="20" cy="15" r="5" fill="#ff5f56" />',
        '<circle cx="36" cy="15" r="5" fill="#ffbd2e" />',
        '<circle cx="52" cy="15" r="5" fill="#27c93f" />',
        f'<text x="{WIDTH / 2}" y="19" fill="#7d8590" font-size="12" '
        f'text-anchor="middle">{esc(TITLE)}</text>',
    ]

    # header: colored user@host + divider
    parts.append(reveal_open(0.08))
    parts.append(
        f'<text x="{PAD_X}" y="{HEADER_Y}" font-size="15" font-weight="700">'
        f'<tspan fill="#3fb950">{esc(USER)}</tspan>'
        f'<tspan fill="#7d8590">@</tspan>'
        f'<tspan fill="#22d3ee">{esc(HOST)}</tspan>'
        f"</text>"
    )
    parts.append(
        f'<line x1="{PAD_X}" y1="{DIVIDER_Y}" x2="{WIDTH - PAD_X}" y2="{DIVIDER_Y}" '
        f'stroke="#30363d" stroke-opacity="0.8" />'
    )
    parts.append("</g>")

    for i, (key, value) in enumerate(FIELDS):
        y = FIELDS_TOP + i * LINE_H
        delay = 0.14 + i * STAGGER
        parts.append(reveal_open(delay))
        parts.append(
            f'<text x="{PAD_X}" y="{y}" fill="#ffa657" font-size="12.5" font-weight="700">{esc(key)}</text>'
        )
        parts.append(
            f'<text x="{PAD_X + KEY_W}" y="{y}" fill="#c9d1d9" font-size="12.5">{esc(value)}</text>'
        )
        parts.append("</g>")

    # classic neofetch ANSI color-swatch strip
    swatch_delay = 0.14 + len(FIELDS) * STAGGER + 0.05
    parts.append(reveal_open(swatch_delay, dy=4))
    sx = PAD_X
    for color in SWATCH_COLORS:
        parts.append(f'<rect x="{sx}" y="{swatch_y}" width="{SWATCH}" height="{SWATCH}" rx="3" fill="{color}" />')
        sx += SWATCH + SWATCH_GAP
    parts.append("</g>")

    # blinking ready-prompt cursor
    parts.append(
        f'<text x="{PAD_X}" y="{prompt_y}" font-size="13">'
        f'<tspan fill="#3fb950">{esc(USER)}</tspan>'
        f'<tspan fill="#7d8590">@</tspan>'
        f'<tspan fill="#22d3ee">{esc(HOST)}</tspan>'
        f'<tspan fill="#7d8590">:~$</tspan>'
        f"</text>"
    )
    cursor_x = PAD_X + 9.2 * (len(USER) + len(HOST) + 4)
    if STATIC:
        parts.append(f'<rect x="{cursor_x:.1f}" y="{prompt_y - 11}" width="7" height="13" fill="#c9d1d9" />')
    else:
        # opacity="0" is the underlying value held until the animation's own
        # begin time, so the cursor stays hidden until the prompt line is reached.
        parts.append(
            f'<rect x="{cursor_x:.1f}" y="{prompt_y - 11}" width="7" height="13" fill="#c9d1d9" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" dur="1s" '
            f'begin="{swatch_delay + 0.35:.2f}s" repeatCount="indefinite" />'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg())
    print(f"wrote {out}{' (static)' if STATIC else ''}")
