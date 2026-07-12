# ai

Private workspace for agent documentation, helpers, and tools. Holds the rules that make Claude Code agents effective and cheap here.

| File | Purpose |
|---|---|
| `CLAUDE.md` | Core rules, loaded every session — kept deliberately small |
| `rules/agents.md` | Inventory of subagents, plugins, skills, MCP servers on this machine |
| `rules/subagents.md` | When and how to delegate to subagents |
| `rules/releases.md` | Release process and guardrails |
| `rules/tooling.md` | Scouted ecosystem tools (optimizers, token trackers, linters) |
| `rules/fleet.md` | Subscription fleet (Codex, Cursor, GLM…) and task routing |
| `AGENTS.md` | Shared hard rules read by the non-Claude tools |
| `rules/research-2026-07.md` | Verified research: what measurably works in agent setups |

## Tools (Python, managed with uv)

| Command | Purpose |
|---|---|
| `uv run rulesync` | Sync the "read this repo first" pointer block into every AI tool's global instructions file (claude, codex, cursor, zcode, agy, trae, opencode, copilot) and force Copilot's `includeCoAuthoredBy` to false. Idempotent; `--dry-run` to preview. Re-run after changing hard rules. |

Projects live in their own subdirectories.
