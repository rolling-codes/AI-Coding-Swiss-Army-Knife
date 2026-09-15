#!/usr/bin/env python3
"""complexity_check.py — Pillar 3 (complexity / size budget) enforcement for lean-code.

Reports functions/files that exceed the budget the model can't reliably eyeball while
generating token-by-token. Python is measured precisely via `ast`; other languages use
honest brace/indent heuristics (flagged as such). Stdlib only.

Exit codes: 0 = clean, 1 = violations found, 2 = usage/no-input error.
"""
from __future__ import annotations

import argparse
import ast
import bisect
import json
import re
import sys
from pathlib import Path

DEFAULTS = {"func_lines": 50, "file_lines": 800, "nesting": 4, "cyclomatic": 10}

PY_EXT = {".py"}
BRACE_EXT = {".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs",
             ".php", ".c", ".cpp", ".cc", ".h", ".hpp"}

PY_NEST = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.AsyncFor, ast.AsyncWith)
PY_DECISION = (ast.If, ast.For, ast.While, ast.AsyncFor, ast.ExceptHandler,
               ast.With, ast.AsyncWith, ast.comprehension, ast.IfExp)

FUNC_PATTERNS = [
    re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"\bfunc\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\("),
    re.compile(r"\bfn\s+([A-Za-z_]\w*)\s*[(<]"),
    re.compile(r"\b([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^;{}]*\)\s*=>\s*\{"),
    re.compile(r"\b([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*\{"),
]


class Violation:
    """One budget breach, with enough context to render a clear line."""

    def __init__(self, kind, name, value, limit, line):
        self.kind, self.name, self.value, self.limit, self.line = (
            kind, name, value, limit, line)

    def to_dict(self):
        return {"kind": self.kind, "name": self.name, "value": self.value,
                "limit": self.limit, "line": self.line}

    def render(self):
        return (f"  L{self.line}: {self.kind} '{self.name}' = {self.value} "
                f"(budget {self.limit})")


def py_max_depth(func):
    """Deepest nesting of block statements inside a Python function body."""
    def walk(node, cur):
        best = cur
        for child in ast.iter_child_nodes(node):
            inc = 1 if isinstance(child, PY_NEST) else 0
            best = max(best, walk(child, cur + inc))
        return best
    return walk(func, 0)


def py_cyclomatic(func):
    """Approximate McCabe complexity: 1 + decision points + boolean operands."""
    count = 1
    for node in ast.walk(func):
        if isinstance(node, ast.BoolOp):
            count += len(node.values) - 1
        elif isinstance(node, PY_DECISION):
            count += 1
    return count


def py_function_violations(node, limits):
    out = []
    span = (node.end_lineno or node.lineno) - node.lineno + 1
    if span > limits["func_lines"]:
        out.append(Violation("function-length", node.name, span,
                             limits["func_lines"], node.lineno))
    depth = py_max_depth(node)
    if depth > limits["nesting"]:
        out.append(Violation("nesting-depth", node.name, depth,
                             limits["nesting"], node.lineno))
    cc = py_cyclomatic(node)
    if cc > limits["cyclomatic"]:
        out.append(Violation("cyclomatic", node.name, cc,
                             limits["cyclomatic"], node.lineno))
    return out


def analyze_python(src, limits):
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [], f"skipped (syntax error: {exc.msg})"
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.extend(py_function_violations(node, limits))
    return out, None


def _blank(text):
    """Same length as text, newlines preserved, everything else spaced out."""
    return "".join("\n" if ch == "\n" else " " for ch in text)


def _consume_line_comment(src, i, n):
    end = src.find("\n", i)
    end = n if end == -1 else end
    return _blank(src[i:end]), end


def _consume_block_comment(src, i, n):
    end = src.find("*/", i)
    end = n if end == -1 else end + 2
    return _blank(src[i:end]), end


def _consume_string(src, i, n):
    quote, j = src[i], i + 1
    while j < n and src[j] != quote:
        j += 2 if src[j] == "\\" and j + 1 < n else 1
    return _blank(src[i:min(j + 1, n)]), min(j + 1, n)


def strip_noise(src):
    """Blank out comments and string literals, preserving newlines and length."""
    handlers = {"//": _consume_line_comment, "/*": _consume_block_comment}
    out, i, n = [], 0, len(src)
    while i < n:
        handler = handlers.get(src[i:i + 2])
        if handler:
            chunk, i = handler(src, i, n)
        elif src[i] in "\"'`":
            chunk, i = _consume_string(src, i, n)
        else:
            chunk, i = src[i], i + 1
        out.append(chunk)
    return "".join(out)


