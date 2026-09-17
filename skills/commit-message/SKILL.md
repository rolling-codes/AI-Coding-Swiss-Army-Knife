---
name: commit-message
description: >
  Use this to generate a Conventional Commits-compliant message from staged git
  changes when changes are staged and a message is needed — "write a commit
  message", "help me commit", "what should I commit this as"; NOT for PR
  descriptions or changelog entries (pr-description / changelog), and NOT for
  deciding what to stage or executing the commit itself
  (dev-workflow handles git operations).
allowed-tools: [Bash, Read]
model: haiku
---

# Commit Message Generator

Produce a commit message following [Conventional Commits](https://www.conventionalcommits.org/).
Good commit messages are the cheapest form of documentation.

## Iron Law

The message is derived from the actual staged diff, never from conversation memory —
because what you remember changing and what is actually staged routinely diverge
(forgotten files, partial staging), and a message describing unstaged intent
documents something that didn't happen.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "I wrote this code in-session — I know what changed, no need to run `git diff --staged`." | Staged state and session memory diverge constantly: partial stages, untracked files, changes from outside the session. | Run the inspection commands every time. They cost seconds. |
| "The diff is huge; I'll describe the overall theme instead of reading it." | Large diffs are exactly where mixed concerns hide — and a mixed-concern commit is the one that most needs an honest message or a split. | Orient with `--stat`, sample the diff, and flag multi-concern splits explicitly. |
| "The type doesn't really matter — feat/fix/chore are close enough here." | Types drive downstream tooling: the changelog skill parses them into release sections. A mislabeled type corrupts release notes later. | Pick the dominant type deliberately; note secondary concerns in the body. |
| "I read the diff, but I also know from the session that more was changed — I'll include that in the message too." | Supplementing the diff with session memory violates the Iron Law as surely as skipping the diff. The message describes what is staged, not what you remember intending. | Describe only what is staged. If meaningful changes are not staged, tell the user: "Stage the functional changes first." |

---

## 1. Inspect staged changes

```bash
git diff --staged --stat        # file overview
git diff --staged               # full diff (sample large diffs with | head -400)
git status                      # catch untracked files the user may have forgotten
```

If nothing is staged, check `git diff --stat` (unstaged) and tell the user — they may
have forgotten to `git add`.

**Forgotten files:** if `git status` shows untracked or modified-but-unstaged files that
look related to the staged changes, surface them explicitly: "You also have `src/auth.ts`
unstaged — did you mean to include it?" Don't silently ignore them.

---

## 2. Choose the commit type

| Type | When to use |
|------|-------------|
| `feat` | New feature or user-visible behaviour added |
| `fix` | Bug fix |
| `refactor` | Code restructured — no behaviour change, no bug fixed |
| `perf` | Performance improvement |
| `test` | Tests added or corrected (no production code change) |
| `docs` | Documentation only |
| `style` | Formatting, whitespace — zero logic change |
| `chore` | Build scripts, dependencies, tooling, CI config |
| `revert` | Reverting a previous commit |

When a change spans types, pick the dominant type and note the rest in the body.

---

## 3. Identify the scope (optional but recommended)

The component, module, or layer affected. Keep it short and consistent with how the
codebase refers to its own parts. Examples: `auth`, `api`, `db`, `ui`, `config`,
`payments`, `bot`, `plugin`, `installer`.

---

## 4. Write the subject line

Format: `type(scope): description`

- **Imperative mood** — "add" not "added", "fix" not "fixes"
- **Max 72 characters** — aim under 60 for clean rendering
- **No period** at the end
- **Lowercase** after the colon
- **Be specific** — "fix bug" is useless; "fix null check in session expiry" is not

---

## 5. Write the body (when needed)

Include when: the *why* isn't obvious, non-obvious implementation choice was made, or
there are caveats/TODOs. Blank line between subject and body. Wrap at 72 chars.
Explain **why**, not what — the diff shows what.

---

## 6. Add footers

```
BREAKING CHANGE: <what broke and what consumers must do>
Fixes #123
Closes #456
Co-authored-by: Name <email>
```

Breaking changes must be in the footer, or signal with `!` after the type:
`feat(api)!: rename /users endpoint to /accounts`

**Co-author trailers:** add `Co-authored-by:` when the commit was pair-programmed,
AI-assisted in a meaningful way, or involves significant contribution from another party.

---

## 7. Output

Present the final message in a code block, ready to copy:

```
feat(auth): add OAuth2 login via Google

Replaces username/password flow with OAuth2 to support SSO and reduce
credential management overhead.

Closes #234
```

Follow with one offer: "Want me to adjust scope, wording, or add a body?"

If the diff spans multiple logical concerns, say so: "This touches X and Y — consider
splitting into two commits."

---

## Next Step

After committing → if preparing a release, continue to **changelog** to document
what changed, or **pr-description** to open a pull request.
