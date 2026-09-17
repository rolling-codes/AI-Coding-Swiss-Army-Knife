---
name: bug-triage
description: >
  Use this to consolidate, deduplicate, and severity-rank a pile of raw bug
  findings into one actionable report when multiple bugs, findings, or review
  results need ranking — "triage these", "which bugs should I fix first",
  "consolidate findings", or a dump of multiple reports or review-agent
  output; NOT for fixing the bugs (dev-workflow), NOT for reviewing a diff to
  find new issues (code-review), and NOT for a single already-identified bug.
allowed-tools: [Read, Grep, Glob]
model: sonnet
---

# Bug Triage

Turn raw findings from one or more review sources into a single, ranked report that a
maintainer can act on without wading through noise.

## Iron Law

Optimise for the shortest list that contains every finding that genuinely matters —
because a 40-item list gets ignored, and a buried critical costs more than every
dropped style nit combined. The cost of a false negative is high, but noise is how
false negatives happen in practice.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "Keeping everything, including style nits, looks more thorough — nothing will seem missed." | Inflating the list buries the criticals. Thoroughness is measured by what's dropped defensibly, not by what's kept. | Apply the filter rules. Style and dead-code items go to footnotes or nothing. |
| "These two findings hit the same line, so they're duplicates — merge them." | The dedup key is root cause, not location. Merging distinct causes hides one real bug behind another. | Merge only findings sharing a root cause; same-line different-cause stays separate. |
| "I can't verify this speculative finding quickly, so I'll park it at Medium as a compromise." | Severity is not a hedge for confidence — a speculative Medium is defined noise under the rubric. | Either verify it up to [likely], or apply the rule: speculative Medium/Low gets dropped, speculative Critical/High stays with the tag. |

---

## 0. Handle the no-findings case

If all sources report zero findings, say so explicitly:

```
Bug hunt: <scope>. No actionable findings.
```

Then stop — don't fabricate observations to fill the report.

---

## 1. Deduplicate

The same root cause frequently appears across multiple sources. Merge entries that share
the same root cause into one, listing every class it belongs to. Two findings on the
same line with *different* root causes stay separate.

---

## 2. Filter

**Drop entirely:**
- Speculative findings with no concrete trigger, data flow, or interleaving.
- Pure style or naming issues (no semantic consequence).
- Issues in dead or cold code with negligible blast radius — footnote at most.

**Downgrade (don't drop):**
- Security findings that never cross a trust boundary → lower severity by one level.
- Race conditions requiring extremely precise timing under unrealistic load.

**Never drop:**
- Anything that causes silent data corruption, even if the trigger is rare.

---

## 3. Severity rubric

| Axis | High | Medium | Low |
|------|------|--------|-----|
| **Blast radius** | Shared util / hot path / public API | Internal service / moderate traffic | Single leaf caller |
| **Likelihood** | Common input or every request | Plausible edge case or occasional race | Needs adversary + multiple preconditions |
| **Cost when fired** | Data corruption / RCE / authz bypass / guaranteed leak | Crash or outage / data exposed to wrong user | Degraded perf / recoverable error |

- **Critical** — High cost AND (high blast radius OR easily triggered). Fix before next deploy.
  - *Example:* An unauthenticated endpoint that returns another user's data on any request.
- **High** — Serious cost, realistic trigger, meaningful blast radius. Fix this sprint.
  - *Example:* A crash on malformed input in a public API endpoint that only some clients send.
- **Medium** — Real bug, limited trigger or contained blast radius. Schedule it.
- **Low** — Minor or very hard to hit. Backlog.

Round up when the code is widely depended on. When a graph is available (per
dev-workflow's `references/graph-tools.md`), score the blast-radius axis from
the affected symbol's edge count rather than estimating it — the lookup is one
tool call and removes the axis most prone to guesswork.

---

## 4. Confidence annotation

- **[confirmed]** — Complete path from trigger to consequence, no assumptions.
- **[likely]** — Strong evidence; one plausible assumption.
- **[speculative]** — Multiple unverified assumptions. Only include if Critical or High.

Drop speculative Medium/Low findings.

---

## 5. Report format

```
Bug hunt: <scope>. <N> findings — <c> critical, <h> high, <m> medium, <l> low.

## Critical

### 1. [file.ext:line] Short title [confirmed]
**Classes:** logic-edge, security
**Trigger:** How the bad state is reached.
**Consequence:** What happens when it fires.
**Fix direction:** Minimal correct approach (describe, don't implement).

## High
...
## Medium
...
## Low
...

*Footnotes (dead-code / style-only, if any):*
```

No fix code. No exploit code. Within a severity group: order by blast radius descending.

---

## 6. Close

End with a dynamic question referencing the top finding(s):

> Should I start a fix plan for **[top finding title]**, or dig deeper into **[second finding]**? I can also open GitHub issues for any of these.

---

## Next Step

- **To fix findings:** use **dev-workflow** to branch, implement, and open a PR
- **After fixing:** use **code-review** to verify the fix before merging
- **To track findings as issues:** `gh issue create --title "[severity] short title" --label "bug"`
