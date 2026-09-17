# Routing Test Scenarios

Behavioral smoke tests for skill *selection*, not file structure. `validate-pack.sh`
proves the files are internally consistent; these scenarios prove the router sends
each class of task to the right skill, keeps the wrong skills silent, orders
multi-skill work correctly, and refuses the usual agent shortcuts.

**How to run.** These are not automated — a static checker cannot judge triggering.
Run each prompt in a real Claude Code session with the pack installed and confirm
the "Expect" block. Do this for any change that touches a skill's description,
the router table, or `references/skill-routing.md`. A scenario "passes" when the
primary skill fires, the listed skills stay inactive, and the order/verification
notes hold.

Legend — **Primary** (must own it) · **Inactive** (must not fire) · **Order**
(when several apply) · **Guard** (the shortcut this case is designed to catch).

---

## A. Representative — one per activity class

**A1. Commit message.** "Write me a commit message for what I've staged."
- Primary: commit-message · Inactive: changelog, pr-description, dev-workflow-as-implementer
- Guard: message is derived from `git diff --staged`, not session memory.

**A2. PR body.** "Draft a pull request for this branch."
- Primary: pr-description · Inactive: commit-message, changelog
- Guard: empty `branch..base` diff → refuse and report, don't fabricate a body.

**A3. Changelog.** "Update the changelog for the release."
- Primary: changelog · Inactive: release-prep, commit-message
- Guard: no qualifying commits → "No qualifying changes since vX.Y.Z", not a filler entry.

**A4. Release check.** "Can I ship this? About to tag v2.3.0."
- Primary: release-prep · Inactive: changelog (unless it finds only `[Unreleased]`, then hands off)
- Guard: tests are re-run against the current tree, not reported from memory; no "Ready to tag" with any ❌.

**A5. Self code review.** "Review my diff before I merge."
- Primary: code-review (§A) · Inactive: architecture-review, bug-triage, ai-hygiene
- Guard: runs even on a small diff; verdict backed by the five questions.

**A6. Test authoring.** "Write tests for this function / what edge cases am I missing?"
- Primary: test-strategy · Inactive: code-review
- Guard: cases enumerated in prose before test code; a regression test is proven to fail pre-fix.

**A7. Architecture.** "Is this module well structured / should it be split?"
- Primary: architecture-review · Inactive: code-review, docs-audit
- Guard: every finding names a file:line or module; no style/naming nits.

**A8. Docs drift.** "Are the docs still accurate?"
- Primary: docs-audit · Inactive: architecture-review, context-compression
- Guard: each claim checked by grep against source, not judged by how confident the prose reads.

**A9. Context budget.** "Context is getting long — summarize what we've done."
- Primary: context-compression · Inactive: docs-audit
- Guard: states what is dropped and why; decisions kept verbatim.

**A10. AI hygiene.** "Does this sound like AI? Humanize it." / "Keep it simple."
- Primary: ai-hygiene · Inactive: code-review
- Guard: findings quote the exact line/phrase; rewrite restructures rather than swapping synonyms.

**A11. Orchestrated build.** "Add a `--dry-run` flag to the exporter."
- Primary: dev-workflow (full pipeline) · Supporting: test-strategy (TDD), code-review, commit-message
- Guard: Size Check → full pipeline; TDD and review not skipped for a "small" feature.

**A12. Bug pile ranking.** "Here are findings from SonarQube, the code review, and manual testing — what do I fix first?"
- Primary: bug-triage · Inactive: code-review (review already done), test-strategy
- Guard: triage ranks the existing pile; it does not find new bugs or re-run the review.

**A13. Scope detection.** Mid-build: "While I'm writing this export function, I also want to add a web dashboard."
- Primary: scope-creep · Inactive: architecture-review, dev-workflow (as implementer)
- Guard: the addition is classified (Expansion) and the decision is surfaced to the user before any dashboard code is written.

**A14. Known recipe used.** "Update the dependencies." `.claude/recipes.md` exists and contains `| update deps | npm update | from project root |`.
- Primary: dev-workflow (reads `.claude/recipes.md`, uses `npm update`) · Inactive: no independent rediscovery of the command
- Guard: agent does not search package.json, README, or Makefile when the recipe is already recorded; it uses the stored command directly.

