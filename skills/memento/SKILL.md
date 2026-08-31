---
name: memento
description: Use when the user corrects a repeated behavior ("again?", "I told you", "stop doing that"), when an approach fails repeatedly before a fix is found, when a quality gate is skipped (coverage, complexity, lint), when discovering a project-specific workaround — and at task start, to load past lessons before choosing an approach.
---

# Memento

Cross-agent mistake ledger: log repeated mistakes, count recurrence and cost, promote repeat offenders into enforced rules. Any tool that reads markdown can use it.

The CLI owns all bookkeeping. Never hand-edit ledger entries, never count occurrences yourself.

```
python3 ~/.agents/memento/memento.py <cmd>
```

Stdlib-only — plain `python3`, never `uv run`. (Exception: inside `~/dev/ai`, `uv run memento` is the same script.)

Ledgers: global `~/.agents/memento/MEMENTO.md`, project `<git root>/MEMENTO.md`.

## Protocol: CONSULT → LOG → PROMOTE

### 1. CONSULT (task start)

```
memento check
```

Run before choosing tools or approach. ENFORCED entries are law. WATCHING entries are strong defaults — deviating without cause is how the mistake repeats.

### 2. LOG (on trigger)

Triggers: the user corrects you (especially "again", "I told you") · an approach fails repeatedly before a fix works (log the fix — that is the valuable part) · a quality gate is skipped or ignored · you discover the way that actually works in this project.

Run `memento list` first — recurrence means reusing the same slug. Then:

```
memento hit <slug> [--rule "..."] [--fix "..."] [--kind habit|trick|gate|project-way] [--scope global|project] [--cost MIN]
```

- New slug requires `--rule`: one enforceable sentence.
- `--fix`: the exact command/env var/edit that worked. "Fixed the SSL issue" is useless next month.
- `--scope`: applies in other repos → `global`; only here → `project`.
- `--cost`: minutes lost this occurrence (feeds the `memento top` pain ranking).
- The CLI warns about similar existing slugs and prints a PROMOTE alert at 3 hits or ≥30 min in one hit.

### 3. PROMOTE (enforcement)

On a PROMOTE alert, or when the user says "always" / "never":

```
memento promote <slug>
```

Writes the rule bullet into a dedicated `## Memento-enforced` section (other sections untouched): global scope → `AGENTS.md` + `CLAUDE.md` in the rules dir (env `MEMENTO_AI_DIR`, else `rules_dir` in `~/.agents/memento/config.json`); project scope → the project's `AGENTS.md` (created if missing) + `CLAUDE.md` if present. The ledger keeps history and the detailed fix; the enforcement doc gets only the rule.

Obsolete rule (tool fixed, project dead, user says so): `memento retire <slug>` — removes the bullet, keeps ledger history, drops it from `check`. A later hit revives it to watching.

## Common mistakes

| Mistake | Fix |
|---|---|
| Lesson only stated in the chat reply | Chat dies with the session. `memento hit` or it didn't happen. |
| Hand-editing MEMENTO.md / counting yourself | The CLI owns bookkeeping. Judgment (rule, fix, scope) is yours; arithmetic is not. |
| Logging straight into AGENTS.md/CLAUDE.md | Those are enforcement docs, not history. `hit` first; `promote` when earned. |
| New slug per occurrence | `memento list` first; recurrence = same slug. Duplicates break rate tracking. |
| Vague fix ("fixed certs") | Record the exact command/env var/edit that worked. |
| Skipping `memento check` at task start | That is precisely how mistakes repeat. |
| Promoting on first occurrence | One-offs pollute enforcement docs. Thresholds exist; user "always/never" overrides them. |

## Bootstrap

If `~/.agents/memento/memento.py` does not exist, read `BOOTSTRAP.md` next to this file and copy its code block verbatim to that path. Never open `BOOTSTRAP.md` otherwise — it is only the embedded script source.
