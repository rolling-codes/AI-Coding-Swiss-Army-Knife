# Skill Routing & Disambiguation

The single source of truth for *which* pack skill owns a task, *when* two skills
legitimately collide, and *what* they hand each other. dev-workflow's `SKILL.md`
routing table stays short; the resolution rules live here so they exist in one
place instead of being duplicated (and drifting) across thirteen files.

Load this reference only when routing is genuinely ambiguous — the `SKILL.md`
table resolves the common cases without it.

---

## 1. Selection decision process

Answer these in order. Stop as soon as the task is placed.

1. **What is the user's actual task?** State it in one sentence, in terms of the
   outcome they want — not the first keyword you noticed.
2. **What is the primary development activity?** Writing code, reviewing a diff,
   shipping a release, ranking findings, managing context, auditing docs, etc.
3. **Which single skill owns that activity?** Use the ownership table (§3). The
   owner is the *primary* skill.
4. **Are supporting skills required?** A supporting skill runs in service of the
   primary one (e.g. commit-message during a dev-workflow commit step). Add only
   those the primary skill's workflow actually calls for.
5. **What is explicitly out of scope?** Name the skills that a keyword might
   suggest but that do not own this task (§4, "irrelevant"). Naming them prevents
   reflexive multi-skill activation.
6. **In what order do the applicable skills run?** Use the overlap table (§5) for
   any pair that can both apply. If order is undefined there, the producing skill
   runs before the consuming one.
7. **What state passes between them?** Use the handoff contract (§6) — pass the
   minimum useful state, not the conversation.

If two skills still fit after this, the tighter-scoped one wins (a dedicated
sibling beats the dev-workflow default). User instructions beat all skill
defaults.

---

## 2. Role each skill can play in a task

A skill is not simply "on" or "off" — it plays one of these roles per task:

| Role | Meaning | Example |
|---|---|---|
| **Primary** | Owns the task; drives the workflow | code-review on "review my diff" |
| **Supporting** | Invoked by the primary skill mid-workflow | commit-message inside dev-workflow's Commit step |
| **Follow-up** | Runs after the primary completes, on its output | bug-triage after a review returns many findings |
| **Escalation** | Takes over when the primary hits its boundary | code-review §B (delegated reviewer) when a diff is too large for self-review |
| **Irrelevant** | A keyword suggests it, but it does not own this task | changelog is irrelevant to "write a commit message" |

Select the smallest set that completes the task correctly. Most tasks have exactly
one primary and zero or one supporting skill.

---

## 3. Ownership at a glance (Capability · Trigger · Boundary)

| Skill | Owns (Capability) | Fires when (Trigger) | Stays out when (Boundary) |
|---|---|---|---|
| dev-workflow | Orchestration: pipeline, GitHub ops, model routing, memory | A dev task with no dedicated owner, or "what next" | A sibling owns the specific artifact/activity |
| ai-hygiene | AI stylistic fingerprints in code/prose; watermarks | Writing substantial new code, "does this sound AI", "humanize", de-AI | Correctness bugs (→ code-review); trivial edits |
| commit-message | Conventional Commit from the **staged** diff | Changes staged, message needed | PR body, changelog, or executing the commit |
| pr-description | PR body from **branch..base** diff + history | Opening a PR / merge request | Single-commit message; changelog; running the merge |
| changelog | Keep-a-Changelog entries from **tag..HEAD**, as user impact | "update changelog", "release notes" | Verifying a release (→ release-prep); commit msgs |
| release-prep | Version-drift + changelog + tests + build go/no-go | "ready to release", "can I ship", "about to tag" | Writing the changelog; authoring tests; tagging |
| code-review | Correctness/security/scope review of a finished diff | "review my changes", "ready to merge" | Structure-only (→ architecture-review); ranking piles (→ bug-triage); AI style (→ ai-hygiene) |
| bug-triage | Dedup + severity-rank findings from ≥1 source | A pile of findings needs ordering | Finding new issues (→ code-review); fixing them |
| scope-creep | Classify a mid-build addition before it's absorbed | New feature/change/dep appears mid-build | Original task; a project not yet started |
| architecture-review | Structural health: coupling/cohesion/layering/deps | "is this well structured", pre-v-next | Line-level correctness (→ code-review); doc drift; style |
| test-strategy | Enumerate cases + write unit/integration/regression tests | "write tests", "what edge cases", post-fix | Enforcing test-first order mid-build (dev-workflow TDD) |
| context-compression | Deliberate keep/drop of **session** context; memory aging | Budget ≥ ~50%, before manual /compact | Doc files (→ docs-audit); code structure; routine memory writes |
| docs-audit | **Doc files** vs current code: current/stale/dead/gap | "are the docs stale", post-release doc pass | Session context (→ context-compression); code structure; net-new authoring |

