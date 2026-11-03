#!/usr/bin/env python3
"""Check a design-to-dev output folder before handing it off.

Usage:
    python3 check_output.py <output>                      # default stack (plain HTML prototype)
    python3 check_output.py <output> --mode B             # also require a filled PLANNER_BRIEF.md
    python3 check_output.py <output> --prototype-entry <output>/prototype/src   # other stacks: where pages live

Exit code 0 when there are no errors. Warnings are printed but do not fail the check.
Python 3 standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LEVELS = {"fixed", "indicative", "tbd"}
# Each HANDOFF section may be titled in English or Chinese; the template uses both.
SECTIONS = {
    "pages": ("Pages", "页面清单"),
    "flow": ("Flow", "流程图"),
    "components": ("Components", "组件清单"),
    "interactions": ("Interactions", "交互细节"),
    "tokens": ("Design tokens", "设计规范"),
    "levels": ("Spec levels", "标注等级"),
    "questions": ("Open questions", "待定问题"),
}
HEX = re.compile(r"(?<![&\w/])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
FUNC_COLOR = re.compile(r"\b(?:rgba?|hsla?)\(")
SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".html"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def strip_non_color_hashes(text: str) -> str:
    """Remove places where '#abc' is not a color: spec notes, href anchors, id selectors, comments."""
    text = re.sub(r"/\*.*?\*/|(?:^|(?<=\s))//[^\n]*|<!--.*?-->", "", text, flags=re.S | re.M)
    text = re.sub(r"data-spec-note=\\?([\"']).*?\\?\1", "", text, flags=re.S)
    text = re.sub(r"href=\\?[\"']#[^\"'\\]*", "href=", text)
    text = re.sub(r"(querySelector(?:All)?|getElementById|closest)\(\s*['\"][^'\"]*['\"]", r"\1(", text)
    return text


def css_tokens(text: str) -> dict[str, str]:
    block = re.search(r":root\s*\{(.*?)\}", text, re.S)
    if not block:
        return {}
    return dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", block.group(1)))


def json_tokens(data: dict, prefix: tuple[str, ...] = ()) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for key, value in data.items():
        if key.startswith("$") or not isinstance(value, dict):
            continue
        path = prefix + (key,)
        if "$value" in value:
            out["-".join(path)] = value
        else:
            out.update(json_tokens(value, path))
    return out


def section(markdown: str, names: tuple[str, ...]) -> str | None:
    """Body of the first '## ' heading that contains one of names, up to the next '## '."""
    parts = re.split(r"^## ", markdown, flags=re.M)
    for part in parts[1:]:
        heading = part.splitlines()[0] if part else ""
        if any(n.lower() in heading.lower() for n in names):
            return part
    return None


def table_rows(body: str) -> list[list[str]]:
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|", line):
            continue
        rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows[1:]  # drop header


def check_tokens(out: Path, r: Report) -> set[str]:
    css_path, json_path = out / "design-tokens" / "tokens.css", out / "design-tokens" / "tokens.json"
    css_text = read(css_path)
    css = css_tokens(css_text)
    roots = re.findall(r":root\s*\{(.*?)\}", css_text, re.S)
    if len(roots) > 1:
        r.error(f"design-tokens/tokens.css: {len(roots)} :root blocks; only the first is read, so tokens would be lost")
    bad = [n for n in re.findall(r"--([^\s:;]+)\s*:", roots[0] if roots else "") if not re.fullmatch(r"[a-z0-9-]+", n)]
    if bad:
        r.error(f"design-tokens/tokens.css: token names must be lowercase a-z, 0-9 and hyphens: {', '.join('--' + n for n in bad)}")
    if not css:
        r.error("design-tokens/tokens.css: no tokens found in a :root { } block")
    try:
        data = json.loads(read(json_path) or "{}")
    except json.JSONDecodeError as exc:
        r.error(f"design-tokens/tokens.json: invalid JSON ({exc})")
        data = {}
    js = json_tokens(data)
    if not js:
        r.error("design-tokens/tokens.json: no tokens with $value found")
    only_css, only_json = sorted(set(css) - set(js)), sorted(set(js) - set(css))
    if only_css:
        r.error(f"tokens only in tokens.css: {', '.join(only_css)}")
    if only_json:
        r.error(f"tokens only in tokens.json: {', '.join(only_json)}")
    counts = {lvl: 0 for lvl in LEVELS}
    for name, tok in js.items():
        level = tok.get("$extensions", {}).get("design-to-dev", {}).get("level")
        if level not in LEVELS:
            r.error(f"tokens.json {name}: level must be fixed, indicative or tbd (got {level!r})")
        else:
            counts[level] += 1
        if name in css and str(tok.get("$value")).strip() != css[name].strip():
            r.error(f"token {name}: tokens.css has {css[name].strip()!r}, tokens.json has {tok.get('$value')!r}")
    r.note(f"tokens: {len(js)} (fixed {counts['fixed']}, indicative {counts['indicative']}, tbd {counts['tbd']})")
    return set(css)


def check_prototype(out: Path, entry: Path, default_stack: bool, tokens: set[str], r: Report) -> tuple[list[str], dict[str, int]]:
    proto = out / "prototype"
    index = read(proto / "index.html")
    if default_stack:
        for name in ("index.html", "styles.css", "proto-kit.js", "data.js", "pages.js"):
            if not (proto / name).is_file():
                r.error(f"prototype/{name} is missing")
        if "../design-tokens/tokens.css" not in index:
            r.error("prototype/index.html does not load ../design-tokens/tokens.css")
    elif not entry.is_dir():
        r.error(f"prototype entry {entry} does not exist")
    if re.search(r"<script[^>]+src=[\"']https?://", index, re.I):
        r.error("prototype/index.html loads a remote script; the prototype must run offline from file://")
    if re.search(r"<link[^>]+href=[\"']https?://", index, re.I):
        r.warn("prototype/index.html loads a remote stylesheet (web font?); it will fall back offline")

    sources = [p for p in sorted(entry.rglob("*")) if p.suffix in SOURCE_SUFFIXES and p.name != "proto-kit.js"
               and "node_modules" not in p.parts]
    styles = [p for p in sorted(entry.rglob("*.css")) if "node_modules" not in p.parts]
    routes: list[str] = []
    marks: dict[str, int] = {}
    for path in sources + styles:
        text = read(path)
        rel = path.relative_to(out).as_posix()
        if "{{" in text:
            r.error(f"{rel}: unfilled template placeholder {{{{…}}}}")
        routes += re.findall(r"Proto\.page\(\s*['\"]([^'\"]+)['\"]", text)
        for value in re.findall(r"data-spec=\\?[\"']([\w-]+)\\?[\"']", text):
            marks[value] = marks.get(value, 0) + 1
        for name in re.findall(r"var\(--([a-z0-9-]+)", text):
            if tokens and name not in tokens:
                r.error(f"{rel}: uses var(--{name}), which is not defined in tokens.css")
        scan = text
        if path.suffix == ".css":
            scan = "".join(re.findall(r"\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", text, flags=re.S)))
        else:
            scan = strip_non_color_hashes(text)
        bad = HEX.findall(scan) + FUNC_COLOR.findall(scan)
        if bad:
            r.error(f"{rel}: raw colors {sorted(set(bad))[:5]}; use token variables")
    if default_stack and not routes:
        r.error("pages.js registers no pages with Proto.page()")
    invalid = sorted(set(marks) - LEVELS)
    if invalid:
        r.error(f"data-spec values must be fixed, indicative or tbd; found {invalid}")
    if not any(marks.get(lvl) for lvl in LEVELS):
        r.error("no data-spec marks in the prototype")
    r.note(f"pages: {len(routes)} ({', '.join(routes)})")
    r.note("spec marks: " + ", ".join(f"{lvl} {marks.get(lvl, 0)}" for lvl in ("fixed", "indicative", "tbd")))
    return routes, marks


SYSTEM_FONTS = {"system-ui", "-apple-system", "blinkmacsystemfont", "sf pro text", "sf pro display", "segoe ui", "roboto",
                "arial", "helvetica", "helvetica neue", "inter", "pingfang sc", "hiragino sans gb", "microsoft yahei",
                "sans-serif", "serif", "ui-sans-serif", "ui-serif"}
SPACING_PROPS = re.compile(r"^(margin|padding)(-(top|right|bottom|left|block|inline)(-(start|end))?)?$|^(row-|column-|grid-)?gap$")
WEIGHT_WORDS = {"normal": "400", "bold": "700"}
# One declaration, optionally followed by its own comment (also after a closing brace): "padding: 6px; /* off-scale: … */"
DECL = re.compile(r"([a-z-]+)\s*:\s*([^;{}]+?)\s*(?:;|(?=\}))\s*\}?\s*(/\*.*?\*/)?")
LENGTH = re.compile(r"(?<![\w.#-])(-?\d*\.?\d+)(px|rem)\b")


def resolve(value: str, tokens: dict[str, str], depth: int = 0) -> str:
    """Replace var(--x, fallback) with the token value (or the fallback), a few levels deep."""
    def sub(m: re.Match) -> str:
        name, fallback = m.group(1), (m.group(2) or "").strip()
        return tokens.get(name, fallback)
    for _ in range(4):
        new = re.sub(r"var\(--([a-z0-9-]+)\s*(?:,\s*([^()]*))?\)", sub, value)
        if new == value:
            break
        value = new
    return value.strip()


def declarations(text: str):
    """(line number, property, value, exempt) for each declaration in CSS text."""
    for n, line in enumerate(text.splitlines(), 1):
        for m in DECL.finditer(line):
            exempt = bool(m.group(3) and re.match(r"/\*\s*(decorative|off-scale)\b", m.group(3)))
            yield n, m.group(1), m.group(2), exempt


def check_visual(out: Path, entry: Path, tokens_css: str, r: Report) -> None:
    """Objective items of the visual QA checklist (references/visual-direction.md). Warnings, not errors,
    because a reason may exist; the close must fix or explain each one. Exempt one declaration with a
    comment right after it: `font-size: 9px; /* decorative: cover texture */` or `/* off-scale: … */`."""
    tokens = dict(re.findall(r"--([a-z0-9-]+)\s*:\s*([^;]+);", tokens_css))
    weights: set[str] = set()
    animated = reduced = False

    def lint(rel: str, n: int, prop: str, raw: str, exempt: bool) -> None:
        nonlocal animated
        value = resolve(raw, tokens)
        if prop in ("animation", "transition") or prop.startswith(("animation-", "transition-")):
            animated = True
        if prop == "font-weight":
            w = WEIGHT_WORDS.get(value, value)
            if w not in ("inherit", "bolder", "lighter", "initial", "unset"):
                weights.add(w)
        if exempt:
            return
        sizes = []
        if prop == "font-size":
            sizes = LENGTH.findall(value)
        elif prop == "font":
            m = re.search(r"(-?\d*\.?\d+)(px|rem)\s*(?:/|\s)", value + " ")
            sizes = [m.groups()] if m else []
        for num, unit in sizes:
            px = float(num) * (16 if unit == "rem" else 1)
            if px < 12:
                via = f" (from {raw.strip()})" if "var(" in raw else ""
                r.warn(f"{rel}:{n}: {prop}: {num}{unit}{via} is below the 12px minimum for readable text")
        if SPACING_PROPS.match(prop):
            bad = []
            for num, unit in LENGTH.findall(value):
                px = abs(float(num)) * (16 if unit == "rem" else 1)
                if px not in (0, 1, 2) and px % 4:
                    bad.append(num + unit)
            if bad:
                r.warn(f"{rel}:{n}: {prop} uses {', '.join(bad)}, off the 4px scale")

    for name, value in tokens.items():
        if name.startswith("font-size-"):
            for num, unit in LENGTH.findall(value):
                if float(num) * (16 if unit == "rem" else 1) < 12:
                    r.warn(f"design-tokens/tokens.css: --{name} is {num}{unit}, below the 12px minimum for readable text")
    files = [p for p in sorted(entry.rglob("*")) if p.suffix in {".css", ".js", ".html"} and p.is_file()
             and p.relative_to(entry).parts[0] not in ("fonts", "node_modules") and p.name != "proto-kit.js"]
    for path in files:
        rel = path.relative_to(out).as_posix()
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".css":
            reduced |= "prefers-reduced-motion" in text
            for n, prop, value, exempt in declarations(text):
                lint(rel, n, prop, value, exempt)
        else:
            # Inline styles in page code: style="…" or style=\"…\".
            for n, line in enumerate(text.splitlines(), 1):
                for m in re.finditer(r"style=\\?([\"'])(.*?)\\?\1", line):
                    for _, prop, value, exempt in declarations(m.group(2)):
                        lint(rel, n, prop, value, exempt)
    if len(weights) > 4:
        r.warn(f"{len(weights)} font weights in use ({', '.join(sorted(weights))}); keep to 3 for text plus 1 for display")
    if animated and not reduced:
        r.warn("styles animate but never handle prefers-reduced-motion")
    display = resolve(tokens.get("font-family-display") or tokens.get("font-family-base", ""), tokens)
    first = display.split(",")[0].strip().strip("'\"").lower()
    if first in SYSTEM_FONTS:
        r.warn(f"display font '{first}' is a system/default face; choose a distinctive face for the direction and bundle it "
               "with fetch_fonts.py, unless the VI specifies a system font")
    fonts_css = entry / "fonts" / "fonts.css"
    if fonts_css.is_file():
        for src in re.findall(r"url\(([^)]+)\)", fonts_css.read_text(encoding="utf-8")):
            if not (fonts_css.parent / src.strip("'\"")).is_file():
                r.error(f"prototype/fonts/fonts.css points to missing font file {src}")


def check_handoff(out: Path, routes: list[str], marks: dict[str, int], r: Report) -> None:
    text = read(out / "HANDOFF.md")
    if not text:
        r.error("HANDOFF.md is missing")
        return
    if "{{" in text:
        r.error("HANDOFF.md: unfilled template placeholder {{…}}")
    bodies = {}
    for key, names in SECTIONS.items():
        body = section(text, names)
        if body is None:
            r.error(f"HANDOFF.md: missing section '{names[0]} / {names[1]}'")
        bodies[key] = body or ""
    if "```mermaid" not in text:
        r.error("HANDOFF.md: no ```mermaid flow diagram")
    # "/?tab=done" is a view of "/": compare paths without the query part.
    listed = {route.split("?")[0] for route in re.findall(r"`(/[^`\s]*)`", bodies["pages"])}
    if routes:
        missing = sorted(set(routes) - listed)
        extra = sorted(listed - set(routes))
        if missing:
            r.error(f"HANDOFF.md pages table is missing routes from the prototype: {missing}")
        if extra:
            r.error(f"HANDOFF.md lists routes that the prototype does not have: {extra}")
    questions = [row for row in table_rows(bodies["questions"]) if any(cell for cell in row[1:])]
    if marks.get("tbd") and not questions:
        r.error("prototype has TBD marks but HANDOFF.md has no open questions")
    elif marks.get("tbd", 0) > len(questions):
        r.warn(f"{marks['tbd']} TBD marks but {len(questions)} open questions; make sure each TBD is covered")
    for row in questions:
        if len(row) >= 4 and (not row[2] or not row[3]):
            r.warn(f"open question {row[0]}: missing suggested answer or owner")
    r.note(f"open questions: {len(questions)}")


def handoff_mode(out: Path) -> str | None:
    """Mode from the HANDOFF 'Handoff to / 交接对象' row: 'A' or 'B', None when not stated."""
    for line in read(out / "HANDOFF.md").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and ("handoff to" in cells[0].lower() or "交接对象" in cells[0]):
            m = re.match(r"^\W*([AB])\b", cells[1].replace("：", ":"), re.I)
            return m.group(1).upper() if m else None
    return None


def check_brief(out: Path, mode: str | None, r: Report) -> None:
    brief = read(out / "PLANNER_BRIEF.md")
    stated = handoff_mode(out)
    if mode and stated and mode.upper() != stated:
        r.error(f"--mode {mode.upper()} but HANDOFF.md says the handoff is mode {stated}")
    mode = (mode or stated or "A").upper()
    r.note(f"mode: {mode}")
    if mode == "B" and not brief:
        r.error("mode B needs PLANNER_BRIEF.md; write it before running this check")
    if brief and "{{" in brief:
        r.error("PLANNER_BRIEF.md: unfilled template placeholder {{…}}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("output", type=Path)
    ap.add_argument("--mode", choices=["A", "B", "a", "b"], help="default: read from HANDOFF.md 'Handoff to', else A")
    ap.add_argument("--prototype-entry", type=Path, help="folder with page sources for non-default stacks")
    args = ap.parse_args()
    out: Path = args.output
    if not out.is_dir():
        print(f"ERROR {out} is not a folder")
        return 2
    r = Report()
    default_stack = args.prototype_entry is None
    entry = args.prototype_entry or out / "prototype"
    tokens = check_tokens(out, r)
    routes, marks = check_prototype(out, entry, default_stack, tokens, r)
    check_visual(out, entry, read(out / "design-tokens" / "tokens.css"), r)
    check_handoff(out, routes, marks, r)
    check_brief(out, args.mode, r)
    for n in r.notes:
        print(f"info  {n}")
    for w in r.warnings:
        print(f"WARN  {w}")
    for e in r.errors:
        print(f"ERROR {e}")
    print(("FAIL" if r.errors else "PASS") + f": {len(r.errors)} errors, {len(r.warnings)} warnings")
    return 1 if r.errors else 0


if __name__ == "__main__":
    sys.exit(main())
