---
name: ai-hygiene
description: >-
  AI-fingerprint hygiene for code and prose. Prevent AI tells when writing new code or
  adding a dependency (reuse, simplicity, deps); remove them from existing code or prose;
  handle watermarks. Use when the user says "keep it simple", "sound like
  AI?", "humanize this", "audit this code", "remove AI patterns", or "watermark/SynthID".
  NOT for correctness/bug review (code-review) or trivial edits.
allowed-tools: [Read, Grep, Glob, Bash]
model: sonnet
---

# ai-hygiene

Manage the fingerprints that mark content as machine-generated, across its whole
lifecycle: **prevent** them when writing new code, **detect and remove** them in code and
prose that already exists, and answer **watermark** questions. This merges the preventive
discipline (formerly `lean-code`) with the detection/humanization catalog (formerly
`deai`) into one skill with a shared toolchain.

## Iron Law

Never hand back AI-authored content without checking it against the documented
fingerprints — because the model reading its own output always judges it clean, so the
unchecked pass is exactly the one that ships the tells. Prevention checks before the code
exists; detection checks what's already on the page. Neither is optional just because the
output *looks* fine.

## Mode router

Read what the user gave you and pick a mode — infer, don't interrogate. When content is
supplied with no instruction, default to Prose Audit for prose, Code Audit for code.

| Situation | Mode |
|---|---|
| About to write substantial new code / add a dependency / "keep it simple" | **1. Prevent** |
| Existing code to check for AI smells / "audit this code" | **2. Code Audit** |
| Text pasted, no rewrite asked / "does this sound like AI" | **3. Prose Audit** |
| "humanize this" / "fix it" / "rewrite this" | **4. Prose Rewrite** |
| Bare invocation, no content / "give me the list" | **5. Cheat Sheet** |
| Watermarks, SynthID, "will this pass detection" (technical) | **6. Watermark Bypass** |

---

## Mode 1: Prevent (writing new code)

Fires when about to author a substantial NEW unit — a file, module, class, component,
endpoint, or multi-function feature (~30+ new lines) — or add a dependency. Skip it for
edits, single-function changes, bug fixes, refactors, or sub-30-line work; forcing the
ritual on trivial changes is its own waste. Four pillars, in order:

1. **Reuse-first** — before writing a new function/util, Grep/Glob for something that does
   80%+ of the job; call or extend it. Write net-new only when the search comes up empty,
   and say what you searched. (Counters the documented duplication/refactoring collapse.)
2. **Simplest-thing-that-works** — the plainest version that meets the *stated* need. No
   speculative params, abstraction layers, or config for a use nobody asked for (YAGNI).
   If you feel the pull to add flexibility, name the concrete real future use or cut it.
3. **Complexity / size budget** — functions <~50 lines, files <~800, nesting ≤4 (early
   returns), no needless mutation. Complexity is invisible to token-by-token generation,
   so **confirm with `scripts/complexity_check.py <path>`** rather than trusting a read.
4. **Dependency verification** — before importing third-party code, confirm it exists and
   is in the manifest; prefer stdlib or an existing dep. **`scripts/verify_deps.py <path>
   [--registry]`** separates real-but-undeclared from hallucinated (slopsquatting).

Before handing new code back, run the orchestrator with Bash — `python
scripts/lean_check.py <path>` (exit 0 = pillars 3 & 4 clean). Evidence and citations:
`references/research-basis.md`.

## Mode 2: Code Audit

Scan existing code for AI structural/architectural smells — over-commenting, verbose
naming, unnecessary abstraction, god class, parameter explosion, copy-paste duplication,
TODO pileup, scaffolding bloat. **Run `scripts/lean_check.py <path>` first** to catch the
measurable ones (complexity, size, unverified imports) deterministically, then read the
rest by hand. Full smell definitions and the output template: `references/fingerprints.md`
§3–4. Quote the specific lines for every finding.

## Mode 3: Prose Audit

Scan text for the documented AI writing patterns — em-dash overuse, hedge clusters,
formulaic openers, parallel-structure addiction, flat cadence (high severity); buzzwords,
corporate verbs, emotional flatness, missing anchors, bullet abuse (medium). Quote the
exact phrase for every finding; never describe without quoting. Full pattern list, severity
weighting, and the audit output template: `references/fingerprints.md` §1, §4.

## Mode 4: Prose Rewrite

Apply the humanizing transformations — restructure at the sentence level, don't swap
synonyms (detectors catch paraphrase). Commit or cut hedges, kill formulaic openers, add a
concrete anchor and one genuine reaction, vary sentence length. Preserve the user's meaning
and register. Then annotate what changed and why. The transformation table is in
`references/fingerprints.md` §2.

## Mode 5: Cheat Sheet

No content or an explicit request for the list → output the reference card from
`references/fingerprints.md` §5 (prose + code patterns, watermark facts, humanization
rules). No audit, no rewrite.

## Mode 6: Watermark Bypass

Technical watermark questions (SynthID, "is there a fingerprint", "will this pass on a
technical level"). Explain what's actually deployed in 2026 and the evasion techniques
ranked by ease, plus what doesn't work. This is transparency about a documented,
mandated-disclosure technology, not a deception aid. Full tables in
`references/fingerprints.md` §6.

---

## Red Flags

Rationalizations that defeat the skill under time pressure, and what to do instead.

| Rationalization | Why it's wrong | Do instead |
|---|---|---|
| "The output looks clean to me, no need to check." | The model always judges its own output clean — that's the Iron Law's whole point. | Run the checker (Prevent/Code Audit) or the pattern scan (Prose). |
| "The repo's small — writing a fresh helper beats searching." | This is the exact habit the data shows rotting codebases. | Grep/Glob first; call or extend what exists. |
| "An extra param/config now future-proofs it." | Speculative generality is the top AI over-engineering pattern. | Name the concrete real use, or cut it (YAGNI). |
| "This package obviously exists." | ~20% of AI-suggested packages are hallucinated. | `verify_deps.py`, or check the manifest/registry. |
| "I'll just swap a few synonyms to humanize it." | Synonym swaps fail detectors and don't touch watermark signal. | Restructure at the sentence level; for watermarks, paraphrase via a different model. |
| "Describe the AI pattern without quoting the line." | An unquoted finding isn't verifiable or fixable. | Quote the exact phrase/line every time. |

## Notes — run free

These patterns are a floor for how AI content typically gives itself away, not a cage. A
deliberate em-dash, a genuinely needed abstraction, a legitimate hedge in an uncertain
domain — keep them, and say why. Don't let the checklist suppress good writing or good
engineering on a real problem.

## Reference files

- `references/fingerprints.md` — the full pattern catalog for the detection modes (prose
  patterns, rewrite transformations, code smells, output templates, cheat sheet, watermark
  tables). Load the section for the mode you're in.
- `references/research-basis.md` — the failure-mode→pillar evidence and citations behind
  Mode 1's prevention pillars.
- `scripts/README.md` — the checker scripts (`lean_check.py`, `complexity_check.py`,
  `verify_deps.py`) that power Mode 1 and the measurable half of Mode 2, plus their test
  suite and fixtures in `scripts/tests/` (`test_lean_code.py`, `fixtures/`).
