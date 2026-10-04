---
name: pr-description
description: >
  Use this to generate a structured pull request description from the current
  branch's diff and commit history when the user is opening a PR or asks what
  it should say — "write a PR", "draft a pull request", "PR description",
  "opening a merge request"; NOT for single-commit messages (commit-message),
  NOT for changelog or release notes (changelog / release-prep), and NOT for
  executing the branch, push, or merge operations (dev-workflow).
allowed-tools: [Bash, Read]
model: sonnet
---

# PR Description Generator

Produce a clear, complete pull request description that gives reviewers everything they
need without making them read the entire diff.

Standards reference: load `skills/dev-workflow/references/pr-standards.md` for size
thresholds, required section definitions, and the PR hygiene checklist.

## Quick examples

**In:** "write a PR description for this branch"
**Out:** size check (Step 0), then 5-section template (Context/Why, What Changed, Risk & Rollback, How to Test, Reviewer Focus) + PR hygiene checklist

**In:** "we're opening a merge request, what should it say?"
**Out:** same; if diff > 600 lines, split recommendation precedes the description

## Iron Law

The description is grounded in `git log` / `git diff` against the base branch, never
in conversation memory — because a PR body written from memory describes the intended
change while reviewers review the branch's actual content, and the two diverge
whenever the branch contains earlier commits or is missing something you think you
pushed. A PR missing a Context/Why section is incomplete — if the diff alone does not
reveal motivation, probe `git log` commit messages before concluding it is obvious.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "I've been working on this branch all session — I can write the PR from memory." | The branch may contain commits from before the session, or lack changes you think are pushed. Memory describes intent; the diff is the artifact under review. | Run the gather-context commands first, every time. |
| "The diff came back empty, but the user asked for a PR body, so I'll write one anyway." | An empty diff means wrong base branch, already merged, or already on main. A PR body over no diff is documentation of nothing. | Fire the guard: report the empty diff and the likely causes, produce no description. |
| "The Why is obvious from the What — I'll skip that section." | Why is the section reviewers judge the approach by. Skipping it moves the motivation question into review comments, where it costs a round-trip. | Write Why even when it feels redundant; one sentence beats absence. |
| "The diff is large but the user just wants the description — a size note would be off-topic." | PR size is reviewability. A 600-line diff reviewed as one unit means reviewers must read everything before judging any part. A split recommendation is part of the description service, not an interruption of it. | Run the size check (Step 0). If > 600 lines and not a mechanical rename/migration, output the split recommendation before proceeding. |
| "I've listed all the changes with bullet points — that's thorough." | Bullet points name things; they don't show them. A reviewer who reads "added Quick examples to all 13 skills" has zero information about what a Quick example looks like, whether it's useful, or what format it produces. Naming a change is not describing it. | For each significant change, include one concrete illustration: before/after diff snippet, a quoted excerpt from the new content, or a representative example of the output. |

---

## 0. Size check

```bash
BASE=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null | sed 's|^[^/]*/||' || echo main)
git diff "$(git merge-base HEAD "$BASE")"...HEAD --shortstat
```

Count additions + deletions. If the total exceeds **600 lines** and the diff is not a
mechanical rename or a generated migration file:

1. Output: _"This diff is N lines — large enough that reviewers will likely lose context across sections. Consider splitting before I write the description."_
2. Suggest the logical split: data model, business logic, test suite, or infrastructure as separate PRs.
3. Pause and wait for user confirmation before proceeding.

If the user confirms to proceed anyway, note the size in the What Changed section.

---

## 1. Gather context

```bash
BASE=$(git rev-parse --abbrev-ref @{upstream} 2>/dev/null | sed 's|^[^/]*/||' || echo main)
git log "$(git merge-base HEAD "$BASE")"..HEAD --oneline --no-merges
git diff "$(git merge-base HEAD "$BASE")"...HEAD --stat
git diff "$(git merge-base HEAD "$BASE")"...HEAD
```

**Guard:** if the diff is empty, check whether you're already on the base branch or the
branch has been merged. Tell the user: "No diff found — you may already be on the base
branch, or this branch has been merged." Don't produce an empty PR.

Also check the branch name for ticket numbers (e.g. `feature/PROJ-123-add-auth`) and
any issue references in commit messages. If there's no git context (user pasted a diff),
work from what was provided.

---

## 2. Analyse the changes

Answer these internally before drafting:

1. What does this PR do? (single sentence)
2. Why is this change needed?
3. How was it implemented? (non-obvious decisions only)
4. What could break, and how would you roll it back?
5. How was it tested?
6. What should reviewers focus on?

---

## 3. Choose a template based on PR size

### Standard PR (most cases)

```markdown
## Context / Why

[The problem being solved. Link to issue/ticket if there is one. One paragraph max.
This section is mandatory — a PR without motivation is unreviewable in context.]

## What Changed

[Approach taken. For each significant change, include one concrete illustration —
a before/after snippet, a quoted excerpt, or a representative example. A reviewer
should be able to judge the quality of a change from this section alone; if they
have to open the file to understand what changed, this section has failed.

Example of what this looks like in practice:
- Don't write: "Updated the diff range in pr-description."
- Do write: "Fixed diff range: was `git diff main..HEAD` (included base-branch commits on diverged branches), now `git diff $(git merge-base HEAD $BASE)...HEAD`."
- Don't write: "Added Quick examples to all 13 skills."
- Do write: "Each skill body now opens with two in/out pairs before the Iron Law, e.g. for code-review: **In:** 'anything I missed before I push?' **Out:** §A verdict block with Critical/Important/Minor findings."]

## Risk & Rollback

[What could break. How to revert if it does. "None" is acceptable but must be stated.]

## How to Test

[Reproducible steps a reviewer can follow to verify this works.]

## Reviewer Focus

[Where you want feedback. What you already feel confident about.]
```

### Small / cleanup PR (< ~10 lines, single purpose)

```markdown
[One sentence summary of what and why.]

Changes:
- [Bullet 1]
- [Bullet 2]
```

### Breaking-change PR

Prepend before the standard template:

```markdown
> ⚠️ **Breaking Change** — [What breaks and what consumers must do.]

## Migration

[Step-by-step migration instructions.]
```

---

## 4. Polish

- **Context / Why** is the most important section — reviewers judge the approach from motivation. More than one paragraph suggests the PR scope may be too broad.
- Branch has a ticket number → add `Closes #123` or Jira link at the bottom.
- Diff touches migrations, DB schema, or infra → add a **Deployment Notes** section.

---

## 5. Output

Present the final description in a single markdown code block ready to paste into
GitHub / GitLab / Bitbucket.

Then output the **PR Hygiene Checklist** as a separate block for the author to
complete before marking Ready for Review:

- [ ] Self-reviewed the diff (ran code-review §A)
- [ ] No debug code, console.logs, or commented-out blocks
- [ ] CI is green (or flaky test documented inline)
- [ ] Commits are clean — no "WIP", "fixup", or "oops" in final history
- [ ] PR title follows Conventional Commits format
- [ ] Breaking changes called out in description and commit footer

Follow with one offer: "Want me to adjust tone, length, or add any sections?"

---

## Next Step

After opening the PR → use **code-review** (§A self-review or §B delegated) to catch
issues before reviewers see it. If reviewers request changes, **dev-workflow** handles
the branch and merge operations.
