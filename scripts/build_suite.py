#!/usr/bin/env python3
"""Check and build the WorkBuddy package of the design-to-dev skill.

Usage:
    python3 scripts/build_suite.py            # check, then build dist/
    python3 scripts/build_suite.py --check    # validate the sources and the package, write nothing

Output (dist/ is never committed; .github/workflows/release.yml attaches the zip to the Release):
    dist/design-to-dev-workbuddy-<version>.zip       folder design-to-dev/ inside; upload this to WorkBuddy
    dist/design-to-dev-workbuddy-<version>-flat.zip  SKILL.md at the zip root, if WorkBuddy refuses the folder
    dist/design-to-dev-workbuddy/                    unpacked package, for inspection

Rules and their sources: docs/workbuddy-rules.md. The skill's own SKILL.md keeps only Agent Skills
standard fields; the WorkBuddy display fields live in workbuddy.yaml and the version in
.claude-plugin/plugin.json (the only version source); both are injected into the packaged SKILL.md.
The build is deterministic: sorted entries, fixed timestamps, LF line endings.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
NAME = "design-to-dev"
SKILL = REPO / "skills" / NAME
WORKBUDDY = REPO / "workbuddy.yaml"
PLUGIN_JSON = REPO / ".claude-plugin" / "plugin.json"
DIST = REPO / "dist"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".md", ".py", ".js", ".css", ".html", ".json", ".yaml", ".yml", ".txt", ""}
EXCLUDE_PATTERNS = [re.compile(p) for p in (r"^__pycache__$", r"\.pyc$", r"^\.DS_Store$", r"^Thumbs\.db$")]

# Agent Skills standard (agentskills.io/specification), see docs/claude-directory-rules.md "Skill files".
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SPEC_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_LIMIT = 1024
COMPATIBILITY_LIMIT = 500
SKILL_MD_MAX_LINES = 500
# WorkBuddy, see docs/workbuddy-rules.md.
WB_REQUIRED = ("display_name", "display_name_en", "description_zh", "description_en", "examples_zh", "examples_en")
WB_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
WB_LIMITS = {"display_name_en": 60, "description_zh": 500, "description_en": 1000}
WB_MAX_EXAMPLES = 3


def excluded(name: str) -> bool:
    return any(p.search(name) for p in EXCLUDE_PATTERNS)


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_yaml_block(text: str) -> dict:
    """Small YAML subset: `key: value`, `key:` + indented `sub: value` map, or `key:` + `  - item` list."""
    data: dict = {}
    key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        top = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if top:
            key, value = top.group(1), top.group(2)
            data[key] = unquote(value) if value.strip() else None
            continue
        if key is None:
            raise SystemExit(f"cannot parse line: {line!r}")
        item = re.match(r"^\s+-\s+(.*)$", line)
        sub = re.match(r"^\s+([A-Za-z][\w-]*):\s*(.*)$", line)
        if item:
            if not isinstance(data[key], list):
                data[key] = []
            data[key].append(unquote(item.group(1)))
        elif sub:
            data[key] = data[key] if isinstance(data[key], dict) else {}
            data[key][sub.group(1)] = unquote(sub.group(2))
        else:
            raise SystemExit(f"cannot parse line: {line!r}")
    return data


def split_frontmatter(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise SystemExit(f"{path}: missing YAML frontmatter")
    return m.group(1), text[m.end():]


def plugin_version(repo: Path = REPO) -> str:
    """The only version source: .claude-plugin/plugin.json."""
    return json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version", "")


def check_skill(skill: Path = SKILL, errors: list[str] | None = None) -> list[str]:
    """Agent Skills standard rules for one skill folder."""
    errors = [] if errors is None else errors
    raw, _ = split_frontmatter(skill / "SKILL.md")
    fm = parse_yaml_block(raw)
    unknown = sorted(set(fm) - SPEC_FIELDS)
    if unknown:
        errors.append(f"SKILL.md: fields outside the Agent Skills standard: {unknown} (put platform fields in workbuddy.yaml)")
    if isinstance(fm.get("metadata"), dict) and "version" in fm["metadata"]:
        errors.append("SKILL.md: metadata.version is not allowed; the version lives only in .claude-plugin/plugin.json")
    name = fm.get("name") or ""
    if not (1 <= len(name) <= 64 and SPEC_NAME.match(name)):
        errors.append(f"name {name!r}: 1-64 chars, a-z 0-9 and single hyphens, no leading/trailing hyphen")
    if name != skill.name:
        errors.append(f"name {name!r} must equal its folder name {skill.name!r}")
    desc = fm.get("description") or ""
    if not 1 <= len(desc) <= DESCRIPTION_LIMIT:
        errors.append(f"description is {len(desc)} chars, allowed 1-{DESCRIPTION_LIMIT}")
    comp = fm.get("compatibility")
    if comp is not None and not 1 <= len(comp) <= COMPATIBILITY_LIMIT:
        errors.append(f"compatibility is {len(comp)} chars, allowed 1-{COMPATIBILITY_LIMIT}")
    if fm.get("metadata") is not None and not isinstance(fm.get("metadata"), dict):
        errors.append("metadata must be a map of string keys to string values")
    lines = (skill / "SKILL.md").read_text(encoding="utf-8").count("\n")
    if lines >= SKILL_MD_MAX_LINES:
        errors.append(f"SKILL.md has {lines} lines; keep it under {SKILL_MD_MAX_LINES}")
    for md in sorted(skill.rglob("*.md")):
        for target in re.findall(r"\]\(([^)#\s]+)", md.read_text(encoding="utf-8")):
            if not re.match(r"^[a-z]+:", target) and not (md.parent / target).resolve().exists():
                errors.append(f"{md.relative_to(skill.parent.parent).as_posix()}: broken link {target}")
    return errors


def workbuddy_fields(errors: list[str], name: str, wb_path: Path = WORKBUDDY) -> tuple[dict, str]:
    raw = wb_path.read_text(encoding="utf-8")
    wb = parse_yaml_block(raw)
    for field in WB_REQUIRED:
        if not wb.get(field):
            errors.append(f"workbuddy.yaml is missing {field}")
    if "version" in wb:
        errors.append("workbuddy.yaml must not carry version; it is injected from .claude-plugin/plugin.json")
    if not WB_NAME.match(name):
        errors.append("name must match ^[a-z0-9][a-z0-9-]{0,39}$ for WorkBuddy")
    for field, limit in WB_LIMITS.items():
        if len(wb.get(field) or "") > limit:
            errors.append(f"{field} is {len(wb[field])} chars, WorkBuddy allows {limit}")
    for field in ("examples_zh", "examples_en"):
        n = len(wb[field]) if isinstance(wb.get(field), list) else 0
        if not 1 <= n <= WB_MAX_EXAMPLES:
            errors.append(f"{field} has {n} items, WorkBuddy allows 1-{WB_MAX_EXAMPLES}")
    return wb, raw


def package_files(skill: Path = SKILL, repo: Path = REPO) -> list[tuple[str, Path]]:
    """(path inside the package, source file), sorted. WorkBuddy allows root/second-level/file."""
    entries = [("LICENSE", repo / "LICENSE")]
    for f in sorted(skill.rglob("*")):
        rel = f.relative_to(skill)
        if f.is_file() and not any(excluded(p) for p in rel.parts):
            entries.append((rel.as_posix(), f))
    return sorted(entries)


def injected_skill_md(skill: Path, wb_raw: str, version: str) -> bytes:
    raw, body = split_frontmatter(skill / "SKILL.md")
    extra = [l for l in wb_raw.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    head = raw.rstrip("\n") + "\n" + "\n".join(extra) + f"\nversion: {version}"
    return f"---\n{head}\n---\n{body}".encode("utf-8")


def content(rel: str, src: Path, wb_raw: str, version: str, skill: Path = SKILL) -> bytes:
    if rel == "SKILL.md":
        return injected_skill_md(skill, wb_raw, version)
    data = src.read_bytes()
    if src.suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return data


def validate_package(entries: list[tuple[str, Path]], wb_raw: str, version: str, skill: Path = SKILL) -> list[str]:
    """The package must read as exactly one skill (docs/workbuddy-rules.md)."""
    errors = []
    skill_files = [rel for rel, _ in entries if rel.rsplit("/", 1)[-1].lower() == "skill.md"]
    if skill_files != ["SKILL.md"]:
        errors.append(f"package must hold exactly one SKILL.md at its root, found {skill_files}")
    for rel, src in entries:
        if f"{NAME}/{rel}".count("/") > 2:
            errors.append(f"{rel}: deeper than root/second-level/file")
        data = content(rel, src, wb_raw, version, skill)
        if data.startswith(b"\xef\xbb\xbf"):
            errors.append(f"{rel} starts with a UTF-8 BOM")
        if rel != "SKILL.md" and rel.endswith(".md") and re.match(rb"\A---\n(?:.*\n)*?name:", data):
            errors.append(f"{rel} carries skill frontmatter; WorkBuddy would read it as a second skill")
    return errors


def make_zip(entries: list[tuple[str, Path]], prefix: str, wb_raw: str, version: str, skill: Path = SKILL) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, src in entries:
            info = zipfile.ZipInfo(prefix + rel, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, content(rel, src, wb_raw, version, skill))
    return buf.getvalue()


def check(repo: Path = REPO) -> tuple[list[str], str, str, list[tuple[str, Path]]]:
    skill = repo / "skills" / NAME
    errors = check_skill(skill)
    version = plugin_version(repo)
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"plugin.json version must be MAJOR.MINOR.PATCH, got {version!r}")
    name = parse_yaml_block(split_frontmatter(skill / "SKILL.md")[0]).get("name") or ""
    _, wb_raw = workbuddy_fields(errors, name, repo / "workbuddy.yaml")
    entries = package_files(skill, repo)
    errors += validate_package(entries, wb_raw, version, skill)
    return errors, version, wb_raw, entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    args = ap.parse_args()
    errors, version, wb_raw, entries = check()
    if errors:
        print("WorkBuddy package check failed:\n  " + "\n  ".join(errors))
        return 1
    data = make_zip(entries, f"{NAME}/", wb_raw, version)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if zf.testzip() is not None or len(zf.namelist()) != len(entries):
            print("WorkBuddy package did not build cleanly")
            return 1
    print(f"ok: {NAME} {version} WorkBuddy package ({len(data) // 1024} KB, {len(entries)} files)")
    if args.check:
        return 0
    DIST.mkdir(exist_ok=True)
    (DIST / f"{NAME}-workbuddy-{version}.zip").write_bytes(data)
    (DIST / f"{NAME}-workbuddy-{version}-flat.zip").write_bytes(make_zip(entries, "", wb_raw, version))
    out = DIST / f"{NAME}-workbuddy"
    if out.exists():
        shutil.rmtree(out)
    for rel, src in entries:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        (out / rel).write_bytes(content(rel, src, wb_raw, version))
    print(f"wrote dist/{NAME}-workbuddy-{version}.zip, the -flat.zip and dist/{NAME}-workbuddy/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
