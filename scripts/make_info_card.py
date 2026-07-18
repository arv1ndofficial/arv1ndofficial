#!/usr/bin/env python
"""Hand-authored neofetch-style info card SVG.

Renders a title bar plus key/value rows that fade + slide in on a short
stagger. Set STATIC=1 to emit a frozen (no-animation) frame, useful for
local Quick Look previews.

Usage: python make_info_card.py [out.svg]
"""
import os
import sys

WIDTH = 490
LINE_H = 30
PAD_TOP = 56
PAD_X = 24
STAGGER = 0.12
DUR = 0.4

TITLE = "arv1ndofficial@github"
FIELDS = [
    ("Now", "Sr. Data Engineer @ M2P Fintech"),
    ("Prev", "Data Engineer @ TCS (2021-2025)"),
    ("Stack", "Spark, Iceberg, Trino, Airflow, K8s"),
    ("Highlights", "Led 5-eng team; MCP agentic data lake"),
]

STATIC = os.environ.get("STATIC") == "1"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg() -> str:
    height = PAD_TOP + LINE_H * len(FIELDS) + 24
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" '
        f'width="{WIDTH}" height="{height}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, Menlo, monospace" font-size="14">',
        f'<rect x="0" y="0" width="{WIDTH}" height="{height}" rx="8" fill="#0d1117" '
        f'stroke="#30363d" />',
        # title bar
        '<circle cx="20" cy="20" r="6" fill="#ff5f56" />',
        '<circle cx="40" cy="20" r="6" fill="#ffbd2e" />',
        '<circle cx="60" cy="20" r="6" fill="#27c93f" />',
        f'<text x="{PAD_X}" y="{PAD_TOP - 20}" fill="#8b949e" font-size="13">{esc(TITLE)}</text>',
        f'<line x1="{PAD_X}" y1="{PAD_TOP - 8}" x2="{WIDTH - PAD_X}" y2="{PAD_TOP - 8}" '
        f'stroke="#30363d" />',
    ]

    for i, (key, value) in enumerate(FIELDS):
        y = PAD_TOP + i * LINE_H + 18
        if STATIC:
            parts.append("<g>")
        else:
            start = i * STAGGER
            parts.append('<g opacity="0" transform="translate(-8,0)">')
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" begin="{start:.2f}s" '
                f'dur="{DUR}s" fill="freeze" />'
            )
            parts.append(
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-8,0" to="0,0" begin="{start:.2f}s" dur="{DUR}s" fill="freeze" />'
            )
        parts.append(f'<text x="{PAD_X}" y="{y}" fill="#39d353">{esc(key)}</text>')
        parts.append(
            f'<text x="{PAD_X + 110}" y="{y}" fill="#c9d1d9">{esc(value)}</text>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "info-card.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_svg())
    print(f"wrote {out}{' (static)' if STATIC else ''}")
