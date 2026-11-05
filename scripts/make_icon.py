#!/usr/bin/env python3
"""Draw assets/design-to-dev-icon.png (512x512 PNG), the plugin directory listing icon.

A phone-sized prototype frame on warm paper: one design token row (three swatches) above
a primary button, in the refined minimal direction the skill defaults to. Needs Pillow;
run only when the icon changes: python3 scripts/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE, SCALE = 512, 4
S = SIZE * SCALE
OUT = Path(__file__).resolve().parent.parent / "assets" / "design-to-dev-icon.png"
PAPER, INK, LINE = (251, 247, 240), (31, 42, 46), (229, 220, 203)
MOSS, AMBER, CLAY = (62, 124, 89), (227, 162, 59), (166, 94, 64)


def px(v: float) -> int:
    return int(v * SCALE)


img = Image.new("RGB", (S, S), PAPER)
d = ImageDraw.Draw(img)
# phone frame
d.rounded_rectangle([px(148), px(72), px(364), px(440)], radius=px(36), fill=(255, 253, 249), outline=INK, width=px(10))
# title bar and two text lines
d.rounded_rectangle([px(184), px(128), px(300), px(146)], radius=px(9), fill=INK)
d.rounded_rectangle([px(184), px(170), px(328), px(182)], radius=px(6), fill=LINE)
d.rounded_rectangle([px(184), px(196), px(276), px(208)], radius=px(6), fill=LINE)
# token swatches
for i, color in enumerate((MOSS, AMBER, CLAY)):
    cx = 202 + i * 54
    d.ellipse([px(cx - 18), px(244), px(cx + 18), px(280)], fill=color)
# primary button
d.rounded_rectangle([px(184), px(352), px(328), px(392)], radius=px(12), fill=MOSS)
img.resize((SIZE, SIZE), Image.LANCZOS).save(OUT, optimize=True)
print(f"wrote {OUT.relative_to(OUT.parent.parent)} ({OUT.stat().st_size // 1024} KB)")
