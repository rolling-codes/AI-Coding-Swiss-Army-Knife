# AI fingerprint catalog

The full pattern reference for `ai-hygiene`'s detection modes. SKILL.md routes and gives
the core moves; this file holds the exhaustive lists and the exact output templates. Load
the section for the mode you're in.

## Table of contents

1. Prose patterns (Prose Audit / Rewrite)
2. Prose rewrite transformations
3. Code smells (Code Audit)
4. Output templates
5. Cheat sheet
6. Watermarks & evasion (Watermark Bypass)

---

## 1. Prose patterns

Quote the exact problematic phrase for every finding — never describe without quoting.

### High-severity (detectors weight these most)

**Em-dash overuse** — AI uses em-dashes 3.28× more than human writers. Flag every `—`
that isn't doing real rhetorical work (replacing a colon, a dramatic reversal). The fix is
a sentence restructure, not swapping the dash for a comma.

**Hedge clusters** — `may`, `might`, `could`, `appears`, `seems`, `arguably`, `somewhat`,
`relatively`, `to some extent`. One hedge is fine; two in a sentence is a pattern; three is
a flag.

**Formulaic openers/closers** — exact phrases: "It's important to note", "It is worth
noting", "It is crucial to understand", "Furthermore", "Moreover", "In addition", "In
conclusion", "Overall", "Significantly", "Crucially", "Underscores the importance of".

**Parallel-structure addiction** — repeated "It's not X, it's Y"; consecutive sentences on
"Unlike X, Y provides…" or "While X, Y…". The pattern isn't wrong; doing it twice in a
paragraph is.

**Uniform sentence length (low burstiness)** — every sentence 15–25 words, no short
punches, no long sprawls. Human prose varies; a paragraph of clones is synthetic.

### Medium-severity

**Buzzword density** — `delve`, `tapestry`, `meticulous`, `nuanced`, `boast`, `testament
to`, `plethora`, `multitude`, `inquiry`, `underscore`, `foster`, `navigate`, `realm`,
`vibrant`, `pivotal`, `crucial`, `comprehensive`, `robust`. Two+ across 300 words is a flag.

**Corporate verbs** — `leverage`, `synergize`, `optimize`, `streamline`, `facilitate`,
`utilize`, `operationalize` used without irony. Simple verbs exist.

**Positivity / emotional flatness** — no frustration, sarcasm, doubt, friction, or negative
emotion anywhere. Real writing has a reaction somewhere.

**Abstraction without anchors** — no specific dates, names, numbers, sensory detail, or
concrete example in 200+ words. Everything stays at 30,000 feet.

**Bullet-point overuse** — lists where prose would flow better; every bullet the same
length and grammatical structure; fewer than 4 items that could be a sentence.

---

## 2. Prose rewrite transformations

Don't swap synonyms — detectors catch paraphrase patterns. Restructure at the sentence
level.

- **Em-dashes** → rewrite so the dash is unnecessary (split into two sentences, or make the
  clause subordinate).
- **Hedging** → commit ("This works") or delete the sentence. Never soften to a different
  hedge.
- **Formulaic openers** → cut the opener, start with the claim. "It's important to note that
  the API changed" → "The API changed."
- **Parallel constructions** → break the rhythm; make the second sentence structurally
  different.
- **Abstractions** → inject at least one concrete anchor (a number, name, date, specific
  example) that could only come from knowing the actual situation.
- **Bullet lists** → collapse to prose if fewer than 4 items; vary grammatical structure if
  kept.
- **Sentence length** → per 300-word block, add at least 2 sentences under 8 words and 1
  over 40. Don't let every sentence land in the same range.
- **Emotional flatness** → add one sentence with a genuine reaction: doubt it'll work,
  frustration with a constraint, a preference stated plainly.

After rewriting, annotate what changed and why, so the user learns the pattern, not just
the fix.

---

## 3. Code smells

Quote the specific lines. The **measurable** smells below can be confirmed with
`scripts/lean_check.py <path>` (complexity, size, unverified imports) instead of eyeballing
— run it, then read the rest by hand.

### Structural

**Over-commenting** — comments that restate the code: `// increment i` above `i++`. Flag any
comment describing mechanics rather than the why; also flag comment-to-code ratio above ~25%.

**Verbose / redundant naming** — `processedUserInputDataContainer`, `intermediateResultValue`,
`tempStringBuffer`; Hungarian notation (`strName`, `arrItems`); names that say nothing
(`result`, `data`, `value`, `temp`). Good names describe intent, not type or lifecycle.

**Unnecessary abstraction** — interface/base class with a single implementation; a helper
wrapping 3 lines; deep inheritance for a simple problem. AI abstracts speculatively; humans
abstract when reuse pressure is real. *(Measurable via the complexity checker.)*

**God class / mixed concerns** — one class or function handling UI, business logic, and data
access; methods from different domains sharing a namespace because the model optimized the
current function without seeing the module boundary.

**Parameter explosion** — a method taking 6+ primitive args in a row. Fix: a config object or
a rethought responsibility boundary. *(complexity_check flags long signatures/functions.)*

**Copy-paste duplication** — near-identical blocks within 50 lines with trivial variable
substitution. AI duplicates rather than extracts. *(The reuse pillar prevents this up front.)*

### Architectural

**TODO accumulation** — `// TODO`, `// FIXME`, `// HACK` clearly never to be resolved,
scattered across a file describing known problems with no plan.

**Scaffolding bloat** — setup/teardown that dwarfs the business logic; more lines
initializing than doing.

---

## 4. Output templates

Use these exact shapes so results are scannable.

### Prose Audit

