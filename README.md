# ai

Workspace for agent documentation, helpers, and small tools — the rules that make AI coding agents effective and cheap. One repo is the single source of truth; every tool on the machine (Claude Code, Codex, Cursor, Copilot, …) gets pointed at it.

| File | Purpose |
|---|---|
| `CLAUDE.md` | Core rules, loaded every session — kept deliberately small |
| `AGENTS.md` | Shared hard rules read by the non-Claude tools |
| `rules/subagents.md` | When and how to delegate to subagents |
| `rules/releases.md` | Release process and guardrails |
| `rules/github-actions.md` | CI cost rules — Linux-first, gated Windows/macOS |
| `rules/rust-app-remote-control.md` | Build, bundle, remotely control, and capture Rust GUI apps on macOS |
| `rules/local/` | Machine-local, gitignored — tool inventories, subscriptions, review bridges |

## Projects

| Directory | Purpose |
|---|---|
| [`memento/`](memento/) | Repeated-mistake ledger for AI agents — mistakes get logged, repeated ones get promoted to enforced rules. Own README, one-command installer. |

## Tools (Python, managed with uv)

| Command | Purpose |
|---|---|
| `uv run rulesync` (or `uv run main.py`) | Sync the "read this repo first" pointer block into every AI tool's global instructions file (claude, codex, cursor, zcode, agy, trae, opencode, copilot) and force Copilot's `includeCoAuthoredBy` to false. Interactive by default: status table → pick tools → preview → confirm. `--dry-run` previews, `--yes` applies without prompts, `--tool NAME` targets specific tools. Idempotent; re-run after changing hard rules. |

Quality gates run locally before merge: `uv run pytest`, `ruff check`.

Projects live in their own subdirectories.
