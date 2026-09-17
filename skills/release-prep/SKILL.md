---
name: release-prep
description: >
  Use this to validate a release before it ships — detect version drift across
  all sources, verify the changelog, confirm tests pass, and produce a
  go/no-go checklist — when the user is about to tag or publish: "ready to
  release", "pre-release check", "can I ship this", "version drift", "about
  to tag"; NOT for writing the changelog itself (changelog), NOT for the tag
  and publish operations (dev-workflow), and NOT for authoring tests
  (test-strategy).
allowed-tools: [Bash, Read, Grep]
model: sonnet
---

# Release Prep

Catch the things that break releases — version drift, stale changelogs, missing
assets — before they land in a tag. Works for Python packages and .NET projects;
handles both in the same repo if needed.

For other stacks (Go, Node, Rust, etc.): check for the canonical version file
(`go.mod`, `package.json`, `Cargo.toml`) and adapt the drift checks — the
principles are the same even if the file paths differ.

## Iron Law

No "Ready to tag" verdict while any checklist item is failing or unchecked —
because a tag is the point of no return, and a checklist that rounds ❌ up to ✅
is worse than no checklist: it converts a known risk into a certified one.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "Tests passed earlier this session — rerunning for the checklist is redundant." | The checklist certifies the current tree, not a memory. Any commit since the last run invalidates the result. | Run the test step fresh against the tree being tagged. |
| "The drift is just a README badge — cosmetic, I'll mark it ✅ with a note." | Drift sources are how wrong-version releases ship. The checklist has no 'mostly consistent' state. | Report it as ❌ with file and value. The user decides whether to ship anyway. |
| "The user is in a hurry — tests pass, so I'll skip the build/packaging step." | Passing tests don't prove the artifact builds. A broken sdist or exe discovered after tagging costs a release redo. | Run the build check. It's one command per stack. |

---

## 1. Detect the project type

```bash
ls pyproject.toml setup.py setup.cfg 2>/dev/null   # Python
find . -name "*.csproj" -not -path "*/obj/*" | head -5  # .NET
ls package.json go.mod Cargo.toml 2>/dev/null       # Node / Go / Rust
```

---

## 2. Extract the canonical version

### Python
```bash
grep -E '^version\s*=' pyproject.toml | head -1
# __version__ usually lives under the package source root — adjust the path to
# the project's own layout (src/, the importable package dir, etc.):
grep -rE '__version__\s*=' src/ 2>/dev/null | head -3
```

### .NET
```bash
grep -E '<(Version|AssemblyVersion|FileVersion)>' **/*.csproj
```

### Node
```bash
node -p "require('./package.json').version"
```

### Go
```bash
grep '^module\|^go ' go.mod | head -2
# Version typically lives in a VERSION file or git tag — check both:
cat VERSION 2>/dev/null || git describe --tags --abbrev=0
```

### Rust
```bash
grep '^version' Cargo.toml | head -1
```

If multiple sources already disagree, report **Drift Finding #1** before continuing.

---

## 3. Check for version drift

### Python drift sources

| Source | How to check |
|--------|-------------|
| README badges | `grep -oE 'badge/v[^-]+-' README.md` |
| CHANGELOG.md heading | First `## [x.y.z]` entry |
| `__init__.py` / `_version.py` | `grep __version__` |
| GitHub Actions asset names | `.github/workflows/*.yml` — hardcoded version strings |
| `docs/conf.py` | `grep ^release` |
| `check_release_metadata.py` | Run it if present: `python scripts/check_release_metadata.py` |

### .NET drift sources

| Source | How to check |
|--------|-------------|
| All `.csproj` files | `grep -rE '<Version>' --include="*.csproj"` |
| `AssemblyInfo.cs` | `grep AssemblyVersion` |
| README / docs | Grep for version string |
| GitHub Actions workflows | Grep for hardcoded version strings |

Report every mismatch with the file and the value found.

---

## 4. Verify the changelog

```bash
head -60 CHANGELOG.md
```

Check:
- Entry for the release version exists (not just `[Unreleased]`)
- Entry has at least one item under Added / Changed / Fixed
- Date is present and correct: `## [1.2.3] - YYYY-MM-DD`
- `[Unreleased]` is still present above for future work

If the changelog only has `[Unreleased]` and no dated entry, the **changelog** skill
needs to run first. Say so and stop.

---

## 5. Confirm tests pass

### Python
```bash
pytest --tb=short -q 2>&1 | tail -20
```

### .NET
```bash
dotnet test --no-build --verbosity minimal 2>&1 | tail -20
```

**If tests fail: stop here.** A release with failing tests is not ready.

Report the failure count and the first failing test name. Suggest next steps:
- Fix the failures, then re-run release-prep
- Open a GitHub issue to track each failure: `gh issue create --title "test: [test name] failing on release branch" --label "bug"`
- Or, if failures are known/pre-existing and intentionally deferred: ask the user to confirm before proceeding

Regardless of user confirmation, the checklist shows **❌** for failing tests — user
confirmation changes the *decision* (whether to ship anyway), not the finding. A
confirmed ❌ in the checklist is not the same as a ✅.

**If no test framework is detected:** document as `❌ No test suite found — not
verified.` This is never a silent pass. "No test framework" is not an N/A state —
the release checklist has no N/A column. An absent test suite is a finding, not an
exemption.

---

## 6. Check build / packaging

### Python
```bash
python -m build --sdist --wheel 2>&1 | tail -10
ls dist/
```

### .NET
```bash
dotnet publish -c Release -r win-x64 --self-contained true \
  -p:PublishSingleFile=true -o publish_check 2>&1 | tail -10
```

---

## 7. Output the release checklist

Pre-fill each item as ✅ or ❌ based on findings:

```
Release checklist — vX.Y.Z

Version consistency
  ✅ pyproject.toml: 5.43.0
  ✅ README badge: 5.43.0
  ❌ docs/conf.py: 5.42.0  ← NEEDS FIX
  ✅ CHANGELOG.md heading: 5.43.0

Changelog
  ✅ Entry for v5.43.0 present
  ✅ At least one item documented
  ✅ Date present

Tests
  ✅ 534 passed, 0 failed

Build
  ✅ Wheel and sdist built cleanly

Ready to tag: NO — fix 1 drift item above first.
```

If everything passes: **"Ready to tag."** Provide the `git tag` + `git push` commands.

---

## 8. Offer next steps

> Fix the drift items above, or should I draft the git tag and GitHub release notes?

---

## If this fails

- **Build fails:** check for missing dependencies or environment issues; don't tag until the build is clean
- **No CHANGELOG entry:** run the **changelog** skill first, then return here
- **Version drift:** fix the drifted file(s), commit with `chore: sync version to X.Y.Z`, then re-run

---

## Next Step

After a clean checklist → use **commit-message** to write the tag commit message, then:

```bash
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

Then use **dev-workflow** (`gh release create`) to publish the GitHub release.
