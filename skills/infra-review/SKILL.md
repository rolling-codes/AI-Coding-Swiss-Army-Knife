---
name: infra-review
description: >
  Use when the user asks to review IaC files — "review this Dockerfile",
  "is this k8s config production-ready", "check the terraform", "audit
  the CI workflow", "is this GitHub Actions safe"; NOT for application
  code correctness (code-review), NOT for dependency vulnerabilities
  (security-audit), and NOT for system architecture design
  (architecture-review).
allowed-tools: [Read, Grep]
model: sonnet
---

# Infrastructure Review

Review Dockerfiles, Kubernetes manifests, Terraform configs, CI/CD pipelines,
and Docker Compose files for the concerns that application code review misses:
image pinning, immutability, secret hygiene, resource constraints, and ordering
safety.

## Quick examples

**In:** "review this Dockerfile before we push to production"
**Out:** findings on base image pinning, layer cache order, non-root user, secret
exposure in ENV/ARG, multi-stage build — severity ranked Critical through Low

**In:** "is this GitHub Actions workflow safe to merge?"
**Out:** check for unpinned action versions, pull_request_target risk, hardcoded
secrets, excessive permissions, supply chain exposure — verdict and specific lines

## Iron Law

Apply the type-specific checklist for the detected infra format — because generic
"looks good" reviews miss the concerns that are invisible to application-code
heuristics (base image drift, K8s resource limits, Terraform state misconfiguration).

## Red Flags — Rationalizations to Refuse

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "This is a dev Dockerfile — production hardening is overkill." | Dev configs ship to production more often than they should. The review cost is the same; the risk if skipped is not. | Review fully; mark findings Medium/Low if they apply only to production deployment. |
| "The K8s config looks like a standard template — probably fine." | Templates are the origin of missing resource limits and overly permissive RBAC. Standard != safe. | Run the K8s checklist; report what the template left unconfigured. |
| "I'll fix the Dockerfile issues while I'm here." | This skill reviews, not implements. IaC changes need the same review cycle as code changes. | Report findings; route to **dev-workflow** to implement. |

---

## Step 1: Detect Infrastructure Types

```bash
find . -name "Dockerfile*" -not -path "*/.git/*" 2>/dev/null
find . \( -name "docker-compose*.yml" -o -name "docker-compose*.yaml" \) -not -path "*/.git/*" 2>/dev/null
find . -name "*.tf" -not -path "*/.git/*" 2>/dev/null | head -5
find . \( -path "./.github/workflows/*.yml" -o -path "./.github/workflows/*.yaml" \) 2>/dev/null
find . \( -name "*.yaml" -o -name "*.yml" \) -not -path "*/.git/*" 2>/dev/null | \
  xargs grep -l "apiVersion:" 2>/dev/null | head -5
```

Process each detected type through its dedicated checklist below.

---

## Step 2: Dockerfile Checklist

| Check | What to look for | Severity if failing |
|-------|-----------------|-------------------|
| Base image pinned | `FROM image@sha256:...` or versioned tag — never `:latest` | High |
| Non-root user | `USER` directive with non-root uid before final stage | High |
| Multi-stage build | Separate build and runtime stages for compiled languages | Medium |
| Layer cache order | COPY package files → install deps → COPY source | Low |
| No secrets in ENV/ARG | `ENV SECRET=` or `ARG TOKEN=` with real values are build-time leaks | Critical |
| HEALTHCHECK present | Containers without health checks don't self-report failures | Medium |

```bash
grep -n "FROM.*:latest\|FROM [^@]*$" Dockerfile 2>/dev/null
grep -n "^ENV\|^ARG" Dockerfile 2>/dev/null | grep -iE "(key|secret|token|pass|pwd)"
grep -n "^USER" Dockerfile 2>/dev/null
```

---

## Step 3: Kubernetes Manifest Checklist

