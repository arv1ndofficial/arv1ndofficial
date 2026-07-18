#!/usr/bin/env python
"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a density
ramp, then wraps each row in a clip-path that wipes left-to-right, staggered
top to bottom, using SMIL animation so GitHub renders it inline. The whole
grid sits inside a terminal-window frame (traffic-light dots + title bar)
to match the reveal happening "inside a shell".

Usage: python make_ascii_svg.py [source-prepped.png] [out.svg]
"""
import sys

from PIL import Image

RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense); leading space = blank
COLS = 100
ROWS = 53
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 11
FILL = "#c9d1d9"  # single light-gray fill; no per-char color
ROW_DURATION = 0.16   # seconds for one row to wipe in
ROW_STAGGER = 0.045   # seconds between successive row starts
TITLE = "arv1ndofficial@github: ~$ ./portrait.sh"

PAD_X = 20
PAD_TOP = 44   # title bar (30) + inner gap
PAD_BOTTOM = 18
TITLE_BAR_H = 30


def brightness_to_char(v: float) -> str:
    idx = int((1 - v / 255) * (len(RAMP) - 1))
    return RAMP[max(0, min(len(RAMP) - 1, idx))]


def image_to_rows(path: str, cols: int, rows: int) -> list[str]:
    img = Image.open(path).convert("L").resize((cols, rows), Image.LANCZOS)
    pixels = img.load()
    out = []
    for y in range(rows):
        line = "".join(brightness_to_char(pixels[x, y]) for x in range(cols))
        out.append(line)
    return out


def escape(c: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(c, c)


def build_svg(rows: list[str]) -> str:
    grid_w = COLS * CHAR_W
    grid_h = ROWS * CHAR_H
    width = grid_w + PAD_X * 2
    height = grid_h + PAD_TOP + PAD_BOTTOM

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, Menlo, monospace">',
        "<defs>",
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0" stop-color="#111722" />',
        '<stop offset="1" stop-color="#0d1117" />',
        "</linearGradient>",
    ]

    for i, row in enumerate(rows):
        clip_id = f"clip{i}"
        start = i * ROW_STAGGER
        y = PAD_TOP + i * CHAR_H
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="{PAD_X}" y="{y:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{grid_w:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1" />'
            f"</rect>"
        )
        parts.append("</clipPath>")

    parts.append("</defs>")

    # terminal window chrome
    parts.append(f'<rect width="{width:.1f}" height="{height:.1f}" rx="12" fill="url(#bg)" />')
    parts.append(
        f'<rect x="0.5" y="0.5" width="{width - 1:.1f}" height="{height - 1:.1f}" rx="12" '
        f'fill="none" stroke="#30363d" />'
    )
    parts.append(f'<line x1="0" y1="{TITLE_BAR_H}" x2="{width:.1f}" y2="{TITLE_BAR_H}" stroke="#30363d" />')
    parts.append('<circle cx="20" cy="15" r="5" fill="#ff5f56" />')
    parts.append('<circle cx="36" cy="15" r="5" fill="#ffbd2e" />')
    parts.append('<circle cx="52" cy="15" r="5" fill="#27c93f" />')
    parts.append(
        f'<text x="{width / 2:.1f}" y="19" fill="#7d8590" font-size="12" '
        f'text-anchor="middle">{escape(TITLE)}</text>'
    )

    for i, row in enumerate(rows):
        y = PAD_TOP + i * CHAR_H + FONT_SIZE - 1
        text = "".join(escape(c) for c in row)
        parts.append(
            f'<g clip-path="url(#clip{i})">'
            f'<text xml:space="preserve" x="{PAD_X}" y="{y:.1f}" fill="{FILL}" font-size="{FONT_SIZE}" '
            f'textLength="{grid_w:.1f}" lengthAdjust="spacing">{text}</text>'
            f"</g>"
        )
        # small block cursor riding the wipe edge of each row, disappears when row finishes
        start = i * ROW_STAGGER
        parts.append(
            f'<rect y="{PAD_TOP + i * CHAR_H:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" '
            f'fill="{FILL}" opacity="0">'
            f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + grid_w - CHAR_W:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1" />'
            f'<set attributeName="opacity" to="0.85" begin="{start:.3f}s" />'
            f'<set attributeName="opacity" to="0" begin="{start + ROW_DURATION:.3f}s" />'
            f"</rect>"
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "avi-ascii.svg"
    rows = image_to_rows(src, COLS, ROWS)
    svg = build_svg(rows)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out} ({COLS}x{ROWS} chars)")