```
PATTERN AUDIT — [title or "pasted text"]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HIGH RISK
  Em-dash overuse — "The solution — which required careful testing — shipped Friday."
    → AI inserts explanatory pauses; rewrite as a subordinate clause or two sentences.

MEDIUM RISK
  Buzzword density — "delve", "meticulous", "nuanced" within 4 sentences.
    → Replace with plain equivalents: explore / careful / subtle.

SUMMARY
  Detection risk: HIGH / MEDIUM / LOW
  Patterns hit: N of 10 categories
  Priority fix: [the single highest-impact change]
```

### Code Audit

```
CODE AUDIT — [filename or "pasted code"]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Lines 12–14  OVER-COMMENTING
  "// Create a new array to store the filtered results
   const filtered = items.filter(...)"
  Why it's AI: comment restates the code.
  Fix: Delete the comment.

SUMMARY
  Smells found: N   (measurable ones confirmed via lean_check.py)
  Most impactful fix: [one action]
```

---

## 5. Cheat sheet

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  AI FINGERPRINT CHEAT SHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROSE — HIGH RISK
  Em-dashes       → 3.28× AI rate; rewrite the sentence
  Hedge clusters  → may/might/could stacked; commit or cut
  Formulaic       → "It's important to note", "Furthermore", "In conclusion"
  Parallel loops  → "It's not X, it's Y" twice in a paragraph
  Flat cadence    → every sentence 15–25 words; no outliers

PROSE — MEDIUM RISK
  Buzzwords       → delve, tapestry, meticulous, nuanced, plethora, pivotal, robust
  Corp verbs      → leverage, synergize, streamline, facilitate
  Emotional flat  → no doubt, no frustration, no reaction
  No anchors      → 200+ words, zero specific dates/names/numbers
  Bullet abuse    → <4 items that could be one sentence

CODE — STRUCTURAL
  Over-comments   → comment restates code; delete it
  Verbose names   → processedUserInputDataContainer → query
  Fake interfaces → one implementation; delete the interface
  God class       → UI + business + data in one file
  Param explosion → 6+ primitive args → config object
  Copy-paste      → near-identical blocks within 50 lines

CODE — ARCHITECTURAL
  TODO pileup     → scattered unresolved // TODO blocks
  Scaffolding     → setup code dwarfs business logic

TECHNICAL WATERMARKS (2026)
  Active in    → Claude (Aug 2026+), Gemini, Llama 3.1+   Not in → ChatGPT
  How detected → statistical, NOT readable; ~50% accuracy now
  Remove with  → LLM paraphrase (different model), back-translation
  Doesn't work → a few synonym swaps, formatting changes, same-model edits

HUMANIZATION RULES
  1. Vary sentence length      4. Add one friction point (doubt/reaction)
  2. Commit to claims          5. Restructure, don't paraphrase
  3. Add one concrete anchor   6. Collapse small lists into prose
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. Watermarks & evasion

### What's actually deployed (2026)

**SynthID-Text** — LIVE, no opt-out. In all new Claude models (mandatory since Aug 2, 2026,
EU AI Act Art. 50), Google Gemini (2024+), Meta Llama 3.1+. Not in ChatGPT. Works by logit
modulation — token probabilities shifted <1% by a hidden pattern; text reads identically.
Detection needs statistical analysis across 100+ tokens, and real-world accuracy is ~50–55%
prose / ~45–50% code (barely above chance, per arXiv:2609.09604). The watermark exists but
is near-undetectable now; the risk is future detectors, not current tools.

**Statistical (red-green token lists)** — some research/enterprise contexts. Detection
60–80% on unmodified text, <20% after paraphrase.

**C2PA / Content Credentials** — image/video metadata provenance, not text watermarks;
stripped when text is copied out.

### Evasion, ranked by ease

```
1. BACK-TRANSLATION (easiest — ~100% removal, 90%+ bypass)
   Text → other language (DeepL) → back to English. Destroys the signal (operates on
   meaning). Trade-off: 20–40% fluency loss; better for prose than technical text.

2. LLM PARAPHRASE (easy — 80–100% removal, 80–90% bypass)
   Feed to a DIFFERENT model and rewrite. Not the same model (same biases). Minimal
   quality loss if you instruct it to preserve meaning. Best all-round.

3. TOKEN SUBSTITUTION (moderate — 40–70% removal)
   Methodically replace key words with synonyms throughout. Time-intensive; partial.

4. CHARACTER PERTURBATIONS (low effort — 30–50% removal)
   Typos, whitespace, Unicode homoglyphs. May trigger other signals; degrades readability.
```

**What doesn't work:** swapping 2–3 synonyms; editing within the same model; adding text
around it; changing formatting (bold/headers/bullets).

**Practical recommendation** for Claude/Gemini (SynthID): the watermark is near-undetectable
now, so stylistic patterns (§1) are the bigger practical risk; for high confidence, LLM
paraphrase with a different provider; for maximum removal, back-translation then a §1
stylistic cleanup.

---

## Gotchas (apply across detection modes)

- Never flag an em-dash doing something a comma or colon can't. The problem is frequency and
  redundancy, not existence.
- Hedging is legitimate in genuinely uncertain domains (medicine, law, research). Flag
  clusters, not single instances.
- Some "AI buzzwords" are domain vocabulary. "Robust" in security is fine; "robust solution"
  in a generic pep talk is not.
- Rewriting keeps the user's meaning and register. A formal report stays formal — it just
  loses the synthetic markers.
- Detection tools are biased against non-native English speakers. If the user's first
  language isn't English, soften grammar-uniformity severity and say so.
