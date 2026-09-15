#!/usr/bin/env python3
"""lean_check.py — the one entry point lean-code runs before handing back code.

Orchestrates the two deterministic pillars into a single pillar-mapped report:
  Pillar 3 — complexity / size budget  (complexity_check.py)
  Pillar 4 — dependency verification   (verify_deps.py)

Pillars 1 (reuse) and 2 (simplicity) stay judgment calls in SKILL.md — they aren't
reliably checkable by a script, and faking that precision would violate the very
principle this skill teaches. Stdlib only.

Exit codes: 0 = clean, 1 = findings, 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import complexity_check as cc  # noqa: E402
import verify_deps as vd  # noqa: E402


def run_complexity(paths, limits):
    results, any_v = cc.run(paths, limits)
    findings = [(p, [v.to_dict() for v in vs], note)
                for p, vs, note in results if vs]
    return findings, any_v


def run_deps(paths, use_registry):
    results = [vd.analyze_file(t, use_registry) for t in vd.iter_targets(paths)]
    findings = []
    for r in results:
        bad = [i for i in r["imports"] if i["status"] in vd.BAD]
        if bad:
            findings.append((r["path"], bad))
    return findings, vd.has_flags(results)


def print_pillar3(findings):
    print("Pillar 3 — complexity / size budget")
    if not findings:
        print("  OK — everything within budget.")
        return
    for path, violations, note in findings:
        tag = f"  [{note}]" if note else ""
        print(f"  {path}{tag}")
        for v in violations:
            print(f"    L{v['line']}: {v['kind']} '{v['name']}' "
                  f"= {v['value']} (budget {v['limit']})")


def print_pillar4(findings):
    print("Pillar 4 — dependency verification")
    if not findings:
        print("  OK — every import is stdlib or declared.")
        return
    for path, imports in findings:
        print(f"  {path}")
        for imp in imports:
            print(f"    {imp['status'].upper()} '{imp['name']}' — {imp['detail']}")


def build_parser():
    p = argparse.ArgumentParser(description="lean-code pre-handoff checker (pillars 3+4)")
    p.add_argument("paths", nargs="+", help="files or directories to check")
    p.add_argument("--registry", action="store_true",
                   help="confirm unknown imports against PyPI/npm (needs network)")
    p.add_argument("--func-lines", type=int, default=cc.DEFAULTS["func_lines"])
    p.add_argument("--file-lines", type=int, default=cc.DEFAULTS["file_lines"])
    p.add_argument("--nesting", type=int, default=cc.DEFAULTS["nesting"])
    p.add_argument("--cyclomatic", type=int, default=cc.DEFAULTS["cyclomatic"])
    p.add_argument("--json", action="store_true", help="emit combined JSON")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    limits = {"func_lines": args.func_lines, "file_lines": args.file_lines,
              "nesting": args.nesting, "cyclomatic": args.cyclomatic}
    c_find, c_any = run_complexity(args.paths, limits)
    d_find, d_any = run_deps(args.paths, args.registry)

    if args.json:
        print(json.dumps({"complexity": c_find, "dependencies": d_find}, indent=2))
    else:
        print_pillar3(c_find)
        print()
        print_pillar4(d_find)
        print()
        print("RESULT:", "FINDINGS — review before handing back code."
              if (c_any or d_any) else "CLEAN — pillars 3 & 4 satisfied.")
    return 1 if (c_any or d_any) else 0


if __name__ == "__main__":
    sys.exit(main())
