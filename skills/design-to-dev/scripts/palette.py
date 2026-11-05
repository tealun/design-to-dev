#!/usr/bin/env python3
"""Read exact colors and scale from a PNG screenshot, and compute WCAG contrast.

Usage:
    python3 palette.py shot.png                    # size, likely scale, top 16 colors with share and a sample point
    python3 palette.py shot.png --top 24           # more colors
    python3 palette.py shot.png --at 200,700 36,412  # colors at image pixel coordinates
    python3 palette.py --contrast "#ffffff" "#1f883d"  # contrast ratio and WCAG AA result
    python3 palette.py --contrast "#ffffff" "#2f6f4f66" --over "#fbf7f0"   # translucent color on its backdrop
    python3 palette.py shot.png --cols 120-150       # horizontal position and width of each block in that y range
    python3 palette.py --contrast "#ffffff" "#6d78d5" --fix   # also print the nearest shade of the background that passes AA
    python3 palette.py shot.png --rows 560-880       # vertical position and height of each block in that x range,
                                                     # in 1x points: compare the source design with the prototype

PNG only (8-bit RGB, RGBA, gray, gray+alpha or palette; not interlaced). For JPEG or other formats,
export a PNG or estimate visually and mark values Indicative. Python 3 standard library only.
"""
from __future__ import annotations

import re
import struct
import sys
import zlib
from collections import Counter
from pathlib import Path

DEVICE_WIDTHS = [(360, "Android phone"), (375, "iPhone"), (390, "iPhone"), (393, "iPhone Pro"), (402, "iPhone Pro"),
                 (414, "iPhone Plus"), (430, "iPhone Pro Max"), (768, "tablet"), (1280, "laptop"), (1440, "desktop"), (1920, "desktop")]


class Image:
    """Decoded PNG kept as one RGB bytes object per row (about 3 bytes per pixel, not a tuple per pixel)."""

    def __init__(self, width: int, height: int, rows: list[bytes]) -> None:
        self.width, self.height, self.rows = width, height, rows

    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        row = self.rows[y]
        return row[3 * x], row[3 * x + 1], row[3 * x + 2]

    def row_pixels(self, y: int):
        row = self.rows[y]
        return zip(row[0::3], row[1::3], row[2::3])

    def counts(self) -> Counter:
        total: Counter = Counter()
        for y in range(self.height):
            total.update(self.row_pixels(y))
        return total


def decode_png(path: Path) -> Image:
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
    rows: list[bytes] = []
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
        if ctype == 2:
            rows.append(bytes(line))
            continue
        rgb = bytearray(width * 3)
        for px, x in enumerate(range(0, stride, channels)):
            if ctype == 6:
                value = (line[x], line[x + 1], line[x + 2])
            elif ctype == 3:
                value = palette[line[x]]
            else:
                value = (line[x],) * 3
            if ctype in (4, 6) and line[x + channels - 1] < 128:
                value = (255, 255, 255)  # treat mostly transparent pixels as a white canvas
            rgb[3 * px:3 * px + 3] = bytes(value)
        rows.append(bytes(rgb))
    return Image(width, height, rows)


def hexcolor(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


class UsageError(Exception):
    pass


def parse_color(color: str) -> tuple[tuple[float, float, float], float]:
    """'#rgb', '#rgba', '#rrggbb' or '#rrggbbaa' -> ((r, g, b) in 0..255, alpha 0..1)."""
    value = color.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8}", value):
        raise UsageError(f"'{color}' is not a hex color; use #rrggbb (named colors are not supported)")
    if len(value) in (3, 4):
        value = "".join(ch * 2 for ch in value)
    rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    alpha = int(value[6:8], 16) / 255 if len(value) == 8 else 1.0
    return rgb, alpha


def composite(color: str, backdrop: str | None) -> str:
    """Flatten a translucent color onto its backdrop; contrast is only defined for opaque colors."""
    rgb, alpha = parse_color(color)
    if alpha >= 1:
        return "#%02x%02x%02x" % rgb
    if not backdrop:
        raise UsageError(f"'{color}' is translucent; pass the color it sits on with --over #rrggbb")
    under, under_alpha = parse_color(backdrop)
    if under_alpha < 1:
        raise UsageError("--over must be an opaque color")
    return "#%02x%02x%02x" % tuple(round(c * alpha + u * (1 - alpha)) for c, u in zip(rgb, under))


