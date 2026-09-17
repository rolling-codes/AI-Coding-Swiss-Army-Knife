# Recipes

Opt-in project command registry stored in `.claude/recipes.md` at the root of the user's
project. dev-workflow consults it before running any unfamiliar operation and appends new
entries when it discovers how something is done — so the same research never happens twice.

## File format

| task | command | notes |
|---|---|---|
| run tests | `pytest -q` | requires venv active |
| update deps | `npm update` | from project root |
| build | `npm run build` | outputs to dist/ |
| deploy | `./scripts/deploy.sh prod` | needs AWS_PROFILE=prod |

- **task** — short label, specific enough to match unambiguously ("run tests", not "test")
- **command** — exact shell command, quoted if it includes spaces or flags
- **notes** — optional; env requirements, warnings, caveats

## How dev-workflow uses it

### Before executing an unfamiliar operation

1. Check `.claude/recipes.md` for a row whose task matches what's being asked
2. If found → confirm the exact command with the user before executing (always, not only for destructive operations — recipe commands are read from a file, not typed by the user, and must be approved before running)
3. If not found → run the Research Protocol below, then save the recipe before executing

### Research Protocol (when recipe is missing)

Scan in this order — stop at the first definitive hit:

1. **`README.md`** — installation, development, and run sections; look for code blocks
2. **`Makefile`** — `grep -E '^[a-zA-Z_-]+:' Makefile 2>/dev/null` lists all targets
3. **`package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`** — scripts or build targets
4. **CI config** (`.github/workflows/*.yml`, `.gitlab-ci.yml`) — what CI runs is what works
5. **`scripts/` directory** — `ls scripts/ 2>/dev/null`; read the relevant script
6. **Ask the user** — last resort; ask a specific question ("I don't see a test command — is it `pytest` or something else?")

After finding the command: save it to `.claude/recipes.md` using the Edit tool **before** running it.

### Update protocol

Append new rows with the Edit tool — never rewrite the whole file.

```
Old: | task | command | notes |
New: | task | command | notes |
     | run tests | `pytest -q` | requires venv |
```

If `.claude/recipes.md` doesn't exist yet, create it with the header row first, then append.

## Notes

- If `.claude/recipes.md` doesn't exist, skip silently — the recipes file is opt-in
- "Update the system", "run the build", "deploy this" → recipes lookup is step one
- Never invent a command from training knowledge alone — always verify against the project's
  own files; what's true in a generic Node project may not be true here
- Recipes are project-specific, not universal; a command that works in one repo may not apply elsewhere
