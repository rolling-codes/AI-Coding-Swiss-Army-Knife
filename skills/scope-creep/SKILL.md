---
name: scope-creep
description: >
  Use this to detect and assess scope creep when a new feature, change, or
  dependency is introduced mid-build — fires proactively, without being asked,
  on "while we're at it", "can we also", "one more thing", "quickly add",
  "let's also", or a mid-build request that changes the original goal or
  expands surface area; NOT for the original task itself (dev-workflow), NOT
  for ranking bug findings (bug-triage), and NOT for defining scope on a
  project that hasn't started.
allowed-tools: [Read]
model: haiku
---

# Scope Creep Detection Skill

A new feature or change is being requested mid-build. Before acting on it, assess whether this is a natural extension or genuine scope creep that needs a conscious decision.

## Quick examples

**In:** "while we're adding OAuth, let's also add social login" (mid-build)
**Out:** scope flag — estimated cost (+2d, 3 new deps), risk of expanding now, recommendation: defer to backlog or proceed with explicit decision

**In:** "can we quickly update the profile page too?" (mid-build)
**Out:** scope flag — original goal vs. new addition, risk assessment, whether this belongs in a separate PR

## Iron Law

Every mid-build addition gets named and classified before any code is written for it —
because silently absorbed scope changes are decisions nobody made, and the project
grows without anyone having chosen that.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "It's a small ask, I can do it in 30 seconds — flagging it is more disruptive than doing it." | Creep is cumulative: each absorbed 'small ask' resets the baseline for the next one. The assessment takes less time than most adds. | Run the classification. Refinements pass through in one line; only Expansions/Pivots pause. |
| "The user asked for it directly, so it's the new scope, not scope creep." | Direct user requests are exactly what scope creep is made of. The skill exists for informed consent, not refusal. | Name it, classify it, then follow the user's call — including 'just do it anyway'. |
| "We're mid-review/mid-debug; a scope check now would derail the flow." | Mid-flow is precisely when additions sneak in unexamined — that's why this skill fires automatically there. | The format is six lines, not a lecture. Present it and move on. |

---

## Step 1: Reconstruct the Original Scope

Look back through the conversation to extract:

- **Original goal** — what was the project supposed to do when first defined?
- **Agreed boundaries** — anything explicitly ruled out or deferred
- **Current build state** — what has already been built or decided?

If the original scope was never written down anywhere, note that — a poorly defined scope is itself a risk.

---

## Step 2: Characterize the New Request

Classify what's being asked:

| Type | Description | Example |
|------|-------------|---------|
| **Refinement** | Making something already planned work better | "make the error message clearer" |
| **Extension** | Adding to something in scope but not yet built | "add a second output format we discussed" |
| **Expansion** | New capability outside original scope | "also make it work as a web API" |
| **Pivot** | Changes the core goal | "actually, let's make it real-time instead of batch" |

Refinements and extensions are usually fine. Expansions and pivots need flagging.

---

## Step 3: Impact Assessment

For Expansions and Pivots, assess:

**Complexity delta**
- How much additional code/logic does this add?
- Does it introduce new dependencies?
- Does it require rethinking existing architecture?

**Risk delta**
- Does this change something already built and working?
- Does it couple previously independent parts?
- Does it push the project into territory that wasn't researched?

**Time delta**
- Is this a 5-minute add or a 2-hour rework?
- Be honest, not optimistic.

---

## Step 4: Present the Assessment

**Every classification, including Refinements, requires visible output.** A Refinement
passes through in one line; an Expansion or Pivot pauses for a decision. Silence is not a
valid output for any mid-build addition.

Format your response clearly:

```
## Scope Check: [Brief description of new request]

**Classification:** [Refinement / Extension / Expansion / Pivot]

**Original scope:** [1 sentence]
**What's being added:** [1 sentence]

**Impact:** [Low / Medium / High] — [1-2 sentences explaining why]

**Recommendation:** [one of the three below]
```

### Recommendations

**✅ Proceed** — This fits the original scope. Building now.

**⚠️ Proceed with note** — This is slightly outside scope but low risk. Adding it, but flagging so you're aware the project has grown. Consider whether it needs to be in the research plan.

**🛑 Pause — scope decision needed** — This is a meaningful expansion. Options:
  - Accept: build it now, but [specific consequence]
  - Defer: finish original scope first, tackle this after — log it as a GitHub issue so it's not lost (`gh issue create --title "..."`)
  - Replace: swap this for something in original scope instead

For **🛑 Pause**, always present all three options and wait for the user to choose before doing anything.

---

## Rules

- Never silently absorb scope creep — always name it
- Never refuse to build the thing — the goal is informed decisions, not blockers
- Keep the assessment short — this shouldn't feel like a lecture
- If the user says "just do it anyway", proceed — your job is to flag, not gatekeep
- If the original scope was never clearly defined, say so — vague origins make everything harder to assess
- Trigger keywords ("while we're at it", "can we also", "one more thing", "quickly add", "let's also", "while you're in there") are sufficient to trigger this skill but not necessary — any mid-build addition that changes the original goal or expands surface area triggers it regardless of phrasing
- This skill fires automatically during **dev-workflow** and **code-review** sessions — no explicit invocation needed

---

## Next Step

After resolving the scope decision:
- **Accepted / Proceed:** return to **dev-workflow** to continue building
- **Deferred:** create a GitHub issue to capture it, then return to **dev-workflow**
- **Replaced:** update the plan before continuing
