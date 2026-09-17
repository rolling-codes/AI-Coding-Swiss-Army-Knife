---
name: context-compression
description: >
  Use this to manage token budget explicitly during long sessions — summarize,
  decide keep vs. drop, and age out stale context — when the context budget
  crosses ~50%, before a deliberate manual /compact, or on "context is getting
  long", "summarize what we've done", "what can we drop"; NOT for
  documentation drift (docs-audit), NOT for code structure (architecture-review),
  and NOT for routine session-memory writes outside a compression
  event (dev-workflow's memory reference).
allowed-tools: [Read, Edit]
model: haiku
---

# Context Compression Skill

Compaction that happens *to* a session loses whatever wasn't explicitly preserved.
This skill makes the keep/drop decision deliberate instead of leaving it to a
generic auto-summarizer. Model: `fast`.

## Iron Law

Compression is an explicit keep/drop classification with the drops stated —
because silent loss is the failure this skill exists to prevent, and
auto-compaction already provides silent loss for free.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "Budget's only at 40% but the session feels long — I'll compress now to be safe." | Speculative compression spends tokens now for hypothetical savings later, violating the lazy-load principle this pack follows. | Check the budget number, not vibes. Under threshold and no user ask → don't compress. |
| "I'll write a really tight summary — brevity is the whole point." | A summary that's compact but useless on reload has failed at its one job. | Optimize for retrievability: task, decisions, open work survive verbatim; brevity comes out of the rest. |
| "Dropping this decision saves tokens and we probably won't need it again." | Decisions are cheap to keep and load-bearing to lose — one dropped decision can cost a rework worth thousands of tokens. | Decisions are keep-as-is category, always. Cut from the bottom of the retrieval priority list instead. |

---

## Step 1: Check Budget, Not Vibes

Don't compress on a hunch. Trigger points:
- Context budget ≥ 50% (compress here, well before auto-compaction, so the
  keep/drop decision is deliberate instead of forced late)
- User explicitly asks
- About to start a subtask that needs a large isolated read (delegate instead of
  compressing, if delegation fits — see dev-workflow's `sub-agents.md`)

If budget is comfortably under threshold, don't compress preemptively — it costs
tokens now to maybe save tokens later, and speculative work violates the lazy-load
principle this whole pack follows.

---

## Step 2: Classify What's in Context

| Category | Keep as-is | Compress to summary | Drop entirely |
|---|---|---|---|
| Active task instructions | ✅ | | |
| Decisions made this session | ✅ (they're cheap and load-bearing) | | |
| File contents read for a now-finished subtask | | ✅ | |
| Full diffs already committed | | | ✅ (git has them) |
| Dead-end exploration (tried, reverted) | | one-line note | rest |
| Long tool output (test logs, build output) already acted on | | ✅ pass/fail + key line | |
| Conversation pleasantries / retries that succeeded on retry | | | ✅ |

Retrieval priority when rebuilding a summary: task instructions > decisions >
open work > everything else. If forced to cut further, cut from the bottom of
that list first.

---

## Step 3: Write the Summary

Keep it retrievable, not just short — a summary that's compact but useless on
reload has failed at its one job.

```
## Session summary (compressed at [budget]% )

**Task:** [what's being worked on]
**Done:** [bullet list, past tense, one line each]
**Decisions:** [decision — one-line reason], ...
**Open:** [what's still pending, in priority order]
**Dropped:**
  - [what was dropped] — [why safe to drop, e.g. "recoverable from git log"]
  - [next item if any]
```

If dev-workflow is installed, this maps directly onto `.claude/memory.json`'s
schema — write there instead of a bare chat summary so it survives the session,
not just the current compaction.

Durable knowledge surfaced while compressing — a decision with its rationale, an
architecture change, a lesson worth keeping across projects — belongs in the
knowledge graph via the **graphify** skill (`/graphify`), not just in the session
summary; see dev-workflow's `references/memory.md` § Knowledge Base Layer. If
graphify isn't installed, keep those items in `memory.json` and say the handoff
was skipped.

---

## Step 4: Memory Aging

Not everything in long-lived memory (`.claude/memory.json`) stays relevant forever.
When writing memory, check existing entries:
- `open_work` items marked done → remove, they're in git history now
- `decisions` superseded by a later decision → mark `supersedes` or drop the older one
- `dont_do` entries no longer true (constraint lifted) → remove, don't let stale
  rules accumulate and mislead future sessions
- Session summaries older than the current one → don't keep a running log, overwrite

---

## Rules

- Compression is a judgment call about relevance, not a token-minimization contest —
  don't drop a decision to save 20 tokens if it'll cause rework later
- Never drop the active task instructions or unresolved user constraints
- State what was dropped and why — silent loss is worse than explicit loss
- Prefer pointing at a durable source (git, a file, an issue) over keeping a
  summary of something that's fully recoverable elsewhere
