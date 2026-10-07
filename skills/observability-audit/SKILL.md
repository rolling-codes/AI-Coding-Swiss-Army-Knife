---
name: observability-audit
description: >
  Use this to audit logging, tracing, and error-handling coverage across a
  codebase — "do we have enough logging", "add observability", "check our
  error handling coverage", "are we tracing this", "alerting gaps", "what
  would we miss if this broke in prod"; NOT for adding new log statements
  (dev-workflow), NOT for performance profiling (performance-audit), and
  NOT for testing error paths (test-strategy).
allowed-tools: [Grep, Read, Glob]
model: sonnet
---

# Observability Audit

Map what the codebase actually emits — logs, traces, metrics, errors — against
its critical paths, and surface the gaps. The goal is answering: "if this broke
in production tonight, would we know, and would we have enough context to fix it?"

## Quick examples

**In:** "do we have enough logging in the payment flow?"
**Out:** map of the payment critical path, log call sites on each segment,
gaps flagged with severity (silent failure vs. noisy but recoverable)

**In:** "what would we miss if the auth service went down?"
**Out:** audit of error handling at the auth boundary — retries, fallbacks,
alerting hooks, what surfaces to the user vs. what silently fails

## Iron Law

Map the critical paths first, then check coverage — because an audit of log
call density without knowing which paths matter produces noise, not signal.

## Red Flags — Rationalizations to Refuse

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "There are lots of log calls — coverage looks good." | Density is not coverage. Logs at the wrong level or wrong location are invisible when it matters. | Map paths → check coverage per segment, not overall count. |
| "This is a small codebase — observability is overkill." | Small codebases fail silently too. The cost of adding a log line is lower than the cost of a blind outage. | Run the audit; the user decides the threshold. |
| "I'll add the missing log statements while I'm here." | This skill audits, not implements. Scope creep here leads to unreviewed observability changes. | Report the gaps; use **dev-workflow** to add them. |

---

## Step 1: Identify Critical Paths

Read the entry points and trace the primary flows:
- API routes / HTTP handlers
- Background jobs / queue consumers
- Auth and session boundaries
- External service calls (DB, cache, third-party APIs)
- Payment / billing / data-write paths

If there's a README, architecture doc, or `.claude/` context file, read it first
to understand which paths the maintainer considers critical.

---

## Step 2: Scan for Observability Call Sites

Search for logging, tracing, and metric instrumentation:

```bash
# Logging patterns (common across languages)
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" \
  -E "(console\.(log|warn|error)|logger\.(info|warn|error|debug)|log\.(info|warn|error)|logging\.(info|warning|error)|slog\.(Info|Warn|Error)|tracing::(info|warn|error))" \
  . 2>/dev/null | grep -v ".git/"

# Error handling patterns
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" \
  -E "(catch|except|rescue|recover|\.catch\(|handleError|on_error)" \
  . 2>/dev/null | grep -v ".git/"

# Metrics / tracing instrumentation
grep -rn --include="*.{js,ts,py,go,rb,java,rs}" \
  -E "(span\.|trace\.|meter\.|histogram\.|counter\.|prometheus|opentelemetry|datadog|newrelic)" \
  . 2>/dev/null | grep -v ".git/"
```

---

## Step 3: Map Coverage Against Critical Paths

For each critical path segment identified in Step 1, check:

| Segment | Has entry log? | Has exit/result log? | Error caught + logged? | Notes |
|---------|---------------|---------------------|----------------------|-------|
| Auth boundary | ✅ | ✅ | ✅ | good |
| Payment submit | ✅ | ❌ | ✅ | missing success log |
| DB write | ❌ | ❌ | ✅ | silent on success and failure detail |

Mark a segment as a **gap** if:
- An error can be swallowed silently (catch block with no log)
- A failed external call has no log before it propagates
- A critical write has no confirmation log
- The segment is entirely absent from log output

---

## Step 4: Classify Gaps by Severity

| Severity | Definition |
|----------|-----------|
| **Critical** | Silent failure — the path can fail with no trace in any log |
| **High** | Error logged but no context (no request ID, user ID, or payload shape) |
| **Medium** | Happy path not confirmed (success has no log, so failure looks identical to success in logs) |
| **Low** | Missing debug-level detail that would help but isn't essential |

---

## Step 5: Report

```
Observability audit: <scope>.
Critical paths mapped: <N>. Gaps: <c> critical, <h> high, <m> medium, <l> low.

## Critical gaps

### [file.ext:line or path segment] Description
**Path:** Auth → DB write → session creation
**Gap:** DB write failure swallowed in catch block — no log, no metric, no re-throw.
**Risk:** Failed logins produce no signal; attackers see the same UX as users.
**Fix direction:** Log the error with request ID and error type before returning false.

## High
...

## What's well-covered
- [list paths that have solid observability]
```

---

## Rules

- No log statements added here — report only; use **dev-workflow** to implement
- If the codebase has zero observability, say so plainly — it's a Critical gap, not just a suggestion
- A `console.log("here")` without context (request ID, relevant data shape) is a gap, not coverage

---

## Next Step

- **To add missing instrumentation:** use **dev-workflow** to implement the gaps
- **Error handling bugs found while auditing:** use **bug-triage** if multiple; **dev-workflow** if single
- **No structured logging library in use:** flag it as a Medium gap — unstructured logs don't query well
