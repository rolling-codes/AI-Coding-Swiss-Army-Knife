---
name: dev-workflow
description: >
  Use this to orchestrate everyday development work — GitHub operations
  (branches, issues, PRs, CI, merges), the five-step pipeline (Research →
  Plan → TDD → Code Review → Commit), session memory, and model routing —
  when given a development task or asked "what should I work on next",
  "open an issue", "create a branch", "push this up", "check the CI",
  "merge this"; NOT for work a dedicated pack skill owns (commit messages,
  PR descriptions, changelog entries, release checks, code review passes,
  bug triage, mid-build scope flags, architecture/docs/context audits,
  test generation) — route to that skill and return.
---

# dev-workflow

Purpose: orchestrate development work through the five-step pipeline (Research →
Plan → TDD → Code Review → Commit) and route specialised tasks to their dedicated
pack skills — because unpiped work loses the constraints each step enforces, and
unrouted work silently loses the sibling skill's guardrails.

**Core principle: load nothing speculatively.** Every file read must be justified
by the current task. This file is a router plus a pipeline; the detailed procedures
live in `references/`, loaded one at a time, only for the task at hand.

## Environment Verification

The pipeline and the context rules lean on ECC. Before running the full
pipeline, verify these exist:

- `~/.claude/rules/ecc/common/development-workflow.md`
- `~/.claude/rules/ecc/common/git-workflow.md`
- `~/.claude/rules/ecc/common/testing.md`
- `~/.claude/rules/ecc/common/code-review.md`
- `~/.claude/rules/ecc/common/performance.md` — context-management foundation

If any are missing, stop and tell the user which ones — the pipeline's
test-coverage, review, and context-budget requirements come from those files, so
proceeding without them means enforcing rules that aren't defined.

**Optional integration — Graphify (knowledge base):** if the graphify skill is
installed (invoked via `/graphify`), durable knowledge — decisions with rationale,
architecture changes, lessons — flows to the knowledge graph at session end; see
`references/memory.md` § Knowledge Base Layer. If graphify is absent,
`.claude/memory.json` remains the only persistence layer: note the gap to the
user, don't block on it.

## Iron Law

The five steps are sequential and mandatory, because each step enforces constraints
the next step depends on: research informs planning, planning informs test structure,
tests inform implementation shape, review catches blindness, commit follows
verification. Break the chain and the implementation is not trusted.

## Red Flags — How Agents Rationalize Around This Skill

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "This matches a sibling skill, but I already have the context loaded — faster to do it inline than route." | Doing sibling work inline silently skips that skill's guardrails (e.g. commit-message's forgotten-files check, pr-description's empty-diff guard). Speed is not a substitute for the checks. | Route to the sibling skill and return. The routing table exists precisely for the moment routing feels unnecessary. |
| "This task is mid-sized — full pipeline is overkill, so I'll run a hybrid: skip research and planning, keep the coding." | The Size Check gate is binary on purpose. A "hybrid" is unaudited step-skipping wearing a reasonable name. | Run the Size Check. If the answer isn't clearly "tiny", it's the full pipeline. |
| "I'll preload a few reference files now so I don't interrupt the flow later." | Speculative loads burn the token budget this pack exists to protect, and most preloaded files go unused. | Load exactly one reference file, when the task actually needs it. |
| "The user/codebase is experienced, so research/planning can be abbreviated." | That's an assumption about what's documented, not evidence. No documentation is the baseline assumption. | Read what actually exists first. If docs are absent or stale, research is mandatory. |
| "I can code first and write tests that match; it's faster to iterate." | Tests-first structures the implementation before you lock into a shape. Tests-after retrofit structure to existing code — the structure wasn't guiding, it was following. | Write one test first. Let it fail. Watch what it forces you to design. |
| "The changes are small/scoped/internal, so code review can be cursory or skipped." | Small changes are where blindness does the most damage — no review means no catch. ECC mandates review; this is not optional. | Full code review, every time. Size and confidence are not exemptions. |

## Skill Routing (check first)

Some tasks belong to a dedicated skill. Route there before doing any work, because
each sibling carries guardrails this skill does not duplicate:

| Task | Skill |
|---|---|
| Write a commit message for staged changes | → **commit-message** |
| Draft a pull request description | → **pr-description** |
| Update CHANGELOG.md for a new version | → **changelog** |
| Validate / checklist before tagging a release | → **release-prep** |
| Review my own diff before merging (or get it reviewed) | → **code-review** |
| Rank or consolidate bug findings from multiple sources | → **bug-triage** |
| New feature/change introduced mid-build | → **scope-creep** (fires automatically) |
| Coupling/cohesion/layering/structural health check | → **architecture-review** |
| Generate unit/integration/edge-case/regression tests | → **test-strategy** |
| Manage token budget, summarize, or age out stale context | → **context-compression** |
| Audit/prune docs against what the code actually does | → **docs-audit** |

