#!/usr/bin/env python3
"""Check and build the Claude plugin package design-to-dev-<version>.plugin.

The repository root holds .claude-plugin/plugin.json, the only version source. The
package is what the plugin directory scans: plugin-branch.yml writes it to the `plugin` branch
and .github/workflows/release.yml attaches it to the Release.

    .claude-plugin/plugin.json
    skills/design-to-dev/...      the skill, minus caches
    README.md, LICENSE, PRIVACY.md
    assets/<icon>                 the icon plugin.json points at
    docs/images/readlog.png       the preview image README.md shows

Output goes to dist/ only and is never committed. The zip is reproducible: sorted
entries, fixed timestamps, LF line endings.

Usage:
    python3 scripts/build_plugin.py                  check, then build
    python3 scripts/build_plugin.py --check          checks only
      [--tag vX.Y.Z]      the tag must equal v + plugin.json version, with release notes
      [--since <tag>]     if the skill changed since <tag>, the version must be higher
      [--release]         also require the MAJOR.MINOR auditor report (implied by --tag)
    python3 scripts/build_plugin.py --notes FILE     write this version's CHANGELOG section
Rules and their sources: docs/claude-directory-rules.md. Plan: docs/06_release-pipeline-plan.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN_JSON = REPO / ".claude-plugin" / "plugin.json"
DIST = REPO / "dist"
NAME = "design-to-dev"
EXTRA_FILES = ["README.md", "LICENSE", "PRIVACY.md", "docs/images/readlog.png"]
VERSION_PATTERN = re.compile(r"\d+\.\d+\.\d+")
REFERENCE_PATTERN = re.compile(r"[(`]((?:references|scripts|templates)/[\w./-]+?)[)`]")

# Claude plugin directory rules (docs/claude-directory-rules.md).
NAME_PATTERN = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?")
RESERVED_NAMES = {"claude", "anthropic", "official", "plugin", "mcp", "test"}
RESERVED_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
README_MIN_WORDS = 40
# The directory shows clone-and-run or pipe-to-shell install steps to users as an install-time risk.
# A Claude session link or ID in a tracked file (the repository is public; see AGENTS.md).
SESSION_ID = re.compile(r"claude\.ai/code/session|\bsession_0[0-9A-Za-z]{20,}")
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".pdf"}
DOWNLOAD_AND_RUN = re.compile(
    r"git clone|curl\s|wget\s|\birm\b|\biwr\b|Invoke-WebRequest|Invoke-Expression|\biex\b"
    r"|\|\s*(ba|z)?sh\b|\bbash\s+\S+\.sh|\.ps1\b|\bnpx\s|\buvx\s|\bpipx\s", re.I)
MAX_FILE_BYTES = 5 * 1024 * 1024          # stops validation
MAX_TEXT_FILE_BYTES = 256 * 1024          # held for a reviewer (images and fonts exempt)
MAX_FILES = 512                           # held for a reviewer
MEDIA_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf"}
HELD_SUFFIXES = {".zip", ".plugin", ".ico", ".pdf", ".exe", ".dll", ".so", ".dylib", ".jar", ".tar", ".gz", ".7z"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini", "__MACOSX"}
# .gitattributes settings that make checked-out or exported bytes differ from the stored ones.
# "-text" and "binary" switch conversion off and are allowed.
REWRITING_ATTRIBUTES = ("text", "eol", "filter", "export-ignore", "export-subst", "ident",
                        "working-tree-encoding", "crlf")


def _load_build_suite():
    spec = importlib.util.spec_from_file_location("build_suite", REPO / "scripts" / "build_suite.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_suite = _load_build_suite()
FIXED_TIME = _suite.FIXED_TIME
excluded = _suite.excluded


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def skill_paths(manifest: dict) -> list[str]:
    """Skill folders from plugin.json, e.g. './skills/design-to-dev' -> 'skills/design-to-dev'."""
    return [s[2:].rstrip("/") if s.startswith("./") else s.rstrip("/") for s in manifest.get("skills", [])]


def check(repo: Path = REPO, tag: str | None = None, since: str | None = None, release: bool = False) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"plugin.json is not readable JSON: {exc}"]

    # manifest fields and naming
    for field in ("name", "version", "description", "author"):
        if not manifest.get(field):
            errors.append(f"plugin.json is missing {field}")
    version = manifest.get("version", "")
    if version and not VERSION_PATTERN.fullmatch(version):
        errors.append(f"plugin.json version {version!r} is not x.y.z")
    name = manifest.get("name", "")
    if name and (not NAME_PATTERN.fullmatch(name) or name in RESERVED_NAMES or name.startswith(RESERVED_PREFIXES)):
        errors.append(f"plugin name {name!r} breaks the directory naming rules")
    if (repo / ".claude-plugin" / "marketplace.json").exists():
        errors.append(".claude-plugin/marketplace.json must not exist: the marketplace entry lives in tealun/tealun-plugins")

    # plugin.json lists exactly the skill folders, each a valid skill whose references exist
    skills = skill_paths(manifest)
    for s in manifest.get("skills", []):
        if not s.startswith("./") or ".." in s:
            errors.append(f"plugin.json skills path {s!r} must start with ./ and stay inside the plugin")
    on_disk = sorted(p.parent.relative_to(repo).as_posix() for p in repo.glob("skills/*/SKILL.md"))
    if sorted(skills) != on_disk:
        errors.append(f"skills differ: plugin.json {sorted(skills)} vs skill folders {on_disk}")
    for skill in skills:
        skill_md = repo / skill / "SKILL.md"
        if not skill_md.is_file():
            errors.append(f"{skill}/SKILL.md is missing")
            continue
        errors += _suite.check_skill(repo / skill)
        for ref in sorted(set(REFERENCE_PATTERN.findall(skill_md.read_text(encoding="utf-8")))):
            if not (repo / skill / ref).is_file():
                errors.append(f"{skill}/SKILL.md references missing file {ref}")

    icon = manifest.get("icon")
    if icon and not (repo / icon).is_file():
        errors.append(f"plugin.json icon {icon} does not exist")
    if not (repo / "LICENSE").is_file() and not manifest.get("license"):
        errors.append("no LICENSE file and no license in plugin.json")
    for doc in ("PRIVACY.md",):
        if not (repo / doc).is_file():
            errors.append(f"{doc} is missing; the directory's data questionnaire answers must match it")

    # README: the listing text
    for readme_name in ("README.md", "README.en.md"):
        readme = repo / readme_name
        if not readme.is_file():
            errors.append(f"{readme_name} is missing")
            continue
        text = readme.read_text(encoding="utf-8")
        if readme_name == "README.md":
            words = len(re.sub(r"```.*?```", "", text, flags=re.S).split())
            if words < README_MIN_WORDS:
                errors.append(f"README.md has {words} words outside code blocks; the directory needs {README_MIN_WORDS}")
        for n, line in enumerate(text.splitlines(), 1):
            if DOWNLOAD_AND_RUN.search(line):
                errors.append(f"{readme_name} line {n}: download-and-run install step; the directory shows it "
                              "to users as an install-time risk")

    # repository as stored: exportable byte for byte, no committed packages
    errors += content_rewriting_attributes(repo)
    errors += export_mismatches(repo)
    for f in tracked_files(repo):
        rel = f.relative_to(repo).as_posix()
        if f.suffix in (".zip", ".plugin"):
            errors.append(f"{rel}: packages are built by release.yml and attached to the Release, never committed")
        elif f.is_file() and not f.is_symlink() and f.suffix not in BINARY_SUFFIXES:
            text = f.read_bytes().decode("utf-8", "replace")
            for n, line in enumerate(text.splitlines(), 1):
                if SESSION_ID.search(line):
                    errors.append(f"{rel} line {n}: session link or session ID; this repository is public "
                                  "(AGENTS.md: no session IDs, private repository names or business arrangements)")
    # the package as the directory will see it on the plugin branch
    for rel, src in package_entries(repo)[1]:
        if src.is_symlink():
            errors.append(f"{rel} is a symlink; the directory refuses symlinks")
        elif src.stat().st_size > MAX_FILE_BYTES:
            errors.append(f"{rel} is over 5 MiB")

    # release path only (a tag, or the plugin-branch workflow): a minor version in development has no report yet
    if release or tag is not None:
        errors += release_audit(version, repo)

    if tag is not None:
        if tag != f"v{version}":
            errors.append(f"tag {tag} does not match plugin.json version {version} (expected v{version})")
        if not release_notes(version, repo):
            errors.append(f"CHANGELOG.md has no '## {NAME} {version}' section for the release notes")

    if since:
        diff = subprocess.run(["git", "-C", str(repo), "diff", "--quiet", since, "--", *skills],
                              capture_output=True, text=True)
        if diff.returncode not in (0, 1):
            errors.append(f"git diff against {since} failed: {diff.stderr.strip()}")
        elif diff.returncode == 1:
            previous = since.lstrip("v")
            if not VERSION_PATTERN.fullmatch(previous):
                errors.append(f"--since {since} is not a v<x.y.z> tag")
            elif VERSION_PATTERN.fullmatch(version) and version_tuple(version) <= version_tuple(previous):
                errors.append(f"the skill changed since {since} but plugin.json version {version} is not higher; "
                              "bump it (see the bump rule in AGENTS.md)")
    return errors


def release_audit(version: str, repo: Path = REPO) -> list[str]:
    """Every MAJOR.MINOR needs a written auditor report (lesson EV-20261103-001)."""
    if not VERSION_PATTERN.fullmatch(version or ""):
        return []
    minor = ".".join(version.split(".")[:2])
    if any((repo / "docs" / "99_audits").glob(f"*release_audit_v{minor}*.md")):
        return []
    return [f"no release audit report for {minor} in docs/99_audits; run the auditor skill and save its report "
            f"as docs/99_audits/99_NN_release_audit_v{minor}.0.md"]


def release_notes(version: str, repo: Path = REPO) -> str:
    """The body of the CHANGELOG section headed '## design-to-dev <version>'."""
    path = repo / "CHANGELOG.md"
    if not path.is_file():
        return ""
    m = re.search(rf"^## {re.escape(NAME)} {re.escape(version)}\b.*?\n(.*?)(?=^## |\Z)",
                  path.read_text(encoding="utf-8"), re.M | re.S)
    return m.group(1).strip() if m else ""


def content_rewriting_attributes(repo: Path) -> list[str]:
    errors = []
    for path in sorted(repo.rglob(".gitattributes")):
        if ".git" in path.relative_to(repo).parts[:-1]:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            fields = line.split("#", 1)[0].split()
            for attr in fields[1:]:
                attr_name = attr.split("=", 1)[0]
                if attr_name.startswith(("-", "!")) or attr_name == "binary":
                    continue
                if attr_name in REWRITING_ATTRIBUTES:
                    errors.append(f"{path.relative_to(repo)} line {n}: '{attr}' rewrites content on some "
                                  "platform; the plugin directory cannot validate the repository")
    if not (repo / ".gitattributes").is_file() or "* -text" not in (repo / ".gitattributes").read_text(encoding="utf-8"):
        errors.append(".gitattributes must contain '* -text' so no platform converts line endings")
    return errors


def export_mismatches(repo: Path) -> list[str]:
    """The directory validates the repository as exported; export the index with git archive
    and compare every file with what is stored."""
    run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True)
    tree = run("write-tree")
    if tree.returncode != 0:
        return []  # not a Git work tree: nothing is exported
    archive = run("archive", tree.stdout.decode().strip())
    if archive.returncode != 0:
        return [f"git archive failed: {archive.stderr.decode().strip()}"]
    exported = {}
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tf:
        for member in tf.getmembers():
            if member.isfile():
                exported[member.name] = tf.extractfile(member).read()
    errors = []
    listing = run("ls-files", "-z", "--cached").stdout.decode().split("\0")
    for path in filter(None, listing):
        stored = run("cat-file", "blob", f":{path}").stdout
        if path not in exported:
            errors.append(f"{path} is missing from the git export (export-ignore?)")
        elif exported[path] != stored:
            errors.append(f"{path} changes on git export (.gitattributes eol/filter rule)")
    return errors


def tracked_files(repo: Path) -> list[Path]:
    out = subprocess.run(["git", "-C", str(repo), "ls-files", "-z"], capture_output=True, text=True)
    if out.returncode != 0:
        return [f for f in repo.rglob("*") if f.is_file() and ".git" not in f.parts]
    return [repo / p for p in out.stdout.split("\0") if p and ((repo / p).is_symlink() or (repo / p).exists())]


def directory_warnings(repo: Path = REPO) -> list[str]:
    """Rules that hold a submission for a reviewer rather than block it, run over the package."""
    warnings: list[str] = []
    entries = package_entries(repo)[1]
    if len(entries) + 1 > MAX_FILES:
        warnings.append(f"{len(entries) + 1} files in the plugin; over {MAX_FILES} is held for review")
    for rel, src in entries:
        suffix = Path(rel).suffix.lower()
        if Path(rel).name in JUNK_NAMES:
            warnings.append(f"{rel}: remove OS junk files")
        elif suffix in HELD_SUFFIXES:
            warnings.append(f"{rel}: {suffix} files are held for a reviewer")
        elif suffix not in MEDIA_SUFFIXES and src.stat().st_size > MAX_TEXT_FILE_BYTES:
            warnings.append(f"{rel}: over 256 KiB is held for a reviewer")
    return warnings


def package_entries(repo: Path = REPO) -> tuple[dict, list[tuple[str, Path]]]:
    """(packaged manifest, [(path inside the package, source file)]) sorted."""
    manifest = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    entries: list[tuple[str, Path]] = []
    for skill in skill_paths(manifest):
        root = repo / skill
        for f in sorted(root.rglob("*")):
            inner = f.relative_to(root)
            if f.is_file() and not any(excluded(p) for p in inner.parts):
                entries.append((f"{skill}/{inner.as_posix()}", f))
    for extra in EXTRA_FILES:
        if (repo / extra).is_file():
            entries.append((extra, repo / extra))
    if manifest.get("icon"):
        icon = manifest["icon"][2:] if manifest["icon"].startswith("./") else manifest["icon"]
        if (repo / icon).is_file():
            entries.append((icon, repo / icon))
    return manifest, sorted(set(entries))


def read_normalized(src: Path) -> bytes:
    data = src.read_bytes()
    if src.suffix in _suite.TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    return data


def make_plugin(repo: Path = REPO) -> tuple[str, bytes]:
    manifest, entries = package_entries(repo)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        files = [(".claude-plugin/plugin.json", (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))]
        files += [(rel, read_normalized(src)) for rel, src in entries]
        for rel, data in sorted(files):
            info = zipfile.ZipInfo(rel, FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, data)
    return manifest["version"], buf.getvalue()


def build(repo: Path = REPO, dist: Path = DIST) -> Path:
    version, data = make_plugin(repo)
    out_dir = dist / NAME
    if out_dir.exists():
        shutil.rmtree(out_dir)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(out_dir)
    target = dist / f"{NAME}-{version}.plugin"
    target.write_bytes(data)
    # claude.ai documents uploading a plugin as a zip (Customize > Plugins > Add > Upload plugin).
    (dist / f"{NAME}-{version}.zip").write_bytes(data)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="run checks only, build nothing")
    parser.add_argument("--tag", help="release tag that must equal v<version>")
    parser.add_argument("--since", help="previous release tag; skill changes since it require a higher version")
    parser.add_argument("--release", action="store_true", help="also require the auditor report for this MAJOR.MINOR")
    parser.add_argument("--notes", metavar="FILE", help="write this version's CHANGELOG section to FILE and exit")
    args = parser.parse_args()
    if args.notes:
        version = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
        notes = release_notes(version)
        if not notes:
            print(f"CHANGELOG.md has no '## {NAME} {version}' section")
            return 1
        Path(args.notes).write_text(notes + "\n", encoding="utf-8")
        return 0
    errors = check(tag=args.tag, since=args.since, release=args.release)
    if errors:
        print("plugin check failed:\n  " + "\n  ".join(errors))
        return 1
    version = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"]
    audited = " and release audit" if args.release or args.tag else ""
    print(f"ok: {NAME} {version}: manifest, skill, README, repository export{audited}")
    for warning in directory_warnings():
        print(f"warning (directory review): {warning}")
    if args.check:
        return 0
    DIST.mkdir(exist_ok=True)
    target = build()
    print(f"wrote {target.relative_to(REPO)}, the same bytes as {target.with_suffix('.zip').name}, and dist/{NAME}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
