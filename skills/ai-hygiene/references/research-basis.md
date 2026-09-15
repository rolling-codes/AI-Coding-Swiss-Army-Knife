# Research basis for lean-code

Why each pillar exists. Large-scale studies of AI-assisted commits from 2024–2026 keep
surfacing the same regressions; lean-code's four pillars each counter one. Read this when
you want the evidence — the SKILL.md carries the actionable version.

## Failure mode → pillar

| Documented AI failure mode | Evidence | Pillar that counters it |
|---|---|---|
| **Duplication instead of reuse** — copy/pasted lines rose 8.3% (2020) → 12.3% (2024); code blocks with 5+ duplicated lines grew ~8× during 2024; cross-file function calls (a reuse signal) down ~35%. AI spins up a new block/package rather than calling what exists. | GitClear 2025; LeadDev | **1. Reuse-first** |
| **Refactoring collapse** — "moved" (refactored) lines fell 24.1% (2020) → 9.5% (2024); 2024 was the first year copy/paste exceeded refactoring. | devclass (2025-02-20); GitClear 2026 | **1. Reuse-first** (extend/refactor over parallel paste) |
| **Over-complexity** — LLMs emit methods with high cyclomatic / cognitive complexity. Root cause: autoregressive generation is token-by-token and optimized for *local* coherence, so architecture is secondary and a method's accumulating complexity is untracked at inference. Adding more context degrades reasoning rather than helping. | arXiv 2508.14727; Simon Willison (2025-03-11) | **2. Simplest-thing-that-works** + **3. Complexity/size budget** |
| **Churn / premature code** — share of new code rewritten within two weeks rose 3.1% (2020) → 5.7% (2024), a signal of low-quality first drafts. | GitClear "Maintainability Gap" 2026 | All four (fewer over-built drafts to rewrite) |
| **Security & hallucinated dependencies** — ~45% of LLM-produced code carried security flaws (Veracode, 100+ models); ~2.74× vulnerability density vs human code; ~20% of packages AI suggests are nonexistent, and ~43% of those recur across prompts, making them predictable "slopsquatting" supply-chain targets. | Snyk; Endor Labs; Veracode | **4. Dependency verification** |

## Sources

- GitClear — *AI Copilot Code Quality 2025*: https://www.gitclear.com/ai_assistant_code_quality_2025_research
- GitClear — *The Maintainability Gap: 2026*: https://www.gitclear.com/the_ai_code_quality_maintainability_gap
- LeadDev — *Code maintainability plummets in the AI coding era*: https://leaddev.com/ai/code-maintainability-plummets-in-the-ai-coding-era
- devclass — *AI is eroding code quality* (2025-02-20): https://www.devclass.com/ai-ml/2025/02/20/ai-is-eroding-code-quality-states-new-in-depth-report/1626250
- arXiv 2508.14727 — *Assessing the Quality and Security of AI-Generated Code*: https://arxiv.org/pdf/2508.14727
- Simon Willison — *Here's how I use LLMs to help me write code* (2025-03-11): https://simonwillison.net/2025/Mar/11/using-llms-for-code/
- Snyk — *Slopsquatting mitigation strategies*: https://snyk.io/articles/slopsquatting-mitigation-strategies/
- Endor Labs — *The most common security vulnerabilities in AI-generated code*: https://www.endorlabs.com/learn/the-most-common-security-vulnerabilities-in-ai-generated-code

Figures are point-in-time from the cited reports (research current to ~2026); they show
direction and magnitude, not precise constants — the habits hold regardless of the exact
percentages.
