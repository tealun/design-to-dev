#!/usr/bin/env python3
"""Bundle real web fonts into a prototype so it looks designed and still runs offline from file://.

Usage:
    python3 fetch_fonts.py <output>/prototype "Noto Serif SC:700" "Noto Sans SC:400,500"
    python3 fetch_fonts.py <output>/prototype "Geist:400,500,600" --latin

Each argument is "Family:weights" as named on Google Fonts (open licenses: OFL / Apache).
By default the font is subset to the characters actually used in the prototype's .html/.js files
(Google Fonts `text=` subsetting), plus ASCII, which keeps Chinese and Japanese fonts small.
--latin downloads the full Latin subset instead (for typed input in Latin scripts).

Pass every family in one call: each run replaces prototype/fonts/ (old .woff2 files and fonts.css).
Writes prototype/fonts/*.woff2 and prototype/fonts/fonts.css (@font-face rules with local URLs).
index.html loads fonts/fonts.css; tokens name the families with system fallbacks after them.
Without network access the script exits with an error: keep the system fallback and record the
font as TBD in HANDOFF. Re-run after copy changes, because new characters are not in the subset.
Python 3 standard library only; honours HTTPS_PROXY and SSL_CERT_FILE.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CSS_API = "https://fonts.googleapis.com/css2"
# A modern browser user agent makes the API answer with woff2.
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TEXT_SUFFIXES = {".html", ".js", ".css"}


def context() -> ssl.SSLContext:
    cafile = os.environ.get("SSL_CERT_FILE") or ("/root/.ccr/ca-bundle.crt" if Path("/root/.ccr/ca-bundle.crt").is_file() else None)
    return ssl.create_default_context(cafile=cafile)


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=context(), timeout=60) as resp:
        return resp.read()


def used_characters(proto: Path) -> str:
    chars = set(chr(c) for c in range(0x20, 0x7F))
    for path in proto.rglob("*"):
        # Judge by the path inside the prototype: a parent folder called "fonts" must not hide everything.
        inside = path.relative_to(proto).parts
        if path.suffix in TEXT_SUFFIXES and path.is_file() and inside[0] != "fonts":
            chars.update(path.read_text(encoding="utf-8"))
    return "".join(sorted(c for c in chars if c.isprintable() and not c.isspace() or c == " "))


def parse_spec(spec: str) -> tuple[str, list[str]]:
    family, _, weights = spec.partition(":")
    family = family.strip()
    weights = [w.strip() for w in (weights or "400").split(",") if w.strip()]
    if not family:
        raise SystemExit(f"'{spec}': missing family name; write it as \"Family Name:400,700\"")
    bad = [w for w in weights if not (w.isdigit() and 1 <= int(w) <= 1000)]
    if bad:
        raise SystemExit(f"'{spec}': font weight must be a number such as 400 or 700, got {', '.join(bad)}")
    return family, sorted(set(weights), key=int)


def fetch(out_dir: Path, family: str, weights: list[str], latin: bool, text: str) -> list[str]:
    query = {"family": f"{family}:wght@{';'.join(weights)}", "display": "swap"}
    if not latin:
        query["text"] = text
    try:
        css = get(CSS_API + "?" + urllib.parse.urlencode(query, safe=":@;")).decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 400:
            raise SystemExit(f"Google Fonts has no family '{family}' with weights {', '.join(weights)}; "
                             "check the exact name and available weights on fonts.google.com")
        raise
    rules = []
    # Each block may be labelled with its script subset, e.g. "/* latin */"; text= subsets carry no label.
    for label, block in re.findall(r"(?:/\*\s*([\w-]+)\s*\*/\s*)?(@font-face\s*\{[^}]*\})", css):
        if latin and label not in ("latin", "latin-ext"):
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        weight = re.search(r"font-weight:\s*(\d+)", block).group(1)
        # Variable fonts return one file for several weights: name by URL so it is stored once.
        name = f"{re.sub(r'[^a-z0-9]+', '-', family.lower()).strip('-')}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.woff2"
        if not (out_dir / name).is_file():
            data = get(url)
            if data[:4] != b"wOF2":
                raise SystemExit(f"{family} {weight}: response is not a woff2 file")
            (out_dir / name).write_bytes(data)
            print(f"  {name}  {len(data) // 1024 or 1} KB")
        rules.append(block.replace(url, name))
    if not rules:
        raise SystemExit(f"{family}: no font files returned; check the family name and weights on fonts.google.com")
    return rules


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[0] in {"-h", "--help"}:
        print(__doc__)
        return 0 if argv and argv[0] in {"-h", "--help"} else 2
    proto = Path(argv[0])
    index = proto / "index.html"
    if not index.is_file():
        raise SystemExit(f"{proto} has no index.html; pass the prototype folder")
    latin = "--latin" in argv
    # Validate everything before touching the network or the fonts folder.
    specs = [parse_spec(a) for a in argv[1:] if not a.startswith("--")]
    html = index.read_text(encoding="utf-8")
    if "fonts/fonts.css" not in html and not re.search(r"<link[^>]+tokens\.css[^>]*>", html):
        raise SystemExit('index.html has no tokens.css <link>; add <link rel="stylesheet" href="fonts/fonts.css"> '
                         "before your token stylesheet yourself, then re-run")
    text = used_characters(proto)
    print(f"{len(text)} characters used in the prototype")
    fonts_dir = proto / "fonts"
    fonts_dir.mkdir(exist_ok=True)
    # Download into a temporary folder; the existing fonts are replaced only when every family succeeded.
    staging = Path(tempfile.mkdtemp(prefix=".fetch-", dir=fonts_dir))
    try:
        rules: list[str] = []
        for family, weights in specs:
            rules += fetch(staging, family, weights, latin, text)
    except (urllib.error.URLError, OSError) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        raise SystemExit(f"cannot reach Google Fonts ({exc}); existing fonts were kept. Without network, keep the "
                         "system fallback and record the font as TBD")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    for old in fonts_dir.glob("*.woff2"):
        old.unlink()
    for new in staging.glob("*.woff2"):
        new.replace(fonts_dir / new.name)
    shutil.rmtree(staging, ignore_errors=True)
    header = "/* fonts.css — generated by fetch_fonts.py from Google Fonts (open licenses). Do not edit; re-run the script. */\n"
    (fonts_dir / "fonts.css").write_text(header + "\n".join(rules) + "\n", encoding="utf-8")
    if "fonts/fonts.css" not in html:
        # Fonts load first, so the token stylesheet can name the families.
        html = re.sub(r"(\s*)(<link[^>]+tokens\.css[^>]*>)", r'\1<link rel="stylesheet" href="fonts/fonts.css">\1\2', html, count=1)
        index.write_text(html, encoding="utf-8")
        print("added fonts/fonts.css to index.html")
    total = sum(p.stat().st_size for p in (proto / "fonts").glob("*.woff2"))
    print(f"wrote fonts/fonts.css ({len(rules)} faces, {total // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
