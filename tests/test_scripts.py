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


class VisualLint(ExampleOutput):
    """R-6: objective visual QA items are checked by the script, not self-graded."""

    def styles(self) -> Path:
        return self.out / "prototype" / "styles.css"

    def add_css(self, css: str) -> None:
        with self.styles().open("a", encoding="utf-8") as f:
            f.write("\n" + css + "\n")

    def warnings(self) -> str:
        return "\n".join(l for l in run("check_output.py", self.out).stdout.splitlines() if l.startswith("WARN"))

    def test_example_has_no_visual_warnings(self) -> None:
        self.assertEqual(self.warnings(), "")

    def test_tiny_text_is_flagged(self) -> None:
        self.add_css(".x { font-size: 9px; }")
        self.assertIn("9px", self.warnings())

    def test_decorative_tiny_text_is_allowed(self) -> None:
        self.add_css(".x { font-size: 9px; } /* decorative: cover texture */")
        self.assertEqual(self.warnings(), "")

    def test_off_scale_spacing_is_flagged(self) -> None:
        self.add_css(".x { padding: 6px 5px; }")
        self.assertIn("off the 4px scale", self.warnings())

    def test_too_many_weights_is_flagged(self) -> None:
        self.add_css(".a { font-weight: 300; } .b { font-weight: 800; } .c { font-weight: 900; }")
        self.assertIn("font weights", self.warnings())

    def test_animation_without_reduced_motion_is_flagged(self) -> None:
        text = self.styles().read_text(encoding="utf-8").replace("prefers-reduced-motion", "prefers-color-scheme")
        self.styles().write_text(text, encoding="utf-8")
        self.assertIn("prefers-reduced-motion", self.warnings())

    def test_system_display_font_is_flagged(self) -> None:
        css = self.out / "design-tokens" / "tokens.css"
        text = css.read_text(encoding="utf-8")
        import re
        text = re.sub(r"--font-family-display: [^;]+;", "--font-family-display: system-ui, sans-serif;", text)
        css.write_text(text, encoding="utf-8")
        run("tokens_json.py", css)
        self.assertIn("display", self.warnings())

    def test_missing_font_file_is_an_error(self) -> None:
        fonts = sorted((self.out / "prototype" / "fonts").glob("*.woff2"))
        self.assertTrue(fonts, "example should bundle its fonts")
        fonts[0].unlink()
        check = run("check_output.py", self.out)
        self.assertNotEqual(check.returncode, 0, check.stdout)
        self.assertIn(fonts[0].name, check.stdout)


def load_script(name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), SCRIPTS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FetchFonts(ExampleOutput):
    """F1-F5 (audit 99_03): failures must leave the bundled fonts untouched; inputs are validated first."""

    def proto(self) -> Path:
        return self.out / "prototype"

    def snapshot(self) -> dict:
        return {p.name: p.read_bytes() for p in (self.proto() / "fonts").iterdir()}

    def run_offline(self, *args: str) -> subprocess.CompletedProcess:
        import os
        env = dict(os.environ, HTTPS_PROXY="http://127.0.0.1:9", https_proxy="http://127.0.0.1:9")
        return subprocess.run([sys.executable, str(SCRIPTS / "fetch_fonts.py"), str(self.proto()), *args],
                              capture_output=True, text=True, env=env)

    def test_network_failure_keeps_existing_fonts(self) -> None:
        before = self.snapshot()
        result = self.run_offline("Noto Serif SC:700")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.snapshot(), before, "fonts folder changed after a failed download")
        self.assertEqual(run("check_output.py", self.out).returncode, 0)

    def test_bad_weight_is_rejected_before_anything_changes(self) -> None:
        before = self.snapshot()
        result = self.run_offline("Noto Serif SC:bold")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("weight", (result.stdout + result.stderr).lower())
        self.assertEqual(self.snapshot(), before)

    def test_missing_tokens_link_is_reported_before_download(self) -> None:
        index = self.proto() / "index.html"
        html = index.read_text(encoding="utf-8")
        index.write_text(html.replace('<link rel="stylesheet" href="fonts/fonts.css">', "")
                         .replace('<link rel="stylesheet" href="../design-tokens/tokens.css">', ""), encoding="utf-8")
        result = self.run_offline("Noto Serif SC:700")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("tokens.css", result.stdout + result.stderr)
        self.assertNotIn("cannot reach", result.stdout + result.stderr)

    def test_parent_folder_named_fonts_still_collects_text(self) -> None:
        module = load_script("fetch_fonts.py")
        nested = self.tmp / "fonts" / "inner" / "prototype"
        shutil.copytree(self.proto(), nested)
        (nested / "styles.css").write_text('.x::after { content: "篆"; }', encoding="utf-8")
        chars = module.used_characters(nested)
        self.assertIn("书", chars)
        self.assertIn("篆", chars, "text in CSS content should be subset too")


