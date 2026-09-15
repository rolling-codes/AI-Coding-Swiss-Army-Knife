"""Unit tests for the lean-code checkers. Stdlib unittest, no network, hermetic.

Run from the scripts/ directory:  python -m unittest discover -v
"""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import complexity_check as cc  # noqa: E402
import lean_check  # noqa: E402
import verify_deps as vd  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def kinds(violations):
    return {v.kind for v in violations}


@contextlib.contextmanager
def project(files):
    """A temp dir with a .git marker (so manifest walk stops here) and given files."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".git").mkdir()
        for name, content in files.items():
            (root / name).write_text(content, encoding="utf-8")
        yield root


class ComplexityTests(unittest.TestCase):

    def test_clean_python_has_no_violations(self):
        violations, note = cc.analyze_file(FIXTURES / "clean_sample.py", cc.DEFAULTS)
        self.assertEqual(violations, [])
        self.assertIsNone(note)

    def test_bad_python_flags_all_three(self):
        violations, _ = cc.analyze_file(FIXTURES / "bad_complexity.py", cc.DEFAULTS)
        self.assertEqual(
            kinds(violations),
            {"function-length", "nesting-depth", "cyclomatic"})

    def test_file_length_violation(self):
        with project({"big.py": "x = 1\n" * 12}) as root:
            limits = dict(cc.DEFAULTS, file_lines=5)
            violations, _ = cc.analyze_file(root / "big.py", limits)
            self.assertIn("file-length", kinds(violations))

    def test_syntax_error_is_graceful(self):
        with project({"broken.py": "def (:\n"}) as root:
            violations, note = cc.analyze_file(root / "broken.py", cc.DEFAULTS)
            self.assertEqual(violations, [])
            self.assertIn("syntax error", note)

    def test_unsupported_extension_skipped(self):
        with project({"notes.txt": "hello\n"}) as root:
            violations, note = cc.analyze_file(root / "notes.txt", cc.DEFAULTS)
            self.assertEqual(violations, [])
            self.assertIn("unsupported", note)

    def test_unreadable_file_is_graceful(self):
        violations, note = cc.analyze_file(FIXTURES / "does_not_exist.py", cc.DEFAULTS)
        self.assertEqual(violations, [])
        self.assertIn("unreadable", note)

    def test_brace_heuristic_function_length(self):
        limits = dict(cc.DEFAULTS, func_lines=15)
        violations, note = cc.analyze_file(FIXTURES / "sample_long.js", limits)
        self.assertEqual(note, "heuristic")
        self.assertIn("function-length", kinds(violations))

    def test_strip_noise_preserves_line_count(self):
        src = '// a { brace }\nconst s = "text { with } braces";\n/* x\ny */\ncode\n'
        cleaned = cc.strip_noise(src)
        self.assertEqual(src.count("\n"), cleaned.count("\n"))
        self.assertNotIn("with", cleaned)


class DepsTests(unittest.TestCase):

    def test_python_stdlib_declared_unknown(self):
        src = "import os\nimport requests\nimport totally_fake_pkg\n"
        with project({"requirements.txt": "requests>=2\n", "app.py": src}) as root:
            result = vd.analyze_file(root / "app.py", use_registry=False)
            status = {i["name"]: i["status"] for i in result["imports"]}
            self.assertEqual(status["os"], "stdlib")
            self.assertEqual(status["requests"], "declared")
            self.assertEqual(status["totally_fake_pkg"], "unknown")

    def test_python_alias_resolves(self):
        with project({"requirements.txt": "pyyaml\n", "a.py": "import yaml\n"}) as root:
            result = vd.analyze_file(root / "a.py", use_registry=False)
            self.assertEqual(result["imports"][0]["status"], "declared")

    def test_node_classification(self):
        src = ('import _ from "lodash";\nimport fs from "fs";\n'
               'import x from "./local";\nimport g from "ghost-pkg-zzz";\n')
        pkg = '{"dependencies": {"lodash": "^4.0.0"}}'
        with project({"package.json": pkg, "app.js": src}) as root:
            result = vd.analyze_file(root / "app.js", use_registry=False)
            status = {i["name"]: i["status"] for i in result["imports"]}
            self.assertEqual(status.get("lodash"), "declared")
            self.assertEqual(status.get("ghost-pkg-zzz"), "unknown")
            self.assertNotIn("fs", status)      # builtin, not flagged
            self.assertNotIn("./local", status)  # relative, ignored

    def test_go_stdlib_vs_thirdparty(self):
        src = 'import (\n\t"fmt"\n\t"github.com/x/y"\n)\n'
        with project({"m.go": src}) as root:
            result = vd.analyze_file(root / "m.go", use_registry=False)
            status = {i["name"]: i["status"] for i in result["imports"]}
            self.assertEqual(status.get("github.com/x/y"), "unknown")
            self.assertNotIn("fmt", status)

    def test_registry_missing_marks_missing(self):
        with mock.patch.object(vd, "registry_exists", return_value=False):
            status, detail = vd.classify("ghostpkg", "python", set(), True)
        self.assertEqual(status, "missing")
        self.assertIn("hallucinated", detail)

    def test_registry_exists_but_undeclared(self):
        with mock.patch.object(vd, "registry_exists", return_value=True):
            status, detail = vd.classify("realpkg", "python", set(), True)
        self.assertEqual(status, "unknown")
        self.assertIn("not declared", detail)

    def test_manifest_walk_does_not_escape_repo(self):
        # Without a matching manifest, a real dep must read as unknown, proving the
        # walk stopped at the .git marker rather than picking up an outside manifest.
        with project({"a.py": "import requests\n"}) as root:
            result = vd.analyze_file(root / "a.py", use_registry=False)
            self.assertEqual(result["imports"][0]["status"], "unknown")

    def test_local_sibling_import_is_local(self):
        files = {"helper.py": "x = 1\n", "main.py": "import helper\nimport os\n"}
        with project(files) as root:
            result = vd.analyze_file(root / "main.py", use_registry=False)
            status = {i["name"]: i["status"] for i in result["imports"]}
            self.assertEqual(status["helper"], "local")
            self.assertEqual(status["os"], "stdlib")


class OrchestratorTests(unittest.TestCase):

    def _run(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = lean_check.main(argv)
        return code, buf.getvalue()

    def test_clean_project_exits_zero(self):
        src = "import os\n\n\ndef f(x):\n    return x + 1\n"
        with project({"clean.py": src}) as root:
            code, out = self._run([str(root / "clean.py")])
        self.assertEqual(code, 0)
        self.assertIn("CLEAN", out)

    def test_findings_exit_one(self):
        code, out = self._run([str(FIXTURES / "bad_complexity.py")])
        self.assertEqual(code, 1)
        self.assertIn("FINDINGS", out)

    def test_usage_error_on_no_targets(self):
        with project({"notes.txt": "x\n"}) as root:
            code, _ = self._run([str(root / "notes.txt")])
        self.assertEqual(code, 0)  # no supported files -> nothing to flag


if __name__ == "__main__":
    unittest.main()
