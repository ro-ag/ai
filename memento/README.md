# Memento

Cross-agent "learn from mistakes" system. Agents have no long-term memory, so the rules that must never be forgotten get tattooed: repeated mistakes, hard-won fixes, and ignored quality gates go into ledgers; recurrence is counted and cost-scored; repeat offenders are promoted automatically into enforced rules in `AGENTS.md`/`CLAUDE.md`.

Protocol lives in [SKILL.md](SKILL.md) (CONSULT → LOG → PROMOTE). The skill ships as **markdown only** — the full `memento.py` source travels in its Appendix and is bootstrapped to `~/.agents/memento/memento.py` on first use. The canonical script here and the Appendix are kept byte-identical by `memento_test.py`.

## Layout

| Piece | Path |
|---|---|
| Runtime CLI (all tools, stdlib only) | `~/.agents/memento/memento.py` |
| Global ledger (machine-wide lessons) | `~/.agents/memento/MEMENTO.md` |
| Project ledger | `<git root>/MEMENTO.md`, created on first `hit` |
| Enforcement docs, global scope | `~/dev/ai/AGENTS.md` + `CLAUDE.md`, section `## Memento-enforced` |
| Enforcement docs, project scope | project `AGENTS.md` (+ `CLAUDE.md` if present) |

Global rules dir resolution: env `MEMENTO_AI_DIR` → `rules_dir` in `~/.agents/memento/config.json` → `~/.agents/memento/` itself. This machine uses config.json pointing at `~/dev/ai`. `MEMENTO_HOME` overrides the global ledger dir (tests use it). SKILL.md stays ultra generic — machine specifics live only in config.json.

## Commands

```
memento check                # task start: enforced (law) + watching (defaults)
memento hit <slug> [--rule "..."] [--fix "..."] [--kind habit|trick|gate|project-way]
                   [--scope global|project] [--cost MINUTES]
memento top                  # rate-of-issues: ranked by hits + cost, last-hit shown
memento list | show <slug>
memento promote <slug>       # write rule into the Memento-enforced section
memento remind               # hook helper: stdin JSON, nudges on correction signals
```

Alerts: 3 hits, or ≥30 min lost in one hit → `PROMOTE: run memento promote <slug>`.

## Per-tool coverage

| Tool | How it gets memento |
|---|---|
| Claude Code | Skill symlink `~/.claude/skills/memento/SKILL.md` + `CLAUDE.md` rule + optional hooks (below) |
| Codex / Copilot CLI | Skill symlink `~/.agents/skills/memento/SKILL.md` + `AGENTS.md` rule (rulesync pointer) |
| Cursor, opencode, zcode, antigravity, trae | `AGENTS.md` rule via rulesync pointer block |

## Install (this machine — already done)

```bash
mkdir -p ~/.agents/memento ~/.agents/skills/memento ~/.claude/skills/memento
cp ~/dev/ai/memento/memento.py ~/.agents/memento/memento.py
printf '{"rules_dir": "%s"}\n' ~/dev/ai > ~/.agents/memento/config.json
ln -sf ~/dev/ai/memento/SKILL.md ~/.claude/skills/memento/SKILL.md
ln -sf ~/dev/ai/memento/SKILL.md ~/.agents/skills/memento/SKILL.md
```

After changing `memento.py`: re-run tests, re-inject the SKILL.md appendix, and re-copy to `~/.agents/memento/`.

## Claude Code hooks (optional, recommended — makes CONSULT/LOG automatic)

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "python3 ~/.agents/memento/memento.py check 2>/dev/null || true"}]}
    ],
    "UserPromptSubmit": [
      {"hooks": [{"type": "command", "command": "python3 ~/.agents/memento/memento.py remind 2>/dev/null || true"}]}
    ]
  }
}
```

`SessionStart` injects the lesson list into every session (CONSULT with zero discipline). `UserPromptSubmit` nudges when a prompt looks like a repeated correction ("again", "I told you", …). Other tools have no hooks and rely on the `AGENTS.md` instruction.

## Tests

```bash
uv run python -m unittest memento.memento_test
```
