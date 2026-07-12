# ai

Private workspace for agent documentation, helpers, and tools. Holds the rules that make Claude Code agents effective and cheap here.

| File | Purpose |
|---|---|
| `CLAUDE.md` | Core rules, loaded every session — kept deliberately small |
| `rules/agents.md` | Inventory of subagents, plugins, skills, MCP servers on this machine |
| `rules/subagents.md` | When and how to delegate to subagents |
| `rules/releases.md` | Release process and guardrails |
| `rules/fleet.md` | Subscription fleet (Codex, Cursor, GLM…) and task routing |
| `rules/second-opinion.md` | Cross-vendor review via Codex / Grok / Gemini bridges |
| `AGENTS.md` | Shared hard rules read by the non-Claude tools |

## Tools (Python, managed with uv)

| Command | Purpose |
|---|---|
| `uv run rulesync` (or `uv run main.py`) | Sync the "read this repo first" pointer block into every AI tool's global instructions file (claude, codex, cursor, zcode, agy, trae, opencode, copilot) and force Copilot's `includeCoAuthoredBy` to false. Interactive by default: status table → pick tools → preview → confirm. `--dry-run` previews, `--yes` applies without prompts, `--tool NAME` targets specific tools. Idempotent; re-run after changing hard rules. |

Projects live in their own subdirectories.
