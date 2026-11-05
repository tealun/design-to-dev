"""Tests for scripts/build_plugin.py and scripts/build_suite.py, run on a temporary Git copy of the
repository. Each rule has a case that must be reported and a case that must pass (AGENTS.md).
Run: python3 -m unittest discover -s tests
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IGNORE = shutil.ignore_patterns(".git", "dist", "node_modules", "__pycache__", "*.pyc")


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bp = load("build_plugin")
bs = load("build_suite")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


class RepoCopy(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = self.tmp / "repo"
        shutil.copytree(REPO, self.repo, ignore=IGNORE)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "t")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "base")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def commit(self, message: str = "change") -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", message)

    def manifest(self) -> dict:
        return json.loads((self.repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))

    def write_manifest(self, data: dict) -> None:
        (self.repo / ".claude-plugin" / "plugin.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def errors(self, **kw) -> list[str]:
        return bp.check(self.repo, **kw)

    def assertReported(self, needle: str, **kw) -> None:
        errs = self.errors(**kw)
        self.assertTrue(any(needle in e for e in errs), f"expected '{needle}' in {errs}")


class PublicRepository(RepoCopy):
    """The repository is public: no session links or IDs in tracked files (AGENTS.md)."""

    def test_session_link_is_reported(self) -> None:
        note = self.repo / "docs" / "note.md"
        note.write_text("See https://claude.ai/code/" + "session_" + "01ABCDEFGHIJKLMNOPQRSTUV\n", encoding="utf-8")
        self.commit()
        self.assertReported("docs/note.md line 1: session link")

    def test_bare_session_id_is_reported(self) -> None:
        (self.repo / "docs" / "note.md").write_text("from " + "session_" + "01ABCDEFGHIJKLMNOPQRSTUV\n", encoding="utf-8")
        self.commit()
        self.assertReported("docs/note.md line 1: session link")

    def test_ordinary_session_wording_passes(self) -> None:
        (self.repo / "docs" / "note.md").write_text("Each session starts with a question; sessionStorage is not used.\n", encoding="utf-8")
        self.commit()
        self.assertEqual(self.errors(), [])


class PluginCheck(RepoCopy):
    def test_repository_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_marketplace_json_is_refused(self) -> None:
        (self.repo / ".claude-plugin" / "marketplace.json").write_text("{}", encoding="utf-8")
        self.assertReported("marketplace.json must not exist")

    def test_skill_list_must_match_skill_folders(self) -> None:
        m = self.manifest()
        m["skills"] = []
        self.write_manifest(m)
        self.assertReported("skills differ")

    def test_skills_path_needs_dot_slash(self) -> None:
        m = self.manifest()
        m["skills"] = ["skills/design-to-dev"]
        self.write_manifest(m)
        self.assertReported("must start with ./")

    def test_missing_reference_file(self) -> None:
        (self.repo / "skills/design-to-dev/references/intake.md").unlink()
        self.assertReported("intake.md")

    def test_version_only_in_plugin_json(self) -> None:
        skill = self.repo / "skills/design-to-dev/SKILL.md"
        skill.write_text(skill.read_text(encoding="utf-8").replace("  author: Tealun\n", '  author: Tealun\n  version: "1.0.0"\n'), encoding="utf-8")
        self.assertReported("metadata.version is not allowed")

    def test_naming_rules(self) -> None:
        for bad in ("claude-designer", "test", "Design"):
            m = self.manifest()
            m["name"] = bad
            self.write_manifest(m)
            self.assertReported("naming rules")

    def test_tag_must_match_version_and_have_notes(self) -> None:
        version = self.manifest()["version"]
        minor = ".".join(version.split(".")[:2])
        (self.repo / "docs" / "99_audits" / f"99_99_release_audit_v{minor}.0.md").write_text("report\n", encoding="utf-8")
        self.assertEqual(self.errors(tag=f"v{version}"), [])
        self.assertReported("does not match", tag="v0.0.1")
        log = self.repo / "CHANGELOG.md"
        log.write_text(re.sub(rf"^## design-to-dev {re.escape(version)}.*$", "## something else", log.read_text(encoding="utf-8"), flags=re.M), encoding="utf-8")
        self.assertReported("no '## design-to-dev", tag=f"v{version}")

    def test_skill_change_needs_version_bump(self) -> None:
        git(self.repo, "tag", "v1.4.0")
        version = self.manifest()["version"]
        git(self.repo, "tag", f"v{version}") if version != "1.4.0" else None
        skill = self.repo / "skills/design-to-dev/references/intake.md"
        skill.write_text(skill.read_text(encoding="utf-8") + "\nOne more line.\n", encoding="utf-8")
        self.commit()
        self.assertReported("is not higher", since=f"v{version}")
        m = self.manifest()
        major, minor, patch = (int(x) for x in version.split("."))
        m["version"] = f"{major}.{minor}.{patch + 1}"
        self.write_manifest(m)
        self.assertEqual([e for e in self.errors(since=f"v{version}") if "not higher" in e], [])

    def test_unchanged_skill_needs_no_bump(self) -> None:
        version = self.manifest()["version"]
        git(self.repo, "tag", f"v{version}")
        (self.repo / "docs" / "note.md").write_text("docs only\n", encoding="utf-8")
        self.commit()
        self.assertEqual(self.errors(since=f"v{version}"), [])

    def test_gitattributes_must_not_rewrite_content(self) -> None:
        (self.repo / ".gitattributes").write_text("* -text\n*.md text eol=crlf\n", encoding="utf-8")
        self.assertReported("rewrites content")
        (self.repo / ".gitattributes").write_text("* text=auto\n", encoding="utf-8")
        self.assertReported("must contain '* -text'")

    def test_export_must_match_stored_content(self) -> None:
        (self.repo / ".gitattributes").write_text("* -text\nREADME.md export-ignore\n", encoding="utf-8")
        self.commit()
        self.assertReported("missing from the git export")

    def test_readme_download_and_run_rejected(self) -> None:
        for line in ("curl -fsSL https://x.sh | sh", "npx skills add tealun/design-to-dev", "git clone https://github.com/x/y"):
            readme = self.repo / "README.md"
            original = readme.read_text(encoding="utf-8")
            readme.write_text(original + f"\n{line}\n", encoding="utf-8")
            self.assertReported("download-and-run")
            readme.write_text(original, encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_committed_package_rejected(self) -> None:
        (self.repo / "design-to-dev.zip").write_bytes(b"PK\x05\x06" + b"\0" * 18)
        self.commit()
        self.assertReported("never committed")

    def test_release_audit_required_per_minor(self) -> None:
        m = self.manifest()
        m["version"] = "9.9.0"
        self.write_manifest(m)
        self.assertReported("no release audit report for 9.9", release=True)
        self.assertEqual([e for e in self.errors() if "release audit" in e], [], "development checks must not need the report")

    def test_missing_privacy_policy(self) -> None:
        (self.repo / "PRIVACY.md").unlink()
        self.assertReported("PRIVACY.md is missing")

    def test_build_is_reproducible_and_scoped(self) -> None:
        v1, a = bp.make_plugin(self.repo)
        v2, b = bp.make_plugin(self.repo)
        self.assertEqual(a, b)
        with zipfile.ZipFile(io.BytesIO(a)) as zf:
            names = zf.namelist()
        tops = {n.split("/")[0] for n in names}
        self.assertEqual(tops, {".claude-plugin", "skills", "README.md", "LICENSE", "PRIVACY.md", "assets", "docs"})
        self.assertIn("docs/images/readlog.png", names)
        self.assertFalse([n for n in names if n.startswith(("scripts/", "tests/", ".github/", "examples/")) or n in ("AGENTS.md", "CLAUDE.md")])
        self.assertIn("skills/design-to-dev/SKILL.md", names)
        self.assertFalse(bp.directory_warnings(self.repo), "package should need no manual review")


class WorkBuddyPackage(RepoCopy):
    def build(self):
        errors, version, wb_raw, entries = bs.check(self.repo)
        return errors, version, wb_raw, entries

    def test_repository_passes_and_injects_version(self) -> None:
        errors, version, wb_raw, entries = self.build()
        self.assertEqual(errors, [])
        data = bs.make_zip(entries, "design-to-dev/", wb_raw, version, self.repo / "skills/design-to-dev")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            skill = zf.read("design-to-dev/SKILL.md").decode("utf-8")
            names = zf.namelist()
        import yaml
        fm = yaml.safe_load(re.match(r"^---\n(.*?)\n---\n", skill, re.S).group(1))
        self.assertEqual(fm["version"], self.manifest()["version"])
        self.assertEqual(fm["name"], "design-to-dev")
        self.assertTrue(all(fm.get(k) for k in bs.WB_REQUIRED))
        self.assertEqual([n for n in names if n.lower().endswith("skill.md")], ["design-to-dev/SKILL.md"])

    def test_second_skill_md_rejected(self) -> None:
        (self.repo / "skills/design-to-dev/references/SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        self.assertTrue(any("exactly one SKILL.md" in e for e in self.build()[0]))

    def test_frontmatter_in_other_markdown_rejected(self) -> None:
        (self.repo / "skills/design-to-dev/references/extra.md").write_text("---\nname: other\n---\ntext\n", encoding="utf-8")
        self.assertTrue(any("second skill" in e for e in self.build()[0]))

    def test_bom_rejected(self) -> None:
        p = self.repo / "skills/design-to-dev/references/intake.md"
        p.write_bytes(b"\xef\xbb\xbf" + p.read_bytes())
        self.assertTrue(any("BOM" in e for e in self.build()[0]))

    def test_depth_rejected(self) -> None:
        deep = self.repo / "skills/design-to-dev/templates/deep"
        deep.mkdir()
        (deep / "a.js").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("deeper than" in e for e in self.build()[0]))

    def test_field_limits(self) -> None:
        wb = self.repo / "workbuddy.yaml"
        text = wb.read_text(encoding="utf-8")
        wb.write_text(text.replace('display_name_en: "', 'display_name_en: "' + "x" * 70), encoding="utf-8")
        self.assertTrue(any("display_name_en" in e for e in self.build()[0]))
        wb.write_text(text + "version: 1.0.0\n", encoding="utf-8")
        self.assertTrue(any("must not carry version" in e for e in self.build()[0]))
        wb.write_text(text.replace("examples_en:\n", 'examples_en:\n  - "one more"\n'), encoding="utf-8")
        self.assertTrue(any("examples_en has 4" in e for e in self.build()[0]))


class ReleaseGatesInSync(unittest.TestCase):
    """Both tag workflows publish to users, so plugin-branch.yml runs every gate release.yml runs (audit 99_04 A-01)."""

    GATES = ("build_suite.py --check", "check_ledger.py", "unittest discover", "check_output.py", "build_plugin.py --check --tag")

    @staticmethod
    def missing(plugin_branch: str, release: str) -> list[str]:
        return [g for g in ReleaseGatesInSync.GATES if g in release and g not in plugin_branch]

    def read(self, name: str) -> str:
        return (REPO / ".github" / "workflows" / name).read_text(encoding="utf-8")

    def test_plugin_branch_has_every_release_gate(self) -> None:
        release = self.read("release.yml")
        self.assertEqual([g for g in self.GATES if g not in release], [], "release.yml lost a gate")
        self.assertEqual(self.missing(self.read("plugin-branch.yml"), release), [])

    def test_a_dropped_gate_is_reported(self) -> None:
        weakened = self.read("plugin-branch.yml").replace("python3 -m unittest discover -s tests", "true")
        self.assertEqual(self.missing(weakened, self.read("release.yml")), ["unittest discover"])

    def test_manual_run_publishes_only_a_released_tag(self) -> None:
        text = self.read("plugin-branch.yml")
        self.assertIn('git checkout --quiet "refs/tags/v$version"', text)
        self.assertIn("is not released yet", text)


class ReleaseFromWebsite(unittest.TestCase):
    """A release published on the GitHub website already exists when release.yml runs; it must be filled, not recreated."""

    def test_existing_release_gets_the_packages(self) -> None:
        text = (REPO / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn('gh release view "$GITHUB_REF_NAME"', text)
        self.assertIn('gh release upload "$GITHUB_REF_NAME" "${assets[@]}" --clobber', text)
        self.assertIn("gh release create", text)


if __name__ == "__main__":
    unittest.main()
