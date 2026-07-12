# AI Workspace

Workspace for agent documentation, helpers, and small tools. These rules exist to get the best results from agents without wasting tokens.

Posture: **quality first** — use the best model for work that matters; save tokens by avoiding waste (repeated work, bloated context), not by downgrading quality.

## Rule files (read on demand — do not preload)

- `rules/subagents.md` — read BEFORE delegating work to any subagent
- `rules/releases.md` — read BEFORE any release, tag, or publish action
- `rules/agents.md` — inventory of agents, skills, and MCP servers on this machine

## Token discipline

- Delegate broad searches and investigation to subagents; keep the main context for decisions. Default code locator: `caveman:cavecrew-investigator` (compressed output).
- If exploration would take more than ~3 file reads or ~5 tool calls, delegate it instead of doing it inline.
- Batch independent tool calls in a single message so they run in parallel.
- Read only the line ranges you need from large files; never re-read files already in context.
- Keep this file under ~50 lines. Details belong in `rules/`, loaded on demand.

## Hard rules

- No AI attribution anywhere, ever: no `Co-Authored-By`, no "Generated with Claude" in commits, PRs, or release notes.
- Always create a working branch before starting work. Never commit directly to `main`.
- If the working directory has no git repository or no associated remote: stop and ask the user how to proceed before making changes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- Each project lives in its own subdirectory. Add a project-level CLAUDE.md only when its rules differ from these.
