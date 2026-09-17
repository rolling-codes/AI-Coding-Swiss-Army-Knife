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

## Iron Law

The description is grounded in `git log` / `git diff` against the base branch, never
in conversation memory — because a PR body written from memory describes the intended
change while reviewers review the branch's actual content, and the two diverge
whenever the branch contains earlier commits or is missing something you think you
pushed.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "I've been working on this branch all session — I can write the PR from memory." | The branch may contain commits from before the session, or lack changes you think are pushed. Memory describes intent; the diff is the artifact under review. | Run the gather-context commands first, every time. |
| "The diff came back empty, but the user asked for a PR body, so I'll write one anyway." | An empty diff means wrong base branch, already merged, or already on main. A PR body over no diff is documentation of nothing. | Fire the guard: report the empty diff and the likely causes, produce no description. |
| "The Why is obvious from the What — I'll skip that section." | Why is the section reviewers judge the approach by. Skipping it moves the motivation question into review comments, where it costs a round-trip. | Write Why even when it feels redundant; one sentence beats absence. |

---

## 1. Gather context

```bash
git log main..HEAD --oneline --no-merges
git diff main..HEAD --stat
git diff main..HEAD | head -600
```

**Guard:** if `git diff main..HEAD` is empty, check whether you're already on main or the
branch has been merged. Tell the user: "No diff found between this branch and main —
you may already be on main, or this branch has been merged." Don't produce an empty PR.

Also check the branch name for ticket numbers (e.g. `feature/PROJ-123-add-auth`) and
any issue references in commit messages. If there's no git context (user pasted a diff),
work from what was provided.

---

## 2. Analyse the changes

Answer these internally before drafting:

1. What does this PR do? (single sentence)
2. Why is this change needed?
3. How was it implemented? (non-obvious decisions only)
4. What could break?
5. How was it tested?
6. What should reviewers focus on?

---

## 3. Choose a template based on PR size

### Standard PR (most cases)

```markdown
## What

[1–3 sentences. What does this PR accomplish?]

## Why

[The motivation. What problem does this solve, or what feature does it deliver?
Link to the issue/ticket if there is one.]

## How

[Notable implementation decisions, tricky areas, or architectural choices.
Skip if the implementation is obvious from the diff.]

## Testing

[How was this tested? What test cases cover this?]

## Checklist

- [ ] Tests pass locally
- [ ] No new lint errors
- [ ] Docs / comments updated where needed
- [ ] No hardcoded secrets or environment values
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

- **What** section over 3 sentences → note the PR may be too large.
- **Why** is the most important section — reviewers judge the approach from motivation.
- Branch has a ticket number → add `Closes #123` or Jira link at the bottom.
- Diff touches migrations, DB schema, or infra → add a **Deployment Notes** section.

---

## 5. Output

Present the final description in a single markdown code block ready to paste into
GitHub / GitLab / Bitbucket. Follow with one offer: "Want me to adjust tone, length,
or add any sections?"

---

## Next Step

After opening the PR → use **code-review** (§A self-review or §B delegated) to catch
issues before reviewers see it. If reviewers request changes, **dev-workflow** handles
the branch and merge operations.
