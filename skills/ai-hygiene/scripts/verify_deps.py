#!/usr/bin/env python3
"""verify_deps.py — Pillar 4 (dependency verification) enforcement for lean-code.

Extracts third-party imports from a source file and classifies each as stdlib,
declared-in-manifest, local, or UNKNOWN. Unknown imports are the slopsquatting /
hallucinated-package risk. Offline by default; `--registry` confirms unknowns against
PyPI / npm. Stdlib only (uses urllib for the optional network check).

Exit codes: 0 = every import accounted for, 1 = unknown import(s), 2 = usage error.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11 — fall back to a shallow regex parse.
    tomllib = None

NODE_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "crypto", "dgram",
    "dns", "events", "fs", "http", "http2", "https", "net", "os", "path", "process",
    "querystring", "readline", "stream", "string_decoder", "timers", "tls", "tty",
    "url", "util", "v8", "vm", "zlib", "worker_threads", "perf_hooks",
}

# import name -> distribution name, for the common cases where they differ.
PY_ALIASES = {
    "yaml": "pyyaml", "cv2": "opencv-python", "PIL": "pillow", "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn", "dotenv": "python-dotenv", "dateutil": "python-dateutil",
}

JS_IMPORT = re.compile(r"""(?:import\s[^'"]*from\s*|import\s*|require\s*\(\s*)['"]([^'"]+)['"]""")
GO_IMPORT = re.compile(r'"([^"]+)"')
RUST_USE = re.compile(r"\buse\s+([A-Za-z_][\w]*)")


def norm(name):
    return name.lower().replace("_", "-").strip()


def py_imports(src):
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def js_pkg(spec):
    """Top-level package name from an import specifier, or None if relative/builtin."""
    if spec.startswith((".", "/")):
        return None
    parts = spec.split("/")
    if spec.startswith("@") and len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def js_imports(src):
    names = set()
    for spec in JS_IMPORT.findall(src):
        pkg = js_pkg(spec)
        if pkg and pkg not in NODE_BUILTINS:
            names.add(pkg)
    return names


def go_imports(src):
    """Third-party Go imports = paths whose first segment looks like a domain."""
    names = set()
    for path in GO_IMPORT.findall(src):
        head = path.split("/")[0]
        if "." in head:
            names.add(path)
    return names


def rust_imports(src):
    names = set()
    for name in RUST_USE.findall(src):
        if name not in {"crate", "self", "super", "std", "core", "alloc"}:
            names.add(name)
    return names


EXTRACTORS = {
    ".py": ("python", py_imports),
    ".js": ("node", js_imports), ".jsx": ("node", js_imports),
    ".ts": ("node", js_imports), ".tsx": ("node", js_imports),
    ".mjs": ("node", js_imports), ".cjs": ("node", js_imports),
    ".go": ("go", go_imports), ".rs": ("rust", rust_imports),
}


def find_manifests(start):
    """Walk upward from a file collecting known manifest paths (stop at a repo root)."""
    found = {}
    names = ["requirements.txt", "pyproject.toml", "package.json", "go.mod",
             "Cargo.toml"]
    cur = Path(start).resolve().parent
    while True:
        for n in names:
            p = cur / n
            if n not in found and p.is_file():
                found[n] = p
        if (cur / ".git").exists() or cur == cur.parent:
            break
        cur = cur.parent
    return found


def parse_requirements(text):
    out = set()
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        m = re.match(r"[A-Za-z0-9_.-]+", line)
        if m:
            out.add(norm(m.group(0)))
    return out


def parse_pyproject(text):
    out = set()
    if tomllib:
        try:
            data = tomllib.loads(text)
        except Exception:
            return out
        proj = data.get("project", {}).get("dependencies", []) or []
        poetry = (data.get("tool", {}).get("poetry", {})
                  .get("dependencies", {}) or {})
        for dep in proj:
            m = re.match(r"[A-Za-z0-9_.-]+", dep)
            if m:
                out.add(norm(m.group(0)))
        out.update(norm(k) for k in poetry if k.lower() != "python")
    else:
        out.update(norm(m) for m in re.findall(r'"([A-Za-z0-9_.-]+)"', text))
    return out


def parse_package_json(text):
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return set()
    out = set()
    for key in ("dependencies", "devDependencies", "peerDependencies",
                "optionalDependencies"):
        out.update(data.get(key, {}).keys())
    return out


def parse_go_mod(text):
    return set(re.findall(r"^\s*(?:require\s+)?([\w./-]+\.[\w./-]+)\s+v",
                          text, re.MULTILINE))


def parse_cargo(text):
    out, in_deps = set(), False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("["):
            in_deps = "dependencies" in s
        elif in_deps:
            m = re.match(r"([A-Za-z0-9_-]+)\s*=", s)
            if m:
                out.add(m.group(1).replace("-", "_"))
    return out


MANIFEST_PARSERS = {
    "requirements.txt": ("python", parse_requirements),
    "pyproject.toml": ("python", parse_pyproject),
    "package.json": ("node", parse_package_json),
    "go.mod": ("go", parse_go_mod),
    "Cargo.toml": ("rust", parse_cargo),
}


def declared_for(lang, manifests):
    declared = set()
    for name, path in manifests.items():
        mlang, parser = MANIFEST_PARSERS[name]
        if mlang == lang:
            try:
                declared |= parser(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    return declared


def is_declared(pkg, lang, declared):
    if lang == "python":
        cand = {norm(pkg), norm(PY_ALIASES.get(pkg, pkg))}
        return bool(cand & declared)
    if lang == "node":
        return pkg in declared
    if lang == "go":
        return pkg in declared or any(pkg.startswith(d) for d in declared)
    if lang == "rust":
        return pkg.replace("-", "_") in declared
    return False


def is_stdlib(pkg, lang):
    if lang == "python":
        return pkg in sys.stdlib_module_names
    if lang == "node":
        return pkg in NODE_BUILTINS
    if lang == "go":
        return "." not in pkg.split("/")[0]
    return False


def registry_url(pkg, lang):
    if lang == "python":
        return f"https://pypi.org/pypi/{norm(PY_ALIASES.get(pkg, pkg))}/json"
    if lang == "node":
        return f"https://registry.npmjs.org/{pkg}"
    return None


def registry_exists(pkg, lang, timeout=6):
    """True/False if resolvable online, None if the check can't run."""
    url = registry_url(pkg, lang)
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "lean-code"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as exc:
        return False if exc.code == 404 else None
    except (urllib.error.URLError, TimeoutError, OSError):
        return None


def local_modules(src_path):
    """Sibling module names importable from the file's own directory (not third-party)."""
    d = Path(src_path).resolve().parent
    names = {p.stem for p in d.glob("*.py")}
    names |= {p.name for p in d.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    return names


def classify(pkg, lang, declared, use_registry, local=None):
    if local and pkg in local:
        return "local", None
    if is_stdlib(pkg, lang):
        return "stdlib", None
    if is_declared(pkg, lang, declared):
        return "declared", None
    if use_registry:
        exists = registry_exists(pkg, lang)
        if exists is True:
            return "unknown", "exists in registry but not declared in the manifest"
        if exists is False:
            return "missing", "NOT FOUND in registry — likely hallucinated"
        return "unknown", "registry check unavailable (offline?)"
    return "unknown", "not in manifest or stdlib"


def analyze_file(path, use_registry):
    ext = Path(path).suffix.lower()
    if ext not in EXTRACTORS:
        return {"path": str(path), "note": "unsupported language", "imports": []}
    lang, extractor = EXTRACTORS[ext]
    try:
        src = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"path": str(path), "note": f"unreadable: {exc.strerror}",
                "imports": []}
    names = extractor(src)
    if names is None:
        return {"path": str(path), "note": "skipped (syntax error)", "imports": []}
    declared = declared_for(lang, find_manifests(path))
    local = local_modules(path) if lang == "python" else set()
    imports = []
    for pkg in sorted(names):
        status, detail = classify(pkg, lang, declared, use_registry, local)
        imports.append({"name": pkg, "status": status, "detail": detail})
    return {"path": str(path), "lang": lang, "note": None, "imports": imports}


def iter_targets(paths):
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.suffix.lower() in EXTRACTORS)
        else:
            yield p


BAD = {"unknown", "missing"}


def print_report(results):
    for r in results:
        flagged = [i for i in r["imports"] if i["status"] in BAD]
        if not flagged and not r.get("note"):
            continue
        header = "FAIL" if flagged else "note"
        note = f"  [{r['note']}]" if r.get("note") else ""
        print(f"{header}: {r['path']}{note}")
        for imp in flagged:
            print(f"  {imp['status'].upper()} '{imp['name']}' — {imp['detail']}")


def has_flags(results):
    return any(i["status"] in BAD for r in results for i in r["imports"])


def main(argv=None):
    parser = argparse.ArgumentParser(description="lean-code dependency verifier")
    parser.add_argument("paths", nargs="+", help="files or directories to check")
    parser.add_argument("--registry", action="store_true",
                        help="confirm unknown imports against PyPI/npm (needs network)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    results = [analyze_file(t, args.registry) for t in iter_targets(args.paths)]
    if not results:
        print("No supported source files found.", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)
        if not has_flags(results):
            print("OK: every import is stdlib or declared in the manifest.")
    return 1 if has_flags(results) else 0


if __name__ == "__main__":
    sys.exit(main())
