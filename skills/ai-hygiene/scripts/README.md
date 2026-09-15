# lean-code scripts

Deterministic enforcement for the two pillars a script can check reliably. Pillars 1
(reuse) and 2 (simplicity) stay judgment calls in `../SKILL.md` on purpose — a linter
for them would be fake precision, which is exactly what this skill warns against.

Python 3 stdlib only — no `pip install`. Every script degrades gracefully (unreadable
file, unknown language, missing manifest, network failure) and never raises a traceback
at the user.

## `lean_check.py` — run this one

The single entry point the skill runs before handing back code. Orchestrates both
checkers into one pillar-mapped report.

```bash
python lean_check.py <file-or-dir> [--registry] [--func-lines N] [--file-lines N] [--nesting N] [--cyclomatic N]
```

## `complexity_check.py` — Pillar 3 (complexity / size budget)

Flags functions/files over budget. Python is measured precisely via `ast` (function
length, nesting depth, cyclomatic complexity); other languages (`.js .jsx .ts .tsx .go
.rs .java .cs .php .c .cpp .h`) use brace/indent heuristics, reported as `[heuristic]`.
Defaults match `~/.claude/rules/ecc/common`: functions 50 lines, files 800, nesting 4,
cyclomatic 10 — all overridable.

```bash
python complexity_check.py path/ --json
```

## `verify_deps.py` — Pillar 4 (dependency verification)

Extracts imports and classifies each as **stdlib**, **declared** (in the nearest
manifest), **local**, or **unknown**. Manifests: `requirements.txt`, `pyproject.toml`,
`package.json`, `go.mod`, `Cargo.toml`; the search walks up to the repo root (a `.git`
directory) so it never picks up an unrelated manifest higher on the machine. Offline by
default; `--registry` confirms unknown Python/npm packages against PyPI/npm and separates
"real but undeclared" (UNKNOWN) from "not found anywhere — likely hallucinated"
(MISSING).

```bash
python verify_deps.py path/ [--registry] [--json]
```

Known limit: Python import names vs distribution names differ in cases beyond the small
built-in alias map (e.g. `yaml`→`pyyaml`); an unfamiliar alias may read as `unknown`
until `--registry` resolves it.

## Exit codes (all three)

`0` clean · `1` findings · `2` usage / no supported files.

## Tests

Stdlib `unittest`, hermetic (temp dirs with a `.git` marker; no network — the registry
path is mocked). Fixtures live in `tests/fixtures/`.

```bash
python -m unittest discover -s tests -v
```
