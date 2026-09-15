# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [2.1.0] - 2026-07-15

### Added

- `references/graph-tools.md` — canonical graph availability check (graphify →
  codegraph MCP → declared no-graph grep fallback) with a question-to-tool map.
  Every graph-first instruction in the pack now resolves through this one file.

### Fixed

- architecture-review measures fan-out and blast radius from the graph before
  opening any file (new Step 1.5) instead of hand-counting them (RBA-F04).
- code-reviewer agent checks for a graph before reading beyond the diff and
  bounds surrounding-context reads; code-review §B's briefing spec now passes
  the `KNOWLEDGE_GRAPH` line that `sub-agents.md` declares mandatory (RBA-F02/F03).
- bug-triage scores the blast-radius severity axis from graph edge counts,
  test-strategy queries callers of the unit under test, and the debugging
  reference traces call chains via the graph — each with the previous manual
  approach as the declared fallback (RBA-F05/F06/F07).

## Earlier releases

v2.0.0 and the 2.0.1 metadata bump predate this changelog; see the
[release tags](https://github.com/rolling-codes/dev-workflow-pack/tags).
