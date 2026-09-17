# PR Standards

Loaded by `pr-description` for size thresholds, required sections, and hygiene.
Loaded by `code-review` and `code-reviewer` for the code quality bar and severity mapping.

---

## PR Size

- **Target:** ≤ 400 lines changed (additions + deletions). Under 200 is ideal.
- **Hard cap:** > 600 lines → recommend splitting into stacked PRs before writing the description — unless the diff is a mechanical rename or a generated migration file.
- **Split rule:** smallest unit = one logical concern (e.g. data model, business logic, UI layer, test suite as separate PRs).

---

## Required Sections

Every standard PR description must have all five sections. A missing section is an incomplete PR.

1. **Context / Why** — the problem being solved, the ticket/issue link. One paragraph max. No Why = unreviewable — it moves the motivation question into review comments and costs a round-trip.
2. **What Changed** — approach taken and non-obvious design decisions. Skip the obvious; the diff speaks for itself.
3. **Risk & Rollback** — what could break; how to revert if it does. "None" is acceptable but must be stated explicitly, not omitted.
4. **How to Test** — reproducible steps a reviewer can follow to verify the change works.
5. **Reviewer Focus** — where you want feedback; what you already feel confident about.

---

## PR Hygiene Checklist

Author completes before marking Ready for Review:

- [ ] Self-reviewed the diff (ran code-review §A)
- [ ] No debug code, console.logs, or commented-out blocks
- [ ] CI is green (or flaky test documented inline)
- [ ] Commits are clean — no "WIP", "fixup", or "oops" in the final history
- [ ] PR title follows Conventional Commits format
- [ ] Breaking changes called out in description and commit footer

---

## What Makes a Bad PR

Anti-patterns to flag when encountered:

- Description written from memory instead of the actual diff
- "While I was in there…" scope creep mixed with the stated concern
- No Context/Why section — the diff is reviewable but not judgeable
- Draft PR never converted to Ready
- CI red with no explanation

---

## Code Quality Bar

Used by `code-review §A` and the `code-reviewer` agent to evaluate every change. Each criterion has a concrete pass and fail state.

| Criterion | Pass | Fail |
|---|---|---|
| **Naming** | Intent-revealing without needing a comment | Requires a comment to explain what a name means |
| **Function size** | < 50 lines; single responsibility | > 50 lines, or does more than one thing |
| **Immutability** | Returns new objects; no in-place mutation | Mutates caller's data; produces hidden side effects |
| **Nesting depth** | ≤ 4 levels; early returns used | > 4 levels; happy path buried in conditionals |
| **Error handling** | Explicit at every trust boundary | Silent swallow; `console.error` only; no fallback |
| **Dead code** | None | Commented-out blocks, unused variables, unreachable branches |
| **Magic values** | Named constants for thresholds, delays, limits | Bare numbers or strings with no label |

---

## Severity Mapping

Used consistently across `code-review §A`, `code-reviewer`, and issue reporting:

| Level | Definition | Merge impact |
|---|---|---|
| **Critical** | Data loss risk, security hole, auth bypass, broken core functionality | Blocks merge — NEEDS FIXES always; never MERGE |
| **Important** | Logic bug, missing error handling at a trust boundary, broken contract, test gap | Fix before merge; ≥ 1 Important = NEEDS FIXES |
| **Minor** | Naming, nesting, dead code, magic values, hygiene | Document and carry forward as tech debt; MERGE if no Critical/Important |