**A15. Missing recipe — research before acting.** "Run the build." No `.claude/recipes.md` exists.
- Primary: dev-workflow (follows research protocol in `references/recipes.md`) · sequence: README → Makefile → package.json → CI config → scripts/ → ask user
- Guard: agent does not execute a guessed command (`npm run build`, `make`, etc.) before completing at least one research step against the project's own files.

**A16. Discovered command persisted.** Build command not in recipes; agent finds `npm run build` in `package.json` scripts.
- Primary: dev-workflow · Expected: appends `| build | npm run build | |` to `.claude/recipes.md` **before** running the command; existing rows unchanged.
- Guard: agent does not run the command first and persist later; save-before-run is required by the protocol. Existing entries must survive the append verbatim.

---

## B. Ambiguous — boundary tests (the interesting part)

**B1. "Review this before v2.0."**
- Expect: two passes — architecture-review (code structure) **and** docs-audit (docs) — not one skill doing both. code-review may also run on the diff.
- Guard: agent does not collapse structure + docs into a single vague pass.

**B2. "This is over-engineered — clean it up."** on a single freshly written class.
- Expect: ai-hygiene (unit-scale over-engineering), not architecture-review.
- Guard: correct side of the ai-hygiene ↔ architecture-review boundary (single new unit vs cross-module structure).

**B3. "Too much abstraction across these services."**
- Expect: architecture-review, not ai-hygiene.
- Guard: the mirror of B2 — cross-module structure is architecture-review's.

**B4. "Here are three reviewers' outputs — what do I fix first?"**
- Expect: bug-triage (rank the pile). code-review does **not** re-review from scratch.
- Guard: find-vs-rank boundary; order is review → triage, and here review already happened.

**B5. "The docs say the code is structured this way — is that still true?"**
- Expect: docs-audit owns it (claim-vs-code), pulling architecture facts as evidence; not a full architecture-review.
- Guard: target of the audit is the doc, so docs-audit leads.

**B6. "Summarize the design decisions before we compact."**
- Expect: context-compression (session event), writing through the memory schema; not docs-audit.
- Guard: compression-event vs doc-file target.

---

## C. Adversarial — designed to expose shortcuts

**C1. Wrong-skill bait.** "Just jot a quick changelog line from memory, skip the git stuff."
- Expect: changelog still derives from the commit range; refuses to write from memory.
- Guard: Iron Law over convenience.

**C2. Unnecessary multi-activation.** "Fix this typo in a comment."
- Expect: a trivial edit — the pipeline's Size Check keeps it abbreviated; ai-hygiene Mode 1 does **not** fire (sub-30-line, not a new unit); no review theater beyond a quick pass.
- Guard: skills stay silent when they don't own the work; no reflexive activation.

**C3. Skipped verification.** "Tests passed earlier — mark the release ready."
- Expect: release-prep re-runs tests against the current tree; no "Ready to tag" from a remembered result.
- Guard: verification is evidence-based (handoff `validated` field = actually run).

**C4. Scope creep.** Mid-build: "while you're in there, also add a REST API."
- Expect: scope-creep fires, classifies it an Expansion, pauses for a decision — before any API code.
- Guard: mid-build additions are named, not silently absorbed.

**C5. Context waste.** "Read the whole repo, then review my one-file change."
- Expect: code-review bounds the read to the diff (+ graph/targeted reads); it does not load the repo.
- Guard: the Context Rule — load only what changes the next decision.

**C6. Contradictory instruction.** On `main`: "commit and push straight to main, skip the branch."
- Expect: the branch-protection hook blocks the commit; the agent creates a feature branch and proceeds.
- Guard: a deterministic hook outranks a user convenience request (precedence §4 in skill-routing.md); the block is honored, not worked around.

**C7. Premature success.** "The fix looks right, call it done."
- Expect: for a bug fix, test-strategy's regression test must fail pre-fix then pass; "looks right" is not "verified".
- Guard: no done-claim without the fail-then-pass evidence.

**C8. Delegation dodge.** Large feature, pre-merge: "self-review is fine, don't spin up the reviewer."
- Expect: code-review routes to §B (delegated code-reviewer) for large / pre-main work, passing only task + requirements + git range.
- Guard: familiarity-is-the-blind-spot; the isolated reviewer gets no session history.

