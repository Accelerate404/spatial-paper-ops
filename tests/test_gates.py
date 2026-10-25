#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_gates.py — self-tests for the gate scripts

Focus: exit-code semantics and the criteria that are easy to get wrong
(ID sets vs counts, nested replacement, waiver expiry, config rejection).
Everything runs in temporary directories.

Usage:
    python tests/test_gates.py          # or: python -m unittest discover tests
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
sys.path.insert(0, HERE)

from run_demo import make_png  # noqa: E402


def run(script: str, args: list[str], cwd: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, os.path.join(ASSETS, script), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class TempDirCase(unittest.TestCase):
    def setUp(self) -> None:
        self.root = tempfile.mkdtemp(prefix="spo_test_")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def p(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)


class TestRecon(TempDirCase):
    def test_identical_files_pass(self):
        write(self.p("a.md"), "value 15.5 and 70.2 percent, see 图1 and Figure 2.\n")
        shutil.copy(self.p("a.md"), self.p("b.md"))
        code, out = run("recon_numeric.py", ["a.md", "b.md"], self.root)
        self.assertEqual(code, 0, out)

    def test_decimal_drift_fails(self):
        write(self.p("a.md"), "shift is 15.5 km.\n")
        write(self.p("b.md"), "shift is 15.4 km.\n")
        code, out = run("recon_numeric.py", ["a.md", "b.md"], self.root)
        self.assertEqual(code, 1, out)

    def test_bilingual_caption_id_counts_are_ignored(self):
        """Bilingual captions extract each ID twice; ID sets still match, so PASS.
        This is the core reason IDs are compared as sets, not counts."""
        write(self.p("a.md"), "**（图1）研究区。** / **Fig. 1 Study area.**\n\n见（图1）。\n")
        write(self.p("b.md"), "**Figure 1 Study area.**\n\nSee Figure 1.\n")
        code, out = run("recon_numeric.py", ["a.md", "b.md"], self.root)
        self.assertEqual(code, 0, out)

    def test_missing_id_in_set_fails(self):
        write(self.p("a.md"), "见（图1）与（图2）。\n")
        write(self.p("b.md"), "See Figure 1.\n")
        code, out = run("recon_numeric.py", ["a.md", "b.md"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("only on left", out)

    def test_registered_exception_is_honoured(self):
        write(self.p("a.md"), "population 1449.8 wan.\n")
        write(self.p("b.md"), "population 14.498 million.\n")
        code, out = run(
            "recon_numeric.py",
            ["a.md", "b.md", "--exceptions", "1449.8=14.498"],
            self.root,
        )
        self.assertEqual(code, 0, out)


class TestFigures(TempDirCase):
    def setUp(self):
        super().setUp()
        os.makedirs(self.p("figures"), exist_ok=True)

    def test_valid_figures_pass(self):
        for i in (1, 2):
            make_png(self.p("figures", f"Fig0{i}_Panel.png"))
        code, out = run("check_figures.py", ["figures", "--expect", "2"], self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("300", out)

    def test_write_residue_is_a_hard_failure(self):
        make_png(self.p("figures", "Fig01_Panel.png"))
        open(self.p("figures", ".Fig01_Panel.png.ab12cd.png"), "wb").close()
        code, out = run("check_figures.py", ["figures", "--expect", "1"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("write residue", out)

    def test_residue_is_not_counted_as_a_figure(self):
        """The placeholder must not inflate the count guard."""
        make_png(self.p("figures", "Fig01_Panel.png"))
        open(self.p("figures", ".Fig01_Panel.png.ab12cd.png"), "wb").close()
        code, out = run("check_figures.py", ["figures", "--expect", "1"], self.root)
        self.assertNotIn("body figure count", out)

    def test_wrong_count_fails(self):
        make_png(self.p("figures", "Fig01_Panel.png"))
        code, out = run("check_figures.py", ["figures", "--expect", "7"], self.root)
        self.assertEqual(code, 1, out)

    def test_undersized_width_fails(self):
        make_png(self.p("figures", "Fig01_Panel.png"), width=1200)
        code, out = run("check_figures.py", ["figures", "--expect", "1"], self.root)
        self.assertEqual(code, 1, out)


class TestText(TempDirCase):
    def test_clean_markdown_passes(self):
        write(self.p("m.md"), "# Title\n\nBody text with 70.2 percent and $x$ inline.\n")
        code, out = run("check_text.py", ["m.md"], self.root)
        self.assertEqual(code, 0, out)

    def test_heading_colon_fails(self):
        write(self.p("m.md"), "# Results: spatial pattern\n\nBody.\n")
        code, out = run("check_text.py", ["m.md"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("colon", out)

    def test_curly_quote_fails(self):
        write(self.p("m.md"), '# Title\n\nHe said \u201cok\u201d.\n')
        code, out = run("check_text.py", ["m.md"], self.root)
        self.assertEqual(code, 1, out)

    def test_inline_bold_is_advisory_by_default(self):
        write(self.p("m.md"), "# Title\n\nThis is **emphasised** text.\n")
        code, out = run("check_text.py", ["m.md"], self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)

    def test_inline_bold_is_fatal_under_strict(self):
        write(self.p("m.md"), "# Title\n\nThis is **emphasised** text.\n")
        code, out = run("check_text.py", ["m.md", "--strict"], self.root)
        self.assertEqual(code, 1, out)

    def test_caption_bold_is_exempt(self):
        write(self.p("m.md"), "# Title\n\n**（图1）研究区。** / **Fig. 1 Study area.**\n")
        code, out = run("check_text.py", ["m.md", "--strict"], self.root)
        self.assertEqual(code, 0, out)

    def test_line_ending_mismatch_fails(self):
        with open(self.p("m.md"), "wb") as f:
            f.write(b"# Title\r\n\r\nBody.\r\n")
        code, out = run("check_text.py", ["m.md", "--md-eol", "lf"], self.root)
        self.assertEqual(code, 1, out)


class TestSafeReplace(TempDirCase):
    def test_plain_replacement_removes_old(self):
        write(self.p("m.md"), "alpha beta alpha\n")
        code, _ = run("safe_replace.py", ["m.md", "--old", "alpha", "--new", "gamma"], self.root)
        self.assertEqual(code, 0)
        with open(self.p("m.md"), encoding="utf-8") as f:
            self.assertEqual(f.read().count("alpha"), 0)

    def test_nested_replacement_uses_count_equality(self):
        """NEW contains OLD: the old string never reaches zero, and that is fine."""
        write(self.p("m.md"), "constraint boundary appears twice: constraint boundary\n")
        code, out = run(
            "safe_replace.py",
            ["m.md", "--old", "constraint boundary", "--new", "spatial constraint boundary"],
            self.root,
        )
        self.assertEqual(code, 0, out)
        with open(self.p("m.md"), encoding="utf-8") as f:
            body = f.read()
        self.assertEqual(body.count("spatial constraint boundary"), 2)
        self.assertEqual(body.count("constraint boundary"), 2)

    def test_missing_old_string_fails(self):
        write(self.p("m.md"), "nothing here\n")
        code, _ = run("safe_replace.py", ["m.md", "--old", "absent", "--new", "x"], self.root)
        self.assertEqual(code, 1)

    def test_declared_expect_mismatch_fails(self):
        write(self.p("m.md"), "a a\n")
        code, _ = run(
            "safe_replace.py", ["m.md", "--old", "a", "--new", "b", "--expect", "5"], self.root
        )
        self.assertEqual(code, 1)

    def test_crlf_preserved(self):
        with open(self.p("m.md"), "wb") as f:
            f.write(b"line one\r\nline two\r\n")
        code, _ = run("safe_replace.py", ["m.md", "--old", "line", "--new", "row"], self.root)
        self.assertEqual(code, 0)
        with open(self.p("m.md"), "rb") as f:
            raw = f.read()
        self.assertEqual(raw.count(b"\r\n"), 2)
        self.assertEqual(raw.count(b"\n") - raw.count(b"\r\n"), 0)


class TestGate(TempDirCase):
    def _project(self, waiver: str = "") -> None:
        os.makedirs(self.p("figures"), exist_ok=True)
        make_png(self.p("figures", "Fig01_Panel.png"))
        write(self.p("m.md"), "# Title\n\nBody.\n")
        write(
            self.p("gate.toml"),
            '[defaults.figures]\nfig_dir = "figures"\nexpect = 1\nwidth = 2244\n\n'
            '[defaults.text]\nmd_eol = "lf"\npy_eol = "lf"\n\n'
            '[[text]]\nname = "main"\npaths = ["m.md"]\n' + waiver,
        )

    def test_clean_project_passes(self):
        self._project()
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 0, out)

    def test_unknown_key_exits_2(self):
        self._project("expectt = 3\n")
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 2, out)
        self.assertIn("unknown", out)

    def test_missing_config_exits_2(self):
        code, out = run("gate.py", ["--config", "nope.toml"], self.root)
        self.assertEqual(code, 2, out)

    def test_failure_exits_1(self):
        self._project()
        write(self.p("m.md"), "# Results: bad\n\nBody.\n")
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 1, out)

    def test_active_waiver_turns_failure_into_pass(self):
        self._project(
            '\n[[waiver]]\ntarget = "text"\nreason = "known issue"\nuntil = "2999-01-01"\n'
        )
        write(self.p("m.md"), "# Results: bad\n\nBody.\n")
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 0, out)
        self.assertIn("waived", out)

    def test_expired_waiver_restores_failure(self):
        self._project(
            '\n[[waiver]]\ntarget = "text"\nreason = "expired"\nuntil = "2020-01-01"\n'
        )
        write(self.p("m.md"), "# Results: bad\n\nBody.\n")
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 1, out)
        self.assertIn("expired", out)

    def test_waiver_without_until_is_a_config_error(self):
        self._project('\n[[waiver]]\ntarget = "text"\nreason = "no expiry"\n')
        code, out = run("gate.py", ["--config", "gate.toml"], self.root)
        self.assertEqual(code, 2, out)
        self.assertIn("until", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
