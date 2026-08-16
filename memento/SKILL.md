---
name: memento
description: Use when the user corrects a repeated behavior of any kind ("again?", "I told you", "how many times", "stop doing that"), when an approach fails repeatedly before a working fix is found (SSL/cert errors, build workarounds, flaky tooling), when a quality gate is skipped or ignored (coverage, cognitive complexity, code smells, lint), when discovering a project-specific way that works differently from the default — and at task start in any project, to load past lessons before choosing an approach.
---

# Memento

Agents have no long-term memory, so the rules that must never be forgotten get tattooed. The tattoos are ledgers (`MEMENTO.md`) owned by a small stdlib-only CLI that does all bookkeeping: recurrence counting, pain scoring, and automatic promotion of repeat offenders into enforced rules. Every repeated mistake burns tokens; this system makes each mistake billable once.

Works for Claude, Codex, Copilot, and Cursor — they all read the same ledgers and the same enforcement docs.

## The tool does the arithmetic — you do the judgment

Never hand-edit ledger entries, never count occurrences yourself. Call the CLI (stdlib only, no env needed):

```
python3 ~/.agents/memento/memento.py <cmd>
```

This skill ships as markdown only — the script source travels in the sibling `BOOTSTRAP.md`. If `~/.agents/memento/memento.py` is missing (first use on a machine), see the Bootstrap section at the end; otherwise never open `BOOTSTRAP.md`.

## Protocol: CONSULT → LOG → PROMOTE

### 1. CONSULT (task start)

```
memento check
```

Run before choosing tools or approach in a project. ENFORCED entries are law. WATCHING entries are strong defaults — deviating from one without cause is how the mistake repeats. (In Claude Code a SessionStart hook can run this automatically — see README.)

### 2. LOG (on trigger)

Triggers — domain-agnostic, any of:

- the user corrects you, especially with repetition signals ("again", "I told you", "every time")
- an approach fails repeatedly before a fix finally works (log the fix — that is the valuable part)
- a quality gate is skipped or its findings ignored (coverage, complexity, smells, lint)
- you discover the way that actually works in this project, differing from the default

Check `memento list` for an existing slug first, then:

```
memento hit <slug> [--rule "..."] [--fix "..."] [--kind habit|trick|gate|project-way] \
                   [--scope global|project] [--cost MINUTES]
```

- Existing slug → date appended, count bumped. New slug → `--rule` required.
- `--rule`: one enforceable sentence. `--fix`: copy-pasteable command/env var/edit — "fixed the SSL issue" is useless next month.
- `--scope`: would the lesson apply in a different repo? yes → `global`, no → `project`.
- `--cost`: minutes lost this occurrence (feeds the pain ranking in `memento top`).

The CLI warns about similar existing slugs (reuse, don't duplicate) and prints a PROMOTE alert when a threshold is crossed (3 hits, or ≥30 min lost in one hit).

### 3. PROMOTE (automatic enforcement)

When the CLI prints a PROMOTE alert, or the user says "always" / "never":

```
memento promote <slug>
```

Writes the rule bullet into a dedicated `## Memento-enforced` section (never touches other sections): global scope → `AGENTS.md` + `CLAUDE.md` in the machine's rules dir (env `MEMENTO_AI_DIR`, else `rules_dir` in `~/.agents/memento/config.json`, else `~/.agents/memento/`); project scope → the project's `AGENTS.md` (created if missing) + `CLAUDE.md` if present. The ledger entry keeps the history and the detailed fix; the enforcement doc gets only the rule.

## Scoring

`memento top` ranks all lessons by hits + total cost with last-hit date — the rate-of-issues view. No database needed; the ledger is the data.

## Common mistakes

| Mistake | Fix |
|---|---|
| Lesson only stated in the chat reply | Chat dies with the session. `memento hit` or it didn't happen. |
| Hand-editing MEMENTO.md / counting yourself | The CLI owns bookkeeping. Judgment (rule text, fix, scope) is yours; arithmetic is not. |
| Logging straight into CLAUDE.md/AGENTS.md | Those are enforcement docs, not history. `hit` first; `promote` when earned. |
| New slug per occurrence | `memento list` first; recurrence = same slug. Duplicates break the rate tracking. |
| Vague fix ("fixed certs") | Record the exact command/env var/edit that worked. |
| Skipping `memento check` at task start | That is precisely how mistakes repeat. |
| Promoting on first occurrence | One-offs pollute enforcement docs. Thresholds exist; user "always/never" overrides them. |

## Bootstrap — script missing?

If `~/.agents/memento/memento.py` does not exist (first use on a machine), read `BOOTSTRAP.md` next to this file and copy its code block verbatim to that path. Do NOT read `BOOTSTRAP.md` otherwise — it is only the embedded script source, ~300 lines you never need when the CLI is installed.