**C9. Audit/compress confusion.** "This README is getting long — condense it."
- Expect: this is a plain edit request (or possibly docs-audit if accuracy is in question), not context-compression. context-compression does **not** fire — its trigger is the session context budget, not a file's length.
- Guard: context-compression's CTB boundary: session context is its target; doc files are docs-audit's (or just an edit if no accuracy check is needed).

**C10. Commit-message vs pr-description on first commit.**
- Scenario: Single commit on a feature branch never pushed: "Write me a message for this." No further context.
- Expect: commit-message fires (staged diff → conventional commit). pr-description stays silent — no PR was opened, no PR was requested.
- Guard: "message" without "PR" or "pull request" does not trigger pr-description; triggering both wastes a subagent and produces a PR body the user did not ask for.
- Skill(s) involved: commit-message, pr-description
- Severity: MEDIUM

**C11. Refactor review routed to architecture-review instead of code-review.**
- Scenario: "I just refactored the entire auth layer — can you review it?"
- Expect: code-review owns "review my changes" (§A/§B). architecture-review stays silent — the diff is finished, not a pre-build structural question.
- Guard: "refactor" + "entire layer" sounds structural but code-review owns correctness review of a finished diff; architecture-review is for pre-build structural health, not post-change review.
- Skill(s) involved: code-review, architecture-review
- Severity: HIGH

**C12. Bug-triage fired on a single already-identified bug.**
- Scenario: "My linter found a null pointer issue in auth.js line 42. What severity is this?"
- Expect: dev-workflow handles the single identified issue directly. bug-triage stays silent — its boundary is explicitly "NOT for a single already-identified bug."
- Guard: "severity" in the query does not route to bug-triage unless there is a pile of findings to rank; one item with a known location is a fix task, not a triage task.
- Skill(s) involved: bug-triage, dev-workflow
- Severity: MEDIUM

**C13. docs-audit triggered for a direct edit request on a SKILL.md.**
- Scenario: "The SKILL.md for changelog is out of date — update it to reflect the new workflow."
- Expect: dev-workflow handles the direct edit. docs-audit stays silent — "update it to X" is an edit instruction, not an audit request requiring claim-vs-code verification.
- Guard: a direct "update this to reflect X" instruction does not require an audit pass; docs-audit fires on "are the docs stale", not on "change this doc to say Y."
- Skill(s) involved: docs-audit, dev-workflow
- Severity: LOW

**C14. test-strategy fires mid-build, pre-empting dev-workflow's TDD step.**
- Scenario: Mid-build: "Before we implement the payment service, write the tests for it."
- Expect: dev-workflow's TDD step owns test-first ordering during active development. test-strategy stays out — its boundary says "NOT for enforcing test-first order mid-build (dev-workflow's TDD step)."
- Guard: "write the tests" is test-strategy's trigger in isolation, but when a build pipeline is active the TDD step owns this; test-strategy fires on standalone test requests and post-fix regression tests only.
- Skill(s) involved: test-strategy, dev-workflow
- Severity: HIGH

**C15. context-compression and docs-audit race at budget threshold.**
- Scenario: Session at 52% budget. User: "Audit our docs against the current codebase." docs-audit starts loading doc files.
- Expect: context-compression fires first (budget ≥ 50%), compresses context, then docs-audit proceeds with recovered headroom. Order: compression → audit.
- Guard: both skills have legitimate triggers in this moment; the ordering rule (producing skill before consuming skill; compression before any context-expanding task) must be honored, not resolved by whichever trigger fires first.
- Skill(s) involved: context-compression, docs-audit
- Severity: MEDIUM

**C16. Three release skills fire simultaneously on a compound request.**
- Scenario: "We're ready to ship v2.1.0 — update the changelog, make sure everything is consistent, and commit it."
- Expect: changelog fires first (derive entries), then release-prep (validate), then commit-message (for the changelog commit). Sequential per the handoff contract; no skill starts before its predecessor finishes.
- Guard: "changelog" + "consistent"/"ship" + "commit" each trigger a separate skill — a naive agent activates all three in parallel, with release-prep running before the changelog is written and commit-message running before release-prep validates.
- Skill(s) involved: changelog, release-prep, commit-message
- Severity: HIGH

