#!/usr/bin/env python3
"""Validate design-to-dev against every target platform and build the upload package.

Usage:
    python3 scripts/build.py            # validate, then write design-to-dev.zip and dist/
    python3 scripts/build.py --check    # validate, and fail if the committed design-to-dev.zip is stale

Targets and their rules (sources in docs/01_plan.md, section 7):
    Agent Skills standard (agentskills.io/specification): SKILL.md frontmatter and folder layout
    Claude Code plugin marketplace: .claude-plugin/marketplace.json
    WorkBuddy: display fields from workbuddy.yaml are injected into the packaged SKILL.md

Output:
    design-to-dev.zip                      committed; folder design-to-dev/ inside (WorkBuddy upload)
    dist/design-to-dev/                    unpacked package, for inspection
    dist/design-to-dev-<version>-flat.zip  SKILL.md at the zip root, for platforms that need it

The build is deterministic (sorted entries, fixed timestamps, LF line endings), so --check can
compare the committed zip byte for byte. Python 3 standard library only.
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
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
CHANGELOG = REPO / "CHANGELOG.md"
ROOT_ZIP = REPO / f"{NAME}.zip"
DIST = REPO / "dist"
FIXED_TIME = (2020, 1, 1, 0, 0, 0)
TEXT_SUFFIXES = {".md", ".py", ".js", ".css", ".html", ".json", ".yaml", ".yml", ".txt", ""}
EXCLUDE = re.compile(r"(^__pycache__$|\.pyc$|^\.DS_Store$)")

# Agent Skills standard
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
SPEC_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_LIMIT = 1024
COMPATIBILITY_LIMIT = 500
SKILL_MD_MAX_LINES = 500
# WorkBuddy (EV-20261102-001 in Tealun-Skills; third-party summary, not yet officially confirmed)
WB_REQUIRED = ("display_name", "display_name_en", "description_zh", "description_en", "examples_zh", "examples_en")
WB_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
WB_LIMITS = {"display_name_en": 60, "description_zh": 500, "description_en": 1000}
WB_MAX_EXAMPLES = 3
# Claude Code marketplace
PLUGIN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


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


def check_spec(errors: list[str]) -> tuple[dict, str]:
    raw, body = split_frontmatter(SKILL / "SKILL.md")
    fm = parse_yaml_block(raw)
    unknown = sorted(set(fm) - SPEC_FIELDS)
    if unknown:
        errors.append(f"SKILL.md: fields outside the Agent Skills standard: {unknown} (put platform fields in workbuddy.yaml)")
    name = fm.get("name") or ""
    if not (1 <= len(name) <= 64 and SPEC_NAME.match(name)):
        errors.append(f"name {name!r}: 1-64 chars, a-z 0-9 and single hyphens, no leading/trailing hyphen")
    if name != SKILL.name:
        errors.append(f"name {name!r} must equal its folder name {SKILL.name!r}")
    desc = fm.get("description") or ""
    if not 1 <= len(desc) <= DESCRIPTION_LIMIT:
        errors.append(f"description is {len(desc)} chars, allowed 1-{DESCRIPTION_LIMIT}")
    comp = fm.get("compatibility")
    if comp is not None and not 1 <= len(comp) <= COMPATIBILITY_LIMIT:
        errors.append(f"compatibility is {len(comp)} chars, allowed 1-{COMPATIBILITY_LIMIT}")
    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        errors.append("metadata must be a map of string keys to string values")
    lines = (SKILL / "SKILL.md").read_text(encoding="utf-8").count("\n")
    if lines >= SKILL_MD_MAX_LINES:
        errors.append(f"SKILL.md has {lines} lines; keep it under {SKILL_MD_MAX_LINES}")
    for f in sorted(SKILL.rglob("*")):
        rel = f.relative_to(SKILL)
        if f.is_file() and not any(EXCLUDE.search(p) for p in rel.parts) and len(rel.parts) > 2:
            errors.append(f"{rel.as_posix()}: nested deeper than one folder (WorkBuddy allows root/second-level/file)")
    for md in sorted(SKILL.rglob("*.md")):
        for target in re.findall(r"\]\(([^)#\s]+)", md.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target):
                continue
            if not (md.parent / target).resolve().exists():
                errors.append(f"{md.relative_to(REPO).as_posix()}: broken link {target}")
    version = (meta or {}).get("version", "") if isinstance(meta, dict) else ""
    print(f"ok-spec: {name}, description {len(desc)}/{DESCRIPTION_LIMIT}, SKILL.md {lines} lines")
    return fm, version


def check_workbuddy(fm: dict, version: str, errors: list[str]) -> tuple[dict, str]:
    raw = WORKBUDDY.read_text(encoding="utf-8")
    wb = parse_yaml_block(raw)
    for field in WB_REQUIRED:
        if not wb.get(field):
            errors.append(f"workbuddy.yaml is missing {field}")
    clash = sorted(set(wb) & set(fm))
    if clash:
        errors.append(f"workbuddy.yaml repeats SKILL.md fields {clash}")
    if not WB_NAME.match(fm.get("name") or ""):
        errors.append("name must match ^[a-z0-9][a-z0-9-]{0,39}$ for WorkBuddy")
    for field, limit in WB_LIMITS.items():
        if len(wb.get(field) or "") > limit:
            errors.append(f"{field} is {len(wb[field])} chars, WorkBuddy allows {limit}")
    for field in ("examples_zh", "examples_en"):
        n = len(wb.get(field) or []) if isinstance(wb.get(field), list) else 0
        if not 1 <= n <= WB_MAX_EXAMPLES:
            errors.append(f"{field} has {n} items, WorkBuddy allows 1-{WB_MAX_EXAMPLES}")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append(f"metadata.version must be MAJOR.MINOR.PATCH, got {version!r}")
    if wb.get("version") != version:
        errors.append(f"workbuddy.yaml version {wb.get('version')!r} != SKILL.md metadata.version {version!r}")
    top = re.search(r"^## \[?(\d+\.\d+\.\d+)", CHANGELOG.read_text(encoding="utf-8"), re.M) if CHANGELOG.is_file() else None
    if not top or top.group(1) != version:
        errors.append(f"CHANGELOG.md latest version {top.group(1) if top else None!r} != {version!r}")
    print(f"ok-workbuddy: description_zh {len(wb.get('description_zh') or '')}/500, "
          f"description_en {len(wb.get('description_en') or '')}/1000")
    return wb, raw


def check_marketplace(version: str, errors: list[str]) -> None:
    try:
        data = json.loads(MARKETPLACE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"marketplace.json: {exc}")
        return
    if not data.get("name") or not (data.get("owner") or {}).get("name") or not data.get("plugins"):
        errors.append("marketplace.json needs name, owner.name and plugins")
    for plugin in data.get("plugins", []):
        pname, source = plugin.get("name", ""), plugin.get("source", "")
        if not PLUGIN_NAME.match(pname):
            errors.append(f"plugin name {pname!r} is invalid")
        if not isinstance(source, str) or not source.startswith("./") or ".." in source:
            errors.append(f"plugin {pname}: source must be a ./ path without '..'")
            continue
        root = (REPO / source).resolve()
        for path in plugin.get("skills", []):
            if not path.startswith("./") or ".." in path or not (root / path / "SKILL.md").is_file():
                errors.append(f"plugin {pname}: skills path {path!r} must start with ./ and hold a SKILL.md")
        if plugin.get("version") and plugin["version"] != version:
            errors.append(f"plugin {pname}: version {plugin['version']} != {version}")
    print(f"ok-marketplace: {len(data.get('plugins', []))} plugin(s)")


def package_files() -> list[tuple[str, Path]]:
    entries = [("LICENSE", REPO / "LICENSE")]
    for f in sorted(SKILL.rglob("*")):
        rel = f.relative_to(SKILL)
        if f.is_file() and not any(EXCLUDE.search(p) for p in rel.parts):
            entries.append((rel.as_posix(), f))
    return sorted(entries)


def content(rel: str, src: Path, wb_raw: str) -> bytes:
    data = src.read_bytes()
    if src.suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    if rel == "SKILL.md":
        raw, body = split_frontmatter(src)
        injected = raw.rstrip("\n") + "\n" + "\n".join(l for l in wb_raw.splitlines() if l.strip() and not l.lstrip().startswith("#"))
        data = f"---\n{injected}\n---\n{body}".encode("utf-8")
    return data


def make_zip(entries: list[tuple[str, Path]], prefix: str, wb_raw: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel, src in entries:
            info = zipfile.ZipInfo(prefix + rel, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, content(rel, src, wb_raw))
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate and compare with the committed zip")
    args = ap.parse_args()
    errors: list[str] = []
    fm, version = check_spec(errors)
    _, wb_raw = check_workbuddy(fm, version, errors)
    check_marketplace(version, errors)
    if errors:
        print("validation failed:\n  " + "\n  ".join(errors))
        return 1
    entries = package_files()
    for rel, _ in entries:
        if rel.count("/") > 1:
            print(f"{rel}: deeper than root/second-level/file")
            return 1
    fresh = make_zip(entries, f"{NAME}/", wb_raw)
    if args.check:
        if not ROOT_ZIP.is_file() or ROOT_ZIP.read_bytes() != fresh:
            print(f"{ROOT_ZIP.name} is missing or stale: run python3 scripts/build.py and commit it")
            return 1
        print(f"ok: {ROOT_ZIP.name} matches the sources ({len(entries)} files, version {version})")
        return 0
    ROOT_ZIP.write_bytes(fresh)
    out = DIST / NAME
    if out.exists():
        shutil.rmtree(out)
    for rel, src in entries:
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content(rel, src, wb_raw))
    flat = DIST / f"{NAME}-{version}-flat.zip"
    flat.write_bytes(make_zip(entries, "", wb_raw))
    print(f"wrote {ROOT_ZIP.name} ({len(fresh) // 1024} KB, {len(entries)} files), dist/{NAME}/ and {flat.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