class VisualLintEdges(ExampleOutput):
    """V1-V6 (audit 99_03): no false alarms on positions, no misses on rem, negatives, shorthands, tokens, inline styles."""

    def lint(self, css: str = "", js: str = "") -> str:
        if css:
            with (self.out / "prototype" / "styles.css").open("a", encoding="utf-8") as f:
                f.write("\n" + css + "\n")
        if js:
            with (self.out / "prototype" / "pages.js").open("a", encoding="utf-8") as f:
                f.write("\n" + js + "\n")
        return "\n".join(l for l in run("check_output.py", self.out).stdout.splitlines() if l.startswith("WARN"))

    def test_positions_are_not_spacing(self) -> None:
        self.assertEqual(self.lint(".x { position: absolute; top: 7px; left: 3px; }"), "")

    def test_negative_rem_and_grid_gap_are_checked(self) -> None:
        out = self.lint(".a { margin-top: -6px; } .b { padding: 0.35rem; } .c { grid-gap: 10px; }")
        self.assertIn("-6px", out)
        self.assertIn("0.35rem", out)
        self.assertIn("10px", out)

    def test_small_text_via_rem_shorthand_and_token(self) -> None:
        css = self.out / "design-tokens" / "tokens.css"
        css.write_text(css.read_text(encoding="utf-8").replace("--font-size-xs: 12px;", "--font-size-xs: 10px;"), encoding="utf-8")
        run("tokens_json.py", css)
        out = self.lint(".a { font-size: 0.6rem; } .b { font: 600 10px/1.2 serif; }")
        self.assertIn("0.6rem", out)
        self.assertIn("font: 10px", out)
        self.assertIn("--font-size-xs", out)

    def test_weights_resolve_fallbacks_and_keywords(self) -> None:
        out = self.lint(".a { font-weight: var(--font-weight-bold, 700); } .b { font-weight: bold; }")
        self.assertEqual(out, "", "700, bold and var(--font-weight-bold) are one weight")

    def test_exemption_covers_one_declaration(self) -> None:
        out = self.lint(".t { padding: 6px; font-size: 9px; /* decorative: sheen */ }")
        self.assertIn("6px", out)
        self.assertNotIn("9px", out)

    def test_display_alias_to_system_font_is_resolved(self) -> None:
        css = self.out / "design-tokens" / "tokens.css"
        import re
        text = re.sub(r"--font-family-display: [^;]+;", "--font-family-display: var(--font-family-system);", css.read_text(encoding="utf-8"))
        text = text.replace(":root {", ':root {\n  --font-family-system: "PingFang SC", sans-serif; /* indicative · test */', 1)
        css.write_text(text, encoding="utf-8")
        run("tokens_json.py", css)
        self.assertIn("display font", self.lint())

    def test_inline_styles_are_checked(self) -> None:
        self.assertIn("pages.js", self.lint(js="var x = '<p style=\"font-size:9px;padding:6px\">x</p>';"))

    def test_url_on_line_does_not_hide_inline_color(self) -> None:  # N-01
        self.lint(js="var x = '<a href=\"https://example.com\" style=\"color:#ff0000\">x</a>';")
        check = run("check_output.py", self.out)
        self.assertNotEqual(check.returncode, 0, check.stdout)
        self.assertIn("#ff0000", check.stdout)


class PaletteInputs(unittest.TestCase):
    """N-02, F-07, F-08 (audits 99_01-99_03)."""

    def test_rows_bad_argument_is_a_usage_error(self) -> None:
        r = run("palette.py", REPO / "docs" / "images" / "readlog.png", "--rows", "abc")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)
        self.assertIn("--rows", r.stdout + r.stderr)

    def test_named_color_is_a_usage_error(self) -> None:
        r = run("palette.py", "--contrast", "white", "#000000")
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_alpha_needs_a_backdrop(self) -> None:
        r = run("palette.py", "--contrast", "#ffffff", "#2f6f4f66")
        self.assertEqual(r.returncode, 2, r.stdout)
        r = run("palette.py", "--contrast", "#ffffff", "#2f6f4f66", "--over", "#ffffff")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("1.", r.stdout)  # white text on a pale composite fails badly

    def test_large_image_memory(self) -> None:
        import resource
        import struct
        import zlib
        tmp = Path(tempfile.mkdtemp())
        try:
            w, h = 2880, 4000
            row = b"\x00" + b"\xfa\xfa\xfa" * w
            raw = zlib.compress(row * h, 6)
            def chunk(kind, data):
                return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
            png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")
            (tmp / "big.png").write_bytes(png)
            before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            r = run("palette.py", tmp / "big.png", "--top", "2")
            self.assertEqual(r.returncode, 0, r.stderr)
            peak_mb = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
            self.assertLess(peak_mb, 400, f"palette.py peaked at {peak_mb:.0f} MB on a 2880x4000 image")
        finally:
            shutil.rmtree(tmp)


class ExampleInSync(unittest.TestCase):
    """The example must not drift from the templates it claims to use (found in audit 99_03 follow-up)."""

    def test_readlog_base_styles_match_template(self) -> None:
        marker = "/* ---------- page styles ---------- */"
        template = (SCRIPTS.parent / "templates" / "styles.css").read_text(encoding="utf-8")
        example = (EXAMPLE / "prototype" / "styles.css").read_text(encoding="utf-8")
        self.assertEqual(example.split(marker)[0], template.split(marker)[0],
                         "copy templates/styles.css (up to the page styles marker) into the Readlog styles.css")

    def test_readlog_kit_matches_template(self) -> None:
        self.assertEqual((EXAMPLE / "prototype" / "proto-kit.js").read_bytes(),
                         (SCRIPTS.parent / "templates" / "proto-kit.js").read_bytes())


class ReleaseAuditGate(unittest.TestCase):
    """A release needs a written auditor report for its MAJOR.MINOR (lesson EV-20261103-001)."""

    def setUp(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("build", REPO / "scripts" / "build.py")
        self.build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.build)

    def test_current_version_has_a_report(self) -> None:
        errors: list[str] = []
        self.build.check_release_audit("1.3.1", REPO / "docs" / "99_audits", errors)
        self.assertEqual(errors, [])

    def test_unaudited_minor_version_fails(self) -> None:
        errors: list[str] = []
        self.build.check_release_audit("1.4.0", REPO / "docs" / "99_audits", errors)
        self.assertTrue(errors and "1.4" in errors[0], errors)


if __name__ == "__main__":
    unittest.main()
