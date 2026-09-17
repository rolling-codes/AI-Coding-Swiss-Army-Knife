# Backlog

Opt-in task board stored in `.claude/backlog.md` at the root of the user's project.
dev-workflow checks it at session start, picks the next slice, and updates status as
work progresses — replacing the implicit linear assumption with an explicit queue.

## File format

```markdown
# Backlog

| id | goal | status | notes |
|---|---|---|---|
| 1 | Add auth module | todo | PROJ-42 |
| 2 | Fix login redirect bug | doing | |
| 3 | Write API docs | done | |
```

- **id** — short unique identifier (number or slug)
- **goal** — one-line task, specific enough to resume cold
- **status** — `todo` → `doing` → `done`
- **notes** — optional; ticket link, blocker, or context

## How dev-workflow uses it

1. **Session start:** read the file, show board summary (N todo / N doing / N done)
2. **Resume:** if any task is `doing`, propose resuming it before starting anything new
3. **Pick:** if no `doing` task, suggest the top `todo` item; wait for user confirmation
4. **Start:** mark the agreed task `doing` (Edit tool — update the status cell in place)
5. **Done:** after Commit step completes, mark it `done`

## Update protocol

Use the Edit tool to update individual status cells — never rewrite the whole file.

```
Old: | 1 | Add auth module | todo |
New: | 1 | Add auth module | doing |
```

Match the full row text to avoid clobbering adjacent rows.

## Creating the file

If the project has no backlog yet:

```bash
mkdir -p .claude && cat > .claude/backlog.md << 'EOF'
# Backlog

| id | goal | status | notes |
|---|---|---|---|
| 1 | [first task] | todo | |
EOF
```
