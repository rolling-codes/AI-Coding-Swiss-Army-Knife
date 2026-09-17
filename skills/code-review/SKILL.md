---
name: code-review
description: >
  Use this to review code changes before merge — self-review of your own diff,
  or dispatching the code-reviewer subagent for an independent pass on larger
  work — when the user wants changes checked before pushing or merging:
  "review my changes", "is this ready to merge", "self-review", "check my
  diff", "anything I missed"; NOT for reviewing someone else's PR
  (dev-workflow's code-review-routing reference), NOT for structural/coupling
  health (architecture-review), and NOT for ranking piles of existing findings
  (bug-triage).
allowed-tools: [Read, Grep, Glob, Bash, Agent]
model: sonnet
---

# Code Review

Vet completed work before it cascades. Two modes, same goal — catch issues while they're
cheap to fix.

## Iron Law

Every diff gets reviewed before merge, regardless of size or author confidence —
because small and familiar changes are exactly where author blindness does the most
damage, and the review's value comes precisely from the cases where it feels
unnecessary.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "It's a one-line change — review would be theater." | One-liners reach production with the same force as features. Size measures effort, not risk. | Run §A. On a true one-liner it takes two minutes. |
| "I just wrote this carefully, with tests — a re-read adds nothing." | The same eyes that made a blind spot cannot see it. The checklist forces a different lens (worst-case input, silent-wrong-path) than the one that wrote the code. | Work the five questions as a sceptical colleague, not as the author. |
| "Delegating costs a subagent spin-up — self-review is basically equivalent for this feature." | For large work, your familiarity *is* the blind spot §B exists to counter. A missed critical issue costs far more than a dispatch. | Follow the mode table. Major feature or pre-main merge → §B. |

---

## ⚡ Pick a mode first

| Situation | Mode |
|---|---|
| Small/medium diff, want a sceptical second pass on your own work | **[§A — Self-Review](#a--self-review)** |
| Major feature, before merge to main, want a fresh *independent* perspective, or main context is getting long | **[§B — Delegated Review](#b--delegated-review)** |
| Both — self-review first, then delegate the parts you're unsure about | Run §A, then §B |

**Default:** self-review (§A) for ordinary changes. Delegate (§B) when the work is large
enough that your own familiarity with it has become a blind spot.

> **Scope creep note:** if the user introduces new requirements *during* this review
> ("oh, while you're here, can we also add…"), the **scope-creep** skill fires automatically
> before proceeding.

---

# §A — Self-Review

Read the diff the way a sceptical colleague would — not the way you wrote it.

## A0. Get the diff

```bash
git diff main..HEAD --stat    # orient first
git diff main..HEAD           # full diff
```

If the diff touches more than ~400 lines or ~8 files, consider splitting into smaller PRs.

## A1. The five questions

Work through these for the diff as a whole, not line by line.

**1. Does this do exactly what I said it does?**
Re-read the PR description or commit message. Check that the diff matches the stated
intent — no more, no less. Stray changes (reformatted unrelated code, debug prints,
commented-out blocks) should be cleaned up.

**2. What's the worst-case input or state this code can receive?**
For every new function or branch: what happens with null/None/empty, zero, a very large
value, a concurrent write, a missing config key, an unauthenticated caller? If you
didn't think about it, flag it.

**3. Is there a path where this silently does the wrong thing?**
Look for: swallowed exceptions, default return values that mask errors, boolean flags
that could be misread, off-by-one loops, data written partially.

**4. Does this change anything outside its stated scope?**
Check for: shared state mutations, config changes, schema migrations, event handlers
registered globally, module-level code that runs on import.

**5. If this breaks in production, how long before I notice?**
Is the code path covered by a test? Is there logging? If it fails, does it fail loudly?
If the answer is "I'd find out from a user report," add observability before merging.

## A2. Line-by-line pass

### Logic
- Conditions with precedence or short-circuit bugs
- Loop bounds, slice indices, off-by-one
- Mutating a collection while iterating
- Async code not awaited, or awaited in the wrong place

### Contracts
- Function now accepts/returns something different but callers weren't updated
- Public API changed without a migration path (CLI flag, slash command parameter,
  REST endpoint, WPF binding, plugin interface)
- Type annotations that lie about what the code actually does

### Security (for anything user-facing)
- Unvalidated user input used in a path, query, format string, or subprocess call
- Credentials, tokens, or keys in code or comments
- Permissions checked after the work is already done

### Hygiene
- Debug prints, `console.log`, `print()`, `Debug.WriteLine()` left in
- TODO comments added without a ticket
- Commented-out code (delete it — git history keeps it)
- Hardcoded values that belong in config

## A3. Test coverage check

```bash
# Python
pytest --tb=short -q 2>&1 | tail -5

# .NET
dotnet test --verbosity minimal 2>&1 | tail -5
```

For every new code path: is there a test that would fail if you broke it?

**Project-specific conventions:** check the repo's existing test helpers before writing
new tests — most codebases have a fixture/builder pattern (a fake context, a test
client, a mock factory) that new tests should reuse rather than duplicate. New CLI
commands → smoke test at minimum. New service classes → unit test with a mocked
dependency, not a live one.

## A4. Output

```
Self-review: <branch or PR title>
Files: N | Lines added: +X / removed: -Y
Verdict: MERGE / NEEDS FIXES / NEEDS DISCUSSION

── Issues ──────────────────────────────────────────
[file.py:42] Silent exception swallow — bare `except:` loses the error type.
  → Change to `except SpecificError as e:` and log or re-raise.

[commands/fun.py:17] No test for the empty-username path.
  → Add a FakeContextBuilder case with ctx.user.display_name = "".

── Hygiene ─────────────────────────────────────────
[services/installer.cs:89] Debug.WriteLine left in.

── Clean ───────────────────────────────────────────
Logic: ✅  Contracts: ✅  Security: ✅
```

Verdict rules:
- **NEEDS FIXES** — any logic, contract, or security issue.
- **NEEDS DISCUSSION** — a design decision that's debatable, not clearly wrong.
- **MERGE** — hygiene only, or no issues.

## A5. Close

> Want me to fix any of these, write the missing tests, or draft the merge commit message?

---

# §B — Delegated Review

Dispatch a code-reviewer subagent to catch issues before they cascade. The reviewer gets
precisely crafted context for evaluation — never your session's history.

**Core principle:** Review early, review often.

## When to delegate

**Mandatory:**
- After completing a major feature
- Before merge to main
- After each task, if working through a multi-task plan

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing a complex bug

## How to request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Dispatch the code-reviewer agent (ships with this plugin):**

Pass in the task message: a brief description of what was built, the plan or
requirements it should satisfy, and the BASE and HEAD SHAs. Run the graph
availability check per dev-workflow's `references/graph-tools.md` (if
installed); when a graph exists, also include
`KNOWLEDGE_GRAPH: graphify-out/graph.json` in the task message — the briefing
rule in dev-workflow's `references/sub-agents.md` applies to this dispatch too.
The agent runs in its own context window and returns only findings, so the
review costs the main conversation almost nothing.

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if the reviewer is wrong (with reasoning)

**If the subagent is unavailable** (running outside Claude Code, or in a context without
sub-agent support): fall back to §A self-review, which covers the same ground more
manually. Note the limitation to the user.

## Integration with workflows

**Plan-based work:** review after each task or at natural checkpoints — catch issues
before they compound.

**Ad-hoc development:** review before merge, and when stuck.

**If the reviewer is wrong:** push back with technical reasoning, show code/tests that
prove it works, or request clarification — deference to a wrong finding is as costly
as ignoring a right one.

---

## Next Step

- **MERGE verdict / issues fixed:** use **pr-description** to write the PR, then **dev-workflow** to merge
- **Issues found:** if findings are numerous or complex, pipe them into **bug-triage** to rank and prioritize before fixing
- **Scope expansion noticed during review:** **scope-creep** fires automatically