def max_brace_depth(clean):
    depth = best = 0
    for ch in clean:
        if ch == "{":
            depth += 1; best = max(best, depth)
        elif ch == "}":
            depth = max(0, depth - 1)
    return best


def line_starts(src):
    starts = [0]
    for idx, ch in enumerate(src):
        if ch == "\n":
            starts.append(idx + 1)
    return starts


def offset_to_line(starts, offset):
    return bisect.bisect_right(starts, offset)


def match_brace_span(clean, open_pos):
    """Return the offset just past the '}' matching the '{' at open_pos, or None."""
    depth = 0
    for i in range(open_pos, len(clean)):
        if clean[i] == "{":
            depth += 1
        elif clean[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def brace_functions(clean, starts):
    """Yield (name, start_line, end_line) for detected functions in brace code."""
    seen = set()
    for pattern in FUNC_PATTERNS:
        for m in pattern.finditer(clean):
            brace = clean.find("{", m.end() - 1)
            if brace == -1 or brace in seen:
                continue
            end = match_brace_span(clean, brace)
            if end is None:
                continue
            seen.add(brace)
            yield (m.group(1), offset_to_line(starts, m.start()),
                   offset_to_line(starts, end))


def analyze_brace(src, limits):
    clean = strip_noise(src)
    starts = line_starts(src)
    out = []
    depth = max_brace_depth(clean)
    if depth > limits["nesting"]:
        out.append(Violation("nesting-depth", "<file>", depth, limits["nesting"], 1))
    for name, start, end in brace_functions(clean, starts):
        span = end - start + 1
        if span > limits["func_lines"]:
            out.append(Violation("function-length", name, span,
                                 limits["func_lines"], start))
    return out, "heuristic"


def analyze_file(path, limits):
    """Return (violations, note). note is None for precise, else a caveat string."""
    try:
        src = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], f"skipped (unreadable: {exc.strerror})"
    ext = Path(path).suffix.lower()
    file_v = []
    total = src.count("\n") + 1
    if total > limits["file_lines"]:
        file_v.append(Violation("file-length", Path(path).name, total,
                               limits["file_lines"], 1))
    if ext in PY_EXT:
        found, note = analyze_python(src, limits)
    elif ext in BRACE_EXT:
        found, note = analyze_brace(src, limits)
    else:
        return file_v, "skipped (unsupported language)" if not file_v else None
    return file_v + found, note


def iter_targets(paths):
    exts = PY_EXT | BRACE_EXT
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.suffix.lower() in exts)
        else:
            yield p


def limits_from_args(args):
    return {"func_lines": args.func_lines, "file_lines": args.file_lines,
            "nesting": args.nesting, "cyclomatic": args.cyclomatic}


def run(paths, limits):
    """Analyze every target; return (results, any_violation)."""
    results, any_v = [], False
    for target in iter_targets(paths):
        violations, note = analyze_file(target, limits)
        if violations:
            any_v = True
        results.append((str(target), violations, note))
    return results, any_v


def print_report(results):
    for path, violations, note in results:
        if not violations and not (note and "syntax error" in note):
            continue
        tag = f"  [{note}]" if note else ""
        status = "FAIL" if violations else "note"
        print(f"{status}: {path}{tag}")
        for v in violations:
            print(v.render())


def build_parser():
    p = argparse.ArgumentParser(description="lean-code complexity/size budget checker")
    p.add_argument("paths", nargs="+", help="files or directories to check")
    p.add_argument("--func-lines", type=int, default=DEFAULTS["func_lines"])
    p.add_argument("--file-lines", type=int, default=DEFAULTS["file_lines"])
    p.add_argument("--nesting", type=int, default=DEFAULTS["nesting"])
    p.add_argument("--cyclomatic", type=int, default=DEFAULTS["cyclomatic"])
    p.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    results, any_v = run(args.paths, limits_from_args(args))
    if not results:
        print("No supported source files found.", file=sys.stderr)
        return 2
    if args.json:
        payload = [{"path": p, "note": n,
                    "violations": [v.to_dict() for v in vs]}
                   for p, vs, n in results]
        print(json.dumps(payload, indent=2))
    else:
        print_report(results)
        if not any_v:
            print("OK: all files within the complexity budget.")
    return 1 if any_v else 0


if __name__ == "__main__":
    sys.exit(main())
