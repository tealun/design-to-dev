"""Regression tests for the skill's Python scripts. Run: python3 -m unittest discover -s tests"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "skills" / "design-to-dev" / "scripts"
EXAMPLE = REPO / "examples" / "readlog" / "output"


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)], capture_output=True, text=True)


class ExampleOutput(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "output"
        shutil.copytree(EXAMPLE, self.out)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def css(self) -> Path:
        return self.out / "design-tokens" / "tokens.css"


class TokenParsing(ExampleOutput):
    """F-02: tokens must never be dropped silently."""

    def test_second_root_block_is_rejected(self) -> None:
        with self.css().open("a", encoding="utf-8") as f:
            f.write("@media (prefers-color-scheme: dark) {\n  :root {\n    --color-bg: #111111; /* tbd · dark */\n  }\n}\n")
        gen = run("tokens_json.py", self.css())
        self.assertNotEqual(gen.returncode, 0, gen.stdout)
        self.assertIn(":root", gen.stdout + gen.stderr)
        check = run("check_output.py", self.out, "--mode", "B")
        self.assertNotEqual(check.returncode, 0, check.stdout)

    def test_non_lowercase_name_is_rejected(self) -> None:
        text = self.css().read_text(encoding="utf-8").replace(
            "--color-danger: #b3261e;", "--color-danger: #b3261e;\n  --colorAccentDark: #000000;")
        self.css().write_text(text, encoding="utf-8")
        gen = run("tokens_json.py", self.css())
        self.assertNotEqual(gen.returncode, 0, gen.stdout)
        self.assertIn("colorAccentDark", gen.stdout + gen.stderr)
        check = run("check_output.py", self.out, "--mode", "B")
        self.assertNotEqual(check.returncode, 0, check.stdout)
        self.assertIn("colorAccentDark", check.stdout)

    def test_example_still_passes(self) -> None:
        self.assertEqual(run("tokens_json.py", self.css(), "--stdout").returncode, 0)
        check = run("check_output.py", self.out, "--mode", "B")
        self.assertEqual(check.returncode, 0, check.stdout)


class ModeBBrief(ExampleOutput):
    """F-03: a mode B handoff must not pass without a filled PLANNER_BRIEF.md, even without --mode."""

    def test_missing_brief_fails_without_flag(self) -> None:
        (self.out / "PLANNER_BRIEF.md").unlink()
        check = run("check_output.py", self.out)
        self.assertNotEqual(check.returncode, 0, check.stdout)
        self.assertIn("PLANNER_BRIEF.md", check.stdout)

    def test_mode_a_handoff_does_not_need_brief(self) -> None:
        (self.out / "PLANNER_BRIEF.md").unlink()
        handoff = self.out / "HANDOFF.md"
        text = handoff.read_text(encoding="utf-8").replace(
            "| 交接对象 Handoff to | B：设计师继续开发", "| 交接对象 Handoff to | A：交给开发者")
        handoff.write_text(text, encoding="utf-8")
        check = run("check_output.py", self.out)
        self.assertEqual(check.returncode, 0, check.stdout)


class RawColorCheck(ExampleOutput):
    """F-06: ids, anchors and spec notes are not raw colors; real colors in code still are."""

    def pages(self) -> Path:
        return self.out / "prototype" / "pages.js"

    def append(self, text: str) -> None:
        with self.pages().open("a", encoding="utf-8") as f:
            f.write(text)

    def test_ids_anchors_and_notes_pass(self) -> None:
        self.append("\nvar probe = document.querySelector('#bad'); var link = '<a href=\"#add\">x</a>';\n"
                    "var note = '<p data-spec=\"tbd\" data-spec-note=\"Reference grey #8f8f8f fails AA\">x</p>';\n")
        check = run("check_output.py", self.out)
        self.assertEqual(check.returncode, 0, check.stdout)

    def test_inline_style_color_still_fails(self) -> None:
        self.append("\nvar bad = '<p style=\"color:#ff0000\">x</p>';\n")
        check = run("check_output.py", self.out)
        self.assertNotEqual(check.returncode, 0, check.stdout)
        self.assertIn("#ff0000", check.stdout)


if __name__ == "__main__":
    unittest.main()