**Disambiguating the three "assess and prune" skills** — the target of the audit
is the disambiguator:

| Question | Skill |
|---|---|
| Is *this conversation's context* getting long / should I summarize? | **context-compression** |
| Do the *docs* (README, CONTRIBUTING, etc.) still match the code? | **docs-audit** |
| Is the *code's structure* itself sound (coupling, layering, dependencies)? | **architecture-review** |

A request can trigger more than one — "review this before v2.0" reasonably means
**architecture-review** on the code and **docs-audit** on the docs, as two separate
passes.

If the request matches a sibling, invoke that skill and return. Everything else
continues below.

## The Pipeline

### Size Check (first thing)

Before anything else, ask: **Is this a one-liner fix, typo, or pinpoint refactor in
code I'm actively editing right now, in this session?**

- **Yes** → Abbreviated pipeline: Research/Plan can be verbal or skipped (you have
  live context), but TDD and Code Review are still mandatory.
- **No or unsure** → Full pipeline, all five steps in order. Being conservative here
  is better than rationalizing.

### Research

Run if you don't have current knowledge of the target area — "current" means this
session, not "I've seen this code before". Familiarity from months ago is not
evidence.

Ask: What does the target already document? Where should I search (GitHub code
search, vendor docs, package registries)? What changed since I last touched this?

Deliverable: a one-paragraph summary of what you learned.

### Plan

Answer four questions in writing (one-liners are fine on small work):
- What is being built?
- Why — what problem does it solve?
- How — rough approach, dependencies, risks?
- What are the test points — what must pass for this to work?

"I'll figure it out as I code" is the step you're skipping, not a plan.

### TDD

Tests come first, because test-first imposes structure on the implementation before
the implementation exists; code-then-test means the code drove the structure.

1. Write one test expressing the intended behavior (RED)
2. Run it; watch it fail — confirms the test is real
3. Write minimal implementation to pass (GREEN)
4. Refactor (IMPROVE)
5. Repeat until complete; verify 80%+ coverage per ECC

If you wrote code first, return here. Retrofitted tests do not satisfy this step.

### Code Review

Route to the **code-review** skill (self-review for ordinary diffs, delegated
code-reviewer agent for large work). Address all CRITICAL and HIGH findings; fix
MEDIUM when possible. Mandatory per ECC — time pressure, scope, and confidence do
not exempt it.

### Commit

Once review is clear: verify CI passes, resolve conflicts, ensure the branch is up
to date, route to **commit-message** for the message, push with `-u` if the branch
is new.

## Task Router (GitHub ops, debugging, delegation)

For orchestration work outside the pipeline, resolve the model alias via
`model-registry.json`, load exactly one reference file, do the work:

| Task type | Model alias | Load |
|---|---|---|
| Plan / decompose / triage | `fast` | `references/planning.md` |
| PR / branch / push / merge | `standard` | `references/github-operations.md` |
| Code review of someone else's PR | `standard` | `references/code-review-routing.md` |
| Write / refactor / implement | `standard` | `references/coding-tasks.md` |
| Architecture / security | `deep` | `references/coding-tasks.md` |
| Debug complex issue | `deep` | `references/debugging.md` |
| Issues / project tracking | `fast` | `references/issues.md` |
| Delegate subtask | task-dependent | `references/sub-agents.md` |
| Resume session | `fast` | `references/memory.md` (§ Load) |
| End session / context long | `fast` | `references/memory.md` (§ Write) |
| Detect repo type / stack / conventions | `fast` | `references/repo-detection.md` |

No entry matches → don't guess; read `references/context-management.md` for the
general discovery rules.

Model names live in `model-registry.json` only — resolve
`task_map.<task> → alias → API string` at call time; never hardcode a model string,
because registry updates must not require touching this file.

## Context Rule (always active)

> Before reading any file: "Will this materially improve my ability to complete
> the task?" If not clearly yes — do not load it.

Context management is grounded in ECC: this rule and
`references/context-management.md` operationalize the Context Window Management
guidance in `~/.claude/rules/ecc/common/performance.md`. Where the two disagree,
ECC wins — it's the user-level rule set.

Depth by task: routine change → target file only; feature work → interface +
relevant files; architecture/security/debugging → full chain.

Load order — stop when sufficient:
`task instructions → docs → architecture → tests → relevant source → adjacent source`

Full rules → `references/context-management.md`

## Branch Protection (enforced by hook, policy is external)

The plugin's PreToolUse hook blocks `git commit` / `git push` on branches matching
`hooks/config/branch-policy.json` (default: `main`, `master`, `develop`,
`release/*`, `hotfix/*`). The hook contains no branch names — edit the policy file
to change protection. If blocked, create a feature branch and retry.

## Notes — Run Free

If the user is at a stage this skill doesn't cleanly fit ("review someone else's
PR", "should I refactor or rewrite?"), hand off to the narrower skill or reference
and return. This skill is the default case; don't force it when a narrower fit
exists.
