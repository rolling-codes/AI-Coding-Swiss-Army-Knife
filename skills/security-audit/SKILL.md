---
name: security-audit
description: >
  Use this to run a security audit on a repository — dependency vulnerability
  scanning, SAST, and secrets detection — when the user asks "check for
  vulnerabilities", "scan for CVEs", "audit dependencies", "any secrets in
  this code", "OWASP check", or "is this safe to ship"; NOT for general code
  quality review (code-review), NOT for checking whether packages are outdated
  (dependency-check), and NOT for manual penetration testing.
allowed-tools: [Bash, Grep, Read]
model: sonnet
---

# Security Audit

Run a layered security scan — universal tools first, language-specific tools
conditionally — and produce a severity-ranked report. The goal is finding
real, actionable vulnerabilities, not a long list of noise.

## Quick examples

**In:** "check this repo for vulnerabilities before we ship"
**Out:** scan runs (osv-scanner + semgrep + lockfile-specific tool), report with
critical/high/medium/low counts, top findings with file paths, recommended fixes

**In:** "any secrets or API keys hardcoded in here?"
**Out:** semgrep secrets scan + grep for common patterns, findings or clean confirmation

## Iron Law

Universal tools run on every repo; language-specific tools run only when the
matching lockfile is detected — because running the wrong tool wastes time and
produces false errors, and skipping the universal tools misses cross-language
dependency chains.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "No lockfile found, so I'll skip dependency scanning." | osv-scanner is language-agnostic and scans vendored source — it runs regardless. | Always run the universal tools; skip only the language-specific ones if their lockfile is absent. |
| "The semgrep rule set is large — I'll skip it to save time." | SAST and secrets detection are the only way to catch hardcoded credentials and injection patterns. Skipping it makes the audit meaningless. | Run `p/security-audit`; it's the minimal rule set, not the exhaustive one. |
| "This finding looks like a false positive, so I'll drop it." | False positive classification requires verification, not intuition. | Keep it; annotate as `[unverified]` with the reasoning. The user decides what to dismiss. |
| "The tool isn't installed — I'll note that and move on." | An absent tool is an audit gap, not a pass. | Report `[TOOL MISSING: <name>]` as a finding at Medium severity — the gap itself is a risk. |

---

## Step 1: Detect Package Managers

Check for lockfiles before deciding which language-specific tools to run:

```bash
# Outputs which managers are present — used to gate Step 3 conditionally
[ -f package.json ]      && echo "npm"
[ -f Cargo.toml ]        && echo "cargo"
[ -f go.mod ]            && echo "go"
[ -f pom.xml ]           && echo "maven"
[ -f requirements.txt ] || [ -f Pipfile ] || [ -f pyproject.toml ] && echo "python"
[ -f Gemfile.lock ]      && echo "ruby"
```

---

## Step 2: Run Universal Tools (always)

These run on every repo regardless of language:

```bash
# Dependency vulnerabilities — language-agnostic, JSON output
osv-scanner scan source -r . --json 2>/dev/null

# SAST + secrets detection
semgrep scan --json --config=p/security-audit . 2>/dev/null
```

If either tool is absent, report `[TOOL MISSING: osv-scanner]` or
`[TOOL MISSING: semgrep]` as a Medium finding — the gap is real.

---

## Step 3: Run Language-Specific Tools (conditional)

Run only the tools whose lockfile was detected in Step 1:

```bash
# npm / Node.js
npm audit --json 2>/dev/null

# Rust
cargo audit --json 2>/dev/null

# Python
pip-audit --desc --format json 2>/dev/null

# Java / Maven (produces JSON report in target/)
mvn dependency-check:check -Ddependency-check.format=JSON -q 2>/dev/null

# Ruby
bundle audit check --format json 2>/dev/null
```

---

## Step 4: Aggregate and Report

Parse the JSON outputs from each tool. Normalize severity to:
`Critical → High → Medium → Low`

Report format:

```
Security audit: <repo or path>. <N> findings — <c> critical, <h> high, <m> medium, <l> low.
Tools run: <list>. Tools missing: <list or "none">.

## Critical

### 1. [package@version or file:line] Short title [confirmed|unverified]
**Source:** osv-scanner / semgrep / npm-audit / ...
**Detail:** What the vulnerability is and how it triggers.
**Fix:** Upgrade to X.Y.Z / patch / remove.

## High
...
## Medium
...
## Low
...
```

Within each severity group: dependency vulns before code-level findings; order
by blast radius descending.

---

## Step 5: Secrets Check (always, separate grep pass)

Even if semgrep runs, do a targeted grep for common secret patterns that rules
sometimes miss:

```bash
grep -rn --include="*.{js,ts,py,go,rb,java,env,yml,yaml,json,toml,sh}" \
  -E "(api[_-]?key|secret[_-]?key|access[_-]?token|password|passwd|aws_secret|private_key)\s*[:=]\s*['\"][^'\"]{8,}" \
  . 2>/dev/null | grep -v ".git/"
```

Any hit is a High finding unless it's clearly a placeholder (e.g., `"your-api-key-here"`).

---

## Rules

- Never drop a Critical or High finding — annotate as `[unverified]` if uncertain, but keep it
- Missing tools are reported as Medium gaps, not silently skipped
- No fix code in the report — describe the fix direction, don't implement it here
- If the repo is clean: say so explicitly — "Security audit: <scope>. No findings."

---

## Next Step

- **Critical or High findings:** use **dev-workflow** to branch and fix; re-run this skill after to verify
- **Outdated packages (not CVEs):** use **dependency-check** for the upgrade sweep
- **Code quality issues surfaced:** use **code-review** — they're out of scope here
- **Track findings as issues:** `gh issue create --title "[security] short title" --label "security"`
