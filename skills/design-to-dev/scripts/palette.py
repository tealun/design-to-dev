#!/usr/bin/env python3
"""Read exact colors and scale from a PNG screenshot, and compute WCAG contrast.

Usage:
    python3 palette.py shot.png                    # size, likely scale, top 16 colors with share and a sample point
    python3 palette.py shot.png --top 24           # more colors
    python3 palette.py shot.png --at 200,700 36,412  # colors at image pixel coordinates
    python3 palette.py --contrast "#ffffff" "#1f883d"  # contrast ratio and WCAG AA result

PNG only (8-bit RGB, RGBA, gray, gray+alpha or palette; not interlaced). For JPEG or other formats,
export a PNG or estimate visually and mark values Indicative. Python 3 standard library only.
"""
from __future__ import annotations

import struct
import sys
import zlib
from collections import Counter
from pathlib import Path

DEVICE_WIDTHS = [(360, "Android phone"), (375, "iPhone"), (390, "iPhone"), (393, "iPhone Pro"), (402, "iPhone Pro"),
                 (414, "iPhone Plus"), (430, "iPhone Pro Max"), (768, "tablet"), (1280, "laptop"), (1440, "desktop"), (1920, "desktop")]


def decode_png(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG file; export PNG or estimate colors visually")
    pos, idat, palette = 8, b"", None
    width = height = depth = ctype = interlace = 0
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"PLTE":
            palette = [tuple(chunk[i:i + 3]) for i in range(0, len(chunk), 3)]
        elif kind == b"IDAT":
            idat += chunk
        elif kind == b"IEND":
            break
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if depth != 8 or interlace or channels is None:
        raise SystemExit(f"{path}: unsupported PNG (bit depth {depth}, color type {ctype}, interlace {interlace})")
    raw = zlib.decompress(idat)
    stride = width * channels
    prev = bytearray(stride)
    pixels: list[tuple[int, int, int]] = []
    i = 0
    for _ in range(height):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ftype == 1:
            for x in range(channels, stride):
                line[x] = (line[x] + line[x - channels]) & 0xFF
        elif ftype == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 0xFF
        elif ftype == 3:
            for x in range(stride):
                left = line[x - channels] if x >= channels else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 0xFF
        elif ftype == 4:
            for x in range(stride):
                a = line[x - channels] if x >= channels else 0
                b = prev[x]
                c = prev[x - channels] if x >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        prev = line
        for x in range(0, stride, channels):
            if ctype == 2 or ctype == 6:
                rgb = (line[x], line[x + 1], line[x + 2])
            elif ctype == 3:
                rgb = palette[line[x]]
            else:
                rgb = (line[x],) * 3
            if ctype in (4, 6) and line[x + channels - 1] < 128:
                rgb = (255, 255, 255)  # treat mostly transparent pixels as a white canvas
            pixels.append(rgb)
    return width, height, pixels


def hexcolor(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def luminance(color: str) -> float:
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    channels = [int(color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def scale_hint(width: int) -> str:
    hints = []
    for factor in (1, 2, 3):
        for device, label in DEVICE_WIDTHS:
            if abs(width / factor - device) <= 1:
                hints.append(f"{factor}x of {device}pt ({label})")
    return "; ".join(hints) or "unknown; ask the designer for the frame width"


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--contrast":
        ratio = contrast(argv[1], argv[2])
        verdict = "AA pass" if ratio >= 4.5 else "AA pass for large text only" if ratio >= 3 else "AA fail"
        print(f"{argv[1]} on {argv[2]}: {ratio:.2f}:1 ({verdict})")
        return 0
    path = Path(argv[0])
    width, height, pixels = decode_png(path)
    print(f"{path.name}: {width}x{height} px; likely scale: {scale_hint(width)}")
    if "--at" in argv:
        for point in argv[argv.index("--at") + 1:]:
            x, y = (int(v) for v in point.split(","))
            if not (0 <= x < width and 0 <= y < height):
                print(f"  ({x},{y}) outside the {width}x{height} image")
                continue
            print(f"  ({x},{y}) {hexcolor(pixels[y * width + x])}")
        return 0
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 16
    counts = Counter(pixels)
    first: dict[tuple[int, int, int], int] = {}
    for index, rgb in enumerate(pixels):
        if rgb not in first:
            first[rgb] = index
    total = len(pixels)
    print("  color    share   first seen at (x,y px)")
    for rgb, n in counts.most_common(top):
        idx = first[rgb]
        print(f"  {hexcolor(rgb)}  {n * 100 / total:5.2f}%  ({idx % width},{idx // width})")
    print("Colors under ~0.05% are usually anti-aliasing; sample a point with --at to confirm a specific element.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
