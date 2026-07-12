# Agent rules — all AI tools

Shared rules for every AI coding tool on this machine (Codex, Cursor, Copilot, Antigravity, Trae, opencode, zcode/GLM). Claude Code reads `CLAUDE.md`, which mirrors these. Keep the two in sync.

## Hard rules

- No AI attribution, ever: no `Co-Authored-By`, no "Generated with …" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`/`master`. Branches land via PR + squash merge, branch deleted at merge.
- If the working directory has no git repository or no associated remote: stop and ask the user before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- GitHub Actions cost money on private repos: never add or enable a workflow unless explicitly asked. When one exists, it triggers on merge to `main` or on release tags only — never on every push or PR update. Quality gates run locally (tests, lint, review) before merge instead.

## Workspace

- Purpose: agent documentation, helpers, and small tools. Each project in its own subdirectory.
- Release process: `rules/releases.md`. Tool fleet and task routing: `rules/fleet.md`.
- Posture: quality first — save tokens by avoiding waste, not by downgrading model quality on work that matters.