Every pair not listed in §5 has non-overlapping triggers — the table above
resolves them directly.

---

## 4. Precedence when instructions conflict

Resolve conflicts in this fixed order (higher wins):

1. **Explicit user instruction, this turn.** Always beats a skill default.
2. **ECC user rules** (`~/.claude/rules/ecc/common/`). The pack operationalizes
   ECC; on conflict, ECC wins (dev-workflow's Context Rule already states this).
3. **A deterministic hook.** The branch-protection PreToolUse hook blocks a
   commit/push on a protected branch even if a skill — or the user in the moment —
   says "commit straight to main". This does not contradict rule 1: the hook
   enforces the branch *policy the user already configured* in
   `hooks/config/branch-policy.json`, and the compliant path (feature branch →
   PR) still delivers the user's actual goal. If the user genuinely wants no
   protection, the fix is to edit the policy file or disable the hook in `/hooks`,
   not to have the agent reason around a live guardrail. Satisfy the hook, don't
   bypass it.
4. **The active skill's Iron Law.** Non-negotiable within that skill's scope.
5. **The dedicated sibling over the dev-workflow default.** Tighter scope wins.
6. **General guidance / this reference.** The fallback when nothing above applies.

Corollaries used across the pack:
- **scope-creep fires before absorption.** A mid-build addition is named and
  classified before any skill builds it, regardless of which skill is active.
- **Verification beats assertion.** No skill claims tests passed, build succeeded,
  or a release is ready without the evidence in hand (see each skill's Iron Law
  and the handoff contract's `validated` field).

---

## 5. Overlapping-pair disambiguation

Only pairs that can *both* legitimately fire are listed. For each: who owns what,
where the boundary is, and the run order when both apply.

### Review / quality cluster

**code-review ↔ architecture-review** — *axis of the critique.*
code-review judges whether the diff is **correct** (bugs, security, scope);
architecture-review judges whether the code is **well-structured** (coupling,
layering), independent of correctness. A change can pass one and fail the other.
Order when both apply: architecture-review on the design, then code-review on the
implementation. Neither reports the other's findings.

**code-review ↔ ai-hygiene** — *correctness vs machine-authored style.*
ai-hygiene handles AI fingerprints (over-engineering, duplication, verbose naming,
AI prose tells, watermarks) and prevents them *as new code is written*; code-review
finds correctness bugs in a *finished* diff. "Does this look AI / over-engineered /
humanize this" → ai-hygiene. "Is this correct / any bugs / ready to merge" →
code-review.

**ai-hygiene ↔ architecture-review** — *both can say "too much abstraction", but not the same abstraction.*
ai-hygiene flags **AI-authored over-engineering in the unit being written** —
speculative params, a wrapper class for one call, YAGNI violations, at the
function/file scale, while the code is fresh. architecture-review flags
**structural over-abstraction across modules** — a layer that earns nothing, an
interface with one implementation shaping the whole dependency graph. Rule of
thumb: single new unit / "keep it simple" → ai-hygiene; cross-module structure /
"is this well structured" → architecture-review.

**code-review ↔ bug-triage** — *find vs rank.* code-review (or any source)
produces findings; bug-triage consolidates and severity-ranks a **pile** from one
or more sources. One review returning a handful of issues does not need triage.
Order: review → triage → fix. bug-triage never finds new bugs; code-review never
ranks an external pile.

**code-review ↔ test-strategy** — *flag the gap vs fill it.* code-review's A3
checks whether a new path *has* a test and flags the gap; test-strategy
**enumerates cases and writes** the tests. Order: review flags → test-strategy
fills → re-review.

**bug-triage ↔ architecture-review** — *subject of the ranked findings.*
Both emit ranked findings, but bug-triage ranks **defects** (things that are
wrong now) and architecture-review ranks **structural risks** (things that will
cost later). Route by whether the items are bugs or shape.

**docs-audit ↔ architecture-review** — *target of the audit: doc files vs. code structure.*
docs-audit checks whether doc files accurately describe what the code does now;
architecture-review checks whether the code's own structure (coupling, layering,
dependencies) is sound. "Review before v-next" or "is everything in order" can
trigger both as separate passes: architecture-review on the code, then docs-audit
on the docs. They do not substitute — a clean docs-audit says nothing about
structural health, and a sound architecture can have stale docs. Run order:
architecture-review first (confirms structure), then docs-audit (checks whether
docs still describe the confirmed structure).

### Lifecycle-artifact cluster (all read git, all produce text — the git range and audience disambiguate)

**commit-message ↔ pr-description ↔ changelog** — same history, three ranges and
three audiences:
- commit-message → **staged diff** → for the next developer reading `git log`.
- pr-description → **branch..base diff + commits** → for reviewers of this branch.
- changelog → **lastTag..HEAD** → for users upgrading, written as impact.
Pick by which range and audience the user named. They chain
(commit → PR → changelog) but never substitute for each other.

**changelog ↔ release-prep** — *write vs verify.* changelog **authors** the
entries; release-prep **verifies** an entry exists, is dated, and matches the
version — and never writes it. If release-prep finds only `[Unreleased]`, it
stops and routes to changelog, then resumes.

**release-prep ↔ commit-message** — release-prep hands off to commit-message for
the tag/sync commit message; it does not compose commit messages itself.

**docs-audit ↔ release-prep** — *accuracy vs readiness.* release-prep owns the
go/no-go **checklist** (version drift, tests pass, build clean, changelog entry
present) and never reads doc content beyond confirming the changelog entry exists.
docs-audit owns **doc-vs-code accuracy** (are the README, API docs, and in-repo
.md files still correct for the current implementation). A "pre-release pass on
everything" request can trigger both: run release-prep first for the go/no-go
verdict, then docs-audit for the doc-accuracy pass. They do not substitute for
each other — a passing release-prep says nothing about doc accuracy, and a
clean docs-audit says nothing about whether tests pass.

### Audit / prune cluster — disambiguated by the *target* of the audit

| The thing being audited | Skill |
|---|---|
| This conversation's **session context** (getting long, summarize) | context-compression |
| **Doc files** (README, CONTRIBUTING, in-repo .md) vs the code | docs-audit |
| The **code's own structure** (coupling, layering, deps) | architecture-review |

"Review before v-next" can legitimately mean architecture-review on the code and
docs-audit on the docs — two separate passes, not one skill.

### Proactive / cross-cutting

**scope-creep ↔ (any active skill)** — scope-creep does not replace the primary
skill; it interrupts to classify a mid-build addition, then hands control back.
It fires automatically inside dev-workflow and code-review sessions.

**context-compression ↔ dev-workflow (memory).** context-compression is the
**event** (budget crossed, deliberate compact) that decides keep/drop;
dev-workflow's `memory.md` is the routine read/write of `memory.json` outside a
compression event. Compression writes *through* the memory schema.

**test-strategy ↔ dev-workflow (TDD step).** dev-workflow's TDD step enforces
**test-first ordering** during active development; test-strategy **generates a
suite or plan** on request (often after code exists, e.g. a regression test for a
fix). Same domain, different moment.

---

## 6. Handoff contract (minimum state to pass between skills)

When one skill hands work to another, pass a compact handoff block — not the
conversation. Include only the fields the receiver needs; omit the rest.

```
HANDOFF
  task:        <one sentence — what the receiver must do>
  requirements:<the plan / acceptance criteria, if any>
  changed:     <files or symbols in scope; git range if relevant>
  decisions:   <decisions already made that constrain the receiver>
  findings:    <relevant findings from the sender, if any>
  validated:   <what is proven vs assumed — e.g. "tests: 12 pass (run at HEAD abc123)"
                or "tests: NOT run">
  unresolved:  <open questions the receiver may hit>
  next:        <the single next action>
```

Rules:
- **`validated` never launders an assumption into a fact.** If the sender did not
  run the tests, it says "NOT run" — the receiver must not report them as passing.
- The delegated code-reviewer (§B of code-review) gets exactly this shape: task,
  requirements, git range (`changed`), and nothing from the session history —
  that isolation is what makes its review independent.
- Prefer pointing at a durable source (a git range, an issue, a file) over
  copying its contents into the handoff.
