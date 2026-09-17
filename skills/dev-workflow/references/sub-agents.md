# Sub-Agent Delegation

Claude decides autonomously when to spin up sub-agents. This reference defines the
decision logic, delegation patterns, and how to aggregate results.

## Model for Sub-Agents

Resolve the model alias for each sub-agent via dev-workflow's `model-registry.json`
(`fast` → Haiku-class, `standard` → Sonnet-class, `deep` → Opus/Fable-class).
Default to `standard` when dispatching the code-reviewer or other analysis agents.
Never hardcode a model name in a dispatch message.

## When to Delegate (Autonomous Decision)

Delegate when ANY of the following are true:

| Trigger | Example |
|---|---|
| Two or more independent workstreams | Write tests AND update changelog simultaneously |
| Subtask requires large isolated context | "Review all files in packages/api" |
| Token budget > 60% with more work remaining | Main context getting crowded |
| Specialized operation benefits from focus | Security audit, perf analysis, docs generation |
| Long-running bash task (tests, builds) | Run tests while main agent continues planning |

Do NOT delegate when:
- Steps are strictly sequential (B depends on A's output)
- Task is < 5 min of work (overhead isn't worth it)
- User asked for an interactive, conversational response

## Delegation Patterns

### Pattern 1: Parallel Workstreams
```
Main agent: orchestrates, waits for results
├── Sub-agent A: write unit tests for changed files
└── Sub-agent B: update README and changelog
```

### Pattern 2: Context Offload
```
Main agent: planning & coordination (stays lean)
└── Sub-agent: reads + summarizes large folder/PR diff
    → returns: compact summary only
```

### Pattern 3: Specialized Focus
```
Main agent: feature implementation
└── Sub-agent: security-focused review of auth changes
    → returns: findings list with severity
```

### Pattern 4: Long-Running Task
```
Main agent: continues next task
└── Sub-agent: runs test suite, returns pass/fail + failures only
```

## Sub-Agent Briefing Template

When spawning a sub-agent, always provide:

```
TASK: [specific, scoped task — not open-ended]
SCOPE: [exact files, dirs, or PR number to work on]
REPO_CONTEXT: [branch, stack, key conventions from memory]
RETURN FORMAT: [what to return — keep it compact]
DO NOT: [anything to avoid — e.g., "don't modify files, just review"]
```

Example:
```
TASK: Review the diff in PR #142 for security issues only.
SCOPE: PR #142 on owner/repo, focus on src/auth/ changes.
REPO_CONTEXT: Node.js/Express, JWT auth, conventional commits.
RETURN FORMAT: List of findings as [SEVERITY] - [file:line] - [issue]. Max 20 items.
DO NOT: Suggest style or formatting changes. Don't leave comments on the PR.
```

## Aggregating Results

When sub-agents return:
1. Collect results before presenting anything to the user
2. Deduplicate overlapping findings
3. Reconcile conflicts (flag them if they can't be auto-resolved)
4. Present a unified summary, not raw sub-agent output

## Failure Handling

If a sub-agent fails or times out:
- Log what it was doing in memory
- Fall back to doing the task inline (if context allows)
- Or surface to user: "The [X] sub-task hit an issue — want me to retry or skip it?"

## Token Savings

Sub-agents don't share the main context window. Each sub-agent call:
- Starts with a clean, small context (just its briefing)
- Returns only its result to the main agent
- Net effect: main agent processes 1–2 paragraphs instead of 10,000 tokens of files
