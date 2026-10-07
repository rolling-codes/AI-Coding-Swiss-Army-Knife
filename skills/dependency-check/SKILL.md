---
name: dependency-check
description: >
  Use this to check whether dependencies are up to date and flag outdated,
  deprecated, or license-incompatible packages — "are our dependencies up to
  date", "check for outdated packages", "any deprecated packages", "license
  compliance check"; NOT for vulnerability scanning (security-audit), NOT for
  fixing or upgrading the packages (dev-workflow).
allowed-tools: [Bash]
model: haiku
---

# Dependency Check

Detect outdated, deprecated, or license-problematic packages and produce a
table the maintainer can act on. This is a report skill, not a fix skill.

## Quick examples

**In:** "are our dependencies up to date?"
**Out:** table of outdated packages — current / latest / breaking columns,
major-version bumps flagged separately

**In:** "license compliance check before we open-source this"
**Out:** list of packages with non-permissive licenses (GPL, AGPL, SSPL, proprietary)
that need review before public release

## Iron Law

Detect the package manager from lockfiles; run only the matching tool. Running
the wrong tool produces misleading output.

## Red Flags — Rationalizations to Refuse

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "No lockfile — I'll skip." | A missing lockfile is itself a finding (no reproducible builds). | Report `[NO LOCKFILE FOUND]` and stop. |
| "Only a few packages are outdated — not worth flagging." | The user asked; every outdated package is a finding. | Report all of them; let the user decide what's worth upgrading. |
| "I'll upgrade the packages while I'm here." | This skill reports, it doesn't change code. Upgrades belong in dev-workflow. | Report only. Recommend `dev-workflow` for the upgrade. |

---

## Step 1: Detect Package Manager

```bash
[ -f package.json ]                                   && echo "npm"
[ -f Cargo.toml ]                                     && echo "cargo"
[ -f go.mod ]                                         && echo "go"
[ -f requirements.txt ] || [ -f pyproject.toml ]      && echo "python"
[ -f Gemfile ]                                        && echo "ruby"
[ -f pom.xml ]                                        && echo "maven"
```

If none found: report `[NO LOCKFILE FOUND]` — reproducible builds are not
guaranteed — and stop.

---

## Step 2: Run the Matching Tool

```bash
# npm / Node.js
npm outdated --json 2>/dev/null

# Rust
cargo outdated 2>/dev/null

# Python
pip list --outdated --format json 2>/dev/null

# Go
go list -u -m -json all 2>/dev/null

# Ruby
bundle outdated --parseable 2>/dev/null
```

---

## Step 3: Report

Format as a table:

```
Dependency check: <manager> (<N> packages checked).
<up> up to date. <out> outdated — <maj> major, <min> minor, <pat> patch.

| Package | Current | Latest | Change | Notes |
|---------|---------|--------|--------|-------|
| lodash  | 4.17.20 | 4.17.21 | patch | CVE fixed in 4.17.21 — upgrade |
| react   | 17.0.2  | 18.3.1  | MAJOR | breaking changes — review changelog |
| ...     |         |         |       |       |

Major-version bumps (review before upgrading):
- react 17→18: [link to changelog if known]
```

Lead with major bumps — they're the ones that break builds.

---

## Step 4: License Check (if requested)

If the user asked about licenses, add:

```bash
# npm
npx license-checker --json --production 2>/dev/null

# Python
pip-licenses --format json 2>/dev/null
```

Flag packages with: `GPL`, `AGPL`, `SSPL`, `LGPL`, `EUPL`, `CC-BY-SA`,
`proprietary`, or `unknown`. Everything else (MIT, BSD, Apache, ISC) is
generally safe for commercial use — confirm with the user if unsure.

---

## Next Step

- **To upgrade packages:** use **dev-workflow** to branch, bump, test, and PR
- **CVEs in outdated packages:** use **security-audit** — it cross-references against the OSV database
- **Major version bumps:** open a GitHub issue per package to track the migration: `gh issue create --title "Upgrade <pkg> to vX"`