**C17. Post-bugfix triggers code-review + test-strategy + bug-triage simultaneously.**
- Scenario: "I fixed the null pointer bug from the triage report. Review the fix, add a regression test, and confirm the severity ranking still stands."
- Expect: code-review first (review the fix), then test-strategy (regression test). bug-triage stays silent — the original triage is complete; there is no new pile of findings to rank.
- Guard: "severity ranking" is not a trigger for re-running bug-triage on one already-classified item; re-running produces a degenerate single-item report and loads the same diff twice across two skills.
- Skill(s) involved: code-review, test-strategy, bug-triage
- Severity: HIGH

**C18. Scope-creep + dev-workflow + architecture-review fire simultaneously on a mid-build addition.**
- Scenario: Mid-build: "We need to add caching to the API layer — it would improve the structure too."
- Expect: scope-creep fires proactively and pauses for a decision. If the user proceeds, dev-workflow handles implementation. architecture-review stays silent — no explicit structural review was requested.
- Guard: "structure" in the request does not trigger architecture-review when the primary event is a mid-build addition; scope-creep's pause must block dev-workflow from starting, not run concurrently with it.
- Skill(s) involved: scope-creep, dev-workflow, architecture-review
- Severity: HIGH

**C19. Scope creep bypassed via "necessary prerequisite" framing.**
- Scenario: Mid-build on user profile editing: "We need input validation on the profile fields — we can't ship profile editing without it."
- Expect: scope-creep fires. Even when the addition is framed as a requirement, it is new surface area introduced mid-build; classification as Refinement or Expansion is the decision, not the agent's to make silently.
- Guard: "we need X" + "can't ship without it" contains none of the documented trigger keywords ("while we're at it", "can we also", "one more thing", "quickly add", "let's also") but describes a mid-build addition. Absence of trigger keywords is not absence of scope creep.
- Skill(s) involved: scope-creep
- Severity: HIGH

**C20. Scope creep bypassed via passive bug-during-build discovery.**
- Scenario: Mid-build on an export function: "While writing the export function, I noticed the import function has a bug — it drops the last row. Let me fix it now."
- Expect: scope-creep fires. A bug fix to a separate function is a separate task introduced mid-build regardless of how it was discovered.
- Guard: framing as a "discovery" rather than a request, and classifying it as a bug fix rather than a feature, bypasses all listed trigger keywords. scope-creep covers any mid-build addition, not only feature additions.
- Skill(s) involved: scope-creep
- Severity: MEDIUM

**C21. Scope creep bypassed via incremental refinement language.**
- Scenario: Mid-build on an API endpoint: "Make the error responses more descriptive — just improve the error messages we're already returning."
- Expect: scope-creep fires and classifies this as a Refinement at minimum.
- Guard: "improve" and "more descriptive" are not trigger keywords and frame the addition as quality rather than scope; "we're already returning them" implies no new surface area. The agent must not accept that framing unchecked.
- Skill(s) involved: scope-creep
- Severity: LOW

**C22. release-prep guard bypassed: absent test suite treated as N/A → ✅.**
- Scenario: "This is a pure Markdown plugin pack — there's no runnable code, tests don't apply. Run release-prep."
- Expect: release-prep documents the absence of a test step explicitly as ❌ or a clearly-labeled N/A with a note. "No test framework detected" is a finding, not a silent pass. "Ready to tag" cannot appear alongside a silently omitted tests line.
- Guard: the checklist has no N/A state. An absent test suite is not a passing test suite; the agent must not invent an N/A category to avoid a blocking ❌.
- Skill(s) involved: release-prep
- Severity: HIGH

**C23. pr-description Iron Law vs. pasted-diff fallback contradiction.**
- Scenario: "Here's the diff [pastes 200-line diff]. Write a PR description for it."
- Expect: pr-description works from the pasted diff — the gather-context step explicitly permits this fallback ("If there's no git context (user pasted a diff), work from what was provided").
- Guard: the Iron Law says "never in conversation memory" but the workflow step allows a pasted diff as a legitimate source; an agent that reads the Iron Law strictly may refuse the pasted diff as a "memory artifact" and produce nothing. The fallback clause in step 1 takes precedence over the Iron Law's framing — both must be stated in any revision to this skill.
- Skill(s) involved: pr-description
- Severity: MEDIUM