| Check | What to look for | Severity if failing |
|-------|-----------------|-------------------|
| Resource limits | `resources.limits.cpu` and `resources.limits.memory` in every container | High |
| Liveness + readiness probes | Both defined for every long-running container | High |
| No secrets in env vars | `env[].value` containing credential-shaped strings | Critical |
| Secrets via secretKeyRef | Prefer `secretKeyRef` over hardcoded env values | High |
| RBAC minimal | No `clusterrole: admin` or wildcard verbs on ServiceAccounts | High |
| Image tag pinned | No `:latest` tags | High |
| `runAsNonRoot: true` | In pod securityContext | Medium |

```bash
grep -rn "resources:" . 2>/dev/null | grep -v ".git/"
grep -rn ":latest" . --include="*.yaml" --include="*.yml" 2>/dev/null | grep -v ".git/"
grep -rn "value:.*KEY\|value:.*SECRET\|value:.*TOKEN" . --include="*.yaml" 2>/dev/null | grep -v ".git/"
```

---

## Step 4: Terraform Checklist

| Check | What to look for | Severity if failing |
|-------|-----------------|-------------------|
| Remote state backend | `backend {}` block configured — not local state | High |
| Provider versions pinned | `version = "~> X.Y"` in `required_providers` | High |
| Destroy protection | `lifecycle { prevent_destroy = true }` on stateful resources | Critical |
| Sensitive outputs masked | `sensitive = true` on outputs containing credentials | High |
| No hardcoded credentials | `access_key =` or `secret_key =` with literal values | Critical |

```bash
grep -rn "backend\s*{" . --include="*.tf" 2>/dev/null | grep -v ".git/"
grep -rn "prevent_destroy" . --include="*.tf" 2>/dev/null | grep -v ".git/"
grep -rn "access_key\s*=\|secret_key\s*=" . --include="*.tf" 2>/dev/null | \
  grep -v "var\.\|data\." | grep -v ".git/"
```

---

## Step 5: CI/CD Workflow Checklist

| Check | What to look for | Severity if failing |
|-------|-----------------|-------------------|
| Action versions pinned | External `uses:` pinned to `@sha256:...` not just `@v3` | High |
| No hardcoded secrets | `env: TOKEN: abc123` instead of `${{ secrets.TOKEN }}` | Critical |
| Minimal permissions | `permissions:` block present; no `write-all` | High |
| `pull_request_target` safety | If present with `checkout`, fork code gets write access | Critical |
| `GITHUB_TOKEN` scope | Not passed to untrusted third-party steps | High |

```bash
# Unpinned external actions
grep -rn "uses:.*@v[0-9]" .github/workflows/ 2>/dev/null
# Hardcoded secret patterns
grep -rn ":\s*['\"][A-Za-z0-9+/]{20,}" .github/workflows/ 2>/dev/null
# pull_request_target present
grep -rn "pull_request_target" .github/workflows/ 2>/dev/null
```

---

## Step 6: Report

```
Infrastructure review: <files reviewed>.
Findings: <c> critical, <h> high, <m> medium, <l> low.

## Critical

### [file:line] Short description
**Type:** Dockerfile / K8s / Terraform / CI
**Issue:** What the problem is and how it can be exploited or cause failure.
**Fix direction:** How to correct it (no implementation here).

## High
...
```

Write findings using the ledger handoff convention documented in dev-workflow.

---

## Rules

- Secrets in IaC files are always Critical — no exceptions for "dev only" or "test values"
- Missing resource limits and missing probes are High, not suggestions — they cause production incidents
- If a file type is detected but has no dedicated checklist, note it as out of scope
- No IaC changes written here — report only

---

## Next Step

- **To fix findings:** use **dev-workflow** to implement, then run this skill again to verify
- **CVEs in base images or packages:** run **security-audit** — that's the dependency layer
- **CI pipeline logic bugs (not config/security):** use **code-review**
- **System-level architecture questions:** use **architecture-review**
