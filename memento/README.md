# Memento

Cross-agent "learn from mistakes" system. Agents have no long-term memory, so the rules that must never be forgotten get tattooed: repeated mistakes, hard-won fixes, and ignored quality gates go into ledgers; recurrence is counted and cost-scored; repeat offenders are promoted automatically into enforced rules in `AGENTS.md`/`CLAUDE.md`.

Protocol lives in [SKILL.md](SKILL.md) (CONSULT → LOG → PROMOTE). The skill ships as **markdown only** — the full `memento.py` source travels in [BOOTSTRAP.md](BOOTSTRAP.md) and is bootstrapped to `~/.agents/memento/memento.py` on first use. SKILL.md stays slim (~80 lines) so loading the skill never re-reads the ~300-line script; agents open BOOTSTRAP.md only when the CLI is missing. The canonical script and the BOOTSTRAP.md block are kept byte-identical by `memento_test.py`.

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

## Install — the easy way (any machine)

One block. Point `REPO` at your clone (or at any directory holding the skill files; no clone at all → copy the BOOTSTRAP.md code block to `~/.agents/memento/memento.py` and skip the `cp`):

```bash
REPO=~/dev/ai/memento
mkdir -p ~/.agents/memento ~/.agents/skills/memento ~/.claude/skills/memento
cp "$REPO/memento.py" ~/.agents/memento/memento.py
ln -sf "$REPO"/{SKILL,BOOTSTRAP}.md ~/.claude/skills/memento/   # Claude Code
ln -sf "$REPO"/{SKILL,BOOTSTRAP}.md ~/.agents/skills/memento/   # Codex, Copilot CLI, Gemini CLI
# optional: where global promoted rules land (default: ~/.agents/memento/)
printf '{"rules_dir": "%s"}\n' "$HOME/dev/ai" > ~/.agents/memento/config.json
```

Run from anywhere, any tool:

```bash
python3 ~/.agents/memento/memento.py check
```

### Per-tool pickup

| Tool | How it finds memento | Extra step |
|---|---|---|
| Claude Code | skill dir `~/.claude/skills/memento/` | optional hooks below |
| Codex CLI | skill dir `~/.agents/skills/memento/` | — |
| Copilot CLI | skill dir `~/.agents/skills/memento/` | — |
| Gemini CLI | skill dir `~/.agents/skills/memento/` | — |
| Cursor | no skills — pointer in `~/.cursor/AGENTS.md` | pointer snippet below (rulesync handles it on this machine) |
| Kimi CLI, opencode, zcode, antigravity, trae, … | pointer in the tool's global agent file (`~/.config/opencode/AGENTS.md`, `~/.zcode/cli/AGENTS.md`, …) | pointer snippet below |

Pointer snippet for tools without skill support — paste into their global `AGENTS.md`:

```markdown
## Memento — learn from mistakes
- Task start: run `python3 ~/.agents/memento/memento.py check` and respect its output.
- On user correction, hard-won fix, or ignored quality gate: `memento hit <slug> --rule "..." --fix "..."`.
- On a PROMOTE alert or user "always/never": `memento promote <slug>`.
- Full protocol: ~/.agents/skills/memento/SKILL.md
```

After changing `memento.py`: re-run tests, re-inject the BOOTSTRAP.md code block, and re-copy to `~/.agents/memento/`.

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