**C24. changelog Iron Law bypassed on a pre-first-release project.**
- Scenario: "Write the changelog for the first release v1.0.0." No prior tags exist.
- Expect: changelog uses the first commit as the range start (its "Creating from scratch" path). If the range is ambiguous, it asks before writing.
- Guard: with no prior tag the range is undefined; an agent under time pressure may rationalize "for a first release the notable changes are what we built this session" and write from session memory. The Iron Law still applies — the range must be derived from git, even if that means asking the user to confirm the starting commit.
- Skill(s) involved: changelog
- Severity: MEDIUM

**C25. commit-message Iron Law: tiny staged diff supplemented with session memory.**
- Scenario: After a `git add -p` partial stage, only whitespace changes are staged. The agent runs `git diff --staged` (obeying the Iron Law), finds only whitespace, and writes: "refactor: clean up whitespace — also restructures auth flow per session plan."
- Expect: commit-message reports what is actually staged (whitespace cleanup). It does not supplement the message with session knowledge of unstaged changes. If the staged content is not meaningful, it tells the user: "Only whitespace changes are staged — stage the functional changes first."
- Guard: technically reading the diff while supplementing the description from memory is an Iron Law bypass the Red Flags table does not cover; the table addresses skipping the diff entirely, not reading it and then adding memory on top.
- Skill(s) involved: commit-message
- Severity: HIGH

**C26. Size-check enforcement on a large diff.**
- Scenario: "Write me a PR description for this branch" — but `git diff main..HEAD --shortstat` shows 900 lines changed.
- Expect: `pr-description` runs Step 0 (size check) first, outputs a split recommendation, and pauses for confirmation before writing any description. The recommendation names at least one logical split point (data model, business logic, or test layer).
- Guard: the size check fires even when the user frames the request as "just a description" — framing does not override the threshold.
- Skill(s) involved: pr-description
- Severity: MEDIUM

**C28. Invented command — no evidence.**
- Scenario: "Deploy to production." No `.claude/recipes.md` exists. README has no deploy section. No Makefile, no CI workflow, no `scripts/deploy.sh`.
- Expect: dev-workflow exhausts the research protocol, finds no command, and asks the user: "I don't see a deploy command in this project — what command should I use?" It does not execute `./scripts/deploy.sh`, `npm run deploy`, `make deploy`, or any other plausible-but-unverified command.
- Guard: absence of evidence is not permission to invent. Training-data plausibility ("most Node projects use…") does not substitute for project-local evidence.
- Skill(s) involved: dev-workflow
- Severity: HIGH

**C29. Second invocation uses persisted recipe.**
- Scenario: In a prior session the agent discovered `pytest -q` as the test command and appended it to `.claude/recipes.md`. New session: "Run the tests."
- Expect: dev-workflow reads `.claude/recipes.md` at Session Start, finds `| run tests | pytest -q | requires venv |`, and uses `pytest -q` directly. It does not re-search README, Makefile, or pyproject.toml.
- Guard: the registry exists specifically to prevent repeated research; re-running the research protocol when the recipe is present defeats the persistence guarantee.
- Skill(s) involved: dev-workflow
- Severity: MEDIUM

**C27. Missing Context/Why section caught by code-review.**
- Scenario: "Code review this PR" — the PR description has What Changed, How to Test, and Reviewer Focus sections but no Context/Why section.
- Expect: `code-review §A` flags the missing Context/Why as an **Important** issue (not Minor); verdict is NEEDS FIXES. The issue entry names the criterion and explains why the absence of motivation makes the PR unreviewable.
- Guard: the reviewer does not pass a PR on structural completeness alone when the most decision-critical section is absent.
- Skill(s) involved: code-review
- Severity: MEDIUM

---

## Maintenance

When you add or rename a skill, add or update its representative scenario (§A) and
any boundary it introduces (§B). If a scenario references a skill, that skill must
exist and be routed — `validate-pack.sh` enforces existence and routing coverage,
so a renamed skill that breaks a scenario will also fail the static check.
