#!/usr/bin/env python
"""Convert a prepped grayscale photo into a self-typing monochrome ASCII SVG.

Downsamples the image to a character grid, maps brightness to a density
ramp, then wraps each row in a clip-path that wipes left-to-right, staggered
top to bottom, using SMIL animation so GitHub renders it inline.

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
ROW_DURATION = 0.55   # seconds for one row to wipe in
ROW_STAGGER = 0.045   # seconds between successive row starts


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
    width = COLS * CHAR_W
    height = ROWS * CHAR_H
    total_duration = ROW_DURATION + ROW_STAGGER * (ROWS - 1)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.1f} {height:.1f}" '
        f'width="{width:.0f}" height="{height:.0f}" font-family="ui-monospace, SFMono-Regular, '
        f'Consolas, Menlo, monospace" font-size="{FONT_SIZE}">',
        "<defs>",
    ]

    for i, row in enumerate(rows):
        clip_id = f"clip{i}"
        start = i * ROW_STAGGER
        y = i * CHAR_H + FONT_SIZE
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'<rect x="0" y="{i * CHAR_H:.1f}" width="0" height="{CHAR_H:.1f}">'
            f'<animate attributeName="width" from="0" to="{width:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1" />'
            f"</rect>"
        )
        parts.append("</clipPath>")

    parts.append("</defs>")
    parts.append(f'<rect x="0" y="0" width="{width:.1f}" height="{height:.1f}" fill="#0d1117" />')

    for i, row in enumerate(rows):
        y = i * CHAR_H + FONT_SIZE - 1
        text = "".join(escape(c) for c in row)
        parts.append(
            f'<g clip-path="url(#clip{i})">'
            f'<text x="0" y="{y:.1f}" fill="{FILL}" xml:space="preserve">{text}</text>'
            f"</g>"
        )
        # small block cursor riding the wipe edge of each row, disappears when row finishes
        start = i * ROW_STAGGER
        parts.append(
            f'<rect x="0" y="{i * CHAR_H:.1f}" width="{CHAR_W:.1f}" height="{CHAR_H:.1f}" fill="{FILL}" opacity="0">'
            f'<animate attributeName="x" from="0" to="{width - CHAR_W:.1f}" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.25 0.1 0.25 1" />'
            f'<animate attributeName="opacity" values="0.9;0.9;0" keyTimes="0;0.85;1" '
            f'begin="{start:.3f}s" dur="{ROW_DURATION}s" fill="freeze" />'
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
