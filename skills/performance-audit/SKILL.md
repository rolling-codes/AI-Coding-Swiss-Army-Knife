---
name: performance-audit
description: >
  Use when the user asks about slow code, bottlenecks, or profiling — "why
  is this slow", "profile this function", "what's the hot path", "benchmark
  before/after", "where is time being spent"; NOT for writing the
  optimization code (dev-workflow), NOT for performance test cases
  (test-strategy), and NOT for logging or tracing coverage gaps
  (observability-audit).
allowed-tools: [Bash, Read, Grep]
model: sonnet
---

# Performance Audit

Locate where time and memory are actually going, not where you think they are.
The goal is a ranked, evidence-backed list of bottlenecks — so the next step
(optimization) fixes the right thing.

## Quick examples

**In:** "our API response time is 800ms — where is the time going?"
**Out:** hot-path map from entry point to DB calls, grep for N+1 patterns and
missing indexes, severity-ranked findings: Critical (>10× expected), High (2–10×)

**In:** "profile the data import pipeline before I optimize it"
**Out:** instrumentation plan for the detected language/stack, existing benchmark
calls inventoried, recommended profiler command with flags

## Iron Law

Map the hot path first, measure second — because optimizing a cold path is
invisible improvement, and a profiler run without a hot-path hypothesis produces
a wall of numbers with no prioritization.

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "The code looks efficient — I'll report no findings." | Performance is empirical, not visual. Code that looks clean can hide N+1 queries, lock contention, or allocation pressure. | Run the detection steps; surface evidence or confirm clean with evidence. |
| "I'll optimize the bottleneck I found while I'm here." | This skill audits, not implements. Scope creep here means an unreviewed optimization lands without going through test-strategy or code-review. | Report findings; route to **dev-workflow** for the fix. |
| "The profiler isn't installed — I'll skip it." | An absent profiler is a gap, not a pass. The instrumentation plan is still deliverable. | Report `[TOOL MISSING: <profiler>]` as a Medium finding; produce the instrumentation plan so it's ready. |

---

## Step 1: Detect Language and Stack

```bash
[ -f go.mod ]                                          && echo "go"
[ -f package.json ]                                    && echo "node"
[ -f requirements.txt ] || [ -f pyproject.toml ]       && echo "python"
[ -f Cargo.toml ]                                      && echo "rust"
[ -f pom.xml ]                                         && echo "java"
[ -f Gemfile ]                                         && echo "ruby"
```

Also check for framework indicators (Express/Fastify, FastAPI/Django, Gin/Echo,
Axum/Actix) — they influence where hot paths live and which profilers apply.

---

## Step 2: Inventory Existing Benchmarks and Profiler Calls

```bash
# Benchmark and profiler patterns
grep -rn --include="*.{go,py,js,ts,rb,java,rs}" \
  -E "(BenchmarkFn|testing\.Benchmark|pytest\.mark\.benchmark|console\.time|performance\.mark|Criterion|bench_function|jmh\.@Benchmark)" \
  . 2>/dev/null | grep -v ".git/"

# Profiler activation patterns
grep -rn --include="*.{go,py,js,ts,sh}" \
  -E "(pprof|cProfile|--inspect|--prof|perf record|py-spy|flamegraph)" \
  . 2>/dev/null | grep -v ".git/"
```

If benchmarks already exist, they are the primary evidence source. Report their
coverage and note which hot paths they miss.

---

## Step 3: Map the Hot Path

Read the primary entry points and trace execution to I/O boundaries:

1. HTTP handlers / route definitions
2. Background job entry points
3. Batch processing loops
4. Recursive or deeply-nested operations

For each path, identify:
- External I/O calls (DB queries, HTTP calls, file reads)
- Loops with embedded I/O (N+1 query patterns)
- Synchronous blocking in async contexts
- Large in-memory collections (sorting, copying, serialization)

```bash
# N+1 candidates — DB calls inside loops
grep -rn --include="*.{js,ts,py,go,rb}" \
  -E "(for |forEach|\.map\(|while )" \
  . 2>/dev/null | grep -v ".git/" | head -50
```

Cross-reference loop locations with DB/HTTP call sites to identify N+1 patterns.

---

## Step 4: Recommend the Right Profiler

Per detected language, the minimum viable profiling command:

| Language | Tool | Command |
|----------|------|---------|
| Go | `pprof` | `go test -cpuprofile cpu.prof -bench=. && go tool pprof cpu.prof` |
| Python | `cProfile` | `python -m cProfile -o profile.out script.py && python -m pstats profile.out` |
| Python (sampling) | `py-spy` | `py-spy record -o profile.svg -- python script.py` |
| Node.js | V8 profiler | `node --prof app.js && node --prof-process isolate-*.log` |
| Rust | `cargo-flamegraph` | `cargo flamegraph --bin <name>` |
| Java | JFR | `java -XX:+FlightRecorder -XX:StartFlightRecording=filename=recording.jfr ...` |
| Native | `perf` | `perf record -g ./binary && perf report` |

If a profiler run output is available in the workspace (`.prof`, `.jfr`, flamegraph SVG),
analyze it and produce findings from actual data instead of the instrumentation plan.

---

## Step 5: Classify and Report

```
Performance audit: <scope>.
Hot paths mapped: <N>. Findings: <c> critical, <h> high, <m> medium, <l> low.
Profiler status: <ran / not installed / instrumentation plan below>.

## Critical (>10× expected or latency SLA breach)

### [file.ext:line] Short description
**Path:** <entry point → bottleneck>
**Evidence:** <benchmark result, query count, or structural analysis>
**Cause:** N+1 query / missing index / synchronous block / O(n²) loop / ...
**Fix direction:** <one sentence — defer implementation to dev-workflow>

## High (2–10× slower than expected)
...

## Medium (<2× but measurable)
...

## Low (style-level waste — no measurable impact)
...

## What's well-optimized
- [paths or patterns that show deliberate performance care]
```

Write findings using the ledger handoff convention documented in dev-workflow.

---

## Rules

- Findings must cite evidence: a file:line, a benchmark number, or a structural pattern — "this looks slow" is not a finding
- No optimization code here — describe the fix direction; use **dev-workflow** to implement
- If no hot path exists (e.g., a CLI tool that runs once and exits), say so explicitly
- Missing profiler tools are Medium findings, not silent skips

---

## Next Step

- **To implement the fix:** use **dev-workflow** with the findings as requirements
- **To write benchmark tests:** use **test-strategy** with performance test scope
- **Multiple findings to rank:** use **bug-triage** to prioritize before implementation
- **Logging/tracing gaps found while auditing:** use **observability-audit**
