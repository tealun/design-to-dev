#!/usr/bin/env python3
"""Generate design-tokens/tokens.json (W3C Design Tokens format) from design-tokens/tokens.css.

Usage:
    python3 tokens_json.py <output>/design-tokens/tokens.css            # writes tokens.json beside it
    python3 tokens_json.py tokens.css --stdout                         # print instead of writing

tokens.css convention (one token per line inside :root):
    --color-primary: #2f6f4f;   /* fixed · brand guide p.3 */
A line without a comment inherits the level and source of the token above it.
Levels: fixed | indicative | tbd. Python 3 standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Longest prefix wins: --font-size-lg -> group "font-size", key "lg".
GROUPS = [
    "color", "font-family", "font-weight", "font-size", "line-height", "letter-spacing",
    "space", "radius", "shadow", "duration", "easing", "layout", "breakpoint", "z", "opacity", "border-width", "size",
]
TYPES = {
    "color": "color", "font-family": "fontFamily", "font-weight": "fontWeight", "font-size": "dimension",
    "line-height": "number", "letter-spacing": "dimension", "space": "dimension", "radius": "dimension",
    "shadow": "shadow", "duration": "duration", "easing": "cubicBezier", "layout": "dimension",
    "breakpoint": "dimension", "z": "number", "opacity": "number", "border-width": "dimension",
    "size": "dimension",
}
LEVELS = {"fixed", "indicative", "tbd"}
DECL = re.compile(r"^\s*--([a-z0-9-]+)\s*:\s*(.+?)\s*;\s*(?:/\*\s*(.*?)\s*\*/)?\s*$")


def split_name(name: str) -> tuple[str, str]:
    for group in sorted(GROUPS, key=len, reverse=True):
        if name.startswith(group + "-"):
            return group, name[len(group) + 1:]
    head, _, rest = name.partition("-")
    return head, rest or "default"


def parse_css(text: str) -> list[dict]:
    tokens, level, source = [], "indicative", "assumed"
    roots = re.findall(r":root\s*\{(.*?)\}", text, re.S)
    if not roots:
        raise SystemExit("tokens.css: no :root { ... } block found")
    if len(roots) > 1:
        raise SystemExit(f"tokens.css: {len(roots)} :root blocks found; use one. Give variants their own names "
                         "(e.g. --color-bg-dark) or record dark mode as TBD.")
    bad = [n for n in re.findall(r"--([^\s:;]+)\s*:", roots[0]) if not re.fullmatch(r"[a-z0-9-]+", n)]
    if bad:
        raise SystemExit(f"tokens.css: token names must be lowercase a-z, 0-9 and hyphens: {', '.join('--' + n for n in bad)}")
    for line in roots[0].splitlines():
        m = DECL.match(line)
        if not m:
            if line.strip().startswith("--"):
                raise SystemExit(f"tokens.css: cannot read this token line; keep one token per line ending with ';': {line.strip()}")
            continue
        name, value, comment = m.groups()
        if comment:
            parts = [p.strip() for p in re.split(r"·|\|", comment, maxsplit=1)]
            if parts[0].lower() in LEVELS:
                level = parts[0].lower()
                source = parts[1] if len(parts) > 1 and parts[1] else source
        tokens.append({"name": name, "value": value, "level": level, "source": source})
    return tokens


def to_json(tokens: list[dict]) -> dict:
    out: dict = {}
    for tok in tokens:
        group, key = split_name(tok["name"])
        node = out.setdefault(group, {})
        if key in node:
            raise SystemExit(f"duplicate token {tok['name']}")
        node[key] = {
            "$value": tok["value"],
            "$type": TYPES.get(group, "string"),
            "$extensions": {"design-to-dev": {"level": tok["level"], "source": tok["source"]}},
        }
    return out


def main(argv: list[str]) -> int:
    if not argv or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv else 2
    css = Path(argv[0])
    data = to_json(parse_css(css.read_text(encoding="utf-8")))
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if "--stdout" in argv:
        sys.stdout.write(text)
    else:
        target = css.with_name("tokens.json")
        target.write_text(text, encoding="utf-8")
        count = sum(len(v) for v in data.values())
        print(f"wrote {target} ({count} tokens in {len(data)} groups)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
