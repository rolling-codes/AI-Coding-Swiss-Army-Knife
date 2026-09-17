---
name: architecture-review
description: >
  Use this to assess structural health of a codebase or a proposed change —
  coupling, cohesion, layering violations, dependency direction, future
  maintenance cost — when asked "review the architecture", "is this well
  structured", "should this be split up", "check for layering violations",
  or before a v-next / major-refactor decision; NOT for line-by-line diff
  review (code-review), NOT for documentation drift (docs-audit), and NOT
  for session context management (context-compression).
allowed-tools: [Read, Grep, Glob, Bash]
model: sonnet
---

# Architecture Review Skill

Assesses structure, not correctness. A change can be bug-free and still be making
the codebase worse to work in. Model: `standard` for a single-module pass, `deep`
for a whole-repo or cross-cutting review (resolve via dev-workflow's
`model-registry.json` if installed).

## Quick examples

**In:** "is this service well-structured before we scale it?"
**Out:** coupling/cohesion report by module, 🔴🟡🟢 findings with file:line, fan-out counts, top recommendation

**In:** "should we split this 2000-line module?"
**Out:** blast-radius analysis + proposed split boundaries with rationale

## Iron Law

Every finding names a concrete file:line or module — because structural critique
without a location is a vibe, not a finding: it can't be verified, ranked, or fixed,
and it trains the reader to skim the report.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "The structure feels messy overall — a general impression is useful; pinning locations would take a full read." | Unlocated critique is unverifiable and unactionable. If you can't name where, you haven't established that. | Bound the read (grep, git diff), then report only what you can pin to file:line or module. |
| "This module is poorly structured — a rewrite would be cleaner than describing a refactor path." | Rewrites are the expensive answer that discards working behaviour. Recommending one where a smaller refactor fixes it inflates cost for the same outcome. | Propose the minimal structural fix; reserve 'design pass needed' for genuinely compounding problems. |
| "While I'm in here, I'll flag naming and formatting too — more findings, more value." | Style isn't structure. Lint noise in a structural report buries the load-bearing findings. | Report structure only. Style belongs to a linter or code-review's hygiene pass. |

---

## Step 1: Establish Scope

- **Single module/file** — reviewing one thing in isolation
- **Change under review** — a diff or new feature, assessed against the existing structure
- **Whole-repo audit** — full structural pass, usually pre-v-next

Don't read the whole repo for a single-module review. Use `grep -rl` / `git diff` to
bound the read before opening files.

---

## Step 1.5: Measure Before Reading

Run the graph availability check per dev-workflow's `references/graph-tools.md`
(if dev-workflow is installed). If a graph is available, pull fan-out counts and
blast-radius edge counts from it for every module in scope before opening any
file — open files only to verify edges the graph flags. Hand-counting what a graph
already measures is the expensive path to a less reliable number. If no graph,
bound the read with `grep -rl` / `git diff` as above.

---

## Step 2: Check Each Axis

**Coupling** — how much does this module know about others' internals?
- Direct reach into another module's internal state/private fields → high coupling
- Communication only through defined interfaces/events → low coupling
- Count fan-out: how many other modules does this one import/call directly? — from
  the graph when available, per Step 1.5

**Cohesion** — does everything in this module belong together?
- Do its functions share a single responsibility, or is it a junk drawer?
- Would splitting it produce two things people would import independently?

**Layering** — does control flow respect the intended layers (e.g. UI → domain → data)?
- Does a lower layer import from a higher one? (a data-access file importing a UI
  component is a violation)
- Are cross-layer calls going through the layer boundary's actual interface, or
  reaching around it?

**Dependency direction** — do dependencies point toward stable abstractions, or
toward volatile concrete detail?
- Does a stable, widely-used module depend on a module that changes often?
- Is there an inversion opportunity (interface/protocol) that would let the
  volatile detail depend on the stable abstraction instead of the reverse?

**Future maintenance cost** — projecting forward, not just describing today
- If this pattern is copied 10 more times (10 more plugins, 10 more endpoints),
  does it still hold up?
- What's the blast radius of a change to this module's public shape? — from the
  graph when available, per Step 1.5

---

## Step 3: Report

**Severity rubric for findings:**
- 🔴 Block / fix before proceeding — structural risk that compounds on every future change (e.g. a layering violation in the hot path, a dependency inversion that forces the stable module to import the volatile one).
- 🟡 Fix before the next major version — a coupling or cohesion issue that is manageable now but will cost more each month it is deferred.
- 🟢 Nice-to-have — a minor improvement with no compounding effect; defer freely.

```
## Architecture Review: [scope]

**Coupling:** [Low / Medium / High] — [1-2 sentences, name the specific fan-out or reach-in]
**Cohesion:** [Low / Medium / High] — [1-2 sentences]
**Layering:** [Clean / Violations found] — [list violations with file:line if found]
**Dependency direction:** [Sound / Inverted somewhere] — [name the inversion candidate if any]
**Maintenance cost trajectory:** [Flat / Growing / Compounding] — [why, in terms of the axes above]

**Findings** (ordered by impact):
1. 🔴 [structural problem] — [file:line] — [why it matters, what it costs if unaddressed]
2. 🟡 [worth doing before it compounds]
3. 🟢 [nice-to-have]

**Recommendation:** [Ship as-is / Fix blocking items first / Needs a design pass before proceeding]
```

---

## Rules

- Report structure, not style — this isn't a lint pass; don't flag formatting or naming alone
- Don't recommend a rewrite for a problem a smaller refactor fixes
- If scope was a single change, judge it against the existing architecture as it
  actually is, not an idealized version of it
- If the repo has an `.claude/architecture.json` (dev-workflow's architecture log),
  read it first — it may already answer "how is this structured" without a fresh scan
- Findings here that require follow-up work → hand off to dev-workflow's Issues
  section (`gh issue create`) rather than fixing silently mid-review
