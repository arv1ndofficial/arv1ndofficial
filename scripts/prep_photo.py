#!/usr/bin/env python
"""Prep a source photo for ASCII conversion.

Removes the background, boosts local contrast (CLAHE), and composites
onto pure white so the background maps to the blank end of the ASCII
ramp. Run once per photo; output feeds make_ascii_svg.py.

Usage: python prep_photo.py <source-photo.jpg> [output.png]
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep_photo(src_path: str, out_path: str = "source-prepped.png") -> None:
    src_bytes = Path(src_path).read_bytes()

    # 1. Remove background -> RGBA with subject isolated on transparency.
    cutout_bytes = remove(src_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white so background -> blank glyph later.
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Boost local contrast with CLAHE on the luminance channel.
    bgr = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge((l_channel, a_channel, b_channel))
    contrast_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    gray = cv2.cvtColor(contrast_bgr, cv2.COLOR_BGR2GRAY)
    Image.fromarray(gray).save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python prep_photo.py <source-photo.jpg> [output.png]")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(sys.argv[1], out)