def luminance(color: str) -> float:
    rgb, _ = parse_color(color)
    channels = [c / 255 for c in rgb]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted([luminance(a), luminance(b)], reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def scale_factor(width: int) -> int:
    for factor in (3, 2):
        if any(abs(width / factor - device) <= 1 for device, _ in DEVICE_WIDTHS):
            return factor
    return 1


def print_rows(image: Image, span: str) -> None:
    """Blocks of rows whose pixels differ from the background inside x range span ('x0-x1', image pixels)."""
    m = re.fullmatch(r"(\d+)-(\d+)", span or "")
    if not m or int(m.group(1)) >= int(m.group(2)):
        raise UsageError(f"--rows needs an x range in image pixels such as 560-880, got '{span}'")
    width, height = image.width, image.height
    x0, x1 = max(0, int(m.group(1))), min(width, int(m.group(2)))
    background = image.counts().most_common(1)[0][0]
    factor = scale_factor(width)

    def differs(rgb: tuple[int, int, int]) -> bool:
        return sum(abs(a - b) for a, b in zip(rgb, background)) > 12  # white surfaces on #fafafa still count

    print(f"  blocks in x {x0}-{x1} px, background {hexcolor(background)}, shown at 1x (scale {factor}x): top, height")
    start = None
    for y in range(height + 1):
        hit = y < height and any(differs(image.pixel(x, y)) for x in range(x0, x1, 2))
        if hit and start is None:
            start = y
        elif not hit and start is not None:
            print(f"  {start / factor:7.1f}  {(y - start) / factor:6.1f}")
            start = None


def print_cols(image: Image, span: str) -> None:
    """Blocks of columns whose pixels differ from the background inside y range span ('y0-y1', image pixels)."""
    m = re.fullmatch(r"(\d+)-(\d+)", span or "")
    if not m or int(m.group(1)) >= int(m.group(2)):
        raise UsageError(f"--cols needs a y range in image pixels such as 120-150, got '{span}'")
    width, height = image.width, image.height
    y0, y1 = max(0, int(m.group(1))), min(height, int(m.group(2)))
    background = image.counts().most_common(1)[0][0]
    factor = scale_factor(width)
    rows = [list(image.row_pixels(y)) for y in range(y0, y1, 2)]

    def hit(x: int) -> bool:
        return any(sum(abs(a - b) for a, b in zip(row[x], background)) > 12 for row in rows)

    print(f"  blocks in y {y0}-{y1} px, background {hexcolor(background)}, shown at 1x (scale {factor}x): left, width")
    start = None
    for x in range(width + 1):
        on = x < width and hit(x)
        if on and start is None:
            start = x
        elif not on and start is not None:
            print(f"  {start / factor:7.1f}  {(x - start) / factor:6.1f}")
            start = None
    print("  Text: cap height is about 0.7 x font size; to confirm a size, compare a rendered text width with the source.")


def nearest_passing(text: str, background: str, target: float = 4.5) -> str | None:
    """The shade of background closest in lightness (same hue and saturation) that gives text at least target:1."""
    import colorsys
    r, g, b = (int(background[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    for step in range(1, 201):
        for sign in (-1, 1):
            lightness = l + sign * step / 200
            if 0 <= lightness <= 1:
                shade = hexcolor(tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, lightness, s)))
                if contrast(text, shade) >= target:
                    return shade
    return None


def scale_hint(width: int) -> str:
    hints = []
    for factor in (1, 2, 3):
        for device, label in DEVICE_WIDTHS:
            if abs(width / factor - device) <= 1:
                hints.append(f"{factor}x of {device}pt ({label})")
    return "; ".join(hints) or "unknown; ask the designer for the frame width"


def main(argv: list[str]) -> int:
    try:
        return run(argv)
    except (UsageError, ValueError, IndexError) as exc:
        message = str(exc) if isinstance(exc, UsageError) else f"bad arguments ({exc}); see --help"
        print(f"palette.py: {message}", file=sys.stderr)
        return 2


def run(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--contrast":
        if len(argv) < 3:
            raise UsageError("--contrast needs two colors: --contrast <text> <background> [--over <backdrop>]")
        over = argv[argv.index("--over") + 1] if "--over" in argv else None
        backdrop = composite(argv[2], over)
        text = composite(argv[1], backdrop)
        ratio = contrast(text, backdrop)
        verdict = "AA pass" if ratio >= 4.5 else "AA pass for large text only" if ratio >= 3 else "AA fail"
        shown = "" if (text, backdrop) == (argv[1].lower(), argv[2].lower()) else f" (as {text} on {backdrop})"
        print(f"{argv[1]} on {argv[2]}: {ratio:.2f}:1 ({verdict}){shown}")
        if "--fix" in argv:
            if ratio >= 4.5:
                print("  already passes AA; nothing to fix")
            else:
                shade = nearest_passing(text, backdrop)
                if shade:
                    print(f"  nearest AA shade: {shade} ({contrast(text, shade):.2f}:1); keep {argv[2]} in the token "
                          "comment as the source value and ask the designer to confirm")
                else:
                    print("  no shade of this background passes with that text; change the text color instead")
        return 0
    path = Path(argv[0])
    image = decode_png(path)
    width, height = image.width, image.height
    print(f"{path.name}: {width}x{height} px; likely scale: {scale_hint(width)}")
    if "--cols" in argv:
        span = argv[argv.index("--cols") + 1] if argv.index("--cols") + 1 < len(argv) else ""
        print_cols(image, span)
        return 0
    if "--rows" in argv:
        span = argv[argv.index("--rows") + 1] if argv.index("--rows") + 1 < len(argv) else ""
        print_rows(image, span)
        return 0
    if "--at" in argv:
        for point in argv[argv.index("--at") + 1:]:
            x, y = (int(v) for v in point.split(","))
            if not (0 <= x < width and 0 <= y < height):
                print(f"  ({x},{y}) outside the {width}x{height} image")
                continue
            print(f"  ({x},{y}) {hexcolor(image.pixel(x, y))}")
        return 0
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 16
    counts = image.counts()
    leaders = counts.most_common(top)
    wanted = {rgb for rgb, _ in leaders}
    first: dict[tuple[int, int, int], tuple[int, int]] = {}
    for y in range(height):
        if len(first) == len(wanted):
            break
        for x, rgb in enumerate(image.row_pixels(y)):
            if rgb in wanted and rgb not in first:
                first[rgb] = (x, y)
    total = width * height
    print("  color    share   first seen at (x,y px)")
    for rgb, n in leaders:
        x, y = first[rgb]
        print(f"  {hexcolor(rgb)}  {n * 100 / total:5.2f}%  ({x},{y})")
    print("Colors under ~0.05% are usually anti-aliasing; sample a point with --at to confirm a specific element.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
