# AI Workspace

Root workspace for AI/agent projects. These rules exist to get the best results from agents at the lowest token cost.

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

- No AI attribution anywhere: no `Co-Authored-By`, no "Generated with Claude" in commits, PRs, or release notes.
- Never release, tag, push, or publish without an explicit user request in the current session.
- Each project lives in its own subdirectory. Add a project-level CLAUDE.md only when its rules differ from these.
