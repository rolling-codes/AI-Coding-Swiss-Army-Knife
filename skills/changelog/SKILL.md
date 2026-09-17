---
name: changelog
description: >
  Use this to generate or update CHANGELOG.md from git commit history in Keep
  a Changelog format when the user wants changes documented — "update
  changelog", "release notes", "what changed since last release"; NOT for
  single commit messages (commit-message), NOT for PR bodies (pr-description),
  and NOT for the full pre-tag validation pass (release-prep).
allowed-tools: [Bash, Read, Edit, Write]
model: sonnet
---

# Changelog Generator

Create or update `CHANGELOG.md` following [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
A good changelog is written for humans — it describes what changed and why it matters,
not what files were touched.

## Iron Law

Entries are derived from the actual commit range and written as user-facing impact —
because the changelog is the upgrade contract, and both failure modes break it:
writing from memory invents or omits changes, and transcribing commit subjects
documents the diff instead of what an upgrader will notice.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "The commit subjects are already descriptive — I'll transcribe them into sections." | Commit subjects describe the diff for developers; the changelog describes impact for upgraders. Transcription produces exactly the `refactor(auth): extract middleware` anti-example below. | Rewrite each qualifying commit as the change a user experiences. |
| "No commits qualify, but the user asked for an entry — I'll write something to fill the version." | A fabricated entry corrupts the upgrade record permanently. | Use the empty-release output: "No qualifying changes since vX.Y.Z." and stop. |
| "chore:/ci: commits never matter — skip them all without reading." | The filter is impact-based, not type-based. A `chore:` that bumps a dependency with breaking behaviour is precisely the entry an upgrader needs most. | Skim skipped types for user-visible impact before dropping them. |

---

## 1. Find the starting point

```bash
git tag --sort=-version:refname | head -10
```

Use the most recent version tag as the lower bound. If no tags, use the initial commit
or branch point. Also read the existing CHANGELOG.md for the last version entry.

---

## 2. Collect commits since last release

```bash
# With a tag:
git log v1.2.3..HEAD --oneline --no-merges

# Without a tag:
git log origin/main..HEAD --oneline --no-merges

# More context on any commit:
git show <sha> --stat
```

**Empty release:** if there are no commits since the last tag (or no qualifying commits
after filtering), say so explicitly:

```
No qualifying changes since v1.2.3. CHANGELOG.md not updated.
```

Don't write a changelog entry for a version with no user-facing changes.

---

## 3. Categorise commits

| Section | What goes here | Conventional Commits hint |
|---------|----------------|--------------------------|
| **Added** | New features, new endpoints, new options | `feat:` |
| **Changed** | Behaviour changes to existing functionality | `refactor:`, `perf:`, breaking `feat:` |
| **Deprecated** | Features that will be removed in a future release | — |
| **Removed** | Features removed in this release | — |
| **Fixed** | Bug fixes | `fix:` |
| **Security** | Vulnerability fixes | `security:`, `fix(security):` |

**Skip silently:** `chore:`, `style:`, `test:`, `ci:` — unless the user-facing impact is
significant. Significant means: a user upgrading would notice or care. Examples that
qualify: a `chore:` that upgrades a dependency with breaking behaviour changes, a `ci:`
that changes the published artifact format. Examples that don't: lint config tweaks,
reformatting, test infrastructure changes.

Skip merge commits and version bump commits.

---

## 4. Write human-readable entries

Each entry should describe the *user-facing change*, not the internal implementation.

**Bad:** `refactor(auth): extract token validation into middleware`
**Good:** `Session tokens are now validated on every request, not just at login`

Rules:
- Start with a verb in past tense: "Added", "Fixed", "Removed"
- Link to PR or issue in parentheses: `(#123)`
- One entry per logical change — split a commit that covers two things
- Mark breaking changes: `**Breaking:** renamed \`/users\` to \`/accounts\``

---

## 5. Write or update CHANGELOG.md

### Creating from scratch

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ...
```

### Updating an existing file

Prepend a new `## [Unreleased]` block immediately after the `# Changelog` header.
Do not modify existing version entries.

When cutting a release, replace `[Unreleased]` with version and date:
```markdown
## [1.3.0] - 2024-03-15
```

---

## 6. Version guidance (if asked)

- **MAJOR** bump: any breaking change
- **MINOR** bump: new feature, fully backward-compatible
- **PATCH** bump: bug fix only, no new features, no breaking changes

---

## 7. Output

Write changes directly to `CHANGELOG.md` and show the user only the new entry (not the
whole file) for review.

---

## If this fails

- No git history available → ask the user to paste the commit log or describe changes manually
- CHANGELOG.md is malformed → show the user the first 20 lines and ask before overwriting

---

## Next Step

After updating the changelog → continue to **release-prep** to validate version
consistency, run tests, and get a go/no-go checklist before tagging.
